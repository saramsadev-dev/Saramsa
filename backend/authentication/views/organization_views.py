"""Organization & prompt-override admin endpoints.

Lives next to authentication_views so it can reuse the JWT auth class and
the AuthenticationService, but the actual org/prompt logic delegates to
integrations.services.{organization,prompt_override}_service.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apis.core.error_handlers import handle_service_errors
from apis.core.response import StandardResponse

from rest_framework_simplejwt.tokens import RefreshToken

from ..authentication import AppJWTAuthentication
from ..org_context import build_user_with_org_context
from ..permissions import IsSuperAdmin
from ..services import get_authentication_service


def _issue_token_pair(user_data):
    """Mint a fresh JWT pair carrying the (possibly updated) active org claim.
    Lets the org-switch endpoint hand the frontend a token that already
    reflects the new tenant — no separate /refresh round-trip needed."""
    profile = user_data.get('profile') or {}
    active_org_id = profile.get('active_organization_id')
    refresh = RefreshToken()
    refresh['user_id'] = user_data.get('id')
    refresh['email'] = user_data.get('email')
    refresh['is_staff'] = user_data.get('is_staff', False)
    refresh['profile_role'] = profile.get('role', 'user')
    if active_org_id:
        refresh['active_organization_id'] = active_org_id
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def _active_organization_id(request):
    profile = getattr(request.user, "profile", None)
    if isinstance(profile, dict):
        return profile.get("active_organization_id")
    return None


class OrganizationsView(APIView):
    """List the caller's organizations or create a new one."""

    authentication_classes = [AppJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @handle_service_errors
    def get(self, request):
        auth_service = get_authentication_service()
        user_data = auth_service.get_user_by_id(request.user.id)
        if not user_data:
            return StandardResponse.not_found(detail="User not found", instance=request.path)
        return StandardResponse.success(
            data=auth_service.get_organization_context(user_data),
            message="Organizations retrieved successfully",
        )

    @handle_service_errors
    def post(self, request):
        from integrations.services import get_organization_service

        name = (request.data.get("name") or "").strip()
        description = (request.data.get("description") or "").strip()
        if not name:
            return StandardResponse.validation_error(
                detail="Organization name is required.", instance=request.path
            )

        org_service = get_organization_service()
        organization = org_service.create_organization(
            name=name,
            description=description,
            created_by_user_id=str(request.user.id),
        )
        auth_service = get_authentication_service()
        auth_service.set_active_organization(str(request.user.id), organization["id"])
        context = auth_service.get_organization_context(
            auth_service.get_user_by_id(str(request.user.id))
        )
        return StandardResponse.created(
            data=context,
            message="Organization created successfully",
            instance=f"/api/auth/organizations/{organization['id']}",
        )


class SwitchActiveOrganizationView(APIView):
    authentication_classes = [AppJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @handle_service_errors
    def post(self, request):
        organization_id = request.data.get("organization_id")
        if not organization_id:
            return StandardResponse.validation_error(
                detail="organization_id is required.", instance=request.path
            )

        auth_service = get_authentication_service()
        try:
            user_data = auth_service.set_active_organization(
                str(request.user.id), str(organization_id)
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)

        return StandardResponse.success(
            data={
                "user": build_user_with_org_context(user_data),
                **_issue_token_pair(user_data),
            },
            message="Active organization updated successfully",
        )


class OrganizationDetailView(APIView):
    """Manage the caller's active workspace: rename, transfer ownership,
    delete. All gated to admin/owner roles inside the service layer."""

    authentication_classes = [AppJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @handle_service_errors
    def patch(self, request):
        from integrations.services import get_organization_service

        organization_id = _active_organization_id(request)
        if not organization_id:
            return StandardResponse.validation_error(
                detail="Active organization is required.", instance=request.path
            )
        name = request.data.get("name") if "name" in request.data else None
        description = request.data.get("description") if "description" in request.data else None
        try:
            updated = get_organization_service().update_organization(
                str(organization_id), str(request.user.id),
                name=name, description=description,
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)

        # Echo the fresh user payload so the frontend's org switcher and
        # navbar pick up the new name without an extra /me round-trip.
        auth_service = get_authentication_service()
        return StandardResponse.success(
            data={
                "organization": updated,
                "user": build_user_with_org_context(auth_service.get_user_by_id(str(request.user.id))),
            },
            message="Workspace updated successfully",
        )

    @handle_service_errors
    def delete(self, request):
        from integrations.services import get_organization_service

        organization_id = _active_organization_id(request)
        if not organization_id:
            return StandardResponse.validation_error(
                detail="Active organization is required.", instance=request.path
            )
        try:
            get_organization_service().delete_organization(
                str(organization_id), str(request.user.id),
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)

        # The user's active org just got reassigned (or cleared) inside
        # delete_organization; mint a fresh JWT so the new active org
        # claim travels with the response.
        auth_service = get_authentication_service()
        user_data = auth_service.get_user_by_id(str(request.user.id))
        return StandardResponse.success(
            data={
                "user": build_user_with_org_context(user_data),
                **_issue_token_pair(user_data),
            },
            message="Workspace deleted successfully",
        )


class OrganizationTransferView(APIView):
    """POST { new_owner_user_id } to hand the workspace to another member."""

    authentication_classes = [AppJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @handle_service_errors
    def post(self, request):
        from integrations.services import get_organization_service

        organization_id = _active_organization_id(request)
        if not organization_id:
            return StandardResponse.validation_error(
                detail="Active organization is required.", instance=request.path
            )
        new_owner_user_id = (request.data.get("new_owner_user_id") or "").strip()
        if not new_owner_user_id:
            return StandardResponse.validation_error(
                detail="new_owner_user_id is required.", instance=request.path
            )
        try:
            result = get_organization_service().transfer_ownership(
                str(organization_id), str(request.user.id), new_owner_user_id,
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)
        return StandardResponse.success(
            data=result, message="Workspace ownership transferred successfully"
        )


class OrganizationMembersView(APIView):
    """List/add/remove members of the caller's active organization."""

    authentication_classes = [AppJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @handle_service_errors
    def get(self, request):
        from integrations.services import get_organization_service

        organization_id = _active_organization_id(request)
        if not organization_id:
            return StandardResponse.validation_error(
                detail="Active organization is required.", instance=request.path
            )
        try:
            result = get_organization_service().list_members(
                str(organization_id), str(request.user.id)
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)
        return StandardResponse.success(
            data=result, message="Organization members retrieved successfully"
        )

    @handle_service_errors
    def post(self, request):
        from integrations.services import get_organization_service

        organization_id = _active_organization_id(request)
        if not organization_id:
            return StandardResponse.validation_error(
                detail="Active organization is required.", instance=request.path
            )
        email = (request.data.get("email") or "").strip() or None
        user_id = (request.data.get("user_id") or "").strip() or None
        role = (request.data.get("role") or "member").strip().lower()
        if not email and not user_id:
            return StandardResponse.validation_error(
                detail="email or user_id is required.", instance=request.path
            )
        try:
            result = get_organization_service().add_member(
                str(organization_id),
                str(request.user.id),
                email=email,
                user_id=user_id,
                role=role,
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)
        return StandardResponse.success(
            data=result, message="Organization member updated successfully"
        )

    @handle_service_errors
    def delete(self, request):
        from integrations.services import get_organization_service

        organization_id = _active_organization_id(request)
        if not organization_id:
            return StandardResponse.validation_error(
                detail="Active organization is required.", instance=request.path
            )
        user_id = (
            request.data.get("user_id") or request.query_params.get("user_id") or ""
        ).strip()
        if not user_id:
            return StandardResponse.validation_error(
                detail="user_id is required.", instance=request.path
            )
        try:
            result = get_organization_service().remove_member(
                str(organization_id), str(request.user.id), str(user_id)
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)
        return StandardResponse.success(
            data=result, message="Organization member removed successfully"
        )


class AdminPromptSettingsView(APIView):
    """Platform-wide and per-organization prompt overrides. Superadmin only."""

    authentication_classes = [AppJWTAuthentication]
    permission_classes = [IsSuperAdmin]

    @handle_service_errors
    def get(self, request):
        from integrations.services import get_prompt_override_service

        organization_id = request.query_params.get("organization_id")
        return StandardResponse.success(
            data=get_prompt_override_service().list_admin_prompt_data(
                organization_id=organization_id
            ),
            message="Prompt settings retrieved successfully",
        )

    @handle_service_errors
    def post(self, request):
        from integrations.services import get_prompt_override_service

        scope = (request.data.get("scope") or "").strip().lower()
        prompt_type = (request.data.get("prompt_type") or "").strip()
        content = request.data.get("content") or ""
        organization_id = (request.data.get("organization_id") or "").strip() or None
        try:
            saved = get_prompt_override_service().upsert_prompt(
                scope=scope,
                prompt_type=prompt_type,
                content=content,
                updated_by_user_id=str(request.user.id),
                organization_id=organization_id,
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)
        return StandardResponse.success(data=saved, message="Prompt settings updated successfully")

    @handle_service_errors
    def delete(self, request):
        from integrations.services import get_prompt_override_service

        scope = (
            request.data.get("scope") or request.query_params.get("scope") or ""
        ).strip().lower()
        prompt_type = (
            request.data.get("prompt_type") or request.query_params.get("prompt_type") or ""
        ).strip()
        organization_id = (
            request.data.get("organization_id")
            or request.query_params.get("organization_id")
            or ""
        ).strip() or None
        try:
            deleted = get_prompt_override_service().delete_prompt(
                scope=scope, prompt_type=prompt_type, organization_id=organization_id
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)
        if not deleted:
            return StandardResponse.not_found(
                detail="Prompt override not found.", instance=request.path
            )
        return StandardResponse.success(data={}, message="Prompt override removed successfully")
