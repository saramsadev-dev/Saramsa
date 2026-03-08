"""
Work item repository for DevOps-related data operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from django.forms.models import model_to_dict
from django.utils import timezone

from authentication.models import UserAccount
from integrations.models import Project
from .models import UserStory, WorkItemQualityRule


def _iso(value):
    if not value:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.utc)
    return value.isoformat()


def _story_to_dict(item: UserStory) -> Dict[str, Any]:
    data = model_to_dict(item)
    data["projectId"] = item.project_id
    data["userId"] = item.user_id
    data["work_items"] = item.work_items or []
    data["generated_at"] = _iso(item.generated_at)
    data["createdAt"] = _iso(item.created_at)
    data["updatedAt"] = _iso(item.updated_at)
    return data


class WorkItemRepository:
    """Repository for work item operations."""

    def __init__(self):
        self.entity_type = "user_story"

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        item = UserStory.objects.create(
            id=data["id"],
            project=Project.objects.filter(id=str(data.get("projectId"))).first(),
            user=UserAccount.objects.filter(id=str(data.get("userId"))).first(),
            type=data.get("type", self.entity_type),
            status=data.get("status", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            generated_at=datetime.fromisoformat(data["generated_at"]) if data.get("generated_at") else None,
            work_items=data.get("work_items", []),
            payload={k: v for k, v in data.items() if k not in {
                "id", "projectId", "userId", "type", "status", "title", "description",
                "generated_at", "work_items", "createdAt", "updatedAt",
            }},
        )
        return _story_to_dict(item)

    def upsert_by_id(self, item_id: str, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        item = UserStory.objects.filter(id=item_id).first()
        if not item:
            data = {**data, "id": item_id, "projectId": project_id}
            return self.create(data)
        return self.update(item_id, data)

    def get_by_id(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        item = UserStory.objects.filter(id=work_item_id).first()
        return _story_to_dict(item) if item else None

    def get_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        rows = UserStory.objects.filter(project_id=str(project_id), type=self.entity_type).order_by("-created_at")
        return [_story_to_dict(r) for r in rows]

    def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        rows = UserStory.objects.filter(user_id=str(user_id), type=self.entity_type).order_by("-created_at")
        return [_story_to_dict(r) for r in rows]

    def update(self, work_item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        item = UserStory.objects.get(id=work_item_id)
        item.status = data.get("status", item.status)
        item.title = data.get("title", item.title)
        item.description = data.get("description", item.description)
        if "work_items" in data:
            item.work_items = data.get("work_items") or []
        if data.get("generated_at"):
            item.generated_at = datetime.fromisoformat(data["generated_at"])
        item.payload = {**(item.payload or {}), **data.get("payload", {})}
        item.updated_at = timezone.now()
        item.save()
        return _story_to_dict(item)

    def delete(self, work_item_id: str) -> bool:
        deleted, _ = UserStory.objects.filter(id=work_item_id).delete()
        return deleted > 0

    def update_embedded_work_item(self, work_item_id: str, user_id: str, updated_data: Dict[str, Any], project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        rows = UserStory.objects.filter(user_id=str(user_id))
        if project_id:
            rows = rows.filter(project_id=str(project_id))
        for story in rows:
            updated = False
            for idx, wi in enumerate(story.work_items or []):
                if str(wi.get("id")) == str(work_item_id):
                    story.work_items[idx] = {**wi, **updated_data}
                    updated = True
                    break
            if updated:
                story.updated_at = timezone.now()
                story.save(update_fields=["work_items", "updated_at"])
                return _story_to_dict(story)
        return None

    def remove_embedded_work_item(self, work_item_id: str, user_id: str, project_id: Optional[str] = None) -> bool:
        rows = UserStory.objects.filter(user_id=str(user_id))
        if project_id:
            rows = rows.filter(project_id=str(project_id))
        for story in rows:
            before = len(story.work_items or [])
            story.work_items = [w for w in (story.work_items or []) if str(w.get("id")) != str(work_item_id)]
            if len(story.work_items) != before:
                story.updated_at = timezone.now()
                story.save(update_fields=["work_items", "updated_at"])
                return True
        return False

    def get_work_items_by_project(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        rows = UserStory.objects.filter(project_id=str(project_id)).order_by("-generated_at", "-created_at")
        return [_story_to_dict(r) for r in rows]

    def get_quality_rules_for_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        row = WorkItemQualityRule.objects.filter(project_id=str(project_id)).first()
        if not row:
            return None
        return {
            "id": row.id,
            "projectId": row.project_id,
            "type": row.type,
            "createdAt": _iso(row.created_at),
            "updatedAt": _iso(row.updated_at),
            **(row.payload or {}),
        }

    def upsert_quality_rules_for_project(self, project_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row, _created = WorkItemQualityRule.objects.update_or_create(
            project_id=str(project_id),
            defaults={
                "id": data.get("id") or f"work_item_quality:{project_id}",
                "type": data.get("type", "work_item_quality_rule"),
                "payload": data,
                "updated_at": timezone.now(),
            },
        )
        return {
            "id": row.id,
            "projectId": row.project_id,
            "type": row.type,
            "createdAt": _iso(row.created_at),
            "updatedAt": _iso(row.updated_at),
            **(row.payload or {}),
        }

    def get_deep_analysis_by_project(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        rows = UserStory.objects.filter(project_id=str(project_id), type="deep_analysis").order_by("-generated_at")
        return [_story_to_dict(r) for r in rows]

