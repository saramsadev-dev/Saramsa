"""
User repository for user-related data operations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from apis.infrastructure.cosmos_service import cosmos_service
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self):
        self.cosmos_service = cosmos_service
        self.container_name = 'users'
        self.entity_type = "user"
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user document."""
        try:
            data['type'] = self.entity_type
            return self.cosmos_service.create_document(self.container_name, data)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            return self.cosmos_service.get_document(
                self.container_name, 
                user_id, 
                user_id
            )
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        query = "SELECT * FROM c WHERE c.username = @username AND c.type = @type"
        parameters = [
            {"name": "@username", "value": username},
            {"name": "@type", "value": self.entity_type}
        ]
        results = self.cosmos_service.query_documents(self.container_name, query, parameters)
        return results[0] if results else None
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        query = "SELECT * FROM c WHERE c.email = @email AND c.type = @type"
        parameters = [
            {"name": "@email", "value": email},
            {"name": "@type", "value": self.entity_type}
        ]
        results = self.cosmos_service.query_documents(self.container_name, query, parameters)
        return results[0] if results else None
    
    def update(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user document."""
        try:
            return self.cosmos_service.update_document(
                self.container_name,
                user_id,
                user_id,  # partition_key
                data      # data
            )
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all users."""
        query = "SELECT * FROM c WHERE c.type = @type"
        parameters = [{"name": "@type", "value": self.entity_type}]
        return self.cosmos_service.query_documents(self.container_name, query, parameters)

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with proper validation."""
        # Check if user already exists
        if self.get_by_username(user_data['username']):
            raise ValueError(f"User with username '{user_data['username']}' already exists")
        
        if self.get_by_email(user_data['email']):
            raise ValueError(f"User with email '{user_data['email']}' already exists")
        
        return self.create(user_data)
    
    # Password reset methods
    def save_reset_token(self, email: str, token: str, expires_at: str) -> Dict[str, Any]:
        """Save password reset token."""
        try:
            token_data = {
                "id": f"reset_token_{token}",
                "type": "password_reset_token",
                "email": email,
                "token": token,
                "expires_at": expires_at,
                "used": False,
                "created_at": datetime.now().isoformat()
            }
            return self.cosmos_service.create_document('password_resets', token_data)
        except Exception as e:
            logger.error(f"Error saving reset token: {e}")
            raise
    
    def get_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get password reset token."""
        try:
            return self.cosmos_service.get_document('password_resets', f"reset_token_{token}", f"reset_token_{token}")
        except Exception as e:
            logger.error(f"Error getting reset token: {e}")
            return None
    
    def mark_reset_token_used(self, token: str) -> bool:
        """Mark password reset token as used."""
        try:
            token_data = self.get_reset_token(token)
            if token_data:
                token_data['used'] = True
                token_data['used_at'] = datetime.now().isoformat()
                self.cosmos_service.update_document('password_resets', f"reset_token_{token}", f"reset_token_{token}", token_data)
                return True
            return False
        except Exception as e:
            logger.error(f"Error marking reset token as used: {e}")
            return False
    
    def save_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save/update user data."""
        try:
            return self.cosmos_service.update_document(
                self.container_name,
                user_data['id'],
                user_data['id'],  # partition_key
                user_data         # data
            )
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            raise

    # Registration OTP methods
    def save_registration_otp(self, otp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update registration OTP entry."""
        try:
            return self.cosmos_service.update_document(
                'registration_otps',
                otp_data['id'],
                otp_data['email'],  # partition_key
                otp_data
            )
        except Exception as e:
            logger.error(f"Error saving registration OTP: {e}")
            raise

    def get_registration_otp(self, email: str) -> Optional[Dict[str, Any]]:
        """Get registration OTP entry by email."""
        try:
            return self.cosmos_service.get_document('registration_otps', f"reg_otp:{email}", email)
        except Exception as e:
            logger.error(f"Error getting registration OTP for {email}: {e}")
            return None

    def delete_registration_otp(self, email: str) -> bool:
        """Delete registration OTP entry by email."""
        try:
            return self.cosmos_service.delete_document('registration_otps', f"reg_otp:{email}", email)
        except Exception as e:
            logger.error(f"Error deleting registration OTP for {email}: {e}")
            return False
