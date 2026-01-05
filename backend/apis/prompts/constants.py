"""
AI Prompts Configuration

This module contains all AI prompts used throughout the application.
Centralized from the root prompts.py file for better organization.

Structure:
- PROMPTS: Main dictionary containing all prompts
- Each company can have its own prompts, with 'default' as fallback
- Each prompt type (sentiment, deep_analysis) is a separate key
- Use $variable syntax for template variables (e.g., $feedback_data, $platform_name)
"""

PROMPTS = {
    "default": {
        "sentiment": """You are a program manager analysing customer feedback for Some Website.
        Analyze the following feedback:
        $feedback_data
        
        Generate a **summary report** in JSON format with the following key insights from my client's point of view:

        1. **Overall sentiment**: Provide the positive, negative, and neutral percentages for the client's feedback.
        2. **Feature-based sentiment analysis**: 
            - Classify the feedback into the following features: features. 
            - Provide the overall sentiment for each feature, for example, "product quality: 70% positive, 20% negative, 10% neutral".
            - Include a concise description for each feature summarizing what users say.
            - Include feature-specific keywords that align with that feature.
            - Include the count of comments that mention each feature.
        3. **Consolidated keywords for wordclouds**: 
            - List the most common **positive** and **negative** keywords that represent feedback for the features. These will be used for word clouds.
        
        Structure the output as:
        {
            "counts": {"total": n, "positive": n, "negative": n, "neutral": n},
            "sentiment_summary": {"positive": "X%", "negative": "Y%", "neutral": "Z%"},
            "feature_asba": [
                {
                    "feature": "product quality", 
                    "description": "Short summary of what users say about product quality.", 
                    "sentiment": {"positive": "60%", "negative": "20%", "neutral": "20%"}, 
                    "keywords": ["durable", "fragile", "build quality"], 
                    "comment_count": 15
                },
                {
                    "feature": "customer service", 
                    "description": "Short summary of what users say about support.", 
                    "sentiment": {"positive": "43%", "negative": "40%", "neutral": "17%"}, 
                    "keywords": ["response time", "SLA", "helpful"], 
                    "comment_count": 12
                },
                {
                    "feature": "pricing", 
                    "description": "Short summary of what users say about pricing.", 
                    "sentiment": {"positive": "30%", "negative": "60%", "neutral": "10%"}, 
                    "keywords": ["expensive", "value", "discount"], 
                    "comment_count": 8
                }
            ],
            "positive_keywords": [
                {"keyword": "quality", "sentiment": 0.8},
                {"keyword": "service", "sentiment": 0.6}
            ],
            "negative_keywords": [
                {"keyword": "delay", "sentiment": 0.9},
                {"keyword": "expensive", "sentiment": 0.7}
            ]
        }
        
        **Important**: Use "comment_count" (with underscore) as the field name for the number of comments per feature.""",

        "deep_analysis": """You are a product program manager reviewing customer feedback for Some Website. Based on the feedback data provided, extract detailed, actionable insights to help the development team prioritize improvements.

$feedback_data

Your job is to:
1. Analyze the feedback to identify specific issues, feature requests, and improvements needed
2. Create work items that can be directly imported into $platform_name based on the available issue types
3. Categorize items appropriately based on their nature (bug, task, feature, change, etc.)

Return the output in the following structured JSON format:

{
  "work_items": [
    {
      "type": "bug|task|feature|change|epic|story",
      "title": "Clear, actionable title",
      "description": "Detailed description of the work item (2-4 sentences)",
      "priority": "critical|high|medium|low",
      "$tag_field": ["tag1", "tag2", "tag3"],
      "acceptance_criteria": "What needs to be done to complete this item",
      "business_value": "Why this item is important",
      "effort_estimate": "Story points or time estimate",
      "feature_area": "Which feature this relates to"
    }
  ],
  "summary": {
    "total_items": 10,
    "by_type": {
      "bug": 3,
      "task": 4,
      "feature": 2,
      "change": 1
    },
    "by_priority": {
      "critical": 2,
      "high": 4,
      "medium": 3,
      "low": 1
    }
  }
}

Guidelines for work item creation:
- bug: Something that's broken or not working as expected
- feature: New functionality that users are requesting
- task: General work that needs to be done
- change: Enhancements to existing features or improvements
- epic: Large initiatives that contain multiple related items
- story: User-focused features or requirements

Priority guidelines:
- critical: System-breaking issues, security vulnerabilities
- high: Major user-impacting issues, core features
- medium: Important improvements, nice-to-have features
- low: Minor improvements, documentation updates

Only return valid JSON with no explanation or commentary."""
    }
}


def get_prompt(company_name=None, prompt_type="sentiment"):
    """
    Get a prompt template for the specified company and type.
    
    Args:
        company_name (str, optional): Company name to look up. Defaults to None.
        prompt_type (str): Type of prompt ('sentiment' or 'deep_analysis'). Defaults to 'sentiment'.
        
    Returns:
        str: The prompt template string
        
    Raises:
        ValueError: If the prompt is not found
    """
    # Try company-specific prompt first
    if company_name and company_name in PROMPTS:
        company_prompts = PROMPTS.get(company_name, {})
        if prompt_type in company_prompts:
            return company_prompts[prompt_type]
    
    # Fallback to default
    default_prompts = PROMPTS.get('default', {})
    if prompt_type in default_prompts:
        return default_prompts[prompt_type]
    
    # If not found, raise error
    error_msg = f"Prompt '{prompt_type}' not found"
    if company_name:
        error_msg += f" for company '{company_name}'"
    error_msg += ". Available prompts: " + ", ".join(default_prompts.keys())
    raise ValueError(error_msg)


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