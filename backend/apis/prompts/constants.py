"""
AI Prompts Configuration

This module contains all AI prompts used throughout the application.
Now organized with separate prompt files for better maintainability.

Structure:
- PROMPTS: Main dictionary containing all prompts
- Each company can have its own prompts, with 'default' as fallback
- Each prompt type (sentiment, deep_analysis, validation) is imported from separate files
- Use $variable syntax for template variables (e.g., $feedback_data, $platform_name)
"""

# Import prompts from separate files
from .sentiment_prompt import (
    DEFAULT_SENTIMENT_PROMPT, 
    COMPANY_SPECIFIC_SENTIMENT_PROMPTS,
    CONFIDENCE_AWARE_SENTIMENT_PROMPT,
    INDUSTRY_SPECIFIC_PROMPTS
)
from .work_items_prompt import (
    DEFAULT_WORK_ITEMS_PROMPT, 
    COMPANY_SPECIFIC_WORK_ITEMS_PROMPTS,
    WORK_ITEMS_VALIDATION_PROMPT,
    CLARIFICATION_PROMPT
)

# Build the main PROMPTS dictionary with enhanced structure
PROMPTS = {
    "default": {
        "sentiment": DEFAULT_SENTIMENT_PROMPT,
        "deep_analysis": DEFAULT_WORK_ITEMS_PROMPT,
        "sentiment_confidence": CONFIDENCE_AWARE_SENTIMENT_PROMPT,
        "work_items_validation": WORK_ITEMS_VALIDATION_PROMPT,
        "clarification": CLARIFICATION_PROMPT
    }
}

# Add industry-specific context
INDUSTRY_CONTEXTS = INDUSTRY_SPECIFIC_PROMPTS

# Add company-specific prompts dynamically
def _build_company_prompts():
    """Build company-specific prompts from imported dictionaries."""
    # Add sentiment prompts for each company
    for company, prompt in COMPANY_SPECIFIC_SENTIMENT_PROMPTS.items():
        if company not in PROMPTS:
            PROMPTS[company] = {}
        PROMPTS[company]["sentiment"] = prompt
    
    # Add work items prompts for each company
    for company, prompt in COMPANY_SPECIFIC_WORK_ITEMS_PROMPTS.items():
        if company not in PROMPTS:
            PROMPTS[company] = {}
        PROMPTS[company]["deep_analysis"] = prompt

# Build company prompts on module load
_build_company_prompts()


def get_prompt(company_name=None, prompt_type="sentiment", industry=None, use_confidence=False):
    """
    Get a prompt template for the specified company and type.
    
    Args:
        company_name (str, optional): Company name to look up. Defaults to None.
        prompt_type (str): Type of prompt ('sentiment', 'deep_analysis', 'validation', 'clarification'). Defaults to 'sentiment'.
        industry (str, optional): Industry context ('saas', 'ecommerce', 'mobile_app'). Defaults to None.
        use_confidence (bool): Whether to use confidence-aware sentiment analysis. Defaults to False.
        
    Returns:
        str: The prompt template string
        
    Raises:
        ValueError: If the prompt is not found
    """
    # Determine the actual prompt type to use
    actual_prompt_type = prompt_type
    if prompt_type == "sentiment" and use_confidence:
        actual_prompt_type = "sentiment_confidence"
    
    # Try company-specific prompt first
    if company_name and company_name in PROMPTS:
        company_prompts = PROMPTS.get(company_name, {})
        if actual_prompt_type in company_prompts:
            base_prompt = company_prompts[actual_prompt_type]
        else:
            # Fallback to default for this company
            base_prompt = PROMPTS.get('default', {}).get(actual_prompt_type)
    else:
        # Use default prompts
        base_prompt = PROMPTS.get('default', {}).get(actual_prompt_type)
    
    if not base_prompt:
        # If not found, raise error
        error_msg = f"Prompt '{prompt_type}' not found"
        if company_name:
            error_msg += f" for company '{company_name}'"
        available_prompts = list(PROMPTS.get('default', {}).keys())
        error_msg += f". Available prompts: {', '.join(available_prompts)}"
        raise ValueError(error_msg)
    
    # Add industry context if specified
    if industry and industry in INDUSTRY_CONTEXTS and prompt_type == "sentiment":
        industry_context = INDUSTRY_CONTEXTS[industry]
        base_prompt = base_prompt + "\n\n" + industry_context
    
    return base_prompt


def add_company_prompts(company_name, prompts_dict):
    """
    Add or update prompts for a specific company.
    
    Args:
        company_name (str): Name of the company
        prompts_dict (dict): Dictionary containing prompt types and their templates
    """
    if company_name not in PROMPTS:
        PROMPTS[company_name] = {}
    
    PROMPTS[company_name].update(prompts_dict)

def get_enhanced_prompt(prompt_type, feedback_data, platform_name=None, company_name=None, 
                       industry=None, project_metadata=None, use_confidence=False):
    """
    Get a fully populated prompt with all variables substituted.
    
    Args:
        prompt_type (str): Type of prompt to get
        feedback_data (str): The feedback data to analyze
        platform_name (str, optional): Platform name (Azure, Jira, etc.)
        company_name (str, optional): Company name for custom prompts
        industry (str, optional): Industry context
        project_metadata (dict, optional): Additional project context
        use_confidence (bool): Whether to use confidence-aware analysis
        
    Returns:
        str: Fully populated prompt ready for LLM
    """
    # Get the base prompt
    base_prompt = get_prompt(
        company_name=company_name, 
        prompt_type=prompt_type, 
        industry=industry,
        use_confidence=use_confidence
    )
    
    # Substitute variables
    populated_prompt = base_prompt.replace('$feedback_data', str(feedback_data))
    
    if platform_name:
        populated_prompt = populated_prompt.replace('$platform_name', platform_name)
    
    # Add project context if available
    if project_metadata:
        context_info = f"\n\nPROJECT CONTEXT:\n"
        context_info += f"- Project: {project_metadata.get('name', 'Unknown')}\n"
        context_info += f"- Type: {project_metadata.get('type', 'Unknown')}\n"
        if project_metadata.get('description'):
            context_info += f"- Description: {project_metadata['description']}\n"
        populated_prompt += context_info
    
    return populated_prompt

def validate_prompt_variables(prompt_template):
    """
    Validate that all required variables in a prompt template are properly formatted.
    
    Args:
        prompt_template (str): The prompt template to validate
        
    Returns:
        dict: Validation results with variables found and any issues
    """
    import re
    
    # Find all variables in the format $variable_name
    variables = re.findall(r'\$(\w+)', prompt_template)
    
    # Check for common issues
    issues = []
    if '$feedback_data' not in prompt_template:
        issues.append("Missing required $feedback_data variable")
    
    # Check for malformed variables
    malformed = re.findall(r'\$[^a-zA-Z_]', prompt_template)
    if malformed:
        issues.append(f"Malformed variables found: {malformed}")
    
    return {
        "variables_found": list(set(variables)),
        "variable_count": len(variables),
        "issues": issues,
        "is_valid": len(issues) == 0
    }

def get_prompt_performance_metrics():
    """
    Get metrics about prompt usage and performance.
    This would be enhanced with actual usage tracking in production.
    
    Returns:
        dict: Performance metrics for prompts
    """
    return {
        "total_prompts": len(PROMPTS.get('default', {})),
        "company_specific_prompts": len(PROMPTS) - 1,  # Exclude 'default'
        "industry_contexts": len(INDUSTRY_CONTEXTS),
        "prompt_types": list(PROMPTS.get('default', {}).keys()),
        "last_updated": "2026-01-11"  # This would be dynamic in production
    }