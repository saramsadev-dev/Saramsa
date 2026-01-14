"""
Structured Prompt Registry Module

This module provides a registry for loading and managing structured prompts
from the prompts.py configuration file.
"""

from typing import Dict, Optional
from .builder import buildStructuredPrompt
import logging

# Import prompts from centralized apis/prompts package
# Django sets up the backend directory in sys.path, so direct import should work
try:
    from apis.prompts import get_prompt
except ImportError:
    # Fallback: try importing from parent directory
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).resolve().parent.parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from apis.prompts import get_prompt

logger = logging.getLogger("apis.app")


class StructuredPromptRegistry:
    """
    Registry for managing structured prompts loaded from prompts.py configuration.
    
    This class provides methods to get prompt templates and build them with
    structured data using the $variable syntax.
    """
    
    def __init__(self):
        """Initialize the registry."""
        pass
    
    def _get_template(self, company_name: Optional[str] = None, prompt_key: str = "sentiment") -> Optional[str]:
        """
        Get prompt template string for a specific company and prompt type.
        
        Args:
            company_name: Company name to look up (optional)
            prompt_key: Type of prompt ('sentiment' or 'deep_analysis')
            
        Returns:
            Prompt template string or None if not found
        """
        try:
            return get_prompt(company_name=company_name, prompt_type=prompt_key)
        except ValueError:
            return None
    
    def getSentimentAnalysisPrompt(
        self,
        company_name: Optional[str] = None,
        feedback_data: Optional[str] = None
    ) -> str:
        """
        Get and build sentiment analysis prompt using structured template system.
        
        Args:
            company_name: Optional company name to get company-specific prompt
            feedback_data: Feedback comments/data to inject into prompt
            
        Returns:
            Rendered sentiment analysis prompt string
            
        Raises:
            ValueError: If prompt template is not found in prompts.py
        """
        template_str = self._get_template(company_name, "sentiment")
        
        if not template_str:
            error_msg = f"Sentiment analysis prompt not found in prompts.py"
            if company_name:
                error_msg += f" for company '{company_name}'"
            error_msg += ". Please configure prompts.py with 'default.sentiment' or company-specific prompt."
            raise ValueError(error_msg)
        
        return buildStructuredPrompt(
            template=template_str,
            feedback_data=feedback_data
        )
    
    def getDeepAnalysisPrompt(
        self,
        platform: str = 'azure',
        project_metadata: Optional[Dict] = None,
        company_name: Optional[str] = None,
        feedback_data: Optional[str] = None
    ) -> str:
        """
        Get and build deep analysis prompt using structured template system.
        
        Args:
            platform: 'azure' or 'jira' (default: 'azure')
            project_metadata: Optional dict with project info (for Jira dynamic prompts)
            company_name: Optional company name to get company-specific prompt
            feedback_data: Feedback comments/data to inject into prompt
            
        Returns:
            Rendered deep analysis prompt string
            
        Raises:
            ValueError: If prompt template is not found in prompts.py
        """
        template_str = self._get_template(company_name, "deep_analysis")
        
        if not template_str:
            error_msg = f"Deep analysis prompt not found in prompts.py"
            if company_name:
                error_msg += f" for company '{company_name}'"
            error_msg += ". Please configure prompts.py with 'default.deep_analysis' or company-specific prompt."
            raise ValueError(error_msg)
        
        # Build context for template rendering
        is_jira = platform.lower() == 'jira'
        tag_field = "labels" if is_jira else "tags"
        platform_name = "Jira" if is_jira else "Azure DevOps"
        
        # Prepare variables for template
        template_vars = {
            'platform_name': platform_name,
            'tag_field': tag_field,
        }
        
        if feedback_data:
            template_vars['feedback_data'] = feedback_data
        
        # If project_metadata is provided for Jira, add it to context
        if is_jira and project_metadata:
            project = project_metadata.get('project', {})
            available_issue_types = project_metadata.get('available_issue_type_names', [])
            project_name = project.get('name', 'Unknown Project')
            
            template_vars['project_name'] = project_name
            if available_issue_types:
                template_vars['issue_type_list'] = ', '.join(available_issue_types)
        
        return buildStructuredPrompt(template=template_str, **template_vars)


# Global registry instance
_structured_prompt_registry = None


def getStructuredPromptRegistry() -> StructuredPromptRegistry:
    """
    Get the global structured prompt registry instance (singleton pattern).
    
    Returns:
        StructuredPromptRegistry instance
    """
    global _structured_prompt_registry
    if _structured_prompt_registry is None:
        _structured_prompt_registry = StructuredPromptRegistry()
    return _structured_prompt_registry