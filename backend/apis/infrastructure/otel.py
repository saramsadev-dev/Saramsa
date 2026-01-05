import os
import logging

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_otel():
    """Setup OpenTelemetry with Azure Application Insights"""
    
    # Get connection string from environment
    connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
    
    # Skip setup if no connection string or if it's the default placeholder
    if not connection_string or connection_string.endswith('00000000-0000-0000-0000-000000000000'):
        logger.info("OpenTelemetry setup skipped - no valid Application Insights connection string")
        logger.info("To enable OpenTelemetry, set APPLICATIONINSIGHTS_CONNECTION_STRING environment variable")
        return
    
    try:
        # Import OpenTelemetry packages
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

        # Instrument Django
        try:
            from opentelemetry.instrumentation.django import DjangoInstrumentor
            DjangoInstrumentor().instrument()
            logger.info("Django instrumentation enabled")
        except Exception as e:
            logger.warning(f"Django instrumentation failed: {e}")

        # Instrument database
        try:
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
            Psycopg2Instrumentor().instrument(enable_commenter=False)
            logger.info("Psycopg2 instrumentation enabled")
        except Exception as e:
            logger.warning(f"Psycopg2 instrumentation failed: {e}")

        # Instrument HTTP requests
        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation enabled")
        except Exception as e:
            logger.warning(f"Requests instrumentation failed: {e}")

        logger.info("OpenTelemetry setup completed successfully")
        logger.info("Traces will be sent to Azure Application Insights")
        
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {e}")
        logger.info("Continuing without OpenTelemetry - basic logging is still active")