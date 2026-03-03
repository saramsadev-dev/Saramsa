# Feature: Integrations & Project Management

## Overview
Manages projects, integration accounts (Azure DevOps, Jira), and provides analysis history/trends per project.

## Project Endpoints
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/integrations/projects/create/` | Bearer | Create project |
| GET | `/api/integrations/projects/list/` | Bearer | List user's projects |
| GET | `/api/integrations/projects/<id>/` | Bearer | Get project detail |
| GET | `/api/integrations/projects/<id>/analysis/latest/` | Bearer | Latest analysis for project |
| GET | `/api/integrations/projects/<id>/trends/` | Bearer | Trend data |
| GET | `/api/integrations/projects/<id>/trends/aspects/<key>/` | Bearer | Aspect-level trends |
| GET/PUT | `/api/integrations/projects/<id>/roles/` | Bearer | Manage project roles |

## Integration Account Endpoints
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/integrations/` | Bearer | List integration accounts |
| POST | `/api/integrations/azure/` | Bearer | Create Azure DevOps integration |
| POST | `/api/integrations/jira/` | Bearer | Create Jira integration |
| POST | `/api/integrations/<id>/test/` | Bearer | Test connection |
| DELETE | `/api/integrations/<id>/` | Bearer | Remove integration |

## External Project Fetching
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/integrations/azure/projects/` | Bearer | Fetch projects from Azure DevOps |
| GET | `/api/integrations/jira/projects/` | Bearer | Fetch projects from Jira |
| GET | `/api/integrations/external/projects/` | Bearer | Fetch from any connected platform |
| POST | `/api/integrations/external/projects/check/` | Bearer | Check if external project exists |

## Analysis History
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/insights/history/` | Bearer | Analysis history for project |
| GET | `/api/insights/history/quarter/` | Bearer | Quarter-based breakdown |
| GET | `/api/insights/history/cumulative/` | Bearer | Cumulative analysis |
| GET | `/api/insights/history/compare/` | Bearer | Compare two analyses |

## Insight Review
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/insights/insights/review/` | Bearer | List insights pending review |
| PUT | `/api/insights/insights/review/update/` | Bearer | Accept/reject insights |
| GET/PUT | `/api/insights/insights/rules/` | Bearer | Manage review rules |
| POST | `/api/insights/insights/rules/apply/` | Bearer | Apply rules to insights |

## Key Files
| File | Purpose |
|------|---------|
| `integrations/views.py` | Integration + project views |
| `integrations/urls.py` | URL routing |
| `integrations/services/` | Platform-specific connectors |
