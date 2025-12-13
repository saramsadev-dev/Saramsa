from datetime import datetime
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from http import HTTPStatus
import json
import csv
import uuid
from asgiref.sync import async_to_sync
from insightsGenerator.processor import process_uploaded_data_async
from authapp.permissions import IsAdminOrUser
from aiCore.cosmos_service import cosmos_service
from apis.response import StandardResponse

@method_decorator(csrf_exempt, name='dispatch')
class AsyncFileUploadView(APIView):
    permission_classes = [IsAdminOrUser]
    
    def extract_comments_from_data(self, data, file_type):
        """Extract comments from uploaded data"""
        comments = []
        
        if file_type == 'json':
            if isinstance(data, list):
                # If data is a list of strings, treat as comments
                comments = [str(item) for item in data if item]
            elif isinstance(data, dict):
                # If data has a comments field
                if 'comments' in data and isinstance(data['comments'], list):
                    comments = [str(comment) for comment in data['comments'] if comment]
                # If data has feedback field
                elif 'feedback' in data and isinstance(data['feedback'], list):
                    comments = [str(feedback) for feedback in data['feedback'] if feedback]
                # If data has reviews field
                elif 'reviews' in data and isinstance(data['reviews'], list):
                    comments = [str(review) for review in data['reviews'] if review]
        
        elif file_type == 'csv':
            if isinstance(data, list) and len(data) > 0:
                # Look for common comment column names
                comment_columns = ['comment', 'comments', 'feedback', 'review', 'reviews', 'text', 'content', 'message']
                first_row = data[0]
                
                # Find the comment column
                comment_column = None
                for col in comment_columns:
                    if col in first_row:
                        comment_column = col
                        break
                
                if comment_column:
                    comments = [str(row[comment_column]) for row in data if row.get(comment_column)]
                else:
                    # Fallback: use the first column
                    first_col = list(first_row.keys())[0] if first_row else None
                    if first_col:
                        comments = [str(row[first_col]) for row in data if row.get(first_col)]
        
        return comments

    @async_to_sync
    async def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        incoming_project_id = request.POST.get('project_id') or request.query_params.get('project_id')
        
        if not file:
            return StandardResponse.validation_error(
                detail='No file provided',
                errors=[{"field": "file", "message": "This field is required."}],
                instance=request.path
            )
        # Get user ID from request
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        if not user_id:
            return StandardResponse.unauthorized(
                detail='User authentication required',
                instance=request.path
            )
        
        # Convert user_id to string for consistency
        user_id = str(user_id)

        resolved_project_id, project_doc, is_draft = cosmos_service.ensure_project_context(
            incoming_project_id,
            user_id,
        )
        project_id = resolved_project_id
        project_context = {
            "project_id": project_id,
            "project_status": project_doc.get("status", "draft" if is_draft else "active"),
            "config_state": project_doc.get("config_state", "unconfigured" if is_draft else "complete"),
            "is_draft": is_draft,
        }

        file_type = file.content_type
        try:
            if file_type == 'application/json':
                try:
                    data = json.load(file)
                    
                    # Extract original comments before processing
                    original_comments = self.extract_comments_from_data(data, 'json')
                    
                    result = await process_uploaded_data_async(data, 'json', 0)

                    # Format response in the new structure only
                    if isinstance(result, dict) and (result.get('overall') is not None or result.get('features') is not None):
                        formatted = {
                            "success": True,
                            "id": f"analysis_{str(uuid.uuid4())}",
                            "projectId": project_id if project_id else 'unknown',
                            "userId": user_id if user_id else 'anonymous',
                            "createdAt": datetime.now().isoformat(),
                            "analysisType": "commentSentiment",
                            "rawLlm": result.get("raw_llm", {}),
                            "analysisData": {
                                "overall": result.get("overall", {}),
                                "counts": result.get("counts", {}),
                                "features": result.get("features", []),
                                "positive_keywords": result.get("positive_keywords", []),
                                "negative_keywords": result.get("negative_keywords", [])
                            },
                            "context": project_context,
                        }
                    else:
                        # Fallback catch-all
                        formatted = {
                            "success": True,
                            "id": f"analysis_{str(uuid.uuid4())}",
                            "projectId": project_id if project_id else 'unknown',
                            "userId": user_id if user_id else 'anonymous',
                            "createdAt": datetime.now().isoformat(),
                            "analysisType": "commentSentiment",
                            "rawLlm": result,
                            "analysisData": result.get("analysisData", {}),
                            "context": project_context,
                        }
                    
                    # Save analysis data to Cosmos DB
                    try:
                        # Save original user data (comments) with user ID and project ID
                        user_data_record = {
                            "user_id": user_id,
                            "project_id": project_id,
                            "file_name": file.name,
                            "file_type": "json",
                            "upload_date": datetime.now().isoformat(),
                            "comments": original_comments,
                            "comments_count": len(original_comments),
                            "type": "user_data"
                        }
                        saved_user_data = cosmos_service.save_user_data(user_data_record)
                        if saved_user_data:
                            print(f"Successfully saved user data: {len(original_comments)} comments for user {user_id}, project {project_id}")
                        else:
                            print(f"Failed to save user data for user {user_id}, project {project_id}")
                        
                        # Do not store extracted content in uploads; keep it under user_data only
                        
                        # Save canonical analysis entity linked to project
                        analysis_id = str(uuid.uuid4())
                        analysis_record = {
                            "id": f"analysis_{analysis_id}",
                            "projectId": project_id,
                            "userId": user_id,
                            "createdAt": datetime.now().isoformat(),
                            "analysisType": "commentSentiment",
                            "rawLlm": formatted.get("raw_llm", {}),
                            "analysisData": {
                                "overall": formatted.get("overall", {}),
                                "counts": formatted.get("counts", {}),
                                "features": formatted.get("features", []),
                                "positive_keywords": formatted.get("positive_keywords", []),
                                "negative_keywords": formatted.get("negative_keywords", [])
                            }
                        }
                        saved = cosmos_service.save_analysis_data(analysis_record)
                        try:
                            if saved and saved.get('id'):
                                cosmos_service.update_project_last_analysis(project_id, saved['id'])
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"Error saving to Cosmos DB: {e}")
                    
                    return StandardResponse.success(
                        data=formatted,
                        message='File uploaded and analyzed successfully'
                    )
                except json.JSONDecodeError:
                    return StandardResponse.validation_error(
                        detail='Invalid JSON file',
                        errors=[{"field": "file", "message": "The uploaded file is not valid JSON."}],
                        instance=request.path
                    )
            
            elif file_type in ['text/csv', 'application/vnd.ms-excel']:
                try:
                    csv_data = []
                    decoded_file = file.read().decode('utf-8').splitlines()
                    reader = csv.DictReader(decoded_file)
                    csv_data = [row for row in reader]
                    
                    # Extract original comments before processing
                    original_comments = self.extract_comments_from_data(csv_data, 'csv')
                    
                    result = await process_uploaded_data_async(
                        csv_data, 'csv', 1
                    )
                    
                    # Save CSV analysis data to Cosmos DB
                    try:
                        # Save original user data (comments) with user ID and project ID
                        user_data_record = {
                            "user_id": user_id,
                            "project_id": project_id,
                            "file_name": file.name,
                            "file_type": "csv",
                            "upload_date": datetime.now().isoformat(),
                            "comments": original_comments,
                            "comments_count": len(original_comments),
                            "type": "user_data"
                        }
                        saved_user_data = cosmos_service.save_user_data(user_data_record)
                        if saved_user_data:
                            print(f"Successfully saved user data: {len(original_comments)} comments for user {user_id}, project {project_id}")
                        else:
                            print(f"Failed to save user data for user {user_id}, project {project_id}")
                        
                        # Do not store extracted content in uploads; keep it under user_data only
                        
                        analysis_id = str(uuid.uuid4())
                        analysis_record = {
                            "id": f"analysis_{analysis_id}",
                            "projectId": project_id,
                            "userId": user_id,
                            "createdAt": datetime.now().isoformat(),
                            "analysisType": "commentSentiment",
                            "rawLlm": result,
                            "analysisData": result.get("analysisData", {})
                        }
                        saved = cosmos_service.save_analysis_data(analysis_record)
                        try:
                            if saved and saved.get('id'):
                                cosmos_service.update_project_last_analysis(project_id, saved['id'])
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"Error saving CSV to Cosmos DB: {e}")
                    
                    # Format CSV response in the new structure
                    formatted = {
                        "success": True,
                        "id": f"analysis_{str(uuid.uuid4())}",
                        "projectId": project_id if project_id else 'unknown',
                        "userId": user_id if user_id else 'anonymous',
                        "createdAt": datetime.now().isoformat(),
                        "analysisType": "commentSentiment",
                        "rawLlm": result,
                        "analysisData": result.get("analysisData", {}),
                        "context": project_context,
                    }
                    
                    return StandardResponse.success(
                        data=formatted,
                        message='CSV file uploaded and analyzed successfully'
                    )
                except Exception as e:
                    return StandardResponse.error(
                        title='CSV Processing Error',
                        detail=f'Error processing CSV file: {str(e)}',
                        status_code=400,
                        error_type='csv-processing-error',
                        instance=request.path
                    )
            
            else:
                return StandardResponse.validation_error(
                    detail='Unsupported file type. Please upload a JSON or CSV file.',
                    errors=[{"field": "file", "message": "Only JSON and CSV files are supported."}],
                    instance=request.path
                )
        
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f'Server error: {str(e)}',
                instance=request.path
            )