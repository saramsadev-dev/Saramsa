# Saramsa – Agent Instructions

## Project Overview

Saramsa is a feedback analysis platform. Users upload customer feedback (CSV, JSON, PDF, plain text, or Word DOCX), and the system runs sentiment analysis, extracts aspects/features, generates insights, and produces actionable work items (user stories). The stack is Django (backend) + Next.js (frontend) + Celery + Redis + Azure Cosmos DB.

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
  tests/fixtures/         Mock test data (JSON, CSV, PDF, TXT, DOCX)
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
- **TXT upload**: One non-empty line per comment (parsed client-side; line endings normalized)
- **PDF upload**: Backend extracts text via `feedback_analysis/file_extractors.py` (pypdf); one extracted line per comment. Encrypted/scanned PDFs are rejected. Goes through `POST /api/insights/ingest/` which is async and returns `{task_id}` like `/analyze/`.
- **DOCX upload**: Backend extracts via python-docx; one non-empty paragraph per comment, plus text from any tables. Goes through the same `POST /api/insights/ingest/` async endpoint.
- Test data lives in `backend/tests/fixtures/mock_feedback.{json,csv,txt,pdf,docx}` (rebuild via `python backend/scripts/build_pdf_test_fixtures.py`)

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
4. On failure: prints errors and exits non-zero

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

## Local Dev Workflow & Checks

- **Backend sanity before push**:
  - Run Django tests locally when changing backend logic:
    ```bash
    cd backend
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python manage.py test
    ```
  - Optionally run the API registry scripts manually if you want to see the same checks as the pre-push hook:
    ```bash
    python scripts/sync_api_registry_from_swagger.py
    python scripts/test_api_registry.py --notify-slack
    ```
- **Frontend sanity before push**:
  - From `saramsa-ai/`:
    ```bash
    npm install
    npm run build
    ```
  - If `npm run lint` exists, run it before opening a PR.

The pre-push hook is the final guardrail for the backend API registry. GitHub Actions workflows then run full CI/CD for backend, frontend, and Celery.

## CI/CD Pipelines

- **Backend (`saramsa-backend`)**:
  - Workflow: `.github/workflows/master_saramsa-backend.yml`
  - Trigger: push to `master` touching `backend/**`
  - Steps (simplified):
    - Create/restore Python virtualenv and install `backend/requirements.txt`
    - Run Django tests
    - Run `collectstatic`
    - Zip backend code into `artifact/backend.zip`
    - Login to Azure and deploy zip to `saramsa-backend` App Service
    - Hit a configurable `BACKEND_HEALTH_URL` (GitHub secret) to verify the deployment

- **Frontend (`saramsa-fe`)**:
  - Workflow: `.github/workflows/master_saramsa-fe.yml`
  - Trigger: push to `master` touching `saramsa-ai/**`
  - Steps (simplified):
    - Install Node.js and `npm ci`
    - Optionally run `npm run lint` if a `lint` script exists
    - Build the Next.js app with `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_API_BASE_URL` pointed at the backend
    - Package the standalone output into `frontend.zip`
    - Deploy `frontend.zip` to `saramsa-fe` App Service using the publish profile
    - Hit a configurable `FRONTEND_HEALTH_URL` (GitHub secret) to verify the deployment

- **Celery GPU worker (`saramsa-celery-gpu`)**:
  - Base image workflow: `.github/workflows/celery-gpu-base-image.yml`
    - Builds and pushes a GPU base image to `saramsaacr` when requirements change.
  - App image workflow: `.github/workflows/master_saramsa-celery-gpu.yml`
    - Builds a Celery GPU worker image on top of the base image
    - Pushes to `saramsaacr`
    - Updates the `saramsa-celery-gpu` Container App to the new image
    - Polls the Container App health until the latest revision is `Healthy`

- **API Registry Tests**:
  - Workflow: `.github/workflows/api-registry-tests.yml`
  - Trigger: push or PR touching `backend/**`
  - Steps:
    - Sync API registry from the live Swagger spec
    - Run API registry tests against the deployed backend (with Slack notifications on failure)

## DevOps Agent (Codex/Cursor)

Use a dedicated DevOps agent when CI/CD or the pre-push hook fails.

- **Overview**:
  - The DevOps agent focuses on keeping backend, frontend, and Celery deployments healthy.
  - It fixes build, test, and deployment issues rather than adding new features.
- **Where to find full instructions**:
  - See `DEVOPS_AGENT.md` for:
    - Detailed scope and responsibilities.
    - Expected inputs (pre-push errors, CI logs, Azure logs).
    - Step-by-step behavior and guardrails.
    - Incident runbook and example prompts.
