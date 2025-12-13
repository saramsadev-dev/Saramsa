import base64
import httpx
import asyncio
import uuid
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from authapp.permissions import IsAdminOrUser, NoAuthentication
from aiCore.cosmos_service import cosmos_service
from integrations.service import integrations_service
from apis.response import StandardResponse

# Get Azure DevOps settings from environment
org = settings.AZURE_DEVOPS_ORGANIZATION
project = settings.AZURE_DEVOPS_PROJECT
pat = settings.AZURE_DEVOPS_PAT

# Validate that required environment variables are set
if not org or not project or not pat:
    print("WARNING: Azure DevOps environment variables not configured!")
    print("Please set AZURE_DEVOPS_ORGANIZATION, AZURE_DEVOPS_PROJECT, and AZURE_DEVOPS_PAT")


class AzureDevOpsConfigView(APIView):
    permission_classes = [IsAuthenticated]  # Keep authentication required for security

    def get(self, request):
        """Return stored Azure DevOps config for the authenticated user."""
        try:
            user_id = getattr(request.user, 'id', None)
            if not user_id:
                return StandardResponse.unauthorized(
                    detail="Authentication required",
                    instance=request.path
                )

            # Get Azure integration account
            account = integrations_service.get_integration_account_by_provider(user_id, 'azure')
            
            if account:
                return StandardResponse.success(
                    data={
                        "organization": account['metadata']['organization'],
                        "has_token": True,  # Don't expose actual token
                        "saved_at": account.get('savedAt'),
                    },
                    message="Azure DevOps configuration retrieved successfully"
                )

            return StandardResponse.not_found(
                detail="No Azure DevOps integration found",
                instance=request.path
            )
        except Exception as e:  # noqa: BLE001
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )


    def post(self, request):
        return asyncio.run(self.handle_post(request))

    async def handle_post(self, request):
        """Configure Azure DevOps connection and fetch projects"""
        organization = request.data.get("organization")
        pat_token = request.data.get("pat_token")

        print(f"Azure DevOps Config - Organization: {organization}")
        print(f"Azure DevOps Config - PAT Token: "
              f"{pat_token[:10]}..." if pat_token else "No PAT token")

        if not organization or not pat_token:
            return StandardResponse.validation_error(
                detail="Both organization and pat_token are required",
                errors=[
                    {"field": "organization", "message": "This field is required."} if not organization else None,
                    {"field": "pat_token", "message": "This field is required."} if not pat_token else None
                ],
                instance=request.path
            )

        # Create basic auth header
        auth_token = base64.b64encode(
            f":{pat_token}".encode()
        ).decode()
        headers = {
            "Authorization": f"Basic {auth_token}",
            "Accept": "application/json"
        }

        # Fetch projects from Azure DevOps
        url = (f"https://dev.azure.com/{organization}/"
               f"_apis/projects?api-version=7.0")

        try:
            print(f"Azure DevOps Config - Making request to: {url}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                print(f"Azure DevOps Config - Response status: {response.status_code}")
                
                if response.status_code == 200:
                    projects_data = response.json()
                    projects = projects_data.get("value", [])

                    # Fetch process template (capabilities) for each project in parallel
                    async def fetch_template_for_project(p):
                        try:
                            proj_id = p.get("id")
                            if not proj_id:
                                return (None, None)
                            details_url = (f"https://dev.azure.com/{organization}/_apis/projects/{proj_id}"
                                           f"?includeCapabilities=true&api-version=7.0")
                            d_resp = await client.get(details_url, headers=headers)
                            if d_resp.status_code == 200:
                                d_json = d_resp.json()
                                template_name = (
                                    ((d_json.get("capabilities") or {})
                                      .get("processTemplate") or {})
                                      .get("templateName")
                                )
                                return (proj_id, template_name)
                            return (proj_id, None)
                        except Exception:
                            return (p.get("id"), None)

                    template_results = await asyncio.gather(*[fetch_template_for_project(p) for p in projects])
                    id_to_template = {pid: t for (pid, t) in template_results if pid}
                    
                    # Transform projects to match frontend expectations
                    transformed_projects = []
                    for project in projects:
                        transformed_projects.append({
                            "id": project.get("id"),
                            "name": project.get("name"),
                            "description": f"Project ID: {project.get('id')}",
                            "state": project.get("state"),
                            "visibility": project.get("visibility"),
                            "lastUpdateTime": project.get("lastUpdateTime"),
                            "templateName": id_to_template.get(project.get("id"))
                        })
                    
                    # Create or update integration account
                    try:
                        user_id = getattr(request.user, 'id', None)
                        if user_id:
                            # Check if integration already exists
                            existing = integrations_service.get_integration_account_by_provider(user_id, 'azure')
                            if not existing:
                                integrations_service.create_azure_integration(
                                    user_id=user_id,
                                    organization=organization,
                                    pat_token=pat_token
                                )
                                print(f"Created Azure integration for user {user_id}")
                            else:
                                print(f"Azure integration already exists for user {user_id}")
                    except Exception as e:
                        print(f"Warning: failed to create integration account: {e}")
                    return StandardResponse.success(
                        data={
                            "projects": transformed_projects,
                            "organization": organization
                        },
                        message="Azure DevOps projects retrieved successfully"
                    )
                else:
                    error_message = "Failed to connect to Azure DevOps"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_message = error_data["message"]
                    except Exception:
                        pass
                    
                    return StandardResponse.error(
                        title="Azure DevOps Connection Failed",
                        detail=error_message,
                        status_code=response.status_code,
                        instance=request.path
                    )
                    
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Connection error: {str(e)}",
                instance=request.path
            )


class CreateAzureWorkItemView(APIView):
    """
    DEPRECATED: Use UserStorySubmissionView in insightsGenerator for unified submission
    This endpoint is kept for backward compatibility
    """
    permission_classes = [IsAdminOrUser]  # Require authentication

    def post(self, request):
        return asyncio.run(self.handle_post(request))

    async def handle_post(self, request):
        """Create work items in Azure DevOps with dynamic configuration"""
        print("🔵 Received request data:", request.data)
        print("🔵 Content-Type:", request.content_type)

        work_items = request.data.get("items", [])
        if not isinstance(work_items, list) or not work_items:
            return StandardResponse.validation_error(
                detail="Payload must contain a non-empty list under 'items'",
                errors=[{"field": "items", "message": "This field must be a non-empty list."}],
                instance=request.path
            )

        # Get Azure DevOps configuration from request, project config, or use defaults
        organization = request.data.get("organization", org)
        project_name = request.data.get("project", project)
        pat_token = request.data.get("pat_token", pat)
        
        # Check for project-scoped configuration
        project_id = request.data.get("project_id") or request.data.get("db_project_id")
        if project_id:
            try:
                stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
                items = cosmos_service.query_items('projects', 'SELECT * FROM c WHERE c.id = @id', [{"name": "@id", "value": stored_id}])
                if items and items[0].get('azure_config'):
                    cfg = items[0]['azure_config']
                    organization = cfg.get('organization') or organization
                    pat_token = cfg.get('pat_token') or pat_token
                    project_name = cfg.get('project_name') or project_name
            except Exception:
                pass

        # Validate required configuration
        if not organization or not project_name or not pat_token:
            return StandardResponse.validation_error(
                detail="Azure DevOps configuration is incomplete. Please provide organization, project, and pat_token.",
                errors=[
                    {"field": "organization", "message": "This field is required."} if not organization else None,
                    {"field": "project", "message": "This field is required."} if not project_name else None,
                    {"field": "pat_token", "message": "This field is required."} if not pat_token else None
                ],
                instance=request.path
            )

        # Encode PAT token for authentication
        auth_token = base64.b64encode(f":{pat_token}".encode()).decode()
        headers = {
            "Content-Type": "application/json-patch+json",
            "Authorization": f"Basic {auth_token}",
            "Accept": "application/json"
        }

        # Text-to-number priority mapping
        priority_mapping = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4
        }

        async def create_item(client, item):
            work_item_type_input = item.get("type", "Task")
            title = item.get("title")
            description = item.get("description", "")
            priority_text = item.get("priority", "medium")
            tags = item.get("tags", "Saramsa")

            if not title:
                return {
                    "success": False, 
                    "error": "Title is required", 
                    "item": item
                }

            safe_priority = priority_mapping.get(priority_text.lower(), 3)

            # Map generic types to template-specific WIT names when possible
            process_template = request.data.get("process_template")

            def map_type_to_template(type_input, template):
                t = (type_input or "").strip().lower()
                if t in ("change", "change request", "changerequest"):
                    return "Task"
                if t == "feature":
                    if template == "Scrum":
                        return "Product Backlog Item"
                    if template == "Agile":
                        return "User Story"
                    if template == "Basic":
                        return "Issue"
                    if template == "CMMI":
                        return "Requirement"
                    # default fallback
                    return "User Story"
                # pass through for known specific types
                specific_map = {
                    "bug": "Bug",
                    "task": "Task",
                    "user story": "User Story",
                    "product backlog item": "Product Backlog Item",
                    "pbi": "Product Backlog Item",
                    "issue": "Issue",
                    "requirement": "Requirement",
                    "feature": "Feature",
                }
                return specific_map.get(t, type_input)

            mapped_type = map_type_to_template(work_item_type_input, process_template)

            # Ensure proper URL encoding for types with spaces
            try:
                from urllib.parse import quote
                encoded_type = quote(mapped_type, safe='')
            except Exception:
                encoded_type = mapped_type

            url = (f"https://dev.azure.com/{organization}/{project_name}/"
                   f"_apis/wit/workitems/${encoded_type}?api-version=7.1-preview.3")
            print("🌐 Posting to:", url)

            body = [
                {"op": "add", "path": "/fields/System.Title", "value": title},
                {"op": "add", "path": "/fields/System.Description", "value": description},
                {"op": "add", 
                 "path": "/fields/Microsoft.VSTS.Common.Priority", 
                 "value": safe_priority},
                {"op": "add", "path": "/fields/System.Tags", "value": tags}
            ]

            try:
                resp = await client.post(url, json=body, headers=headers)

                if resp.status_code in [200, 201]:
                    return {"success": True, "work_item": resp.json()}
                else:
                    return {
                        "success": False,
                        "status": resp.status_code,
                        "error": resp.text,
                        "item": item
                    }

            except Exception as e:
                return {"success": False, "error": str(e), "item": item}

        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [create_item(client, item) for item in work_items]
            results = await asyncio.gather(*tasks)

        # Save work item creation history to Cosmos DB
        try:
            work_item_id = str(uuid.uuid4())
            work_item_data = {
                'id': f'work_item_{work_item_id}',
                'type': 'work_item',
                'platform': 'azure_devops',
                'organization': organization,
                'project': project_name,
                'work_items_requested': len(work_items),
                'work_items_created': len([r for r in results if r.get('success')]),
                'creation_date': datetime.now().isoformat(),
                'results': results,
                'metadata': {
                    'source': 'api_request',
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'request_timestamp': datetime.now().isoformat()
                }
            }
            
            saved_work_item = cosmos_service.save_work_item(work_item_data)
            if saved_work_item:
                work_item_data['cosmos_id'] = saved_work_item.get('id')
        except Exception as e:
            print(f"Error saving work item to Cosmos DB: {e}")

        return StandardResponse.success(
            data={
                "results": results,
                "work_item_batch_id": work_item_id,
                "summary": {
                    "total_requested": len(work_items),
                    "successful": len([r for r in results if r.get('success')]),
                    "failed": len([r for r in results if not r.get('success')])
                }
            },
            message="Work items creation completed",
            status_code=207
        )


class ListAzureWorkItemTypes(APIView):
    permission_classes = [IsAdminOrUser]  # Require authentication
    
    def get(self, request):
        """List available work item types from Azure DevOps"""
        # Get configuration from request parameters or use defaults
        organization = request.GET.get("organization", org)
        project_name = request.GET.get("project", project)
        pat_token = request.GET.get("pat_token", pat)
        
        if not organization or not project_name or not pat_token:
            return StandardResponse.validation_error(
                detail="Azure DevOps configuration is incomplete. Please provide organization, project, and pat_token.",
                errors=[
                    {"field": "organization", "message": "This field is required."} if not organization else None,
                    {"field": "project", "message": "This field is required."} if not project_name else None,
                    {"field": "pat_token", "message": "This field is required."} if not pat_token else None
                ],
                instance=request.path
            )
        
        print(f"Project: {project_name}, Org: {organization}")
        url = (f"https://dev.azure.com/{organization}/{project_name}/"
               f"_apis/wit/workitemtypes?api-version=7.1")
        
        # Correct Azure DevOps PAT format: encode ":PAT" not "username:PAT"
        auth_token = base64.b64encode(f":{pat_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_token}",
            "Accept": "application/json"
        }

        try:
            import requests
            response = requests.get(url, headers=headers)
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            
            if response.status_code in [200, 201]:
                return StandardResponse.success(
                    data=response.json(),
                    message="Work item types retrieved successfully"
                )
            else:
                return StandardResponse.error(
                    title="Failed to fetch work item types",
                    detail=response.text,
                    status_code=response.status_code,
                    instance=request.path
                )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )

class WorkItemsListView(APIView):
    """Get all work items from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        try:
            # Get all work items from Cosmos DB
            work_items = cosmos_service.query_items("work_items", "SELECT * FROM c WHERE c.type = 'work_item' ORDER BY c.creation_date DESC")
            
            return StandardResponse.success(
                data={
                    "work_items": work_items,
                    "count": len(work_items)
                },
                message="Work items retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch work items: {str(e)}",
                instance=request.path
            )

class WorkItemDetailView(APIView):
    """Get specific work item by ID from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request, work_item_id):
        try:
            work_item_data = cosmos_service.get_work_item(work_item_id)
            if not work_item_data:
                return StandardResponse.not_found(
                    detail="Work item not found",
                    instance=request.path
                )
            
            return StandardResponse.success(
                data=work_item_data,
                message="Work item retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch work item: {str(e)}",
                instance=request.path
            )

class WorkItemsByPlatformView(APIView):
    """Get work items by platform (azure_devops, jira)"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request, platform):
        try:
            # Query work items by platform
            work_items = cosmos_service.query_items(
                "work_items", 
                "SELECT * FROM c WHERE c.type = 'work_item' AND c.platform = @platform ORDER BY c.creation_date DESC",
                [{"name": "@platform", "value": platform}]
            )
            
            return StandardResponse.success(
                data={
                    "work_items": work_items,
                    "count": len(work_items),
                    "platform": platform
                },
                message="Work items retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch work items: {str(e)}",
                instance=request.path
            )


class AzureDevOpsProjectsView(APIView):
    """Get Azure DevOps projects - similar to JiraProjectsView"""
    permission_classes = [NoAuthentication]
    authentication_classes = []  # Explicitly disable all authentication

    def get(self, request):
        print(f"🔍 Azure DevOps Projects GET request received")
        print(f"   User: {getattr(request, 'user', 'No user')}")
        print(f"   Auth header: {request.headers.get('Authorization', 'No auth header')[:50]}...")
        print(f"   Query params: {dict(request.query_params)}")
        return asyncio.run(self.handle_get(request))
    
    def post(self, request):
        return asyncio.run(self.handle_post(request))

    async def handle_get(self, request):
        # Get credentials from query parameters (for initial config) or use global defaults
        organization = request.query_params.get('organization') or org
        pat_token = request.query_params.get('pat_token') or pat
        return await self._fetch_projects(request, organization, pat_token)
    
    async def handle_post(self, request):
        # Get credentials from request body (more secure)
        organization = request.data.get('organization')
        pat_token = request.data.get('pat_token')
        
        print(f"Azure DevOps Config - Organization: {organization}")
        print(f"Azure DevOps Config - PAT Token: {pat_token[:10] + '...' if pat_token else 'None'}")
        
        if not organization or not pat_token:
            return StandardResponse.validation_error(
                detail="Organization and pat_token are required",
                errors=[
                    {"field": "organization", "message": "This field is required."} if not organization else None,
                    {"field": "pat_token", "message": "This field is required."} if not pat_token else None
                ],
                instance=request.path
            )
        
        return await self._fetch_projects(request, organization, pat_token)
    
    async def _fetch_projects(self, request, organization, pat_token):
        # Prefer project-scoped Azure config if provided
        project_id = request.query_params.get('projectId')
        if project_id:
            try:
                stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
                items = cosmos_service.query_items('projects', 'SELECT * FROM c WHERE c.id = @id', [{"name": "@id", "value": stored_id}])
                if items and items[0].get('azure_config'):
                    cfg = items[0]['azure_config']
                    organization = cfg.get('organization') or organization
                    pat_token = cfg.get('pat_token') or pat_token
            except Exception:
                pass

        auth_token = base64.b64encode(f":{pat_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_token}",
            "Accept": "application/json"
        }

        try:
            url = f"https://dev.azure.com/{organization}/_apis/projects?api-version=7.0"
            print(f"🌐 Making request to Azure DevOps: {url}")
            print(f"🔑 Auth header: Basic {auth_token[:20]}...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=headers)
                
                print(f"📊 Azure DevOps response: {resp.status_code}")
                if resp.status_code != 200:
                    print(f"❌ Error response body: {resp.text}")
                
                if resp.status_code == 200:
                    projects_data = resp.json()
                    projects = projects_data.get("value", [])

                    # Fetch process template (capabilities) for each project in parallel
                    async def fetch_template_for_project(p):
                        try:
                            proj_id = p.get("id")
                            if not proj_id:
                                return (None, None)
                            details_url = (f"https://dev.azure.com/{organization}/_apis/projects/{proj_id}"
                                           f"?includeCapabilities=true&api-version=7.0")
                            d_resp = await client.get(details_url, headers=headers)
                            if d_resp.status_code == 200:
                                d_json = d_resp.json()
                                template_name = (
                                    ((d_json.get("capabilities") or {})
                                      .get("processTemplate") or {})
                                      .get("templateName")
                                )
                                return (proj_id, template_name)
                            return (proj_id, None)
                        except Exception:
                            return (p.get("id"), None)

                    template_results = await asyncio.gather(*[fetch_template_for_project(p) for p in projects])
                    id_to_template = {pid: t for (pid, t) in template_results if pid}
                    
                    # Transform projects to match frontend expectations
                    transformed_projects = []
                    for project in projects:
                        transformed_projects.append({
                            "id": project.get("id"),
                            "name": project.get("name"),
                            "description": f"Project ID: {project.get('id')}",
                            "state": project.get("state"),
                            "visibility": project.get("visibility"),
                            "lastUpdateTime": project.get("lastUpdateTime"),
                            "templateName": id_to_template.get(project.get("id"))
                        })
                    
                    return StandardResponse.success(
                        data={
                            "projects": transformed_projects,
                            "organization": organization
                        },
                        message="Azure DevOps projects retrieved successfully"
                    )
                else:
                    error_message = "Failed to connect to Azure DevOps"
                    try:
                        error_data = resp.json()
                        if "message" in error_data:
                            error_message = error_data["message"]
                        elif "value" in error_data and error_data["value"]:
                            error_message = error_data["value"]
                    except Exception:
                        pass
                    
                    return StandardResponse.error(
                        title="Azure DevOps Connection Failed",
                        detail=error_message,
                        status_code=resp.status_code,
                        instance=request.path
                    )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )


class AzureDevOpsProjectCreationView(APIView):
    """Create a new Azure DevOps project entity in the database - similar to JiraProjectCreationView"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a new Azure DevOps project entity in the database"""
        try:
            # Get user from request
            user = request.user
            if not user or not user.is_authenticated:
                return StandardResponse.unauthorized(
                    detail="Authentication required",
                    instance=request.path
                )
            
            # Extract project data from request
            project_name = request.data.get('project_name')
            azure_project_id = request.data.get('azure_project_id')
            azure_project_name = request.data.get('azure_project_name')
            azure_organization = request.data.get('azure_organization')
            azure_pat_token = request.data.get('azure_pat_token')
            azure_process_template = request.data.get('azure_process_template')
            
            if not all([project_name, azure_project_id, azure_project_name, azure_organization, azure_pat_token]):
                return StandardResponse.validation_error(
                    detail='Missing required fields: project_name, azure_project_id, azure_project_name, azure_organization, azure_pat_token',
                    instance=request.path
                )
            
            # Create project data structure
            project_id = str(uuid.uuid4())
            project_data = {
                'id': f'project_{project_id}',
                'type': 'project',
                'platform': 'azure_devops',
                'name': project_name,
                'owner_user_id': str(user.id),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'external_project_id': azure_project_id,
                'external_project_name': azure_project_name,
                'organization': azure_organization,
                'azure_config': {
                    'organization': azure_organization,
                    'pat_token': azure_pat_token,
                    'project_id': azure_project_id,
                    'project_name': azure_project_name,
                    'process_template': azure_process_template
                },
                'status': 'active',
                'last_analysis_id': None,
                'analysis_count': 0,
                'work_items_count': 0
            }
            
            # Save project to Cosmos DB
            saved_project = cosmos_service.save_project(project_data)
            if not saved_project:
                return StandardResponse.internal_server_error(
                    detail='Failed to save project',
                    instance=request.path
                )
            
            return StandardResponse.created(
                data={
                    'id': project_id,
                    'name': project_name,
                    'platform': 'azure_devops',
                    'azure_project_id': azure_project_id,
                    'azure_project_name': azure_project_name,
                    'created_at': project_data['created_at']
                },
                message='Azure DevOps project created successfully',
                instance=f"/api/projects/{project_id}"
            )
            
        except Exception as e:
            print(f"Error creating Azure DevOps project: {e}")
            return StandardResponse.internal_server_error(
                detail=f'Project creation failed: {str(e)}',
                instance=request.path
            )


class AzureDevOpsWorkItemTypesView(APIView):
    """Get Azure DevOps work item types for a project - similar to JiraIssueTypesView"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return asyncio.run(self.handle_get(request))

    async def handle_get(self, request):
        project_id = request.query_params.get('projectId')
        if not project_id:
            return StandardResponse.validation_error(
                detail="projectId parameter is required",
                errors=[{"field": "projectId", "message": "This parameter is required."}],
                instance=request.path
            )

        # Prefer project-scoped Azure config if present
        organization = org
        pat_token = pat
        project_name = project
        
        try:
            stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
            items = cosmos_service.query_items('projects', 'SELECT * FROM c WHERE c.id = @id', [{"name": "@id", "value": stored_id}])
            if items and items[0].get('azure_config'):
                cfg = items[0]['azure_config']
                organization = cfg.get('organization') or organization
                pat_token = cfg.get('pat_token') or pat_token
                project_name = cfg.get('project_name') or project_name
        except Exception:
            pass

        auth_token = base64.b64encode(f":{pat_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_token}",
            "Accept": "application/json"
        }

        try:
            url = f"https://dev.azure.com/{organization}/{project_name}/_apis/wit/workitemtypes?api-version=7.1"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=headers)
                
                if resp.status_code == 200:
                    work_item_types = resp.json()
                    
                    # Transform work item types to match frontend expectations
                    enhanced_work_item_types = []
                    for wit in work_item_types.get("value", []):
                        enhanced_wit = {
                            'name': wit.get('name'),
                            'description': wit.get('description'),
                            'color': wit.get('color'),
                            'icon': wit.get('icon'),
                            'isDisabled': wit.get('isDisabled', False),
                            'referenceName': wit.get('referenceName')
                        }
                        enhanced_work_item_types.append(enhanced_wit)
                    
                    return StandardResponse.success(
                        data={"work_item_types": enhanced_work_item_types},
                        message="Work item types retrieved successfully"
                    )
                else:
                    return StandardResponse.error(
                        title="Failed to fetch work item types",
                        detail=f"Failed to fetch work item types: {resp.status_code}",
                        status_code=resp.status_code,
                        instance=request.path
                    )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )


class AzureDevOpsProjectMetadataView(APIView):
    """Get Azure DevOps project metadata including work item types - similar to JiraProjectMetadataView"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return asyncio.run(self.handle_get(request))

    async def handle_get(self, request):
        project_id = request.query_params.get('projectId')
        if not project_id:
            return StandardResponse.validation_error(
                detail="projectId parameter is required",
                errors=[{"field": "projectId", "message": "This parameter is required."}],
                instance=request.path
            )

        # Prefer project-scoped Azure config if present
        organization = org
        pat_token = pat
        project_name = project
        
        try:
            stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
            items = cosmos_service.query_items('projects', 'SELECT * FROM c WHERE c.id = @id', [{"name": "@id", "value": stored_id}])
            if items and items[0].get('azure_config'):
                cfg = items[0]['azure_config']
                organization = cfg.get('organization') or organization
                pat_token = cfg.get('pat_token') or pat_token
                project_name = cfg.get('project_name') or project_name
        except Exception:
            pass

        auth_token = base64.b64encode(f":{pat_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_token}",
            "Accept": "application/json"
        }

        try:
            # Get project details and work item types in parallel
            project_url = f"https://dev.azure.com/{organization}/_apis/projects/{project_name}?includeCapabilities=true&api-version=7.0"
            work_item_types_url = f"https://dev.azure.com/{organization}/{project_name}/_apis/wit/workitemtypes?api-version=7.1"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch project and work item types in parallel
                project_resp, work_item_types_resp = await asyncio.gather(
                    client.get(project_url, headers=headers),
                    client.get(work_item_types_url, headers=headers)
                )
                
                if project_resp.status_code == 200 and work_item_types_resp.status_code == 200:
                    project_data = project_resp.json()
                    work_item_types_data = work_item_types_resp.json()
                    
                    # Transform work item types
                    valid_work_item_types = [
                        {
                            'name': wit.get('name'),
                            'description': wit.get('description'),
                            'color': wit.get('color'),
                            'icon': wit.get('icon'),
                            'isDisabled': wit.get('isDisabled', False),
                            'referenceName': wit.get('referenceName')
                        }
                        for wit in work_item_types_data.get("value", [])
                        if not wit.get('isDisabled', False)
                    ]
                    
                    # Get process template info
                    template_name = (
                        ((project_data.get("capabilities") or {})
                          .get("processTemplate") or {})
                          .get("templateName")
                    )
                    
                    metadata = {
                        'project': {
                            'id': project_data.get('id'),
                            'name': project_data.get('name'),
                            'description': project_data.get('description'),
                            'state': project_data.get('state'),
                            'visibility': project_data.get('visibility'),
                            'lastUpdateTime': project_data.get('lastUpdateTime'),
                            'templateName': template_name
                        },
                        'work_item_types': valid_work_item_types,
                        'available_work_item_type_names': [wit['name'] for wit in valid_work_item_types]
                    }
                    
                    return StandardResponse.success(
                        data={"metadata": metadata},
                        message="Project metadata retrieved successfully"
                    )
                else:
                    return StandardResponse.error(
                        title="Failed to fetch project metadata",
                        detail=f"Failed to fetch project metadata. Project status: {project_resp.status_code}, Work item types status: {work_item_types_resp.status_code}",
                        status_code=400,
                        instance=request.path
                    )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )


class AzureDevOpsProjectsListView(APIView):
    """Get all Azure DevOps projects from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        try:
            # Get all Azure DevOps projects from Cosmos DB
            projects = cosmos_service.query_items("projects", "SELECT * FROM c WHERE c.type = 'project' AND c.platform = 'azure_devops' ORDER BY c.created_at DESC")
            
            return StandardResponse.success(
                data={
                    "projects": projects,
                    "count": len(projects)
                },
                message="Azure DevOps projects retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch Azure DevOps projects: {str(e)}",
                instance=request.path
            )


class AzureDevOpsProjectDetailView(APIView):
    """Get specific Azure DevOps project by ID from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request, project_id):
        try:
            # Ensure project_id has the correct prefix
            stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
            
            project_data = cosmos_service.query_items(
                "projects", 
                "SELECT * FROM c WHERE c.id = @id AND c.platform = 'azure_devops'",
                [{"name": "@id", "value": stored_id}]
            )
            
            if not project_data:
                return StandardResponse.not_found(
                    detail="Azure DevOps project not found",
                    instance=request.path
                )
            
            return StandardResponse.success(
                data=project_data[0],
                message="Azure DevOps project retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch Azure DevOps project: {str(e)}",
                instance=request.path
            )


class AzureDevOpsWorkItemsListView(APIView):
    """Get all Azure DevOps work items from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        try:
            # Get all Azure DevOps work items from Cosmos DB
            work_items = cosmos_service.query_items("work_items", "SELECT * FROM c WHERE c.type = 'work_item' AND c.platform = 'azure_devops' ORDER BY c.creation_date DESC")
            
            return StandardResponse.success(
                data={
                    "work_items": work_items,
                    "count": len(work_items)
                },
                message="Azure DevOps work items retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch Azure DevOps work items: {str(e)}",
                instance=request.path
            )


class AzureDevOpsWorkItemDetailView(APIView):
    """Get specific Azure DevOps work item by ID from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request, work_item_id):
        try:
            work_item_data = cosmos_service.get_work_item(work_item_id)
            if not work_item_data or work_item_data.get('platform') != 'azure_devops':
                return StandardResponse.not_found(
                    detail="Azure DevOps work item not found",
                    instance=request.path
                )
            
            return StandardResponse.success(
                data=work_item_data,
                message="Azure DevOps work item retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch Azure DevOps work item: {str(e)}",
                instance=request.path
            )