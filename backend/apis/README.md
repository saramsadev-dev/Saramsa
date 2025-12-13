# API Response Standards

## Overview

All API endpoints use the `StandardResponse` class for consistent response formatting.

## Usage

```python
from apis.response import StandardResponse

# Success (200)
return StandardResponse.success(
    data={"items": []},
    message="Items retrieved successfully"
)

# Created (201)
return StandardResponse.created(
    data={"id": "123"},
    message="Item created successfully",
    instance="/api/items/123"
)

# Validation Error (400)
return StandardResponse.validation_error(
    detail="Invalid input",
    errors=[{"field": "name", "message": "Required"}],
    instance=request.path
)

# Unauthorized (401)
return StandardResponse.unauthorized(
    detail="Authentication required",
    instance=request.path
)

# Not Found (404)
return StandardResponse.not_found(
    detail="Resource not found",
    instance=request.path
)

# Server Error (500)
return StandardResponse.internal_server_error(
    detail="Something went wrong",
    instance=request.path
)
```

## Response Formats

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "meta": {
    "request_id": "abc-123",
    "timestamp": "2025-12-06T10:30:00.000Z"
  }
}
```

### Error Response (RFC 7807)
```json
{
  "type": "https://api.saramsa.com/problems/validation-error",
  "title": "Validation error",
  "status": 400,
  "detail": "One or more fields are invalid",
  "instance": "/api/v1/users",
  "errors": [
    {
      "field": "email",
      "message": "This field is required."
    }
  ],
  "request_id": "abc-123",
  "timestamp": "2025-12-06T10:30:00.000Z"
}
```

## Files

- `response.py` - StandardResponse class
- `exceptions.py` - Custom exception handler
- `response_examples.py` - Usage examples
- `request_context.py` - Request ID tracking

## Configuration

Exception handler is configured in `settings.py`:

```python
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apis.exceptions.custom_exception_handler',
}
```

## Benefits

- ✅ Consistent response format
- ✅ RFC 7807 compliant errors
- ✅ Automatic request ID tracking
- ✅ Field-level validation errors
- ✅ Better debugging
