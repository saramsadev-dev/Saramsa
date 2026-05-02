"""
Authentication views for user management and authentication.

Contains views for authentication operations:
- User registration and login
- JWT token management
- Profile management
- Password reset functionality
- User listing and details
"""

from http import HTTPStatus
from rest_framework import generics, permissions, serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apis.core.response import StandardResponse
from apis.core.error_handlers import handle_service_errors
from ..services import get_authentication_service

from ..permissions import NoAuthentication, IsSuperAdmin
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
import logging
import uuid
from datetime import datetime, timedelta, timezone
import secrets
from django.conf import settings
from ..serializers import (
    AppUserSerializer, 
    AppUserRegisterWithOtpSerializer,
    AppTokenObtainPairSerializer,
    AppTokenRefreshSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    RegistrationOtpRequestSerializer,
    build_user_auth_context,
)
from ..authentication import AppJWTAuthentication, AppUser
import bcrypt


class RegisterView(generics.CreateAPIView):
    permission_classes = [NoAuthentication]
    serializer_class = AppUserRegisterWithOtpSerializer
    logger = logging.getLogger(__name__)
    
    def get(self, request):
        return StandardResponse.success(
            data={"status": "ok"},
            message="Registration endpoint is available"
        )

    @handle_service_errors
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Use authentication service to create user
        auth_service = get_authentication_service()

        # Verify OTP before creating user
        otp_code = serializer.validated_data.get('otp')
        try:
            auth_service.verify_registration_otp(
                email=serializer.validated_data['email'],
                code=otp_code
            )
        except ValueError as e:
            return StandardResponse.validation_error(detail=str(e), instance=request.path)
        
        user_data = auth_service.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            role=serializer.validated_data.get('role', 'user')
        )

        # Generate JWT tokens for the newly created user
        token_serializer = AppTokenObtainPairSerializer()
        token_data = token_serializer.validate({
            'email': user_data['email'],
            'password': serializer.validated_data['password']
        })

        return StandardResponse.created(
            data={
                "username": user_data['username'],
                "email": user_data['email'],
                "user_id": user_data['id'],
                "user": token_data.get('user'),
                "access": token_data['access'],
                "refresh": token_data['refresh']
            },
            message="User created successfully",
            instance=f"/api/auth/users/{user_data['id']}"
        )


class RegisterOtpRequestView(APIView):
    permission_classes = [NoAuthentication]
    logger = logging.getLogger(__name__)

    @handle_service_errors
    def post(self, request):
        serializer = RegistrationOtpRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_service = get_authentication_service()
        email = serializer.validated_data['email']
        username = serializer.validated_data.get('username') or None

        try:
            result = auth_service.request_registration_otp(email=email, username=username)
        except ValueError as e:
            return StandardResponse.validation_error(detail=str(e), instance=request.path)

        return StandardResponse.success(
            data=result,
            message="Registration code sent successfully"
        )


class AppTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view for PostgreSQL users"""
    serializer_class = AppTokenObtainPairSerializer


class AppTokenRefreshView(TokenRefreshView):
    """Custom token refresh view for PostgreSQL users"""
    serializer_class = AppTokenRefreshSerializer


class ProfileMeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [AppJWTAuthentication]
    
    def get(self, request):
        # Get user from service using username from JWT token
        auth_service = get_authentication_service()
        username = request.user.username
        user_data = auth_service.get_user_by_username(username)
        
        if not user_data:
            return StandardResponse.not_found(
                detail="User not found",
                instance=request.path
            )
        
        # Use the authenticated user's ID directly
        organization_context = auth_service.get_organization_context(user_data)
        return StandardResponse.success(
            data={
                **build_user_auth_context(user_data, organization_context),
                "user_id": request.user.id,
                "company_name": user_data.get('company_name'),
                "company_url": user_data.get('company_url'),
                "avatar_url": user_data.get('avatar_url'),
                "date_joined": user_data.get('date_joined')
            },
            message="Profile retrieved successfully"
        )
    
    @handle_service_errors
    def patch(self, request):
        """Update basic profile fields using service layer."""
        auth_service = get_authentication_service()
        username = request.user.username
        user_doc = auth_service.get_user_by_username(username)
        
        if not user_doc:
            return StandardResponse.not_found(
                detail="User not found",
                instance=request.path
            )

        updatable = {"first_name", "last_name", "email", "company_name", "company_url", "avatar_url"}
        changed = False
        for key in updatable:
            if key in request.data:
                user_doc[key] = request.data.get(key, "")
                changed = True
        
        if changed:
            auth_service.update_user(user_doc['id'], user_doc)
        
        return StandardResponse.success(
            data={
                "username": user_doc.get('username'),
                "email": user_doc.get('email'),
                "first_name": user_doc.get('first_name'),
                "last_name": user_doc.get('last_name'),
            },
            message="Profile updated successfully"
        )


class CheckUsernameView(APIView):
    permission_classes = [NoAuthentication]
    
    def get(self, request):
        username = request.query_params.get('username', '').strip()
        if not username:
            return StandardResponse.validation_error(
                detail="Username parameter is required",
                errors=[{"field": "username", "message": "This parameter is required."}],
                instance=request.path
            )
        
        # Check length
        if len(username) < 3:
            return StandardResponse.success(
                data={
                    "available": False,
                    "message": "Username must be at least 3 characters"
                },
                message="Username validation completed"
            )
        
        # Check character validity
        import re
        if not re.match(r'^[\w.@+-]+\Z', username):
            return StandardResponse.success(
                data={
                    "available": False,
                    "message": "Username can only contain letters, numbers, and @/./+/-/_ characters"
                },
                message="Username validation completed"
            )
        
        # Check availability using service
        auth_service = get_authentication_service()
        username_exists = auth_service.get_user_by_username(username) is not None
        
        return StandardResponse.success(
            data={
                "available": not username_exists,
                "message": "Username is already taken" if username_exists else "Username is available"
            },
            message="Username availability checked"
        )


class UserListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [AppJWTAuthentication]
    
    @handle_service_errors
    def get(self, request):
        """Get all users - admin only."""
        from authentication.permissions import _get_role_from_user
        if _get_role_from_user(request.user) not in ("admin", "superadmin"):
            return StandardResponse.error(
                title="Forbidden",
                detail="Only admins can list all users.",
                status_code=403,
                error_type="forbidden",
                instance=request.path,
            )

        auth_service = get_authentication_service()
        users = auth_service.get_all_users()
        
        for user in users:
            user.pop('password', None)
        
        return StandardResponse.success(
            data={
                "users": users,
                "count": len(users)
            },
            message="Users retrieved successfully"
        )


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [AppJWTAuthentication]
    
    @handle_service_errors
    def get(self, request, user_id):
        """Get specific user by ID - restricted to own profile or admin."""
        if str(user_id) != str(request.user.id):
            return StandardResponse.error(
                title="Forbidden",
                detail="You can only view your own profile.",
                status_code=403,
                error_type="forbidden",
                instance=request.path,
            )

        auth_service = get_authentication_service()
        user_data = auth_service.get_user_by_id(user_id)
        
        if not user_data:
            return StandardResponse.not_found(
                detail=f"User with ID '{user_id}' was not found",
                instance=request.path
            )
        
        if 'password' in user_data:
            del user_data['password']
        
        return StandardResponse.success(
            data=user_data,
            message="User retrieved successfully"
        )


class LoginView(APIView):
    permission_classes = [NoAuthentication]
    
    @handle_service_errors
    def post(self, request):
        """Custom login endpoint using service layer"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return StandardResponse.validation_error(
                detail="Email and password are required",
                errors=[
                    {"field": "email", "message": "This field is required."} if not email else None,
                    {"field": "password", "message": "This field is required."} if not password else None
                ],
                instance=request.path
            )
        
        # Use service for authentication
        auth_service = get_authentication_service()
        user_data = auth_service.get_user_by_email(email)
        
        if not user_data or not auth_service._verify_password(password, user_data.get('password', '')):
            return StandardResponse.unauthorized(
                detail="Invalid credentials",
                instance=request.path
            )
        
        # Check if user is active
        if not user_data.get('is_active', True):
            return StandardResponse.unauthorized(
                detail="User account is disabled",
                instance=request.path
            )
        
        # Generate JWT token
        from ..serializers import AppTokenObtainPairSerializer
        serializer = AppTokenObtainPairSerializer()
        token_data = serializer.validate({
            'email': email,
            'password': password
        })
        
        return StandardResponse.success(
            data=token_data,
            message="Login successful"
        )


class OrganizationsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [AppJWTAuthentication]

    @handle_service_errors
    def get(self, request):
        auth_service = get_authentication_service()
        user_data = auth_service.get_user_by_id(request.user.id)
        if not user_data:
            return StandardResponse.not_found(
                detail="User not found",
                instance=request.path
            )

        organization_context = auth_service.get_organization_context(user_data)
        return StandardResponse.success(
            data=organization_context,
            message="Organizations retrieved successfully"
        )

    @handle_service_errors
    def post(self, request):
        name = (request.data.get("name") or "").strip()
        description = (request.data.get("description") or "").strip()
        if not name:
            return StandardResponse.validation_error(
                detail="Organization name is required.",
                instance=request.path
            )

        from integrations.services import get_organization_service

        organization_service = get_organization_service()
        organization = organization_service.create_organization(
            name=name,
            description=description,
            created_by_user_id=str(request.user.id),
        )
        auth_service = get_authentication_service()
        auth_service.set_active_organization(str(request.user.id), organization["id"])
        organization_context = auth_service.get_organization_context(
            auth_service.get_user_by_id(str(request.user.id))
        )

        return StandardResponse.created(
            data=organization_context,
            message="Organization created successfully",
            instance=f"/api/auth/organizations/{organization['id']}"
        )


class SwitchActiveOrganizationView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [AppJWTAuthentication]

    @handle_service_errors
    def post(self, request):
        organization_id = request.data.get("organization_id")
        if not organization_id:
            return StandardResponse.validation_error(
                detail="organization_id is required.",
                instance=request.path
            )

        auth_service = get_authentication_service()
        try:
            user_data = auth_service.set_active_organization(str(request.user.id), str(organization_id))
        except ValueError as exc:
            return StandardResponse.validation_error(
                detail=str(exc),
                instance=request.path
            )

        organization_context = auth_service.get_organization_context(user_data)
        return StandardResponse.success(
            data=build_user_auth_context(user_data, organization_context),
            message="Active organization updated successfully"
        )


class OrganizationMembersView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [AppJWTAuthentication]

    def _get_active_organization_id(self, request):
        profile = getattr(request.user, "profile", {}) or {}
        if isinstance(profile, dict):
            return profile.get("active_organization_id")
        return None

    @handle_service_errors
    def get(self, request):
        organization_id = self._get_active_organization_id(request)
        if not organization_id:
            return StandardResponse.validation_error(
                detail="Active organization is required.",
                instance=request.path
            )

        from integrations.services import get_organization_service

        organization_service = get_organization_service()
        try:
            result = organization_service.list_members(str(organization_id), str(request.user.id))
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)

        return StandardResponse.success(
            data=result,
            message="Organization members retrieved successfully"
        )

    @handle_service_errors
    def post(self, request):
        organization_id = self._get_active_organization_id(request)
        if not organization_id:
            return StandardResponse.validation_error(
                detail="Active organization is required.",
                instance=request.path
            )

        email = (request.data.get("email") or "").strip() or None
        user_id = (request.data.get("user_id") or "").strip() or None
        role = (request.data.get("role") or "member").strip().lower()
        if not email and not user_id:
            return StandardResponse.validation_error(
                detail="email or user_id is required.",
                instance=request.path
            )

        from integrations.services import get_organization_service

        organization_service = get_organization_service()
        try:
            result = organization_service.add_member(
                str(organization_id),
                str(request.user.id),
                email=email,
                user_id=user_id,
                role=role,
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)

        return StandardResponse.success(
            data=result,
            message="Organization member updated successfully"
        )

    @handle_service_errors
    def delete(self, request):
        organization_id = self._get_active_organization_id(request)
        if not organization_id:
            return StandardResponse.validation_error(
                detail="Active organization is required.",
                instance=request.path
            )

        user_id = (request.data.get("user_id") or request.query_params.get("user_id") or "").strip()
        if not user_id:
            return StandardResponse.validation_error(
                detail="user_id is required.",
                instance=request.path
            )

        from integrations.services import get_organization_service

        organization_service = get_organization_service()
        try:
            result = organization_service.remove_member(
                str(organization_id),
                str(request.user.id),
                str(user_id),
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)

        return StandardResponse.success(
            data=result,
            message="Organization member removed successfully"
        )


class AdminPromptSettingsView(APIView):
    permission_classes = [IsSuperAdmin]
    authentication_classes = [AppJWTAuthentication]

    @handle_service_errors
    def get(self, request):
        organization_id = request.query_params.get("organization_id")
        from integrations.services import get_prompt_override_service

        service = get_prompt_override_service()
        data = service.list_admin_prompt_data(organization_id=organization_id)
        return StandardResponse.success(
            data=data,
            message="Prompt settings retrieved successfully"
        )

    @handle_service_errors
    def post(self, request):
        scope = (request.data.get("scope") or "").strip().lower()
        prompt_type = (request.data.get("prompt_type") or "").strip()
        content = request.data.get("content") or ""
        organization_id = (request.data.get("organization_id") or "").strip() or None

        from integrations.services import get_prompt_override_service

        service = get_prompt_override_service()
        try:
            saved = service.upsert_prompt(
                scope=scope,
                prompt_type=prompt_type,
                content=content,
                updated_by_user_id=str(request.user.id),
                organization_id=organization_id,
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)

        return StandardResponse.success(
            data=saved,
            message="Prompt settings updated successfully"
        )

    @handle_service_errors
    def delete(self, request):
        scope = (request.data.get("scope") or request.query_params.get("scope") or "").strip().lower()
        prompt_type = (request.data.get("prompt_type") or request.query_params.get("prompt_type") or "").strip()
        organization_id = (
            request.data.get("organization_id")
            or request.query_params.get("organization_id")
            or ""
        ).strip() or None

        from integrations.services import get_prompt_override_service

        service = get_prompt_override_service()
        try:
            deleted = service.delete_prompt(
                scope=scope,
                prompt_type=prompt_type,
                organization_id=organization_id,
            )
        except ValueError as exc:
            return StandardResponse.validation_error(detail=str(exc), instance=request.path)

        if not deleted:
            return StandardResponse.not_found(
                detail="Prompt override not found.",
                instance=request.path
            )

        return StandardResponse.success(
            data={},
            message="Prompt override removed successfully"
        )


class ForgotPasswordView(APIView):
    permission_classes = [NoAuthentication]
    logger = logging.getLogger(__name__)
    
    def post(self, request):
        """Generate and send password reset token"""
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            # Use service layer
            auth_service = get_authentication_service()
            
            # Check if user exists
            user_data = auth_service.get_user_by_email(email)
            if not user_data:
                # Don't reveal if email exists for security
                return StandardResponse.success(
                    data={},
                    message="If an account exists with this email, you will receive a password reset link."
                )
            
            # Generate secure token
            token = secrets.token_urlsafe(32)
            
            expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            
            # Save reset token using service layer
            auth_service.save_reset_token(email, token, expires_at)
            
            # Build reset link for frontend
            frontend_base = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")
            if not frontend_base:
                frontend_base = settings.BACKEND_BASE_URL or request.build_absolute_uri("/")[:-1]
            reset_link = f"{frontend_base}/reset-password?token={token}"
            
            # Send email (log failures but do not reveal to client)
            email_sent = auth_service.send_password_reset_email(email, reset_link)
            if not email_sent:
                self.logger.warning("Password reset email failed for %s", email)
            if settings.DEBUG:
                self.logger.info(f"Password reset link for {email}: {reset_link}")
            
            return StandardResponse.success(
                data={
                    # Remove this in production - only for development
                    "reset_link": reset_link if settings.DEBUG else None
                },
                message="If an account exists with this email, you will receive a password reset link."
            )
            
        except Exception as e:
            self.logger.exception(f"Error in forgot password: {e}")
            return StandardResponse.internal_server_error(
                detail="Failed to process password reset request",
                instance=request.path
            )


class ResetPasswordView(APIView):
    permission_classes = [NoAuthentication]
    logger = logging.getLogger(__name__)
    
    def post(self, request):
        """Reset password using token"""
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            # Use service layer
            auth_service = get_authentication_service()
            
            # Get reset token
            token_data = auth_service.get_reset_token(token)
            if not token_data:
                return StandardResponse.validation_error(
                    detail="Invalid or expired reset token",
                    errors=[{"field": "token", "message": "This token is invalid or has expired."}],
                    instance=request.path
                )
            
            # Check if token is used
            if token_data.get('used', False):
                return StandardResponse.error(
                    title="Token already used",
                    detail="This reset link has already been used",
                    status_code=400,
                    error_type="token-already-used",
                    instance=request.path
                )
            
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                return StandardResponse.error(
                    title="Token expired",
                    detail="This reset link has expired",
                    status_code=400,
                    error_type="token-expired",
                    instance=request.path
                )
            
            # Get user by email using service layer
            email = token_data['email']
            user_data = auth_service.get_user_by_email(email)
            if not user_data:
                return StandardResponse.not_found(
                    detail="User not found",
                    instance=request.path
                )
            
            # Hash new password
            hashed_password = ResetPasswordSerializer().hash_password(new_password)
            
            # Update user password using service layer
            user_data['password'] = hashed_password
            auth_service.save_user(user_data)
            
            # Mark token as used using service layer
            auth_service.mark_reset_token_used(token)
            
            return StandardResponse.success(
                data={},
                message="Password has been reset successfully"
            )
            
        except Exception as e:
            self.logger.exception(f"Error in reset password: {e}")
            return StandardResponse.internal_server_error(
                detail="Failed to reset password",
                instance=request.path
            )

