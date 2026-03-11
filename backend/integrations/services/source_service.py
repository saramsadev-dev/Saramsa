"""
Feedback source management service.

Handles CRUD for feedback source configurations (e.g. which Slack channels to
monitor for a given project).
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from ..repositories import IntegrationsRepository

logger = logging.getLogger(__name__)


class SourceService:
    """Service for feedback source configuration."""

    def __init__(self):
        self.repo = IntegrationsRepository()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_slack_source(
        self,
        user_id: str,
        project_id: str,
        account_id: str,
        channels: List[Dict[str, str]],
        sync_frequency: str = "hourly",
    ) -> Dict[str, Any]:
        """Create a new Slack feedback source for a project."""
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": f"source_{uuid.uuid4().hex[:12]}",
            "type": "feedbackSource",
            "userId": user_id,
            "projectId": project_id,
            "provider": "slack",
            "accountId": account_id,
            "config": {
                "channels": channels,
                "sync_frequency": sync_frequency,
                "last_synced_at": None,
                "last_sync_cursor": None,
                "last_analyzed_at": None,
                "last_analyzed_ts": None,
                "last_analysis_status": None,
                "last_analysis_error": None,
                "last_analysis_enqueued_at": None,
                "last_analysis_failed_at": None,
                "last_range_analysis_at": None,
                "last_range_analysis_from": None,
                "last_range_analysis_to": None,
                "last_range_analysis_count": None,
            },
            "status": "active",
            "createdAt": now,
            "updatedAt": now,
        }
        return self.repo.cosmos_service.create_document(
            self.repo.container_name, doc
        )

    def get_sources_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all feedback sources for a project."""
        query = (
            "SELECT * FROM c "
            "WHERE c.projectId = @project_id AND c.type = 'feedbackSource' "
            "ORDER BY c.createdAt DESC"
        )
        params = [{"name": "@project_id", "value": project_id}]
        return self.repo.cosmos_service.query_documents(
            self.repo.container_name, query, params
        )

    def get_source(self, source_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single feedback source with ownership check."""
        query = (
            "SELECT * FROM c "
            "WHERE c.id = @source_id AND c.userId = @user_id AND c.type = 'feedbackSource'"
        )
        params = [
            {"name": "@source_id", "value": source_id},
            {"name": "@user_id", "value": user_id},
        ]
        results = self.repo.cosmos_service.query_documents(
            self.repo.container_name, query, params
        )
        return results[0] if results else None

    def update_source_channels(
        self, source_id: str, user_id: str, channels: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """Update channels on an existing source."""
        source = self.get_source(source_id, user_id)
        if not source:
            return None
        source["config"]["channels"] = channels
        source["updatedAt"] = datetime.now(timezone.utc).isoformat()
        return self.repo.cosmos_service.update_document(
            self.repo.container_name, source_id, source["userId"], source
        )

    def delete_source(self, source_id: str, user_id: str) -> bool:
        """Delete a feedback source."""
        source = self.get_source(source_id, user_id)
        if not source:
            return False
        try:
            self.repo.cosmos_service.delete_document(
                self.repo.container_name, source_id, source["userId"]
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting source {source_id}: {e}")
            return False

    def update_sync_cursor(
        self,
        source_id: str,
        user_id: str,
        cursor: Optional[str],
        synced_at: str,
    ) -> Optional[Dict[str, Any]]:
        """Update sync cursor and last_synced_at after a sync run."""
        source = self.get_source(source_id, user_id)
        if not source:
            return None
        source["config"]["last_sync_cursor"] = cursor
        source["config"]["last_synced_at"] = synced_at
        source["updatedAt"] = datetime.now(timezone.utc).isoformat()
        return self.repo.cosmos_service.update_document(
            self.repo.container_name, source_id, source["userId"], source
        )

    def update_analysis_cursor(
        self,
        source_id: str,
        user_id: str,
        analyzed_at: Optional[str],
        analyzed_ts: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Update last analyzed marker after a Slack analysis run."""
        source = self.get_source(source_id, user_id)
        if not source:
            return None
        source["config"]["last_analyzed_at"] = analyzed_at
        source["config"]["last_analyzed_ts"] = analyzed_ts
        source["updatedAt"] = datetime.now(timezone.utc).isoformat()
        return self.repo.cosmos_service.update_document(
            self.repo.container_name, source_id, source["userId"], source
        )

    def update_analysis_status(
        self,
        source_id: str,
        user_id: str,
        status: str,
        error: Optional[str] = None,
        enqueued_at: Optional[str] = None,
        failed_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update analysis status metadata for a source."""
        source = self.get_source(source_id, user_id)
        if not source:
            return None
        source["config"]["last_analysis_status"] = status
        source["config"]["last_analysis_error"] = error
        if enqueued_at:
            source["config"]["last_analysis_enqueued_at"] = enqueued_at
        if failed_at:
            source["config"]["last_analysis_failed_at"] = failed_at
        if status in ("queued", "success") and failed_at is None:
            source["config"]["last_analysis_failed_at"] = None
        source["updatedAt"] = datetime.now(timezone.utc).isoformat()
        return self.repo.cosmos_service.update_document(
            self.repo.container_name, source_id, source["userId"], source
        )

    def update_range_analysis_meta(
        self,
        source_id: str,
        user_id: str,
        analyzed_at: Optional[str],
        from_iso: Optional[str],
        to_iso: Optional[str],
        count: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        """Persist last manual range analysis metadata."""
        source = self.get_source(source_id, user_id)
        if not source:
            return None
        source["config"]["last_range_analysis_at"] = analyzed_at
        source["config"]["last_range_analysis_from"] = from_iso
        source["config"]["last_range_analysis_to"] = to_iso
        source["config"]["last_range_analysis_count"] = count
        source["updatedAt"] = datetime.now(timezone.utc).isoformat()
        return self.repo.cosmos_service.update_document(
            self.repo.container_name, source_id, source["userId"], source
        )

    def get_active_sources_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get all active sources for a given provider (used by scheduler)."""
        query = (
            "SELECT * FROM c "
            "WHERE c.provider = @provider AND c.type = 'feedbackSource' AND c.status = 'active'"
        )
        params = [{"name": "@provider", "value": provider}]
        return self.repo.cosmos_service.query_documents(
            self.repo.container_name, query, params
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_source_service: Optional[SourceService] = None


def get_source_service() -> SourceService:
    global _source_service
    if _source_service is None:
        _source_service = SourceService()
    return _source_service
