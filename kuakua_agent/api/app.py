import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from kuakua_agent.api.errors import register_exception_handlers
from kuakua_agent.api.activitywatch_proxy_routes import router as activitywatch_proxy_router
from kuakua_agent.api.routes import router
from kuakua_agent.api.phone_routes import router as phone_router
from kuakua_agent.api.usage_summary_routes import (
    usage_router as usage_summary_router,
    jobs_router as usage_jobs_router,
)
from kuakua_agent.core.logging import configure_logging, get_logger
from kuakua_agent.core.tracing import TRACE_ID_HEADER, new_trace_id
from kuakua_agent.services.websocket_manager import ws_manager

logger = get_logger(__name__)


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get(TRACE_ID_HEADER) or new_trace_id()
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response


def create_app() -> FastAPI:
    configure_logging()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        """Startup / shutdown logic, replacing the deprecated on_event hooks."""
        from kuakua_agent.services.storage_layer import get_database
        from kuakua_agent.services.monitor.scheduler import PraiseScheduler
        from kuakua_agent.services.monitor.activitywatch import ActivityWatchScheduler
        from kuakua_agent.services.monitor.nightly_summary_scheduler import NightlySummaryScheduler

        db = get_database()
        await db.init_db()

        # Load custom app categories into the shared guess_category cache
        from kuakua_agent.utils.shared import load_custom_categories
        from kuakua_agent.services.storage_layer import PreferenceStore
        pref = PreferenceStore()
        raw = await pref.get("app_categories") or "{}"
        load_custom_categories(raw)

        scheduler = PraiseScheduler()
        await scheduler.start()

        aw_scheduler = ActivityWatchScheduler()
        await aw_scheduler.start()

        nightly_summary = NightlySummaryScheduler()
        await nightly_summary.start()

        yield

        await scheduler.stop()
        await aw_scheduler.stop()
        await nightly_summary.stop()

    app = FastAPI(
        title="Kuakua Agent API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TraceIdMiddleware)

    register_exception_handlers(app)
    app.include_router(router, prefix="/api")
    app.include_router(phone_router, prefix="/api")
    app.include_router(usage_summary_router, prefix="/api")
    app.include_router(usage_jobs_router, prefix="/api")
    app.include_router(activitywatch_proxy_router, prefix="/api")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except Exception:
                    pass
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)

    logger.info("api_app_initialized", extra={"module_name": "api", "event": "startup_init"})
    return app
