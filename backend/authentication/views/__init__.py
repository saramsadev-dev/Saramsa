"""
Views package for authentication.

Contains views for authentication operations:
- User registration and login
- JWT token management  
- Profile management
- Password reset functionality
- User listing and details
"""

from .authentication_views import (
    RegisterView,
    RegisterOtpRequestView,
    AppTokenObtainPairView,
    AppTokenRefreshView,
    ProfileMeView,
    CheckUsernameView,
    UserListView,
    UserDetailView,
    LoginView,
    ForgotPasswordView,
    ResetPasswordView,
)

__all__ = [
    'RegisterView',
    'RegisterOtpRequestView',
    'AppTokenObtainPairView',
    'AppTokenRefreshView',
    'ProfileMeView',
    'CheckUsernameView',
    'UserListView',
    'UserDetailView',
    'LoginView',
    'ForgotPasswordView',
    'ResetPasswordView',
]

