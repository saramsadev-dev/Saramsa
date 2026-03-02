"""
Run due ingestion schedules (for cron/worker usage).
"""

import logging
from django.core.management.base import BaseCommand

from feedback_analysis.services.ingestion_schedule_service import get_ingestion_schedule_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run due ingestion schedules and enqueue analysis tasks."

    def handle(self, *args, **options):
        service = get_ingestion_schedule_service()
        results = service.run_due_schedules()
        self.stdout.write(
            f"Scheduled ingestion run completed: "
            f"due={results.get('due')} started={results.get('started')} skipped={results.get('skipped')}"
        )
        logger.info(
            "Scheduled ingestion run completed via management command: due=%s started=%s skipped=%s",
            results.get("due"),
            results.get("started"),
            results.get("skipped"),
        )
