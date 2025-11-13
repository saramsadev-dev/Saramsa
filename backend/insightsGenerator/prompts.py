import json

MY_CLIENT = "Some Website"
Features = "features"
def getSentAnalysisPrompt():
    return f"""You are a program manager analysing customer feedback for {MY_CLIENT}.
        Analyze the following feedback:\n <feedback_data>\n
        Generate a **summary report** in JSON format with the following key insights from my client's point of view:

        1. **Overall sentiment**: Provide the positive, negative, and neutral percentages for the client's feedback.
        2. **Feature-based sentiment analysis**: 
            - Classify the feedback into the following features: {Features}. 
            - Provide the overall sentiment for each feature, for example, "product quality: 70% positive, 20% negative, 10% neutral".
            - Include a concise description for each feature summarizing what users say.
            - Include feature-specific keywords that align with that feature.
            - Include the count of comments that mention each feature.
        3. **Consolidated keywords for wordclouds**: 
            - List the most common **positive** and **negative** keywords that represent feedback for the features. These will be used for word clouds.
        
        Structure the output as:
        {{
        "counts": {{"total": n, "positive":n, "negative":n, "neutral":n}},
        "sentiment_summary": {{ "positive": X%, "negative": Y%, "neutral": Z% }},
        "feature_asba": [
            {{ "feature": "product quality", "description": "Short summary of what users say about product quality.", "sentiment": {{ "positive": 60%, "negative": 20%, "neutral": 20% }}, "keywords" : ["durable", "fragile", "build quality"], "comment_count": 15 }},
            {{ "feature": "customer service", "description": "Short summary of what users say about support.", "sentiment": {{ "positive": 43%, "negative": 40%, "neutral": 17% }}, "keywords" : ["response time", "SLA", "helpful"], "comment_count": 12 }},
            {{ "feature": "pricing", "description": "Short summary of what users say about pricing.", "sentiment": {{ "positive": 30%, "negative": 60%, "neutral": 10% }}, "keywords" : ["expensive", "value", "discount"], "comment_count": 8 }}
        ],
        "positive_keywords": [
            {{ "keyword": "quality", "sentiment": 0.8 }},
            {{ "keyword": "service", "sentiment": 0.6 }}
        ],
        "negative_keywords": [
            {{ "keyword": "delay", "sentiment": 0.9 }},
            {{ "keyword": "expensive", "sentiment": 0.7 }}
        ]
        }}
        
        **Important**: Use "comment_count" (with underscore) as the field name for the number of comments per feature.
"""

def getDeepAnalysisPrompt():
    return f"""
You are a product program manager reviewing customer feedback for {MY_CLIENT}. Based on the feedback data provided, extract detailed, actionable insights to help the development team prioritize improvements.

<feedback_data>

Your job is to:
1. Analyze the feedback to identify specific issues, feature requests, and improvements needed
2. Create work items that can be directly imported into Azure DevOps based on the project template
3. Categorize items appropriately based on their nature (bugs, features, tasks, etc.)

Return the output in the following structured JSON format:

{{
  "work_items": [
    {{
      "type": "bug|feature|task|change",
      "title": "Clear, actionable title",
      "description": "Detailed description of the work item (2-4 sentences)",
      "priority": "critical|high|medium|low",
      "tags": ["tag1", "tag2", "tag3"],
      "acceptance_criteria": "What needs to be done to complete this item",
      "business_value": "Why this item is important",
      "effort_estimate": "Story points or time estimate",
      "feature_area": "Which feature this relates to"
    }}
  ],
  "summary": {{
    "total_items": 10,
    "by_type": {{
      "Bug": 3,
      "Feature": 4,
      "Task": 2,
      "Epic": 1
    }},
    "by_priority": {{
      "critical": 2,
      "high": 4,
      "medium": 3,
      "low": 1
    }}
  }}
}}

Guidelines for work item creation:
- bug: Something that's broken or not working as expected
- feature: New functionality that users are requesting
- task: General work that needs to be done
- change: Enhancements to existing features or improvements

Priority guidelines:
- critical: System-breaking issues, security vulnerabilities
- high: Major user-impacting issues, core features
- medium: Important improvements, nice-to-have features
- low: Minor improvements, documentation updates

Only return valid JSON with no explanation or commentary.
"""

def getJiraDeepAnalysisPrompt():
    return f"""
You are a product program manager reviewing customer feedback for {MY_CLIENT}. Based on the feedback data provided, extract detailed, actionable insights to help the development team prioritize improvements.

<feedback_data>

Your job is to:
1. Analyze the feedback to identify specific issues, feature requests, and improvements needed
2. Create work items that can be directly imported into Jira based on the available issue types
3. Categorize items appropriately based on their nature (bugs, features, tasks, epics, etc.)

Return the output in the following structured JSON format:

{{
  "work_items": [
    {{
      "type": "bug|task|feature|change",
      "title": "Clear, actionable title",
      "description": "Detailed description of the work item (2-4 sentences)",
      "priority": "critical|high|medium|low",
      "labels": ["tag1", "tag2", "tag3"],
      "acceptance_criteria": "What needs to be done to complete this item",
      "business_value": "Why this item is important",
      "effort_estimate": "Story points or time estimate",
      "feature_area": "Which feature this relates to"
    }}
  ],
  "summary": {{
    "total_items": 10,
    "by_type": {{
      "bug": 3,
      "task": 4,
      "feature": 2,
      "change": 1
    }},
    "by_priority": {{
      "critical": 2,
      "high": 4,
      "medium": 3,
      "low": 1
    }}
  }}
}}

Guidelines for work item creation:
- bug: Something that's broken or not working as expected
- task: General work that needs to be done
- feature: New functionality that users are requesting
- change: Enhancements to existing features or improvements

Priority guidelines:
- critical: System-breaking issues, security vulnerabilities
- high: Major user-impacting issues, core features
- medium: Important improvements, nice-to-have features
- low: Minor improvements, documentation updates

Only return valid JSON with no explanation or commentary.
"""


# Explicit map of allowed work item types per Azure DevOps process template
WORK_ITEM_TYPES_BY_TEMPLATE = {
    "Agile": ["Epic", "Feature", "User Story", "Task", "Bug"],
    "Scrum": ["Epic", "Feature", "Product Backlog Item", "Task", "Bug"],
    "Basic": ["Epic", "Issue", "Task"],
    "CMMI": ["Epic", "Feature", "Requirement", "Task", "Bug"],
}


def getGeneralAnalysisPrompt():
    return f"""
You are a product analyst reviewing customer feedback for {MY_CLIENT}.

<feedback_data>

Analyze the feedback and return STRICT JSON capturing:
- A list of features with: name, count of mentions, a concise description, and sentiment breakdown (positive/negative/neutral percentages) per feature
- Overall sentiment percentages across all feedback

JSON OUTPUT SHAPE (no extra keys, no commentary):
{{
  "overall": {{ "positive": X%, "negative": Y%, "neutral": Z% }},
  "features": [
    {{
      "name": "Feature name",
      "count": 12,
      "description": "1-2 sentence summary of what users say",
      "sentiment": {{ "positive": A%, "negative": B%, "neutral": C% }}
    }}
  ]
}}
"""


def getWorkItemCreationPrompt(process_template: str):
    allowed_types = WORK_ITEM_TYPES_BY_TEMPLATE.get(process_template, WORK_ITEM_TYPES_BY_TEMPLATE.get("Agile"))
    # Join allowed types as comma-separated for instruction clarity
    allowed_types_text = ", ".join(allowed_types)
    return f"""
You are generating Azure DevOps work items for a project using the "{process_template}" process template.
Use ONLY valid work item types for this template: {allowed_types_text}.

Rules:
- Choose the most appropriate work item type per item based on the described need
- Titles must be clear and actionable
- Descriptions should be concise (2-4 sentences) and self-contained
- Priority must be one of: critical, high, medium, low
- Tags: a short comma-separated list (e.g., feature area, platform)

Return STRICT JSON with an array named "items". Do not include commentary.
JSON OUTPUT SHAPE:
{{
  "items": [
    {{
      "type": "One of: {allowed_types_text}",
      "title": "...",
      "description": "...",
      "priority": "critical|high|medium|low",
      "tags": ["tag1", "tag2"]
    }}
  ]
}}
"""

def getWorkItemsFromAnalysisPrompt(process_template: str, analysis_data: dict):
    allowed_types = WORK_ITEM_TYPES_BY_TEMPLATE.get(process_template, WORK_ITEM_TYPES_BY_TEMPLATE.get("Agile"))
    allowed_types_text = ", ".join(allowed_types)
    
    return f"""
You are a product manager creating Azure DevOps work items based on customer feedback analysis.

PROJECT TEMPLATE: {process_template}
ALLOWED WORK ITEM TYPES: {allowed_types_text}

ANALYSIS DATA:
{json.dumps(analysis_data, indent=2)}

Based on this analysis, create work items that address the identified issues and feature requests. Follow these guidelines:

WORK ITEM TYPE MAPPING:
- BUG: Issues that are broken or not working correctly
- FEATURE: New functionality requested by users
- TASK: General work items, improvements, or technical debt
- EPIC: Large initiatives that contain multiple related items
- USER STORY: User-focused features (Agile template)
- PRODUCT BACKLOG ITEM: User-focused features (Scrum template)
- ISSUE: General problems or improvements (Basic template)
- REQUIREMENT: Detailed specifications (CMMI template)

PRIORITY GUIDELINES:
- CRITICAL: System-breaking issues, security vulnerabilities, major user blockers
- HIGH: Significant user impact, core feature issues
- MEDIUM: Important improvements, user experience enhancements
- LOW: Nice-to-have features, minor improvements

You MUST return a valid JSON object with this EXACT structure:
{{
  "work_items": [
    {{
      "type": "One of: {allowed_types_text}",
      "title": "Clear, actionable title",
      "description": "Detailed description explaining the issue or request",
      "priority": "critical|high|medium|low",
      "tags": ["feature-area", "platform", "user-impact"],
      "acceptance_criteria": "What needs to be completed to mark this as done",
      "business_value": "Why this work item is important",
      "effort_estimate": "Story points (1-13) or time estimate",
      "feature_area": "Which feature this relates to from the analysis"
    }}
  ],
  "summary": {{
    "total_items": 0,
    "by_type": {{}},
    "by_priority": {{}},
    "by_feature_area": {{}}
  }}
}}

IMPORTANT: 
1. Focus on creating actionable, specific work items that directly address the feedback analysis
2. Create at least 3-5 work items based on the most critical issues
3. Ensure each work item has a clear title, description, and priority
4. Return ONLY valid JSON - no explanations or commentary
5. Make sure the JSON structure matches exactly what is shown above
"""

def getDynamicJiraDeepAnalysisPrompt(project_metadata):
    """
    Generate a dynamic Jira deep analysis prompt based on project metadata.
    
    Args:
        project_metadata (dict): Contains project info and available issue types
            {
                'project': {
                    'name': str,
                    'key': str,
                    'style': 'classic' | 'next-gen',
                    'isCompanyManaged': bool,
                    'isTeamManaged': bool
                },
                'issue_types': [
                    {'name': str, 'description': str, 'hierarchyLevel': int}
                ],
                'available_issue_type_names': [str]
            }
    """
    project = project_metadata.get('project', {})
    available_issue_types = project_metadata.get('available_issue_type_names', [])
    
    # Determine management style and adjust prompt accordingly
    is_company_managed = project.get('isCompanyManaged', False)
    is_team_managed = project.get('isTeamManaged', False)
    project_name = project.get('name', 'Unknown Project')
    
    # Build issue type list for the prompt
    issue_type_list = ', '.join(available_issue_types) if available_issue_types else 'Task, Bug, Story'
    
    # Adjust prompt based on management style
    if is_company_managed:
        management_style_note = f"""
This is a **Company-managed** Jira project ({project_name}) with full workflow and custom field support.
You can use advanced features like Epic linking, custom fields, and detailed acceptance criteria.
"""
        additional_fields = """
- **Epic Link**: If this is part of a larger initiative, specify the epic
- **Custom Fields**: Include any relevant custom field data
- **Detailed Acceptance Criteria**: Provide comprehensive acceptance criteria
- **Business Value**: Explain the business impact and value
"""
    elif is_team_managed:
        management_style_note = f"""
This is a **Team-managed** Jira project ({project_name}) with simplified workflows.
Keep issue descriptions concise and focus on essential information only.
"""
        additional_fields = """
- **Simple Acceptance Criteria**: Keep criteria concise and actionable
- **Basic Business Value**: Brief explanation of why this matters
"""
    else:
        management_style_note = f"""
This is a Jira project ({project_name}) with standard configuration.
Use standard Jira fields and keep descriptions clear and actionable.
"""
        additional_fields = """
- **Acceptance Criteria**: Clear, testable criteria for completion
- **Business Value**: Why this work item is important
"""

    return f"""
You are a product program manager reviewing customer feedback for {MY_CLIENT}. Based on the feedback data provided, extract detailed, actionable insights to help the development team prioritize improvements.

<feedback_data>

{management_style_note}

Your job is to:
1. Analyze the feedback to identify specific issues, feature requests, and improvements needed
2. Create work items that can be directly imported into the Jira project: **{project_name}**
3. Use ONLY the available issue types for this project: **{issue_type_list}**
4. Categorize items appropriately based on their nature and the available issue types

Return the output in the following structured JSON format:

{{
  "work_items": [
    {{
      "type": "{issue_type_list}",
      "title": "Clear, actionable title",
      "description": "Detailed description of the work item (2-4 sentences)",
      "priority": "critical|high|medium|low",
      "labels": ["tag1", "tag2", "tag3"],
      "acceptance_criteria": "What needs to be done to complete this item",
      "business_value": "Why this item is important",
      "effort_estimate": "Story points or time estimate",
      "feature_area": "Which feature this relates to"
    }}
  ],
  "summary": {{
    "total_items": 10,
    "by_type": {{
      "bug": 3,
      "task": 4,
      "feature": 2,
      "change": 1
    }},
    "by_priority": {{
      "critical": 2,
      "high": 4,
      "medium": 3,
      "low": 1
    }}
  }}
}}

**IMPORTANT GUIDELINES:**

**Available Issue Types for {project_name}:**
{chr(10).join([f"- {it}" for it in available_issue_types])}

**Issue Type Guidelines:**
- Use ONLY the issue types listed above
- If "Bug" is available: Use for broken functionality, errors, or defects
- If "Task" is available: Use for general work, improvements, or technical debt
- If "Story" is available: Use for user-focused features or requirements
- If "Epic" is available: Use for large initiatives that contain multiple features
- If "Feature" is available: Use for new functionality requests
- If "Improvement" is available: Use for enhancements to existing features

**Priority Guidelines:**
- **CRITICAL**: System-breaking issues, security vulnerabilities, major outages
- **HIGH**: Major user-impacting issues, core features, significant bugs
- **MEDIUM**: Important improvements, nice-to-have features, minor bugs
- **LOW**: Minor improvements, documentation updates, cosmetic changes

**Additional Fields to Include:**
{additional_fields}

**Project-Specific Notes:**
- Project Name: {project_name}
- Management Style: {'Company-managed' if is_company_managed else 'Team-managed' if is_team_managed else 'Standard'}
- Available Issue Types: {issue_type_list}

Only return valid JSON with no explanation or commentary.
"""