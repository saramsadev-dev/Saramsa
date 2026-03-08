from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from authentication.models import PasswordResetToken, RegistrationOtp, UserAccount
from feedback_analysis.models import (
    Analysis,
    CommentExtraction,
    IngestionSchedule,
    Insight,
    InsightReview,
    InsightRule,
    Taxonomy,
    Upload,
    UsageRecord,
    UserData,
)
from integrations.models import IntegrationAccount, Project, ProjectRole
from work_items.models import UserStory, WorkItemQualityRule


def _parse_dt(value: Any):
    if not value:
        return timezone.now()
    if isinstance(value, datetime):
        return value
    try:
        dt = datetime.fromisoformat(str(value))
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return dt
    except Exception:
        return timezone.now()


class Command(BaseCommand):
    help = "Import Cosmos JSON exports into PostgreSQL Django models."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Read and map documents without writing DB rows.")
        parser.add_argument(
            "--source-dir",
            default=str(Path("backend") / "data_exports" / "cosmos"),
            help="Directory containing exported container files (*.json or *.ndjson).",
        )

    def handle(self, *args, **options):
        self.source_dir = Path(options["source_dir"]).resolve()
        if not self.source_dir.exists():
            raise CommandError(f"Source directory not found: {self.source_dir}")
        dry_run = options["dry_run"]
        counts = defaultdict(int)

        with transaction.atomic():
            counts["users"] = self._migrate_users(dry_run)
            counts["password_resets"] = self._migrate_password_resets(dry_run)
            counts["registration_otps"] = self._migrate_registration_otps(dry_run)
            counts["projects"] = self._migrate_projects(dry_run)
            counts["project_roles"] = self._migrate_project_roles(dry_run)
            counts["integrations"] = self._migrate_integrations(dry_run)
            counts["analysis"] = self._migrate_analysis(dry_run)
            counts["uploads"] = self._migrate_uploads(dry_run)
            counts["user_data"] = self._migrate_user_data(dry_run)
            counts["insights"] = self._migrate_insights(dry_run)
            counts["taxonomies"] = self._migrate_taxonomies(dry_run)
            counts["usage"] = self._migrate_usage(dry_run)
            counts["comment_extractions"] = self._migrate_comment_extractions(dry_run)
            counts["insight_rules"] = self._migrate_insight_rules(dry_run)
            counts["insight_reviews"] = self._migrate_insight_reviews(dry_run)
            counts["ingestion_schedules"] = self._migrate_ingestion_schedules(dry_run)
            counts["user_stories"] = self._migrate_user_stories(dry_run)
            counts["work_item_quality_rules"] = self._migrate_work_item_quality_rules(dry_run)
            if dry_run:
                transaction.set_rollback(True)

        for k, v in counts.items():
            self.stdout.write(self.style.SUCCESS(f"{k}: {v}"))

    def _read(self, container: str) -> List[Dict[str, Any]]:
        json_path = self.source_dir / f"{container}.json"
        ndjson_path = self.source_dir / f"{container}.ndjson"

        if json_path.exists():
            with json_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                return data["items"]
            return []

        if ndjson_path.exists():
            rows: List[Dict[str, Any]] = []
            with ndjson_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rows.append(json.loads(line))
            return rows

        self.stdout.write(self.style.WARNING(f"Missing export for container '{container}' in {self.source_dir}"))
        return []

    def _migrate_users(self, dry_run: bool) -> int:
        rows = self._read("users")
        models = []
        for d in rows:
            if d.get("type") and d.get("type") != "user":
                continue
            models.append(
                UserAccount(
                    id=str(d["id"]),
                    username=d.get("username") or str(d["id"]),
                    email=d.get("email") or f"{d['id']}@local.invalid",
                    password=d.get("password", ""),
                    first_name=d.get("first_name", ""),
                    last_name=d.get("last_name", ""),
                    is_active=d.get("is_active", True),
                    is_staff=d.get("is_staff", False),
                    date_joined=_parse_dt(d.get("date_joined") or d.get("createdAt")),
                    profile=d.get("profile") or {},
                    company_name=d.get("company_name", ""),
                    company_url=d.get("company_url", ""),
                    avatar_url=d.get("avatar_url", ""),
                    created_at=_parse_dt(d.get("createdAt")),
                    updated_at=_parse_dt(d.get("updatedAt")),
                )
            )
        if not dry_run:
            UserAccount.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_password_resets(self, dry_run: bool) -> int:
        rows = self._read("password_resets")
        models = [
            PasswordResetToken(
                id=str(d["id"]),
                email=d.get("email", ""),
                token=d.get("token", ""),
                expires_at=_parse_dt(d.get("expires_at")),
                used=d.get("used", False),
                used_at=_parse_dt(d.get("used_at")) if d.get("used_at") else None,
                created_at=_parse_dt(d.get("created_at") or d.get("createdAt")),
                updated_at=_parse_dt(d.get("updated_at") or d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            PasswordResetToken.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_registration_otps(self, dry_run: bool) -> int:
        rows = self._read("registration_otps")
        models = [
            RegistrationOtp(
                id=str(d["id"]),
                email=d.get("email", ""),
                otp_hash=d.get("otp_hash", ""),
                expires_at=_parse_dt(d.get("expires_at")),
                attempts=int(d.get("attempts", 0)),
                max_attempts=int(d.get("max_attempts", 5)),
                send_count=int(d.get("send_count", 1)),
                last_sent_at=_parse_dt(d.get("last_sent_at")),
                used=d.get("used", False),
                used_at=_parse_dt(d.get("used_at")) if d.get("used_at") else None,
                created_at=_parse_dt(d.get("created_at") or d.get("createdAt")),
                updated_at=_parse_dt(d.get("updated_at") or d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            RegistrationOtp.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_projects(self, dry_run: bool) -> int:
        rows = [r for r in self._read("projects") if r.get("type") in (None, "project")]
        models = [
            Project(
                id=str(d["id"]),
                user_id=str(d.get("userId")) if d.get("userId") else None,
                name=d.get("name", ""),
                description=d.get("description", ""),
                status=d.get("status", "active"),
                external_links=d.get("externalLinks") or [],
                metadata=d,
                last_analysis_id=d.get("lastAnalysisId", ""),
                last_analyzed_at=_parse_dt(d.get("lastAnalyzedAt")) if d.get("lastAnalyzedAt") else None,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            Project.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_project_roles(self, dry_run: bool) -> int:
        rows = self._read("project_roles")
        models = [
            ProjectRole(
                id=str(d.get("id") or f"role:{d.get('projectId')}:{d.get('userId')}"),
                project_id=str(d.get("projectId")),
                user_id=str(d.get("userId")),
                role=d.get("role", "viewer"),
                actor_id=str(d.get("actorId") or ""),
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows if d.get("projectId") and d.get("userId")
        ]
        if not dry_run:
            ProjectRole.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_integrations(self, dry_run: bool) -> int:
        rows = [r for r in self._read("integrations") if r.get("type") in (None, "integration_account")]
        models = [
            IntegrationAccount(
                id=str(d["id"]),
                user_id=str(d.get("userId")) if d.get("userId") else None,
                provider=d.get("provider", ""),
                type=d.get("type", "integration_account"),
                account_name=d.get("account_name", d.get("name", "")),
                credentials=d.get("credentials") or {},
                config=d,
                is_active=d.get("is_active", True),
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            IntegrationAccount.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_analysis(self, dry_run: bool) -> int:
        rows = self._read("analysis")
        models = [
            Analysis(
                id=str(d["id"]),
                project_id=str(d.get("projectId")) if d.get("projectId") else None,
                user_id=str(d.get("userId")) if d.get("userId") else None,
                type=d.get("type", "analysis"),
                analysis_type=d.get("analysis_type", ""),
                quarter=d.get("quarter", ""),
                result=d.get("result") or {},
                comments=d.get("comments") or [],
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            Analysis.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_uploads(self, dry_run: bool) -> int:
        rows = self._read("uploads")
        models = [
            Upload(
                id=str(d["id"]),
                user_id=str(d.get("userId")) if d.get("userId") else None,
                project_id=str(d.get("projectId")) if d.get("projectId") else None,
                type=d.get("type", "upload"),
                filename=d.get("filename", ""),
                content_type=d.get("content_type", ""),
                status=d.get("status", "uploaded"),
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            Upload.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_user_data(self, dry_run: bool) -> int:
        rows = self._read("user_data")
        models = [
            UserData(
                id=str(d["id"]),
                user_id=str(d.get("userId")) if d.get("userId") else None,
                project_id=str(d.get("projectId")) if d.get("projectId") else None,
                type=d.get("type", "user_data"),
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            UserData.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_insights(self, dry_run: bool) -> int:
        rows = self._read("insights")
        models = [
            Insight(
                id=str(d["id"]),
                user_id=str(d.get("userId")) if d.get("userId") else None,
                project_id=str(d.get("projectId")) if d.get("projectId") else None,
                type=d.get("type", "insight"),
                analysis_type=d.get("analysis_type", ""),
                analysis_date=_parse_dt(d.get("analysis_date")) if d.get("analysis_date") else None,
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            Insight.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_taxonomies(self, dry_run: bool) -> int:
        rows = self._read("taxonomies")
        models = [
            Taxonomy(
                id=str(d["id"]),
                project_id=str(d.get("projectId")) if d.get("projectId") else None,
                type=d.get("type", "taxonomy"),
                version=int(d.get("version", 1) or 1),
                status=d.get("status", "active"),
                is_pinned=bool(d.get("is_pinned", False)),
                taxonomy=d.get("taxonomy") or {},
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            Taxonomy.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_usage(self, dry_run: bool) -> int:
        rows = self._read("usage")
        models = [
            UsageRecord(
                id=str(d["id"]),
                project_id=str(d.get("projectId")) if d.get("projectId") else None,
                user_id=str(d.get("userId")) if d.get("userId") else None,
                type=d.get("type", "usage"),
                endpoint=d.get("endpoint", ""),
                count=int(d.get("count", 0) or 0),
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            UsageRecord.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_comment_extractions(self, dry_run: bool) -> int:
        rows = self._read("comment_extractions")
        models = [
            CommentExtraction(
                id=str(d["id"]),
                project_id=str(d.get("projectId")) if d.get("projectId") else None,
                user_id=str(d.get("userId")) if d.get("userId") else None,
                type=d.get("type", "comment_extraction"),
                source_type=d.get("source_type", ""),
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            CommentExtraction.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_insight_rules(self, dry_run: bool) -> int:
        rows = self._read("insight_rules")
        models = [
            InsightRule(
                id=str(d.get("id") or f"insight_rule:{d.get('projectId')}"),
                project_id=str(d.get("projectId")),
                type=d.get("type", "insight_rule"),
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows if d.get("projectId")
        ]
        if not dry_run:
            InsightRule.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_insight_reviews(self, dry_run: bool) -> int:
        rows = self._read("insight_reviews")
        models = [
            InsightReview(
                id=str(d.get("id") or f"insight_review:{d.get('projectId')}:{idx}"),
                project_id=str(d.get("projectId")),
                type=d.get("type", "insight_review"),
                status=d.get("status", ""),
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for idx, d in enumerate(rows) if d.get("projectId")
        ]
        if not dry_run:
            InsightReview.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_ingestion_schedules(self, dry_run: bool) -> int:
        rows = self._read("ingestion_schedules")
        models = [
            IngestionSchedule(
                id=str(d["id"]),
                project_id=str(d.get("projectId")) if d.get("projectId") else None,
                type=d.get("type", "ingestion_schedule"),
                status=d.get("status", "active"),
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            IngestionSchedule.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_user_stories(self, dry_run: bool) -> int:
        rows = self._read("user_stories")
        models = [
            UserStory(
                id=str(d["id"]),
                project_id=str(d.get("projectId")) if d.get("projectId") else None,
                user_id=str(d.get("userId")) if d.get("userId") else None,
                type=d.get("type", "user_story"),
                status=d.get("status", ""),
                title=d.get("title", ""),
                description=d.get("description", ""),
                generated_at=_parse_dt(d.get("generated_at")) if d.get("generated_at") else None,
                work_items=d.get("work_items") or [],
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows
        ]
        if not dry_run:
            UserStory.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)

    def _migrate_work_item_quality_rules(self, dry_run: bool) -> int:
        rows = self._read("work_item_quality_rules")
        models = [
            WorkItemQualityRule(
                id=str(d.get("id") or f"work_item_quality:{d.get('projectId')}"),
                project_id=str(d.get("projectId")),
                type=d.get("type", "work_item_quality_rule"),
                payload=d,
                created_at=_parse_dt(d.get("createdAt")),
                updated_at=_parse_dt(d.get("updatedAt")),
            )
            for d in rows if d.get("projectId")
        ]
        if not dry_run:
            WorkItemQualityRule.objects.bulk_create(models, ignore_conflicts=True, batch_size=500)
        return len(models)


