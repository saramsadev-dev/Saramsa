# Saramsa Repo Overview

This repo contains the Saramsa backend (Django), frontend (Next.js), and supporting services (Celery, infra).

## Key Paths
- `backend/`: Django API (Cosmos DB, Celery, integrations)
- `saramsa-ai/`: Next.js frontend
- `celery_ops/`: Celery worker setup
- `infra/`: Infra scripts

## How To Run (local)
- Frontend: `cd saramsa-ai` then `npm install` and `npm run dev`
- Backend: `cd backend` then `python manage.py runserver`

## Production Notes
- Uses Cosmos DB containers configured in `backend/apis/settings.py`
- Azure DevOps/Jira integration in `backend/work_items` and `backend/integrations`

## Recent Features
- Insight Review rules + status storage
- Work item quality gate (project-level rules)
- Pipeline status widget + SSE task list

## Where to add features
- UI features: `saramsa-ai/src/components/ui`
- API endpoints: `backend/apis/urls.py` and app `urls.py`
- Business logic: `backend/*/services`

## Branching
- Use `feature/<name>` for new features
- Open PRs to `master`
