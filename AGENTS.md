# Saramsa – Agent Instructions

## Project Overview

Saramsa is a feedback analysis platform. Users upload customer feedback (CSV/JSON), and the system runs sentiment analysis, extracts aspects/features, generates insights, and produces actionable work items (user stories). The stack is Django (backend) + Next.js (frontend) + Celery + Redis + Azure Cosmos DB.

## Repository Layout

```
backend/                  Django API server
  feedback_analysis/      Core analysis pipeline (views, services, schemas)
  authentication/         JWT auth (SimpleJWT)
  work_items/             Work item generation and Azure DevOps/Jira push
  integrations/           External platform connectors (DevOps, Jira)
  aiCore/                 LLM completion service, local sentiment, aspect classification
  apis/                   Shared infra (Cosmos, cache, response format, prompts, URLs)
  scripts/                Automation scripts (API registry sync, test runner, user creation)
  tests/fixtures/         Mock test data (JSON/CSV)
saramsa-ai/               Next.js frontend
  src/app/                Pages (Next.js App Router)
  src/components/ui/      UI components (dashboard, cards, charts, navbar)
  src/store/              Redux store (RTK Query slices)
  src/lib/                API request helpers
celery_ops/               Celery worker configuration
infra/                    Infrastructure and deployment scripts
.githooks/                Git hooks (pre-push API registry validation)
```

## Running Locally

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py runserver

# Frontend
cd saramsa-ai
npm install
npm run dev

# Celery worker (requires Redis)
cd celery_ops
celery -A celery_config worker --loglevel=info
```

## Key Conventions

### API Response Format
All API responses use `StandardResponse` from `apis/core/response.py`:
```json
{"data": {...}, "message": "...", "success": true}
```
Error responses follow RFC 7807 Problem Details.

### Feedback Data Format
- **JSON upload**: `{"comments": ["comment1", "comment2", ...]}` or root array of strings
- **CSV upload**: Must have a `comment` column (fallback: first column)
- Test data lives in `backend/tests/fixtures/mock_feedback.json` and `.csv`

### Locked Extraction Schema
LLM outputs must conform to the schema in `feedback_analysis/schemas/semantic_schema.py`:
- Fields: `comment_id`, `sentiment`, `confidence`, `intent_type`, `intent_phrase`, `keywords`, `aspects`
- Sentiment: `POSITIVE | NEGATIVE | NEUTRAL`
- Confidence: `HIGH | MEDIUM | LOW`
- Intent: `PRAISE | COMPLAINT | SUGGESTION | OBSERVATION`
- No optional fields. No extra keys.

### API Registry
- `backend/api-registry.json` tracks all API endpoints with test expectations
- New endpoints must be configured here before pushing (the pre-push hook enforces this)
- Fields: `name`, `method`, `path`, `auth`, `enabled`, `expected_status`, `expect_json_keys`, `body`
- Remove `"discovered": true` after configuring an endpoint

### Database
- Production: Azure Cosmos DB (containers: `users`, `analysis`, `projects`, `work_items`, etc.)
- Local dev: `apis/infrastructure/local_json_db.py` provides a file-based Cosmos mock at `backend/local_db/`

### Authentication
- JWT via `rest_framework_simplejwt`
- Roles: `admin`, `user`
- Project-level permissions: `IsProjectViewer`, `IsProjectEditor`

### Environment Variables (backend/.env)
```
API_BASE_URL=http://127.0.0.1:8000
SECRET_KEY=...
OPENAI_API_KEY=...
COSMOS_ENDPOINT=...
COSMOS_KEY=...
REDIS_URL=redis://127.0.0.1:6379/0
LOGIN_EMAIL=...
LOGIN_PASSWORD=...
```

## Pre-push Hook

The `.githooks/pre-push` hook runs automatically before every push:
1. Syncs `api-registry.json` from the live Swagger schema
2. Fails if any endpoints are unconfigured (`discovered: true` + `enabled: false`)
3. Runs API tests against all enabled endpoints
4. On failure: opens a Windows Terminal with `codex --yolo` and a prompt containing the errors

To configure the hook: `git config core.hooksPath .githooks`

## When Fixing Errors

1. Read the error output carefully
2. For unconfigured API endpoints: look at the Django view to understand the response shape, then update `api-registry.json`
3. For test failures: fix the code or adjust the registry config
4. Always re-run both scripts to verify:
   ```bash
   cd backend
   python scripts/sync_api_registry_from_swagger.py
   python scripts/test_api_registry.py --notify-slack
   ```
