from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kuakua_agent.api.errors import register_exception_handlers
from kuakua_agent.api.routes import router
from kuakua_agent.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Kuakua Agent API",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

    register_exception_handlers(app)
    app.include_router(router, prefix="/api")
    return app

