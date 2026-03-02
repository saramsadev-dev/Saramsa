"""
Celery task to run scheduled ingestions.
"""

from celery import shared_task
import logging
from .ingestion_schedule_service import get_ingestion_schedule_service

logger = logging.getLogger(__name__)


@shared_task(name="feedback_analysis.run_scheduled_ingestions")
def run_scheduled_ingestions():
    service = get_ingestion_schedule_service()
    schedules = service.get_due_schedules()
    if not schedules:
        return {"status": "no_schedules"}

    processed = 0
    for schedule in schedules:
        if service.run_schedule(schedule):
            processed += 1

    return {"status": "ok", "processed": processed}
