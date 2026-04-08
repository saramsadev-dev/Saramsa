from django.contrib.auth.backends import BaseBackend
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from .models import UserAccount
import logging

logger = logging.getLogger(__name__)


class AppUser:
    """Compatibility wrapper around UserAccount for request.user."""

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


class AppAuthenticationBackend(BaseBackend):
    """Authentication backend that queries UserAccount via ORM."""

    def authenticate(self, request, username=None, password=None):
        if not username or not password:
            return None
        try:
            user = UserAccount.objects.filter(email=username, is_active=True).first()
            if user and user.check_password(password):
                return AppUser(_user_to_dict(user))
        except Exception as e:
            logger.error(f"Authentication error: {e}")
        return None

    def get_user(self, user_id):
        try:
            user = UserAccount.objects.filter(id=user_id).first()
            if user:
                return AppUser(_user_to_dict(user))
        except Exception as e:
            logger.error(f"Get user error: {e}")
        return None


class AppJWTAuthentication(JWTAuthentication):
    """Thin simplejwt subclass that resolves user_id against UserAccount ORM."""

    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise AuthenticationFailed('Token contained no recognizable user identification')

        user = UserAccount.objects.filter(id=user_id, is_active=True).first()
        if not user:
            raise AuthenticationFailed('User not found or inactive')

        return AppUser(_user_to_dict(user))


def _user_to_dict(user: UserAccount) -> dict:
    return {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined,
        'profile': user.profile or {},
        'company_name': user.company_name,
        'company_url': user.company_url,
        'avatar_url': user.avatar_url,
    }
