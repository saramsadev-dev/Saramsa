"""
Celery tasks for feedback analysis.
"""

import logging
from celery import shared_task

from .services.ingestion_schedule_service import get_ingestion_schedule_service

logger = logging.getLogger(__name__)


@shared_task(name="feedback_analysis.run_scheduled_ingestions")
def run_scheduled_ingestions():
    service = get_ingestion_schedule_service()
    results = service.run_due_schedules()
    logger.info(
        "Scheduled ingestion run completed: due=%s started=%s skipped=%s",
        results.get("due"),
        results.get("started"),
        results.get("skipped"),
    )
    return results
