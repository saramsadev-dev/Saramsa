"""
Views package for feedback analysis.

Organized into logical modules:
- analysis_views: Core analysis operations
- insights_views: Insights and reporting views
"""

from .analysis_views import (
    AnalyzeCommentsView,
    UpdateKeywordsView,
    GetUserCommentsView,
    TaskStatusView,
    TaskListView,
    AnalysisByIdView,
    AnalysisRenameView,
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
    UserStoryUpdateView,
    UserStoryDeleteView,
    UserStoryBulkDeleteView,
    InsightReviewListView,
    InsightReviewUpdateView,
    InsightRulesView,
    InsightRulesApplyView,
)
from .ingestion_schedule_views import (
    IngestionScheduleView,
    IngestionRunNowView,
)
from .digest_views import (
    DigestPreferenceView,
    DigestPreviewView,
    DigestSendNowView,
)

__all__ = [
    # Analysis views
    'AnalyzeCommentsView',
    'UpdateKeywordsView',
    'GetUserCommentsView',
    'TaskStatusView',
    'TaskListView',
    'AnalysisByIdView',
    'AnalysisRenameView',
    # Insights views
    'InsightsListView',
    'InsightDetailView',
    'InsightsByTypeView',
    'AnalysisHistoryView',
    'AnalysisByQuarterView',
    'CumulativeAnalysisView',
    'AnalysisComparisonView',
    'UserStoriesView',
    'UserStoryUpdateView',
    'UserStoryDeleteView',
    'UserStoryBulkDeleteView',
    # Digest views
    'DigestPreferenceView',
    'DigestPreviewView',
    'DigestSendNowView',
]

