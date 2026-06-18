from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import AnalyticsSnapshot, CCTVCamera, VehicleEvent


def utcnow() -> datetime:
    return datetime.now(UTC)


VEHICLE_CLASS_MAP = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


@dataclass
class CameraRuntimeState:
    tracker: Any
    line_zone: Any
    counter_date: date = field(default_factory=lambda: utcnow().date())
    total_counts: dict[str, int] = field(
        default_factory=lambda: {
            "motorcycle": 0,
            "car": 0,
            "truck": 0,
            "bus": 0,
            "line_in": 0,
            "line_out": 0,
        }
    )
    unique_tracker_labels: set[tuple[int | None, str]] = field(default_factory=set)
    last_object_events: set[tuple[int | None, str, str]] = field(default_factory=set)


class VisionPipeline:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.enabled = self.settings.enable_ai_pipeline
        self.ready = False
        self.error: str | None = None
        self.model: Any | None = None
        self.sv: Any | None = None
        self.cv2: Any | None = None
        self.np: Any | None = None
        self.runtime_states: dict[str, CameraRuntimeState] = {}

        if not self.enabled:
            return

        try:
            import cv2
            import numpy as np
            import supervision as sv
            from ultralytics import YOLO

            self.cv2 = cv2
            self.np = np
            self.sv = sv
            self.model = YOLO(self.settings.yolo_model_path)
            self.ready = True
        except Exception as exc:  # pragma: no cover
            self.error = str(exc)
            self.ready = False

    def mode(self) -> str:
        return "yolo-supervision" if self.ready else "dry-run"

    def _build_line_zone(self, camera: CCTVCamera, width: int, height: int) -> Any:
        assert self.sv is not None
        return self.sv.LineZone(
            start=self.sv.Point(
                x=int(width * camera.line_start_x_ratio),
                y=int(height * camera.line_start_y_ratio),
            ),
            end=self.sv.Point(
                x=int(width * camera.line_end_x_ratio),
                y=int(height * camera.line_end_y_ratio),
            ),
        )

    def _runtime_for(self, camera: CCTVCamera, width: int, height: int) -> CameraRuntimeState:
        assert self.sv is not None
        runtime = self.runtime_states.get(camera.cctv_id)
        if runtime is not None and runtime.counter_date == utcnow().date():
            return runtime
        runtime = CameraRuntimeState(
            tracker=self.sv.ByteTrack(),
            line_zone=self._build_line_zone(camera, width, height),
            counter_date=utcnow().date(),
        )
        self.runtime_states[camera.cctv_id] = runtime
        return runtime

    async def process_camera(self, session: AsyncSession, camera: CCTVCamera) -> AnalyticsSnapshot:
        if not self.ready or not self.cv2 or not self.np or not self.sv or not self.model:
            snapshot = AnalyticsSnapshot(
                cctv_id=camera.cctv_id,
                captured_at=utcnow(),
                last_inference_at=None,
                source="dry-run",
                processed_frames=0,
                sample_every_n_frames=self.settings.vision_sample_every_n_frames,
                tracker_active_objects=0,
                line_in_count=0,
                line_out_count=0,
                motorcycle_count=0,
                car_count=0,
                truck_count=0,
                bus_count=0,
                metadata_json={"reason": self.error or "AI pipeline disabled"},
            )
            session.add(snapshot)
            await session.commit()
            return snapshot

        capture = self.cv2.VideoCapture(camera.stream_url)
        processed_frames = 0
        frame_index = 0
        active_objects = 0
        runtime: CameraRuntimeState | None = None

        try:
            while frame_index < self.settings.vision_frames_per_camera:
                ok, frame = capture.read()
                if not ok or frame is None:
                    break

                frame_index += 1
                if frame_index % self.settings.vision_sample_every_n_frames != 0:
                    continue

                if runtime is None:
                    height, width = frame.shape[:2]
                    runtime = self._runtime_for(camera, width=width, height=height)

                result = self.model(
                    frame,
                    verbose=False,
                    conf=self.settings.vision_confidence_threshold,
                )[0]
                detections = self.sv.Detections.from_ultralytics(result)
                if detections.class_id is None or len(detections) == 0:
                    processed_frames += 1
                    continue

                mask = self.np.isin(detections.class_id, list(VEHICLE_CLASS_MAP.keys()))
                detections = detections[mask]
                if len(detections) == 0:
                    processed_frames += 1
                    continue

                tracked = runtime.tracker.update_with_detections(detections)
                active_objects = len(tracked)

                before_in = getattr(runtime.line_zone, "in_count", 0)
                before_out = getattr(runtime.line_zone, "out_count", 0)
                runtime.line_zone.trigger(tracked)
                runtime.total_counts["line_in"] = getattr(runtime.line_zone, "in_count", 0)
                runtime.total_counts["line_out"] = getattr(runtime.line_zone, "out_count", 0)

                tracker_ids = tracked.tracker_id if tracked.tracker_id is not None else []
                class_ids = tracked.class_id if tracked.class_id is not None else []
                confidences = tracked.confidence if tracked.confidence is not None else []

                for idx, class_id in enumerate(class_ids):
                    label = VEHICLE_CLASS_MAP.get(int(class_id))
                    if not label:
                        continue
                    if idx < len(tracker_ids):
                        tracker_id = int(tracker_ids[idx]) if tracker_ids[idx] is not None else None
                    else:
                        tracker_id = None
                    confidence = (
                        float(confidences[idx])
                        if idx < len(confidences) and confidences[idx] is not None
                        else None
                    )
                    tracker_key = (tracker_id, label)
                    if tracker_key not in runtime.unique_tracker_labels:
                        runtime.unique_tracker_labels.add(tracker_key)
                        runtime.total_counts[label] += 1

                    if getattr(runtime.line_zone, "in_count", 0) > before_in:
                        event_key = (tracker_id, label, "in")
                        if event_key not in runtime.last_object_events:
                            runtime.last_object_events.add(event_key)
                            session.add(
                                VehicleEvent(
                                    cctv_id=camera.cctv_id,
                                    object_id=tracker_id,
                                    label=label,
                                    confidence=confidence,
                                    direction="in",
                                    frame_index=frame_index,
                                )
                            )
                    if getattr(runtime.line_zone, "out_count", 0) > before_out:
                        event_key = (tracker_id, label, "out")
                        if event_key not in runtime.last_object_events:
                            runtime.last_object_events.add(event_key)
                            session.add(
                                VehicleEvent(
                                    cctv_id=camera.cctv_id,
                                    object_id=tracker_id,
                                    label=label,
                                    confidence=confidence,
                                    direction="out",
                                    frame_index=frame_index,
                                )
                            )

                processed_frames += 1

        finally:
            capture.release()

        counts = runtime.total_counts if runtime else {
            "motorcycle": 0,
            "car": 0,
            "truck": 0,
            "bus": 0,
            "line_in": 0,
            "line_out": 0,
        }
        snapshot = AnalyticsSnapshot(
            cctv_id=camera.cctv_id,
            captured_at=utcnow(),
            last_inference_at=utcnow(),
            source=self.mode(),
            processed_frames=processed_frames,
            sample_every_n_frames=self.settings.vision_sample_every_n_frames,
            tracker_active_objects=active_objects,
            line_in_count=counts["line_in"],
            line_out_count=counts["line_out"],
            motorcycle_count=counts["motorcycle"],
            car_count=counts["car"],
            truck_count=counts["truck"],
            bus_count=counts["bus"],
            metadata_json={
                "vision_frames_per_camera": self.settings.vision_frames_per_camera,
                "confidence_threshold": self.settings.vision_confidence_threshold,
            },
        )
        session.add(snapshot)
        await session.commit()
        return snapshot
