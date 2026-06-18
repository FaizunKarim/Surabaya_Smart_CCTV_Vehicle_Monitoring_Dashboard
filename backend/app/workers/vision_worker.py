import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.entities import CCTVCamera
from app.services.bootstrap import create_tables
from app.services.discovery import sync_cctv_catalog
from app.services.vision import VisionPipeline


async def main() -> None:
    settings = get_settings()
    await create_tables()
    pipeline = VisionPipeline()

    async with SessionLocal() as session:
        try:
            await sync_cctv_catalog(session)
        except Exception as exc:
            print(f"[vision-worker] initial sync failed: {exc}")

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
            print(f"[vision-worker] cycle failed: {exc}")
        await asyncio.sleep(settings.vision_loop_seconds)


if __name__ == "__main__":
    asyncio.run(main())
