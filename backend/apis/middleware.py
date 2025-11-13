import os
import uuid
import time
import logging
import json
from django.utils.deprecation import MiddlewareMixin
from opentelemetry import trace, context as otel_context
from opentelemetry.trace import Status, StatusCode
from .otel import log_custom_event, log_custom_metric
from .request_context import request_id_var, token_usage_var
from .logging_filters import redact_headers, redact_payload

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('apis.security')

LOG_REQUEST_BODIES = os.getenv('LOG_REQUEST_BODIES', 'false').lower() == 'true'
SLOW_REQUEST_MS = int(os.getenv('SLOW_REQUEST_MS', '1000'))

class RequestResponseLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log request and response details with OpenTelemetry integration
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        """Log request details"""
        # Start timing
        request.start_time = time.time()
        
        # Get current span if available
        current_span = trace.get_current_span()
        
        # Correlation ID: use incoming or generate
        request_id = (
            request.headers.get('X-Request-ID')
            or request.headers.get('X-Correlation-ID')
            or str(uuid.uuid4())
        )
        request.request_id = request_id
        request_id_var.set(request_id)
        
        # Start a manual server span to ensure trace correlation
        try:
            tracer = trace.get_tracer("apis.middleware")
            span_name = f"HTTP {request.method} {request.path}"
            span = tracer.start_span(span_name)
            # Make it current so logs include trace_id/span_id
            token = otel_context.attach(otel_context.set_span_in_context(span))
            # Save to request to finish later
            request._otel_span = span
            request._otel_token = token
            # Set initial attributes
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.target", request.path)
            client_ip = self._get_client_ip(request)
            user_id = str(request.user) if request.user.is_authenticated else 'anonymous'
            span.set_attribute("http.client_ip", client_ip)
            span.set_attribute("enduser.id", user_id)
            span.set_attribute("http.request_id", request_id)
        except Exception:
            request._otel_span = None
            request._otel_token = None

        # Prepare request metadata for final single-line access log
        safe_headers = redact_headers(dict(request.headers))
        request._client_ip = self._get_client_ip(request)
        request._request_id = request_id
        request._user_agent = safe_headers.get('User-Agent') or safe_headers.get('user-agent')
        request._route = getattr(getattr(request, 'resolver_match', None), 'route', None) or request.path
        try:
            request._request_len = int(request.META.get('CONTENT_LENGTH') or 0)
        except Exception:
            request._request_len = 0
        
        # Add custom attributes to span
        if current_span:
            try:
                current_span.set_attribute("http.request_id", request_id)
                current_span.set_attribute("http.request.method", request.method)
                current_span.set_attribute("http.request.path", request.path)
                user_val = str(request.user) if request.user.is_authenticated else 'anonymous'
                current_span.set_attribute("http.request.user", user_val)
                current_span.set_attribute("http.request.ip", request._client_ip)
            except Exception:
                pass
        
        # Log custom event (without referencing non-existent dict)
        try:
            log_custom_event("request_started", {
                'method': request.method,
                'path': request.path,
                'ip': getattr(request, '_client_ip', None),
                'user': str(request.user) if request.user.is_authenticated else 'anonymous',
                'request_id': request_id,
            })
        except Exception:
            pass
        
        return None

    def process_response(self, request, response):
        """Log response details"""
        # Calculate response time
        response_time = time.time() - getattr(request, 'start_time', time.time())
        
        # Get current span if available
        current_span = trace.get_current_span()
        
        # Build single consolidated access log entry
        duration_ms = round(response_time * 1000, 2)
        response_len = len(response.content) if hasattr(response, 'content') else 0
        http_obj = {
            'method': request.method,
            'route': getattr(request, '_route', request.path),
            'target': request.path,
            'status_code': response.status_code,
            'duration_ms': duration_ms,
            'request_content_length': getattr(request, '_request_len', 0),
            'response_content_length': response_len,
            'client_ip': getattr(request, '_client_ip', None),
            'user_agent': getattr(request, '_user_agent', None),
            'request_id': getattr(request, '_request_id', None),
            'url': request.build_absolute_uri() if hasattr(request, 'build_absolute_uri') else None,
            'user': str(request.user) if getattr(request, 'user', None) and request.user.is_authenticated else 'anonymous',
        }

        # Enrich with token usage if available from this request
        try:
            tu = token_usage_var.get()
            if tu:
                http_obj['token_usage'] = tu
        except Exception:
            pass

        level = logging.WARNING if (duration_ms >= SLOW_REQUEST_MS or response.status_code >= 500) else logging.INFO
        logger.log(level, "access", extra={'event': 'access', 'http': http_obj, 'request_id': http_obj['request_id']})
        
        # Add custom attributes to span
        active_span = getattr(request, '_otel_span', None) or current_span
        if active_span:
            try:
                if hasattr(request, 'request_id'):
                    active_span.set_attribute("http.request_id", request.request_id)
                active_span.set_attribute("http.status_code", response.status_code)
                active_span.set_attribute("http.response_content_length", response_len)
                active_span.set_status(Status(StatusCode.OK))
            except Exception:
                pass
        
        # Echo X-Request-ID in response for client correlation
        try:
            if hasattr(request, 'request_id') and request.request_id:
                response.headers['X-Request-ID'] = request.request_id
        except Exception:
            pass

        # Clear contextvar for safety
        try:
            request_id_var.set(None)
        except Exception:
            pass
        try:
            token_usage_var.set(None)
        except Exception:
            pass

        # End manual span and detach context
        if getattr(request, '_otel_span', None):
            try:
                request._otel_span.end()
            except Exception:
                pass
            finally:
                try:
                    if getattr(request, '_otel_token', None) is not None:
                        otel_context.detach(request._otel_token)
                except Exception:
                    pass
        
        # Optional: emit slow_request event (no extra log line; access has level WARNING already)
        if duration_ms >= SLOW_REQUEST_MS:
            log_custom_event("slow_request", {
                'status_code': response.status_code,
                'response_time': duration_ms,
                'content_length': response_len,
                'method': request.method,
                'path': request.path,
                'request_id': getattr(request, '_request_id', None),
            })
        
        return response

    def process_exception(self, request, exception):
        """Log exception details"""
        exception_info = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if request.user.is_authenticated else 'anonymous',
        }
        
        logger.error(
            "exception_occurred",
            extra={
                'event': 'exception_occurred',
                'exception': exception_info,
            },
        )
        
        # Log custom event
        log_custom_event("exception_occurred", exception_info)

        # Record exception on span
        try:
            span = getattr(request, '_otel_span', None) or trace.get_current_span()
            if span:
                span.record_exception(exception)
                span.set_status(Status(StatusCode.ERROR))
        except Exception:
            pass
        
        return None

    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor performance metrics
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        """Start performance monitoring"""
        request.perf_start = time.time()
        return None

    def process_response(self, request, response):
        """Log performance metrics"""
        if hasattr(request, 'perf_start'):
            duration = time.time() - request.perf_start
            
            # Log performance metrics
            log_custom_metric("request_duration_seconds", duration)
            log_custom_metric("requests_total", 1, {
                "method": request.method,
                "status_code": response.status_code,
                "path": request.path,
            })
            
            # Log high duration requests
            if duration > 5.0:  # Log requests taking more than 5 seconds
                logger.warning(f"High duration request: {request.method} {request.path} took {duration:.2f}s")
                log_custom_event("high_duration_request", {
                    "duration": duration,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                })
        
        return response


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log security-related events
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        """Log security events"""
        # Log authentication attempts
        if request.path.endswith('/login/') or request.path.endswith('/register/'):
            evt = {
                "path": request.path,
                "method": request.method,
                "ip": self._get_client_ip(request),
            }
            security_logger.info("authentication_attempt", extra={'event': 'authentication_attempt', 'http': evt})
            log_custom_event("authentication_attempt", evt)
        
        # Log API access
        if request.path.startswith('/api/'):
            evt = {
                "path": request.path,
                "method": request.method,
                "user": str(request.user) if request.user.is_authenticated else 'anonymous',
                "ip": self._get_client_ip(request),
            }
            security_logger.info("api_access", extra={'event': 'api_access', 'http': evt})
            log_custom_event("api_access", evt)
        
        return None

    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
