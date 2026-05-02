# Feature: Billing & Usage Quotas

## Overview
Per-user monthly quotas on LLM-billable operations. Requests that would push a
user past their limit are rejected with HTTP 429 before any work runs. Usage
counters are incremented on success.

Three resources are tracked independently:

| Resource | Counter | Default monthly limit | Env var |
|---|---|---|---|
| `analysis` | `UsageRecord.analysis_count` | 50 | `QUOTA_ANALYSIS_PER_MONTH` |
| `work_item_gen` | `UsageRecord.work_item_gen_count` | 100 | `QUOTA_WORK_ITEMS_PER_MONTH` |
| `llm_tokens` | `UsageRecord.llm_tokens_used` | 500000 | `QUOTA_LLM_TOKENS_PER_MONTH` |

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/billing/usage/` | Bearer | Current period usage + remaining for the calling user |

Sample response:
```json
{
  "data": {
    "period": "2026-05",
    "usage": {
      "analysis":      {"used": 12, "limit": 50,  "remaining": 38},
      "work_item_gen": {"used": 4,  "limit": 100, "remaining": 96},
      "llm_tokens":    {"used": 0,  "limit": 500000, "remaining": 500000}
    }
  }
}
```

## Protected endpoints

| Endpoint | Resource consumed |
|---|---|
| `POST /api/insights/analyze/` | `analysis` |
| `POST /api/insights/upload/` | `analysis` |
| `POST /api/feedback/keywords/update/` | `analysis` |
| `POST /api/insights/user-story-creation/` | `work_item_gen` |

When over quota, these return:
```json
{
  "title": "Quota exceeded",
  "detail": "Monthly analysis quota exceeded: 50/50. Upgrade your plan or wait until next month.",
  "status": 429
}
```

## Per-user overrides
A `BillingProfile` row's `metadata` JSON may set custom limits:
```json
{"quota_overrides": {"analysis_limit": 200, "work_item_gen_limit": 500}}
```
These override the env var defaults for that user only.

## Implementation

| File | Purpose |
|------|---------|
| `billing/models.py` | `UsageRecord` (per user/month), `BillingProfile` |
| `billing/quota.py` | `check_quota(user_id, resource)` + `record_usage(user_id, resource)` + `QuotaExceeded` |
| `billing/views.py` | `UsageStatusView` |
| `billing/urls.py` | URL routing |

The view-level pattern is:
```python
from billing.quota import check_quota, record_usage, QuotaExceeded
try:
    check_quota(request.user.id, "analysis")
except QuotaExceeded as exc:
    return StandardResponse.error(
        title="Quota exceeded", detail=str(exc),
        status_code=429, instance=request.path,
    )
# ... do the billable work ...
record_usage(str(request.user.id), "analysis")
```
For async views, wrap `check_quota` and `record_usage` in `sync_to_async`.

**Gate ordering:** put `check_quota` after auth/permission checks and after
trivial input presence checks (e.g. file or user-id missing) but **before**
any payload validation, project-context lookup, taxonomy resolution, or LLM
call. The intent is to fail fast for over-quota users without consuming any
billable downstream work, while still surfacing 401/400 responses for
clearly-broken requests instead of misdirecting them as a quota error.

`record_usage` should run only on a successful response and should be
wrapped in a try/log so that a transient accounting failure does not turn
a successful request into a 500.

## Known limits

- **Race**: two concurrent requests at limit-1 can both pass `check_quota` and
  both increment, briefly going one over. Acceptable for current scale; would
  need a `SELECT ... FOR UPDATE` to fix exactly.
- **`llm_tokens` not yet wired**: the field exists on `UsageRecord` but no code
  path increments it. `aiCore.services.completion_service.generate_completions`
  returns token counts but doesn't call `record_usage("...", "llm_tokens", n)`.
- **Usage records are recorded on attempt, not just success**: matches the
  existing `AnalyzeCommentsView` pattern (recorded after task is queued, even if
  the background task later fails). Trade reliability for blast-radius
  prevention against runaway retries.

## Testing

Tests live in `billing/tests/`. Run with the test settings module:
```bash
DJANGO_SETTINGS_MODULE=apis.test_settings python manage.py test billing.tests
```

`apis/test_settings.py` overrides `DATABASES` to in-memory SQLite and sets
`DJANGO_TEST_MODE=1` to bypass the production Neon-only DB assertion.
