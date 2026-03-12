"""
Feedback source management service.

Handles CRUD for feedback source configurations (e.g. which Slack channels to
monitor for a given project).
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from ..models import FeedbackSource

logger = logging.getLogger(__name__)


def _source_to_dict(source: FeedbackSource) -> Dict[str, Any]:
    return {
        "id": source.id,
        "type": "feedbackSource",
        "userId": source.user_id,
        "projectId": source.project_id,
        "provider": source.provider,
        "accountId": source.account_id,
        "config": source.config or {},
        "status": source.status,
        "createdAt": source.created_at.isoformat() if source.created_at else None,
        "updatedAt": source.updated_at.isoformat() if source.updated_at else None,
    }


class SourceService:
    """Service for feedback source configuration."""

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
        source = FeedbackSource.objects.create(
            id=f"source_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            project_id=project_id,
            provider="slack",
            account_id=account_id,
            config={
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
            status="active",
        )
        return _source_to_dict(source)

    def get_sources_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all feedback sources for a project."""
        sources = FeedbackSource.objects.filter(
            project_id=project_id,
        ).order_by("-created_at")
        return [_source_to_dict(s) for s in sources]

    def get_source(self, source_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single feedback source with ownership check."""
        source = FeedbackSource.objects.filter(
            id=source_id, user_id=user_id,
        ).first()
        return _source_to_dict(source) if source else None

    def update_source_channels(
        self, source_id: str, user_id: str, channels: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """Update channels on an existing source."""
        source = FeedbackSource.objects.filter(
            id=source_id, user_id=user_id,
        ).first()
        if not source:
            return None
        config = source.config or {}
        config["channels"] = channels
        source.config = config
        source.updated_at = datetime.now(timezone.utc)
        source.save(update_fields=["config", "updated_at"])
        return _source_to_dict(source)

    def delete_source(self, source_id: str, user_id: str) -> bool:
        """Delete a feedback source."""
        deleted, _ = FeedbackSource.objects.filter(
            id=source_id, user_id=user_id,
        ).delete()
        return deleted > 0

    def update_sync_cursor(
        self,
        source_id: str,
        user_id: str,
        cursor: Optional[str],
        synced_at: str,
    ) -> Optional[Dict[str, Any]]:
        """Update sync cursor and last_synced_at after a sync run."""
        source = FeedbackSource.objects.filter(
            id=source_id, user_id=user_id,
        ).first()
        if not source:
            return None
        config = source.config or {}
        config["last_sync_cursor"] = cursor
        config["last_synced_at"] = synced_at
        source.config = config
        source.updated_at = datetime.now(timezone.utc)
        source.save(update_fields=["config", "updated_at"])
        return _source_to_dict(source)

    def update_analysis_cursor(
        self,
        source_id: str,
        user_id: str,
        analyzed_at: Optional[str],
        analyzed_ts: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Update last analyzed marker after a Slack analysis run."""
        source = FeedbackSource.objects.filter(
            id=source_id, user_id=user_id,
        ).first()
        if not source:
            return None
        config = source.config or {}
        config["last_analyzed_at"] = analyzed_at
        config["last_analyzed_ts"] = analyzed_ts
        source.config = config
        source.updated_at = datetime.now(timezone.utc)
        source.save(update_fields=["config", "updated_at"])
        return _source_to_dict(source)

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
        source = FeedbackSource.objects.filter(
            id=source_id, user_id=user_id,
        ).first()
        if not source:
            return None
        config = source.config or {}
        config["last_analysis_status"] = status
        config["last_analysis_error"] = error
        if enqueued_at:
            config["last_analysis_enqueued_at"] = enqueued_at
        if failed_at:
            config["last_analysis_failed_at"] = failed_at
        if status in ("queued", "success") and failed_at is None:
            config["last_analysis_failed_at"] = None
        source.config = config
        source.updated_at = datetime.now(timezone.utc)
        source.save(update_fields=["config", "updated_at"])
        return _source_to_dict(source)

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
        source = FeedbackSource.objects.filter(
            id=source_id, user_id=user_id,
        ).first()
        if not source:
            return None
        config = source.config or {}
        config["last_range_analysis_at"] = analyzed_at
        config["last_range_analysis_from"] = from_iso
        config["last_range_analysis_to"] = to_iso
        config["last_range_analysis_count"] = count
        source.config = config
        source.updated_at = datetime.now(timezone.utc)
        source.save(update_fields=["config", "updated_at"])
        return _source_to_dict(source)

    def get_active_sources_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get all active sources for a given provider (used by scheduler)."""
        sources = FeedbackSource.objects.filter(
            provider=provider, status="active",
        )
        return [_source_to_dict(s) for s in sources]


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_source_service: Optional[SourceService] = None


def get_source_service() -> SourceService:
    global _source_service
    if _source_service is None:
        _source_service = SourceService()
    return _source_service
