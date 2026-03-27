"""
One-time data migration: extract embedded JSON work items from
UserStory.work_items into the new WorkItemCandidate table.

Usage:
    python manage.py migrate_work_items_json          # dry-run
    python manage.py migrate_work_items_json --apply   # persist
"""

import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from work_items.models import UserStory, WorkItemCandidate
from work_items.repositories import _dict_to_candidate_kwargs

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate embedded JSON work items into the work_item_candidates table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Actually write to the database (default is dry-run).",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        mode = "APPLY" if apply else "DRY-RUN"
        self.stdout.write(f"\n=== Migrate Work Items JSON -> Table ({mode}) ===\n")

        stories = UserStory.objects.exclude(work_items=[]).exclude(work_items__isnull=True)
        total_stories = stories.count()
        self.stdout.write(f"Found {total_stories} UserStory rows with embedded work_items.\n")

        total_created = 0
        total_skipped = 0
        total_errors = 0

        for story in stories.iterator():
            items = story.work_items or []
            if not items:
                continue

            project_id = str(story.project_id) if story.project_id else ""
            if not project_id:
                self.stdout.write(
                    self.style.WARNING(f"  Skipping story {story.id}: no project_id")
                )
                total_skipped += len(items)
                continue

            self.stdout.write(f"  Story {story.id}: {len(items)} items")
            candidates = []
            for d in items:
                item_id = d.get("id") or d.get("work_item_id")
                if not item_id:
                    total_skipped += 1
                    continue

                if WorkItemCandidate.objects.filter(id=str(item_id)).exists():
                    total_skipped += 1
                    continue

                try:
                    kwargs = _dict_to_candidate_kwargs(d, project_id, story)
                    c = WorkItemCandidate(**kwargs)
                    try:
                        c.id = item_id
                    except (ValueError, AttributeError):
                        pass
                    candidates.append(c)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"    Error building candidate from item {item_id}: {e}")
                    )
                    total_errors += 1

            if candidates and apply:
                try:
                    with transaction.atomic():
                        created = WorkItemCandidate.objects.bulk_create(
                            candidates, ignore_conflicts=True,
                        )
                        total_created += len(created)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"    Bulk create failed for story {story.id}: {e}")
                    )
                    total_errors += 1
            elif candidates:
                total_created += len(candidates)

        self.stdout.write(f"\n--- Summary ({mode}) ---")
        self.stdout.write(f"  Created:  {total_created}")
        self.stdout.write(f"  Skipped:  {total_skipped}")
        self.stdout.write(f"  Errors:   {total_errors}")

        if not apply:
            self.stdout.write(
                self.style.SUCCESS("\nDry-run complete. Re-run with --apply to persist.\n")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\nMigration complete.\n")
            )
