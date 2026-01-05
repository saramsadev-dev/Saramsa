"""
External API views for fetching data from external platforms.

Contains views for external platform interactions:
- Get Azure DevOps projects from API
- Get Jira projects from API
- Get dashboard projects (filtered by provider)
- Check external project existence
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from apis.core.response import StandardResponse
from apis.core.error_handlers import handle_service_errors

from ..services import get_external_api_service, get_project_service, get_integration_service

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@handle_service_errors
def get_azure_projects(request):
    """Get Azure DevOps projects directly from Azure API (for config page)."""
    # This endpoint fetches projects directly from Azure DevOps API
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
    external_api_service = get_external_api_service()
    projects = external_api_service.fetch_azure_projects(organization, pat_token)
    
    return StandardResponse.success(
        data={
            'projects': projects,
            'organization': organization
        },
        message='Azure DevOps projects retrieved successfully'
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@handle_service_errors
def get_jira_projects(request):
    """Get Jira projects directly from Jira API (for config page)."""
    # This endpoint fetches projects directly from Jira API
    # Used during initial setup/configuration, not from database
    
    # Get credentials from request body or query params
    domain = request.GET.get('domain') or request.data.get('domain')
    email = request.GET.get('email') or request.data.get('email')
    api_token = request.GET.get('api_token') or request.data.get('api_token')
    
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
    
    # Fetch projects directly from Jira API
    external_api_service = get_external_api_service()
    projects = external_api_service.fetch_jira_projects(domain, email, api_token)
    
    return StandardResponse.success(
        data={
            'projects': projects,
            'domain': domain
        },
        message='Jira projects retrieved successfully'
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@handle_service_errors
def get_dashboard_azure_projects(request):
    """Get user's imported Azure DevOps projects from database (for dashboard)."""
    user_id = request.user.id
    
    # Get user's projects filtered by Azure DevOps provider
    project_service = get_project_service()
    azure_projects = project_service.get_projects_by_provider(str(user_id), 'azure')
    
    return StandardResponse.success(
        data={'projects': azure_projects},
        message='Azure DevOps projects retrieved from database'
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@handle_service_errors
def get_dashboard_jira_projects(request):
    """Get user's imported Jira projects from database (for dashboard)."""
    user_id = request.user.id
    
    # Get user's projects filtered by Jira provider
    project_service = get_project_service()
    jira_projects = project_service.get_projects_by_provider(str(user_id), 'jira')
    
    return StandardResponse.success(
        data={'projects': jira_projects},
        message='Jira projects retrieved from database'
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@handle_service_errors
def get_external_projects(request):
    """Get external projects from various providers."""
    provider = request.GET.get('provider')
    user_id = request.user.id
    
    if not provider:
        return StandardResponse.validation_error(
            detail='Provider is required',
            errors=[{"field": "provider", "message": "This parameter is required."}],
            instance=request.path
        )
    
    try:
        integration_service = get_integration_service()
        
        if provider == 'azure':
            organization = request.GET.get('organization')
            pat_token = request.GET.get('pat_token')
            projects = integration_service.get_external_projects(
                user_id, provider, organization=organization, pat_token=pat_token
            )
        elif provider == 'jira':
            domain = request.GET.get('domain')
            email = request.GET.get('email')
            api_token = request.GET.get('api_token')
            projects = integration_service.get_external_projects(
                user_id, provider, domain=domain, email=email, api_token=api_token
            )
        else:
            return StandardResponse.validation_error(
                detail=f'Unsupported provider: {provider}',
                instance=request.path
            )
        
        return StandardResponse.success(
            data={'projects': projects, 'provider': provider},
            message=f'{provider.title()} projects retrieved successfully'
        )
        
    except ValueError as e:
        return StandardResponse.validation_error(
            detail=str(e),
            instance=request.path
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@handle_service_errors
def check_external_project(request):
    """Check if an external project is already imported."""
    provider = request.GET.get('provider')
    external_id = request.GET.get('externalId')
    user_id = request.user.id
    
    if not provider or not external_id:
        return StandardResponse.validation_error(
            detail='Provider and externalId are required',
            errors=[
                {"field": "provider", "message": "This parameter is required."} if not provider else None,
                {"field": "externalId", "message": "This parameter is required."} if not external_id else None
            ],
            instance=request.path
        )
    
    integration_service = get_integration_service()
    existing = integration_service.check_external_project_exists(provider, external_id, user_id)
    
    return StandardResponse.success(
        data={
            'exists': existing is not None,
            'project': existing
        },
        message='External project check completed'
    )