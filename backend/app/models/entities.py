from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class CCTVCamera(Base):
    __tablename__ = "cctv_cameras"

    cctv_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    no: Mapped[int] = mapped_column(Integer, index=True)
    source_db_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    area: Mapped[str] = mapped_column(String(128), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    stream_url: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="loading", index=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status_change: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    line_start_x_ratio: Mapped[float] = mapped_column(Float, default=0.15)
    line_start_y_ratio: Mapped[float] = mapped_column(Float, default=0.72)
    line_end_x_ratio: Mapped[float] = mapped_column(Float, default=0.85)
    line_end_y_ratio: Mapped[float] = mapped_column(Float, default=0.72)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    snapshots: Mapped[list["AnalyticsSnapshot"]] = relationship(
        back_populates="camera", cascade="all, delete-orphan"
    )
    events: Mapped[list["VehicleEvent"]] = relationship(
        back_populates="camera", cascade="all, delete-orphan"
    )


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        Index("ix_analytics_snapshots_cctv_id_captured_at", "cctv_id", "captured_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cctv_id: Mapped[str] = mapped_column(
        ForeignKey("cctv_cameras.cctv_id", ondelete="CASCADE"), index=True
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_inference_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source: Mapped[str] = mapped_column(String(64), default="dry-run")
    processed_frames: Mapped[int] = mapped_column(Integer, default=0)
    sample_every_n_frames: Mapped[int] = mapped_column(Integer, default=12)
    tracker_active_objects: Mapped[int] = mapped_column(Integer, default=0)
    line_in_count: Mapped[int] = mapped_column(Integer, default=0)
    line_out_count: Mapped[int] = mapped_column(Integer, default=0)
    motorcycle_count: Mapped[int] = mapped_column(Integer, default=0)
    car_count: Mapped[int] = mapped_column(Integer, default=0)
    truck_count: Mapped[int] = mapped_column(Integer, default=0)
    bus_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    camera: Mapped[CCTVCamera] = relationship(back_populates="snapshots")


class VehicleEvent(Base):
    __tablename__ = "vehicle_events"
    __table_args__ = (
        Index("ix_vehicle_events_cctv_id_crossed_at", "cctv_id", "crossed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cctv_id: Mapped[str] = mapped_column(
        ForeignKey("cctv_cameras.cctv_id", ondelete="CASCADE"), index=True
    )
    object_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    label: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    direction: Mapped[str] = mapped_column(String(32), default="unknown")
    frame_index: Mapped[int] = mapped_column(Integer, default=0)
    crossed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    camera: Mapped[CCTVCamera] = relationship(back_populates="events")
