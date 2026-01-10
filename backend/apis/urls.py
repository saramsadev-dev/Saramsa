from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from .views import health_check, performance_metrics, reset_performance_stats
from feedback_analysis.views import UserStoriesView, AnalyzeCommentsView, TaskStatusView, GetUserCommentsView, FeedbackFileUploadView
from work_items.views import WorkItemGenerationView

urlpatterns = [
    # Health and monitoring endpoints
    path('api/health/', health_check, name='health-check'),
    path('api/performance/', performance_metrics, name='performance-metrics'),
    path('api/performance/reset/', reset_performance_stats, name='reset-performance-stats'),
    
    # App-specific API endpoints
    path('api/feedback/', include('feedback_analysis.urls')),
    path('api/work-items/', include('work_items.urls')),
    path('api/auth/', include('authentication.urls')), 
    path('api/projects/', include('integrations.urls')),  # Projects now handled by integrations
    path('api/integrations/', include('integrations.urls')),
    # Insights endpoints (aliased from feedback_analysis for frontend compatibility)
    path('api/insights/analyze/', AnalyzeCommentsView.as_view(), name='insights_analyze'),
    path('api/insights/task-status/<str:task_id>/', TaskStatusView.as_view(), name='insights_task_status'),
    path('api/insights/comments/', GetUserCommentsView.as_view(), name='insights_comments'),
    path('api/insights/user-story-creation/', WorkItemGenerationView.as_view(), name='insights_user_story_creation'),
    path('api/insights/user-stories/', UserStoriesView.as_view(), name='insights_user_stories'),
    path('api/insights/user-stories/all/', UserStoriesView.as_view(), name='insights_user_stories_all'),
    
    # Additional aliases without /api prefix for frontend compatibility
    path('insights/comments/', GetUserCommentsView.as_view(), name='insights_comments_no_api'),
    path('insights/upload/', FeedbackFileUploadView.as_view(), name='insights_upload_no_api'),
    
    # Swagger/OpenAPI URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
