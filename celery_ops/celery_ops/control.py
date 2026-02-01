"""
Limited operational controls: revoke (cancel), retry, requeue.

All best-effort and cooperative. Cancel is non-guaranteed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from celery import Celery

from .model import TaskSummary
from .store import OpsStore

logger = logging.getLogger(__name__)


def revoke_task(app: Celery, task_id: str, terminate: bool = True) -> dict[str, Any]:
    """
    Best-effort task cancel (revoke).

    Cooperative and non-guaranteed: workers must honour revoke.
    terminate=True sends SIGTERM; worker must support it.
    """
    try:
        app.control.revoke(task_id, terminate=terminate, signal="SIGTERM")
        return {"ok": True, "task_id": task_id, "message": "Revoke sent (best-effort, cooperative)"}
    except Exception as e:
        logger.warning("Celery Ops: revoke %s failed: %s", task_id, e)
        return {"ok": False, "task_id": task_id, "error": str(e)}


def retry_task(
    app: Celery,
    store: OpsStore,
    task_id: str,
    queue: Optional[str] = None,
) -> dict[str, Any]:
    """
    Retry (requeue) task with same arguments. Best-effort.

    Uses args/kwargs from event store when available. Not all tasks are retriable.
    """
    t = store.get(task_id)
    if not t:
        return {"ok": False, "task_id": task_id, "error": "Task not found in ops store"}
    if not t.task_name:
        return {"ok": False, "task_id": task_id, "error": "Task name unknown"}
    send_queue = queue or t.queue
    try:
        celery_task = app.tasks.get(t.task_name)
        if not celery_task:
            return {"ok": False, "task_id": task_id, "error": f"Task {t.task_name!r} not registered"}
        args = t._args or ()
        kwargs = t._kwargs or {}
        r = celery_task.apply_async(args=args, kwargs=kwargs, queue=send_queue)
        return {"ok": True, "task_id": task_id, "new_task_id": r.id, "message": "Retry sent (best-effort)"}
    except Exception as e:
        logger.warning("Celery Ops: retry %s failed: %s", task_id, e)
        return {"ok": False, "task_id": task_id, "error": str(e)}
