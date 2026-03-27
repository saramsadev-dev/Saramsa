"""
Scoped throttle classes for expensive operations.

Apply these to individual views via `throttle_classes = [AnalysisRateThrottle]`
instead of the global default.
"""

from rest_framework.throttling import UserRateThrottle


class AnalysisRateThrottle(UserRateThrottle):
    """Tight limit on feedback analysis (LLM-heavy)."""
    scope = "analysis"


class UploadRateThrottle(UserRateThrottle):
    """Limit on file uploads."""
    scope = "upload"


class WorkItemGenerationThrottle(UserRateThrottle):
    """Limit on AI work-item generation."""
    scope = "work_items"
