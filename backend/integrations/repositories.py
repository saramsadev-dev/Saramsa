"""
Integrations repository for integration-related data operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from django.forms.models import model_to_dict
from django.utils import timezone

from authentication.models import UserAccount
from .models import IntegrationAccount, Project


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
    return data


class IntegrationsRepository:
    """Repository for integrations operations."""

    def __init__(self):
        self.entity_type = "integration_account"

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

    def delete_project(self, project_id: str) -> bool:
        deleted, _ = Project.objects.filter(id=project_id).delete()
        return deleted > 0

    def check_external_project_exists(self, provider: str, external_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        projects = Project.objects.filter(user_id=str(user_id))
        for project in projects:
            links = project.external_links or []
            for link in links:
                if link.get("provider") == provider and str(link.get("externalId")) == str(external_id):
                    return _project_to_dict(project)
        return None

