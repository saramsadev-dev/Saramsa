from celery import shared_task
import asyncio
from asgiref.sync import async_to_sync
from .processing_service import get_processing_service
from .analysis_service import get_analysis_service
from aiCore.services.completion_service import generate_completions
from apis.prompts import getSentAnalysisPrompt
import logging
import json
import uuid
from datetime import datetime

logger = logging.getLogger("apis.app")


class TaskService:
    """Service for managing background tasks."""
    
    def __init__(self):
        self.processing_service = get_processing_service()
    
    def process_feedback_background(self, comments, company_name, user_id_str, project_id):
        """
        Process user feedback using LLM, normalize, and save.
        This is the main business logic for background feedback processing.
        """
        logger.info(f"📈 Background task started: feedback analysis for project {project_id}")
        
        try:
            # 1. Prepare Prompt using structured system
            feedback_block = "\n".join([str(c) for c in comments])
            prompt = getSentAnalysisPrompt(company_name=company_name, feedback_data=feedback_block)
            
            # 2. Call LLM (generate_completions is usually sync or async-wrapped)
            result = async_to_sync(generate_completions)(prompt)

            # 3. Normalize the results
            normalized = self._normalize_analysis_result(result)

            # 4. Save to database
            insight_id = str(uuid.uuid4())
            insight_data = {
                'id': f'insight_{insight_id}',
                'type': 'insight',
                'project_id': project_id,
                'user_id': user_id_str,
                'analysis_type': 'sentiment_analysis',
                'analysis_date': datetime.now().isoformat(),
                'result': normalized,
                'status': 'complete'
            }
            
            # Save using analysis service
            analysis_service = get_analysis_service()
            analysis_service.save_analysis_data(insight_data)
            logger.info(f"Analysis saved to Cosmos DB for background task")
            
            return {"insight_id": insight_id, "result": normalized}

        except Exception as e:
            logger.error(f"Error in feedback analysis task: {str(e)}")
            raise
    
    def _normalize_analysis_result(self, result):
        """Normalize LLM analysis result to standard format."""
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
            except:
                try: 
                    return int(v)
                except: 
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

        return {
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


# Global service instance
_task_service = None

def get_task_service():
    """Get the global task service instance."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


# Celery task wrapper - this stays at module level for Celery discovery
@shared_task(name="feedback_analysis.tasks.process_feedback_task")
def process_feedback_task(comments, company_name, user_id_str, project_id):
    """
    Celery background task wrapper for feedback processing.
    Delegates to TaskService for actual business logic.
    """
    task_service = get_task_service()
    return task_service.process_feedback_background(comments, company_name, user_id_str, project_id)