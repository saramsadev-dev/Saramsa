# Feature: Work Items & User Stories

## Overview
Generates actionable work items (user stories, bugs, tasks) from analysis results and allows submission to Azure DevOps or Jira.

## Endpoints
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/work-items/generate/` | Bearer | Generate work items from analysis |
| POST | `/api/work-items/submit/` | Bearer | Submit work items to DevOps/Jira |
| GET | `/api/work-items/` | Bearer | List work items for project |
| GET | `/api/work-items/<id>/` | Bearer | Get single work item |
| PUT | `/api/work-items/<id>/update/` | Bearer | Update work item |
| GET | `/api/work-items/platform/<platform>/` | Bearer | List by platform |
| DELETE | `/api/work-items/remove/` | Bearer | Remove work items |
| GET/PUT | `/api/work-items/quality-rules/` | Bearer | Manage quality gate rules |
| POST | `/api/work-items/quality-check/` | Bearer | Run quality check on items |

## Generation Flow
1. User triggers generation from the analysis dashboard
2. Backend takes analysis results (features, sentiments, keywords)
3. LLM generates structured work items per feature area
4. Work items are stored in Cosmos DB linked to the project
5. User can review, edit, and submit to external platforms

## Work Item Structure
```json
{
  "id": "wi_...",
  "title": "Improve CSV upload error handling",
  "description": "...",
  "type": "User Story",
  "feature_area": "File Upload",
  "priority": "High",
  "acceptance_criteria": ["..."],
  "submitted": false,
  "submitted_to": null
}
```

## Quality Gate
- Project-level rules in `quality-rules/`
- Checks run before submission (e.g., minimum acceptance criteria, description length)
- Configurable per project

## Key Files
| File | Purpose |
|------|---------|
| `work_items/views.py` | All work item views |
| `work_items/services.py` | Generation and DevOps/Jira push logic |
| `work_items/urls.py` | URL routing |
