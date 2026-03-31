"""
Celery inspect API wrapper.

Uses only Celery introspection. No app DB. Best-effort.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from .model import QueueSummary, WorkerSummary

if TYPE_CHECKING:
    from celery import Celery

logger = logging.getLogger(__name__)


def get_workers(app: Celery) -> list[WorkerSummary]:
    """List workers via inspect active_reserved_stats (or ping + stats)."""
    out: list[WorkerSummary] = []
    i = app.control.inspect()
    try:
        stats = i.stats() or {}
        active = i.active() or {}
        reserved = i.reserved() or {}
        for name, s in stats.items():
            w = WorkerSummary(
                name=name,
                status="online",
                pid=s.get("pid"),
                processed=sum(s.get("total", {}).values()) if isinstance(s.get("total"), dict) else 0,
            )
            w.active = len(active.get(name) or [])
            w.active += len(reserved.get(name) or [])
            queues = s.get("queues") or []
            w.queues = [q if isinstance(q, str) else str(q) for q in queues]
            out.append(w)
    except Exception as e:
        logger.debug("Celery Ops: inspect workers failed: %s", e)
    return out


def get_queues(app: Celery) -> list[QueueSummary]:
    """List queues via inspect active_queues. Length best-effort when broker supports it."""
    out: list[QueueSummary] = []
    i = app.control.inspect()
    try:
        aq = i.active_queues() or {}
        seen: set[str] = set()
        for worker_queues in aq.values():
            for q in worker_queues or []:
                name = q.get("name") if isinstance(q, dict) else str(q)
                if name and name not in seen:
                    seen.add(name)
                    out.append(QueueSummary(name=name, length=0))
    except Exception as e:
        logger.debug("Celery Ops: inspect queues failed: %s", e)
    return out


def get_active_tasks(app: Celery) -> list[dict[str, Any]]:
    """Raw active task list from inspect. For merging with store."""
    i = app.control.inspect()
    try:
        active = i.active() or {}
        rows: list[dict[str, Any]] = []
        for worker, tasks in active.items():
            for t in tasks or []:
                t = dict(t) if isinstance(t, dict) else {}
                t["worker"] = worker
                t["state"] = "STARTED"
                rows.append(t)
        return rows
    except Exception as e:
        logger.debug("Celery Ops: inspect active failed: %s", e)
        return []


def get_live_tasks(app: Celery) -> list[dict[str, Any]]:
    """Running + reserved tasks from inspect, as API-shaped dicts. Used to show Runs even without events."""
    out: list[dict[str, Any]] = []
    i = app.control.inspect()
    try:
        active = i.active() or {}
        reserved = i.reserved() or {}
        for worker, tasks in active.items():
            for t in (tasks or []):
                t = dict(t) if isinstance(t, dict) else {}
                tid = t.get("id") or t.get("task_id")
                if not tid:
                    continue
                name = t.get("name") or t.get("task") or "unknown"
                out.append({
                    "task_id": str(tid),
                    "task_name": name,
                    "state": "STARTED",
                    "worker": worker,
                    "retries": int(t.get("retries") or 0),
                    "runtime_ms": None,
                })
        for worker, tasks in reserved.items():
            for t in (tasks or []):
                t = dict(t) if isinstance(t, dict) else {}
                tid = t.get("id") or t.get("task_id")
                if not tid:
                    continue
                name = t.get("name") or t.get("task") or "unknown"
                out.append({
                    "task_id": str(tid),
                    "task_name": name,
                    "state": "RECEIVED",
                    "worker": worker,
                    "retries": int(t.get("retries") or 0),
                    "runtime_ms": None,
                })
    except Exception as e:
        logger.debug("Celery Ops: get_live_tasks failed: %s", e)
    return out


def get_registered_task_names(app: Celery) -> list[str]:
    """List all registered task names (tasks we can run). Excludes celery.* built-ins."""
    names: set[str] = set()
    
    # 1. From app task registry (autodiscover loads app.tasks modules)
    try:
        for key in app.tasks.keys():
            if isinstance(key, str) and not key.startswith("celery."):
                names.add(key)
    except Exception as e:
        logger.debug("Celery Ops: app.tasks registry failed: %s", e)
    
    # 2. From workers via inspect (when workers are running)
    try:
        reg = app.control.inspect().registered() or {}
        for task_list in reg.values():
            for t in task_list or []:
                if isinstance(t, str) and not t.startswith("celery."):
                    names.add(t)
    except Exception as e:
        logger.debug("Celery Ops: inspect registered failed: %s", e)
    
    return sorted(names)


def get_running_queued_by_task(app: Celery) -> tuple[dict[str, int], dict[str, int]]:
    """Aggregate running and queued counts by task name from inspect. Returns (running_by_name, queued_by_name)."""
    running: dict[str, int] = {}
    queued: dict[str, int] = {}
    i = app.control.inspect()
    try:
        active = i.active() or {}
        reserved = i.reserved() or {}
        for tasks in active.values():
            for t in tasks or []:
                name = (t.get("name") or t.get("task") or "unknown") if isinstance(t, dict) else "unknown"
                running[name] = running.get(name, 0) + 1
        for tasks in reserved.values():
            for t in tasks or []:
                name = (t.get("name") or t.get("task") or "unknown") if isinstance(t, dict) else "unknown"
                queued[name] = queued.get(name, 0) + 1
    except Exception as e:
        logger.debug("Celery Ops: running/queued aggregate failed: %s", e)
    return running, queued
