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
    # External provider project fetching (for configuration) - most specific first
    path('azure/projects/', get_azure_projects, name='get_azure_projects'),
    path('jira/projects/', get_jira_projects, name='get_jira_projects'),
    
    # Dashboard endpoints (fetch imported projects from database)
    path('dashboard/azure/projects/', get_dashboard_azure_projects, name='get_dashboard_azure_projects'),
    path('dashboard/jira/projects/', get_dashboard_jira_projects, name='get_dashboard_jira_projects'),
    
    # External project utilities
    path('external/projects/check/', check_external_project, name='check_external_project'),
    path('external/projects/', get_external_projects, name='get_external_projects'),
    
    # Project CRUD operations - MOST SPECIFIC FIRST
    path('projects/create/', ProjectCreateView.as_view(), name='project_create_with_path'),
    path('projects/list/', ProjectListView.as_view(), name='project_list'),
    path('projects/<str:project_id>/analysis/latest/', LatestAnalysisView.as_view(), name='project_latest_analysis'),
    path('projects/<str:project_id>/', ProjectDetailView.as_view(), name='project_detail'),
    path('projects/', ProjectListView.as_view(), name='project_list_root'),  # Changed to list for GET requests
    
    # Integration account management - SPECIFIC ROUTES MUST COME BEFORE PARAMETERIZED ROUTES
    path('azure/', create_azure_integration, name='create_azure_integration'),
    path('jira/', create_jira_integration, name='create_jira_integration'),
    
    # Project CRUD operations (direct paths for /api/projects/...)
    # Specific routes must come before parameterized routes
    path('list/', ProjectListView.as_view(), name='project_list_short'),
    path('<str:project_id>/analysis/latest/', LatestAnalysisView.as_view(), name='project_latest_analysis_direct'),
    
    # PARAMETERIZED ROUTES MUST COME LAST
    path('<str:account_id>/test/', test_integration_connection, name='test_integration_connection'),
    path('<str:account_id>/', delete_integration_account, name='delete_integration_account'),
    path('<str:project_id>/', ProjectDetailView.as_view(), name='project_detail_direct'),
    
    # Root path
    path('', get_integration_accounts, name='get_integration_accounts'),
]
