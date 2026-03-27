"""
Work item repository for DevOps-related data operations.
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from django.forms.models import model_to_dict
from django.utils import timezone

from authentication.models import UserAccount
from integrations.models import Project
from .models import UserStory, WorkItemQualityRule

logger = logging.getLogger(__name__)


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

    def get_all_work_items_flat(self, project_id: str) -> List[Dict[str, Any]]:
        """Return all embedded work items across all UserStory rows for a project."""
        items: List[Dict[str, Any]] = []
        rows = UserStory.objects.filter(project_id=str(project_id)).order_by("-generated_at", "-created_at")
        for story in rows:
            for item in story.work_items or []:
                entry = dict(item)
                entry["_story_id"] = str(story.id)
                entry.setdefault("id", item.get("id") or item.get("work_item_id"))
                items.append(entry)
        return items

    def get_candidates_by_status(self, project_id: str, status: str) -> List[Dict[str, Any]]:
        """Get embedded work item candidates filtered by review status."""
        candidates: List[Dict[str, Any]] = []
        rows = UserStory.objects.filter(project_id=str(project_id)).order_by("-generated_at", "-created_at")

        for story in rows:
            for item in story.work_items or []:
                item_status = item.get("status") or item.get("review_status") or "pending"
                if item_status != status:
                    continue
                candidate_id = item.get("id") or item.get("work_item_id")
                if not candidate_id:
                    continue
                candidate = dict(item)
                candidate["id"] = str(candidate_id)
                candidate["projectId"] = str(project_id)
                candidate.setdefault("createdAt", _iso(story.created_at))
                candidate.setdefault("updatedAt", _iso(story.updated_at))
                candidates.append(candidate)
        return candidates

    def update_candidate_status(self, candidate_id: str, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an embedded work item candidate by ID."""
        rows = UserStory.objects.filter(project_id=str(project_id))
        for story in rows:
            items = story.work_items or []
            for idx, item in enumerate(items):
                current_id = str(item.get("id") or item.get("work_item_id") or "")
                if current_id != str(candidate_id):
                    continue
                updated = {**item, **updates}
                if "status" in updates:
                    updated["review_status"] = updates["status"]
                story.work_items[idx] = updated
                story.updated_at = timezone.now()
                story.save(update_fields=["work_items", "updated_at"])
                result = dict(updated)
                result["id"] = str(candidate_id)
                result["projectId"] = str(project_id)
                result.setdefault("updatedAt", _iso(story.updated_at))
                result.setdefault("createdAt", _iso(story.created_at))
                return result
        raise ValueError(f"Candidate {candidate_id} not found")

    def get_candidate_by_id(self, candidate_id: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a single embedded candidate by ID."""
        rows = UserStory.objects.filter(project_id=str(project_id))
        for story in rows:
            for item in story.work_items or []:
                current_id = str(item.get("id") or item.get("work_item_id") or "")
                if current_id == str(candidate_id):
                    result = dict(item)
                    result["id"] = str(candidate_id)
                    result["projectId"] = str(project_id)
                    result.setdefault("createdAt", _iso(story.created_at))
                    result.setdefault("updatedAt", _iso(story.updated_at))
                    return result
        return None

    def get_expired_snoozed_candidates(self) -> List[Dict[str, Any]]:
        """Return snoozed candidates where snooze_until has already passed."""
        now = timezone.now()
        expired: List[Dict[str, Any]] = []
        rows = UserStory.objects.all().order_by("-generated_at", "-created_at")

        for story in rows:
            for item in story.work_items or []:
                item_status = item.get("status") or item.get("review_status") or "pending"
                if item_status != "snoozed":
                    continue
                raw_until = item.get("snooze_until")
                if not raw_until:
                    continue
                try:
                    parsed_until = datetime.fromisoformat(str(raw_until).replace("Z", "+00:00"))
                    if timezone.is_naive(parsed_until):
                        parsed_until = timezone.make_aware(parsed_until, timezone.utc)
                except Exception:
                    logger.warning("Invalid snooze_until value for candidate %s: %s", item.get("id"), raw_until)
                    continue
                if parsed_until <= now:
                    candidate = dict(item)
                    candidate["id"] = str(item.get("id") or item.get("work_item_id"))
                    candidate["projectId"] = str(story.project_id) if story.project_id else ""
                    expired.append(candidate)
        return expired

    def get_deep_analysis_by_project(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        rows = UserStory.objects.filter(project_id=str(project_id), type="deep_analysis").order_by("-generated_at")
        return [_story_to_dict(r) for r in rows]

