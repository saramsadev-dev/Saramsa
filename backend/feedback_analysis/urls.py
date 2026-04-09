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
    DigestPreferenceView,
    DigestPreviewView,
    DigestSendNowView,
)

urlpatterns = [
    # Analysis by ID
    path('analysis/<str:analysis_id>/', AnalysisByIdView.as_view(), name='analysis_by_id'),
    path('analysis/<str:analysis_id>/rename/', AnalysisRenameView.as_view(), name='analysis_rename'),
    path('keywords/update/', UpdateKeywordsView.as_view(), name='update_keywords'),

    # Insights list/detail
    path('insights/', InsightsListView.as_view(), name='insights_list'),
    path('insights/<str:insight_id>/', InsightDetailView.as_view(), name='insight_detail'),
    path('insights/type/<str:analysis_type>/', InsightsByTypeView.as_view(), name='insights_by_type'),

    # Analysis history & quarterly analytics
    path('history/', AnalysisHistoryView.as_view(), name='analysis_history'),
    path('history/quarter/', AnalysisByQuarterView.as_view(), name='analysis_by_quarter'),
    path('history/cumulative/', CumulativeAnalysisView.as_view(), name='cumulative_analysis'),
    path('history/compare/', AnalysisComparisonView.as_view(), name='analysis_comparison'),

    # Weekly digest
    path('digest/preferences/', DigestPreferenceView.as_view(), name='digest_preferences'),
    path('digest/preview/', DigestPreviewView.as_view(), name='digest_preview'),
    path('digest/send-now/', DigestSendNowView.as_view(), name='digest_send_now'),
]
