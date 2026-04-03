from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .services import get_user_service
import bcrypt
import base64
import json
from datetime import datetime, timedelta
import jwt
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AppUser:
    """Custom user class for PostgreSQL users"""
    
    def __init__(self, user_data):
        self.user_data = user_data
        self.id = user_data.get('id')
        self.pk = self.id
        self.email = user_data.get('email') or ''
        self.first_name = user_data.get('first_name', '')
        self.last_name = user_data.get('last_name', '')
        self.is_active = user_data.get('is_active', True)
        self.is_staff = user_data.get('is_staff', False)
        self.is_authenticated = True
        self.is_anonymous = False
        self.date_joined = user_data.get('date_joined')
        self.profile = user_data.get('profile', {})
    
    def get_username(self):
        """Django expects a username; we use email as the human identifier."""
        return self.email

    @property
    def username(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def has_perm(self, perm, obj=None):
        return self.is_staff
    
    def has_module_perms(self, app_label):
        return self.is_staff
    
    def check_password(self, password):
        """Verify password against stored bcrypt hash"""
        stored_password = self.user_data.get('password', '')
        return self._verify_password(password, stored_password)
    
    def _verify_password(self, password, stored_password):
        """Verify password against stored bcrypt hash"""
        try:
            # Convert stored password to bytes if it's a string
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
            
            # Convert input password to bytes
            password_bytes = password.encode('utf-8')
            
            # Use bcrypt to verify password
            return bcrypt.checkpw(password_bytes, stored_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def _hash_password(self, password):
        """Hash password using bcrypt"""
        try:
            # Convert password to bytes
            password_bytes = password.encode('utf-8')
            
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Return as string for storage
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            return None

class AppAuthenticationBackend(BaseBackend):
    """Custom authentication backend for PostgreSQL users"""
    
    def authenticate(self, request, username=None, password=None):
        if username is None or password is None:
            return None
        
        try:
            user_service = get_user_service()
            user_data = user_service.authenticate_user(username, password)
            
            if user_data:
                return AppUser(user_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def get_user(self, user_id):
        try:
            user_service = get_user_service()
            user_data = user_service.get_user_by_id(user_id)
            if not user_data and user_id.startswith('user_'):
                # Backward compatibility for legacy prefixes.
                user_data = user_service.get_user_by_id(user_id[5:])
            
            if user_data:
                return AppUser(user_data)
            return None
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None

class AppJWTAuthentication(BaseAuthentication):
    """Custom JWT authentication for PostgreSQL users"""
    
    def authenticate(self, request):
        # Get the token from the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            user_id = payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Invalid token')
            
            user_service = get_user_service()
            user_data = user_service.get_user_by_id(user_id)
            if not user_data:
                raise AuthenticationFailed('User not found')
            
            # Create user object
            user = AppUser(user_data)
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        return 'Bearer realm="api"'

class AppTokenAuthentication(BaseAuthentication):
    """Custom token authentication for PostgreSQL users"""
    
    def authenticate(self, request):
        # Get the token from the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode token (simple base64 for now)
            token_data = base64.b64decode(token).decode('utf-8')
            token_payload = json.loads(token_data)
            
            user_id = token_payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Invalid token')
            
            user_service = get_user_service()
            user_data = user_service.get_user_by_id(user_id)
            if not user_data:
                raise AuthenticationFailed('User not found')
            
            # Create user object
            user = AppUser(user_data)
            
            return (user, token)
            
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        return 'Token realm="api"'

