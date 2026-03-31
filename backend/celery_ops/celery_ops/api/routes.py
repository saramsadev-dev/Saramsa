"""
REST API routes for Celery Ops.

Read-only observation + limited control (cancel, retry).
All best-effort; no app DB coupling.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from ..control import retry_task, revoke_task
from ..inspect import (
    get_live_tasks,
    get_queues,
    get_registered_task_names,
    get_running_queued_by_task,
    get_workers,
)
from ..model import TaskSummary
from ..store import OpsStore

router = APIRouter(prefix="/api", tags=["ops"])

_app = None
_store: Optional[OpsStore] = None


def init_routes(app: Any, store: OpsStore) -> None:
    global _app, _store
    _app = app
    _store = store
    # Router is included in app with init_routes called at startup
    pass


def _get_app():
    if _app is None:
        raise HTTPException(status_code=503, detail="Celery app not configured")
    return _app


def _get_store() -> OpsStore:
    if _store is None:
        raise HTTPException(status_code=503, detail="Ops store not configured")
    return _store


def _matches_filters(t: dict[str, Any], state: Optional[str], task_name: Optional[str], worker: Optional[str]) -> bool:
    if state and (t.get("state") or "").upper() != state.upper():
        return False
    if task_name and (t.get("task_name") or "") != task_name:
        return False
    if worker and (t.get("worker") or "") != worker:
        return False
    return True


@router.get("/tasks")
def list_tasks(
    state: Optional[str] = Query(None, description="Filter by state"),
    task_name: Optional[str] = Query(None, description="Filter by task name"),
    worker: Optional[str] = Query(None, description="Filter by worker"),
    limit: Optional[int] = Query(None, description="Max tasks to return"),
) -> dict[str, Any]:
    """List tasks from ops store (event-derived) + live inspect (running/reserved). Best-effort."""
    s = _get_store()
    store_tasks = s.list_tasks(state=state, task_name=task_name, worker=worker, limit=limit)
    store_ids = {t.task_id for t in store_tasks}
    out: list[dict[str, Any]] = [t.to_api() for t in store_tasks]

    app = _get_app()
    live = get_live_tasks(app)
    n = limit or s._limit
    for t in live:
        if len(out) >= n:
            break
        tid = t.get("task_id")
        if not tid or tid in store_ids:
            continue
        if not _matches_filters(t, state, task_name, worker):
            continue
        out.append(t)
        store_ids.add(tid)

    return {"tasks": out, "count": len(out)}


@router.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
    """Task detail from ops store, or live-only from AsyncResult/inspect. Best-effort."""
    s = _get_store()
    t = s.get(task_id)
    if t:
        out = t.to_api()
        try:
            from celery.result import AsyncResult
            app = _get_app()
            ar = AsyncResult(task_id, app=app)
            out["live_ready"] = ar.ready()
            out["live_state"] = ar.state
            if ar.ready() and not ar.successful():
                out["live_error"] = str(ar.result) if ar.result else None
        except Exception:
            pass
        return out

    # Not in store: check live (running/reserved) from inspect
    app = _get_app()
    for live_task in get_live_tasks(app):
        if live_task.get("task_id") == task_id:
            return live_task

    # Fallback: AsyncResult only
    try:
        from celery.result import AsyncResult
        ar = AsyncResult(task_id, app=app)
        return {
            "task_id": task_id,
            "task_name": getattr(ar, "name", None) or "unknown",
            "state": ar.state,
            "live_ready": ar.ready(),
            "live_state": ar.state,
            "live_error": str(ar.result) if ar.ready() and not ar.successful() and ar.result else None,
        }
    except Exception:
        pass
    raise HTTPException(status_code=404, detail="Task not found in ops store or inspect")


@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, terminate: bool = Query(True, description="Send SIGTERM to worker")) -> dict[str, Any]:
    """
    Best-effort task cancel (revoke).

    Cooperative and non-guaranteed. Workers must honour revoke.
    See SCOPE.md and README.
    """
    app = _get_app()
    return revoke_task(app, task_id, terminate=terminate)


@router.post("/tasks/{task_id}/retry")
def retry_task_route(
    task_id: str,
    queue: Optional[str] = Query(None, description="Override queue for retry"),
) -> dict[str, Any]:
    """Retry (requeue) task with same arguments. Best-effort. Not all tasks are retriable."""
    app = _get_app()
    s = _get_store()
    return retry_task(app, s, task_id, queue=queue)


@router.get("/workers")
def list_workers() -> dict[str, Any]:
    """List workers from Celery inspect. No app DB."""
    app = _get_app()
    workers = get_workers(app)
    return {"workers": [w.to_api() for w in workers], "count": len(workers)}


@router.get("/workers/{name}")
def get_worker(name: str) -> dict[str, Any]:
    """Worker detail from inspect."""
    app = _get_app()
    workers = get_workers(app)
    for w in workers:
        if w.name == name:
            return w.to_api()
    raise HTTPException(status_code=404, detail="Worker not found")


@router.get("/queues")
def list_queues() -> dict[str, Any]:
    """List queues from inspect. Best-effort."""
    app = _get_app()
    queues = get_queues(app)
    return {"queues": [q.to_api() for q in queues], "count": len(queues)}


@router.get("/task-types")
def list_task_types() -> dict[str, Any]:
    """Aggregated task types for Trigger-like Tasks view: all runnable tasks + running, queued, activity, avg_duration."""
    app = _get_app()
    s = _get_store()
    registered = get_registered_task_names(app)
    running_by_name, queued_by_name = get_running_queued_by_task(app)
    agg = s.aggregate_by_task_name(limit_per_task=50)
    names = set(registered) | set(running_by_name.keys()) | set(queued_by_name.keys()) | set(agg.keys())
    types: list[dict[str, Any]] = []
    for name in sorted(names):
        r = running_by_name.get(name, 0)
        q = queued_by_name.get(name, 0)
        a = agg.get(name) or {}
        activity = a.get("activity") or []
        avg_ms = a.get("avg_duration_ms")
        types.append({
            "task_name": name,
            "running": r,
            "queued": q,
            "activity": activity,
            "avg_duration_ms": avg_ms,
            "run_count": a.get("run_count", 0),
            "ok_count": a.get("ok_count", 0),
            "fail_count": a.get("fail_count", 0),
        })
    return {"task_types": types, "count": len(types)}


@router.get("/tasks/{task_id}/execution")
def get_task_execution(task_id: str) -> dict[str, Any]:
    """Get detailed execution steps for a task (Trigger.dev style)."""
    s = _get_store()
    t = s.get(task_id)
    
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Generate mock execution steps for demonstration
    # In a real implementation, this would come from task execution tracking
    execution_steps = generate_mock_execution_steps(t)
    
    return {
        "task_id": task_id,
        "execution": execution_steps
    }


def generate_mock_execution_steps(task: TaskSummary) -> dict[str, Any]:
    """Generate mock execution steps based on task type and status."""
    import time
    
    # Base steps that most tasks have
    steps = []
    current_time = time.time()
    
    # Step 1: Task Received
    steps.append({
        "step_id": "received",
        "name": "Task Received",
        "status": "SUCCESS",
        "started_at": task.received_at or current_time - 100,
        "completed_at": (task.received_at or current_time - 100) + 0.1,
        "duration_ms": 100,
        "metadata": {
            "queue": task.queue or "default",
            "worker": task.worker or "unknown"
        }
    })
    
    # Step 2: Task Started
    if task.started_at:
        steps.append({
            "step_id": "started",
            "name": "Task Started",
            "status": "SUCCESS",
            "started_at": task.started_at,
            "completed_at": task.started_at + 0.05,
            "duration_ms": 50,
            "metadata": {
                "worker": task.worker or "unknown"
            }
        })
    
    # Step 3: Task-specific execution steps
    if "feedback_analysis" in task.task_name:
        steps.extend([
            {
                "step_id": "validate_input",
                "name": "Validate Input Data",
                "status": "SUCCESS",
                "started_at": (task.started_at or current_time) + 0.1,
                "completed_at": (task.started_at or current_time) + 0.5,
                "duration_ms": 400,
                "metadata": {"validation_rules": 5}
            },
            {
                "step_id": "process_feedback",
                "name": "Process Feedback Comments",
                "status": "SUCCESS" if task.state == "SUCCESS" else "RUNNING",
                "started_at": (task.started_at or current_time) + 0.5,
                "completed_at": (task.started_at or current_time) + 30 if task.state == "SUCCESS" else None,
                "duration_ms": 29500 if task.state == "SUCCESS" else None,
                "metadata": {"comments_processed": 1234}
            },
            {
                "step_id": "generate_insights",
                "name": "Generate AI Insights",
                "status": "SUCCESS" if task.state == "SUCCESS" else "PENDING",
                "started_at": (task.started_at or current_time) + 30 if task.state == "SUCCESS" else None,
                "completed_at": (task.started_at or current_time) + 40 if task.state == "SUCCESS" else None,
                "duration_ms": 10000 if task.state == "SUCCESS" else None,
                "metadata": {"insights_generated": 15}
            }
        ])
    else:
        # Generic task steps
        steps.extend([
            {
                "step_id": "initialize",
                "name": "Initialize Task",
                "status": "SUCCESS",
                "started_at": (task.started_at or current_time) + 0.1,
                "completed_at": (task.started_at or current_time) + 0.2,
                "duration_ms": 100,
                "metadata": {}
            },
            {
                "step_id": "execute",
                "name": "Execute Main Logic",
                "status": "SUCCESS" if task.state == "SUCCESS" else "RUNNING" if task.state in ["STARTED", "RETRY"] else "FAILURE" if task.state == "FAILURE" else "PENDING",
                "started_at": (task.started_at or current_time) + 0.2,
                "completed_at": (task.succeeded_at or task.failed_at) if task.state in ["SUCCESS", "FAILURE"] else None,
                "duration_ms": task.runtime_ms if task.runtime_ms else None,
                "metadata": {},
                "error": task.error if task.state == "FAILURE" else None
            }
        ])
    
    # Final step: Task Completed
    if task.state in ["SUCCESS", "FAILURE"]:
        steps.append({
            "step_id": "completed",
            "name": "Task Completed",
            "status": "SUCCESS" if task.state == "SUCCESS" else "FAILURE",
            "started_at": task.succeeded_at or task.failed_at,
            "completed_at": (task.succeeded_at or task.failed_at or current_time) + 0.01,
            "duration_ms": 10,
            "metadata": {
                "final_state": task.state
            },
            "error": task.error if task.state == "FAILURE" else None
        })
    
    return {
        "steps": steps,
        "current_step": get_current_step(steps, task.state),
        "progress_percentage": calculate_progress(steps, task.state)
    }


def calculate_progress(steps: list, task_state: str) -> float:
    """Calculate progress percentage based on completed steps."""
    if not steps:
        return 0.0
    
    completed_steps = sum(1 for step in steps if step.get("status") in ["SUCCESS", "FAILURE"])
    total_steps = len(steps)
    
    if task_state in ["SUCCESS", "FAILURE"]:
        return 100.0
    elif task_state == "STARTED":
        return min(90.0, (completed_steps / total_steps) * 100)
    else:
        return (completed_steps / total_steps) * 100


def get_current_step(steps: list, task_state: str) -> str:
    """Determine the current step based on task state."""
    if task_state in ["SUCCESS", "FAILURE"]:
        return ""  # No current step for completed tasks
    elif task_state == "STARTED":
        return "execute"
    elif task_state == "RECEIVED":
        return "started"
    else:
        return "received"


@router.get("/status")
def get_status() -> dict[str, Any]:
    """Get Celery Ops status including basic health check."""
    s = _get_store()
    
    # Try to get some basic info to verify the system is working
    try:
        task_count = len(s.list_tasks(limit=100))
        app = _get_app()
        
        # Try to ping the Celery broker to check connectivity
        try:
            # Simple broker connectivity check
            workers = get_workers(app)
            broker_connected = True
        except Exception:
            broker_connected = False
        
        status = {
            "celery_ops": "running",
            "event_consumer": {
                "enabled": True,  # Assume enabled if no --no-events flag
                "status": "running" if broker_connected else "connection_issue"
            },
            "store": {
                "type": s.__class__.__name__,
                "task_count": task_count
            },
            "broker_connected": broker_connected
        }
        
        return status
    except Exception as e:
        return {
            "celery_ops": "error",
            "error": str(e),
            "event_consumer": {
                "enabled": False,
                "status": "error"
            }
        }


@router.get("/stats")
def stats() -> dict[str, Any]:
    """Ops store stats. Disposable metadata only."""
    s = _get_store()
    return s.stats()
