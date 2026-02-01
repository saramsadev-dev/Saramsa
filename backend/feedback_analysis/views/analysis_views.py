"""
Analysis views for feedback analysis.

Contains views for analysis operations:
- AnalyzeCommentsView: Start background analysis task
- UpdateKeywordsView: Update keywords and regenerate analysis
- GetUserCommentsView: Get user comments for regeneration
- TaskStatusView: Check Celery task status
"""

from rest_framework.views import APIView
from rest_framework import status
from asgiref.sync import async_to_sync
from datetime import datetime
import json
import uuid
import logging
import os

from aiCore.services.completion_service import generate_completions
from authentication.permissions import IsAdminOrUser
from apis.core.response import StandardResponse
from apis.core.error_handlers import handle_service_errors
from celery.result import AsyncResult
from apis.infrastructure.cache_service import get_cache_service

from apis.prompts import getSentAnalysisPrompt
from ..services import get_task_service
from ..services.task_service import process_feedback_task
from ..services import get_analysis_service

logger = logging.getLogger(__name__)


class AnalyzeCommentsView(APIView):
    permission_classes = [IsAdminOrUser]
    
    @handle_service_errors
    def post(self, request):
        logger.info("AnalyzeCommentsView called (Background Mode)")
        
        comments = request.data.get("comments")
        incoming_project_id = request.data.get("project_id")

        if not comments or not isinstance(comments, list):
            return StandardResponse.validation_error(
                detail="A list of comments is required.",
                errors=[{"field": "comments", "message": "This field must be a list."}],
                instance=request.path
            )
        max_comments = int(os.getenv("MAX_COMMENTS_PER_ANALYSIS", "50000"))
        if len(comments) > max_comments:
            return StandardResponse.validation_error(
                detail=f"Too many comments for one analysis (max {max_comments}).",
                errors=[{"field": "comments", "message": "Max comments per analysis exceeded."}],
                instance=request.path
            )

        # Get user info and project context
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else "anonymous"
        user_id_str = str(user_id)
        
        # Validate project ID is provided
        if not incoming_project_id:
            return StandardResponse.validation_error(
                detail="Project ID is required. Please select or create a project first.",
                errors=[{"field": "project_id", "message": "This field is required."}],
                instance=request.path
            )
        
        analysis_service = get_analysis_service()
        from ..services import get_taxonomy_service
        
        company_name = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_data = analysis_service.get_user_by_username(request.user.username)
                if user_data:
                    company_name = user_data.get('company_name')
            except Exception as e:
                logger.warning(f"Could not get company_name for user: {e}")

        try:
            project_id, _, _ = analysis_service.ensure_project_context(
                incoming_project_id,
                user_id_str,
            )
        except ValueError as e:
            return StandardResponse.validation_error(
                detail=str(e),
                errors=[{"field": "project_id", "message": str(e)}],
                instance=request.path
            )
        
        # Generate idempotency key for analysis
        analysis_id = str(uuid.uuid4())

        # Track task start for TTL safeguards
        cache = get_cache_service()

        # Trigger background task
        task = process_feedback_task.delay(comments, company_name, user_id_str, project_id, analysis_id)
        cache.set(f"task_start:{task.id}", datetime.now().isoformat(), ttl=3600)
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        cache.incr(f"analyses_hour:{project_id}:{hour_key}", 1, ttl=3600)
        
        response = StandardResponse.success(
            data={
                "task_id": task.id,
                "analysis_id": analysis_id,
                "message": "Analysis started in background.",
                "status": "processing"
            }
        )
        response.status_code = status.HTTP_202_ACCEPTED
        return response


class UpdateKeywordsView(APIView):
    permission_classes = [IsAdminOrUser]
    
    @handle_service_errors
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

        analysis_service = get_analysis_service()
        
        project_id, project_doc, is_draft = analysis_service.ensure_project_context(
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
                user_data = analysis_service.get_user_by_username(request.user.username)
                if user_data:
                    company_name = user_data.get('company_name')
            except Exception as e:
                logger.warning(f"Could not get company_name for user: {e}")
        
        # Add keyword context to the feedback data
        keyword_context = "UPDATED KEYWORDS:\n"
        for feature_name, keywords in updated_keywords.items():
            keyword_context += f"{feature_name}: {', '.join(keywords)}\n"
        
        # Build feedback data with keyword context
        feedback_data = f"{keyword_context}\n\nFEEDBACK DATA:\n" + "\n".join([str(c) for c in comments])
        
        # Create prompt using structured system
        prompt = getSentAnalysisPrompt(company_name=company_name, feedback_data=feedback_data)
        
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

        # Resolve taxonomy for versioned linkage (Phase-1)
        taxonomy_service = get_taxonomy_service()
        taxonomy = taxonomy_service.get_active_taxonomy(project_id, comments=None)
        if not taxonomy and updated_keywords:
            taxonomy = taxonomy_service.create_initial_taxonomy(
                project_id,
                list(updated_keywords.keys()),
                source="user"
            )

        # Save updated analysis to service layer
        try:
            analysis_id = str(uuid.uuid4())
            analysis_data = {
                'id': f'analysis_{analysis_id}',
                'projectId': project_id,
                'userId': user_id_str,
                'taxonomy_id': taxonomy.get('taxonomy_id') if taxonomy else None,
                'taxonomy_version': taxonomy.get('version') if taxonomy else None,
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
            
            saved_analysis = analysis_service.save_analysis_data(analysis_data)
            if saved_analysis:
                analysis_service.update_project_last_analysis(project_id, saved_analysis['id'])
        except Exception as e:
            logger.error(f"Error saving updated analysis: {e}")

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


class GetUserCommentsView(APIView):
    """Get user comments for regeneration"""
    permission_classes = [IsAdminOrUser]
    
    @handle_service_errors
    def get(self, request):
        """
        Get user comments for a specific project - Updated to get from analysis data
        """
        analysis_service = get_analysis_service()
        
        project_id = request.query_params.get('project_id')
        is_personal_param = request.query_params.get('is_personal')
        explicit_personal = str(is_personal_param).lower() in ('true', '1', 'yes')
        
        # Get user ID from request
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        if not user_id:
            return StandardResponse.unauthorized(detail="User authentication required.", instance=request.path)
        user_id_str = str(user_id)
        
        # Try to get comments from analysis data first
        if project_id and not explicit_personal:
            logger.info(f"DEBUG: Starting analysis data lookup for project {project_id}, user {user_id_str}")
            
            # Check if there's a recent analysis ID in the request or session
            recent_analysis_id = request.query_params.get('analysis_id')
            
            try:
                # COMPREHENSIVE DEBUG: Check what analysis documents exist
                logger.info("STEP 1: Checking all analysis documents for this user...")
                try:
                    analysis_service = get_analysis_service()
                    
                    # Use the existing analysis service to check documents
                    debug_results = analysis_service.analysis_repo.cosmos_service.query_documents(
                        'analysis', 
                        "SELECT * FROM c WHERE c.userId = @user_id ORDER BY c.createdAt DESC",
                        [{"name": "@user_id", "value": user_id_str}]
                    )
                    logger.info(f"Found {len(debug_results)} total analysis documents for user {user_id_str}")
                    
                    # Log details of each document
                    for i, doc in enumerate(debug_results[:5]):  # Log first 5 documents
                        logger.info(f"Document {i+1}: id={doc.get('id')}, projectId={doc.get('projectId')}, type={doc.get('type')}, createdAt={doc.get('createdAt')}")
                        logger.info(f"  - Has original_comments: {bool(doc.get('original_comments'))}")
                        logger.info(f"  - Has feedback: {bool(doc.get('feedback'))}")
                        if doc.get('original_comments'):
                            logger.info(f"  - original_comments count: {len(doc.get('original_comments', []))}")
                        if doc.get('feedback'):
                            logger.info(f"  - feedback count: {len(doc.get('feedback', []))}")
                    
                    # Check specifically for this project
                    project_results = analysis_service.analysis_repo.cosmos_service.query_documents(
                        'analysis',
                        "SELECT * FROM c WHERE c.userId = @user_id AND c.projectId = @project_id ORDER BY c.createdAt DESC",
                        [
                            {"name": "@user_id", "value": user_id_str},
                            {"name": "@project_id", "value": project_id}
                        ]
                    )
                    logger.info(f"Found {len(project_results)} analysis documents for project {project_id}")
                    
                except Exception as debug_e:
                    logger.error(f"DEBUG query failed: {debug_e}")
                
                logger.info("STEP 2: Attempting to get analysis data using service method...")
                
                # If we have a specific analysis ID, try to get that first
                if recent_analysis_id:
                    logger.info(f"Looking for specific analysis ID: {recent_analysis_id}")
                    try:
                        specific_analysis = analysis_service.get_analysis_by_id(recent_analysis_id, user_id_str)
                        if specific_analysis:
                            analysis_data = specific_analysis
                            logger.info("Found specific analysis by ID")
                        else:
                            logger.info("Specific analysis ID not found, falling back to latest")
                            analysis_data = analysis_service.get_latest_analysis_by_project(project_id, user_id_str)
                    except Exception as e:
                        logger.warning(f"Error getting specific analysis: {e}")
                        analysis_data = analysis_service.get_latest_analysis_by_project(project_id, user_id_str)
                else:
                    # Get latest analysis for the project
                    analysis_data = analysis_service.get_latest_analysis_by_project(project_id, user_id_str)
                
                logger.info(f"Analysis data result: {analysis_data is not None}")
                
                if analysis_data:
                    logger.info(f"Analysis data keys: {list(analysis_data.keys()) if isinstance(analysis_data, dict) else 'Not a dict'}")
                    logger.info(f"Analysis ID: {analysis_data.get('id')}, Created: {analysis_data.get('createdAt')}")
                    
                    # Extract comments from analysis data with comprehensive search
                    comments = []
                    source_field = None
                    
                    # Check all possible locations for comments
                    comment_sources = [
                        ('original_comments', analysis_data.get('original_comments')),
                        ('feedback', analysis_data.get('feedback')),
                        ('analysisData.original_comments', analysis_data.get('analysisData', {}).get('original_comments')),
                        ('analysisData.feedback', analysis_data.get('analysisData', {}).get('feedback')),
                        ('result.original_comments', analysis_data.get('result', {}).get('original_comments')),
                        ('result.feedback', analysis_data.get('result', {}).get('feedback'))
                    ]
                    
                    for field_name, field_value in comment_sources:
                        if field_value and isinstance(field_value, list) and len(field_value) > 0:
                            # Filter out empty strings and clean the data
                            cleaned_comments = [str(comment).strip().strip('"') for comment in field_value if comment and str(comment).strip() and str(comment).strip() != '""']
                            if cleaned_comments:
                                comments = cleaned_comments
                                source_field = field_name
                                logger.info(f"Found {len(comments)} valid comments in '{field_name}' (after cleaning)")
                                break
                    
                    if comments:
                        return StandardResponse.success(data={
                            "success": True,
                            "comments": comments,
                            "comments_count": len(comments),
                            "file_name": analysis_data.get('file_name'),
                            "upload_date": analysis_data.get('createdAt') or analysis_data.get('analysis_date'),
                            "is_personal": False,
                            "project_id": project_id,
                            "source": "analysis_data",
                            "source_field": source_field,
                            "analysis_id": analysis_data.get('id')
                        }, message="Comments retrieved from analysis data")
                    else:
                        logger.warning("Analysis data found but no valid comments in any expected field")
                        logger.info(f"Available fields: {list(analysis_data.keys())}")
                        # Log a sample of the data structure for debugging
                        if 'analysisData' in analysis_data:
                            logger.info(f"analysisData keys: {list(analysis_data['analysisData'].keys())}")
                        if 'result' in analysis_data:
                            logger.info(f"result keys: {list(analysis_data['result'].keys())}")
                        
                        # Return empty result with helpful message
                        return StandardResponse.success(data={
                            "success": True,
                            "comments": [],
                            "comments_count": 0,
                            "file_name": analysis_data.get('file_name'),
                            "upload_date": analysis_data.get('createdAt') or analysis_data.get('analysis_date'),
                            "is_personal": False,
                            "project_id": project_id,
                            "source": "analysis_data",
                            "message": "Analysis found but no comments available. Please upload a feedback file first.",
                            "error_type": "no_comments_in_analysis",
                            "analysis_id": analysis_data.get('id')
                        }, message="Analysis found but no comments available")
                else:
                    logger.info("No analysis data found")
                    # Return helpful message when no analysis is found
                    return StandardResponse.success(data={
                        "success": True,
                        "comments": [],
                        "comments_count": 0,
                        "file_name": None,
                        "upload_date": None,
                        "is_personal": False,
                        "project_id": project_id,
                        "source": "analysis_data",
                        "message": "No analysis found for this project. Please upload a feedback file or run an analysis first.",
                        "error_type": "no_analysis_found"
                    }, message="No analysis found for this project")
            except Exception as e:
                logger.error(f"Error getting comments from analysis data: {e}", exc_info=True)
        
        # Fallback to original logic for user data
        if not project_id or explicit_personal:
            # Fall back to personal data when project not supplied
            personal_data = analysis_service.get_latest_personal_user_data(user_id_str)
            if not personal_data:
                return StandardResponse.success(data={
                    "success": True,
                    "comments": [],
                    "comments_count": 0,
                    "file_name": None,
                    "upload_date": None,
                    "message": "No comments found. Please upload a feedback file or run an analysis first.",
                    "is_personal": True,
                    "error_type": "no_data_available"
                }, message="No comments available - please upload data first")

            return StandardResponse.success(data={
                "success": True,
                "comments": personal_data.get('feedback', []),
                "comments_count": len(personal_data.get('feedback', [])),
                "file_name": personal_data.get('file_name'),
                "upload_date": personal_data.get('uploaded_date'),
                "is_personal": True,
                "project_id": personal_data.get('project_id'),
                "source": "personal_data"
            }, message="Operation completed successfully")

        # Project-specific user data path (original logic)
        user_data = analysis_service.get_user_data_by_project(user_id_str, project_id)
        
        if not user_data:
            return StandardResponse.success(data={
                "success": True,
                "comments": [],
                "comments_count": 0,
                "file_name": None,
                "upload_date": None,
                "message": "No comments found for this project. Please upload a feedback file or run an analysis first.",
                "is_personal": False,
                "project_id": project_id,
                "source": "user_data",
                "error_type": "no_project_data"
            }, message="No comments available for this project - please upload data first")
        
        return StandardResponse.success(data={
            "success": True,
            "comments": user_data.get('feedback', []),
            "comments_count": len(user_data.get('feedback', [])),
            "file_name": user_data.get('file_name'),
            "upload_date": user_data.get('uploaded_date'),
            "is_personal": bool(user_data.get('is_personal')),
            "project_id": project_id,
            "source": "user_data"
        }, message="Operation completed successfully")


class TaskStatusView(APIView):
    """View to check the status of a Celery task"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request, task_id):
        res = AsyncResult(task_id)
        cache = get_cache_service()
        max_runtime = int(os.getenv("ANALYSIS_TASK_MAX_RUNTIME_SECONDS", "1800"))
        started_at = cache.get(f"task_start:{task_id}")
        pipeline_health = cache.get(f"pipeline_health:{task_id}") if cache else None
        elapsed = None
        if started_at:
            try:
                started_dt = datetime.fromisoformat(started_at)
                elapsed = (datetime.now() - started_dt).total_seconds()
            except Exception:
                elapsed = None
        if res.status in ("PENDING", "STARTED") and elapsed is not None and elapsed > max_runtime:
            return StandardResponse.success(data={
                "task_id": task_id,
                "status": "FAILED",
                "ready": False,
                "pipeline_health": {
                    "status": "FAILED",
                    "errors": {"timeout": f"Exceeded max runtime {max_runtime}s"},
                    "started_at": started_at,
                }
            })
        response_data = {
            "task_id": task_id,
            "status": res.status,  # PENDING, STARTED, SUCCESS, FAILURE
            "ready": res.ready(),
        }
        
        if res.ready():
            if res.successful():
                result = res.result or {}
                response_data["result"] = result
                if result.get("pipeline_health"):
                    pipeline_health = result.get("pipeline_health")
                pipeline_status = result.get("pipeline_health", {}).get("status", "COMPLETE")
                if pipeline_status == "DEGRADED":
                    response_data["status"] = "PARTIAL"
                elif pipeline_status in ("COMPLETE", "SUCCESS"):
                    response_data["status"] = "SUCCESS"
                else:
                    response_data["status"] = pipeline_status
            else:
                response_data["error"] = str(res.result)
                response_data["status"] = "FAILED"
        else:
            response_data["status"] = "RUNNING"
        if pipeline_health:
            response_data["pipeline_health"] = pipeline_health
                
        return StandardResponse.success(data=response_data)

