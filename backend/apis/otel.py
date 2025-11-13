import os
import logging
from .request_context import request_id_var
from .http_propagation import patch_requests_propagation

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_otel():
    """Setup OpenTelemetry with Azure Application Insights - Simplified for Python 3.12 compatibility"""
    
    # Get connection string from environment
    connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
    
    # Skip setup if no connection string or if it's the default placeholder
    if not connection_string or connection_string.endswith('00000000-0000-0000-0000-000000000000'):
        logger.info("OpenTelemetry setup skipped - no valid Application Insights connection string")
        logger.info("To enable OpenTelemetry, set APPLICATIONINSIGHTS_CONNECTION_STRING environment variable")
        return
    
    try:
        # Try to import OpenTelemetry packages with error handling
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
        except ImportError as e:
            logger.warning(f"OpenTelemetry core packages not available: {e}")
            logger.info("Continuing without OpenTelemetry instrumentation")
            return
        
        # Configure resource
        resource = Resource.create({
            "service.name": os.getenv('WEBSITE_SITE_NAME', 'saramsa-backend'),
            "service.instance.id": os.getenv('HOSTNAME', 'localhost'),
            "service.version": os.getenv('APP_VERSION', '1.0.0'),
            "deployment.environment": os.getenv('ENVIRONMENT', 'development'),
        })

        # Configure tracing
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        # Add Azure Monitor trace exporter
        trace_exporter = AzureMonitorTraceExporter.from_connection_string(connection_string)
        span_processor = BatchSpanProcessor(trace_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        # Try to instrument Django (with error handling)
        try:
            from opentelemetry.instrumentation.django import DjangoInstrumentor
            DjangoInstrumentor().instrument(
                request_hook=request_hook,
                response_hook=response_hook
            )
            logger.info("Django instrumentation enabled")
        except Exception as e:
            logger.warning(f"Django instrumentation failed: {e}")

        # Try to instrument other components (with error handling)
        try:
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
            Psycopg2Instrumentor().instrument(enable_commenter=False)
            logger.info("Psycopg2 instrumentation enabled")
        except Exception as e:
            logger.warning(f"Psycopg2 instrumentation failed: {e}")

        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor
            RequestsInstrumentor().instrument(
                span_name=lambda request: f"{request.method} {request.url}"
            )
            logger.info("Requests instrumentation enabled")
        except Exception as e:
            logger.warning(f"Requests instrumentation failed: {e}")

        logger.info("OpenTelemetry setup completed successfully")
        logger.info("Traces will be sent to Azure Application Insights")
        # Ensure outbound requests carry X-Request-ID
        try:
            patch_requests_propagation()
            logger.info("Enabled X-Request-ID propagation on outbound HTTP requests")
        except Exception:
            logger.warning("Failed to enable X-Request-ID propagation on outbound HTTP requests")
        
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {e}")
        logger.info("Continuing without OpenTelemetry - basic logging is still active")
        # Don't raise the exception to prevent app startup failure

def request_hook(span, request):
    """Custom request hook to log request details"""
    try:
        # Add request details to span
        span.set_attribute("http.request.method", request.method)
        span.set_attribute("http.request.url", request.build_absolute_uri())
        span.set_attribute("http.request.headers", str(dict(request.headers)))
        # Attach app correlation id
        try:
            req_id = request.headers.get('X-Request-ID') or request.headers.get('X-Correlation-ID') or request_id_var.get()
            if req_id:
                span.set_attribute("request_id", req_id)
        except Exception:
            pass
        span.set_attribute("http.request.body_size", len(request.body) if request.body else 0)
        
        # Log request details
        logger.info(f"Request: {request.method} {request.build_absolute_uri()}")
        logger.debug(f"Request Headers: {dict(request.headers)}")
        
        # Log request body for non-GET requests (be careful with sensitive data)
        if request.method != 'GET' and request.body:
            try:
                body_str = request.body.decode('utf-8')
                # Truncate long bodies to avoid excessive logging
                if len(body_str) > 1000:
                    body_str = body_str[:1000] + "... [truncated]"
                logger.debug(f"Request Body: {body_str}")
            except Exception as e:
                logger.warning(f"Could not decode request body: {e}")
                
    except Exception as e:
        logger.error(f"Error in request_hook: {e}")

def response_hook(span, request, response):
    """Custom response hook to log response details"""
    try:
        # Add response details to span
        span.set_attribute("http.response.status_code", response.status_code)
        span.set_attribute("http.response.headers", str(dict(response.headers)))
        
        # Log response details
        logger.info(f"Response: {response.status_code} for {request.method} {request.build_absolute_uri()}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        
        # Log response content for debugging (be careful with sensitive data)
        if hasattr(response, 'content') and response.content:
            try:
                content_str = response.content.decode('utf-8')
                # Truncate long responses to avoid excessive logging
                if len(content_str) > 1000:
                    content_str = content_str[:1000] + "... [truncated]"
                logger.debug(f"Response Content: {content_str}")
            except Exception as e:
                logger.warning(f"Could not decode response content: {e}")
                
    except Exception as e:
        logger.error(f"Error in response_hook: {e}")

def log_custom_event(event_name, attributes=None):
    """Log custom events to Application Insights"""
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(event_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            logger.info(f"Custom event logged: {event_name}")
    except Exception as e:
        logger.error(f"Failed to log custom event {event_name}: {e}")

def log_custom_metric(metric_name, value, attributes=None):
    """No-op metrics for now to avoid SDK compatibility errors.

    We only log a concise line and skip OpenTelemetry metrics calls to keep logs clean.
    """
    try:
        logger.debug(f"metric: {metric_name}={value} attrs={attributes}")
    except Exception:
        # Intentionally swallow errors to avoid noise
        pass