from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from http import HTTPStatus
from aiCore.cosmos_service import cosmos_service
from integrations.service import integrations_service
 
from datetime import datetime
import uuid


class ProjectCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_id = getattr(request.user, 'id', None)
            project_name = request.data.get('project_name')
            description = request.data.get('description', '')
            platform = request.data.get('platform', 'standalone')
            external_project_id = request.data.get('external_project_id')
            integration_account_id = request.data.get('integration_account_id')

            if not user_id or not project_name:
                return Response(
                    {'error': 'user_id (auth) and project_name are required'},
                    status=HTTPStatus.BAD_REQUEST,
                )

            # Check if external project already imported
            if platform != 'standalone' and external_project_id:
                provider = 'azure' if platform == 'azure_devops' else 'jira'
                existing = integrations_service.check_external_project_exists(provider, external_project_id, user_id)
                if existing:
                    return Response({
                        'success': False,
                        'error': f'Project "{existing["name"]}" is already imported',
                        'existing_project': existing
                    }, status=HTTPStatus.CONFLICT)

            # Create external links if importing from external platform
            external_links = []
            if platform != 'standalone' and external_project_id:
                provider = 'azure' if platform == 'azure_devops' else 'jira'
                external_url = request.data.get('external_url', '')
                external_key = request.data.get('jira_project_key') if provider == 'jira' else None
                
                external_links.append({
                    'provider': provider,
                    'integrationAccountId': integration_account_id or 'legacy',
                    'externalId': external_project_id,
                    'externalKey': external_key,
                    'url': external_url,
                    'status': 'ok',
                    'lastSyncedAt': None,
                    'syncMetadata': {}
                })

            # Create project using integrations service
            project = integrations_service.create_project(
                user_id=user_id,
                name=project_name,
                description=description,
                external_links=external_links
            )
            
            return Response({'success': True, 'project': project}, status=HTTPStatus.CREATED)
        except Exception as e:
            # Return error message to help diagnose 500s from the client
            return Response({'error': f'Project create failed: {str(e)}'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


class ProjectListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return Response({'error': 'Unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
        
        # Use integrations service to get projects
        projects = integrations_service.get_projects_by_user(user_id)
        return Response({'projects': projects, 'count': len(projects)})


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return Response({'error': 'Unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
        
        # Use integrations service to get project
        project = integrations_service.get_project(project_id, user_id)
        if not project:
            return Response({'error': 'Not found'}, status=HTTPStatus.NOT_FOUND)
        return Response(project)

    def delete(self, request, project_id: str):
        """Delete a project."""
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return Response({'error': 'Unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
        
        try:
            # Delete the project using the integrations service
            success = integrations_service.delete_project(project_id, user_id)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Project deleted successfully'
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Project not found or you do not have permission to delete it'
                }, status=HTTPStatus.NOT_FOUND)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to delete project: {str(e)}'
            }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


class LatestAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id: str):
        # Use the project_id as-is since projects are created with UUID only (no prefix)
        stored_project_id = project_id
        
        # Get the latest comment analysis
        latest_analysis = cosmos_service.get_latest_analysis_for_project(stored_project_id)
        
        # Get the latest user story collection (work items)
        latest_user_stories = cosmos_service.get_user_stories_by_project(stored_project_id)
        print(f"Found {len(latest_user_stories) if latest_user_stories else 0} user story collections for project {stored_project_id}")
        
        if latest_user_stories:
            print(f"User story records: {[record.get('id') for record in latest_user_stories]}")
        
        if not latest_analysis:
            return Response({'exists': False}, status=HTTPStatus.OK)
        
        # Get user ID for submission status lookup
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # Combine the data
        response_data = {
            'exists': True, 
            'analysis': latest_analysis
        }
        
        # Add user stories if available
        if latest_user_stories:
            # Get the most recent user story collection
            latest_stories = latest_user_stories[0] if isinstance(latest_user_stories, list) else latest_user_stories
            print(f"Using user story record: {latest_stories.get('id')}")
            print(f"Work items count: {len(latest_stories.get('work_items', []))}")
            
            # Get submission status for work items
            work_items_with_submission_status = self._enrich_work_items_with_submission_status(
                latest_stories.get('work_items', []), 
                user_id, 
                stored_project_id
            )
            
            response_data['analysis']['userStories'] = {
                'work_items': work_items_with_submission_status,
                'work_items_by_feature': self._group_work_items_by_feature(work_items_with_submission_status),
                'summary': latest_stories.get('summary', {}),
                'process_template': latest_stories.get('process_template', 'Agile'),
                'generated_at': latest_stories.get('generated_at'),
                'comments_count': latest_stories.get('comments_count', 0)
            }
        else:
            print("No user stories found, setting userStories to null")
            response_data['analysis']['userStories'] = None
            
        # Add comments data to reduce API calls
        if user_id:
            try:
                user_data = cosmos_service.get_user_data_by_project(str(user_id), stored_project_id)
                if user_data:
                    response_data['analysis']['comments'] = {
                        'comments': user_data.get('feedback', []),
                        'comments_count': len(user_data.get('feedback', [])),
                        'file_name': user_data.get('file_name'),
                        'upload_date': user_data.get('uploaded_date')
                    }
                else:
                    response_data['analysis']['comments'] = None
            except Exception as e:
                print(f"Error fetching comments: {e}")
                response_data['analysis']['comments'] = None
            
        return Response(response_data, status=HTTPStatus.OK)
    
    def _group_work_items_by_feature(self, work_items: list) -> dict:
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
    
    def _enrich_work_items_with_submission_status(self, work_items: list, user_id: str, project_id: str) -> list:
        """
        Return work items as-is since they should already have submission status from _update_user_stories_submission_status.
        This method is kept for backward compatibility but the work items should already be enriched.
        """
        if not work_items:
            return work_items
            
        print(f"🔍 Work items already have submission status - returning {len(work_items)} items as-is")
        
        # Log submission status for debugging
        for item in work_items:
            if item.get('submitted'):
                print(f"🔍 Work item {item.get('id')} is submitted: {item.get('submitted_to')} at {item.get('submitted_at')}")
        
        return work_items


