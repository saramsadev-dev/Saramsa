from celery import shared_task
import asyncio
from asgiref.sync import async_to_sync
from .processor import process_feedback
from aiCore.aiCompletions import generate_completions
from aiCore.cosmos_service import cosmos_service
from .prompts import getSentAnalysisPrompt
import logging
import json
import uuid
from datetime import datetime

logger = logging.getLogger("apis.app")

@shared_task(name="insightsGenerator.tasks.process_feedback_task")
def process_feedback_task(comments, company_name, user_id_str, project_id):
    """
    Background task to process user feedback using LLM, normalize, and save.
    """
    logger.info(f"📈 Background task started: feedback analysis for project {project_id}")
    
    try:
        # 1. Prepare Prompt
        prompt = getSentAnalysisPrompt(company_name=company_name)
        feedback_block = "\n".join([str(c) for c in comments])
        prompt_filled = prompt.replace("<feedback_data>", feedback_block)
        
        # 2. Call LLM (generate_completions is usually sync or async-wrapped)
        # Assuming it's the one from aiCore.aiCompletions
        result = async_to_sync(generate_completions)(prompt_filled)

        # 3. Normalize
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
            try: return float(v)
            except:
                try: return int(v)
                except: return 0

        features_norm = []
        for f in features_input:
            if not isinstance(f, dict): continue
            name = f.get('feature') or f.get('name')
            if not name: continue
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

        # 4. Save to Cosmos DB (Simulating what View was doing)
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
        
        cosmos_service.save_analysis_data(insight_data)
        logger.info(f"Analysis saved to Cosmos DB for task {process_feedback_task.request.id}")
        
        return {"insight_id": insight_id, "result": normalized}

    except Exception as e:
        logger.error(f" Error in feedback analysis task: {str(e)}")
        raise
