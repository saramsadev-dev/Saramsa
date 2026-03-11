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
from .views.review_views import (
    ReviewQueueListView,
    ReviewQueueStatsView,
    CandidateApproveView,
    CandidateDismissView,
    CandidateSnoozeView,
    CandidateMergeView,
    CandidateBatchApproveView,
    CandidateUpdateView,
    CandidateRetryPushView,
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

    # REVIEW QUEUE ENDPOINTS
    path('review/', ReviewQueueListView.as_view(), name='review_queue_list'),
    path('review/stats/', ReviewQueueStatsView.as_view(), name='review_queue_stats'),
    path('review/approve/', CandidateApproveView.as_view(), name='review_approve'),
    path('review/dismiss/', CandidateDismissView.as_view(), name='review_dismiss'),
    path('review/snooze/', CandidateSnoozeView.as_view(), name='review_snooze'),
    path('review/merge/', CandidateMergeView.as_view(), name='review_merge'),
    path('review/batch-approve/', CandidateBatchApproveView.as_view(), name='review_batch_approve'),
    path('review/update/', CandidateUpdateView.as_view(), name='review_update'),
    path('review/retry-push/', CandidateRetryPushView.as_view(), name='review_retry_push'),
]

# NOTE: Platform-specific configuration endpoints (Azure DevOps, Jira) have been moved to the integrations app
# to eliminate duplication. Use the integrations app endpoints for:
# - /integrations/azure/projects/
# - /integrations/jira/projects/
# - /integrations/projects/create/
# - etc.
