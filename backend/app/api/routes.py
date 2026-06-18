import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.schemas.api import (
    AnalyticsHistoryPoint,
    CCTVAnalytics,
    CCTVRecord,
    DashboardSocketPayload,
    DashboardSummary,
)
from app.services.analytics import (
    get_cctv_analytics,
    get_cctv_record,
    get_history,
    get_summary,
    list_cctvs,
    websocket_payload,
)
from app.services.bootstrap import shutdown, startup


router = APIRouter()


@router.get("/api/health")
async def health(request: Request) -> dict[str, Any]:
    pipeline = request.app.state.vision_pipeline
    return {
        "status": "ok",
        "last_sync": request.app.state.last_sync,
        "ai_pipeline": pipeline.mode(),
        "ai_ready": pipeline.ready,
        "hf_space_mode": get_settings().hf_space_mode,
    }


@router.get("/api/cctvs", response_model=list[CCTVRecord])
async def cctvs(
    search: str = Query(default=""),
    status: str = Query(default="all"),
    area: str = Query(default="all"),
    sort: str = Query(default="asc"),
    session: AsyncSession = Depends(get_db_session),
) -> list[CCTVRecord]:
    return await list_cctvs(session, search=search, status=status, area=area, sort=sort)


@router.get("/api/cctvs/{cctv_id}", response_model=CCTVRecord)
async def cctv_detail(
    cctv_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> CCTVRecord:
    record = await get_cctv_record(session, cctv_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"CCTV {cctv_id} not found")
    return record


@router.get("/api/cctvs/{cctv_id}/analytics", response_model=CCTVAnalytics)
async def cctv_analytics(
    cctv_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> CCTVAnalytics:
    analytics = await get_cctv_analytics(session, cctv_id)
    if analytics is None:
        raise HTTPException(status_code=404, detail=f"CCTV {cctv_id} not found")
    return analytics


@router.get("/api/cctvs/{cctv_id}/history", response_model=list[AnalyticsHistoryPoint])
async def cctv_history(
    cctv_id: str,
    minutes: int = Query(default=60, ge=5, le=1440),
    session: AsyncSession = Depends(get_db_session),
) -> list[AnalyticsHistoryPoint]:
    return await get_history(session, cctv_id, minutes=minutes)


@router.get("/api/dashboard/summary", response_model=DashboardSummary)
async def dashboard_summary(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> DashboardSummary:
    return await get_summary(
        session,
        ai_enabled=request.app.state.vision_pipeline.ready,
        last_sync=request.app.state.last_sync,
    )


@router.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket, cctv: str | None = None) -> None:
    settings = get_settings()
    await websocket.accept()
    try:
        while True:
            async for session in get_db_session():
                payload = await websocket_payload(
                    session,
                    selected_cctv_id=cctv,
                    ai_enabled=websocket.app.state.vision_pipeline.ready,
                    last_sync=websocket.app.state.last_sync,
                )
                await websocket.send_json(payload.model_dump(mode="json"))
                break
            await asyncio.sleep(settings.ws_push_interval_seconds)
    except WebSocketDisconnect:
        return


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup(app)
    try:
        yield
    finally:
        await shutdown(app)


def build_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.resolved_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app
