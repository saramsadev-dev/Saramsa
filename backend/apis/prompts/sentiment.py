"""
Sentiment Analysis Prompts

Centralized sentiment analysis prompts. This module provides direct access to 
sentiment analysis prompts without depending on the aiCore prompt system to avoid circular imports.
"""

from .constants import get_prompt


def getSentAnalysisPrompt(company_name: str = None, feedback_data: str = None):
    """
    Get sentiment analysis prompt using the centralized prompt system.
    
    Args:
        company_name: Optional company name to get company-specific prompt
        feedback_data: Feedback comments/data to inject into prompt
    
    Returns:
        Rendered sentiment analysis prompt string with variables substituted
    
    Example:
        prompt = getSentAnalysisPrompt(
            company_name="Acme Corp",
            feedback_data="User feedback here..."
        )
    """
    # Get the prompt template
    prompt_template = get_prompt(company_name, "sentiment")
    
    # Simple variable substitution
    if feedback_data:
        prompt_template = prompt_template.replace("$feedback_data", str(feedback_data))
    
    return prompt_template