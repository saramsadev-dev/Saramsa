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

    def update_organization(
        self,
        organization_id: str,
        actor_user_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        actor_membership = self.require_membership(organization_id, actor_user_id)
        if not self.has_min_role(actor_membership, "admin"):
            raise ValueError("Only workspace admins can rename or update the workspace.")

        updates: Dict[str, Any] = {}
        if name is not None:
            cleaned = name.strip()
            if not cleaned:
                raise ValueError("Workspace name cannot be empty.")
            updates["name"] = cleaned
            updates["slug"] = self._ensure_unique_slug(self._slugify(cleaned))
        if description is not None:
            updates["description"] = description.strip()

        if not updates:
            return self.repo.get_organization_by_id(organization_id)
        return self.repo.update_organization(organization_id, updates)

    def transfer_ownership(
        self,
        organization_id: str,
        actor_user_id: str,
        new_owner_user_id: str,
    ) -> Dict[str, Any]:
        """Hand the owner role to another existing member. Caller must be
        the current owner; the new owner must already be a member."""
        actor_membership = self.require_membership(organization_id, actor_user_id)
        if actor_membership.get("role") != "owner":
            raise ValueError("Only the current owner can transfer ownership.")
        if str(new_owner_user_id) == str(actor_user_id):
            raise ValueError("You already own this workspace.")

        target_membership = self.repo.get_organization_membership(
            organization_id, str(new_owner_user_id)
        )
        if not target_membership:
            raise ValueError("Target user is not a member of this workspace.")

        # Demote current owner first so the upsert below doesn't see two
        # owner rows in transit.
        self.repo.upsert_organization_membership(
            organization_id, str(actor_user_id), "admin", actor_id=str(actor_user_id),
        )
        self.repo.upsert_organization_membership(
            organization_id, str(new_owner_user_id), "owner", actor_id=str(actor_user_id),
        )
        return self.list_members(organization_id, str(actor_user_id))

    def delete_organization(self, organization_id: str, actor_user_id: str) -> Dict[str, Any]:
        """Hard-delete a workspace. Cascades to memberships, prompt
        overrides, projects, integrations, feedback sources via the FKs
        already declared with on_delete=CASCADE in the org-management
        migration. Members whose active workspace was this one will need
        to be redirected to another org on their next request."""
        actor_membership = self.require_membership(organization_id, actor_user_id)
        if actor_membership.get("role") != "owner":
            raise ValueError("Only the workspace owner can delete the workspace.")

        from ..models import Organization

        organization = Organization.objects.filter(id=organization_id).first()
        if not organization:
            raise ValueError("Workspace not found.")

        # Reassign every user whose active org was this one to one of
        # their remaining workspaces (or clear it). This avoids the
        # frontend showing "no workspace" with a broken state.
        from authentication.models import UserAccount

        memberships = self.repo.list_organization_memberships(organization_id)
        affected_user_ids = [m["userId"] for m in memberships]

        organization.delete()

        for uid in affected_user_ids:
            user = UserAccount.objects.filter(id=uid).first()
            if not user:
                continue
            profile = user.profile or {}
            if profile.get("active_organization_id") == organization_id:
                remaining = self.list_organizations_for_user(uid)
                profile["active_organization_id"] = remaining[0]["id"] if remaining else None
                user.profile = profile
                user.save(update_fields=["profile", "updated_at"])

        return {"deleted_organization_id": organization_id}

    def get_organization_context_for_user(
        self,
        user: Dict[str, Any],
        active_organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        organizations = self.list_organizations_for_user(str(user["id"]))

        # Saramsa is invite-only: an org membership only exists by invitation
        # acceptance. A user with no orgs gets an empty context — never an
        # auto-bootstrapped personal workspace.
        if not organizations:
            return {
                "organizations": [],
                "active_organization": None,
                "active_organization_id": None,
            }

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
