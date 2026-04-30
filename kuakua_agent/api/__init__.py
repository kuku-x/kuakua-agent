"""HTTP API layer."""

from __future__ import annotations

import inspect

from starlette.routing import Router


def _patch_starlette_router_for_fastapi() -> None:
    """Bridge FastAPI APIRouter with Starlette 1.x Router signature changes."""
    params = inspect.signature(Router.__init__).parameters
    if "on_startup" in params and "on_shutdown" in params:
        return

    original_init = Router.__init__

    def patched_init(
        self,
        routes=None,
        redirect_slashes: bool = True,
        default=None,
        on_startup=None,
        on_shutdown=None,
        lifespan=None,
        *,
        middleware=None,
    ) -> None:
        startup_handlers = list(on_startup or [])
        shutdown_handlers = list(on_shutdown or [])
        original_init(
            self,
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            lifespan=lifespan,
            middleware=middleware,
        )
        self.on_startup = startup_handlers
        self.on_shutdown = shutdown_handlers

    Router.__init__ = patched_init


_patch_starlette_router_for_fastapi()
