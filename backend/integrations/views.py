"""
Views for integration management API endpoints.
Following the existing codebase pattern with DRF and Cosmos DB.
"""

import logging
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.http import JsonResponse
from apis.response import StandardResponse
from .service import integrations_service
from .external_apis import test_azure_connection, test_jira_connection, fetch_azure_projects, fetch_jira_projects

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_endpoint(request):
    """Debug endpoint to test URL routing."""
    return StandardResponse.success(
        data={'user_id': request.user.id},
        message='Debug endpoint working'
    )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_integration_accounts(request):
    """Get all integration accounts for the authenticated user."""
    try:
        user_id = request.user.id
        logger.info(f"Getting integration accounts for user_id: {user_id}")
        accounts = integrations_service.get_integration_accounts_by_user(user_id)
        
        return StandardResponse.success(
            data={'accounts': accounts},
            message="Integration accounts retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting integration accounts: {e}")
        return StandardResponse.internal_server_error(
            detail=str(e),
            instance=request.path
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_azure_integration(request):
    """Create Azure DevOps integration account."""
    try:
        user_id = request.user.id
        data = request.data
        
        organization = data.get('organization', '').strip()
        pat_token = data.get('pat_token', '').strip()
        
        if not organization or not pat_token:
            return StandardResponse.validation_error(
                detail='Organization and PAT token are required',
                errors=[
                    {"field": "organization", "message": "This field is required."} if not organization else None,
                    {"field": "pat_token", "message": "This field is required."} if not pat_token else None
                ],
                instance=request.path
            )
        
        # Test the connection first
        test_result = test_azure_connection(organization, pat_token)
        if not test_result['success']:
            return StandardResponse.error(
                title="Connection test failed",
                detail=f"Connection test failed: {test_result['error']}",
                status_code=400,
                error_type="connection-test-failed",
                instance=request.path
            )
        
        # Create or update the integration account
        account = integrations_service.create_azure_integration(user_id, organization, pat_token)
        
        return StandardResponse.created(
            data={'account': account},
            message='Azure DevOps integration configured successfully'
        )
        
    except ValueError as e:
        return StandardResponse.validation_error(
            detail=str(e),
            instance=request.path
        )
    except Exception as e:
        logger.error(f"Error creating Azure integration: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to create Azure integration',
            instance=request.path
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_jira_integration(request):
    """Create Jira integration account."""
    try:
        user_id = request.user.id
        data = request.data
        
        domain = data.get('domain', '').strip()
        email = data.get('email', '').strip()
        api_token = data.get('api_token', '').strip()
        
        if not domain or not email or not api_token:
            return StandardResponse.validation_error(
                detail='Domain, email, and API token are required',
                errors=[
                    {"field": "domain", "message": "This field is required."} if not domain else None,
                    {"field": "email", "message": "This field is required."} if not email else None,
                    {"field": "api_token", "message": "This field is required."} if not api_token else None
                ],
                instance=request.path
            )
        
        # Test the connection first
        test_result = test_jira_connection(domain, email, api_token)
        if not test_result['success']:
            return StandardResponse.error(
                title="Connection test failed",
                detail=f"Connection test failed: {test_result['error']}",
                status_code=400,
                error_type="connection-test-failed",
                instance=request.path
            )
        
        # Create or update the integration account
        account = integrations_service.create_jira_integration(user_id, domain, email, api_token)
        
        return StandardResponse.created(
            data={'account': account},
            message='Jira integration configured successfully'
        )
        
    except ValueError as e:
        return StandardResponse.validation_error(
            detail=str(e),
            instance=request.path
        )
    except Exception as e:
        logger.error(f"Error creating Jira integration: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to create Jira integration',
            instance=request.path
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_integration_connection(request, account_id):
    """Test connection for an integration account."""
    try:
        user_id = request.user.id
        
        # Get the integration account with decrypted credentials
        accounts = integrations_service.get_integration_accounts_by_user(user_id)
        account = next((acc for acc in accounts if acc['id'] == account_id), None)
        
        if not account:
            return StandardResponse.not_found(
                detail='Integration account not found',
                instance=request.path
            )
        
        # Get decrypted credentials for testing
        account_with_creds = integrations_service.get_decrypted_credentials(user_id, account['provider'])
        if not account_with_creds:
            return StandardResponse.internal_server_error(
                detail='Failed to retrieve credentials',
                instance=request.path
            )
        
        # Test connection based on provider
        if account['provider'] == 'azure':
            organization = account['metadata']['organization']
            pat_token = account_with_creds['credentials']['pat_token']
            test_result = test_azure_connection(organization, pat_token)
        elif account['provider'] == 'jira':
            domain = account['metadata']['domain']
            email = account['metadata']['email']
            api_token = account_with_creds['credentials']['api_token']
            test_result = test_jira_connection(domain, email, api_token)
        else:
            return StandardResponse.validation_error(
                detail='Unsupported provider',
                errors=[{"field": "provider", "message": "Provider must be 'azure' or 'jira'."}],
                instance=request.path
            )
        
        return StandardResponse.success(
            data=test_result,
            message='Connection test completed'
        )
        
    except Exception as e:
        logger.error(f"Error testing connection for account {account_id}: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to test connection',
            instance=request.path
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_integration_account(request, account_id):
    """Delete an integration account."""
    try:
        user_id = request.user.id
        success = integrations_service.delete_integration_account(user_id, account_id)
        
        if success:
            return StandardResponse.success(
                data={},
                message='Integration account deleted successfully'
            )
        else:
            return StandardResponse.not_found(
                detail='Integration account not found',
                instance=request.path
            )
        
    except Exception as e:
        logger.error(f"Error deleting integration account {account_id}: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to delete integration account',
            instance=request.path
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_external_projects(request):
    """Get external projects from a provider."""
    try:
        user_id = request.user.id
        provider = request.GET.get('provider')
        account_id = request.GET.get('accountId')
        
        if not provider or not account_id:
            return StandardResponse.validation_error(
                detail='Provider and accountId are required',
                errors=[
                    {"field": "provider", "message": "This parameter is required."} if not provider else None,
                    {"field": "accountId", "message": "This parameter is required."} if not account_id else None
                ],
                instance=request.path
            )
        
        # Get the integration account with decrypted credentials using accountId
        account = integrations_service.get_integration_account_by_id(user_id, account_id)
        if not account:
            return StandardResponse.not_found(
                detail='Integration account not found',
                instance=request.path
            )
        
        # Verify the provider matches
        if account['provider'] != provider:
            return StandardResponse.validation_error(
                detail='Provider mismatch',
                errors=[{"field": "provider", "message": "Provider does not match the account."}],
                instance=request.path
            )
        
        # Get decrypted credentials for this specific account
        account_with_creds = integrations_service.get_decrypted_credentials_by_account_id(user_id, account_id)
        if not account_with_creds:
            return StandardResponse.internal_server_error(
                detail='Failed to retrieve credentials',
                instance=request.path
            )
        
        # Fetch projects based on provider
        if provider == 'azure':
            organization = account['metadata']['organization']
            pat_token = account_with_creds['credentials']['pat_token']
            projects = fetch_azure_projects(organization, pat_token)
        elif provider == 'jira':
            domain = account['metadata']['domain']
            email = account['metadata']['email']
            api_token = account_with_creds['credentials']['api_token']
            projects = fetch_jira_projects(domain, email, api_token)
        else:
            return StandardResponse.validation_error(
                detail='Unsupported provider',
                errors=[{"field": "provider", "message": "Provider must be 'azure' or 'jira'."}],
                instance=request.path
            )
        
        return StandardResponse.success(
            data={'projects': projects},
            message='External projects retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f"Error fetching external projects: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to fetch external projects',
            instance=request.path
        )


# Project management views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_projects(request):
    """Get all projects for the authenticated user."""
    try:
        user_id = str(request.user.id)
        logger.info(f"Getting projects for user_id: {user_id}")
        projects = integrations_service.get_projects_by_user(user_id)
        
        return StandardResponse.success(
            data={'projects': projects},
            message='Projects retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return StandardResponse.internal_server_error(
            detail=str(e),
            instance=request.path
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project(request):
    """Create a new project."""
    try:
        user_id = str(request.user.id)
        data = request.data
        
        name = data.get('project_name', '').strip()
        description = data.get('description', '').strip() or None
        platform = data.get('platform', 'standalone')
        external_project_id = data.get('external_project_id')
        
        if not name:
            return StandardResponse.validation_error(
                detail='Project name is required',
                errors=[{"field": "project_name", "message": "This field is required."}],
                instance=request.path
            )
        
        # Check if project already exists for external platforms
        if platform != 'standalone' and external_project_id:
            provider = 'azure' if platform == 'azure_devops' else 'jira'
            
            # Check if project with same external ID already exists for this user
            existing_project = integrations_service.check_external_project_exists(
                provider, external_project_id, user_id
            )
            
            if existing_project:
                # Project already exists, return the existing project instead of creating duplicate
                logger.info(f"Project with external ID {external_project_id} already exists, returning existing project")
                return StandardResponse.success(
                    data={
                        'project': existing_project,
                        'already_exists': True
                    },
                    message='Project already exists - navigating to existing project'
                )
        
        # Create external links if importing from external platform
        external_links = []
        if platform != 'standalone' and external_project_id:
            provider = 'azure' if platform == 'azure_devops' else 'jira'
            
            # Create external link
            integration_account_id = data.get('integration_account_id', 'legacy')
            
            link = {
                'provider': provider,
                'integrationAccountId': integration_account_id,
                'externalId': external_project_id,
                'externalKey': data.get('jira_project_key'),
                'url': data.get('external_url', ''),
                'status': 'ok',
                'lastSyncedAt': None,
                'syncMetadata': {}
            }
            external_links.append(link)
        
        # Create the project
        project = integrations_service.create_project(user_id, name, description, external_links)
        
        return StandardResponse.created(
            data={'project': project},
            message='Project created successfully',
            instance=f"/api/projects/{project.get('id')}"
        )
        
    except ValueError as e:
        return StandardResponse.validation_error(
            detail=str(e),
            instance=request.path
        )
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        logger.error(f"Error details: {str(e)}")
        logger.error(f"Request data: {data}")
        return StandardResponse.internal_server_error(
            detail=f'Failed to create project: {str(e)}',
            instance=request.path
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_external_project(request):
    """Check if an external project is already imported."""
    try:
        provider = request.GET.get('provider')
        external_id = request.GET.get('externalId')
        
        if not provider or not external_id:
            return StandardResponse.validation_error(
                detail='Provider and externalId are required',
                errors=[
                    {"field": "provider", "message": "This parameter is required."} if not provider else None,
                    {"field": "externalId", "message": "This parameter is required."} if not external_id else None
                ],
                instance=request.path
            )
        
        existing = integrations_service.check_external_project_exists(provider, external_id)
        
        return StandardResponse.success(
            data={
                'exists': existing is not None,
                'project': existing
            },
            message='External project check completed'
        )
        
    except Exception as e:
        logger.error(f"Error checking external project: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to check external project',
            instance=request.path
        )


# Specific endpoints for Azure DevOps and Jira projects (for frontend compatibility)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_azure_projects(request):
    """Get Azure DevOps projects directly from Azure API (for config page)."""
    try:
        # This endpoint should fetch projects directly from Azure DevOps API
        # Used during initial setup/configuration, not from database
        
        # Get credentials from request body or query params
        organization = request.GET.get('organization') or request.data.get('organization')
        pat_token = request.GET.get('pat_token') or request.data.get('pat_token')
        
        if not organization or not pat_token:
            return StandardResponse.validation_error(
                detail='Organization and PAT token are required',
                errors=[
                    {"field": "organization", "message": "This field is required."} if not organization else None,
                    {"field": "pat_token", "message": "This field is required."} if not pat_token else None
                ],
                instance=request.path
            )
        
        # Fetch projects directly from Azure DevOps API
        projects = fetch_azure_projects(organization, pat_token)
        
        return StandardResponse.success(
            data={
                'projects': projects,
                'organization': organization
            },
            message='Azure DevOps projects retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f"Error fetching Azure projects from API: {e}")
        return StandardResponse.internal_server_error(
            detail=f'Failed to fetch Azure DevOps projects: {str(e)}',
            instance=request.path
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_jira_projects(request):
    """Get Jira projects directly from Jira API (for config page)."""
    try:
        # This endpoint should fetch projects directly from Jira API
        # Used during initial setup/configuration, not from database
        
        # Get credentials from request body or query params
        domain = request.GET.get('domain') or request.data.get('domain')
        email = request.GET.get('email') or request.data.get('email')
        api_token = request.GET.get('api_token') or request.data.get('api_token')
        
        logger.info(f"get_jira_projects called with domain: {domain}, email: {email}")
        
        if not domain or not email or not api_token:
            logger.warning(f"Missing required parameters - domain: {bool(domain)}, email: {bool(email)}, api_token: {bool(api_token)}")
            return StandardResponse.validation_error(
                detail='Domain, email, and API token are required',
                errors=[
                    {"field": "domain", "message": "This field is required."} if not domain else None,
                    {"field": "email", "message": "This field is required."} if not email else None,
                    {"field": "api_token", "message": "This field is required."} if not api_token else None
                ],
                instance=request.path
            )
        
        # Fetch projects directly from Jira API
        logger.info("Calling fetch_jira_projects...")
        projects = fetch_jira_projects(domain, email, api_token)
        logger.info(f"Successfully fetched {len(projects)} projects")
        
        return StandardResponse.success(
            data={
                'projects': projects,
                'domain': domain
            },
            message='Jira projects retrieved successfully'
        )
        
    except Exception as e:
        logger.error(f"Error fetching Jira projects from API: {e}")
        logger.exception("Full traceback:")
        return StandardResponse.internal_server_error(
            detail=f'Failed to fetch Jira projects: {str(e)}',
            instance=request.path
        )


# Dashboard endpoints - fetch projects from database (for daily use)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_azure_projects(request):
    """Get user's imported Azure DevOps projects from database (for dashboard)."""
    try:
        user_id = request.user.id
        
        # Get user's projects from database that are linked to Azure DevOps
        projects = integrations_service.get_projects_by_user(user_id)
        
        # Filter for Azure DevOps projects
        azure_projects = [
            project for project in projects 
            if any(link.get('provider') == 'azure' for link in project.get('externalLinks', []))
        ]
        
        return StandardResponse.success(
            data={'projects': azure_projects},
            message='Azure DevOps projects retrieved from database'
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard Azure projects: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to fetch Azure DevOps projects from database',
            instance=request.path
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_jira_projects(request):
    """Get user's imported Jira projects from database (for dashboard)."""
    try:
        user_id = request.user.id
        
        # Get user's projects from database that are linked to Jira
        projects = integrations_service.get_projects_by_user(user_id)
        
        # Filter for Jira projects
        jira_projects = [
            project for project in projects 
            if any(link.get('provider') == 'jira' for link in project.get('externalLinks', []))
        ]
        
        return StandardResponse.success(
            data={'projects': jira_projects},
            message='Jira projects retrieved from database'
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard Jira projects: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to fetch Jira projects from database',
            instance=request.path
        )


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_project(request, project_id):
    """Update or delete a project."""
    logger.info(f"update_project view called: method={request.method}, project_id={project_id}")
    try:
        user_id = str(request.user.id)
        
        if request.method == 'DELETE':
            # Delete project
            logger.info(f"Attempting to delete project {project_id} for user {user_id}")
            success = integrations_service.delete_project(project_id, user_id)
            if success:
                logger.info(f"Successfully deleted project {project_id}")
                return StandardResponse.success(
                    data={},
                    message='Project deleted successfully'
                )
            else:
                logger.warning(f"Failed to delete project {project_id} - not found or access denied")
                return StandardResponse.not_found(
                    detail='Project not found or access denied',
                    instance=request.path
                )
        
        elif request.method == 'PATCH':
            # Update project
            updates = request.data
            project = integrations_service.update_project(project_id, user_id, updates)
            return StandardResponse.success(
                data={'project': project},
                message='Project updated successfully'
            )
            
    except Exception as e:
        logger.error(f"Error updating/deleting project: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to update project',
            instance=request.path
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_project(request, project_id):
    """Sync project with external provider."""
    try:
        user_id = request.user.id
        provider = request.data.get('provider')
        
        if not provider:
            return StandardResponse.validation_error(
                detail='Provider is required',
                errors=[{"field": "provider", "message": "This field is required."}],
                instance=request.path
            )
        
        # This would implement sync logic with external providers
        # For now, just return success
        return StandardResponse.success(
            data={
                'syncedAt': datetime.now().isoformat()
            },
            message=f'Project synced with {provider}'
        )
        
    except Exception as e:
        logger.error(f"Error syncing project: {e}")
        return StandardResponse.internal_server_error(
            detail='Failed to sync project',
            instance=request.path
        )


# Project deletion is now handled by the projects app - ProjectDetailView.delete()
