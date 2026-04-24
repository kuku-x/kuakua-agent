from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kuakua_agent.api.errors import register_exception_handlers
from kuakua_agent.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Kuakua Agent API",
        version="0.1.0",
    )

    # 跨域中间件配置 - 允许所有来源开发
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(router, prefix="/api")
    return app
