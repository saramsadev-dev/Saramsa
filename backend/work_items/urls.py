from django.urls import path
from .views import (
    WorkItemGenerationView,
    WorkItemSubmissionView,
    WorkItemsListView,
    WorkItemDetailView,
    WorkItemUpdateView,
    WorkItemsByPlatformView,
    WorkItemRemovalView,
    WorkItemQualityRulesView,
    WorkItemQualityCheckView
)

urlpatterns = [
    # CORE WORK ITEMS ENDPOINTS (Primary functionality)
    path('generate/', WorkItemGenerationView.as_view(), name='work_items_generate'),
    path('submit/', WorkItemSubmissionView.as_view(), name='work_items_submit'),
    path('', WorkItemsListView.as_view(), name='work_items_list'),
    path('<str:work_item_id>/', WorkItemDetailView.as_view(), name='work_item_detail'),
    path('<str:work_item_id>/update/', WorkItemUpdateView.as_view(), name='work_item_update'),
    path('platform/<str:platform>/', WorkItemsByPlatformView.as_view(), name='work_items_by_platform'),
    path('remove/', WorkItemRemovalView.as_view(), name='work_items_remove'),
    path('quality-rules/', WorkItemQualityRulesView.as_view(), name='work_item_quality_rules'),
    path('quality-check/', WorkItemQualityCheckView.as_view(), name='work_item_quality_check'),
]

# NOTE: Platform-specific configuration endpoints (Azure DevOps, Jira) have been moved to the integrations app
# to eliminate duplication. Use the integrations app endpoints for:
# - /integrations/azure/projects/
# - /integrations/jira/projects/
# - /integrations/projects/create/
# - etc.
