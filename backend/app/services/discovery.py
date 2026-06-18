from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import CCTVCamera


def utcnow() -> datetime:
    return datetime.now(UTC)


def normalize_status(status: str | None) -> str:
    normalized = (status or "loading").strip().lower()
    if normalized in {"online", "offline", "error", "loading"}:
        return normalized
    return "error"


async def sync_cctv_catalog(session: AsyncSession) -> datetime:
    settings = get_settings()
    timeout = settings.request_timeout_seconds

    async with httpx.AsyncClient(timeout=timeout) as client:
        cctv_response, status_response = await client.get(
            f"{settings.surabaya_base_url}/cctvs"
        ), await client.get(f"{settings.surabaya_base_url}/api/cctv_statuses")
        cctv_response.raise_for_status()
        status_response.raise_for_status()

    cctvs = cctv_response.json()
    status_map = status_response.json()
    now = utcnow()

    sorted_items = sorted(
        cctvs,
        key=lambda item: (
            str(item.get("area", "")),
            int(item.get("db_id", 0)),
            str(item.get("name", "")),
        ),
    )

    existing = {
        camera.cctv_id: camera
        for camera in (
            await session.execute(select(CCTVCamera))
        ).scalars()
    }
    active_ids: set[str] = set()

    for index, item in enumerate(sorted_items, start=1):
        cctv_id = str(item["id"])
        active_ids.add(cctv_id)
        status = normalize_status(status_map.get(cctv_id))
        stream_url = f"{settings.surabaya_base_url}/hls/{cctv_id}/stream.m3u8"
        camera = existing.get(cctv_id)

        if camera is None:
            camera = CCTVCamera(
                cctv_id=cctv_id,
                no=index,
                source_db_id=int(item["db_id"]),
                name=str(item["name"]).strip(),
                area=str(item.get("area", "UNKNOWN")).strip() or "UNKNOWN",
                latitude=float(item["lat"]),
                longitude=float(item["lng"]),
                stream_url=stream_url,
                status=status,
                last_seen_at=now,
                last_status_change=now,
                line_start_x_ratio=settings.line_start_x_ratio,
                line_start_y_ratio=settings.line_start_y_ratio,
                line_end_x_ratio=settings.line_end_x_ratio,
                line_end_y_ratio=settings.line_end_y_ratio,
            )
            session.add(camera)
            continue

        if camera.status != status:
            camera.last_status_change = now

        camera.no = index
        camera.source_db_id = int(item["db_id"])
        camera.name = str(item["name"]).strip()
        camera.area = str(item.get("area", "UNKNOWN")).strip() or "UNKNOWN"
        camera.latitude = float(item["lat"])
        camera.longitude = float(item["lng"])
        camera.stream_url = stream_url
        camera.status = status
        camera.last_seen_at = now

    for cctv_id, camera in existing.items():
        if cctv_id not in active_ids:
            await session.delete(camera)

    await session.commit()
    return now
