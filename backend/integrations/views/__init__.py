"""
Views package for integrations.

Organized into logical modules:
- integration_views: Integration account management
- project_views: Project CRUD operations
- external_views: External API interactions
"""

from .integration_views import (
    get_integration_accounts,
    create_azure_integration,
    create_jira_integration,
    test_integration_connection,
    delete_integration_account,
)
from .project_views import (
    ProjectCreateView,
    ProjectListView,
    ProjectDetailView,
    LatestAnalysisView,
)
from .external_views import (
    get_azure_projects,
    get_jira_projects,
    get_dashboard_azure_projects,
    get_dashboard_jira_projects,
    get_external_projects,
    check_external_project,
)

__all__ = [
    # Integration views
    'get_integration_accounts',
    'create_azure_integration',
    'create_jira_integration',
    'test_integration_connection',
    'delete_integration_account',
    # Project views
    'ProjectCreateView',
    'ProjectListView',
    'ProjectDetailView',
    'LatestAnalysisView',
    # External views
    'get_azure_projects',
    'get_jira_projects',
    'get_dashboard_azure_projects',
    'get_dashboard_jira_projects',
    'get_external_projects',
    'check_external_project',
]