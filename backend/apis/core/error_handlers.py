"""
Standardized error handling for the application.
Provides consistent error responses and logging.
"""

from functools import wraps
from typing import Any, Callable
from rest_framework.response import Response
from rest_framework import status
from .response import StandardResponse
import logging

logger = logging.getLogger(__name__)


def handle_service_errors(func: Callable) -> Callable:
    """
    Decorator to handle service layer errors and return standardized responses.
    
    Usage:
        @handle_service_errors
        def my_view_method(self, request):
            # Your view logic here
            return StandardResponse.success(data=result)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            # Business logic validation errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.warning(f"Validation error in {func_name}: {e}")
            return StandardResponse.validation_error(
                detail=str(e)
            )
        except PermissionError as e:
            # Permission/authorization errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.warning(f"Permission error in {func_name}: {e}")
            return StandardResponse.error(
                title="Permission denied",
                detail=str(e),
                status_code=status.HTTP_403_FORBIDDEN,
                error_type="permission-denied"
            )
        except FileNotFoundError as e:
            # Resource not found errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.warning(f"Resource not found in {func_name}: {e}")
            return StandardResponse.error(
                title="Resource not found",
                detail=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type="resource-not-found"
            )
        except ConnectionError as e:
            # External service connection errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.error(f"Connection error in {func_name}: {e}")
            return StandardResponse.error(
                title="Service unavailable",
                detail="Unable to connect to external service. Please try again later.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error_type="service-unavailable"
            )
        except Exception as e:
            # Unexpected errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.error(f"Unexpected error in {func_name}: {e}", exc_info=True)
            return StandardResponse.internal_server_error(
                detail="An unexpected error occurred. Please try again later."
            )
    
    return wrapper


def handle_async_service_errors(func: Callable) -> Callable:
    """
    Decorator to handle service layer errors in async functions.
    
    Usage:
        @handle_async_service_errors
        async def my_async_view_method(self, request):
            # Your async view logic here
            return StandardResponse.success(data=result)
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            # Business logic validation errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.warning(f"Validation error in {func_name}: {e}")
            return StandardResponse.validation_error(
                detail=str(e)
            )
        except PermissionError as e:
            # Permission/authorization errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.warning(f"Permission error in {func_name}: {e}")
            return StandardResponse.error(
                title="Permission denied",
                detail=str(e),
                status_code=status.HTTP_403_FORBIDDEN,
                error_type="permission-denied"
            )
        except FileNotFoundError as e:
            # Resource not found errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.warning(f"Resource not found in {func_name}: {e}")
            return StandardResponse.error(
                title="Resource not found",
                detail=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type="resource-not-found"
            )
        except ConnectionError as e:
            # External service connection errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.error(f"Connection error in {func_name}: {e}")
            return StandardResponse.error(
                title="Service unavailable",
                detail="Unable to connect to external service. Please try again later.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error_type="service-unavailable"
            )
        except Exception as e:
            # Unexpected errors
            func_name = getattr(func, '__name__', 'unknown_function')
            logger.error(f"Unexpected error in {func_name}: {e}", exc_info=True)
            return StandardResponse.internal_server_error(
                detail="An unexpected error occurred. Please try again later."
            )
    
    return wrapper


class BusinessLogicError(Exception):
    """Custom exception for business logic errors."""
    pass


class ResourceNotFoundError(Exception):
    """Custom exception for resource not found errors."""
    pass


class PermissionDeniedError(Exception):
    """Custom exception for permission denied errors."""
    pass


class ExternalServiceError(Exception):
    """Custom exception for external service errors."""
    pass


def standardize_external_api_response(response_data: dict) -> Response:
    """
    Standardize external API responses to use StandardResponse format.
    
    Args:
        response_data: Dictionary with 'success', 'message'/'error' keys
        
    Returns:
        Standardized Response object
    """
    if response_data.get('success', False):
        return StandardResponse.success(
            data=response_data,
            message=response_data.get('message', 'Operation completed successfully')
        )
    else:
        error_message = response_data.get('error', 'Operation failed')
        return StandardResponse.error(
            title="External service error",
            detail=error_message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="external-service-error"
        )