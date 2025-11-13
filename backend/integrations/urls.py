"""
URL routing for integrations API endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Provider-specific project endpoints (must come before generic provider endpoints)
    path('azure/projects/', views.get_azure_projects, name='get_azure_projects'),
    path('jira/projects/', views.get_jira_projects, name='get_jira_projects'),
    
    # Project management (must come before generic account patterns)
    path('projects/', views.get_projects, name='get_projects'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/check-external/', views.check_external_project, name='check_external_project'),
    path('projects/<str:project_id>/', views.update_project, name='update_project'),
    path('projects/<str:project_id>/sync/', views.sync_project, name='sync_project'),
    
    # Dashboard endpoints (fetch from database)
    path('dashboard/azure/projects/', views.get_dashboard_azure_projects, name='get_dashboard_azure_projects'),
    path('dashboard/jira/projects/', views.get_dashboard_jira_projects, name='get_dashboard_jira_projects'),
    
    # Create new integration accounts (must be before generic account patterns)
    path('azure/', views.create_azure_integration, name='create_azure_integration'),
    path('jira/', views.create_jira_integration, name='create_jira_integration'),

    # Integration account management (generic patterns last)
    path('<str:account_id>/test/', views.test_integration_connection, name='test_integration_connection'),
    path('<str:account_id>/', views.delete_integration_account, name='delete_integration_account'),
    
    # Get the integration accounts
    path('', views.get_integration_accounts, name='get_integration_accounts'),

    # Generic external project fetching
    path('external/projects/', views.get_external_projects, name='get_external_projects'), 
]
