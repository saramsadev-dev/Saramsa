"""
Centralized Prompts Package

All AI prompts for the application are centralized here for better organization,
maintainability, and reusability across different apps.

Structure:
- sentiment.py: Sentiment analysis prompts
- work_items.py: Work item generation prompts  
- constants.py: Shared constants and configurations
"""

from .sentiment import getSentAnalysisPrompt
from .work_items import getDeepAnalysisPrompt, WORK_ITEM_TYPES_BY_TEMPLATE
from .constants import PROMPTS, get_prompt, add_company_prompts

__all__ = [
    'getSentAnalysisPrompt',
    'getDeepAnalysisPrompt', 
    'WORK_ITEM_TYPES_BY_TEMPLATE',
    'PROMPTS',
    'get_prompt',
    'add_company_prompts'
]