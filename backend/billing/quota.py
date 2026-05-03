"""Usage quota enforcement.

Call `check_quota` before expensive operations. Call `record_usage` after
the operation succeeds. Quotas are scoped to the user's active
organization so all members of a workspace share one credit pool. Limits
come from env vars by default and can be overridden per-org via
BillingProfile.metadata["quota_overrides"].

The public API still takes a user_id (so the views never had to change),
but internally we resolve the user's active_organization_id and key all
counters and limits by that. If a user somehow has no active org (only
possible for accounts whose signup-time bootstrap failed), we fall back
to user-keyed counters so quotas still apply rather than silently going
unlimited.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from django.db import models as _  # noqa — ensure app registry is ready

logger = logging.getLogger(__name__)


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _resolve_active_org_id(user_id: str) -> Optional[str]:
    """Look up the user's active workspace. Returns None if the user
    has no active org (e.g. signup bootstrap failed); callers fall back
    to user-keyed records so quotas don't disappear."""
    from authentication.models import UserAccount
    try:
        user = UserAccount.objects.filter(id=str(user_id)).first()
        if not user:
            return None
        profile = user.profile or {}
        org_id = profile.get("active_organization_id")
        return str(org_id) if org_id else None
    except Exception as exc:
        logger.warning("Could not resolve active_organization for user %s: %s", user_id, exc)
        return None


def _record_lookup_keys(user_id: str) -> Tuple[dict, dict]:
    """Return (filter_kwargs, create_defaults) for UsageRecord:
    org-keyed when an active org exists, user-keyed otherwise."""
    period = _current_period()
    org_id = _resolve_active_org_id(user_id)
    if org_id:
        return (
            {"organization_id": org_id, "period": period},
            {"user_id": str(user_id)},
        )
    return (
        {"organization_id": "", "user_id": str(user_id), "period": period},
        {},
    )


def _get_or_create_record(user_id: str):
    from .models import UsageRecord
    filter_kwargs, defaults = _record_lookup_keys(user_id)
    record, _ = UsageRecord.objects.get_or_create(defaults=defaults, **filter_kwargs)
    return record


def _get_limits(user_id: str) -> dict:
    """Limits attach to the org first (so all teammates share one plan),
    falling back to a user-keyed BillingProfile for legacy single-user
    accounts that pre-date organizations, then to env-var defaults."""
    from .models import BillingProfile, UsageRecord
    defaults = UsageRecord.default_limits()
    try:
        org_id = _resolve_active_org_id(user_id)
        profile = None
        if org_id:
            profile = BillingProfile.objects.filter(organization_id=org_id).first()
        if profile is None:
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
    """Raised when a workspace has hit its monthly usage limit."""

    def __init__(self, resource: str, limit: int, used: int):
        self.resource = resource
        self.limit = limit
        self.used = used
        super().__init__(
            f"Monthly {resource} quota exceeded: {used}/{limit}. "
            "Upgrade your plan or wait until next month."
        )


def check_quota(user_id: str, resource: str) -> None:
    """Raise QuotaExceeded if the caller's workspace has hit its limit
    for `resource`.

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
    """Increment the workspace's usage counter after a successful operation."""
    from django.db.models import F
    from .models import UsageRecord

    field_map = {
        "analysis": "analysis_count",
        "work_item_gen": "work_item_gen_count",
        "llm_tokens": "llm_tokens_used",
    }
    field = field_map.get(resource)
    if not field:
        return

    # Ensure the row exists before .update() — .update() on an empty
    # queryset is a silent no-op, so a record_usage call without a prior
    # check_quota would otherwise drop usage.
    _get_or_create_record(user_id)
    filter_kwargs, _defaults = _record_lookup_keys(user_id)
    UsageRecord.objects.filter(**filter_kwargs).update(**{field: F(field) + amount})
