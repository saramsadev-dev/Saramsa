"""
Semantic Schema Package

Locked semantic schema definitions for LLM outputs.
"""

from .semantic_schema import (
    CommentExtraction,
    Sentiment,
    Confidence,
    IntentType,
    REQUIRED_FIELDS,
    ALLOWED_SENTIMENT_VALUES,
    ALLOWED_CONFIDENCE_VALUES,
    ALLOWED_INTENT_TYPE_VALUES,
    validate_comment_extraction,
    normalize_comment_extraction,
    SCHEMA_DESCRIPTION,
    SCHEMA_VERSION,
)

__all__ = [
    'CommentExtraction',
    'Sentiment',
    'Confidence',
    'IntentType',
    'REQUIRED_FIELDS',
    'ALLOWED_SENTIMENT_VALUES',
    'ALLOWED_CONFIDENCE_VALUES',
    'ALLOWED_INTENT_TYPE_VALUES',
    'validate_comment_extraction',
    'normalize_comment_extraction',
    'SCHEMA_DESCRIPTION',
    'SCHEMA_VERSION',
]
