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

from aiCore.services.completion_service import generate_completions
from authentication.permissions import IsAdminOrUser
from apis.core.response import StandardResponse
from apis.core.error_handlers import handle_service_errors
from celery.result import AsyncResult

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

        # Get user info and project context
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else "anonymous"
        user_id_str = str(user_id)
        
        analysis_service = get_analysis_service()
        
        company_name = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_data = analysis_service.get_user_by_username(request.user.username)
                if user_data:
                    company_name = user_data.get('company_name')
            except Exception as e:
                logger.warning(f"Could not get company_name for user: {e}")

        project_id, _, _ = analysis_service.ensure_project_context(
            incoming_project_id,
            user_id_str,
        )
        
        # Trigger background task
        task = process_feedback_task.delay(comments, company_name, user_id_str, project_id)
        
        response = StandardResponse.success(
            data={
                "task_id": task.id,
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

        # Save updated analysis to service layer
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
        Get user comments for a specific project
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
        user_data = analysis_service.get_user_data_by_project(user_id_str, project_id)
        
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


class TaskStatusView(APIView):
    """View to check the status of a Celery task"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request, task_id):
        res = AsyncResult(task_id)
        response_data = {
            "task_id": task_id,
            "status": res.status,  # PENDING, STARTED, SUCCESS, FAILURE
            "ready": res.ready(),
        }
        
        if res.ready():
            if res.successful():
                response_data["result"] = res.result
            else:
                response_data["error"] = str(res.result)
                
        return StandardResponse.success(data=response_data)

