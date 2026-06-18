from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AnalyticsSnapshot, CCTVCamera
from app.schemas.api import (
    AnalyticsHistoryPoint,
    CCTVAnalytics,
    CCTVRecord,
    DashboardSocketPayload,
    DashboardSummary,
    VehicleCounts,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


def snapshot_counts(snapshot: AnalyticsSnapshot | None) -> VehicleCounts:
    if snapshot is None:
        return VehicleCounts()
    return VehicleCounts(
        motorcycle=snapshot.motorcycle_count,
        car=snapshot.car_count,
        truck=snapshot.truck_count,
        bus=snapshot.bus_count,
        line_in=snapshot.line_in_count,
        line_out=snapshot.line_out_count,
    )


async def latest_snapshot_map(
    session: AsyncSession, cctv_ids: list[str] | None = None
) -> dict[str, AnalyticsSnapshot]:
    query: Select[tuple[AnalyticsSnapshot]] = select(AnalyticsSnapshot).order_by(
        AnalyticsSnapshot.cctv_id, desc(AnalyticsSnapshot.captured_at)
    )
    if cctv_ids:
        query = query.where(AnalyticsSnapshot.cctv_id.in_(cctv_ids))

    rows = (await session.execute(query)).scalars().all()
    latest: dict[str, AnalyticsSnapshot] = {}
    for row in rows:
        latest.setdefault(row.cctv_id, row)
    return latest


async def list_cctvs(
    session: AsyncSession,
    search: str = "",
    status: str = "all",
    area: str = "all",
    sort: str = "asc",
) -> list[CCTVRecord]:
    query = select(CCTVCamera)
    if status != "all":
        query = query.where(CCTVCamera.status == status.lower())
    if area != "all":
        query = query.where(func.lower(CCTVCamera.area) == area.lower())

    cameras = (await session.execute(query)).scalars().all()
    snapshot_map = await latest_snapshot_map(session, [camera.cctv_id for camera in cameras])

    items: list[CCTVRecord] = []
    needle = search.lower().strip()
    for camera in cameras:
        if needle and not (
            needle in camera.name.lower()
            or needle in camera.cctv_id.lower()
            or needle in camera.area.lower()
            or needle in str(camera.source_db_id)
            or needle in str(camera.no)
        ):
            continue

        snapshot = snapshot_map.get(camera.cctv_id)
        items.append(
            CCTVRecord(
                no=camera.no,
                id=camera.source_db_id,
                cctv_id=camera.cctv_id,
                name=camera.name,
                area=camera.area,
                status=camera.status,  # type: ignore[arg-type]
                latitude=camera.latitude,
                longitude=camera.longitude,
                stream_url=camera.stream_url,
                vehicle_counts=snapshot_counts(snapshot),
                ai_source=snapshot.source if snapshot else "dry-run",
                last_update=snapshot.captured_at if snapshot else camera.last_seen_at,
                last_status_change=camera.last_status_change,
            )
        )

    items.sort(key=lambda item: item.no, reverse=sort.lower() == "desc")
    return items


async def get_cctv_record(session: AsyncSession, cctv_id: str) -> CCTVRecord | None:
    camera = await session.get(CCTVCamera, cctv_id)
    if camera is None:
        return None

    snapshot = (
        await session.execute(
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.cctv_id == cctv_id)
            .order_by(desc(AnalyticsSnapshot.captured_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    return CCTVRecord(
        no=camera.no,
        id=camera.source_db_id,
        cctv_id=camera.cctv_id,
        name=camera.name,
        area=camera.area,
        status=camera.status,  # type: ignore[arg-type]
        latitude=camera.latitude,
        longitude=camera.longitude,
        stream_url=camera.stream_url,
        vehicle_counts=snapshot_counts(snapshot),
        ai_source=snapshot.source if snapshot else "dry-run",
        last_update=snapshot.captured_at if snapshot else camera.last_seen_at,
        last_status_change=camera.last_status_change,
    )


async def get_cctv_analytics(
    session: AsyncSession, cctv_id: str
) -> CCTVAnalytics | None:
    camera = await session.get(CCTVCamera, cctv_id)
    if camera is None:
        return None

    snapshot = (
        await session.execute(
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.cctv_id == cctv_id)
            .order_by(desc(AnalyticsSnapshot.captured_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    counts = snapshot_counts(snapshot)

    return CCTVAnalytics(
        no=camera.no,
        id=camera.source_db_id,
        cctv_id=camera.cctv_id,
        name=camera.name,
        area=camera.area,
        status=camera.status,  # type: ignore[arg-type]
        stream_url=camera.stream_url,
        counts=counts,
        total_vehicles=counts.total,
        tracker_active_objects=snapshot.tracker_active_objects if snapshot else 0,
        processed_frames=snapshot.processed_frames if snapshot else 0,
        sample_every_n_frames=snapshot.sample_every_n_frames if snapshot else 0,
        last_update=snapshot.captured_at if snapshot else camera.last_seen_at,
        ai_mode=snapshot.source if snapshot else "dry-run",
        line_zone={
            "start_x_ratio": camera.line_start_x_ratio,
            "start_y_ratio": camera.line_start_y_ratio,
            "end_x_ratio": camera.line_end_x_ratio,
            "end_y_ratio": camera.line_end_y_ratio,
        },
        metadata=snapshot.metadata_json if snapshot else {},
    )


async def get_summary(session: AsyncSession, ai_enabled: bool, last_sync: datetime | None) -> DashboardSummary:
    cameras = (await session.execute(select(CCTVCamera))).scalars().all()
    snapshot_map = await latest_snapshot_map(session, [camera.cctv_id for camera in cameras])

    counts = {"online": 0, "offline": 0, "error": 0, "loading": 0}
    total_vehicles_today = 0
    total_crossings_today = 0
    today = utcnow() - timedelta(hours=24)

    for camera in cameras:
        counts[camera.status] = counts.get(camera.status, 0) + 1

    today_rows = (
        await session.execute(
            select(AnalyticsSnapshot).where(AnalyticsSnapshot.captured_at >= today)
        )
    ).scalars()
    latest_per_camera: dict[str, AnalyticsSnapshot] = {}
    for row in today_rows:
        if row.cctv_id not in latest_per_camera or row.captured_at > latest_per_camera[row.cctv_id].captured_at:
            latest_per_camera[row.cctv_id] = row

    for snapshot in latest_per_camera.values():
        counts_obj = snapshot_counts(snapshot)
        total_vehicles_today += counts_obj.total
        total_crossings_today += counts_obj.line_in + counts_obj.line_out

    return DashboardSummary(
        total_cctv=len(cameras),
        online_cctv=counts["online"],
        offline_cctv=counts["offline"],
        error_cctv=counts["error"],
        loading_cctv=counts["loading"],
        total_vehicles_today=total_vehicles_today,
        total_crossings_today=total_crossings_today,
        last_sync=last_sync,
        ai_pipeline_enabled=ai_enabled,
    )


async def get_history(
    session: AsyncSession, cctv_id: str, minutes: int = 60
) -> list[AnalyticsHistoryPoint]:
    since = utcnow() - timedelta(minutes=minutes)
    snapshots = (
        await session.execute(
            select(AnalyticsSnapshot)
            .where(
                AnalyticsSnapshot.cctv_id == cctv_id,
                AnalyticsSnapshot.captured_at >= since,
            )
            .order_by(AnalyticsSnapshot.captured_at.asc())
        )
    ).scalars().all()

    return [
        AnalyticsHistoryPoint(
            captured_at=item.captured_at,
            counts=snapshot_counts(item),
            total_vehicles=snapshot_counts(item).total,
            tracker_active_objects=item.tracker_active_objects,
            processed_frames=item.processed_frames,
            ai_mode=item.source,
        )
        for item in snapshots
    ]


async def websocket_payload(
    session: AsyncSession,
    selected_cctv_id: str | None,
    ai_enabled: bool,
    last_sync: datetime | None,
) -> DashboardSocketPayload:
    summary = await get_summary(session, ai_enabled=ai_enabled, last_sync=last_sync)
    selected = None
    if selected_cctv_id:
        selected = await get_cctv_analytics(session, selected_cctv_id)
    return DashboardSocketPayload(
        generated_at=utcnow(),
        summary=summary,
        selected=selected,
    )
