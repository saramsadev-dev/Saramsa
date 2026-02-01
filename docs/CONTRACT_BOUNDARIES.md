# Phase-0 Contract Boundaries

## Purpose of Phase-0
Phase-0 locks the contract between deterministic system logic and LLM narration.
It prevents boundary drift by making responsibilities explicit and enforceable.

## Definitions

### Decision Layer
Deterministic logic that produces outcomes, counts, thresholds, priorities, and persistence decisions.
The LLM must not decide or alter these.

### Narration Layer
Text-only outputs that describe or explain deterministic results.
The LLM may provide wording, but not decisions.

## Responsibilities

| Responsibility | Owner | Enforcement mechanism |
|---|---|---|
| Aspect assignment | System | Deterministic pipeline + boundary guards |
| Sentiment classification | System | Deterministic pipeline + schema validation |
| Aggregation logic | System | Deterministic aggregation services |
| Work-item existence rules | System | Deterministic rules + boundary guards |
| Work-item priority rules | System | Deterministic prioritization + boundary guards |
| Threshold logic | System | Deterministic constants/services |
| Taxonomy health checks | System | Deterministic checks + logs |
| Schema conversion | System | Schema validation + normalization |
| Persistence decisions | System | Repository/service layer |
| Aspect naming (bootstrap only) | LLM | Aspect suggestion prompt + boundary guards |
| Insight wording | LLM | GPT synthesis (text-only) + boundary guards |
| Feature descriptions (text only) | LLM | GPT synthesis (text-only) + boundary guards |
| Work-item titles | LLM | GPT synthesis / work-item prompt + boundary guards |
| Work-item descriptions | LLM | GPT synthesis / work-item prompt + boundary guards |
| Summaries / explanations | LLM | GPT synthesis + boundary guards |

## What will break if this contract is violated
- Metrics become untrustworthy because the LLM can change counts or sentiment.
- Prioritization becomes inconsistent across runs and environments.
- Work items can disappear or be created without deterministic justification.
- Aspect taxonomy drifts over time and comparisons become invalid.
- Debugging becomes impossible because decisions are no longer reproducible.

