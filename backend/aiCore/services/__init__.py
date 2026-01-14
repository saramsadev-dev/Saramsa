"""
AI Core Services Package

This package contains all AI/ML related services including:
- OpenAI client management
- Completion services
- Utility functions for AI processing
"""

from .completion_service import generate_completions
from .openai_client import get_azure_client, AzureOpenAIClient
from .utilities import (
    fix_json_string, 
    validate_json_structure, 
    flatten_feedback,
    sanitize_llm_output,
    extract_json_from_text
)

__all__ = [
    'generate_completions',
    'get_azure_client',
    'AzureOpenAIClient',
    'fix_json_string',
    'validate_json_structure',
    'flatten_feedback',
    'sanitize_llm_output',
    'extract_json_from_text'
]