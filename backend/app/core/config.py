from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Surabaya Smart CCTV Vehicle Monitoring API"
    app_version: str = "0.2.0"
    app_env: str = "development"
    api_port: int = 8000

    surabaya_base_url: str = "http://36.66.208.101:5000"
    request_timeout_seconds: float = 20.0
    sync_interval_seconds: int = 300

    frontend_origin: str = "http://localhost:3000"
    public_api_base_url: str = "http://localhost:8000"

    database_url: str = "sqlite+aiosqlite:///./surabaya_cctv.db"
    auto_create_tables: bool = True

    enable_ai_pipeline: bool = False
    run_embedded_vision_worker: bool = False
    yolo_model_path: str = "yolov8n.pt"
    vision_loop_seconds: float = 5.0
    vision_max_cameras_per_cycle: int = 4
    vision_sample_every_n_frames: int = 12
    vision_frames_per_camera: int = 60
    vision_confidence_threshold: float = 0.3
    line_start_x_ratio: float = 0.15
    line_start_y_ratio: float = 0.72
    line_end_x_ratio: float = 0.85
    line_end_y_ratio: float = 0.72

    ws_push_interval_seconds: float = 1.0

    hf_space_mode: bool = False
    hf_public_url: str | None = None

    nginx_port: int = 8080
    postgres_db: str = "surabaya_cctv"
    postgres_user: str = "surabaya"
    postgres_password: str = "surabaya"

    cors_origins: list[str] = Field(default_factory=list)

    def resolved_cors_origins(self) -> list[str]:
        values = [
            self.frontend_origin,
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ]
        values.extend(self.cors_origins)
        if self.hf_public_url:
            values.append(self.hf_public_url)
        deduped: list[str] = []
        for value in values:
            if value and value not in deduped:
                deduped.append(value)
        return deduped


@lru_cache
def get_settings() -> Settings:
    return Settings()
