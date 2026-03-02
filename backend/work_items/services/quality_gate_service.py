"""
Quality gate service for work items.
Validates work items against project-specific "definition of ready" rules.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from ..repositories import WorkItemRepository


DEFAULT_RULES = {
    "require_acceptance_criteria": True,
    "require_priority": True,
    "require_tags": False,
    "min_description_length": 30,
    "min_acceptance_criteria_length": 20,
    "allow_push_with_warnings": False,
}


class WorkItemQualityGateService:
    def __init__(self):
        self.repo = WorkItemRepository()

    def get_rules_for_project(self, project_id: str) -> Dict[str, Any]:
        rules_doc = self.repo.get_quality_rules_for_project(project_id)
        if not rules_doc:
            return DEFAULT_RULES.copy()
        return {
            "require_acceptance_criteria": rules_doc.get("require_acceptance_criteria", DEFAULT_RULES["require_acceptance_criteria"]),
            "require_priority": rules_doc.get("require_priority", DEFAULT_RULES["require_priority"]),
            "require_tags": rules_doc.get("require_tags", DEFAULT_RULES["require_tags"]),
            "min_description_length": int(rules_doc.get("min_description_length", DEFAULT_RULES["min_description_length"])),
            "min_acceptance_criteria_length": int(rules_doc.get("min_acceptance_criteria_length", DEFAULT_RULES["min_acceptance_criteria_length"])),
            "allow_push_with_warnings": rules_doc.get("allow_push_with_warnings", DEFAULT_RULES["allow_push_with_warnings"]),
        }

    def save_rules_for_project(self, project_id: str, rules: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "id": f"work_item_quality_rule:{project_id}",
            "type": "work_item_quality_rule",
            "projectId": project_id,
            "require_acceptance_criteria": bool(rules.get("require_acceptance_criteria", DEFAULT_RULES["require_acceptance_criteria"])),
            "require_priority": bool(rules.get("require_priority", DEFAULT_RULES["require_priority"])),
            "require_tags": bool(rules.get("require_tags", DEFAULT_RULES["require_tags"])),
            "min_description_length": int(rules.get("min_description_length", DEFAULT_RULES["min_description_length"])),
            "min_acceptance_criteria_length": int(rules.get("min_acceptance_criteria_length", DEFAULT_RULES["min_acceptance_criteria_length"])),
            "allow_push_with_warnings": bool(rules.get("allow_push_with_warnings", DEFAULT_RULES["allow_push_with_warnings"])),
            "updatedAt": now,
            "updatedBy": str(user_id) if user_id else None,
        }
        return self.repo.upsert_quality_rules_for_project(project_id, payload)

    def evaluate_work_items(self, work_items: List[Dict[str, Any]], rules: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        for item in work_items:
            item_id = item.get("id") or item.get("work_item_id") or item.get("title")
            title = item.get("title", "")
            description = item.get("description", "") or ""
            acceptance = item.get("acceptance_criteria") or item.get("acceptancecriteria") or item.get("acceptance") or ""
            priority = item.get("priority")
            tags = item.get("tags") or item.get("labels") or []

            item_issues = []
            if rules.get("require_acceptance_criteria"):
                if not acceptance or len(str(acceptance).strip()) < int(rules.get("min_acceptance_criteria_length", 0)):
                    item_issues.append({
                        "code": "missing_acceptance_criteria",
                        "message": "Acceptance criteria is missing or too short."
                    })

            if rules.get("require_priority") and not priority:
                item_issues.append({
                    "code": "missing_priority",
                    "message": "Priority is required."
                })

            if rules.get("require_tags") and (not tags or len(tags) == 0):
                item_issues.append({
                    "code": "missing_tags",
                    "message": "Tags/labels are required."
                })

            if description and len(description.strip()) < int(rules.get("min_description_length", 0)):
                item_issues.append({
                    "code": "description_too_short",
                    "message": "Description is too short."
                })

            if item_issues:
                issues.append({
                    "id": item_id,
                    "title": title,
                    "issues": item_issues
                })

        return {
            "total_items": len(work_items),
            "items_with_issues": len(issues),
            "issues": issues,
        }


_quality_gate_service = None


def get_quality_gate_service() -> WorkItemQualityGateService:
    global _quality_gate_service
    if _quality_gate_service is None:
        _quality_gate_service = WorkItemQualityGateService()
    return _quality_gate_service
