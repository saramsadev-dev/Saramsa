"""
Prompt Builder Module

This module provides structured prompt building using Python's string.Template
for reliable variable substitution. Replaces the old XML tag-based approach.
"""

import re
from string import Template
from typing import Optional, List
import logging

logger = logging.getLogger("apis.app")


class PromptBuilder:
    """
    Builder class for constructing prompts from templates with structured variables.
    
    Uses Python's string.Template syntax: $variable or ${variable}
    This is more reliable than XML tags and provides better error handling.
    
    Example:
        template = "Analyze the following: $feedback_data"
        builder = PromptBuilder(template)
        prompt = builder.build(feedback_data="User feedback here")
    """
    
    def __init__(self, template: str):
        """
        Initialize the prompt builder with a template string.
        
        Args:
            template: Template string with $variable or ${variable} placeholders
        """
        self.template = template
        self._template_obj = Template(template)
        self._variables = self._extract_variables(template)
    
    def _extract_variables(self, template: str) -> List[str]:
        """
        Extract variable names from template string.
        
        Supports both $variable and ${variable} syntax.
        
        Args:
            template: Template string
            
        Returns:
            List of variable names found in template
        """
        # Pattern matches $variable or ${variable}
        pattern = r'\$\{?(\w+)\}?'
        matches = re.findall(pattern, template)
        return list(set(matches))  # Return unique variable names
    
    def get_required_variables(self) -> List[str]:
        """
        Get list of variables that appear in the template.
        
        Returns:
            List of variable names
        """
        return self._variables.copy()
    
    def build(self, **kwargs) -> str:
        """
        Build the prompt by substituting variables from kwargs.
        
        Uses safe_substitute to leave missing variables as-is (for backward compatibility).
        This allows partial substitution without errors.
        
        Args:
            **kwargs: Variable values to substitute into template
            
        Returns:
            Rendered prompt string with variables substituted
        """
        try:
            # Use safe_substitute to avoid KeyError for missing variables
            # This allows backward compatibility with old prompts
            result = self._template_obj.safe_substitute(**kwargs)
            
            # Log warning if there are still unsubstituted variables
            remaining_vars = self._extract_variables(result)
            if remaining_vars:
                logger.warning(
                    f"Prompt template has unsubstituted variables: {remaining_vars}. "
                    f"These will remain as-is in the output."
                )
            
            return result
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            raise
    
    def build_strict(self, **kwargs) -> str:
        """
        Build the prompt with strict validation - raises error if variables are missing.
        
        Args:
            **kwargs: Variable values to substitute into template
            
        Returns:
            Rendered prompt string with all variables substituted
            
        Raises:
            KeyError: If required variables are missing
        """
        # Check for missing variables
        missing_vars = [var for var in self._variables if var not in kwargs]
        if missing_vars:
            raise KeyError(
                f"Missing required variables for prompt template: {missing_vars}. "
                f"Provided variables: {list(kwargs.keys())}"
            )
        
        # Use substitute (not safe_substitute) to raise error on missing vars
        return self._template_obj.substitute(**kwargs)


def buildStructuredPrompt(
    template: str,
    feedback_data: Optional[str] = None,
    platform_name: Optional[str] = None,
    tag_field: Optional[str] = None,
    project_name: Optional[str] = None,
    issue_type_list: Optional[str] = None,
    **extra_vars
) -> str:
    """
    Convenience function to build a structured prompt from a template.
    
    This function handles common prompt variables and provides a simple interface
    for building prompts using structured template syntax.
    
    Args:
        template: Template string with $variable placeholders
        feedback_data: Feedback comments/data to inject
        platform_name: Platform name like "Azure DevOps" or "Jira"
        tag_field: Field name for tags like "tags" or "labels"
        project_name: Project name for Jira/Azure DevOps
        issue_type_list: Comma-separated list of issue types
        **extra_vars: Additional variables to pass to template
        
    Returns:
        Rendered prompt string
        
    Example:
        template = "Analyze: $feedback_data for $platform_name"
        prompt = buildStructuredPrompt(
            template=template,
            feedback_data="User comments here",
            platform_name="Azure DevOps"
        )
    """
    # Build context dictionary from provided arguments
    context = {}
    
    if feedback_data is not None:
        context['feedback_data'] = feedback_data
    if platform_name is not None:
        context['platform_name'] = platform_name
    if tag_field is not None:
        context['tag_field'] = tag_field
    if project_name is not None:
        context['project_name'] = project_name
    if issue_type_list is not None:
        context['issue_type_list'] = issue_type_list
    
    # Add any extra variables
    context.update(extra_vars)
    
    # Build prompt using PromptBuilder
    builder = PromptBuilder(template)
    return builder.build(**context)

