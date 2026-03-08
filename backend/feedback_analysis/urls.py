from django.urls import path
from .views import (
    AnalysisByIdView,
    AnalysisRenameView,
    UpdateKeywordsView,
    InsightsListView,
    InsightDetailView,
    InsightsByTypeView,
    AnalysisHistoryView,
    AnalysisByQuarterView,
    CumulativeAnalysisView,
    AnalysisComparisonView,
)

urlpatterns = [
    # Analysis by ID (unique to /api/feedback/)
    path('analysis/<str:analysis_id>/', AnalysisByIdView.as_view(), name='analysis_by_id'),
    path('analysis/<str:analysis_id>/rename/', AnalysisRenameView.as_view(), name='analysis_rename'),
    path('keywords/update/', UpdateKeywordsView.as_view(), name='update_keywords'),

    # Insights list/detail (unique to /api/feedback/)
    path('insights/', InsightsListView.as_view(), name='insights_list'),
    path('insights/<str:insight_id>/', InsightDetailView.as_view(), name='insight_detail'),
    path('insights/type/<str:analysis_type>/', InsightsByTypeView.as_view(), name='insights_by_type'),

    # Analysis history (unique to /api/feedback/)
    path('history/', AnalysisHistoryView.as_view(), name='analysis_history'),
    path('history/quarter/', AnalysisByQuarterView.as_view(), name='analysis_by_quarter'),
    path('history/cumulative/', CumulativeAnalysisView.as_view(), name='cumulative_analysis'),
    path('history/compare/', AnalysisComparisonView.as_view(), name='analysis_comparison'),
]

# Endpoints moved to /api/insights/ aliases in apis/urls.py:
#   analyze, task-status, tasks, comments, upload,
#   user-stories, review, rules, ingestion
# Work item endpoints: /api/work-items/
# Integration endpoints: /api/integrations/
