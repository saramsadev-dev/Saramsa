"""
Structured Prompt System

This module provides a modern, reliable prompt system using Python's string.Template
to replace the old XML tag-based approach. It uses structured templates with clear
variable definitions and validation.

The new system uses $variable or ${variable} syntax (standard Python Template syntax)
instead of XML tags like <feedback_data>.
"""

from .builder import PromptBuilder, buildStructuredPrompt
from .registry import StructuredPromptRegistry

__all__ = [
    'PromptBuilder',
    'buildStructuredPrompt',
    'StructuredPromptRegistry',
]

