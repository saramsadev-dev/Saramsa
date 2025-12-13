import httpx
import asyncio
import base64
import uuid
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from aiCore.cosmos_service import cosmos_service
from integrations.service import integrations_service
from rest_framework.permissions import IsAuthenticated
from authapp.permissions import NoAuthentication, IsAdminOrUser
from apis.response import StandardResponse



def to_adf_description(text):
    """Convert plain text into Atlassian Document Format (ADF)"""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        ]
    }


class JiraConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return stored Jira config for the authenticated user."""
        try:
            user_id = getattr(request.user, 'id', None)
            if not user_id:
                return StandardResponse.unauthorized(
                    detail="Authentication required",
                    instance=request.path
                )

            # Get Jira integration account
            account = integrations_service.get_integration_account_by_provider(user_id, 'jira')
            
            if account:
                return StandardResponse.success(
                    data={
                        "domain": account['metadata']['domain'],
                        "email": account['metadata']['email'],
                        "has_token": True,  # Don't expose actual token
                        "saved_at": account.get('savedAt'),
                    },
                    message="Jira configuration retrieved successfully"
                )

            return StandardResponse.not_found(
                detail="No Jira integration found",
                instance=request.path
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )

    def post(self, request):
        return asyncio.run(self.handle_post(request))

    async def handle_post(self, request):
        """Configure Jira connection and fetch projects"""
        domain = request.data.get("domain")
        email = request.data.get("email")
        api_token = request.data.get("api_token")

        print(f"Jira Config - Domain: {domain}")
        print(f"Jira Config - Email: {email}")
        print(f"Jira Config - API Token: "
              f"{api_token[:10]}..." if api_token else "No API token")

        if not domain or not email or not api_token:
            return StandardResponse.validation_error(
                detail="Domain, email, and api_token are all required",
                errors=[
                    {"field": "domain", "message": "This field is required."} if not domain else None,
                    {"field": "email", "message": "This field is required."} if not email else None,
                    {"field": "api_token", "message": "This field is required."} if not api_token else None
                ],
                instance=request.path
            )

        # Create basic auth header
        auth_token = base64.b64encode(
            f"{email}:{api_token}".encode()
        ).decode()
        headers = {
            "Authorization": f"Basic {auth_token}",
            "Accept": "application/json"
        }

        # Fetch projects from Jira
        url = f"https://{domain}/rest/api/3/project"

        try:
            print(f"Jira Config - Making request to: {url}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                print(f"Jira Config - Response status: {response.status_code}")
                
                if response.status_code == 200:
                    projects_data = response.json()
                    
                    # Transform projects to match frontend expectations
                    transformed_projects = []
                    for project in projects_data:
                        transformed_projects.append({
                            "id": project.get("id"),
                            "key": project.get("key"),
                            "name": project.get("name"),
                            "description": f"Project Key: {project.get('key')}",
                            "projectTypeKey": project.get("projectTypeKey"),
                            "style": project.get("style"),
                            "isCompanyManaged": project.get("style") == "classic",
                            "isTeamManaged": project.get("style") == "next-gen",
                            "projectCategory": project.get("projectCategory", {}).get("name") if project.get("projectCategory") else None
                        })
                    
                    # Create or update integration account
                    try:
                        user_id = getattr(request.user, 'id', None)
                        if user_id:
                            # Check if integration already exists
                            existing = integrations_service.get_integration_account_by_provider(user_id, 'jira')
                            if not existing:
                                integrations_service.create_jira_integration(
                                    user_id=user_id,
                                    domain=domain,
                                    email=email,
                                    api_token=api_token
                                )
                                print(f"Created Jira integration for user {user_id}")
                            else:
                                print(f"Jira integration already exists for user {user_id}")
                    except Exception as e:
                        print(f"Warning: failed to create integration account: {e}")
                    
                    return StandardResponse.success(
                        data={
                            "projects": transformed_projects,
                            "domain": domain
                        },
                        message="Jira projects retrieved successfully"
                    )
                else:
                    error_message = "Failed to connect to Jira"
                    try:
                        error_data = response.json()
                        if "errorMessages" in error_data:
                            error_message = "; ".join(error_data["errorMessages"])
                        elif "message" in error_data:
                            error_message = error_data["message"]
                    except Exception:
                        pass
                    
                    return StandardResponse.error(
                        title="Jira Connection Failed",
                        detail=error_message,
                        status_code=response.status_code,
                        instance=request.path
                    )
                    
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Connection error: {str(e)}",
                instance=request.path
            )


class JiraProjectCreationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a new Jira project entity in the database"""
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
            jira_project_id = request.data.get('jira_project_id')
            jira_project_key = request.data.get('jira_project_key')
            jira_project_name = request.data.get('jira_project_name')
            jira_domain = request.data.get('jira_domain')
            jira_email = request.data.get('jira_email')
            jira_api_token = request.data.get('jira_api_token')
            
            if not all([project_name, jira_project_id, jira_project_key, jira_domain, jira_email, jira_api_token]):
                return StandardResponse.validation_error(
                    detail='Missing required fields: project_name, jira_project_id, jira_project_key, jira_domain, jira_email, jira_api_token',
                    instance=request.path
                )
            
            # Create project data structure
            project_id = str(uuid.uuid4())
            project_data = {
                'id': f'project_{project_id}',
                'type': 'project',
                'platform': 'jira',
                'name': project_name,
                'owner_user_id': str(user.id),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'external_project_id': jira_project_id,
                'external_project_key': jira_project_key,
                'external_project_name': jira_project_name,
                'organization': jira_domain,
                'jira_config': {
                    'domain': jira_domain,
                    'email': jira_email,
                    'api_token': jira_api_token,
                    'project_id': jira_project_id,
                    'project_key': jira_project_key,
                    'project_name': jira_project_name
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
                    'platform': 'jira',
                    'jira_project_key': jira_project_key,
                    'jira_project_name': jira_project_name,
                    'created_at': project_data['created_at']
                },
                message='Jira project created successfully',
                instance=f"/api/projects/{project_id}"
            )
            
        except Exception as e:
            print(f"Error creating Jira project: {e}")
            return StandardResponse.internal_server_error(
                detail=f'Project creation failed: {str(e)}',
                instance=request.path
            )


class JiraProjectsView(APIView):
    permission_classes = [NoAuthentication]

    def get(self, request):
        return asyncio.run(self.handle_get(request))

    async def handle_get(self, request):
        # Prefer project-scoped Jira config if provided
        project_id = request.query_params.get('projectId')
        email = settings.JIRA_EMAIL
        api_token = settings.JIRA_API_TOKEN
        domain = settings.JIRA_DOMAIN
        if project_id:
            try:
                stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
                items = cosmos_service.query_items('projects', 'SELECT * FROM c WHERE c.id = @id', [{"name": "@id", "value": stored_id}])
                if items and items[0].get('jira_config'):
                    cfg = items[0]['jira_config']
                    email = cfg.get('email') or email
                    api_token = cfg.get('api_token') or api_token
                    domain = cfg.get('domain') or domain
            except Exception:
                pass

        auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json"
        }

        try:
            url = f"https://{domain}/rest/api/3/project"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=headers)
                
                if resp.status_code == 200:
                    projects = resp.json()
                    
                    # Enhance project data with management style info
                    enhanced_projects = []
                    for project in projects:
                        enhanced_project = {
                            'id': project.get('id'),
                            'key': project.get('key'),
                            'name': project.get('name'),
                            'projectTypeKey': project.get('projectTypeKey'),
                            'style': project.get('style'),
                            'isCompanyManaged': project.get('style') == 'classic',
                            'isTeamManaged': project.get('style') == 'next-gen',
                            'projectCategory': project.get('projectCategory', {}).get('name') if project.get('projectCategory') else None
                        }
                        enhanced_projects.append(enhanced_project)
                    
                    return StandardResponse.success(
                        data={"projects": enhanced_projects},
                        message="Jira projects retrieved successfully"
                    )
                else:
                    return StandardResponse.error(
                        title="Failed to fetch projects",
                        detail=f"Failed to fetch projects: {resp.status_code}",
                        status_code=resp.status_code,
                        instance=request.path
                    )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )


class JiraIssueTypesView(APIView):
    permission_classes = [NoAuthentication]

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

        # Prefer project-scoped Jira config if present
        email = settings.JIRA_EMAIL
        api_token = settings.JIRA_API_TOKEN
        domain = settings.JIRA_DOMAIN
        try:
            stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
            items = cosmos_service.query_items('projects', 'SELECT * FROM c WHERE c.id = @id', [{"name": "@id", "value": stored_id}])
            if items and items[0].get('jira_config'):
                cfg = items[0]['jira_config']
                email = cfg.get('email') or email
                api_token = cfg.get('api_token') or api_token
                domain = cfg.get('domain') or domain
        except Exception:
            pass

        auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json"
        }

        try:
            url = f"https://{domain}/rest/api/3/issuetype/project?projectId={project_id}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=headers)
                
                if resp.status_code == 200:
                    issue_types = resp.json()
                    
                    # Filter out subtasks and enhance with metadata
                    enhanced_issue_types = []
                    for issue_type in issue_types:
                        if not issue_type.get('subtask', False):
                            enhanced_issue_type = {
                                'id': issue_type.get('id'),
                                'name': issue_type.get('name'),
                                'description': issue_type.get('description'),
                                'iconUrl': issue_type.get('iconUrl'),
                                'hierarchyLevel': issue_type.get('hierarchyLevel', 0),
                                'isSubtask': issue_type.get('subtask', False)
                            }
                            enhanced_issue_types.append(enhanced_issue_type)
                    
                    return StandardResponse.success(
                        data={"issue_types": enhanced_issue_types},
                        message="Issue types retrieved successfully"
                    )
                else:
                    return StandardResponse.error(
                        title="Failed to fetch issue types",
                        detail=f"Failed to fetch issue types: {resp.status_code}",
                        status_code=resp.status_code,
                        instance=request.path
                    )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )


class JiraProjectMetadataView(APIView):
    permission_classes = [NoAuthentication]

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

        # Prefer project-scoped Jira config if present
        email = settings.JIRA_EMAIL
        api_token = settings.JIRA_API_TOKEN
        domain = settings.JIRA_DOMAIN
        try:
            stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
            items = cosmos_service.query_items('projects', 'SELECT * FROM c WHERE c.id = @id', [{"name": "@id", "value": stored_id}])
            if items and items[0].get('jira_config'):
                cfg = items[0]['jira_config']
                email = cfg.get('email') or email
                api_token = cfg.get('api_token') or api_token
                domain = cfg.get('domain') or domain
        except Exception:
            pass

        auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json"
        }

        try:
            # Get project details
            project_url = f"https://{domain}/rest/api/3/project/{project_id}"
            issue_types_url = f"https://{domain}/rest/api/3/issuetype/project?projectId={project_id}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch project and issue types in parallel
                project_resp, issue_types_resp = await asyncio.gather(
                    client.get(project_url, headers=headers),
                    client.get(issue_types_url, headers=headers)
                )
                
                if project_resp.status_code == 200 and issue_types_resp.status_code == 200:
                    project_data = project_resp.json()
                    issue_types_data = issue_types_resp.json()
                    
                    # Filter out subtasks
                    valid_issue_types = [
                        {
                            'id': it.get('id'),
                            'name': it.get('name'),
                            'description': it.get('description'),
                            'hierarchyLevel': it.get('hierarchyLevel', 0)
                        }
                        for it in issue_types_data
                        if not it.get('subtask', False)
                    ]
                    
                    metadata = {
                        'project': {
                            'id': project_data.get('id'),
                            'key': project_data.get('key'),
                            'name': project_data.get('name'),
                            'projectTypeKey': project_data.get('projectTypeKey'),
                            'style': project_data.get('style'),
                            'isCompanyManaged': project_data.get('style') == 'classic',
                            'isTeamManaged': project_data.get('style') == 'next-gen'
                        },
                        'issue_types': valid_issue_types,
                        'available_issue_type_names': [it['name'] for it in valid_issue_types]
                    }
                    
                    return StandardResponse.success(
                        data={"metadata": metadata},
                        message="Project metadata retrieved successfully"
                    )
                else:
                    return StandardResponse.error(
                        title="Failed to fetch project metadata",
                        detail=f"Failed to fetch project metadata. Project status: {project_resp.status_code}, Issue types status: {issue_types_resp.status_code}",
                        status_code=400,
                        instance=request.path
                    )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=str(e),
                instance=request.path
            )


class CreateJiraIssuesView(APIView):
    """
    DEPRECATED: Use UserStorySubmissionView in insightsGenerator for unified submission
    This endpoint is kept for backward compatibility
    """
    permission_classes = [NoAuthentication]

    def post(self, request):
        return asyncio.run(self.handle_post(request))

    async def handle_post(self, request):
        issues = request.data.get("items", [])
        project_id = request.data.get("project_id")
        project_key = request.data.get("project_key")
        
        if not isinstance(issues, list) or not issues:
            return StandardResponse.validation_error(
                detail="Payload must contain a non-empty list under 'items'",
                errors=[{"field": "items", "message": "This field must be a non-empty list."}],
                instance=request.path
            )

        if not project_id and not project_key:
            return StandardResponse.validation_error(
                detail="Either project_id or project_key is required",
                errors=[
                    {"field": "project_id", "message": "Either project_id or project_key is required."},
                    {"field": "project_key", "message": "Either project_id or project_key is required."}
                ],
                instance=request.path
            )

        # Prefer project-scoped Jira config if present
        email = settings.JIRA_EMAIL
        api_token = settings.JIRA_API_TOKEN
        domain = settings.JIRA_DOMAIN
        try:
            # Allow either DB project id or raw uuid
            stored_id = None
            if project_id:
                stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
            elif request.data.get('db_project_id'):
                pid = request.data.get('db_project_id')
                stored_id = pid if pid.startswith('project_') else f'project_{pid}'
            if stored_id:
                items = cosmos_service.query_items('projects', 'SELECT * FROM c WHERE c.id = @id', [{"name": "@id", "value": stored_id}])
                if items and items[0].get('jira_config'):
                    cfg = items[0]['jira_config']
                    email = cfg.get('email') or email
                    api_token = cfg.get('api_token') or api_token
                    domain = cfg.get('domain') or domain
                    # Default project_key from config if not provided
                    if not project_key:
                        project_key = cfg.get('project_key') or project_key
        except Exception:
            pass

        # Use provided project_key or fallback to settings
        if not project_key:
            project_key = settings.JIRA_PROJECT_KEY

        auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async def create_issue(client, item):
            summary = item.get("title")
            description = item.get("description", "")
            issue_type = item.get("type", "Task")
            priority = item.get("priority", "Medium")
            labels = item.get("labels", [])
            acceptance_criteria = item.get("acceptance_criteria", "")
            business_value = item.get("business_value", "")

            if not summary:
                return {"success": False, "error": "Title is required", "item": item}

            # Build description with additional fields
            full_description = description
            if acceptance_criteria:
                full_description += f"\n\n**Acceptance Criteria:**\n{acceptance_criteria}"
            if business_value:
                full_description += f"\n\n**Business Value:**\n{business_value}"

            # Add default labels
            if "ai-feedback" not in labels:
                labels.append("ai-feedback")
            if "auto-created" not in labels:
                labels.append("auto-created")

            payload = {
                "fields": {
                    "project": { "id": project_id } if project_id else { "key": project_key },
                    "summary": summary,
                    "description": to_adf_description(full_description),
                    "issuetype": { "name": issue_type },
                    "labels": labels
                }
            }

            # Add priority if specified and supported by issue type
            # Note: Epic issue types often don't support priority field
            if priority and priority.lower() != "medium" and issue_type.lower() != "epic":
                priority_map = {
                    "critical": "Highest",
                    "high": "High", 
                    "medium": "Medium",
                    "low": "Low"
                }
                mapped_priority = priority_map.get(priority.lower(), "Medium")
                payload["fields"]["priority"] = { "name": mapped_priority }

            try:
                url = f"https://{domain}/rest/api/3/issue"
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in [200, 201]:
                    issue_data = resp.json()
                    return {
                        "success": True, 
                        "issue": issue_data,
                        "url": f"https://{domain}/browse/{issue_data.get('key', '')}"
                    }
                else:
                    return {
                        "success": False,
                        "status": resp.status_code,
                        "error": await resp.aread(),
                        "item": item
                    }
            except Exception as e:
                return {"success": False, "error": str(e), "item": item}

        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [create_issue(client, item) for item in issues]
            results = await asyncio.gather(*tasks)

        # Save work item creation history to Cosmos DB
        try:
            work_item_id = str(uuid.uuid4())
            work_item_data = {
                'id': f'work_item_{work_item_id}',
                'type': 'work_item',
                'platform': 'jira',
                'domain': domain,
                'project_id': project_id,
                'project_key': project_key,
                'issues_requested': len(issues),
                'issues_created': len([r for r in results if r.get('success')]),
                'creation_date': datetime.now().isoformat(),
                'results': results,
                'metadata': {
                    'source': 'api_request',
                    'email': email,
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
                    "total_requested": len(issues),
                    "successful": len([r for r in results if r.get('success')]),
                    "failed": len([r for r in results if not r.get('success')])
                }
            },
            message="Issues creation completed",
            status_code=207
        )


class JiraWorkItemsListView(APIView):
    """Get all Jira work items from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        try:
            # Get all Jira work items from Cosmos DB
            work_items = cosmos_service.query_items("work_items", "SELECT * FROM c WHERE c.type = 'work_item' AND c.platform = 'jira' ORDER BY c.creation_date DESC")
            
            return StandardResponse.success(
                data={
                    "work_items": work_items,
                    "count": len(work_items)
                },
                message="Jira work items retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch Jira work items: {str(e)}",
                instance=request.path
            )


class JiraWorkItemDetailView(APIView):
    """Get specific Jira work item by ID from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request, work_item_id):
        try:
            work_item_data = cosmos_service.get_work_item(work_item_id)
            if not work_item_data or work_item_data.get('platform') != 'jira':
                return StandardResponse.not_found(
                    detail="Jira work item not found",
                    instance=request.path
                )
            
            return StandardResponse.success(
                data=work_item_data,
                message="Jira work item retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch Jira work item: {str(e)}",
                instance=request.path
            )


class JiraProjectsListView(APIView):
    """Get all Jira projects from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request):
        try:
            # Get all Jira projects from Cosmos DB
            projects = cosmos_service.query_items("projects", "SELECT * FROM c WHERE c.type = 'project' AND c.platform = 'jira' ORDER BY c.created_at DESC")
            
            return StandardResponse.success(
                data={
                    "projects": projects,
                    "count": len(projects)
                },
                message="Jira projects retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch Jira projects: {str(e)}",
                instance=request.path
            )


class JiraProjectDetailView(APIView):
    """Get specific Jira project by ID from Cosmos DB"""
    permission_classes = [IsAdminOrUser]
    
    def get(self, request, project_id):
        try:
            # Ensure project_id has the correct prefix
            stored_id = project_id if project_id.startswith('project_') else f'project_{project_id}'
            
            project_data = cosmos_service.query_items(
                "projects", 
                "SELECT * FROM c WHERE c.id = @id AND c.platform = 'jira'",
                [{"name": "@id", "value": stored_id}]
            )
            
            if not project_data:
                return StandardResponse.not_found(
                    detail="Jira project not found",
                    instance=request.path
                )
            
            return StandardResponse.success(
                data=project_data[0],
                message="Jira project retrieved successfully"
            )
        except Exception as e:
            return StandardResponse.internal_server_error(
                detail=f"Failed to fetch Jira project: {str(e)}",
                instance=request.path
            )

