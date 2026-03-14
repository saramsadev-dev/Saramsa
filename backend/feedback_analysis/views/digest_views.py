"""
API views for weekly digest preferences and on-demand sending.
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apis.core.response import StandardResponse
from authentication.models import UserAccount

logger = logging.getLogger(__name__)


class DigestPreferenceView(APIView):
    """
    GET  — return the current user's weekly digest preference.
    PATCH — update it (body: { "enabled": true/false }).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = UserAccount.objects.get(pk=request.user.id)
        prefs = user.extra or {}
        return StandardResponse.success(
            data={"weekly_digest_enabled": prefs.get("weekly_digest_enabled", True)},
        )

    def patch(self, request):
        enabled = request.data.get("enabled")
        if enabled is None:
            return StandardResponse.validation_error(
                detail="'enabled' field is required.",
            )

        user = UserAccount.objects.get(pk=request.user.id)
        extra = user.extra or {}
        extra["weekly_digest_enabled"] = bool(enabled)
        user.extra = extra
        user.save(update_fields=["extra", "updated_at"])

        return StandardResponse.success(
            data={"weekly_digest_enabled": bool(enabled)},
        )


class DigestPreviewView(APIView):
    """
    GET — return the digest payload for the current user (preview, no email sent).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from feedback_analysis.services.digest_service import gather_user_digest, _week_bounds

        user = UserAccount.objects.get(pk=request.user.id)
        since, until = _week_bounds()
        digest = gather_user_digest(user, since, until)
        return StandardResponse.success(data=digest)


class DigestSendNowView(APIView):
    """
    POST — immediately send the weekly digest to the current user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from feedback_analysis.services.digest_service import (
            gather_user_digest,
            send_digest_email,
            _week_bounds,
        )

        user = UserAccount.objects.get(pk=request.user.id)
        since, until = _week_bounds()
        digest = gather_user_digest(user, since, until)

        if not any(digest["totals"].values()):
            return StandardResponse.success(
                data={"sent": False, "reason": "No activity in the last 7 days."},
            )

        ok = send_digest_email(user, digest)
        return StandardResponse.success(
            data={"sent": ok},
        )
