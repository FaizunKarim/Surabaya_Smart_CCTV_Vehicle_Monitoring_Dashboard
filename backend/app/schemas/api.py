from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


CCTVStatus = Literal["online", "offline", "error", "loading"]


class VehicleCounts(BaseModel):
    motorcycle: int = 0
    car: int = 0
    truck: int = 0
    bus: int = 0
    line_in: int = 0
    line_out: int = 0

    @property
    def total(self) -> int:
        return self.motorcycle + self.car + self.truck + self.bus


class CCTVRecord(BaseModel):
    no: int
    id: int
    cctv_id: str
    name: str
    area: str
    status: CCTVStatus
    latitude: float
    longitude: float
    stream_url: str
    vehicle_counts: VehicleCounts = Field(default_factory=VehicleCounts)
    ai_source: str = "dry-run"
    last_update: datetime | None = None
    last_status_change: datetime | None = None


class DashboardSummary(BaseModel):
    total_cctv: int
    online_cctv: int
    offline_cctv: int
    error_cctv: int
    loading_cctv: int
    total_vehicles_today: int
    total_crossings_today: int
    last_sync: datetime | None
    ai_pipeline_enabled: bool


class CCTVAnalytics(BaseModel):
    no: int
    id: int
    cctv_id: str
    name: str
    area: str
    status: CCTVStatus
    stream_url: str
    counts: VehicleCounts
    total_vehicles: int
    tracker_active_objects: int = 0
    processed_frames: int = 0
    sample_every_n_frames: int = 0
    last_update: datetime | None = None
    ai_mode: str
    line_zone: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsHistoryPoint(BaseModel):
    captured_at: datetime
    counts: VehicleCounts
    total_vehicles: int
    tracker_active_objects: int
    processed_frames: int
    ai_mode: str


class DashboardSocketPayload(BaseModel):
    type: str = "dashboard_snapshot"
    generated_at: datetime
    summary: DashboardSummary
    selected: CCTVAnalytics | None = None
