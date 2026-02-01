"""
Celery tasks for feedback_analysis.

Autodiscover loads this module; tasks are defined in services.task_service.
Import here so they are registered with the Celery app.
"""

from .services.task_service import process_feedback_task  # noqa: F401

__all__ = ("process_feedback_task",)
