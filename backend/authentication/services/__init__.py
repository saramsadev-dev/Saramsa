"""
Authentication Services

This package contains all business logic services for the authentication app.
Following Django best practices with organized service modules.
"""

from .authentication_service import AuthenticationService, get_authentication_service, get_user_service

__all__ = [
    'AuthenticationService',
    'get_authentication_service',
    'get_user_service',  # Legacy alias
]