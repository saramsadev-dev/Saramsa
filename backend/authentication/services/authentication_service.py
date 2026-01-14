"""
Authentication service for user-related business logic.

This service handles the business logic for user authentication, registration,
password management, and user profile operations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
import bcrypt
from ..repositories import UserRepository
import logging

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service for authentication business logic."""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def create_user(self, username: str, email: str, password: str, 
                   first_name: str = "", last_name: str = "", 
                   role: str = "user") -> Dict[str, Any]:
        """Create a new user with hashed password."""
        try:
            # Hash password
            hashed_password = self._hash_password(password)
            
            # Create user data
            user_data = {
                "id": f"user_{uuid.uuid4().hex[:12]}",
                "username": username,
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
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password."""
        try:
            user = self.user_repo.get_by_username(username)
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
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        return self.user_repo.get_by_username(username)
    
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
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        try:
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise ValueError("Failed to hash password")
    
    def _verify_password(self, password: str, stored_password: str) -> bool:
        """Verify password against stored bcrypt hash."""
        try:
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
            
            password_bytes = password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, stored_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False


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