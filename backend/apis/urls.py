from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from .views import health_check, performance_metrics, reset_performance_stats
from feedback_analysis.views import UserStoriesView, AnalyzeCommentsView, TaskStatusView, TaskListView, GetUserCommentsView, FeedbackFileUploadView
from feedback_analysis.views import InsightReviewListView, InsightReviewUpdateView, InsightRulesView, InsightRulesApplyView
from feedback_analysis.views import IngestionScheduleView, IngestionRunNowView
from work_items.views import WorkItemGenerationView, WorkItemSubmissionView, WorkItemUpdateView, WorkItemRemovalView

urlpatterns = [
    # Health and monitoring endpoints
    path('api/health/', health_check, name='health-check'),
    path('api/performance/', performance_metrics, name='performance-metrics'),
    path('api/performance/reset/', reset_performance_stats, name='reset-performance-stats'),
    
    # App-specific API endpoints
    path('api/feedback/', include('feedback_analysis.urls')),
    path('api/work-items/', include('work_items.urls')),
    path('api/auth/', include('authentication.urls')),
    path('api/integrations/', include('integrations.urls')),
    # Insights endpoints (aliased from feedback_analysis and work_items for frontend compatibility)
    path('api/insights/analyze/', AnalyzeCommentsView.as_view(), name='insights_analyze'),
    path('api/insights/task-status/<str:task_id>/', TaskStatusView.as_view(), name='insights_task_status'),
    path('api/insights/tasks/', TaskListView.as_view(), name='insights_tasks'),
    path('api/insights/comments/', GetUserCommentsView.as_view(), name='insights_comments'),
    path('api/insights/upload/', FeedbackFileUploadView.as_view(), name='insights_upload'),
    path('api/insights/user-story-creation/', WorkItemGenerationView.as_view(), name='insights_user_story_creation'),
    path('api/insights/user-story-submission/', WorkItemSubmissionView.as_view(), name='insights_user_story_submission'),
    path('api/insights/user-stories/', UserStoriesView.as_view(), name='insights_user_stories'),
    path('api/insights/user-stories/remove-work-items/', WorkItemRemovalView.as_view(), name='insights_remove_work_items'),
    path('api/insights/work-items/<str:work_item_id>/update/', WorkItemUpdateView.as_view(), name='insights_work_item_update'),
    path('api/insights/review/', InsightReviewListView.as_view(), name='insights_review'),
    path('api/insights/review/update/', InsightReviewUpdateView.as_view(), name='insights_review_update'),
    path('api/insights/rules/', InsightRulesView.as_view(), name='insights_rules'),
    path('api/insights/rules/apply/', InsightRulesApplyView.as_view(), name='insights_rules_apply'),
    path('api/insights/ingestion/schedule/', IngestionScheduleView.as_view(), name='insights_ingestion_schedule'),
    path('api/insights/ingestion/run-now/', IngestionRunNowView.as_view(), name='insights_ingestion_run_now'),
    
    # Swagger/OpenAPI URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
