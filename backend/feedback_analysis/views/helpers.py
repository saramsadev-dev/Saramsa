"""
Helper functions for feedback analysis views.

Contains shared utility functions used across different view modules.
"""

from rest_framework.response import Response
from rest_framework import status
from aiCore.services.completion_service import generate_completions 
from apis.prompts import getSentAnalysisPrompt, getDeepAnalysisPrompt
from datetime import datetime
import json
import uuid
import logging

logger = logging.getLogger(__name__)


async def getSentimentAnalysis(comments):
    """
    Perform sentiment analysis on a list of comments.
    
    Args:
        comments (list): List of comment strings to analyze
        
    Returns:
        dict: Analysis result or error response
    """
    if not comments or not isinstance(comments, list):
        return Response(
            {"error": "A list of comments is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        logger.debug(f"Processing {len(comments)} comments for sentiment analysis")
        # Build feedback data from comments
        feedback_data = "\n".join([str(c) for c in comments])
        prompt = getSentAnalysisPrompt(feedback_data=feedback_data)
        logger.debug("Starting sentiment analysis")
        result, _usage = await generate_completions(prompt)
        
        # Save insight using analysis service
        try:
            from ..services import get_analysis_service
            analysis_service = get_analysis_service()
            
            insight_id = str(uuid.uuid4())
            insight_data = {
                'id': f'insight_{insight_id}',
                'type': 'insight',
                'analysis_type': 'sentiment_analysis',
                'comments_count': len(comments),
                'analysis_date': datetime.now().isoformat(),
                'analysis_result': result,
                'metadata': {
                    'source': 'helper_function',
                    'processing_timestamp': datetime.now().isoformat()
                }
            }
            
            saved_analysis = analysis_service.save_analysis_data(insight_data)
            if saved_analysis:
                logger.info(f"Analysis saved to PostgreSQL with ID: {saved_analysis.get('id')}")
        except Exception as e:
            logger.error(f"Error saving insight to PostgreSQL: {e}")
        
        formatted = {
            "success": True,
            "data": result,
            "analysis_date": datetime.now().isoformat()
        }
        return result
    except Exception as e:
        return {"error": str(e)}


def flattenComments(comments):
    """
    Flatten comments data structure to extract text content.
    
    Args:
        comments (list): List of comment objects with 'text' field
        
    Returns:
        str: JSON string of flattened comment texts
    """
    dataText = []
    for comment in comments:
        dataText.append(comment["text"])
    return json.dumps(dataText)
