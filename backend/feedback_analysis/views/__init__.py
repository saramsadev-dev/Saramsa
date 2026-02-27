"""
Views package for feedback analysis.

Organized into logical modules:
- analysis_views: Core analysis operations
- insights_views: Insights and reporting views  
- file_upload_views: File upload and processing views
- helpers: Shared helper functions
"""

from .analysis_views import (
    AnalyzeCommentsView,
    UpdateKeywordsView,
    GetUserCommentsView,
    TaskStatusView,
    AnalysisByIdView,
)
from .insights_views import (
    InsightsListView,
    InsightDetailView,
    InsightsByTypeView,
    AnalysisHistoryView,
    AnalysisByQuarterView,
    CumulativeAnalysisView,
    AnalysisComparisonView,
    UserStoriesView,
)
from .file_upload_views import (
    FeedbackFileUploadView,
)

__all__ = [
    # Analysis views
    'AnalyzeCommentsView',
    'UpdateKeywordsView',
    'GetUserCommentsView',
    'TaskStatusView',
    'AnalysisByIdView',
    # Insights views
    'InsightsListView',
    'InsightDetailView',
    'InsightsByTypeView',
    'AnalysisHistoryView',
    'AnalysisByQuarterView',
    'CumulativeAnalysisView',
    'AnalysisComparisonView',
    'UserStoriesView',
    # File upload views
    'FeedbackFileUploadView',
]

