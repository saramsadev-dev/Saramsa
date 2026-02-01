"""
Contract boundaries for Phase-0: Decision Layer vs Narration Layer.

This module is the single source of truth for what the system decides
(deterministic) vs what the LLM is allowed to narrate (text-only).
"""

# Deterministic responsibilities (non-LLM)
DECISION_LAYER = {
    # Aspect assignment and taxonomy
    "aspect_assignment",
    "taxonomy_health_checks",

    # Sentiment and aggregation
    "sentiment_classification",
    "aggregation_logic",

    # Work-item rules
    "work_item_existence_rules",
    "work_item_priority_rules",
    "threshold_logic",

    # Data integrity and storage
    "schema_conversion",
    "persistence_decisions",
}

# LLM-assisted narration (text-only)
NARRATION_LAYER = {
    # Bootstrap naming only
    "aspect_naming_bootstrap_only",

    # Narrative outputs
    "insight_wording",
    "feature_descriptions_text_only",
    "work_item_titles",
    "work_item_descriptions",
    "summaries_explanations",
}
