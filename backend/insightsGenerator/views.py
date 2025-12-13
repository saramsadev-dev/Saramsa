from rest_framework.views import APIView
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .prompts import (
    getSentAnalysisPrompt,
    WORK_ITEM_TYPES_BY_TEMPLATE,
    getDeepAnalysisPrompt,
)
import json
from aiCore.aiCompletions import *
from aiCore.cosmos_service import cosmos_service
from asgiref.sync import async_to_sync
from datetime import datetime
import uuid
from authapp.permissions import IsAdmin, IsAdminOrUser
from apis.usage_logging import log_token_usage
from apis.response import StandardResponse
import logging

app_logger = logging.getLogger("apis.app")

class AnalyzeCommentsView(APIView):
    permission_classes = [IsAdminOrUser]
    
    @async_to_sync
    async def post(self, request):
        print("📈 AnalyzeCommentsView called")
        print("📦 Request data:", request.data)
        
        comments = request.data.get("comments")
        incoming_project_id = request.data.get("project_id")

        print(f"💬 Comments count: {len(comments) if comments else 0}")
        print(f"🆔 Project ID (incoming): {incoming_project_id}")

        if not comments or not isinstance(comments, list):
            print("❌ Invalid comments data")
            return StandardResponse.validation_error(
                detail="A list of comments is required.",
                errors=[{"field": "comments", "message": "This field must be a list."}],
                instance=request.path
            )

        # Get file name and user info for later use
        file_name = request.data.get("file_name", "uploaded_file")
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else "anonymous"
        user_id_str = str(user_id)
        
        # Get company name from user profile for company-specific prompts
        company_name = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_data = cosmos_service.get_user_by_username(request.user.username)
                if user_data:
                    company_name = user_data.get('company_name')
            except Exception as e:
                print(f"Warning: Could not get company_name for user: {e}")

        project_id, project_document, is_draft_project = cosmos_service.ensure_project_context(
            incoming_project_id,
            user_id_str,
        )
        storage_project_id = project_id
        is_personal_analysis = is_draft_project
        project_status = project_document.get("status", "draft" if is_personal_analysis else "active")
        project_config_state = project_document.get("config_state", "unconfigured" if is_personal_analysis else "complete")
        
        try:
            prompt = getSentAnalysisPrompt(company_name=company_name)
            feedback_block = "\n".join([str(c) for c in comments])
            prompt_filled = prompt.replace("<feedback_data>", feedback_block)
            result = await generate_completions(prompt_filled)

            # Normalize the LLM output into the expected schema
            try:
                parsed = json.loads(result) if isinstance(result, str) else (result or {})
            except Exception:
                parsed = {}

            sentiments = parsed.get('sentimentsummary') or parsed.get('sentiment_summary') or {}
            counts = parsed.get('counts') or {}
            features_input = parsed.get('feature_asba') or parsed.get('featureasba') or []
            pos_keys = parsed.get('positive_keywords') or parsed.get('positivekeywords') or []
            neg_keys = parsed.get('negative_keywords') or parsed.get('negativekeywords') or []

            def to_num(v):
                try:
                    return float(v)
                except Exception:
                    try:
                        return int(v)
                    except Exception:
                        return 0

            features_norm = []
            for f in features_input:
                if not isinstance(f, dict):
                    continue
                name = f.get('feature') or f.get('name')
                if not name:
                    continue
                sent = f.get('sentiment') or {}
                features_norm.append({
                    'name': name,
                    'description': f.get('description') or '',
                    'sentiment': {
                        'positive': to_num(sent.get('positive')),
                        'negative': to_num(sent.get('negative')),
                        'neutral': to_num(sent.get('neutral')),
                    },
                    'keywords': f.get('keywords') or [],
                    'comment_count': to_num(f.get('comment_count') or f.get('commentcount') or 0)
                })

            normalized = {
                'overall': {
                    'positive': to_num(sentiments.get('positive')),
                    'negative': to_num(sentiments.get('negative')),
                    'neutral': to_num(sentiments.get('neutral')),
                },
                'counts': {
                    'total': to_num(counts.get('total')),
                    'positive': to_num(counts.get('positive')),
                    'negative': to_num(counts.get('negative')),
                    'neutral': to_num(counts.get('neutral')),
                },
                'features': features_norm,
                'positive_keywords': pos_keys,
                'negative_keywords': neg_keys,
            }
            # If token usage was captured by the LLM layer, a token_usage event will exist.
            # Log a high-level custom event for this API.
            try:
                app_logger.info(
                    "analysis_generated",
                    extra={
                        "event": "analysis_generated",
                        "analysis_type": "sentiment_analysis",
                        "comments_count": len(comments),
                    },
                )
            except Exception:
                pass
            
            # Create insight data for Cosmos DB
            insight_id = str(uuid.uuid4())
            insight_data = {
                'id': f'insight_{insight_id}',
                'type': 'insight',
                'analysis_type': 'sentiment_analysis',
                'comments_count': len(comments),
                'analysis_date': datetime.now().isoformat(),
                # Save normalized for fast retrieval
                **normalized,
                # Keep raw for traceability
                'raw_llm': {
                    'comment': result,
                },
                'metadata': {
                    'source': 'api_request',
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'request_timestamp': datetime.now().isoformat(),
                    'is_personal': is_personal_analysis,
                },
                'projectId': storage_project_id,
                'is_personal': is_personal_analysis,
                'userId': user_id_str,
            }
            
            # Save to analysis container
            try:
                saved_analysis = cosmos_service.save_analysis_data(insight_data)
                if saved_analysis:
                    insight_data['cosmos_id'] = saved_analysis.get('id')
            except Exception as e:
                print(f"Error saving analysis to Cosmos DB: {e}")
            
            # Store user feedback data in user_data container after successful analysis
            if comments:
                user_data_record = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id_str,
                    "project_id": storage_project_id,
                    "feedback": comments,
                    "uploaded_date": datetime.now().isoformat(),
                    "file_name": file_name,
                    "is_personal": is_personal_analysis,
                    "tenant_id": project_document.get("tenant_id", "default"),
                }
                
                try:
                    saved_user_data = cosmos_service.save_user_data(user_data_record)
                    if saved_user_data:
                        print(f"✅ Successfully saved user data: {len(comments)} comments for user {user_id_str}, project {storage_project_id}")
                    else:
                        print("⚠️ Failed to save user data to Cosmos DB")
                except Exception as e:
                    print(f"❌ Error saving user data: {e}")
                    # Don't fail the analysis if user data storage fails
            
            # If project_id is provided, also save to analysis container
            if storage_project_id:
                try:
                    # Get existing analysis data to aggregate with new data
                    existing_analysis = None
                    try:
                        existing_analysis = cosmos_service.get_latest_analysis_for_project(storage_project_id)
                        if existing_analysis:
                            print(f"📊 Found existing analysis for project {storage_project_id}")
                    except Exception as e:
                        print(f"⚠️ No existing analysis found for project {storage_project_id}: {e}")
                    
                    # Aggregate data if existing analysis exists
                    if existing_analysis:
                        print("🔄 Aggregating with existing analysis data...")
                        aggregated_data = aggregate_analysis_data(existing_analysis, normalized, len(comments))
                    else:
                        print("🆕 Creating new analysis data...")
                        aggregated_data = normalized
                        # Add total comments count to the new data
                        aggregated_data['total_comments_analyzed'] = len(comments)
                    
                    analysis_id = str(uuid.uuid4())
                    analysis_data = {
                        'id': f'analysis_{analysis_id}',
                        'projectId': storage_project_id,
                        'userId': user_id_str,
                        'createdAt': datetime.now().isoformat(),
                        'analysisType': 'commentSentiment',
                        'rawLlm': result,
                        'analysisData': {
                            'overall': aggregated_data['overall'],
                            'counts': aggregated_data['counts'],
                            'features': aggregated_data['features'],
                            'positive_keywords': aggregated_data['positive_keywords'],
                            'negative_keywords': aggregated_data['negative_keywords']
                        },
                        'metadata': {
                            'is_personal': is_personal_analysis,
                            'source_project_id': incoming_project_id,
                            'owner_user_id': user_id_str,
                        }
                    }
                    
                    saved_analysis = cosmos_service.save_analysis_data(analysis_data)
                    if saved_analysis:
                        # Update project's last_analysis_id
                        if project_id:
                            cosmos_service.update_project_last_analysis(project_id, saved_analysis['id'])
                except Exception as e:
                    print(f"Error saving analysis to Cosmos DB: {e}")
            
            # Use aggregated data if available, otherwise use normalized data
            response_data = aggregated_data if storage_project_id and 'aggregated_data' in locals() else normalized
            
            # Format response in the new structure only
            formatted = {
                'success': True,
                'id': f'analysis_{insight_id}',
                'projectId': storage_project_id,
                'userId': user_id_str,
                'createdAt': datetime.now().isoformat(),
                'analysisType': 'commentSentiment',
                'rawLlm': result,
                'analysisData': {
                    'overall': response_data['overall'],
                    'counts': response_data['counts'],
                    'features': response_data['features'],
                    'positive_keywords': response_data['positive_keywords'],
                    'negative_keywords': response_data['negative_keywords']
                },
                'isPersonal': is_personal_analysis,
                'sourceProjectId': incoming_project_id,
                'context': {
                    'project_id': storage_project_id,
                    'project_status': project_status,
                    'config_state': project_config_state,
                    'is_draft': is_personal_analysis,
                }
            }
            
            return StandardResponse.success(data=formatted, message="Operation completed successfully")
        except Exception as e:
            print (str(e))
            error_response = {
                "error": str(e),
                "details": "Failed to analyze comments",
                "code": "analysis_error"
            }
            return StandardResponse.internal_server_error(detail=error_response.get("error", "Internal server error"), instance=request.path)

class InsightsListView(APIView):
    """Get all insights from Cosmos DB"""
    permission_classes = [IsAdmin]
    
    def get(self, request):
        try:
            # Get all insights from Cosmos DB
            insights = cosmos_service.query_items("insights", "SELECT * FROM c WHERE c.type = 'insight' ORDER BY c.analysis_date DESC")
            
            return StandardResponse.success(data={
                "insights": insights,
                "count": len(insights)
            }, message="Operation completed successfully")
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch insights: {str(e)}",
                instance=request.path
            )

class InsightDetailView(APIView):
    """Get specific insight by ID from Cosmos DB"""
    permission_classes = [IsAdmin]
    
    def get(self, request, insight_id):
        try:
            insight_data = cosmos_service.get_insight(insight_id)
            if not insight_data:
                return StandardResponse.not_found(detail="Insight not found"
                , instance=request.path)
            
            return StandardResponse.success(data=insight_data, message="Operation completed successfully")
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch insight: {str(e)}",
                instance=request.path
            )

class InsightsByTypeView(APIView):
    """Get insights by analysis type"""
    permission_classes = [IsAdmin]
    
    def get(self, request, analysis_type):
        try:
            # Query insights by analysis type
            insights = cosmos_service.query_items(
                "insights", 
                "SELECT * FROM c WHERE c.type = 'insight' AND c.analysis_type = @analysis_type ORDER BY c.analysis_date DESC",
                [{"name": "@analysis_type", "value": analysis_type}]
            )
            
            return StandardResponse.success(data={
                "insights": insights,
                "count": len(insights),
                "analysis_type": analysis_type
            }, message="Operation completed successfully")
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch insights: {str(e)}",
                instance=request.path
            )


class GetWorkItemsView(APIView):
    """Retrieve work items for a specific project"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        """
        Get work items for a specific project
        """
        project_id = request.query_params.get("project_id")
        
        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)
        
        try:
            # Get work items from Cosmos DB - check both work_items and deep_analysis types
            work_items_data = cosmos_service.get_work_items_by_project(project_id)
            deep_analysis_data = cosmos_service.get_deep_analysis_by_project(project_id)
            
            # Combine both types of data
            all_data = []
            if work_items_data:
                all_data.extend(work_items_data)
            if deep_analysis_data:
                all_data.extend(deep_analysis_data)
            
            if not all_data:
                return StandardResponse.success(
                    data={
                        "work_items": [],
                    "work_items_by_feature": {},
                    "summary": {},
                    "message": "No work items found for this project"
                }, status=status.HTTP_200_OK)
            
            # Return the most recent work items data
            latest_data = all_data[-1] if isinstance(all_data, list) else all_data
            
            work_items = latest_data.get('work_items', [])
            summary = latest_data.get('summary', {})
            
            return StandardResponse.success(data={
                "success": True,
                "work_items": work_items,
                "work_items_by_feature": groupWorkItemsByFeature(work_items),
                "summary": summary,
                "process_template": latest_data.get('process_template', 'Agile'),
                "generated_at": latest_data.get('generated_at'),
                "message": "Work items retrieved successfully"
            }, message="Operation completed successfully")
            
        except Exception as e:
            print(f"Error retrieving work items: {e}")
            return StandardResponse.internal_server_error(detail="Failed to retrieve work items.", instance=request.path)


class WorkItemsGenerationView(APIView):
    permission_classes = [IsAdminOrUser]
    
    @async_to_sync
    async def post(self, request):
        """
        Generate work items based on analysis data and template (Azure DevOps or Jira)
        """
        print("🔧 WorkItemsGenerationView called")
        print("📦 Request data:", request.data)
        
        analysis_data = request.data.get("analysis_data")
        process_template = request.data.get("process_template", "Agile")
        incoming_project_id = request.data.get("project_id")
        platform = request.data.get("platform", "azure")  # Default to Azure DevOps
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else "anonymous"
        user_id_str = str(user_id)

        resolved_project_id, project_doc, is_draft = cosmos_service.ensure_project_context(
            incoming_project_id,
            user_id_str,
        )
        project_id = resolved_project_id

        print(f"🏗️ Platform: {platform}")
        print(f"📋 Process template: {process_template}")
        print(f"🆔 Project ID (resolved): {project_id}")

        if not analysis_data:
            print("❌ No analysis data provided")
            return StandardResponse.validation_error(detail="Analysis data is required.", instance=request.path)

        try:
            # Create prompt for work item generation based on platform
            if platform.lower() == "jira":
                print("🔧 Using Jira-specific prompt")
                # For Jira, we need to get project metadata to create appropriate work items
                project_metadata = request.data.get("project_metadata")
                if project_metadata:
                    print("📊 Using project metadata for Jira prompt")
                    # Use the same Azure DevOps prompt but with Jira-specific instructions
                    prompt = getWorkItemsFromAnalysisPrompt(process_template, analysis_data)
                    # Add Jira-specific instructions to the prompt
                    jira_instructions = f"""
                    
IMPORTANT: This is for Jira integration. Please ensure:
1. Use Jira-compatible issue types: {', '.join(project_metadata.get('available_issue_type_names', ['Task', 'Bug', 'Story']))}
2. Use Jira field names: 'labels' instead of 'tags', 'acceptance_criteria' for acceptance criteria
3. Project: {project_metadata.get('project', {}).get('name', 'Unknown')}
4. Keep descriptions concise and actionable for Jira
"""
                    prompt += jira_instructions
                else:
                    print("⚠️ No project metadata, using fallback prompt")
                    # Fallback to Azure DevOps prompt for Jira
                    prompt = getWorkItemsFromAnalysisPrompt(process_template, analysis_data)
            else:
                print("🔧 Using Azure DevOps prompt")
                # Default Azure DevOps prompt
                prompt = getWorkItemsFromAnalysisPrompt(process_template, analysis_data)
            
            print(f"Work items generation prompt length: {len(prompt)} characters")
            print(f"Prompt preview: {prompt[:500]}...")
            
            # Generate work items using AI
            result = await generate_completions(prompt)
            
            print(f"Raw LLM result length: {len(str(result))} characters")
            print(f"Raw LLM result preview: {str(result)[:500]}...")

            # Parse the LLM response
            try:
                parsed = json.loads(result) if isinstance(result, str) else (result or {})
                print(f"Parsed result: {parsed}")
            except Exception as e:
                print(f"Error parsing work items response: {e}")
                print(f"Raw result that failed to parse: {result}")
                parsed = {"work_items": [], "summary": {}}

            # Validate and structure the response
            work_items = parsed.get("work_items", []) or parsed.get("workitems", [])
            summary = parsed.get("summary", {})
            
            print(f"Extracted work_items: {work_items}")
            print(f"Extracted summary: {summary}")

            # Fallback: If no work items were generated, create some based on the analysis
            if not work_items and analysis_data:
                print("No work items generated by LLM, creating fallback work items")
                work_items = createFallbackWorkItems(analysis_data, process_template)
                summary = {
                    "total_items": len(work_items),
                    "by_type": {},
                    "by_priority": {},
                    "by_feature_area": {}
                }

            # Add metadata to each work item
            for item in work_items:
                item["id"] = str(uuid.uuid4())
                item["created_at"] = datetime.now().isoformat()
                item["project_id"] = project_id
                item["process_template"] = process_template

            # Save to Cosmos DB if project_id is provided
            if project_id:
                try:
                    work_items_data = {
                        'id': f'work_items_{uuid.uuid4()}',
                        'type': 'work_items',
                        'project_id': project_id,
                        'process_template': process_template,
                        'generated_at': datetime.now().isoformat(),
                        'work_items': work_items,
                        'summary': summary,
                        'analysis_data': analysis_data
                    }
                    
                    # Work items are now saved directly to user_stories container
                    pass
                except Exception as e:
                    print(f"Error saving work items to Cosmos DB: {e}")

            # Format response
            formatted = {
                'success': True,
                'work_items': work_items,
                'work_items_by_feature': groupWorkItemsByFeature(work_items),
                'summary': summary,
                'process_template': process_template,
                'generated_at': datetime.now().isoformat(),
                'context': {
                    'project_id': project_id,
                    'project_status': project_doc.get("status", "draft" if is_draft else "active"),
                    'config_state': project_doc.get("config_state", "unconfigured" if is_draft else "complete"),
                    'is_draft': is_draft,
                }
            }
            
            return StandardResponse.success(data=formatted, message="Operation completed successfully")
            
        except Exception as e:
            print(f"Error generating work items: {e}")
            error_response = {
                "error": str(e),
                "details": "Failed to generate work items",
                "code": "work_items_generation_error"
            }
            return StandardResponse.internal_server_error(detail=error_response.get("error", "Internal server error"), instance=request.path)


def createFallbackWorkItems(analysis_data: dict, process_template: str) -> list:
    """
    Create fallback work items based on analysis data when LLM fails to generate them
    """
    work_items = []
    
    # Get allowed work item types for the template
    allowed_types = WORK_ITEM_TYPES_BY_TEMPLATE.get(process_template, WORK_ITEM_TYPES_BY_TEMPLATE.get("Agile"))
    
    # Process features with negative sentiment
    # Try different possible keys for features
    features = []
    
    # Check if analysis_data has nested structure
    if isinstance(analysis_data, dict):
        # Try to get features from nested analysisData
        nested_data = analysis_data.get('analysisData', {})
        if isinstance(nested_data, dict):
            features = nested_data.get('features', []) or nested_data.get('featureasba', [])
        else:
            # Try direct keys
            features = analysis_data.get('features', []) or analysis_data.get('featureasba', [])
    
    print(f"🔧 Fallback: analysis_data keys: {list(analysis_data.keys()) if isinstance(analysis_data, dict) else 'Not a dict'}")
    print(f"🔧 Fallback: features found: {len(features)}")
    if features:
        print(f"🔧 Fallback: first feature example: {features[0] if features else 'None'}")
    
    for feature in features:
        feature_name = feature.get('name', 'Unknown Feature')
        sentiment = feature.get('sentiment', {})
        negative_percent = sentiment.get('negative', 0)
        description = feature.get('description', '')
        
        # Create work items for features with significant negative sentiment
        if negative_percent > 30:
            # Determine work item type based on template
            if process_template == 'Agile':
                work_item_type = 'User Story'
            elif process_template == 'Scrum':
                work_item_type = 'Product Backlog Item'
            elif process_template == 'Basic':
                work_item_type = 'Issue'
            elif process_template == 'CMMI':
                work_item_type = 'Requirement'
            else:
                work_item_type = 'Task'
            
            # Determine priority based on negative sentiment
            if negative_percent > 70:
                priority = 'high'
            elif negative_percent > 50:
                priority = 'medium'
            else:
                priority = 'low'
            
            work_item = {
                "type": work_item_type,
                "title": f"Improve {feature_name} based on customer feedback",
                "description": f"Address customer concerns about {feature_name.lower()}. {description}",
                "priority": priority,
                "tags": [feature_name.lower().replace(' ', '-'), "customer-feedback"],
                "acceptance_criteria": f"Customer satisfaction for {feature_name.lower()} improves based on feedback metrics",
                "business_value": f"Improve customer experience and reduce negative feedback for {feature_name.lower()}",
                "effort_estimate": "5",
                "feature_area": feature_name
            }
            
            work_items.append(work_item)
    
    # Add a general improvement work item if we have overall negative sentiment
    overall_sentiment = analysis_data.get('sentimentsummary', {})
    overall_negative = overall_sentiment.get('negative', 0)
    
    if overall_negative > 30 and len(work_items) < 3:
        work_item = {
            "type": "Task",
            "title": "Review and address overall customer feedback",
            "description": f"Overall customer sentiment shows {overall_negative}% negative feedback. Review all feedback and prioritize improvements.",
            "priority": "medium",
            "tags": ["customer-feedback", "improvement"],
            "acceptance_criteria": "Action plan created and prioritized based on customer feedback analysis",
            "business_value": "Improve overall customer satisfaction and reduce negative feedback",
            "effort_estimate": "8",
            "feature_area": "General"
        }
        work_items.append(work_item)
    
    return work_items

def groupWorkItemsByFeature(work_items: list) -> dict:
    """
    Groups work items by their 'feature_area' or 'featurearea' attribute.
    """
    grouped_items = {}
    for item in work_items:
        # Handle both 'feature_area' and 'featurearea' field names
        feature_area = item.get('feature_area') or item.get('featurearea') or 'General'
        if feature_area not in grouped_items:
            grouped_items[feature_area] = []
        grouped_items[feature_area].append(item)
    return grouped_items

class UpdateKeywordsView(APIView):
    permission_classes = [IsAdminOrUser]
    
    @async_to_sync
    async def post(self, request):
        """
        Update keywords for features and regenerate analysis
        """
        incoming_project_id = request.data.get("project_id")
        updated_keywords = request.data.get("updated_keywords", {})
        comments = request.data.get("comments", [])
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else "anonymous"
        user_id_str = str(user_id)

        if not updated_keywords or not comments:
            return StandardResponse.validation_error(detail="Updated keywords and comments are required.", instance=request.path)

        project_id, project_doc, is_draft = cosmos_service.ensure_project_context(
            incoming_project_id,
            user_id_str,
        )
        project_context = {
            'project_id': project_id,
            'project_status': project_doc.get("status", "draft" if is_draft else "active"),
            'config_state': project_doc.get("config_state", "unconfigured" if is_draft else "complete"),
            'is_draft': is_draft,
        }

        # Get company name from user profile for company-specific prompts
        company_name = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_data = cosmos_service.get_user_by_username(request.user.username)
                if user_data:
                    company_name = user_data.get('company_name')
            except Exception as e:
                print(f"Warning: Could not get company_name for user: {e}")
        
        try:
            # Create a modified prompt that includes the updated keywords
            prompt = getSentAnalysisPrompt(company_name=company_name)
            
            # Add keyword context to the prompt
            keyword_context = "UPDATED KEYWORDS:\n"
            for feature_name, keywords in updated_keywords.items():
                keyword_context += f"{feature_name}: {', '.join(keywords)}\n"
            
            prompt = prompt.replace("<feedback_data>", f"{keyword_context}\n\nFEEDBACK DATA:\n" + "\n".join([str(c) for c in comments]))
            
            result = await generate_completions(prompt)

            # Parse and normalize the result (same as AnalyzeCommentsView)
            try:
                parsed = json.loads(result) if isinstance(result, str) else (result or {})
            except Exception:
                parsed = {}

            sentiments = parsed.get('sentimentsummary') or parsed.get('sentiment_summary') or {}
            counts = parsed.get('counts') or {}
            features_input = parsed.get('feature_asba') or parsed.get('featureasba') or []
            pos_keys = parsed.get('positive_keywords') or parsed.get('positivekeywords') or []
            neg_keys = parsed.get('negative_keywords') or parsed.get('negativekeywords') or []

            def to_num(v):
                try:
                    return float(v)
                except Exception:
                    try:
                        return int(v)
                    except Exception:
                        return 0

            features_norm = []
            for f in features_input:
                if not isinstance(f, dict):
                    continue
                name = f.get('feature') or f.get('name')
                if not name:
                    continue
                sent = f.get('sentiment') or {}
                features_norm.append({
                    'name': name,
                    'description': f.get('description') or '',
                    'sentiment': {
                        'positive': to_num(sent.get('positive')),
                        'negative': to_num(sent.get('negative')),
                        'neutral': to_num(sent.get('neutral')),
                    },
                    'keywords': f.get('keywords') or [],
                    'comment_count': to_num(f.get('comment_count') or f.get('commentcount') or 0)
                })

            normalized = {
                'overall': {
                    'positive': to_num(sentiments.get('positive')),
                    'negative': to_num(sentiments.get('negative')),
                    'neutral': to_num(sentiments.get('neutral')),
                },
                'counts': {
                    'total': to_num(counts.get('total')),
                    'positive': to_num(counts.get('positive')),
                    'negative': to_num(counts.get('negative')),
                    'neutral': to_num(counts.get('neutral')),
                },
                'features': features_norm,
                'positive_keywords': pos_keys,
                'negative_keywords': neg_keys,
            }

            # Save updated analysis to Cosmos DB
            try:
                analysis_id = str(uuid.uuid4())
                analysis_data = {
                    'id': f'analysis_{analysis_id}',
                    'projectId': project_id,
                    'userId': user_id_str,
                    'createdAt': datetime.now().isoformat(),
                    'analysisType': 'commentSentiment',
                    'rawLlm': result,
                    'analysisData': {
                        'overall': normalized['overall'],
                        'counts': normalized['counts'],
                        'features': normalized['features'],
                        'positive_keywords': normalized['positive_keywords'],
                        'negative_keywords': normalized['negative_keywords']
                    }
                }
                
                saved_analysis = cosmos_service.save_analysis_data(analysis_data)
                if saved_analysis:
                    cosmos_service.update_project_last_analysis(project_id, saved_analysis['id'])
            except Exception as e:
                print(f"Error saving updated analysis to Cosmos DB: {e}")

            # Format response in the new structure only
            formatted = {
                'success': True,
                'id': f'analysis_{str(uuid.uuid4())}',
                'projectId': project_id if project_id else 'unknown',
                'userId': user_id_str,
                'createdAt': datetime.now().isoformat(),
                'analysisType': 'commentSentiment',
                'rawLlm': result,
                'analysisData': {
                    'overall': normalized['overall'],
                    'counts': normalized['counts'],
                    'features': normalized['features'],
                    'positive_keywords': normalized['positive_keywords'],
                    'negative_keywords': normalized['negative_keywords']
                },
                'context': project_context
            }
            
            return StandardResponse.success(data=formatted, message="Operation completed successfully")
            
        except Exception as e:
            print(f"Error updating keywords and regenerating analysis: {e}")
            error_response = {
                "error": str(e),
                "details": "Failed to update keywords and regenerate analysis",
                "code": "keywords_update_error"
            }
            return StandardResponse.internal_server_error(detail=error_response.get("error", "Internal server error"), instance=request.path)


class GetUserCommentsView(APIView):
    """Get user comments for regeneration"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        """
        Get user comments for a specific project
        """
        project_id = request.query_params.get('project_id')
        is_personal_param = request.query_params.get('is_personal')
        explicit_personal = str(is_personal_param).lower() in ('true', '1', 'yes')
        
        # Get user ID from request
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        if not user_id:
            return StandardResponse.unauthorized(detail="User authentication required.", instance=request.path)
        user_id_str = str(user_id)
        
        try:
            if not project_id or explicit_personal:
                # Fall back to personal data when project not supplied
                personal_data = cosmos_service.get_latest_personal_user_data(user_id_str)
                if not personal_data:
                    return StandardResponse.success(data={
                        "success": True,
                        "comments": [],
                        "comments_count": 0,
                        "file_name": None,
                        "upload_date": None,
                        "message": "No comments found for personal analysis",
                        "is_personal": True,
                    }, message="Operation completed successfully")

                return StandardResponse.success(data={
                    "success": True,
                    "comments": personal_data.get('feedback', []),
                    "comments_count": len(personal_data.get('feedback', [])),
                    "file_name": personal_data.get('file_name'),
                    "upload_date": personal_data.get('uploaded_date'),
                    "is_personal": True,
                    "project_id": personal_data.get('project_id'),
                }, message="Operation completed successfully")

            # Project-specific data path
            user_data = cosmos_service.get_user_data_by_project(user_id_str, project_id)
            
            if not user_data:
                return StandardResponse.success(data={
                    "success": True,
                    "comments": [],
                    "comments_count": 0,
                    "file_name": None,
                    "upload_date": None,
                    "message": "No comments found for this project",
                    "is_personal": False,
                }, message="Operation completed successfully")
            
            return StandardResponse.success(data={
                "success": True,
                "comments": user_data.get('feedback', []),
                "comments_count": len(user_data.get('feedback', [])),
                "file_name": user_data.get('file_name'),
                "upload_date": user_data.get('uploaded_date'),
                "is_personal": bool(user_data.get('is_personal')),
                "project_id": project_id,
            }, message="Operation completed successfully")
            
        except Exception as e:
            print(f"Error retrieving user comments: {e}")
            return StandardResponse.internal_server_error(detail="Failed to retrieve user comments.", instance=request.path)


class GetUserStoriesView(APIView):
    """Get user stories for a specific user and project"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        """
        Get user stories for a specific project
        Query parameters:
        - project_id (required): The project ID to retrieve user stories for
        - user_id (optional): If not provided, uses the authenticated user's ID
        """
        project_id = request.query_params.get('project_id')
        
        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)
        
        # Get user ID from request or use authenticated user
        user_id = request.query_params.get('user_id')
        if not user_id:
            user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            
        if not user_id:
            return StandardResponse.unauthorized(detail="User authentication required.", instance=request.path)
        
        try:
            # Get user stories for the specific user and project
            user_stories = cosmos_service.get_user_stories_by_user_and_project(str(user_id), project_id)
            
            return StandardResponse.success(data={
                "success": True,
                "user_stories": user_stories,
                "count": len(user_stories),
                "user_id": str(user_id),
                "project_id": project_id
            }, message="Operation completed successfully")
            
        except Exception as e:
            print(f"Error retrieving user stories: {e}")
            return StandardResponse.internal_server_error(detail="Failed to retrieve user stories.", instance=request.path)


class GetAllUserStoriesView(APIView):
    """Get all user stories for a specific user across all projects"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        """
        Get all user stories for the authenticated user
        Query parameters:
        - user_id (optional): If not provided, uses the authenticated user's ID
        """
        # Get user ID from request or use authenticated user
        user_id = request.query_params.get('user_id')
        if not user_id:
            user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            
        if not user_id:
            return StandardResponse.unauthorized(detail="User authentication required.", instance=request.path)
        
        try:
            # Get all user stories for the user
            user_stories = cosmos_service.get_user_stories_by_user(str(user_id))
            
            return StandardResponse.success(data={
                "success": True,
                "user_stories": user_stories,
                "count": len(user_stories),
                "user_id": str(user_id)
            }, message="Operation completed successfully")
            
        except Exception as e:
            print(f"Error retrieving user stories: {e}")
            return StandardResponse.internal_server_error(detail="Failed to retrieve user stories.", instance=request.path)


class GetUserWorkItemsView(APIView):
    """Get user work items from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        try:
            project_id = request.query_params.get('project_id')
            user_id = request.user.id if request.user.is_authenticated else None
            
            if not project_id:
                return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)
            
            # Query user work items from Cosmos DB
            query = "SELECT * FROM c WHERE c.projectId = @project_id AND c.type = 'user_story'"
            parameters = [{"name": "@project_id", "value": project_id}]
            
            if user_id:
                query += " AND c.userId = @user_id"
                parameters.append({"name": "@user_id", "value": str(user_id)})
            
            query += " ORDER BY c.generated_at DESC"
            
            work_items = cosmos_service.query_items('user_stories', query, parameters)
            
            return StandardResponse.success(data={
                "work_items": work_items,
                "count": len(work_items)
            }, message="Operation completed successfully")
            
        except Exception as e:
            return StandardResponse.internal_server_error(detail="Failed to retrieve user work items.", instance=request.path)


class UserStoryCreationView(APIView):
    """Generate user stories/work items from analysis data"""
    permission_classes = [IsAdminOrUser]
    
    @async_to_sync
    async def post(self, request):
        """
        Generate user stories/work items from analysis data (from /analyze endpoint)
        """
        analysis_data = request.data.get("analysis_data")
        comments = request.data.get("comments", [])  # Keep for fallback
        process_template = request.data.get("process_template", "Agile")
        incoming_project_id = request.data.get("project_id")
        platform = request.data.get("platform", "azure")  # Default to Azure DevOps
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else "anonymous"
        user_id_str = str(user_id)
        
        # Get company name from user profile for company-specific prompts
        company_name = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_data = cosmos_service.get_user_by_username(request.user.username)
                if user_data:
                    company_name = user_data.get('company_name')
            except Exception as e:
                print(f"Warning: Could not get company_name for user: {e}")

        resolved_project_id, project_doc, is_draft = cosmos_service.ensure_project_context(
            incoming_project_id,
            user_id_str,
        )
        project_id = resolved_project_id
        project_context = {
            "project_id": project_id,
            "project_status": project_doc.get("status", "draft" if is_draft else "active"),
            "config_state": project_doc.get("config_state", "unconfigured" if is_draft else "complete"),
            "is_draft": is_draft,
        }

        print("🔧 UserStoryCreationView called")
        print(f"📦 Platform: {platform}")
        print(f"📋 Process template: {process_template}")
        print(f"🆔 Project ID (incoming): {incoming_project_id}")
        print(f"🆔 Project ID (resolved): {project_id}")
        print(f"📊 Analysis data provided: {analysis_data is not None}")
        print(f"💬 Comments count: {len(comments) if comments else 0}")
        print(f"🏢 Company name: {company_name}")

        # Validate input - need both analysis_data and comments
        if not analysis_data:
            return StandardResponse.validation_error(detail="analysis_data is required. Please run sentiment analysis first using /analyze endpoint.", instance=request.path)
        
        if not comments or not isinstance(comments, list):
            return StandardResponse.validation_error(detail="comments are required along with analysis_data for work item generation.", instance=request.path)

        try:
            work_items = []
            summary = {}

            print("🔧 Generating work items from analysis data...")
            
            # Extract the actual analysis data from the response structure
            actual_analysis_data = analysis_data
            if isinstance(analysis_data, dict) and 'analysisData' in analysis_data:
                actual_analysis_data = analysis_data['analysisData']
            
            # Create work item generation prompt based on platform
            project_metadata = request.data.get("project_metadata")
            prompt = getDeepAnalysisPrompt(platform=platform, project_metadata=project_metadata, company_name=company_name)
            feedback_block = "\n".join([str(c) for c in comments]) if comments else "Analysis data provided"
            prompt_filled = prompt.replace("<feedback_data>", feedback_block)
            
            print(f"Work item generation prompt length: {len(prompt_filled)} characters")
            
            # Generate work items using AI
            try:
                work_items_result = await generate_completions(prompt_filled)
                print(f"🔍 Raw work items result: {work_items_result}")
                print(f"🔍 Raw work items result type: {type(work_items_result)}")
                print(f"🔍 Raw work items result length: {len(str(work_items_result)) if work_items_result else 0}")
            except Exception as e:
                print(f"❌ Error in AI completion: {e}")
                work_items_result = None

            # Parse the LLM response
            try:
                parsed_work_items = json.loads(work_items_result) if isinstance(work_items_result, str) else (work_items_result or {})
                print(f"🔍 Parsed work items: {parsed_work_items}")
                print(f"🔍 Parsed work items type: {type(parsed_work_items)}")
                print(f"🔍 Parsed work items keys: {list(parsed_work_items.keys()) if isinstance(parsed_work_items, dict) else 'Not a dict'}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"🔧 Attempting to fix truncated JSON...")
                
                # Try to fix truncated JSON by adding missing closing braces
                try:
                    # Find the last complete object and add missing braces
                    result_str = str(work_items_result)
                    
                    # Count opening and closing braces to see what's missing
                    open_braces = result_str.count('{')
                    close_braces = result_str.count('}')
                    missing_braces = open_braces - close_braces
                    
                    if missing_braces > 0:
                        # Add missing closing braces
                        fixed_result = result_str + '}' * missing_braces
                        print(f"🔧 Added {missing_braces} missing closing braces")
                        parsed_work_items = json.loads(fixed_result)
                        print(f"✅ Successfully parsed fixed JSON")
                    else:
                        raise e
                        
                except Exception as fix_error:
                    print(f"❌ Failed to fix JSON: {fix_error}")
                    print(f"❌ Raw result that failed to parse: {work_items_result}")
                    parsed_work_items = {"work_items": [], "summary": {}}
            except Exception as e:
                print(f"❌ Error parsing work items response: {e}")
                print(f"❌ Raw result that failed to parse: {work_items_result}")
                parsed_work_items = {"work_items": [], "summary": {}}

            # Validate and structure the response
            work_items = parsed_work_items.get("work_items", []) or parsed_work_items.get("workitems", [])
            summary = parsed_work_items.get("summary", {})
            
            print(f"🔍 Extracted work_items: {work_items}")
            print(f"🔍 Extracted work_items length: {len(work_items) if work_items else 0}")
            print(f"🔍 Extracted summary: {summary}")
            
            # Fallback: If no work items generated, create them from analysis data
            if not work_items or len(work_items) == 0:
                print("⚠️ No work items generated by AI, creating fallback work items from analysis data")
                print(f"🔧 Analysis data structure: {list(analysis_data.keys()) if isinstance(analysis_data, dict) else 'Not a dict'}")
                work_items = createFallbackWorkItems(analysis_data, process_template)
                summary = {
                    "total_items": len(work_items),
                    "by_type": {},
                    "by_priority": {}
                }
                print(f"🔧 Fallback work items created: {len(work_items)} items")
            else:
                print(f"✅ AI generated {len(work_items)} work items successfully")

            # Normalize work items to unified format
            normalized_work_items = []
            for item in work_items:
                # Ensure consistent field names across platforms
                normalized_item = {
                    "id": str(uuid.uuid4()),
                    "type": item.get("type", "Feature"),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "priority": item.get("priority", "Medium"),
                    "tags": item.get("tags", []) or item.get("labels", []),
                    "acceptancecriteria": item.get("acceptancecriteria") or item.get("acceptance_criteria") or item.get("acceptance", ""),
                    "businessvalue": item.get("businessvalue") or item.get("business_value", ""),
                    "effortestimate": item.get("effortestimate") or item.get("effort_estimate", ""),
                    "featurearea": item.get("featurearea") or item.get("feature_area", "General"),
                    "created_at": datetime.now().isoformat(),
                    "project_id": project_id,
                    "process_template": process_template,
                    "platform": platform,
                    "submitted": False,
                    "submitted_at": None,
                    "submitted_to": None,
                    "external_work_item_id": None,
                    "external_url": None,
                    "submission_id": None
                }
                normalized_work_items.append(normalized_item)

            work_items = normalized_work_items
            print(f"✅ Work items normalization completed: {len(work_items)} items")

            # Generate summary statistics
            if not summary or not summary.get('totalitems'):
                type_counts = {}
                priority_counts = {}
                for item in work_items:
                    item_type = item.get('type', 'Unknown')
                    item_priority = item.get('priority', 'Unknown')
                    type_counts[item_type] = type_counts.get(item_type, 0) + 1
                    priority_counts[item_priority] = priority_counts.get(item_priority, 0) + 1
                
                summary = {
                    "totalitems": len(work_items),
                    "bytype": type_counts,
                    "bypriority": priority_counts
                }

            # Step 3: Save to Cosmos DB if project_id is provided
            user_story_id = f'user_story_{str(uuid.uuid4()).replace("-", "")}'
            if project_id and work_items:
                try:
                    # Save work items to Cosmos DB in unified format
                    user_story_data = {
                        'id': user_story_id,
                        'type': 'user_story',
                        'userId': user_id_str,
                        'projectId': project_id,
                        'process_template': process_template,
                        'platform': platform,
                        'generated_at': datetime.now().isoformat(),
                        'work_items': work_items,
                        'summary': summary,
                        'comments_count': len(comments) if comments else 0
                    }
                    
                    print(f"Saving user stories with project_id: {project_id}")
                    print(f"User story data ID: {user_story_data['id']}")
                    print(f"Work items count: {len(work_items)}")
                    
                    saved_result = cosmos_service.save_user_story(user_story_data)
                    if saved_result:
                        print(f"Successfully saved user stories: {saved_result.get('id')}")
                        user_story_id = saved_result.get('id', user_story_id)
                    else:
                        print("Failed to save user stories")
                        
                except Exception as e:
                    print(f"Error saving to Cosmos DB: {e}")

            # Format response to match the unified format
            formatted = {
                'id': user_story_id,
                'type': 'user_story',
                'userId': user_id_str,
                'projectId': project_id if project_id else 'unknown',
                'process_template': process_template,
                'platform': platform,
                'generated_at': datetime.now().isoformat(),
                'work_items': work_items,
                'summary': summary,
                'comments_count': len(comments) if comments else 0,
                'success': True,
                'context': project_context,
            }
            
            print(f"🔍 Final response data: {formatted}")
            print(f"🔍 Final work_items count: {len(work_items)}")
            print(f"🔍 Final work_items_by_feature keys: {list(groupWorkItemsByFeature(work_items).keys())}")
                
            return StandardResponse.success(data=formatted, message="Operation completed successfully")
            
        except Exception as e:
            print(f"Error generating user stories: {e}")
            error_response = {
                "error": str(e),
                "details": "Failed to generate user stories",
                "code": "user_story_creation_error"
            }
            return StandardResponse.internal_server_error(detail=error_response.get("error", "Internal server error"), instance=request.path)


class UpdateWorkItemView(APIView):
    """Update a specific work item"""
    permission_classes = [IsAdminOrUser]
    
    def put(self, request, work_item_id):
        """
        Update a work item by ID
        """
        # Get user ID from request
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        if not user_id:
            return StandardResponse.unauthorized(detail="User authentication required.", instance=request.path)
        
        try:
            # Get the updated work item data
            updated_data = request.data
            print(f"Updating work item {work_item_id} with data: {updated_data}")
            
            # Validate required fields
            if not updated_data.get('title'):
                return StandardResponse.validation_error(detail="Title is required.", instance=request.path)
            
            # Use the new method that handles embedded work items in insights container
            updated_work_item = cosmos_service.update_embedded_work_item(
                work_item_id=work_item_id,
                user_id=str(user_id),
                updated_data=updated_data
            )
            
            if not updated_work_item:
                return StandardResponse.not_found(detail="Work item not found or update failed.", instance=request.path)
            
            return StandardResponse.success(data={
                "success": True,
                "work_item": updated_work_item,
                "message": "Work item updated successfully"
            }, message="Operation completed successfully")
            
        except Exception as e:
            print(f"Error updating work item: {e}")
            return StandardResponse.internal_server_error(detail="Failed to update work item.", instance=request.path)


class JiraDeepAnalysisView(APIView):
    permission_classes = [IsAdminOrUser]
    
    @async_to_sync
    async def post(self, request):
        comments = request.data.get("comments")
        project_id = request.data.get("project_id")
        project_metadata = request.data.get("project_metadata")
        
        # Get company name from user profile for company-specific prompts
        company_name = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_data = cosmos_service.get_user_by_username(request.user.username)
                if user_data:
                    company_name = user_data.get('company_name')
            except Exception as e:
                app_logger.warning(f"Could not get company_name for user: {e}")

        if not comments or not isinstance(comments, list):
            return StandardResponse.validation_error(detail="A list of comments is required.", instance=request.path)

        try:
            # Use unified prompt with Jira platform and optional project metadata
            prompt = getDeepAnalysisPrompt(platform='jira', project_metadata=project_metadata, company_name=company_name)
            if project_metadata:
                app_logger.info(f"Using dynamic prompt for project: {project_metadata.get('project', {}).get('name', 'Unknown')}")
            else:
                app_logger.info("Using static Jira prompt (no project metadata provided)")
            
            feedback_block = "\n".join([str(c) for c in comments])
            prompt_filled = prompt.replace("<feedback_data>", feedback_block)
            result = await generate_completions(prompt_filled)

            # Parse the result
            try:
                parsed = json.loads(result) if isinstance(result, str) else (result or {})
            except Exception as e:
                app_logger.error(f"Failed to parse Jira deep analysis result: {e}")
                parsed = {}

            # Save analysis to Cosmos DB
            try:
                analysis_id = str(uuid.uuid4())
                analysis_data = {
                    'id': f'jira_analysis_{analysis_id}',
                    'type': 'jira_analysis',
                    'project_id': project_id,
                    'project_metadata': project_metadata,
                    'comments_count': len(comments),
                    'analysis_date': datetime.now().isoformat(),
                    'analysis_result': parsed,
                    'metadata': {
                        'source': 'jira_deep_analysis',
                        'prompt_type': 'dynamic' if project_metadata else 'static',
                        'processing_timestamp': datetime.now().isoformat()
                    }
                }
                
                # Save Jira analysis to user_stories container
                saved_analysis = cosmos_service.save_user_story(analysis_data)
                if saved_analysis:
                    app_logger.info(f"Jira analysis saved to Cosmos DB with ID: {saved_analysis.get('id')}")
            except Exception as e:
                app_logger.error(f"Error saving Jira analysis to Cosmos DB: {e}")

            # Extract work items and summary from the parsed result
            work_items = parsed.get("work_items", []) or parsed.get("workitems", [])
            summary = parsed.get("summary", {})
            
            # Normalize field names in work items
            for item in work_items:
                # Normalize field names to handle variations
                if "acceptancecriteria" in item and "acceptance_criteria" not in item:
                    item["acceptance_criteria"] = item.pop("acceptancecriteria")
                if "businessvalue" in item and "business_value" not in item:
                    item["business_value"] = item.pop("businessvalue")
                if "effortestimate" in item and "effort_estimate" not in item:
                    item["effort_estimate"] = item.pop("effortestimate")
                if "featurearea" in item and "feature_area" not in item:
                    item["feature_area"] = item.pop("featurearea")
                
                # Handle tags vs labels
                if "tags" in item and "labels" not in item:
                    item["labels"] = item["tags"]
                
                # Add metadata to each work item
                item["id"] = str(uuid.uuid4())
                item["created_at"] = datetime.now().isoformat()
                item["project_id"] = project_id
                item["process_template"] = "Agile"  # Default for Jira

            # Format response to match Azure format
            formatted = {
                'success': True,
                'work_items': work_items,
                'work_items_by_feature': groupWorkItemsByFeature(work_items),
                'summary': summary,
                'process_template': 'Agile',
                'generated_at': datetime.now().isoformat(),
                'comments_analyzed': len(comments),
                'project_metadata': project_metadata
            }
            
            return StandardResponse.success(data=formatted, message="Operation completed successfully")

        except Exception as e:
            app_logger.error(f"Error in Jira deep analysis: {e}")
            return StandardResponse.internal_server_error(
                detail=f"Analysis failed: {str(e)}",
                instance=request.path
            )


class AnalysisHistoryView(APIView):
    """Get analysis history for a project"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        """Get all analyses for a specific project"""
        project_id = request.query_params.get('project_id')
        
        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)
        
        try:
            # Get analysis history
            history = cosmos_service.get_analysis_history_for_project(project_id)
            
            return StandardResponse.success(data={
                "success": True,
                "project_id": project_id,
                "total_analyses": len(history),
                "analyses": history,
                "quarters": list(set(a.get('quarter', '') for a in history if a.get('quarter')))
            }, message="Operation completed successfully")
            
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch analysis history: {str(e)}",
                instance=request.path
            )


class AnalysisByQuarterView(APIView):
    """Get analysis for a specific quarter"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        """Get analysis for a specific project and quarter"""
        project_id = request.query_params.get('project_id')
        quarter = request.query_params.get('quarter')
        
        if not project_id or not quarter:
            return StandardResponse.validation_error(detail="Project ID and quarter are required.", instance=request.path)
        
        try:
            analysis = cosmos_service.get_analysis_by_quarter(project_id, quarter)
            
            if not analysis:
                return StandardResponse.not_found(
                    detail=f"No analysis found for project {project_id} in quarter {quarter}",
                    instance=request.path
                )
            
            return StandardResponse.success(data={
                "success": True,
                "project_id": project_id,
                "quarter": quarter,
                "analysis": analysis
            }, message="Operation completed successfully")
            
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch analysis: {str(e)}",
                instance=request.path
            )


class CumulativeAnalysisView(APIView):
    """Get cumulative analysis combining all historical data"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        """Get cumulative analysis for a project"""
        project_id = request.query_params.get('project_id')
        
        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)
        
        try:
            cumulative = cosmos_service.get_cumulative_analysis_for_project(project_id)
            
            if not cumulative:
                return StandardResponse.not_found(
                    detail=f"No data found for project {project_id}",
                    instance=request.path
                )
            
            return StandardResponse.success(data={
                "success": True,
                "project_id": project_id,
                "cumulative_analysis": cumulative
            }, message="Operation completed successfully")
            
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch cumulative analysis: {str(e)}",
                instance=request.path
            )


class GetUserStoriesView(APIView):
    """Get user stories for a specific project"""
    permission_classes = [IsAdminOrUser]

    def get(self, request):
        """Get user stories for a specific project"""
        project_id = request.query_params.get("project_id")
        user_id = request.query_params.get("user_id")

        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)

        try:
            if user_id:
                # Get user stories for specific user and project
                user_stories = cosmos_service.get_user_stories_by_user_and_project(user_id, project_id)
            else:
                # Get all user stories for the project (backend will infer user from token)
                user_stories = cosmos_service.get_user_stories_by_project(project_id)

            return StandardResponse.success(data={
                "success": True,
                "user_stories": user_stories,
                "project_id": project_id,
                "count": len(user_stories)
            }, message="Operation completed successfully")

        except Exception as e:
            print(f"Error getting user stories: {e}")
            return StandardResponse.internal_server_error(detail="Failed to retrieve user stories.", instance=request.path)


class GetAllUserStoriesView(APIView):
    """Get all user stories for a user"""
    permission_classes = [IsAdminOrUser]

    def get(self, request):
        """Get all user stories for the current user"""
        user_id = request.query_params.get("user_id")

        try:
            if user_id:
                # Get user stories for specific user
                user_stories = cosmos_service.get_user_stories_by_user(user_id)
            else:
                # Backend will infer user from token
                # For now, return empty list if no user_id provided
                user_stories = []

            return StandardResponse.success(data={
                "success": True,
                "user_stories": user_stories,
                "count": len(user_stories)
            }, message="Operation completed successfully")

        except Exception as e:
            print(f"Error getting all user stories: {e}")
            return StandardResponse.internal_server_error(detail="Failed to retrieve user stories.", instance=request.path)


class AnalysisComparisonView(APIView):
    """Compare analyses between quarters"""
    permission_classes = [IsAdminOrUser]

    def get(self, request):
        """Compare analyses between two quarters"""
        project_id = request.query_params.get('project_id')
        quarter1 = request.query_params.get('quarter1')
        quarter2 = request.query_params.get('quarter2')
        
        if not all([project_id, quarter1, quarter2]):
            return StandardResponse.validation_error(detail="Project ID, quarter1, and quarter2 are required.", instance=request.path)
        
        try:
            analysis1 = cosmos_service.get_analysis_by_quarter(project_id, quarter1)
            analysis2 = cosmos_service.get_analysis_by_quarter(project_id, quarter2)
            
            if not analysis1:
                return StandardResponse.not_found(
                    detail=f"No analysis found for quarter {quarter1}",
                    instance=request.path
                )
            
            if not analysis2:
                return StandardResponse.not_found(
                    detail=f"No analysis found for quarter {quarter2}",
                    instance=request.path
                )
            
            # Create comparison data
            comparison = {
                "project_id": project_id,
                "quarter1": {
                    "quarter": quarter1,
                    "analysis": analysis1,
                    "sentiment_summary": analysis1.get('sentimentsummary', {}),
                    "feature_count": len(analysis1.get('featureasba', [])),
                    "total_comments": analysis1.get('counts', {}).get('total', 0)
                },
                "quarter2": {
                    "quarter": quarter2,
                    "analysis": analysis2,
                    "sentiment_summary": analysis2.get('sentimentsummary', {}),
                    "feature_count": len(analysis2.get('featureasba', [])),
                    "total_comments": analysis2.get('counts', {}).get('total', 0)
                },
                "comparison": {
                    "sentiment_change": self._calculate_sentiment_change(
                        analysis1.get('sentimentsummary', {}),
                        analysis2.get('sentimentsummary', {})
                    ),
                    "feature_change": len(analysis2.get('featureasba', [])) - len(analysis1.get('featureasba', [])),
                    "comment_change": analysis2.get('counts', {}).get('total', 0) - analysis1.get('counts', {}).get('total', 0)
                }
            }
            
            return StandardResponse.success(data={
                "success": True,
                "comparison": comparison
            }, message="Operation completed successfully")
            
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to compare analyses: {str(e)}",
                instance=request.path
            )
    
    def _calculate_sentiment_change(self, sentiment1, sentiment2):
        """Calculate sentiment change between two analyses"""
        return {
            "positive_change": sentiment2.get('positive', 0) - sentiment1.get('positive', 0),
            "negative_change": sentiment2.get('negative', 0) - sentiment1.get('negative', 0),
            "neutral_change": sentiment2.get('neutral', 0) - sentiment1.get('neutral', 0)
        }


class UpdateUserStoryView(APIView):
    """Update a specific user story"""
    permission_classes = [IsAdminOrUser]

    def put(self, request, user_story_id):
        """Update a user story (actually updates embedded work item)"""
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None

        if not user_id:
            return StandardResponse.unauthorized(detail="Authentication required.", instance=request.path)

        try:
            # Get the updated data from request body
            updated_data = request.data

            # Update the embedded work item in Cosmos DB
            # The user_story_id is actually the work item ID in this context
            updated_work_item = cosmos_service.update_embedded_work_item(
                work_item_id=user_story_id,
                user_id=str(user_id),
                updated_data=updated_data
            )

            if not updated_work_item:
                return StandardResponse.not_found(detail="Work item not found or update failed.", instance=request.path)

            return StandardResponse.success(data={
                "success": True,
                "work_item": updated_work_item,
                "message": "Work item updated successfully"
            }, message="Operation completed successfully")

        except Exception as e:
            print(f"Error updating work item: {e}")
            return StandardResponse.internal_server_error(detail="Failed to update work item.", instance=request.path)


class DeleteUserStoryView(APIView):
    """Delete a specific user story"""
    permission_classes = [IsAdminOrUser]

    def delete(self, request, user_story_id):
        """Delete a user story"""
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None

        if not user_id:
            return StandardResponse.unauthorized(detail="Authentication required.", instance=request.path)

        try:
            # Get the user story first to verify ownership
            user_story = cosmos_service.get_user_story(user_story_id, str(user_id))
            if not user_story:
                return StandardResponse.not_found(detail="User story not found.", instance=request.path)

            # Delete the user story from Cosmos DB
            success = cosmos_service.delete_item(
                container_type='user_stories',
                item_id=user_story_id,
                partition_key=str(user_id)
            )

            if not success:
                return StandardResponse.internal_server_error(detail="Failed to delete user story.", instance=request.path)

            return StandardResponse.success(data={
                "success": True,
                "message": "User story deleted successfully"
            }, message="Operation completed successfully")

        except Exception as e:
            print(f"Error deleting user story: {e}")
            return StandardResponse.internal_server_error(detail="Failed to delete user story.", instance=request.path)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteUserStoryItemsView(APIView):
    """Delete embedded user story items (work items) from collections or entire user stories"""
    permission_classes = [IsAdminOrUser]
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to add debugging"""
        print(f"🔥 DeleteUserStoryItemsView.dispatch called - Method: {request.method}")
        print(f"🔥 Available methods: {self.http_method_names}")
        return super().dispatch(request, *args, **kwargs)

    def put(self, request):
        """Update user story by removing specific work items (using PUT for update operation)
        
        Body: { 
            "ids": ["work_item_id1", "work_item_id2", ...],
            "type": "work_items",
            "user_story_id": "user_story_xxx" // Required for targeted deletion
        }
        """
        return self._handle_remove_work_items(request)
    
    def post(self, request):
        """Alternative POST method for remove operations"""
        print("🚀 POST method called in DeleteUserStoryItemsView!")
        return self._handle_remove_work_items(request)
    
    def get(self, request):
        """Debug GET method to test if view is accessible"""
        print("🔍 GET method called in DeleteUserStoryItemsView!")
        return StandardResponse.success(data={
            "message": "DeleteUserStoryItemsView is accessible",
            "methods": ["GET", "POST", "PUT"],
            "endpoint": "/api/insights/user-stories/delete-items/"
        }, message="Operation completed successfully")
    
    def _handle_remove_work_items(self, request):
        """Remove work items from user story using UPDATE approach"""
        print(f"🔄 RemoveWorkItems called - Method: {request.method}")
        print(f"📦 Request data: {request.data}")
        
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None

        if not user_id:
            return StandardResponse.unauthorized(detail="Authentication required.", instance=request.path)

        work_item_ids = request.data.get('ids', [])
        user_story_id = request.data.get('user_story_id')
        
        if not isinstance(work_item_ids, list) or len(work_item_ids) == 0:
            return StandardResponse.validation_error(detail="A non-empty 'ids' array is required.", instance=request.path)

        if not user_story_id:
            return StandardResponse.validation_error(detail="user_story_id is required for work item removal.", instance=request.path)

        try:
            # Handle consolidated user story IDs (created by frontend)
            actual_user_story_id = user_story_id
            if user_story_id.startswith('consolidated_'):
                # Extract project ID from consolidated ID
                project_id = user_story_id.replace('consolidated_', '')
                print(f"🔍 Consolidated ID detected, finding user story for project: {project_id}")
                
                # Find user story by project ID and user ID
                user_stories = cosmos_service.get_user_stories_by_user_and_project(str(user_id), project_id)
                if not user_stories:
                    print(f"❌ No user stories found for project: {project_id} and user: {user_id}")
                    return StandardResponse.not_found(
                        detail=f"No user stories found for project '{project_id}'",
                        instance=request.path
                    )
                
                # Use the first (most recent) user story
                actual_user_story_id = user_stories[0]['id']
                print(f"✅ Found user story: {actual_user_story_id}")
            
            # Use the cosmos service method to remove work items from specific user story
            result = cosmos_service.delete_work_items_from_user_story(
                actual_user_story_id, work_item_ids, str(user_id)
            )
            
            if result["success"]:
                print(f"✅ Successfully removed {result['deleted_count']} work items from {user_story_id}")
                return StandardResponse.success(
                    data={
                        "deleted": result["deleted_count"],
                        "remaining": result["remaining_count"],
                        "user_story_id": result["user_story_id"],
                        "type": "work_items"
                    },
                    message=f"Removed {result['deleted_count']} work items from user story"
                )
            else:
                print(f"❌ Failed to remove work items: {result['error']}")
                return StandardResponse.validation_error(detail=result["error"]
                , instance=request.path)
                
        except Exception as e:
            print(f"💥 Error removing work items: {e}")
            return StandardResponse.internal_server_error(
                detail=f"Failed to remove work items: {str(e)}",
                instance=request.path
            )


class WorkItemRemovalView(APIView):
    """New clean view for work item removal"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        """Debug GET method to test if view is accessible"""
        print("🔍 WorkItemRemovalView GET called!")
        return StandardResponse.success(data={
            "message": "WorkItemRemovalView is accessible",
            "methods": ["GET", "PUT"],
            "endpoint": "/api/insights/user-stories/remove-work-items/",
            "status": "working",
            "note": "Use PUT method for updating user story (removing work items)"
        }, message="Operation completed successfully")
    
    def put(self, request):
        """Remove work items from user story (UPDATE operation)"""
        print("🎯 WorkItemRemovalView PUT called!")
        print(f"📦 Request data: {request.data}")
        
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        if not user_id:
            return StandardResponse.unauthorized(detail="Authentication required.", instance=request.path)

        work_item_ids = request.data.get('ids', [])
        user_story_id = request.data.get('user_story_id')
        
        print(f"🔍 Attempting to remove work items: {work_item_ids}")
        print(f"🔍 From user story: {user_story_id}")
        print(f"🔍 For user: {user_id}")
        
        if not work_item_ids or not user_story_id:
            return StandardResponse.validation_error(detail="Both 'ids' and 'user_story_id' are required."
            , instance=request.path)

        try:
            # Handle consolidated user story IDs (created by frontend)
            actual_user_story_id = user_story_id
            if user_story_id.startswith('consolidated_'):
                # Extract project ID from consolidated ID
                project_id = user_story_id.replace('consolidated_', '')
                print(f"🔍 Consolidated ID detected, finding user story for project: {project_id}")
                
                # Find user story by project ID and user ID
                user_stories = cosmos_service.get_user_stories_by_user_and_project(str(user_id), project_id)
                if not user_stories:
                    print(f"❌ No user stories found for project: {project_id} and user: {user_id}")
                    return StandardResponse.not_found(
                        detail=f"No user stories found for project '{project_id}'",
                        instance=request.path
                    )
                
                # Use the first (most recent) user story
                actual_user_story_id = user_stories[0]['id']
                print(f"✅ Found user story: {actual_user_story_id}")
            else:
                # user_story_id was provided directly
                actual_user_story_id = f"user_story_{user_story_id}"
            
            # Get the user story (cross-partition safe)
            user_story = cosmos_service.get_user_story_by_id(actual_user_story_id)
            if not user_story:
                print(f"❌ User story not found: {actual_user_story_id} for user: {user_id}")
                return StandardResponse.not_found(
                    detail=f"User story '{actual_user_story_id}' not found for user '{user_id}'",
                    instance=request.path
                )
            
            print(f"✅ Found user story: {user_story.get('id', 'unknown')}")
            print(f"📊 Current work items count: {len(user_story.get('work_items', []))}")
            
            # Use the cosmos service method to remove work items
            result = cosmos_service.delete_work_items_from_user_story(
                actual_user_story_id, work_item_ids, str(user_id)
            )
            
            print(f"🔄 Cosmos service result: {result}")
            
            if result["success"]:
                return StandardResponse.success(
                    data={
                        "deleted": result["deleted_count"],
                    "remaining": result["remaining_count"],
                    "user_story_id": result["user_story_id"],
                    "message": f"Successfully removed {result['deleted_count']} work items"
                }, status=status.HTTP_200_OK)
            else:
                return StandardResponse.validation_error(detail=result["error"]
                , instance=request.path)
                
        except Exception as e:
            print(f"💥 Error in WorkItemRemovalView: {e}")
            import traceback
            traceback.print_exc()
            return StandardResponse.internal_server_error(
                detail=f"Failed to remove work items: {str(e)}",
                instance=request.path
            )


class TestDeleteView(APIView):
    """Simple test view to debug method handling"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        return StandardResponse.success(data={"message": "GET works", "method": "GET"}, message="Operation completed successfully")
    
    def post(self, request):
        print("🧪 TestDeleteView POST called!")
        return StandardResponse.success(data={"message": "POST works", "method": "POST", "data": request.data}, message="Operation completed successfully")
    
    def put(self, request):
        return StandardResponse.success(data={"message": "PUT works", "method": "PUT", "data": request.data}, message="Operation completed successfully")
    
    def delete(self, request):
        return StandardResponse.success(data={"message": "DELETE works", "method": "DELETE", "data": request.data}, message="Operation completed successfully")


class DeleteSingleUserStoryItemView(APIView):
    """Delete a single embedded user story item by id"""
    permission_classes = [IsAdminOrUser]

    def delete(self, request, work_item_id: str):
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        if not user_id:
            return StandardResponse.unauthorized(detail="Authentication required.", instance=request.path)
        try:
            deleted = cosmos_service.delete_embedded_work_items([work_item_id], str(user_id))
            if deleted == 0:
                return StandardResponse.not_found(detail="User story item not found.", instance=request.path)
            return StandardResponse.success(data={"success": True, "deleted": 1}, message="Operation completed successfully")
        except Exception as e:
            print(f"Error deleting user story item: {e}")
            return StandardResponse.internal_server_error(detail="Failed to delete user story item.", instance=request.path)

def aggregate_analysis_data(existing_analysis, new_analysis, new_comments_count):
    """
    Aggregate existing analysis data with new analysis data
    """
    print("🔄 Starting data aggregation...")
    
    # Get existing data
    existing_overall = existing_analysis.get('sentimentsummary', {})
    existing_counts = existing_analysis.get('counts', {})
    existing_features = existing_analysis.get('featureasba', [])
    existing_pos_keywords = existing_analysis.get('positivekeywords', [])
    existing_neg_keywords = existing_analysis.get('negativekeywords', [])
    existing_total_comments = existing_analysis.get('total_comments_analyzed', existing_counts.get('total', 0))
    
    # Get new data
    new_overall = new_analysis.get('overall', {})
    new_counts = new_analysis.get('counts', {})
    new_features = new_analysis.get('features', [])
    new_pos_keywords = new_analysis.get('positive_keywords', [])
    new_neg_keywords = new_analysis.get('negative_keywords', [])
    
    # Calculate total comments analyzed
    total_comments_analyzed = existing_total_comments + new_comments_count
    
    print(f"📊 Existing comments: {existing_total_comments}, New comments: {new_comments_count}, Total: {total_comments_analyzed}")
    
    # Aggregate sentiment counts (add them together)
    aggregated_overall = {
        'positive': existing_overall.get('positive', 0) + new_overall.get('positive', 0),
        'negative': existing_overall.get('negative', 0) + new_overall.get('negative', 0),
        'neutral': existing_overall.get('neutral', 0) + new_overall.get('neutral', 0),
    }
    
    # Aggregate total counts
    aggregated_counts = {
        'total': existing_counts.get('total', 0) + new_counts.get('total', 0),
        'positive': existing_counts.get('positive', 0) + new_counts.get('positive', 0),
        'negative': existing_counts.get('negative', 0) + new_counts.get('negative', 0),
        'neutral': existing_counts.get('neutral', 0) + new_counts.get('neutral', 0),
    }
    
    # Aggregate features (merge by name, combine sentiment data)
    features_dict = {}
    
    # Add existing features
    for feature in existing_features:
        name = feature.get('name', '')
        if name:
            features_dict[name] = {
                'name': name,
                'description': feature.get('description', ''),
                'sentiment': feature.get('sentiment', {}),
                'keywords': feature.get('keywords', []),
                'comment_count': feature.get('comment_count', 0)
            }
    
    # Add/merge new features
    for feature in new_features:
        name = feature.get('name', '')
        if name:
            if name in features_dict:
                # Merge sentiment data
                existing_sentiment = features_dict[name]['sentiment']
                new_sentiment = feature.get('sentiment', {})
                features_dict[name]['sentiment'] = {
                    'positive': existing_sentiment.get('positive', 0) + new_sentiment.get('positive', 0),
                    'negative': existing_sentiment.get('negative', 0) + new_sentiment.get('negative', 0),
                    'neutral': existing_sentiment.get('neutral', 0) + new_sentiment.get('neutral', 0),
                }
                features_dict[name]['comment_count'] = features_dict[name]['comment_count'] + feature.get('comment_count', 0)
                # Merge keywords (avoid duplicates)
                existing_keywords = set(features_dict[name]['keywords'])
                new_keywords = set(feature.get('keywords', []))
                features_dict[name]['keywords'] = list(existing_keywords.union(new_keywords))
            else:
                # Add new feature
                features_dict[name] = {
                    'name': name,
                    'description': feature.get('description', ''),
                    'sentiment': feature.get('sentiment', {}),
                    'keywords': feature.get('keywords', []),
                    'comment_count': feature.get('comment_count', 0)
                }
    
    aggregated_features = list(features_dict.values())
    
    # Aggregate keywords (merge and remove duplicates)
    def merge_keywords(existing_kw, new_kw):
        # Handle both string arrays and object arrays
        existing_set = set()
        new_set = set()
        
        for kw in existing_kw:
            if isinstance(kw, str):
                existing_set.add(kw)
            elif isinstance(kw, dict) and 'keyword' in kw:
                existing_set.add(kw['keyword'])
        
        for kw in new_kw:
            if isinstance(kw, str):
                new_set.add(kw)
            elif isinstance(kw, dict) and 'keyword' in kw:
                new_set.add(kw['keyword'])
        
        return list(existing_set.union(new_set))
    
    aggregated_pos_keywords = merge_keywords(existing_pos_keywords, new_pos_keywords)
    aggregated_neg_keywords = merge_keywords(existing_neg_keywords, new_neg_keywords)
    
    aggregated_data = {
        'overall': aggregated_overall,
        'counts': aggregated_counts,
        'features': aggregated_features,
        'positive_keywords': aggregated_pos_keywords,
        'negative_keywords': aggregated_neg_keywords,
        'total_comments_analyzed': total_comments_analyzed
    }
    
    print(f"✅ Aggregation complete. Total features: {len(aggregated_features)}, Total comments: {total_comments_analyzed}")
    
    return aggregated_data


class UserStorySubmissionView(APIView):
    """Submit user stories to ITSM tools (Azure DevOps/Jira)"""
    permission_classes = [IsAdminOrUser]
    
    @async_to_sync
    async def post(self, request):
        """
        Submit user stories to respective ITSM tools
        Expected payload:
        {
            "user_id": "user_123",
            "project_id": "project_456", 
            "user_stories": [
                {
                    "id": "story_1",
                    "title": "Story title",
                    "description": "Story description",
                    "type": "Feature",
                    "priority": "High",
                    "acceptance_criteria": "Criteria",
                    "business_value": "Value",
                    "tags": ["tag1", "tag2"],
                    "created": false
                }
            ],
            "platform": "azure|jira",
            "process_template": "Agile",
            "time": "2025-01-01T12:00:00Z"
        }
        """
        try:
            # Extract request data
            user_id = request.data.get("user_id")
            project_id = request.data.get("project_id")
            user_stories = request.data.get("user_stories", [])
            platform = request.data.get("platform", "azure").lower()
            process_template = request.data.get("process_template", "Agile")
            submission_time = request.data.get("time", datetime.now().isoformat())
            
            print(f"🔧 UserStorySubmissionView called")
            print(f"👤 User ID: {user_id}")
            print(f"📋 Project ID: {project_id}")
            print(f"📊 Platform: {platform}")
            print(f"📝 User stories count: {len(user_stories)}")
            print(f"⏰ Submission time: {submission_time}")
            print(f"🔍 User stories being submitted: {[story.get('id') for story in user_stories]}")
            
            # Validate required fields
            if not user_id or not project_id or not user_stories:
                return StandardResponse.validation_error(detail="user_id, project_id, and user_stories are required", instance=request.path)
            
            if platform not in ['azure', 'jira']:
                return StandardResponse.validation_error(detail="platform must be either 'azure' or 'jira'", instance=request.path)
            
            if not isinstance(user_stories, list) or len(user_stories) == 0:
                return StandardResponse.validation_error(detail="user_stories must be a non-empty array", instance=request.path)
            
            # Get project configuration from Cosmos DB
            try:
                # Projects are stored with just the UUID, not with project_ prefix
                stored_project_id = project_id.replace('project_', '') if project_id.startswith('project_') else project_id
                print(f"🔍 Looking for project with ID: {stored_project_id}")
                
                project_data = cosmos_service.query_items(
                    'projects', 
                    'SELECT * FROM c WHERE c.id = @id',
                    [{"name": "@id", "value": stored_project_id}]
                )
                
                print(f"🔍 Project query result: {len(project_data) if project_data else 0} projects found")
                if project_data:
                    print(f"🔍 Found project: {project_data[0].get('name')} (ID: {project_data[0].get('id')})")
                else:
                    # Let's also try to see what projects exist
                    all_projects = cosmos_service.query_items('projects', 'SELECT c.id, c.name FROM c')
                    print(f"🔍 All projects in database: {[(p.get('id'), p.get('name')) for p in all_projects[:5]]}")
                
                if not project_data:
                    return StandardResponse.not_found(
                        detail=f"Project {project_id} not found",
                        instance=request.path
                    )
                
                project_config = project_data[0]
                print(f"📋 Found project: {project_config.get('name')}")
                print(f"📋 Project config keys: {list(project_config.keys())}")
                print(f"📋 Project externalLinks: {project_config.get('externalLinks', [])}")
                print(f"📋 Project userId: {project_config.get('userId')}")
                print(f"📋 Project azure_config: {project_config.get('azure_config', {})}")
                
            except Exception as e:
                print(f"❌ Error fetching project: {e}")
                return StandardResponse.internal_server_error(
                    detail=f"Failed to fetch project configuration: {str(e)}",
                    instance=request.path
                )
            
            # Transform user stories for the target platform
            transformed_items = []
            results = []
            
            for story in user_stories:
                # Skip already created stories if they have created=true
                if story.get("created", False):
                    print(f"⏭️ Skipping already created story: {story.get('title', 'Untitled')}")
                    results.append({
                        "success": True,
                        "story_id": story.get("id"),
                        "message": "Story already created, skipped",
                        "skipped": True
                    })
                    continue
                
                # Skip already submitted stories if they have submitted=true
                if story.get("submitted", False):
                    print(f"⏭️ Skipping already submitted story: {story.get('title', 'Untitled')}")
                    results.append({
                        "success": True,
                        "story_id": story.get("id"),
                        "message": "Story already submitted, skipped",
                        "skipped": True
                    })
                    continue
                
                # Transform story based on platform
                if platform == "azure":
                    transformed_item = {
                        "title": story.get("title", ""),
                        "description": story.get("description", ""),
                        "work_item_type": story.get("type", "Feature"),
                        "priority": self._map_priority_for_azure(story.get("priority", "Medium")),
                        "tags": "; ".join(story.get("tags", [])),
                        "acceptance_criteria": story.get("acceptance_criteria", ""),
                        "business_value": story.get("business_value", ""),
                        "story_points": story.get("story_points"),
                        "assigned_to": story.get("assigned_to"),
                        "area_path": story.get("area_path"),
                        "iteration_path": story.get("iteration_path")
                    }
                else:  # jira
                    transformed_item = {
                        "title": story.get("title", ""),
                        "description": story.get("description", ""),
                        "type": story.get("type", "Story"),
                        "priority": self._map_priority_for_jira(story.get("priority", "Medium")),
                        "labels": story.get("tags", []),
                        "acceptance_criteria": story.get("acceptance_criteria", ""),
                        "business_value": story.get("business_value", "")
                    }
                
                # Add story metadata
                transformed_item["original_story_id"] = story.get("id")
                transformed_items.append(transformed_item)
            
            # Submit to respective ITSM tool
            if platform == "azure":
                submission_results = await self._submit_to_azure_devops(
                    transformed_items, project_config, process_template
                )
            else:  # jira
                submission_results = await self._submit_to_jira(
                    transformed_items, project_config
                )
            
            # Combine results
            results.extend(submission_results)
            
            # Update user stories with submission status for successfully submitted items
            updated_user_stories = await self._update_user_stories_submission_status(user_id, project_id, results)
            
            # Calculate success metrics
            created_count = len([r for r in results if r.get('success') and not r.get('skipped')])
            skipped_count = len([r for r in results if r.get('skipped')])
            failed_count = len([r for r in results if not r.get('success')])
            
            # Determine overall success: true only if at least one story was created successfully
            # or if all stories were skipped (already created)
            overall_success = created_count > 0 or (skipped_count > 0 and failed_count == 0)
            
            # Prepare response
            response_data = {
                "success": overall_success,
                "platform": platform,
                "project_id": project_id,
                "summary": {
                    "total_stories": len(user_stories),
                    "created": created_count,
                    "skipped": skipped_count,
                    "failed": failed_count
                },
                "results": results,
                "updated_user_stories": updated_user_stories,  # Include updated user stories with submission status
                "submitted_at": submission_time
            }
            
            print(f"✅ User story submission completed: {response_data['summary']}")
            return StandardResponse.success(data=response_data, message="Operation completed successfully")
            
        except Exception as e:
            print(f"❌ Error in user story submission: {e}")
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )
        
        # This code should not be reached, but just in case
        return StandardResponse.internal_server_error(
            detail="Unexpected error in user story submission",
            instance=request.path
        )


# Dummy placeholder to close the function properly
class DummyPlaceholder:
    pass
    
    def _map_priority_for_azure(self, priority):
        """Map generic priority to Azure DevOps priority"""
        priority_map = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4
        }
        return priority_map.get(priority.lower(), 3)
    
    def _map_priority_for_jira(self, priority):
        """Map generic priority to Jira priority"""
        priority_map = {
            "critical": "Highest",
            "high": "High",
            "medium": "Medium", 
            "low": "Low"
        }
        return priority_map.get(priority.lower(), "Medium")
    
    async def _update_user_stories_submission_status(self, user_id, project_id, results):
        """Update user stories with submission status for successfully submitted items"""
        try:
            # Get all user story collections (generated work items) for this project
            # Filter for records that have work_items field (original generated collections) and exclude submission records
            user_stories = cosmos_service.query_items(
                'user_stories',
                'SELECT * FROM c WHERE c.userId = @user_id AND c.projectId = @project_id AND c.type = @type AND IS_DEFINED(c.work_items) AND ARRAY_LENGTH(c.work_items) > 0 AND NOT STARTSWITH(c.id, @submission_prefix)',
                [
                    {"name": "@user_id", "value": user_id},
                    {"name": "@project_id", "value": project_id},
                    {"name": "@type", "value": "user_story"},
                    {"name": "@submission_prefix", "value": "user_story_submission_"}
                ]
            )
            
            print(f"🔍 Query parameters: user_id={user_id}, project_id={project_id}, type=user_story")
            print(f"🔍 Found user stories: {len(user_stories)}")
            
            # If no user stories found, try with alternative user ID formats
            if len(user_stories) == 0:
                print(f"🔍 No user stories found with user_id={user_id}, trying alternative formats...")
                
                # Try with double "user_" prefix
                alt_user_id = f"user_{user_id}" if not user_id.startswith("user_user_") else user_id
                print(f"🔍 Trying with alternative user_id: {alt_user_id}")
                
                user_stories = cosmos_service.query_items(
                    'user_stories',
                    'SELECT * FROM c WHERE c.userId = @user_id AND c.projectId = @project_id AND c.type = @type AND IS_DEFINED(c.work_items) AND ARRAY_LENGTH(c.work_items) > 0 AND NOT STARTSWITH(c.id, @submission_prefix)',
                    [
                        {"name": "@user_id", "value": alt_user_id},
                        {"name": "@project_id", "value": project_id},
                        {"name": "@type", "value": "user_story"},
                        {"name": "@submission_prefix", "value": "user_story_submission_"}
                    ]
                )
                print(f"🔍 Found user stories with alternative user_id: {len(user_stories)}")
            
            for story in user_stories:
                print(f"🔍 User story: {story.get('id')}, userId: {story.get('userId')}, type: {story.get('type')}, work_items: {len(story.get('work_items', []))}")
                # Check if any work items match the successful submissions
                work_items = story.get('work_items', [])
                for item in work_items:
                    if item.get('id') in [r.get('story_id') for r in results if r.get('success')]:
                        print(f"🔍 Found matching work item: {item.get('id')} - {item.get('title')}")
            
            if not user_stories:
                print("🔍 No user story collections found to update")
                return []
            
            print(f"🔍 Found {len(user_stories)} user story collections to check for updates")
            
            # Create a mapping of work item IDs to submission results
            successful_submissions = {}
            for result in results:
                if result.get('success') and not result.get('skipped'):
                    # The story_id in the result is actually the work item ID from the frontend
                    work_item_id = result.get('story_id')
                    if work_item_id:
                        successful_submissions[work_item_id] = result
            
            if not successful_submissions:
                print("🔍 No successful submissions to update")
                return user_stories
            
            print(f"🔍 Updating {len(successful_submissions)} work items with submission status")
            print(f"🔍 Successful submissions: {successful_submissions}")
            
            # Update each user story that has successfully submitted work items
            updated_user_stories = []
            for user_story in user_stories:
                work_items = user_story.get('work_items', [])
                print(f"🔍 Processing user story {user_story.get('id')} with {len(work_items)} work items")
                print(f"🔍 Original work items: {[item.get('id') for item in work_items]}")
                
                updated_work_items = []
                story_updated = False
                
                for work_item in work_items:
                    work_item_id = work_item.get('id')
                    print(f"🔍 Checking work item {work_item_id} against successful submissions")
                    print(f"🔍 Successful submissions keys: {list(successful_submissions.keys())}")
                    
                    if work_item_id in successful_submissions:
                        # Mark this work item as submitted
                        work_item['submitted'] = True
                        work_item['submitted_at'] = datetime.now().isoformat()
                        work_item['submitted_to'] = successful_submissions[work_item_id].get('platform', 'unknown')
                        if successful_submissions[work_item_id].get('work_item_id'):
                            work_item['external_work_item_id'] = successful_submissions[work_item_id]['work_item_id']
                        if successful_submissions[work_item_id].get('url'):
                            work_item['external_url'] = successful_submissions[work_item_id]['url']
                        story_updated = True
                        print(f"✅ Marked work item {work_item_id} as submitted")
                        print(f"✅ Work item details: {work_item}")
                    else:
                        print(f"🔍 Work item {work_item_id} not in successful submissions")
                    
                    updated_work_items.append(work_item)
                
                print(f"🔍 Story updated: {story_updated}")
                print(f"🔍 Updated work items count: {len(updated_work_items)}")
                
                # Update the user story if any work items were submitted
                if story_updated:
                    print(f"🔍 About to patch user story {user_story.get('id')} with work items: {[item.get('id') for item in updated_work_items]}")
                    print(f"🔍 Submitted work items: {[item.get('id') for item in updated_work_items if item.get('submitted')]}")
                    
                    # Create patch operations for Cosmos DB
                    try:
                        # Use the userId as partition key (Cosmos DB partition key)
                        partition_key = user_story.get('userId')
                        
                        # Create patch operations to update work_items and last_submitted_at
                        patch_operations = [
                            {
                                "op": "set",
                                "path": "/work_items",
                                "value": updated_work_items
                            },
                            {
                                "op": "set", 
                                "path": "/last_submitted_at",
                                "value": datetime.now().isoformat()
                            }
                        ]
                        
                        patched_doc = cosmos_service.patch_user_story(user_story.get('id'), partition_key, patch_operations)
                        if patched_doc:
                            print(f"✅ Successfully patched user story {user_story.get('id')} with submission status")
                            print(f"✅ Patched document ID: {patched_doc.get('id')}")
                            # Update the local user_story object with the patched data
                            user_story['work_items'] = updated_work_items
                            user_story['last_submitted_at'] = datetime.now().isoformat()
                            updated_user_stories.append(user_story)
                        else:
                            print(f"⚠️ Failed to patch user story {user_story.get('id')} - patch_user_story returned None")
                    except Exception as patch_error:
                        print(f"❌ Error patching user story {user_story.get('id')}: {patch_error}")
                        import traceback
                        print(f"❌ Full traceback: {traceback.format_exc()}")
                else:
                    print(f"🔍 No work items updated in user story {user_story.get('id')}")
            
            print(f"🔍 Returning {len(updated_user_stories)} updated user stories")
            return updated_user_stories
            
        except Exception as e:
            print(f"❌ Error updating user stories submission status: {e}")
            # Don't fail the entire submission if this update fails
            return []
    
    async def _submit_to_azure_devops(self, items, project_config, process_template):
        """Submit work items to Azure DevOps"""
        try:
            import httpx
            from integrations.service import IntegrationsService
            from integrations.encryption import decrypt_token
            
            # Get Azure DevOps configuration from project config first
            azure_config = project_config.get('azure_config', {})
            organization = azure_config.get('organization')
            project_name = azure_config.get('project')
            pat_token = azure_config.get('pat_token')
            
            # If configuration is missing, try to get it from integration account
            if not all([organization, project_name, pat_token]):
                print("🔍 Azure DevOps configuration missing from project, attempting to fetch from integration account...")
                
                # Get integration account ID from project's external links
                external_links = project_config.get('externalLinks', [])
                print(f"🔍 External links: {external_links}")
                
                azure_link = None
                for link in external_links:
                    print(f"🔍 Checking link: {link}")
                    if link.get('provider') == 'azure':
                        azure_link = link
                        print(f"🔍 Found Azure link: {azure_link}")
                        break
                
                if azure_link and azure_link.get('integrationAccountId'):
                    integration_account_id = azure_link['integrationAccountId']
                    print(f"🔍 Found Azure integration account ID: {integration_account_id}")
                    
                    try:
                        # Get the user ID from the project
                        user_id = project_config.get('userId')
                        print(f"🔍 Project user ID: {user_id}")
                        
                        if not user_id:
                            print("❌ No user ID found in project config")
                            return [{
                                "success": False,
                                "error": "Missing user ID in project configuration"
                            }]
                        
                        # Get integration service and fetch decrypted credentials
                        integrations_service = IntegrationsService()
                        print(f"🔍 Fetching Azure integration credentials for user: {user_id}")
                        
                        account_with_creds = integrations_service.get_decrypted_credentials(user_id, 'azure')
                        print(f"🔍 Integration account result: {account_with_creds is not None}")
                        
                        if account_with_creds:
                            print("✅ Successfully retrieved Azure credentials from integration account")
                            print(f"🔍 Account metadata: {account_with_creds.get('metadata', {})}")
                            print(f"🔍 Account credentials keys: {list(account_with_creds.get('credentials', {}).keys())}")
                            
                            organization = account_with_creds['metadata']['organization']
                            pat_token = account_with_creds['credentials']['pat_token']
                            
                            # Get project name from the external link
                            project_name = azure_link.get('externalId')
                            
                            print(f"🔍 Retrieved config - Organization: {organization}, Project: {project_name}")
                        else:
                            print("❌ Failed to retrieve integration account credentials")
                            return [{
                                "success": False,
                                "error": "Failed to retrieve Azure integration credentials"
                            }]
                            
                    except Exception as e:
                        print(f"❌ Error fetching integration credentials: {e}")
                        import traceback
                        print(f"❌ Traceback: {traceback.format_exc()}")
                        return [{
                            "success": False,
                            "error": f"Failed to fetch Azure integration configuration: {str(e)}"
                        }]
                else:
                    print("❌ No Azure integration account found in project external links")
                    print(f"❌ Azure link found: {azure_link is not None}")
                    if azure_link:
                        print(f"❌ Azure link integrationAccountId: {azure_link.get('integrationAccountId')}")
                    
                    # Try to get Azure integration directly by user ID as fallback
                    try:
                        user_id = project_config.get('userId')
                        if user_id:
                            print(f"🔍 Trying fallback: get Azure integration directly for user: {user_id}")
                            integrations_service = IntegrationsService()
                            account_with_creds = integrations_service.get_decrypted_credentials(user_id, 'azure')
                            
                            if account_with_creds:
                                print("✅ Fallback successful: Found Azure integration by user ID")
                                organization = account_with_creds['metadata']['organization']
                                pat_token = account_with_creds['credentials']['pat_token']
                                
                                # Try to get project name from project config or use a default
                                project_name = project_config.get('name', 'Default Project')
                                print(f"🔍 Fallback config - Organization: {organization}, Project: {project_name}")
                            else:
                                print("❌ Fallback failed: No Azure integration found for user")
                                return [{
                                    "success": False,
                                    "error": "No Azure DevOps integration found for this user. Please configure Azure DevOps integration first."
                                }]
                        else:
                            return [{
                                "success": False,
                                "error": "Missing user ID in project configuration"
                            }]
                    except Exception as e:
                        print(f"❌ Fallback error: {e}")
                        return [{
                            "success": False,
                            "error": f"Missing Azure DevOps configuration and no integration account found. Error: {str(e)}"
                        }]
            
            # Final validation
            if not all([organization, project_name, pat_token]):
                return [{
                    "success": False,
                    "error": "Missing Azure DevOps configuration (organization, project, or PAT token)"
                }]
            
            # Azure DevOps requires PAT token to be base64 encoded with empty username
            import base64
            auth_string = f":{pat_token}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_auth}',
                'Content-Type': 'application/json-patch+json'
            }
            
            results = []
            
            async with httpx.AsyncClient(timeout=270.0) as client:
                for item in items:
                    try:
                        # Build work item fields
                        fields = [
                            {"op": "add", "path": "/fields/System.Title", "value": item["title"]},
                            {"op": "add", "path": "/fields/System.Description", "value": item["description"]},
                            {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": item["priority"]}
                        ]
                        
                        # Add optional fields
                        if item.get("tags"):
                            fields.append({"op": "add", "path": "/fields/System.Tags", "value": item["tags"]})
                        
                        if item.get("acceptance_criteria"):
                            fields.append({
                                "op": "add", 
                                "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria", 
                                "value": item["acceptance_criteria"]
                            })
                        
                        if item.get("business_value"):
                            fields.append({
                                "op": "add",
                                "path": "/fields/Microsoft.VSTS.Common.BusinessValue",
                                "value": item["business_value"]
                            })
                        
                        # Create work item
                        url = f"https://dev.azure.com/{organization}/{project_name}/_apis/wit/workitems/${item['work_item_type']}?api-version=7.0"
                        
                        print(f"🔍 Azure DevOps API call:")
                        print(f"🔍 URL: {url}")
                        print(f"🔍 Headers: {headers}")
                        print(f"🔍 Fields: {fields}")
                        
                        response = await client.post(url, headers=headers, json=fields)
                        
                        print(f"🔍 Response status: {response.status_code}")
                        print(f"🔍 Response headers: {dict(response.headers)}")
                        if response.status_code not in [200, 201]:
                            print(f"🔍 Response text: {response.text[:500]}...")
                        
                        if response.status_code in [200, 201]:
                            work_item_data = response.json()
                            results.append({
                                "success": True,
                                "story_id": item["original_story_id"],
                                "work_item_id": work_item_data.get("id"),
                                "url": work_item_data.get("_links", {}).get("html", {}).get("href"),
                                "title": item["title"]
                            })
                        else:
                            error_message = f"Azure DevOps API error: {response.status_code}"
                            if response.status_code == 302:
                                error_message = "Azure DevOps authentication failed. Please check your PAT token permissions and validity."
                            elif response.status_code == 401:
                                error_message = "Azure DevOps authentication failed. Invalid PAT token."
                            elif response.status_code == 403:
                                error_message = "Azure DevOps access denied. PAT token doesn't have required permissions."
                            elif response.status_code == 404:
                                error_message = "Azure DevOps project or organization not found. Please check the project name and organization."
                            
                            results.append({
                                "success": False,
                                "story_id": item["original_story_id"],
                                "error": error_message,
                                "details": response.text[:1000] if response.text else "No details available",
                                "title": item["title"]
                            })
                            
                    except Exception as e:
                        results.append({
                            "success": False,
                            "story_id": item["original_story_id"],
                            "error": str(e),
                            "title": item.get("title", "Unknown")
                        })
            
            return results
            
        except Exception as e:
            return [{
                "success": False,
                "error": f"Azure DevOps submission failed: {str(e)}"
            }]
    
    async def _submit_to_jira(self, items, project_config):
        """Submit issues to Jira"""
        try:
            import httpx
            import base64
            from integrations.service import IntegrationsService
            from integrations.encryption import decrypt_token
            
            # Get Jira configuration from project config first
            jira_config = project_config.get('jira_config', {})
            domain = jira_config.get('domain')
            email = jira_config.get('email')
            api_token = jira_config.get('api_token')
            project_key = jira_config.get('project_key')
            
            # If configuration is missing, try to get it from integration account
            if not all([domain, email, api_token, project_key]):
                print("🔍 Jira configuration missing from project, attempting to fetch from integration account...")
                
                # Get integration account ID from project's external links
                external_links = project_config.get('externalLinks', [])
                jira_link = None
                for link in external_links:
                    if link.get('provider') == 'jira':
                        jira_link = link
                        break
                
                if jira_link and jira_link.get('integrationAccountId'):
                    integration_account_id = jira_link['integrationAccountId']
                    print(f"🔍 Found Jira integration account ID: {integration_account_id}")
                    
                    try:
                        # Get the user ID from the project
                        user_id = project_config.get('userId')
                        if not user_id:
                            print("❌ No user ID found in project config")
                            return [{
                                "success": False,
                                "error": "Missing user ID in project configuration"
                            }]
                        
                        # Get integration service and fetch decrypted credentials
                        integrations_service = IntegrationsService()
                        account_with_creds = integrations_service.get_decrypted_credentials(user_id, 'jira')
                        
                        if account_with_creds:
                            print("✅ Successfully retrieved Jira credentials from integration account")
                            domain = account_with_creds['metadata']['domain']
                            email = account_with_creds['metadata']['email']
                            api_token = account_with_creds['credentials']['api_token']
                            
                            # Get project key from the external link
                            project_key = jira_link.get('externalKey')
                            
                            print(f"🔍 Retrieved config - Domain: {domain}, Email: {email}, Project Key: {project_key}")
                        else:
                            print("❌ Failed to retrieve integration account credentials")
                            return [{
                                "success": False,
                                "error": "Failed to retrieve Jira integration credentials"
                            }]
                            
                    except Exception as e:
                        print(f"❌ Error fetching integration credentials: {e}")
                        return [{
                            "success": False,
                            "error": f"Failed to fetch Jira integration configuration: {str(e)}"
                        }]
                else:
                    print("❌ No Jira integration account found in project external links")
                    
                    # Try to get Jira integration directly by user ID as fallback
                    try:
                        user_id = project_config.get('userId')
                        if user_id:
                            print(f"🔍 Trying fallback: get Jira integration directly for user: {user_id}")
                            integrations_service = IntegrationsService()
                            account_with_creds = integrations_service.get_decrypted_credentials(user_id, 'jira')
                            
                            if account_with_creds:
                                print("✅ Fallback successful: Found Jira integration by user ID")
                                domain = account_with_creds['metadata']['domain']
                                email = account_with_creds['metadata']['email']
                                api_token = account_with_creds['credentials']['api_token']
                                
                                # Try to get project key from project config or use a default
                                project_key = project_config.get('name', 'DEFAULT').upper()[:10]  # Use project name as key
                                print(f"🔍 Fallback config - Domain: {domain}, Email: {email}, Project Key: {project_key}")
                            else:
                                print("❌ Fallback failed: No Jira integration found for user")
                                return [{
                                    "success": False,
                                    "error": "No Jira integration found for this user. Please configure Jira integration first."
                                }]
                        else:
                            return [{
                                "success": False,
                                "error": "Missing user ID in project configuration"
                            }]
                    except Exception as e:
                        print(f"❌ Fallback error: {e}")
                        return [{
                            "success": False,
                            "error": f"Missing Jira configuration and no integration account found. Error: {str(e)}"
                        }]
            
            # Final validation
            if not all([domain, email, api_token, project_key]):
                return [{
                    "success": False,
                    "error": "Missing Jira configuration (domain, email, api_token, or project_key)"
                }]
            
            # Create auth header
            auth_token = base64.b64encode(f"{email}:{api_token}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            results = []
            
            async with httpx.AsyncClient(timeout=270.0) as client:
                for item in items:
                    try:
                        # Build description with additional fields
                        full_description = item["description"]
                        if item.get("acceptance_criteria"):
                            full_description += f"\n\n**Acceptance Criteria:**\n{item['acceptance_criteria']}"
                        if item.get("business_value"):
                            full_description += f"\n\n**Business Value:**\n{item['business_value']}"
                        
                        # Convert to ADF format
                        description_adf = {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": full_description
                                        }
                                    ]
                                }
                            ]
                        }
                        
                        # Build Jira issue payload
                        payload = {
                            "fields": {
                                "project": {"key": project_key},
                                "summary": item["title"],
                                "description": description_adf,
                                "issuetype": {"name": item["type"]},
                                "labels": item.get("labels", [])
                            }
                        }
                        
                        # Skip priority field - this Jira project doesn't support priority for any issue type
                        # Note: Priority field is not available in this Jira project configuration
                        
                        # Create issue
                        url = f"https://{domain}/rest/api/3/issue"
                        print(f"🌐 Making Jira API request to: {url}")
                        print(f"📦 Jira payload: {json.dumps(payload, indent=2)}")
                        
                        response = await client.post(url, headers=headers, json=payload)
                        
                        print(f"📊 Jira API response status: {response.status_code}")
                        print(f"📄 Jira API response text: {response.text}")
                        
                        if response.status_code in [200, 201]:
                            issue_data = response.json()
                            print(f"✅ Jira issue created successfully: {issue_data.get('key')}")
                            results.append({
                                "success": True,
                                "story_id": item["original_story_id"],
                                "issue_id": issue_data.get("id"),
                                "issue_key": issue_data.get("key"),
                                "url": f"https://{domain}/browse/{issue_data.get('key', '')}",
                                "title": item["title"]
                            })
                        else:
                            print(f"❌ Jira API error: {response.status_code}")
                            print(f"❌ Jira error details: {response.text}")
                            results.append({
                                "success": False,
                                "story_id": item["original_story_id"],
                                "error": f"Jira API error: {response.status_code}",
                                "details": response.text,
                                "title": item["title"]
                            })
                            
                    except Exception as e:
                        results.append({
                            "success": False,
                            "story_id": item["original_story_id"],
                            "error": str(e),
                            "title": item.get("title", "Unknown")
                        })
            
            return results
            
        except Exception as e:
            return [{
                "success": False,
                "error": f"Jira submission failed: {str(e)}"
            }]