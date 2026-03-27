"""
Usage quota enforcement.

Call `check_quota` before expensive operations. Call `record_usage` after
the operation succeeds.  Quota limits come from env vars by default but
can be overridden per-user via BillingProfile.metadata["quota_overrides"].
"""

import logging
from datetime import datetime, timezone

from django.db import models as _  # noqa — ensure app registry is ready

logger = logging.getLogger(__name__)


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _get_or_create_record(user_id: str):
    from .models import UsageRecord
    period = _current_period()
    record, _ = UsageRecord.objects.get_or_create(
        user_id=str(user_id),
        period=period,
    )
    return record


def _get_limits(user_id: str) -> dict:
    from .models import BillingProfile, UsageRecord
    defaults = UsageRecord.default_limits()
    try:
        profile = BillingProfile.objects.filter(user_id=str(user_id)).first()
        if profile and isinstance(profile.metadata, dict):
            overrides = profile.metadata.get("quota_overrides") or {}
            for key in defaults:
                if key in overrides:
                    defaults[key] = int(overrides[key])
    except Exception:
        pass
    return defaults


class QuotaExceeded(Exception):
    """Raised when a user has hit their monthly usage limit."""

    def __init__(self, resource: str, limit: int, used: int):
        self.resource = resource
        self.limit = limit
        self.used = used
        super().__init__(
            f"Monthly {resource} quota exceeded: {used}/{limit}. "
            "Upgrade your plan or wait until next month."
        )


def check_quota(user_id: str, resource: str) -> None:
    """
    Raise QuotaExceeded if the user has hit their limit for `resource`.

    resource: "analysis" | "work_item_gen" | "llm_tokens"
    """
    record = _get_or_create_record(user_id)
    limits = _get_limits(user_id)

    field_map = {
        "analysis": ("analysis_count", "analysis_limit"),
        "work_item_gen": ("work_item_gen_count", "work_item_gen_limit"),
        "llm_tokens": ("llm_tokens_used", "llm_token_limit"),
    }

    if resource not in field_map:
        return

    count_field, limit_key = field_map[resource]
    used = getattr(record, count_field, 0)
    limit = limits.get(limit_key, 999_999)

    if used >= limit:
        raise QuotaExceeded(resource, limit, used)


def record_usage(user_id: str, resource: str, amount: int = 1) -> None:
    """Increment usage counter after a successful operation."""
    from .models import UsageRecord

    period = _current_period()
    field_map = {
        "analysis": "analysis_count",
        "work_item_gen": "work_item_gen_count",
        "llm_tokens": "llm_tokens_used",
    }
    field = field_map.get(resource)
    if not field:
        return

    from django.db.models import F
    UsageRecord.objects.filter(
        user_id=str(user_id), period=period,
    ).update(**{field: F(field) + amount})
