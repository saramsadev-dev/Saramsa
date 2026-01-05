import os
import uuid
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from opentelemetry import trace
from ..core.request_context import request_id_var, token_usage_var

logger = logging.getLogger(__name__)

class RequestResponseLoggingMiddleware(MiddlewareMixin):
    """
    Lightweight middleware for request correlation - OpenTelemetry handles detailed logging
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        """Set up request correlation ID"""
        # Start timing
        request.start_time = time.time()
        
        # Correlation ID: use incoming or generate
        request_id = (
            request.headers.get('X-Request-ID')
            or request.headers.get('X-Correlation-ID')
            or str(uuid.uuid4())
        )
        request.request_id = request_id
        request_id_var.set(request_id)
        
        return None

    def process_response(self, request, response):
        """Add request ID to response headers and clean up context"""
        # Echo X-Request-ID in response for client correlation
        try:
            if hasattr(request, 'request_id') and request.request_id:
                response.headers['X-Request-ID'] = request.request_id
        except Exception:
            pass

        # Clear contextvar for safety
        try:
            request_id_var.set(None)
            token_usage_var.set(None)
        except Exception:
            pass
        
        return response


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Basic performance monitoring - OpenTelemetry provides detailed metrics
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        """Start performance monitoring"""
        request.perf_start = time.time()
        return None

    def process_response(self, request, response):
        """Log only high duration requests"""
        if hasattr(request, 'perf_start'):
            duration = time.time() - request.perf_start
            
            # Log only requests taking more than 5 seconds
            if duration > 5.0:
                logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}s")
        
        return response


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Basic security event logging - OpenTelemetry captures detailed request data
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        """Log critical security events only"""
        # Log authentication attempts
        if request.path.endswith('/login/') or request.path.endswith('/register/'):
            logger.info(f"Authentication attempt: {request.method} {request.path} from {self._get_client_ip(request)}")
        
        return None

    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip