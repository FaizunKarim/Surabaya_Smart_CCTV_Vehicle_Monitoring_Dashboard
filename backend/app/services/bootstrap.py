import asyncio
from contextlib import suppress
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import Base, SessionLocal, engine
from app.models.entities import CCTVCamera
from app.services.discovery import sync_cctv_catalog
from app.services.vision import VisionPipeline


def utcnow() -> datetime:
    return datetime.now(UTC)


async def create_tables() -> None:
    settings = get_settings()
    if not settings.auto_create_tables:
        return
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def sync_loop(app) -> None:
    settings = get_settings()
    while True:
        try:
            async with SessionLocal() as session:
                app.state.last_sync = await sync_cctv_catalog(session)
        except Exception as exc:
            print(f"[sync-loop] failed: {exc}")
        await asyncio.sleep(settings.sync_interval_seconds)


async def vision_loop(app) -> None:
    settings = get_settings()
    pipeline: VisionPipeline = app.state.vision_pipeline

    while True:
        try:
            async with SessionLocal() as session:
                cameras = (
                    await session.execute(
                        select(CCTVCamera)
                        .where(CCTVCamera.status == "online")
                        .order_by(CCTVCamera.no.asc())
                        .limit(settings.vision_max_cameras_per_cycle)
                    )
                ).scalars().all()

                for camera in cameras:
                    await pipeline.process_camera(session, camera)
        except Exception as exc:
            print(f"[vision-loop] failed: {exc}")
        await asyncio.sleep(settings.vision_loop_seconds)


async def startup(app) -> None:
    await create_tables()
    app.state.vision_pipeline = VisionPipeline()
    app.state.last_sync = None
    app.state.vision_task = None

    async with SessionLocal() as session:
        try:
            app.state.last_sync = await sync_cctv_catalog(session)
        except Exception as exc:
            print(f"[startup-sync] failed: {exc}")

    app.state.sync_task = asyncio.create_task(sync_loop(app))
    if get_settings().run_embedded_vision_worker:
        app.state.vision_task = asyncio.create_task(vision_loop(app))


async def shutdown(app) -> None:
    for attr in ("sync_task", "vision_task"):
        task = getattr(app.state, attr, None)
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
