from rest_framework import permissions


def _get_role_from_user(user):
    if not user:
        return None
    profile = getattr(user, 'profile', None)
    if isinstance(profile, dict):
        return profile.get('role')
    return getattr(profile, 'role', None)


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return False
        return _get_role_from_user(user) == 'admin'


class IsUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return False
        return _get_role_from_user(user) == 'user'


class IsAdminOrUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return False
        return _get_role_from_user(user) in ['admin', 'user']


class NoAuthentication(permissions.BasePermission):
    def has_permission(self, request, view):
        return True
