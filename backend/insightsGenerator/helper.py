from rest_framework.response import Response
from rest_framework import status
from aiCore.aiCompletions import generate_completions 
from aiCore.cosmos_service import cosmos_service
from .prompts import getSentAnalysisPrompt, getDeepAnalysisPrompt
from datetime import datetime
import json
import uuid

async def getSentimentAnalysis(comments):
        if not comments or not isinstance(comments, list):
            return Response(
                {"error": "A list of comments is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            print (len(comments))
            prompt = getSentAnalysisPrompt(comments)
            print (prompt)
            print ("Starting...")
            result = await generate_completions(prompt)
            
            # Save insight to Cosmos DB
            try:
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
                
                saved_analysis = cosmos_service.save_analysis_data(insight_data)
                if saved_analysis:
                    print(f"Analysis saved to Cosmos DB with ID: {saved_analysis.get('id')}")
            except Exception as e:
                print(f"Error saving insight to Cosmos DB: {e}")
            
            formatted = {
                "success": True,
                "data": result,
                "analysis_date": datetime.now().isoformat()
            }
            return result
        except Exception as e:
            return {"error": str(e)}
        
def flattenComments(comments):
    dataText = []
    for comment in comments:
        dataText.append(comment["text"])
    return json.dumps(dataText)