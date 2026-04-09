"""
Authentication service for user-related business logic.

This service handles the business logic for user authentication, registration,
password management, and user profile operations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import uuid
import hashlib
import secrets
from django.contrib.auth.hashers import make_password, check_password
from ..repositories import UserRepository
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service for authentication business logic."""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def create_user(self, email: str, password: str,
                   first_name: str = "", last_name: str = "",
                   role: str = "user") -> Dict[str, Any]:
        """Create a new user with hashed password."""
        try:
            # Hash password
            hashed_password = self._hash_password(password)
            
            # Create user data
            user_data = {
                "id": f"user_{uuid.uuid4().hex[:12]}",
                "email": email,
                "password": hashed_password,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "is_staff": False,
                "date_joined": datetime.now(timezone.utc).isoformat(),
                "profile": {
                    "role": role
                },
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat()
            }
            
            return self.user_repo.create_user(user_data)
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password (Django passes this as `username`)."""
        try:
            user = self.user_repo.get_by_email(email)
            if not user:
                return None
            
            if not user.get('is_active', False):
                return None
            
            # Verify password
            if self._verify_password(password, user.get('password', '')):
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return self.user_repo.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        return self.user_repo.get_by_email(email)
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data."""
        try:
            user_data['updatedAt'] = datetime.now(timezone.utc).isoformat()
            return self.user_repo.update(user_id, user_data)
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        try:
            return self.user_repo.get_all()
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            raise
    
    # Password reset methods
    def save_reset_token(self, email: str, token: str, expires_at: str) -> Dict[str, Any]:
        """Save password reset token."""
        return self.user_repo.save_reset_token(email, token, expires_at)
    
    def get_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get password reset token."""
        return self.user_repo.get_reset_token(token)
    
    def mark_reset_token_used(self, token: str) -> bool:
        """Mark password reset token as used."""
        return self.user_repo.mark_reset_token_used(token)
    
    def save_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save/update user data."""
        return self.user_repo.save_user(user_data)

    def change_password(self, email: str, new_password: str) -> bool:
        """Set a new hashed password for the user identified by email."""
        from authentication.models import UserAccount
        user = UserAccount.objects.filter(email=email).first()
        if not user:
            return False
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        return True

    def send_password_reset_email(self, email: str, reset_link: str) -> bool:
        """Send password reset email with a secure link."""
        subject = getattr(settings, "PASSWORD_RESET_EMAIL_SUBJECT", "Reset your Saramsa password")
        from_email = getattr(settings, "PASSWORD_RESET_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL)

        text_body = (
            "You requested a password reset for your Saramsa account.\n\n"
            f"Reset your password using this link:\n{reset_link}\n\n"
            "If you did not request this, you can ignore this email."
        )

        html_body = (
            "<p>You requested a password reset for your Saramsa account.</p>"
            f"<p><a href=\"{reset_link}\">Reset your password</a></p>"
            "<p>If you did not request this, you can ignore this email.</p>"
        )

        try:
            message = EmailMultiAlternatives(subject, text_body, from_email, [email])
            message.attach_alternative(html_body, "text/html")
            message.send(fail_silently=False)
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False

    # Registration OTP methods
    def request_registration_otp(self, email: str) -> Dict[str, Any]:
        """Generate and send registration OTP to email."""
        if self.user_repo.get_by_email(email):
            raise ValueError("Email already exists")

        now = datetime.now(timezone.utc)
        ttl_minutes = getattr(settings, "REGISTRATION_OTP_TTL_MINUTES", 10)
        cooldown_seconds = getattr(settings, "REGISTRATION_OTP_RESEND_COOLDOWN_SECONDS", 60)

        existing = self.user_repo.get_registration_otp(email)
        if existing:
            last_sent_at = self._parse_iso_datetime(existing.get("last_sent_at"))
            if last_sent_at:
                elapsed = (now - last_sent_at).total_seconds()
                if elapsed < cooldown_seconds:
                    remaining = int(cooldown_seconds - elapsed)
                    raise ValueError(f"Please wait {remaining} seconds before requesting a new code.")

        code = f"{secrets.randbelow(1000000):06d}"
        otp_hash = self._hash_otp(code)
        expires_at = (now + timedelta(minutes=ttl_minutes)).isoformat()

        send_count = 1
        attempts = 0
        if existing:
            send_count = int(existing.get("send_count", 0)) + 1
            attempts = int(existing.get("attempts", 0))

        payload = {
            "id": f"reg_otp:{email}",
            "type": "registration_otp",
            "email": email,
            "otp_hash": otp_hash,
            "expires_at": expires_at,
            "attempts": attempts,
            "max_attempts": getattr(settings, "REGISTRATION_OTP_MAX_ATTEMPTS", 5),
            "send_count": send_count,
            "last_sent_at": now.isoformat(),
            "created_at": existing.get("created_at") if existing else now.isoformat(),
            "updated_at": now.isoformat(),
            "used": False,
        }

        self.user_repo.save_registration_otp(payload)
        self.send_registration_otp_email(email, code, ttl_minutes)

        return {
            "email": email,
            "expires_in_seconds": int(ttl_minutes * 60),
            "cooldown_seconds": int(cooldown_seconds)
        }

    def verify_registration_otp(self, email: str, code: str) -> None:
        """Verify registration OTP or raise ValueError."""
        if getattr(settings, "REGISTRATION_OTP_BYPASS", False):
            logger.warning("Registration OTP bypass is enabled; skipping verification.")
            return
        entry = self.user_repo.get_registration_otp(email)
        if not entry:
            raise ValueError("OTP not found. Please request a new code.")
        if entry.get("used"):
            raise ValueError("OTP already used. Please request a new code.")

        now = datetime.now(timezone.utc)
        expires_at = self._parse_iso_datetime(entry.get("expires_at"))
        if expires_at and now > expires_at:
            raise ValueError("OTP has expired. Please request a new code.")

        max_attempts = int(entry.get("max_attempts") or getattr(settings, "REGISTRATION_OTP_MAX_ATTEMPTS", 5))
        attempts = int(entry.get("attempts", 0))
        if attempts >= max_attempts:
            raise ValueError("OTP attempt limit reached. Please request a new code.")

        if not secrets.compare_digest(self._hash_otp(code), entry.get("otp_hash", "")):
            entry["attempts"] = attempts + 1
            entry["updated_at"] = now.isoformat()
            self.user_repo.save_registration_otp(entry)
            raise ValueError("Invalid OTP code.")

        entry["used"] = True
        entry["used_at"] = now.isoformat()
        entry["updated_at"] = now.isoformat()
        self.user_repo.save_registration_otp(entry)

    def send_registration_otp_email(self, email: str, code: str, ttl_minutes: int) -> bool:
        """Send registration OTP email."""
        subject = getattr(settings, "REGISTRATION_OTP_EMAIL_SUBJECT", "Your Saramsa registration code")
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@saramsa.ai")

        text_body = (
            "Use the code below to complete your Saramsa registration:\n\n"
            f"{code}\n\n"
            f"This code expires in {ttl_minutes} minutes."
        )

        html_body = (
            "<p>Use the code below to complete your Saramsa registration:</p>"
            f"<p style=\"font-size: 20px; font-weight: bold; letter-spacing: 2px;\">{code}</p>"
            f"<p>This code expires in {ttl_minutes} minutes.</p>"
        )

        try:
            message = EmailMultiAlternatives(subject, text_body, from_email, [email])
            message.attach_alternative(html_body, "text/html")
            message.send(fail_silently=False)
            return True
        except Exception as e:
            logger.error(f"Failed to send registration OTP email to {email}: {e}")
            return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password using Django's make_password."""
        return make_password(password)

    def _verify_password(self, password: str, stored_password: str) -> bool:
        """Verify password against stored hash.

        Supports legacy raw bcrypt ($2b$) and Django-format hashes.
        """
        try:
            # Django-format hashes (pbkdf2_sha256$..., bcrypt$$2b$..., etc.)
            if check_password(password, stored_password):
                return True

            # Legacy: raw bcrypt hash stored without Django prefix
            if stored_password.startswith('$2b$') or stored_password.startswith('$2a$'):
                import bcrypt
                return bcrypt.checkpw(
                    password.encode('utf-8'),
                    stored_password.encode('utf-8') if isinstance(stored_password, str) else stored_password
                )

            return False
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def _hash_otp(self, code: str) -> str:
        payload = f"{code}{settings.SECRET_KEY}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _parse_iso_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None


# Global service instance
_authentication_service = None

def get_authentication_service() -> AuthenticationService:
    """Get the global authentication service instance."""
    global _authentication_service
    if _authentication_service is None:
        _authentication_service = AuthenticationService()
    return _authentication_service


# Legacy alias for backward compatibility
def get_user_service() -> AuthenticationService:
    """Legacy alias - use get_authentication_service() instead."""
    return get_authentication_service()
