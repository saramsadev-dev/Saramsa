"""
Integrations repository for integration-related data operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from django.forms.models import model_to_dict
from django.utils import timezone

from authentication.models import UserAccount
from .models import FeedbackSource, IntegrationAccount, OAuthState, Project


def _iso(value):
    if not value:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.utc)
    return value.isoformat()


def _project_to_dict(project: Project) -> Dict[str, Any]:
    data = model_to_dict(project)
    data["userId"] = project.user_id
    data["externalLinks"] = project.external_links or []
    data["createdAt"] = _iso(project.created_at)
    data["updatedAt"] = _iso(project.updated_at)
    if project.last_analyzed_at:
        data["lastAnalyzedAt"] = _iso(project.last_analyzed_at)
    data["type"] = "project"
    data.pop("external_links", None)
    return data


def _integration_to_dict(item: IntegrationAccount) -> Dict[str, Any]:
    data = model_to_dict(item)
    data["userId"] = item.user_id
    data["createdAt"] = _iso(item.created_at)
    data["updatedAt"] = _iso(item.updated_at)
    data["type"] = item.type
    # Flatten config fields to top level for frontend compatibility.
    # Slack OAuth stores displayName, status, metadata, scopes inside config.
    config = data.get("config") or {}
    if "displayName" in config and not data.get("displayName"):
        data["displayName"] = config["displayName"]
    if "status" in config and not data.get("status"):
        data["status"] = config["status"]
    if "metadata" in config and not data.get("metadata"):
        data["metadata"] = config["metadata"]
    if "scopes" in config and not data.get("scopes"):
        data["scopes"] = config["scopes"]
    # Fallbacks: derive status from is_active, displayName from account_name
    if not data.get("status"):
        data["status"] = "active" if item.is_active else "revoked"
    if not data.get("displayName"):
        data["displayName"] = item.account_name or f"{item.provider} integration"
    if not data.get("metadata"):
        data["metadata"] = {}
    if not data.get("scopes"):
        data["scopes"] = []
    return data


def _oauth_state_to_dict(item: OAuthState) -> Dict[str, Any]:
    return {
        "id": item.id,
        "type": "oauth_state",
        "userId": item.user_id,
        "provider": item.provider,
        "status": item.status,
        "expiresAt": _iso(item.expires_at),
        "createdAt": _iso(item.created_at),
        "updatedAt": _iso(item.updated_at),
        "metadata": item.metadata or {},
    }


def _feedback_source_to_dict(item: FeedbackSource) -> Dict[str, Any]:
    data = model_to_dict(item)
    data["userId"] = item.user_id
    data["projectId"] = item.project_id
    data["accountId"] = item.account_id
    data["createdAt"] = _iso(item.created_at)
    data["updatedAt"] = _iso(item.updated_at)
    data["type"] = item.type
    data.pop("account_id", None)
    return data


class IntegrationsRepository:
    """Repository for integrations operations."""

    def __init__(self):
        self.entity_type = "integration_account"

    # OAuth state (Slack install flow)
    def create_oauth_state(
        self,
        state_id: str,
        user_id: str,
        provider: str = "slack",
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        item = OAuthState.objects.create(
            id=state_id,
            user=UserAccount.objects.filter(id=str(user_id)).first(),
            provider=provider,
            status="active",
            expires_at=expires_at,
            metadata=metadata or {},
        )
        return _oauth_state_to_dict(item)

    def get_oauth_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        item = OAuthState.objects.filter(id=state_id, status="active").first()
        if not item:
            return None
        if item.expires_at and item.expires_at <= timezone.now():
            item.status = "expired"
            item.updated_at = timezone.now()
            item.save(update_fields=["status", "updated_at"])
            return None
        return _oauth_state_to_dict(item)

    def delete_oauth_state(self, state_id: str) -> bool:
        deleted, _ = OAuthState.objects.filter(id=state_id).delete()
        return deleted > 0

    def create_integration_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        item = IntegrationAccount.objects.create(
            id=data["id"],
            user=UserAccount.objects.filter(id=str(data.get("userId"))).first(),
            provider=data.get("provider", ""),
            type=self.entity_type,
            account_name=data.get("account_name", data.get("name", "")),
            credentials=data.get("credentials", {}),
            config={k: v for k, v in data.items() if k not in {
                "id", "userId", "provider", "account_name", "name", "credentials",
                "type", "createdAt", "updatedAt",
            }},
            is_active=data.get("is_active", True),
        )
        return _integration_to_dict(item)

    def create_or_update_integration_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(data.get("userId"))
        provider = data.get("provider")
        if user_id and provider:
            existing = self.get_by_user_and_provider(user_id, provider)
            if existing:
                updated = {**existing, **data}
                return self.update(existing["id"], updated)
        return self.create_integration_account(data)

    def get_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        item = IntegrationAccount.objects.filter(id=account_id).first()
        return _integration_to_dict(item) if item else None

    def get_integration_account(self, user_id: str, account_id: str) -> Optional[Dict[str, Any]]:
        item = IntegrationAccount.objects.filter(id=account_id, user_id=str(user_id)).first()
        return _integration_to_dict(item) if item else None

    def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        items = IntegrationAccount.objects.filter(user_id=str(user_id), type=self.entity_type).order_by("-created_at")
        return [_integration_to_dict(i) for i in items]

    def get_integration_accounts_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        return self.get_by_user(user_id)

    def get_by_user_and_provider(self, user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        item = IntegrationAccount.objects.filter(user_id=str(user_id), provider=provider, type=self.entity_type).first()
        return _integration_to_dict(item) if item else None

    def update(self, account_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        item = IntegrationAccount.objects.get(id=account_id)
        item.provider = data.get("provider", item.provider)
        item.account_name = data.get("account_name", data.get("name", item.account_name))
        item.credentials = data.get("credentials", item.credentials)
        item.config = {**(item.config or {}), **data.get("config", {})}
        item.is_active = data.get("is_active", item.is_active)
        item.updated_at = timezone.now()
        item.save()
        return _integration_to_dict(item)

    def delete(self, account_id: str) -> bool:
        deleted, _ = IntegrationAccount.objects.filter(id=account_id).delete()
        return deleted > 0

    def delete_integration_account(self, user_id: str, account_id: str) -> bool:
        deleted, _ = IntegrationAccount.objects.filter(id=account_id, user_id=str(user_id)).delete()
        return deleted > 0

    # Feedback source (Slack sources per project)
    def create_feedback_source(self, data: Dict[str, Any]) -> Dict[str, Any]:
        item = FeedbackSource.objects.create(
            id=data["id"],
            user=UserAccount.objects.filter(id=str(data.get("userId"))).first(),
            project=Project.objects.filter(id=str(data.get("projectId"))).first(),
            type=data.get("type", "feedbackSource"),
            provider=data.get("provider", "slack"),
            account_id=data.get("accountId", ""),
            status=data.get("status", "active"),
            config=data.get("config", {}) or {},
            metadata={k: v for k, v in data.items() if k not in {
                "id", "type", "userId", "projectId", "provider", "accountId",
                "status", "config", "createdAt", "updatedAt",
            }},
        )
        return _feedback_source_to_dict(item)

    def get_feedback_sources_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        rows = FeedbackSource.objects.filter(
            project_id=str(project_id), type="feedbackSource"
        ).order_by("-created_at")
        return [_feedback_source_to_dict(row) for row in rows]

    def get_feedback_source(self, source_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        qs = FeedbackSource.objects.filter(id=str(source_id), type="feedbackSource")
        if user_id is not None:
            qs = qs.filter(user_id=str(user_id))
        row = qs.first()
        return _feedback_source_to_dict(row) if row else None

    def update_feedback_source(self, source_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row = FeedbackSource.objects.filter(id=str(source_id), type="feedbackSource").first()
        if not row:
            return None
        if "status" in data:
            row.status = data.get("status") or row.status
        if "accountId" in data:
            row.account_id = data.get("accountId") or row.account_id
        if "config" in data:
            row.config = data.get("config") or {}
        if "metadata" in data:
            row.metadata = data.get("metadata") or {}
        row.updated_at = timezone.now()
        row.save()
        return _feedback_source_to_dict(row)

    def delete_feedback_source(self, source_id: str, user_id: Optional[str] = None) -> bool:
        qs = FeedbackSource.objects.filter(id=str(source_id), type="feedbackSource")
        if user_id is not None:
            qs = qs.filter(user_id=str(user_id))
        deleted, _ = qs.delete()
        return deleted > 0

    def get_active_feedback_sources_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        rows = FeedbackSource.objects.filter(
            provider=provider, type="feedbackSource", status="active"
        ).order_by("created_at")
        return [_feedback_source_to_dict(row) for row in rows]

    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        project = Project.objects.create(
            id=data["id"],
            user=UserAccount.objects.filter(id=str(data.get("userId"))).first(),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=data.get("status", "active"),
            external_links=data.get("externalLinks", []),
            metadata={k: v for k, v in data.items() if k not in {
                "id", "userId", "name", "description", "status", "externalLinks",
                "createdAt", "updatedAt", "type",
            }},
            last_analysis_id=data.get("lastAnalysisId", ""),
            last_analyzed_at=datetime.fromisoformat(data["lastAnalyzedAt"]) if data.get("lastAnalyzedAt") else None,
        )
        return _project_to_dict(project)

    def get_projects_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        projects = Project.objects.filter(user_id=str(user_id)).order_by("-created_at")
        return [_project_to_dict(p) for p in projects]

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        project = Project.objects.filter(id=project_id).first()
        return _project_to_dict(project) if project else None

    def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        project = Project.objects.filter(id=project_id, user_id=str(user_id)).first()
        return _project_to_dict(project) if project else None

    def update_project(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        project = Project.objects.get(id=project_id)
        project.name = data.get("name", project.name)
        project.description = data.get("description", project.description)
        project.status = data.get("status", project.status)
        if "externalLinks" in data:
            project.external_links = data.get("externalLinks") or []
        if "lastAnalysisId" in data:
            project.last_analysis_id = data.get("lastAnalysisId") or ""
        if data.get("lastAnalyzedAt"):
            project.last_analyzed_at = datetime.fromisoformat(data["lastAnalyzedAt"])
        project.updated_at = timezone.now()
        project.save()
        return _project_to_dict(project)

    def delete_project(self, project_id: str, user_id: Optional[str] = None) -> bool:
        qs = Project.objects.filter(id=project_id)
        if user_id is not None:
            qs = qs.filter(user_id=str(user_id))
        deleted, _ = qs.delete()
        return deleted > 0

    def check_external_project_exists(self, provider: str, external_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        projects = Project.objects.filter(user_id=str(user_id))
        for project in projects:
            links = project.external_links or []
            for link in links:
                if link.get("provider") == provider and str(link.get("externalId")) == str(external_id):
                    return _project_to_dict(project)
        return None
