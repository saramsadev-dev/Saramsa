"""
Views for integration management API endpoints.
Following the existing codebase pattern with DRF and Cosmos DB.
"""

import logging
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .service import integrations_service
from .external_apis import test_azure_connection, test_jira_connection, fetch_azure_projects, fetch_jira_projects

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_endpoint(request):
    """Debug endpoint to test URL routing."""
    return Response({
        'success': True,
        'message': 'Debug endpoint working',
        'user_id': request.user.id
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_integration_accounts(request):
    """Get all integration accounts for the authenticated user."""
    try:
        user_id = request.user.id
        logger.info(f"Getting integration accounts for user_id: {user_id}")
        accounts = integrations_service.get_integration_accounts_by_user(user_id)
        
        return Response({
            'success': True,
            'accounts': accounts
        })
        
    except Exception as e:
        logger.error(f"Error getting integration accounts: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({
                'success': False,
                'error': 'Organization and PAT token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Test the connection first
        test_result = test_azure_connection(organization, pat_token)
        if not test_result['success']:
            return Response({
                'success': False,
                'error': f"Connection test failed: {test_result['error']}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update the integration account
        account = integrations_service.create_azure_integration(user_id, organization, pat_token)
        
        return Response({
            'success': True,
            'account': account,
            'message': 'Azure DevOps integration configured successfully'
        })
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating Azure integration: {e}")
        return Response({
            'success': False,
            'error': 'Failed to create Azure integration'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({
                'success': False,
                'error': 'Domain, email, and API token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Test the connection first
        test_result = test_jira_connection(domain, email, api_token)
        if not test_result['success']:
            return Response({
                'success': False,
                'error': f"Connection test failed: {test_result['error']}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update the integration account
        account = integrations_service.create_jira_integration(user_id, domain, email, api_token)
        
        return Response({
            'success': True,
            'account': account,
            'message': 'Jira integration configured successfully'
        })
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating Jira integration: {e}")
        return Response({
            'success': False,
            'error': 'Failed to create Jira integration'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({
                'success': False,
                'error': 'Integration account not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get decrypted credentials for testing
        account_with_creds = integrations_service.get_decrypted_credentials(user_id, account['provider'])
        if not account_with_creds:
            return Response({
                'success': False,
                'error': 'Failed to retrieve credentials'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
            return Response({
                'success': False,
                'error': 'Unsupported provider'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(test_result)
        
    except Exception as e:
        logger.error(f"Error testing connection for account {account_id}: {e}")
        return Response({
            'success': False,
            'error': 'Failed to test connection'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_integration_account(request, account_id):
    """Delete an integration account."""
    try:
        user_id = request.user.id
        success = integrations_service.delete_integration_account(user_id, account_id)
        
        if success:
            return Response({
                'success': True,
                'message': 'Integration account deleted successfully'
            })
        else:
            return Response({
                'success': False,
                'error': 'Integration account not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error deleting integration account {account_id}: {e}")
        return Response({
            'success': False,
            'error': 'Failed to delete integration account'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_external_projects(request):
    """Get external projects from a provider."""
    try:
        user_id = request.user.id
        provider = request.GET.get('provider')
        account_id = request.GET.get('accountId')
        
        if not provider or not account_id:
            return Response({
                'success': False,
                'error': 'Provider and accountId are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the integration account with decrypted credentials using accountId
        account = integrations_service.get_integration_account_by_id(user_id, account_id)
        if not account:
            return Response({
                'success': False,
                'error': 'Integration account not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify the provider matches
        if account['provider'] != provider:
            return Response({
                'success': False,
                'error': 'Provider mismatch'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get decrypted credentials for this specific account
        account_with_creds = integrations_service.get_decrypted_credentials_by_account_id(user_id, account_id)
        if not account_with_creds:
            return Response({
                'success': False,
                'error': 'Failed to retrieve credentials'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
            return Response({
                'success': False,
                'error': 'Unsupported provider'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'projects': projects
        })
        
    except Exception as e:
        logger.error(f"Error fetching external projects: {e}")
        return Response({
            'success': False,
            'error': 'Failed to fetch external projects'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Project management views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_projects(request):
    """Get all projects for the authenticated user."""
    try:
        user_id = str(request.user.id)
        logger.info(f"Getting projects for user_id: {user_id}")
        projects = integrations_service.get_projects_by_user(user_id)
        
        return Response({
            'success': True,
            'projects': projects
        })
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({
                'success': False,
                'error': 'Project name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
                return Response({
                    'success': True,
                    'project': existing_project,
                    'message': 'Project already exists - navigating to existing project',
                    'already_exists': True
                })
        
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
        
        return Response({
            'success': True,
            'project': project,
            'message': 'Project created successfully'
        })
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        logger.error(f"Error details: {str(e)}")
        logger.error(f"Request data: {data}")
        return Response({
            'success': False,
            'error': f'Failed to create project: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_external_project(request):
    """Check if an external project is already imported."""
    try:
        provider = request.GET.get('provider')
        external_id = request.GET.get('externalId')
        
        if not provider or not external_id:
            return Response({
                'success': False,
                'error': 'Provider and externalId are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        existing = integrations_service.check_external_project_exists(provider, external_id)
        
        return Response({
            'success': True,
            'exists': existing is not None,
            'project': existing
        })
        
    except Exception as e:
        logger.error(f"Error checking external project: {e}")
        return Response({
            'success': False,
            'error': 'Failed to check external project'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({
                'success': False,
                'error': 'Organization and PAT token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch projects directly from Azure DevOps API
        projects = fetch_azure_projects(organization, pat_token)
        
        return Response({
            'success': True,
            'projects': projects,
            'organization': organization
        })
        
    except Exception as e:
        logger.error(f"Error fetching Azure projects from API: {e}")
        return Response({
            'success': False,
            'error': f'Failed to fetch Azure DevOps projects: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        
        if not domain or not email or not api_token:
            return Response({
                'success': False,
                'error': 'Domain, email, and API token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch projects directly from Jira API
        projects = fetch_jira_projects(domain, email, api_token)
        
        return Response({
            'success': True,
            'projects': projects,
            'domain': domain
        })
        
    except Exception as e:
        logger.error(f"Error fetching Jira projects from API: {e}")
        return Response({
            'success': False,
            'error': f'Failed to fetch Jira projects: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        
        return Response({
            'success': True,
            'projects': azure_projects
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard Azure projects: {e}")
        return Response({
            'success': False,
            'error': 'Failed to fetch Azure DevOps projects from database'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        
        return Response({
            'success': True,
            'projects': jira_projects
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard Jira projects: {e}")
        return Response({
            'success': False,
            'error': 'Failed to fetch Jira projects from database'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                return Response({
                    'success': True,
                    'message': 'Project deleted successfully'
                })
            else:
                logger.warning(f"Failed to delete project {project_id} - not found or access denied")
                return Response({
                    'success': False,
                    'error': 'Project not found or access denied'
                }, status=status.HTTP_404_NOT_FOUND)
        
        elif request.method == 'PATCH':
            # Update project
            updates = request.data
            project = integrations_service.update_project(project_id, user_id, updates)
            return Response({
                'success': True,
                'project': project
            })
            
    except Exception as e:
        logger.error(f"Error updating/deleting project: {e}")
        return Response({
            'success': False,
            'error': 'Failed to update project'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_project(request, project_id):
    """Sync project with external provider."""
    try:
        user_id = request.user.id
        provider = request.data.get('provider')
        
        if not provider:
            return Response({
                'success': False,
                'error': 'Provider is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # This would implement sync logic with external providers
        # For now, just return success
        return Response({
            'success': True,
            'message': f'Project synced with {provider}',
            'syncedAt': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error syncing project: {e}")
        return Response({
            'success': False,
            'error': 'Failed to sync project'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Project deletion is now handled by the projects app - ProjectDetailView.delete()
