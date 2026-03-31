"""
FastAPI app for Celery Ops.

Wires config, store, event consumer (background thread), API routes, optional UI.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import init_routes, router
from .config import OpsConfig
from .events import TaskEventConsumer
from .store import OpsStore

logger = logging.getLogger(__name__)

_consumer_thread: threading.Thread | None = None
_consumer: TaskEventConsumer | None = None


def _start_consumer(app: Any, store: OpsStore) -> None:
    global _consumer_thread, _consumer
    _consumer = TaskEventConsumer(app, store)
    _consumer_thread = threading.Thread(target=_consumer.run, daemon=True)
    _consumer_thread.start()
    logger.info("Celery Ops: event consumer started (background thread)")


def _ensure_ui_static() -> Path | None:
    base = Path(__file__).resolve().parent
    # Try React build first
    react_build = base / "ui" / "react" / "build"
    if react_build.is_dir() and (react_build / "index.html").exists():
        return react_build
    # Fallback to simple HTML UI
    simple_ui = base / "ui" / "simple"
    if simple_ui.is_dir() and (simple_ui / "index.html").exists():
        return simple_ui
    return None


def create_app(celery_app: Any, config: OpsConfig) -> FastAPI:
    """Create FastAPI app for Celery Ops."""
    store = OpsStore(config)
    init_routes(celery_app, store)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if config.events_enabled:
            _start_consumer(celery_app, store)
        else:
            logger.info("Celery Ops: event consumer disabled (--no-events)")
        yield
        # Daemon thread will exit with process; no explicit stop needed

    api = FastAPI(
        title="Celery Ops",
        description="Ops-only observer and lightweight controller for Celery. See SCOPE.md.",
        version="0.1.0",
        lifespan=lifespan,
    )
    api.include_router(router)

    static_dir = _ensure_ui_static()
    if config.ui_enabled and static_dir:
        # Check if static subdirectory exists (React build creates this)
        static_subdir = static_dir / "static"
        if static_subdir.exists():
            api.mount("/static", StaticFiles(directory=str(static_subdir)), name="static")
        
        index = static_dir / "index.html"
        if index.is_file():

            @api.get("/")
            def _index() -> FileResponse:
                return FileResponse(index)
                
            # Only add SPA fallback for React builds (not simple HTML)
            if "react" in str(static_dir):
                # Serve React app for all non-API routes
                @api.get("/{path:path}")
                def _spa_fallback(path: str) -> FileResponse:
                    # Don't intercept API routes
                    if path.startswith("api/") or path.startswith("docs"):
                        raise HTTPException(404)
                    return FileResponse(index)
        else:
            @api.get("/")
            def _index_no_build() -> dict[str, str]:
                return {
                    "message": "Celery Ops API", 
                    "docs": "/docs", 
                    "ui": "No UI found",
                    "note": "Install React dependencies and build the UI"
                }
    elif config.ui_enabled:

        @api.get("/")
        def _index_fallback() -> dict[str, str]:
            return {
                "message": "Celery Ops API", 
                "docs": "/docs", 
                "ui": "disabled",
                "note": "UI is disabled in configuration"
            }

    return api
