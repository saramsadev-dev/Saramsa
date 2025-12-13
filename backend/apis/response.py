from rest_framework.response import Response
from rest_framework import status
from typing import Any, Optional, Dict, List
from datetime import datetime
from apis.request_context import request_id_var

class StandardResponse:
    """
    Standard API response wrapper following:
    - Success: { success, message, data, meta }
    - Errors: RFC 7807 Problem Details format
    """

    # Base URL for error types (update with your domain)
    ERROR_TYPE_BASE = "https://api.saramsa.com/problems"

    @staticmethod
    def _get_request_id() -> Optional[str]:
        """Get request ID from context (set by middleware)"""
        try:
            return request_id_var.get()
        except LookupError:
            return None

    @staticmethod
    def _get_meta() -> Dict[str, Any]:
        """Build standard meta object"""
        meta = {
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        request_id = StandardResponse._get_request_id()
        if request_id:
            meta["request_id"] = request_id
        
        return meta

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Operation completed successfully",
        meta: Optional[Dict] = None,
        status_code: int = status.HTTP_200_OK
    ) -> Response:
        """
        Standard success response format:
        {
            "success": true,
            "message": "...",
            "data": {...},
            "meta": { "request_id": "...", "timestamp": "..." }
        }
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data if data is not None else [],
        }
        
        # Merge custom meta with standard meta
        base_meta = StandardResponse._get_meta()
        if meta:
            base_meta.update(meta)
        response_data["meta"] = base_meta
        
        return Response(response_data, status=status_code)

    @staticmethod
    def error(
        title: str,
        detail: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_type: Optional[str] = None,
        instance: Optional[str] = None,
        errors: Optional[List[Dict[str, str]]] = None
    ) -> Response:
        """
        RFC 7807 Problem Details error response format:
        {
            "type": "https://api.saramsa.com/problems/...",
            "title": "...",
            "status": 400,
            "detail": "...",
            "instance": "/api/v1/users",
            "errors": [...],  // optional field-level errors
            "request_id": "...",
            "timestamp": "..."
        }
        """
        # Determine error type from status code if not provided
        if not error_type:
            if status_code == 400:
                error_type = "validation-error"
            elif status_code == 401:
                error_type = "unauthorized"
            elif status_code == 403:
                error_type = "forbidden"
            elif status_code == 404:
                error_type = "not-found"
            elif status_code == 409:
                error_type = "conflict"
            elif status_code >= 500:
                error_type = "internal-server-error"
            else:
                error_type = "bad-request"
        
        response_data = {
            "type": f"{StandardResponse.ERROR_TYPE_BASE}/{error_type}",
            "title": title,
            "status": status_code,
            "detail": detail,
        }
        
        if instance:
            response_data["instance"] = instance
        
        # Add field-level errors if provided
        if errors:
            response_data["errors"] = errors
        
        # Add request_id and timestamp
        meta = StandardResponse._get_meta()
        if "request_id" in meta:
            response_data["request_id"] = meta["request_id"]
        response_data["timestamp"] = meta["timestamp"]
        
        return Response(response_data, status=status_code)

    @staticmethod
    def validation_error(
        detail: str = "One or more fields are invalid.",
        errors: Optional[List[Dict[str, str]]] = None,
        instance: Optional[str] = None
    ) -> Response:
        """Convenience method for validation errors"""
        return StandardResponse.error(
            title="Validation error",
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="validation-error",
            instance=instance,
            errors=errors
        )

    @staticmethod
    def unauthorized(
        detail: str = "Authentication credentials were not provided or are invalid.",
        instance: Optional[str] = None
    ) -> Response:
        """Convenience method for 401 Unauthorized"""
        return StandardResponse.error(
            title="Unauthorized",
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="unauthorized",
            instance=instance
        )

    @staticmethod
    def forbidden(
        detail: str = "You do not have permission to perform this action.",
        instance: Optional[str] = None
    ) -> Response:
        """Convenience method for 403 Forbidden"""
        return StandardResponse.error(
            title="Forbidden",
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="forbidden",
            instance=instance
        )

    @staticmethod
    def not_found(
        detail: str = "The requested resource was not found.",
        instance: Optional[str] = None
    ) -> Response:
        """Convenience method for 404 Not Found"""
        return StandardResponse.error(
            title="Not found",
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="not-found",
            instance=instance
        )

    @staticmethod
    def internal_server_error(
        detail: str = "An unexpected error occurred. Please try again later.",
        instance: Optional[str] = None
    ) -> Response:
        """Convenience method for 500 Internal Server Error"""
        return StandardResponse.error(
            title="Internal server error",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="internal-server-error",
            instance=instance
        )

    @staticmethod
    def created(
        data: Any = None,
        message: str = "Resource created successfully",
        instance: Optional[str] = None
    ) -> Response:
        """201 Created response"""
        response = StandardResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED
        )
        
        if instance:
            response.data["meta"]["instance"] = instance
        
        return response
