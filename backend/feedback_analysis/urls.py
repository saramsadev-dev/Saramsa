from django.urls import path
from .views import (
    # Analysis views
    AnalyzeCommentsView,
    UpdateKeywordsView,
    GetUserCommentsView,
    TaskStatusView,
    AnalysisByIdView,
    # Insights views
    InsightsListView,
    InsightDetailView,
    InsightsByTypeView,
    AnalysisHistoryView,
    AnalysisByQuarterView,
    CumulativeAnalysisView,
    AnalysisComparisonView,
    UserStoriesView,
    # File upload views
    FeedbackFileUploadView,
)

urlpatterns = [
    # Core analysis endpoints
    path('analyze/', AnalyzeCommentsView.as_view(), name='analyze_comments'),
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='task_status'),
    path('analysis/<str:analysis_id>/', AnalysisByIdView.as_view(), name='analysis_by_id'),
    path('keywords/update/', UpdateKeywordsView.as_view(), name='update_keywords'),
    path('comments/', GetUserCommentsView.as_view(), name='get_user_comments'),
    
    # Insights endpoints (analysis results)
    path('insights/', InsightsListView.as_view(), name='insights_list'),
    path('insights/<str:insight_id>/', InsightDetailView.as_view(), name='insight_detail'),
    path('insights/type/<str:analysis_type>/', InsightsByTypeView.as_view(), name='insights_by_type'),
    path('insights/user-stories/', UserStoriesView.as_view(), name='user_stories'),
    path('insights/user-stories/all/', UserStoriesView.as_view(), name='user_stories_all'),
    
    # Analysis history endpoints
    path('history/', AnalysisHistoryView.as_view(), name='analysis_history'),
    path('history/quarter/', AnalysisByQuarterView.as_view(), name='analysis_by_quarter'),
    path('history/cumulative/', CumulativeAnalysisView.as_view(), name='cumulative_analysis'),
    path('history/compare/', AnalysisComparisonView.as_view(), name='analysis_comparison'),
    
    # File upload endpoints
    path('upload/', FeedbackFileUploadView.as_view(), name='feedback-file-upload'),
]

# NOTE: User story endpoints have been moved to /work_items/ app
# NOTE: Integration endpoints have been moved to /integrations/ app
# This eliminates duplication and follows proper Django app separation
