from rest_framework import permissions
from apis.infrastructure.cosmos_service import cosmos_service


def _get_role_from_user(user):
    if not user:
        return None
    profile = getattr(user, 'profile', None)
    if isinstance(profile, dict):
        return profile.get('role')
    return getattr(profile, 'role', None)


def _get_user_id(user):
    if not user:
        return None
    return getattr(user, 'id', None) or getattr(user, 'user_id', None)


def _get_project_id_from_request(request, view):
    # Check URL kwargs first
    kwargs = getattr(view, 'kwargs', {}) or {}
    for key in ('project_id', 'projectId'):
        if key in kwargs and kwargs[key]:
            return kwargs[key]

    # Check query params
    query_params = getattr(request, 'query_params', {}) or {}
    for key in ('project_id', 'projectId'):
        value = query_params.get(key)
        if value:
            return value

    # Check request body
    data = getattr(request, 'data', {}) or {}
    for key in ('project_id', 'projectId'):
        value = data.get(key)
        if value:
            return value

    return None


_ROLE_ORDER = {
    'viewer': 1,
    'editor': 2,
    'admin': 3
}


class ProjectRolePermission(permissions.BasePermission):
    """Base permission enforcing project-level roles."""
    min_role = 'viewer'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return False

        # Global admins always pass
        if _get_role_from_user(user) == 'admin':
            return True

        project_id = _get_project_id_from_request(request, view)
        if not project_id:
            return False

        user_id = _get_user_id(user)
        if not user_id:
            return False

        project = cosmos_service.get_project_by_id_any(project_id)
        owner_id = None
        if isinstance(project, dict):
            owner_id = project.get('owner_user_id') or project.get('userId')
        if owner_id and str(owner_id) == str(user_id):
            return True

        role = cosmos_service.get_project_role_for_user(project_id, str(user_id))
        if not role:
            return False

        return _ROLE_ORDER.get(role, 0) >= _ROLE_ORDER.get(self.min_role, 0)


class IsProjectViewer(ProjectRolePermission):
    min_role = 'viewer'


class IsProjectEditor(ProjectRolePermission):
    min_role = 'editor'


class IsProjectAdmin(ProjectRolePermission):
    min_role = 'admin'


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
