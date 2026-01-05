"""
URL routing for integrations API endpoints.
"""

from django.urls import path
from .views import (
    # Integration views
    get_integration_accounts,
    create_azure_integration,
    create_jira_integration,
    test_integration_connection,
    delete_integration_account,
    # Project views
    ProjectCreateView,
    ProjectListView,
    ProjectDetailView,
    LatestAnalysisView,
    # External views
    get_azure_projects,
    get_jira_projects,
    get_dashboard_azure_projects,
    get_dashboard_jira_projects,
    get_external_projects,
    check_external_project,
)

urlpatterns = [
    # Project CRUD operations
    path('projects/', ProjectCreateView.as_view(), name='project_create'),
    path('projects/list/', ProjectListView.as_view(), name='project_list'),
    path('projects/<str:project_id>/', ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<str:project_id>/analysis/latest/', LatestAnalysisView.as_view(), name='project_latest_analysis'),
    
    # External provider project fetching (for configuration)
    path('azure/projects/', get_azure_projects, name='get_azure_projects'),
    path('jira/projects/', get_jira_projects, name='get_jira_projects'),
    
    # Dashboard endpoints (fetch imported projects from database)
    path('dashboard/azure/projects/', get_dashboard_azure_projects, name='get_dashboard_azure_projects'),
    path('dashboard/jira/projects/', get_dashboard_jira_projects, name='get_dashboard_jira_projects'),
    
    # External project utilities
    path('external/projects/', get_external_projects, name='get_external_projects'),
    path('external/projects/check/', check_external_project, name='check_external_project'),
    
    # Integration account management
    path('azure/', create_azure_integration, name='create_azure_integration'),
    path('jira/', create_jira_integration, name='create_jira_integration'),
    path('<str:account_id>/test/', test_integration_connection, name='test_integration_connection'),
    path('<str:account_id>/', delete_integration_account, name='delete_integration_account'),
    path('', get_integration_accounts, name='get_integration_accounts'),
]
