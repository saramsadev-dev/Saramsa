from datetime import datetime
from typing import Any, Dict, List, Optional

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
from integrations.models import Project, ProjectRole
from work_items.models import UserStory, WorkItemQualityRule


def _now_iso() -> str:
    return timezone.now().isoformat()


def _as_dt(value: Any):
    if not value:
        return timezone.now()
    if isinstance(value, datetime):
        return value
    try:
        dt = datetime.fromisoformat(str(value))
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return dt
    except Exception as exc:
        raise ValueError(f"Invalid datetime value: {value!r}") from exc


class StorageService:
    """ORM-backed data service using Django ORM."""

    def __init__(self):
        self.is_enabled = True
        self.client = {"engine": "django-orm"}
        self.database = {"name": "postgresql"}
        self.containers = {
            "users": UserAccount,
            "password_resets": PasswordResetToken,
            "registration_otps": RegistrationOtp,
            "projects": Project,
            "project_roles": ProjectRole,
            "analysis": Analysis,
            "uploads": Upload,
            "user_data": UserData,
            "insights": Insight,
            "taxonomies": Taxonomy,
            "usage": UsageRecord,
            "comment_extractions": CommentExtraction,
            "ingestion_schedules": IngestionSchedule,
            "user_stories": UserStory,
            "insight_rules": InsightRule,
            "insight_reviews": InsightReview,
            "work_item_quality_rules": WorkItemQualityRule,
        }
        self._stats = {"queries": 0, "writes": 0}

    def _now(self):
        return _now_iso()

    def create_database_if_not_exists(self):
        return True

    def create_all_containers(self):
        return True

    def get_performance_stats(self):
        return dict(self._stats)

    def reset_stats(self):
        self._stats = {"queries": 0, "writes": 0}

    def get_container_stats(self):
        return {k: {"count": v.objects.count()} for k, v in self.containers.items()}

    def _doc(self, container: str, obj):
        if not obj:
            return None
        if hasattr(obj, "payload") and isinstance(obj.payload, dict):
            d = dict(obj.payload)
        elif hasattr(obj, "extra") and isinstance(obj.extra, dict):
            d = dict(obj.extra)
        else:
            d = {}
        d["id"] = str(obj.id)
        if hasattr(obj, "created_at") and obj.created_at:
            d.setdefault("createdAt", obj.created_at.isoformat())
        if hasattr(obj, "updated_at") and obj.updated_at:
            d.setdefault("updatedAt", obj.updated_at.isoformat())
        if hasattr(obj, "project_id"):
            d.setdefault("projectId", obj.project_id)
        if hasattr(obj, "user_id"):
            d.setdefault("userId", obj.user_id)
        if container == "users":
            d.update({
                "username": obj.username,
                "email": obj.email,
                "password": obj.password,
                "first_name": obj.first_name,
                "last_name": obj.last_name,
                "is_active": obj.is_active,
                "is_staff": obj.is_staff,
                "profile": obj.profile or {},
                "type": "user",
                "date_joined": obj.date_joined.isoformat() if obj.date_joined else None,
            })
        if container == "user_stories":
            d.update({
                "type": obj.type,
                "status": obj.status,
                "title": obj.title,
                "description": obj.description,
                "generated_at": obj.generated_at.isoformat() if obj.generated_at else None,
                "work_items": obj.work_items or [],
            })
        return d

    def get_document(self, container_name: str, item_id: str, partition_key: Optional[str] = None):
        model = self.containers.get(container_name)
        if not model:
            return None
        return self._doc(container_name, model.objects.filter(id=str(item_id)).first())

    def create_document(self, container_name: str, data: Dict[str, Any]):
        return self.update_document(container_name, str(data["id"]), str(data.get("projectId") or data.get("userId") or data["id"]), data)

    def update_document(self, container_name: str, item_id: str, partition_key: str, data: Dict[str, Any]):
        self._stats["writes"] += 1
        if container_name == "users":
            obj, _ = UserAccount.objects.update_or_create(
                id=str(item_id),
                defaults={
                    "username": data.get("username", str(item_id)),
                    "email": data.get("email", f"{item_id}@local.invalid"),
                    "password": data.get("password", ""),
                    "first_name": data.get("first_name", ""),
                    "last_name": data.get("last_name", ""),
                    "is_active": data.get("is_active", True),
                    "is_staff": data.get("is_staff", False),
                    "date_joined": _as_dt(data.get("date_joined") or data.get("createdAt")),
                    "profile": data.get("profile") or {},
                    "extra": data,
                    "updated_at": timezone.now(),
                },
            )
            return self._doc(container_name, obj)
        if container_name == "registration_otps":
            obj, _ = RegistrationOtp.objects.update_or_create(
                email=data.get("email", partition_key),
                defaults={
                    "id": str(item_id),
                    "otp_hash": data.get("otp_hash", ""),
                    "expires_at": _as_dt(data.get("expires_at")),
                    "attempts": int(data.get("attempts", 0)),
                    "max_attempts": int(data.get("max_attempts", 5)),
                    "send_count": int(data.get("send_count", 1)),
                    "last_sent_at": _as_dt(data.get("last_sent_at")),
                    "used": bool(data.get("used", False)),
                    "used_at": _as_dt(data.get("used_at")) if data.get("used_at") else None,
                    "extra": data,
                    "updated_at": timezone.now(),
                },
            )
            return self._doc(container_name, obj)
        if container_name == "projects":
            obj, _ = Project.objects.update_or_create(
                id=str(item_id),
                defaults={
                    "user_id": str(data.get("userId")) if data.get("userId") else None,
                    "name": data.get("name", ""),
                    "description": data.get("description", ""),
                    "status": data.get("status", "active"),
                    "external_links": data.get("externalLinks") or [],
                    "metadata": data,
                    "updated_at": timezone.now(),
                },
            )
            return self._doc(container_name, obj)
        if container_name == "analysis":
            obj, _ = Analysis.objects.update_or_create(
                id=str(item_id),
                defaults={
                    "project_id": str(data.get("projectId")) if data.get("projectId") else None,
                    "user_id": str(data.get("userId")) if data.get("userId") else None,
                    "type": data.get("type", "analysis"),
                    "analysis_type": data.get("analysis_type", ""),
                    "quarter": data.get("quarter", ""),
                    "result": data.get("result") or {},
                    "comments": data.get("comments") or [],
                    "payload": data,
                    "updated_at": timezone.now(),
                },
            )
            return self._doc(container_name, obj)
        if container_name == "user_stories":
            obj, _ = UserStory.objects.update_or_create(
                id=str(item_id),
                defaults={
                    "project_id": str(data.get("projectId")) if data.get("projectId") else None,
                    "user_id": str(data.get("userId")) if data.get("userId") else None,
                    "type": data.get("type", "user_story"),
                    "status": data.get("status", ""),
                    "title": data.get("title", ""),
                    "description": data.get("description", ""),
                    "generated_at": _as_dt(data.get("generated_at")) if data.get("generated_at") else None,
                    "work_items": data.get("work_items") or [],
                    "payload": data,
                    "updated_at": timezone.now(),
                },
            )
            return self._doc(container_name, obj)
        model = self.containers.get(container_name)
        if not model:
            return data
        obj, _ = model.objects.update_or_create(id=str(item_id))
        return self._doc(container_name, obj)

    def delete_document(self, container_name: str, item_id: str, partition_key: Optional[str] = None):
        return self.delete_item(container_name, item_id, partition_key or item_id)

    def delete_item(self, container_type: str, item_id: str, partition_key: str):
        model = self.containers.get(container_type)
        if not model:
            return False
        deleted, _ = model.objects.filter(id=str(item_id)).delete()
        return deleted > 0

    def save_analysis_data(self, analysis_data: Dict[str, Any]):
        item_id = str(analysis_data.get("id") or f"insight_{timezone.now().timestamp()}")
        return self.update_document("analysis", item_id, str(analysis_data.get("projectId") or analysis_data.get("userId") or item_id), analysis_data)

    def get_analysis_data(self, analysis_id: str):
        return self.get_document("analysis", analysis_id, analysis_id)

    def get_latest_analysis_for_project(self, project_id: str):
        obj = Analysis.objects.filter(project_id=str(project_id)).order_by("-created_at").first()
        return self._doc("analysis", obj)

    def get_latest_personal_analysis(self, user_id: str):
        obj = Analysis.objects.filter(user_id=str(user_id)).order_by("-created_at").first()
        return self._doc("analysis", obj)

    def get_analysis_history_for_project(self, project_id: str):
        return [self._doc("analysis", r) for r in Analysis.objects.filter(project_id=str(project_id)).order_by("-created_at")]

    def get_analysis_by_quarter(self, project_id: str, quarter: str):
        obj = Analysis.objects.filter(project_id=str(project_id), quarter=quarter).order_by("-created_at").first()
        return self._doc("analysis", obj)

    def get_cumulative_analysis_for_project(self, project_id: str):
        rows = [self._doc("analysis", r) for r in Analysis.objects.filter(project_id=str(project_id)).order_by("created_at")]
        return {"items": rows, "count": len(rows)} if rows else None

    def get_latest_personal_user_data(self, user_id: str):
        obj = UserData.objects.filter(user_id=str(user_id)).order_by("-created_at").first()
        return self._doc("user_data", obj)

    def get_user_data_by_project(self, user_id: str, project_id: str):
        obj = UserData.objects.filter(user_id=str(user_id), project_id=str(project_id)).order_by("-created_at").first()
        return self._doc("user_data", obj)

    def update_project_last_analysis(self, project_id: str, analysis_id: str):
        p = Project.objects.filter(id=str(project_id)).first()
        if not p:
            return False
        p.last_analysis_id = analysis_id
        p.last_analyzed_at = timezone.now()
        p.updated_at = timezone.now()
        p.save(update_fields=["last_analysis_id", "last_analyzed_at", "updated_at"])
        return True

    def get_user_stories_by_user_and_project(self, user_id: str, project_id: str):
        return [self._doc("user_stories", r) for r in UserStory.objects.filter(user_id=str(user_id), project_id=str(project_id)).order_by("-created_at")]

    def get_user_stories_by_user(self, user_id: str):
        return [self._doc("user_stories", r) for r in UserStory.objects.filter(user_id=str(user_id)).order_by("-created_at")]

    def get_user_stories_by_project(self, project_id: str):
        return [self._doc("user_stories", r) for r in UserStory.objects.filter(project_id=str(project_id)).order_by("-created_at")]

    def save_user_story(self, user_story_data: Dict[str, Any]):
        item_id = str(user_story_data.get("id") or f"user_story_{timezone.now().timestamp()}")
        return self.update_document("user_stories", item_id, str(user_story_data.get("projectId") or user_story_data.get("userId") or item_id), user_story_data)

    def get_user_story(self, user_story_id: str, user_id: str):
        obj = UserStory.objects.filter(id=str(user_story_id), user_id=str(user_id)).first()
        return self._doc("user_stories", obj)

    def get_user_story_by_id(self, user_story_id: str):
        return self.get_document("user_stories", user_story_id, user_story_id)

    def patch_user_story(self, user_story_id: str, partition_key: str, patch_operations: List[Dict[str, Any]]):
        obj = UserStory.objects.filter(id=str(user_story_id)).first()
        if not obj:
            return None
        doc = self._doc("user_stories", obj)
        for op in patch_operations:
            if op.get("op") == "replace":
                key = str(op.get("path", "")).strip("/")
                if key:
                    doc[key] = op.get("value")
        return self.update_document("user_stories", user_story_id, partition_key, doc)

    def update_embedded_work_item(self, work_item_id: str, user_id: str, updated_data: Dict[str, Any], project_id: Optional[str] = None):
        qs = UserStory.objects.filter(user_id=str(user_id))
        if project_id:
            qs = qs.filter(project_id=str(project_id))
        for story in qs:
            items = story.work_items or []
            for i, wi in enumerate(items):
                if str(wi.get("id")) == str(work_item_id):
                    items[i] = {**wi, **updated_data}
                    story.work_items = items
                    story.updated_at = timezone.now()
                    story.save(update_fields=["work_items", "updated_at"])
                    return self._doc("user_stories", story)
        return None

    def delete_embedded_work_items(self, work_item_ids: List[str], user_id: str):
        count = 0
        for wid in work_item_ids:
            if self.remove_embedded_work_item(wid, user_id):
                count += 1
        return count

    def remove_embedded_work_item(self, work_item_id: str, user_id: str, project_id: Optional[str] = None):
        qs = UserStory.objects.filter(user_id=str(user_id))
        if project_id:
            qs = qs.filter(project_id=str(project_id))
        for story in qs:
            old = story.work_items or []
            new = [w for w in old if str(w.get("id")) != str(work_item_id)]
            if len(new) != len(old):
                story.work_items = new
                story.updated_at = timezone.now()
                story.save(update_fields=["work_items", "updated_at"])
                return True
        return False

    def delete_work_items_from_user_story(self, user_story_id: str, work_item_ids: List[str], user_id: str):
        story = UserStory.objects.filter(id=str(user_story_id), user_id=str(user_id)).first()
        if not story:
            return {"deleted_count": 0, "remaining_count": 0}
        old = story.work_items or []
        new = [w for w in old if str(w.get("id")) not in {str(i) for i in work_item_ids}]
        story.work_items = new
        story.updated_at = timezone.now()
        story.save(update_fields=["work_items", "updated_at"])
        return {"deleted_count": len(old) - len(new), "remaining_count": len(new)}

    def get_work_items_by_project(self, project_id: str):
        return [self._doc("user_stories", r) for r in UserStory.objects.filter(project_id=str(project_id)).order_by("-generated_at", "-created_at")]

    def get_deep_analysis_by_project(self, project_id: str):
        return [self._doc("user_stories", r) for r in UserStory.objects.filter(project_id=str(project_id), type="deep_analysis").order_by("-generated_at")]

    def get_insight(self, insight_id: str):
        return self.get_document("insights", insight_id, insight_id)

    def get_insight_rules_for_project(self, project_id: str):
        obj = InsightRule.objects.filter(project_id=str(project_id)).first()
        return self._doc("insight_rules", obj)

    def upsert_insight_rules_for_project(self, project_id: str, data: Dict[str, Any]):
        item_id = str(data.get("id") or f"insight_rule:{project_id}")
        data = {**data, "projectId": project_id}
        return self.update_document("insight_rules", item_id, project_id, data)

    def get_insight_reviews_for_project(self, project_id: str):
        return [self._doc("insight_reviews", r) for r in InsightReview.objects.filter(project_id=str(project_id)).order_by("-created_at")]

    def upsert_insight_review(self, project_id: str, data: Dict[str, Any]):
        item_id = str(data.get("id") or f"insight_review:{project_id}:{timezone.now().timestamp()}")
        data = {**data, "projectId": project_id}
        return self.update_document("insight_reviews", item_id, project_id, data)

    def get_work_item_quality_rules_for_project(self, project_id: str):
        obj = WorkItemQualityRule.objects.filter(project_id=str(project_id)).first()
        return self._doc("work_item_quality_rules", obj)

    def upsert_work_item_quality_rules_for_project(self, project_id: str, data: Dict[str, Any]):
        item_id = str(data.get("id") or f"work_item_quality:{project_id}")
        data = {**data, "projectId": project_id}
        return self.update_document("work_item_quality_rules", item_id, project_id, data)

    def get_project_by_id_any(self, project_id: str):
        return self._doc("projects", Project.objects.filter(id=str(project_id)).first())

    def get_project_role_for_user(self, project_id: str, user_id: str):
        return self._doc("project_roles", ProjectRole.objects.filter(project_id=str(project_id), user_id=str(user_id)).first())

    def get_project_roles_for_project(self, project_id: str):
        return [self._doc("project_roles", r) for r in ProjectRole.objects.filter(project_id=str(project_id))]

    def upsert_project_role(self, project_id: str, user_id: str, role: str, actor_id: Optional[str] = None):
        obj, _ = ProjectRole.objects.update_or_create(
            project_id=str(project_id),
            user_id=str(user_id),
            defaults={"id": f"project_role:{project_id}:{user_id}", "role": role, "actor_id": str(actor_id or ""), "updated_at": timezone.now()},
        )
        return self._doc("project_roles", obj)

    def delete_project_role(self, project_id: str, user_id: str):
        deleted, _ = ProjectRole.objects.filter(project_id=str(project_id), user_id=str(user_id)).delete()
        return deleted > 0

    def get_project_ids_for_user(self, user_id: str):
        return list(ProjectRole.objects.filter(user_id=str(user_id)).values_list("project_id", flat=True))

    def get_projects_by_ids(self, ids: List[str]):
        return [self._doc("projects", p) for p in Project.objects.filter(id__in=[str(i) for i in ids])]

    def get_ingestion_schedule_for_project(self, project_id: str):
        obj = IngestionSchedule.objects.filter(project_id=str(project_id)).first()
        return self._doc("ingestion_schedules", obj)

    def upsert_ingestion_schedule_for_project(self, project_id: str, data: Dict[str, Any]):
        item_id = str(data.get("id") or f"ingestion_schedule:{project_id}")
        obj, _ = IngestionSchedule.objects.update_or_create(
            project_id=str(project_id),
            defaults={
                "id": item_id,
                "type": data.get("type", "ingestion_schedule"),
                "status": "active" if data.get("enabled", False) else "disabled",
                "payload": data,
                "updated_at": timezone.now(),
            },
        )
        return self._doc("ingestion_schedules", obj)

    def get_enabled_ingestion_schedules(self):
        rows = IngestionSchedule.objects.filter(status="active").order_by("updated_at")
        return [self._doc("ingestion_schedules", r) for r in rows]


_storage_service = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


class _StorageServiceProxy:
    def __getattr__(self, name):
        return getattr(get_storage_service(), name)

    def __dir__(self):
        return dir(get_storage_service())


storage_service = _StorageServiceProxy()


