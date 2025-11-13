from django.urls import path
from .azureViews import (
    CreateAzureWorkItemView, 
    ListAzureWorkItemTypes, 
    AzureDevOpsConfigView,
    AzureDevOpsProjectsView,
    AzureDevOpsProjectCreationView,
    AzureDevOpsWorkItemTypesView,
    AzureDevOpsProjectMetadataView,
    AzureDevOpsProjectsListView,
    AzureDevOpsProjectDetailView,
    AzureDevOpsWorkItemsListView,
    AzureDevOpsWorkItemDetailView,
    WorkItemsListView,
    WorkItemDetailView,
    WorkItemsByPlatformView
)
from .jiraViews import (
    CreateJiraIssuesView, 
    JiraProjectsView, 
    JiraIssueTypesView, 
    JiraProjectMetadataView, 
    JiraProjectCreationView,
    JiraConfigView,
    JiraWorkItemsListView,
    JiraWorkItemDetailView,
    JiraProjectsListView,
    JiraProjectDetailView
)

urlpatterns = [
    # Azure DevOps endpoints
    path('azure/config', AzureDevOpsConfigView.as_view(), name='azure_config'),
    path('azure/project/create', AzureDevOpsProjectCreationView.as_view(), name='azure_project_create'),
    path('azure/projects', AzureDevOpsProjectsView.as_view(), name='azure_projects'),
    path('azure/work-item-types', AzureDevOpsWorkItemTypesView.as_view(), name='azure_work_item_types'),
    path('azure/project-metadata', AzureDevOpsProjectMetadataView.as_view(), name='azure_project_metadata'),
    path('azure/create', CreateAzureWorkItemView.as_view(), name='create_wi_azure'),
    path('azure/list', ListAzureWorkItemTypes.as_view(), name='list_wi_azure'),
    
    # Azure DevOps Work Items and Projects Management
    path('azure/work-items/', AzureDevOpsWorkItemsListView.as_view(), name='azure_work_items_list'),
    path('azure/work-items/<str:work_item_id>/', AzureDevOpsWorkItemDetailView.as_view(), name='azure_work_item_detail'),
    path('azure/projects-list/', AzureDevOpsProjectsListView.as_view(), name='azure_projects_list'),
    path('azure/projects/<str:project_id>/', AzureDevOpsProjectDetailView.as_view(), name='azure_project_detail'),

    # Jira endpoints
    path('jira/config', JiraConfigView.as_view(), name='jira_config'),
    path('jira/project/create', JiraProjectCreationView.as_view(), name='jira_project_create'),
    path('jira/projects', JiraProjectsView.as_view(), name='jira_projects'),
    path('jira/issue-types', JiraIssueTypesView.as_view(), name='jira_issue_types'),
    path('jira/project-metadata', JiraProjectMetadataView.as_view(), name='jira_project_metadata'),
    path('jira/create', CreateJiraIssuesView.as_view(), name='create_wi_jira'),
    
    # Jira Work Items and Projects Management
    path('jira/work-items/', JiraWorkItemsListView.as_view(), name='jira_work_items_list'),
    path('jira/work-items/<str:work_item_id>/', JiraWorkItemDetailView.as_view(), name='jira_work_item_detail'),
    path('jira/projects-list/', JiraProjectsListView.as_view(), name='jira_projects_list'),
    path('jira/projects/<str:project_id>/', JiraProjectDetailView.as_view(), name='jira_project_detail'),
    
    # Work Items History and Management (All Platforms)
    path('work-items/', WorkItemsListView.as_view(), name='work_items_list'),
    path('work-items/<str:work_item_id>/', WorkItemDetailView.as_view(), name='work_item_detail'),
    path('work-items/platform/<str:platform>/', WorkItemsByPlatformView.as_view(), name='work_items_by_platform'),
]
