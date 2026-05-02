import re
import uuid
from typing import Any, Dict, List, Optional

from ..repositories import IntegrationsRepository
from authentication.repositories import UserRepository


class OrganizationService:
    _ROLE_ORDER = {
        "viewer": 1,
        "member": 2,
        "admin": 3,
        "owner": 4,
    }

    def __init__(self):
        self.repo = IntegrationsRepository()
        self.user_repo = UserRepository()

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or f"organization-{uuid.uuid4().hex[:6]}"

    def _ensure_unique_slug(self, base_slug: str) -> str:
        slug = base_slug
        counter = 1
        while self.repo.get_organization_by_slug(slug):
            counter += 1
            slug = f"{base_slug}-{counter}"
        return slug

    def create_organization(
        self,
        *,
        name: str,
        created_by_user_id: str,
        description: str = "",
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        base_slug = self._slugify(name)
        organization = self.repo.create_organization(
            {
                "id": f"org_{uuid.uuid4().hex[:12]}",
                "name": name.strip(),
                "slug": self._ensure_unique_slug(base_slug),
                "description": description,
                "settings": settings or {},
                "metadata": {},
                "createdByUserId": created_by_user_id,
            }
        )
        self.repo.upsert_organization_membership(
            organization["id"],
            created_by_user_id,
            "owner",
            actor_id=created_by_user_id,
        )
        return organization

    def ensure_default_organization_for_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(user["id"])
        organizations = self.list_organizations_for_user(user_id)
        if organizations:
            return organizations[0]

        name = (
            user.get("company_name")
            or f"{user.get('first_name', '').strip()} {user.get('last_name', '').strip()}".strip()
            or user.get("username")
            or "My Workspace"
        )
        if not name.lower().endswith("workspace"):
            name = f"{name} Workspace"
        organization = self.create_organization(name=name, created_by_user_id=user_id)
        self.repo.assign_legacy_records_to_organization(user_id, organization["id"])
        return organization

    def list_organizations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        organizations = self.repo.list_organizations_for_user(user_id)
        memberships = {
            item["organizationId"]: item
            for org in organizations
            for item in [self.repo.get_organization_membership(org["id"], user_id)]
            if item
        }
        enriched = []
        for org in organizations:
            membership = memberships.get(org["id"])
            enriched.append(
                {
                    **org,
                    "membership": membership,
                    "role": membership.get("role") if membership else None,
                }
            )
        return enriched

    def get_membership(self, organization_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_organization_membership(organization_id, user_id)

    def require_membership(self, organization_id: str, user_id: str) -> Dict[str, Any]:
        membership = self.get_membership(organization_id, user_id)
        if not membership:
            raise ValueError("You do not have access to this organization.")
        return membership

    def has_min_role(self, membership: Optional[Dict[str, Any]], required_role: str) -> bool:
        if not membership:
            return False
        return self._ROLE_ORDER.get(membership.get("role"), 0) >= self._ROLE_ORDER.get(required_role, 0)

    def list_members(self, organization_id: str, actor_user_id: str) -> Dict[str, Any]:
        membership = self.require_membership(organization_id, actor_user_id)
        organization = self.repo.get_organization_by_id(organization_id)
        memberships = self.repo.list_organization_memberships(organization_id)
        members = []
        for item in memberships:
            user = self.user_repo.get_by_id(item["userId"])
            if not user:
                continue
            members.append(
                {
                    "membership_id": item["id"],
                    "user_id": user["id"],
                    "email": user.get("email"),
                    "username": user.get("username"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                    "role": item.get("role"),
                    "status": item.get("status"),
                    "is_current_user": str(user["id"]) == str(actor_user_id),
                }
            )
        return {
            "organization": organization,
            "current_membership": membership,
            "members": members,
        }

    def add_member(
        self,
        organization_id: str,
        actor_user_id: str,
        *,
        email: Optional[str] = None,
        user_id: Optional[str] = None,
        role: str = "member",
    ) -> Dict[str, Any]:
        actor_membership = self.require_membership(organization_id, actor_user_id)
        if not self.has_min_role(actor_membership, "admin"):
            raise ValueError("Only workspace admins can manage members.")
        if role not in ("viewer", "member", "admin"):
            raise ValueError("Role must be viewer, member, or admin.")

        target_user = None
        if user_id:
            target_user = self.user_repo.get_by_id(str(user_id))
        elif email:
            target_user = self.user_repo.get_by_email(str(email).strip())

        if not target_user:
            raise ValueError("User not found.")

        membership = self.repo.get_organization_membership(organization_id, target_user["id"])
        if membership and membership.get("role") == "owner":
            raise ValueError("Owner role cannot be modified.")

        self.repo.upsert_organization_membership(
            organization_id,
            target_user["id"],
            role,
            actor_id=actor_user_id,
        )
        return self.list_members(organization_id, actor_user_id)

    def remove_member(self, organization_id: str, actor_user_id: str, target_user_id: str) -> Dict[str, Any]:
        actor_membership = self.require_membership(organization_id, actor_user_id)
        if not self.has_min_role(actor_membership, "admin"):
            raise ValueError("Only workspace admins can manage members.")

        membership = self.repo.get_organization_membership(organization_id, target_user_id)
        if not membership:
            raise ValueError("Member not found.")
        if membership.get("role") == "owner":
            raise ValueError("Owner membership cannot be removed.")
        if str(target_user_id) == str(actor_user_id):
            raise ValueError("Use another admin account to remove yourself from the workspace.")

        self.repo.delete_organization_membership(organization_id, target_user_id)
        return self.list_members(organization_id, actor_user_id)

    def get_organization_context_for_user(
        self,
        user: Dict[str, Any],
        active_organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        organizations = self.list_organizations_for_user(str(user["id"]))
        if not organizations:
            default_org = self.ensure_default_organization_for_user(user)
            organizations = self.list_organizations_for_user(str(user["id"])) or [default_org]

        selected = None
        if active_organization_id:
            selected = next((org for org in organizations if org["id"] == active_organization_id), None)
        if selected is None:
            selected = organizations[0]
        if selected:
            self.repo.assign_legacy_records_to_organization(str(user["id"]), selected["id"])

        return {
            "organizations": organizations,
            "active_organization": selected,
            "active_organization_id": selected["id"] if selected else None,
        }


_organization_service = None


def get_organization_service() -> OrganizationService:
    global _organization_service
    if _organization_service is None:
        _organization_service = OrganizationService()
    return _organization_service
