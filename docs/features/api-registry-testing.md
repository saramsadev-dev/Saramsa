# Feature: API Registry & Automated Testing

## Overview
An automated system that discovers API endpoints from the Swagger schema, tracks them in a registry, and tests them before every push. Failures automatically trigger Codex CLI to fix issues.

## How It Works

### 1. Swagger Sync (`scripts/sync_api_registry_from_swagger.py`)
- Fetches the OpenAPI schema from `{API_BASE_URL}/api/schema/`
- Compares against `backend/api-registry.json`
- Adds new endpoints with `"discovered": true, "enabled": false`
- **Fails** if any endpoint has `discovered: true` and `enabled: false` (unconfigured)

### 2. API Tests (`scripts/test_api_registry.py`)
- Reads `api-registry.json`, runs every endpoint marked `"enabled": true`
- Authenticates via `API_TOKEN` or `LOGIN_EMAIL`/`LOGIN_PASSWORD`
- Validates response status codes and JSON keys
- Posts failures to Slack if `--notify-slack` flag and `SLACK_WEBHOOK_URL` are set

### 3. Pre-push Hook (`.githooks/pre-push`)
- Runs sync first, then tests
- On failure: captures error output, writes a prompt file, spawns a Windows Terminal running `codex --yolo` with the error context
- Codex reads the errors and autonomously fixes the issues

## Registry Entry Format
```json
{
  "name": "Login",
  "method": "POST",
  "path": "/api/auth/login/",
  "auth": "none",
  "enabled": true,
  "expected_status": 200,
  "expect_json_keys": ["data"],
  "body": {"email": "test@example.com", "password": "..."}
}
```

### Field Reference
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable endpoint name |
| `method` | string | HTTP method (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) |
| `path` | string | URL path (supports `{{PROJECT_ID}}` placeholder) |
| `auth` | string | `"none"` or `"bearer"` |
| `enabled` | boolean | Whether to run this test |
| `expected_status` | integer | Expected HTTP status code |
| `expect_json_keys` | string[] | Top-level keys that must exist in the response |
| `body` | object | Request body for POST/PUT/PATCH |
| `source` | string | `"swagger"` if auto-discovered |
| `discovered` | boolean | `true` if newly discovered and not yet configured |

## Configuring a New Endpoint
1. Look at the Django view to understand what status code it returns and the response shape
2. In `api-registry.json`, find the entry with `"discovered": true`
3. Set `"enabled": true`
4. Set `"expected_status"` to the correct value (200, 201, 204, etc.)
5. Set `"expect_json_keys"` to match the actual response (`["data"]` for most endpoints)
6. Add `"body"` if the method requires a request body
7. Remove the `"discovered"` and `"source"` fields
8. Run `python scripts/sync_api_registry_from_swagger.py` to verify

## Environment Variables
| Variable | Purpose |
|----------|---------|
| `API_BASE_URL` | Backend URL (default `http://127.0.0.1:8000`) |
| `API_TOKEN` | Pre-existing JWT token for tests |
| `LOGIN_EMAIL` | Auto-login email (fallback if no `API_TOKEN`) |
| `LOGIN_PASSWORD` | Auto-login password |
| `PROJECT_ID` | Used for `{{PROJECT_ID}}` placeholder |
| `SLACK_WEBHOOK_URL` | Slack notifications on failure |

## Setup
```bash
git config core.hooksPath .githooks
```

## Key Files
| File | Purpose |
|------|---------|
| `backend/api-registry.json` | The registry (source of truth for API tests) |
| `backend/scripts/sync_api_registry_from_swagger.py` | Swagger sync script |
| `backend/scripts/test_api_registry.py` | Test runner |
| `.githooks/pre-push` | Git hook orchestrator |
| `.github/workflows/api-registry-tests.yml` | CI workflow |
