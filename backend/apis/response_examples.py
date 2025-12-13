"""
Usage of StandardResponse in Django REST Framework views.

This file demonstrates how to use the standardized response format
in your API views and viewsets.
"""

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from apis.response import StandardResponse


# ============================================================================
# Example 1: Class-based view with success responses
# ============================================================================

class UserListView(APIView):
    """Example view showing various success responses"""
    
    def get(self, request):
        """Get list of users - 200 OK"""
        users = [
            {"id": "1", "username": "john", "email": "john@example.com"},
            {"id": "2", "username": "jane", "email": "jane@example.com"}
        ]
        
        return StandardResponse.success(
            data=users,
            message="Users retrieved successfully"
        )
    
    def post(self, request):
        """Create a new user - 201 Created"""
        # Your validation and creation logic here
        new_user = {
            "id": "3",
            "username": request.data.get("username"),
            "email": request.data.get("email")
        }
        
        return StandardResponse.created(
            data=new_user,
            message="User created successfully",
            instance=f"/api/v1/users/{new_user['id']}"
        )


# ============================================================================
# Example 2: Function-based view with error handling
# ============================================================================

@api_view(['GET'])
def get_user_detail(request, user_id):
    """Get user by ID with error handling"""
    
    # Simulate user lookup
    user = None  # Your database lookup here
    
    if not user:
        return StandardResponse.not_found(
            detail=f"User with ID '{user_id}' was not found.",
            instance=request.path
        )
    
    return StandardResponse.success(
        data=user,
        message="User retrieved successfully"
    )


# ============================================================================
# Example 3: Validation errors
# ============================================================================

@api_view(['POST'])
def create_project(request):
    """Create project with validation"""
    
    # Manual validation example
    errors = []
    
    if not request.data.get('name'):
        errors.append({
            "field": "name",
            "message": "This field is required."
        })
    
    if not request.data.get('description'):
        errors.append({
            "field": "description",
            "message": "This field is required."
        })
    
    if errors:
        return StandardResponse.validation_error(
            detail="One or more fields are invalid.",
            errors=errors,
            instance=request.path
        )
    
    # Create project logic here
    project = {
        "id": "proj-123",
        "name": request.data.get('name'),
        "description": request.data.get('description')
    }
    
    return StandardResponse.created(
        data=project,
        message="Project created successfully",
        instance=f"/api/v1/projects/{project['id']}"
    )


# ============================================================================
# Example 4: Authorization errors
# ============================================================================

@api_view(['DELETE'])
def delete_project(request, project_id):
    """Delete project with permission check"""
    
    # Check if user owns the project
    user_owns_project = False  # Your logic here
    
    if not user_owns_project:
        return StandardResponse.forbidden(
            detail="You do not have permission to delete this project.",
            instance=request.path
        )
    
    # Delete logic here
    
    return StandardResponse.success(
        data=None,
        message="Project deleted successfully"
    )


# ============================================================================
# Example 5: Empty results
# ============================================================================

@api_view(['GET'])
def search_projects(request):
    """Search projects - may return empty results"""
    
    query = request.query_params.get('q', '')
    results = []  # Your search logic here
    
    if not results:
        return StandardResponse.success(
            data=[],
            message="No projects found matching your search criteria."
        )
    
    return StandardResponse.success(
        data=results,
        message=f"Found {len(results)} projects"
    )


# ============================================================================
# Example 6: Custom error with additional metadata
# ============================================================================

@api_view(['POST'])
def process_file(request):
    """Process file upload with custom error handling"""
    
    try:
        # Your file processing logic
        file = request.FILES.get('file')
        
        if not file:
            return StandardResponse.validation_error(
                detail="No file was uploaded.",
                errors=[{
                    "field": "file",
                    "message": "This field is required."
                }],
                instance=request.path
            )
        
        # Process file...
        result = {"file_id": "file-123", "status": "processed"}
        
        return StandardResponse.success(
            data=result,
            message="File processed successfully",
            meta={"processing_time_ms": 1234}  # Custom metadata
        )
        
    except Exception as e:
        return StandardResponse.internal_server_error(
            detail="An error occurred while processing the file.",
            instance=request.path
        )


# ============================================================================
# Example Response Formats
# ============================================================================

"""
SUCCESS RESPONSE (200 OK):
{
    "success": true,
    "message": "Users retrieved successfully",
    "data": [
        {"id": "1", "username": "john", "email": "john@example.com"},
        {"id": "2", "username": "jane", "email": "jane@example.com"}
    ],
    "meta": {
        "request_id": "c0a80123-4567-89ab-cdef-0123456789ab",
        "timestamp": "2025-12-04T09:15:23.123Z"
    }
}

CREATED RESPONSE (201 Created):
{
    "success": true,
    "message": "User created successfully",
    "data": {
        "id": "3",
        "username": "alice",
        "email": "alice@example.com"
    },
    "meta": {
        "request_id": "c0a80123-4567-89ab-cdef-0123456789ab",
        "timestamp": "2025-12-04T09:15:23.123Z",
        "instance": "/api/v1/users/3"
    }
}

VALIDATION ERROR (400 Bad Request):
{
    "type": "https://api.saramsa.com/problems/validation-error",
    "title": "Validation error",
    "status": 400,
    "detail": "One or more fields are invalid.",
    "instance": "/api/v1/projects",
    "errors": [
        {
            "field": "name",
            "message": "This field is required."
        },
        {
            "field": "description",
            "message": "This field is required."
        }
    ],
    "request_id": "c0a80123-4567-89ab-cdef-0123456789ab",
    "timestamp": "2025-12-04T09:15:23.123Z"
}

NOT FOUND ERROR (404 Not Found):
{
    "type": "https://api.saramsa.com/problems/not-found",
    "title": "Not found",
    "status": 404,
    "detail": "User with ID '999' was not found.",
    "instance": "/api/v1/users/999",
    "request_id": "c0a80123-4567-89ab-cdef-0123456789ab",
    "timestamp": "2025-12-04T09:15:23.123Z"
}

FORBIDDEN ERROR (403 Forbidden):
{
    "type": "https://api.saramsa.com/problems/forbidden",
    "title": "Forbidden",
    "status": 403,
    "detail": "You do not have permission to delete this project.",
    "instance": "/api/v1/projects/proj-123",
    "request_id": "c0a80123-4567-89ab-cdef-0123456789ab",
    "timestamp": "2025-12-04T09:15:23.123Z"
}
"""
