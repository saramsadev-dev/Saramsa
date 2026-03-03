# Feature: Feedback Analysis Pipeline

## Overview
Accepts customer feedback (CSV or JSON), runs sentiment analysis and aspect extraction, and produces structured insights. This is the core feature of Saramsa.

## Entry Points
- **Upload**: `POST /api/insights/upload/` — accepts `file` + `project_id` (multipart form)
- **Analyze**: `POST /api/insights/analyze/` — accepts `{"comments": [...], "project_id": "...", "file_name": "..."}`
- **Task Status**: `GET /api/insights/task-status/<task_id>/`
- **Task List**: `GET /api/insights/tasks/`
- **Task Stream**: `GET /api/insights/tasks/stream/` (SSE)

## Processing Modes

### LLM Pipeline (default)
1. Comments are chunked (~30 per batch) by `processing_service.py`
2. Each chunk is sent to the LLM with `getSentAnalysisPrompt()` from `apis/prompts.py`
3. LLM returns extractions per the locked schema (`schemas/semantic_schema.py`)
4. `schema_validator.py` validates every extraction (no missing/extra fields, enum values match)
5. `aggregation_service.py` aggregates into overall sentiment, per-feature breakdowns, and keywords

### Local ML Pipeline (`USE_LOCAL_PIPELINE=true`)
1. Bi-encoder (`all-MiniLM-L6-v2`) classifies aspects via cosine similarity
2. `LocalSentimentService` runs batch sentiment classification
3. GPT generates a narrative summary from aggregated results

## Locked Extraction Schema
All LLM outputs must match `feedback_analysis/schemas/semantic_schema.py`:

| Field | Type | Values |
|-------|------|--------|
| `comment_id` | int | 0-based index |
| `sentiment` | enum | `POSITIVE`, `NEGATIVE`, `NEUTRAL` |
| `confidence` | enum | `HIGH`, `MEDIUM`, `LOW` |
| `intent_type` | enum | `PRAISE`, `COMPLAINT`, `SUGGESTION`, `OBSERVATION` |
| `intent_phrase` | string | Key phrase from the comment |
| `keywords` | string[] | Extracted keywords |
| `aspects` | string[] | Matched aspect/feature names |

## Aggregated Output Shape
```json
{
  "overall": {"positive": 0.6, "negative": 0.3, "neutral": 0.1},
  "counts": {"total": 10, "positive": 6, "negative": 3, "neutral": 1},
  "features": [
    {
      "name": "Dashboard UI",
      "sentiment": {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
      "keywords": ["fast", "clean", "dark mode"],
      "comment_count": 3
    }
  ],
  "positive_keywords": ["fast", "clean", "intuitive"],
  "negative_keywords": ["slow", "error", "broken"]
}
```

## Taxonomy
- Project-level aspect taxonomy stored in Cosmos DB
- Created on first analysis if none exists (GPT suggests initial aspects)
- Aspects are frozen for the duration of a single analysis run
- Managed by `taxonomy_service.py`

## Key Files
| File | Purpose |
|------|---------|
| `feedback_analysis/views/file_upload_views.py` | CSV/JSON parsing and upload |
| `feedback_analysis/views/analysis_views.py` | Analyze endpoint, task status, comments retrieval |
| `feedback_analysis/services/processing_service.py` | LLM chunking and extraction |
| `feedback_analysis/services/aggregation_service.py` | Sentiment/aspect aggregation |
| `feedback_analysis/services/schema_validator.py` | Extraction validation |
| `feedback_analysis/services/taxonomy_service.py` | Aspect taxonomy CRUD |
| `feedback_analysis/services/narration_service.py` | GPT narrative generation |
| `feedback_analysis/schemas/semantic_schema.py` | Locked schema + validators |
| `feedback_analysis/tasks.py` | Celery task definitions |

## Test Data
Mock feedback (10 comments covering all sentiment/intent types):
- `backend/tests/fixtures/mock_feedback.json`
- `backend/tests/fixtures/mock_feedback.csv`
