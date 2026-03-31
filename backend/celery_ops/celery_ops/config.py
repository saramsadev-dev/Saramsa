"""Configuration for Celery Ops."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class OpsConfig:
    """Ops-only config. No app DB, auth, or billing."""

    host: str = "0.0.0.0"
    port: int = 9800
    ui_enabled: bool = True
    events_enabled: bool = True
    store: Literal["memory", "sqlite", "redis"] = "memory"
    store_ttl_seconds: int = 86400 * 3  # 3 days persistence in Redis
    task_list_limit: int = 500  # max tasks returned from store
    celery_app: str = ""

    @classmethod
    def from_env(cls, celery_app: str = "") -> OpsConfig:
        host = os.getenv("CELERY_OPS_HOST", "0.0.0.0")
        port = int(os.getenv("CELERY_OPS_PORT", "9800"))
        ui = os.getenv("CELERY_OPS_UI", "1").lower() in ("1", "true", "yes")
        store = os.getenv("CELERY_OPS_STORE", "memory").lower()
        if store not in ("memory", "sqlite", "redis"):
            store = "memory"
        ttl = int(os.getenv("CELERY_OPS_STORE_TTL", str(86400 * 3)))
        limit = int(os.getenv("CELERY_OPS_TASK_LIST_LIMIT", "500"))
        return cls(
            host=host,
            port=port,
            ui_enabled=ui,
            store=store,
            store_ttl_seconds=ttl,
            task_list_limit=limit,
            celery_app=celery_app,
        )
