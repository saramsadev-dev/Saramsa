"""
Taxonomy service for Phase-1: project-owned, versioned taxonomy.

Rules:
- Exactly ONE active taxonomy per project.
- LLMs may propose but never apply changes.
- Taxonomy changes are explicit, versioned, and archived (never deleted).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import logging

from ..repositories import ProjectTaxonomyRepository
from .aspect_suggestion_service import get_aspect_suggestion_service
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class TaxonomyService:
    """Service for managing project taxonomies."""

    def __init__(self):
        self.taxonomy_repo = ProjectTaxonomyRepository()

    def get_active_taxonomy(self, project_id: str, comments: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Resolve the active taxonomy for a project.

        Resolution order:
        1) Pinned taxonomy exists -> use it
        2) Active taxonomy exists AND healthy -> use it
        3) No taxonomy exists -> bootstrap once using GPT and save as version=1
        4) Taxonomy unhealthy -> use current taxonomy and flag DEGRADED
        """
        pinned = self.taxonomy_repo.get_pinned_by_project(project_id)
        if pinned:
            return pinned

        active = self.taxonomy_repo.get_active_by_project(project_id)
        if active:
            if self._is_taxonomy_healthy(active):
                return active
            # Unhealthy: keep it, flag degraded
            self.mark_taxonomy_degraded(project_id, active, metrics=None)
            return active

        # No taxonomy exists -> bootstrap once using GPT (requires comments)
        if comments is None:
            logger.warning("No active taxonomy found and no comments provided for bootstrap")
            return None
        aspect_service = get_aspect_suggestion_service()
        aspect_result = async_to_sync(aspect_service.suggest_aspects)(comments)
        suggested_aspects = aspect_result.get("suggested_aspects", [])
        return self.create_initial_taxonomy(project_id, suggested_aspects, source="gpt")

    def create_initial_taxonomy(self, project_id: str, aspects: List[str], source: str = "gpt") -> Dict[str, Any]:
        """Create initial taxonomy for a project (version 1 or next)."""
        now = datetime.now(timezone.utc).isoformat()
        next_version = max(1, self.taxonomy_repo.get_latest_version(project_id) + 1)
        taxonomy_id = str(uuid.uuid4())

        taxonomy_doc = {
            "id": taxonomy_id,
            "taxonomy_id": taxonomy_id,
            "project_id": project_id,
            "projectId": project_id,
            "version": next_version,
            "status": "active",
            "aspects": [
                {
                    "key": self._normalize_aspect_key(a),
                    "label": str(a),
                    "synonyms": [],
                }
                for a in aspects
                if a
            ],
            "source": source,
            "is_pinned": False,
            "created_at": now,
            "updated_at": now,
            "health_snapshot": {
                "last_unmapped_rate": None,
                "last_avg_aspects_per_comment": None,
                "last_confidence_p95": None,
            },
            "taxonomy_health": "UNKNOWN",
        }

        created = self.taxonomy_repo.create(taxonomy_doc)
        try:
            self.taxonomy_repo.archive_others_for_project(project_id, created.get("id"))
        except Exception as e:
            logger.warning(f"Failed to archive other taxonomies after creation: {e}")
        return created

    def mark_taxonomy_degraded(self, project_id: str, taxonomy: Dict[str, Any], metrics: Optional[Dict[str, Any]]) -> None:
        """
        Mark taxonomy as degraded and store health snapshot.

        This is a warning-only signal; it must not trigger automatic regeneration.
        """
        if not taxonomy:
            return
        updated = taxonomy.copy()
        updated["taxonomy_health"] = "DEGRADED"
        if metrics:
            updated["health_snapshot"] = metrics
        updated["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.taxonomy_repo.update(updated.get("id"), project_id, updated)
        # TODO(phase-2): generate taxonomy suggestions from UNMAPPED comments.

    def pin_taxonomy(self, taxonomy_id: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Pin a taxonomy and make it the active one."""
        taxonomy = self.taxonomy_repo.get_by_id(taxonomy_id, project_id)
        if not taxonomy:
            return None
        taxonomy["is_pinned"] = True
        taxonomy["status"] = "active"
        taxonomy["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = self.taxonomy_repo.update(taxonomy_id, project_id, taxonomy)
        if updated:
            self.taxonomy_repo.archive_others_for_project(project_id, taxonomy_id)
        return updated

    def archive_taxonomy(self, taxonomy_id: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Archive a taxonomy (never delete)."""
        taxonomy = self.taxonomy_repo.get_by_id(taxonomy_id, project_id)
        if not taxonomy:
            return None
        taxonomy["status"] = "archived"
        taxonomy["is_pinned"] = False
        taxonomy["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.taxonomy_repo.update(taxonomy_id, project_id, taxonomy)

    def record_health_snapshot(self, project_id: str, taxonomy: Dict[str, Any], metrics: Dict[str, Any]) -> None:
        """Record health snapshot and set health status without changing taxonomy content."""
        if not taxonomy:
            return
        updated = taxonomy.copy()
        updated["health_snapshot"] = metrics
        updated["taxonomy_health"] = "HEALTHY" if self._is_healthy_metrics(metrics) else "DEGRADED"
        updated["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.taxonomy_repo.update(updated.get("id"), project_id, updated)

    def _is_taxonomy_healthy(self, taxonomy: Dict[str, Any]) -> bool:
        """Evaluate taxonomy health based on last recorded snapshot and age."""
        snapshot = taxonomy.get("health_snapshot") or {}
        if snapshot.get("last_unmapped_rate") is None or snapshot.get("last_avg_aspects_per_comment") is None:
            return True
        metrics = {
            "last_unmapped_rate": snapshot.get("last_unmapped_rate"),
            "last_avg_aspects_per_comment": snapshot.get("last_avg_aspects_per_comment"),
            "taxonomy_age_days": self._taxonomy_age_days(taxonomy),
        }
        return self._is_healthy_metrics(metrics)

    @staticmethod
    def _is_healthy_metrics(metrics: Dict[str, Any]) -> bool:
        """Health guardrails (deterministic)."""
        try:
            unmapped_rate = float(metrics.get("last_unmapped_rate"))
            avg_aspects = float(metrics.get("last_avg_aspects_per_comment"))
            age_days = float(metrics.get("taxonomy_age_days"))
        except Exception:
            return False
        return (
            unmapped_rate <= 0.15
            and avg_aspects <= 1.35
            and age_days <= 30
        )

    @staticmethod
    def _taxonomy_age_days(taxonomy: Dict[str, Any]) -> float:
        created_at = taxonomy.get("created_at") or taxonomy.get("createdAt")
        if not created_at:
            return 0.0
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except Exception:
            return 0.0
        return (datetime.now(timezone.utc) - created_dt).days

    @staticmethod
    def _normalize_aspect_key(label: str) -> str:
        return str(label).strip().lower().replace(" ", "_")


_taxonomy_service = None


def get_taxonomy_service() -> TaxonomyService:
    """Get the global taxonomy service instance."""
    global _taxonomy_service
    if _taxonomy_service is None:
        _taxonomy_service = TaxonomyService()
    return _taxonomy_service
