"""
Ops-only task execution data model.

All fields are derived from Celery events and inspect APIs.
Disposable, non-authoritative. No app DB coupling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, List
from datetime import datetime


@dataclass
class ExecutionStep:
    """Individual step within a task execution."""
    
    step_id: str
    name: str
    status: str  # PENDING, RUNNING, SUCCESS, FAILURE, SKIPPED
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    sub_steps: List['ExecutionStep'] = field(default_factory=list)
    
    def to_api(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
            "sub_steps": [step.to_api() for step in self.sub_steps]
        }


@dataclass
class TaskExecution:
    """Detailed task execution with step-by-step tracking."""
    
    task_id: str
    task_name: str
    state: str
    steps: List[ExecutionStep] = field(default_factory=list)
    current_step: Optional[str] = None
    progress_percentage: float = 0.0
    
    def to_api(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "state": self.state,
            "steps": [step.to_api() for step in self.steps],
            "current_step": self.current_step,
            "progress_percentage": self.progress_percentage
        }


@dataclass
class TaskSummary:
    """Task-level metadata from events + optional inspect."""

    task_id: str
    task_name: str
    state: str  # PENDING, RECEIVED, STARTED, SUCCESS, FAILURE, REVOKED, RETRY, ...
    retries: int = 0
    runtime_ms: Optional[float] = None
    worker: Optional[str] = None
    queue: Optional[str] = None
    args_preview: str = ""
    kwargs_preview: str = ""
    traceback_preview: Optional[str] = None
    error: Optional[str] = None
    # Timestamps (epoch seconds, best-effort)
    received_at: Optional[float] = None
    started_at: Optional[float] = None
    succeeded_at: Optional[float] = None
    failed_at: Optional[float] = None
    # Enhanced execution tracking
    execution: Optional[TaskExecution] = None
    # For retry/requeue: store raw args/kwargs from events (best-effort)
    _args: Optional[tuple] = field(default=None, repr=False)
    _kwargs: Optional[dict] = field(default=None, repr=False)

    def to_api(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "state": self.state,
            "retries": self.retries,
            "runtime_ms": self.runtime_ms,
            "worker": self.worker,
            "queue": self.queue,
            "args_preview": self.args_preview,
            "kwargs_preview": self.kwargs_preview,
            "traceback_preview": self.traceback_preview,
            "error": self.error,
            "received_at": self.received_at,
            "started_at": self.started_at,
            "succeeded_at": self.succeeded_at,
            "failed_at": self.failed_at,
        }
        
        # Include execution details if available
        if self.execution:
            d["execution"] = self.execution.to_api()
            
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class WorkerSummary:
    """Worker metadata from inspect."""

    name: str
    status: str
    active: int = 0
    processed: int = 0
    pid: Optional[int] = None
    queues: list[str] = field(default_factory=list)

    def to_api(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "active": self.active,
            "processed": self.processed,
            "pid": self.pid,
            "queues": self.queues,
        }


@dataclass
class QueueSummary:
    """Queue metadata from inspect."""

    name: str
    length: int = 0

    def to_api(self) -> dict[str, Any]:
        return {"name": self.name, "length": self.length}
