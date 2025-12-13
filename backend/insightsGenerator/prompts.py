import json
import os
from django.conf import settings

# Load prompts from environment variable
_PROMPTS_MAP = {}
try:
    prompts_json = os.getenv('PROMPTS_JSON', '{}')
    if prompts_json:
        _PROMPTS_MAP = json.loads(prompts_json)
except Exception as e:
    print(f"Warning: Failed to load PROMPTS_JSON from environment: {e}")
    _PROMPTS_MAP = {}


def _get_prompt(company_name: str = None, prompt_key: str = "sentiment") -> str:
    """
    Get prompt for a specific company and prompt type.
    
    Args:
        company_name: Company name to look up (optional)
        prompt_key: Type of prompt ('sentiment' or 'deep_analysis')
    
    Returns:
        Prompt string or None if not found
    """
    if not _PROMPTS_MAP:
        return None
    
    # Try company-specific prompt first
    if company_name and company_name in _PROMPTS_MAP:
        company_prompts = _PROMPTS_MAP.get(company_name, {})
        if prompt_key in company_prompts:
            return company_prompts[prompt_key]
    
    # Fallback to default
    default_prompts = _PROMPTS_MAP.get('default', {})
    if prompt_key in default_prompts:
        return default_prompts[prompt_key]
    
    return None

def getSentAnalysisPrompt(company_name: str = None):
    """
    Get sentiment analysis prompt for a company.
    
    Args:
        company_name: Optional company name to get company-specific prompt
    
    Returns:
        Sentiment analysis prompt string or None if not found in environment
    
    Raises:
        ValueError: If prompt is not found in PROMPTS_JSON environment variable
    """
    # Get prompt from environment variable only
    env_prompt = _get_prompt(company_name, "sentiment")
    if env_prompt:
        return env_prompt
    
    # No fallback - raise error if prompt not found
    error_msg = f"Sentiment analysis prompt not found in PROMPTS_JSON environment variable"
    if company_name:
        error_msg += f" for company '{company_name}'"
    error_msg += ". Please configure PROMPTS_JSON with 'default.sentiment' or company-specific prompt."
    raise ValueError(error_msg)

def getDeepAnalysisPrompt(platform='azure', project_metadata=None, company_name: str = None):
    """
    Unified deep analysis prompt that works for both Azure DevOps and Jira.
    
    Args:
        platform: 'azure' or 'jira' (default: 'azure')
        project_metadata: Optional dict with project info (for Jira dynamic prompts)
            {
                'project': {
                    'name': str,
                    'key': str,
                    'isCompanyManaged': bool,
                    'isTeamManaged': bool
                },
                'available_issue_type_names': [str]
            }
        company_name: Optional company name to get company-specific prompt
    
    Returns:
        Deep analysis prompt string from environment variable
    
    Raises:
        ValueError: If prompt is not found in PROMPTS_JSON environment variable
    """
    # Get prompt from environment variable only
    env_prompt = _get_prompt(company_name, "deep_analysis")
    
    if not env_prompt:
        # No fallback - raise error if prompt not found
        error_msg = f"Deep analysis prompt not found in PROMPTS_JSON environment variable"
        if company_name:
            error_msg += f" for company '{company_name}'"
        error_msg += ". Please configure PROMPTS_JSON with 'default.deep_analysis' or company-specific prompt."
        raise ValueError(error_msg)
    
    # Replace platform-specific placeholders if they exist
    # This allows companies to use {platform_name}, {tag_field}, etc. in their prompts
    is_jira = platform.lower() == 'jira'
    tag_field = "labels" if is_jira else "tags"
    platform_name = "Jira" if is_jira else "Azure DevOps"
    
    # Simple replacements for common placeholders
    env_prompt = env_prompt.replace("{platform_name}", platform_name)
    env_prompt = env_prompt.replace("{tag_field}", tag_field)
    
    # If project_metadata is provided for Jira, inject it
    if is_jira and project_metadata:
        project = project_metadata.get('project', {})
        available_issue_types = project_metadata.get('available_issue_type_names', [])
        project_name = project.get('name', 'Unknown Project')
        
        env_prompt = env_prompt.replace("{project_name}", project_name)
        if available_issue_types:
            issue_type_list = ', '.join(available_issue_types)
            env_prompt = env_prompt.replace("{issue_type_list}", issue_type_list)
    
    return env_prompt


# Explicit map of allowed work item types per Azure DevOps process template
WORK_ITEM_TYPES_BY_TEMPLATE = {
    "Agile": ["Epic", "Feature", "User Story", "Task", "Bug"],
    "Scrum": ["Epic", "Feature", "Product Backlog Item", "Task", "Bug"],
    "Basic": ["Epic", "Issue", "Task"],
    "CMMI": ["Epic", "Feature", "Requirement", "Task", "Bug"],
}
