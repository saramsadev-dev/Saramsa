"""
Core API views for system monitoring and health checks.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from apis.core.response import StandardResponse
from apis.infrastructure.performance_middleware import get_performance_summary
from apis.infrastructure.cache_service import get_cache_service
from apis.infrastructure.cosmos_service import cosmos_service
from aiCore.services.openai_client import get_azure_client
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    System health check endpoint.
    
    Public endpoint for monitoring systems, load balancers, and health probes.
    No authentication required.
    
    Returns:
        System health status and component availability
    """
    health_status = {
        'status': 'healthy',
        'timestamp': cosmos_service._now(),
        'components': {}
    }
    
    # Diagnostic: Check raw environment variables and config values
    raw_endpoint = os.getenv('COSMOS_DB_ENDPOINT')
    raw_key = os.getenv('COSMOS_DB_KEY')
    config_endpoint = settings.COSMOS_DB_CONFIG.get('endpoint')
    config_key = settings.COSMOS_DB_CONFIG.get('key')
    
    # Build diagnostic info (don't expose full key for security)
    diagnostic = {
        'raw_env': {
            'COSMOS_DB_ENDPOINT_present': bool(raw_endpoint),
            'COSMOS_DB_ENDPOINT_length': len(raw_endpoint) if raw_endpoint else 0,
            'COSMOS_DB_ENDPOINT_value': raw_endpoint[:50] + '...' if raw_endpoint and len(raw_endpoint) > 50 else raw_endpoint,
            'COSMOS_DB_KEY_present': bool(raw_key),
            'COSMOS_DB_KEY_length': len(raw_key) if raw_key else 0,
            'COSMOS_DB_KEY_preview': raw_key[:10] + '...' if raw_key and len(raw_key) > 10 else ('***' if raw_key else None),
        },
        'from_config': {
            'endpoint': config_endpoint[:50] + '...' if config_endpoint and len(config_endpoint) > 50 else config_endpoint,
            'endpoint_has_placeholder': 'your-cosmos-account' in str(config_endpoint) if config_endpoint else None,
            'key_length': len(str(config_key)) if config_key else 0,
            'key_is_placeholder': config_key == 'your-cosmos-db-key' if config_key else None,
            'key_preview': str(config_key)[:10] + '...' if config_key and len(str(config_key)) > 10 else ('***' if config_key else None),
        },
        'service_state': {
            'is_enabled': cosmos_service.is_enabled,
            'has_client': cosmos_service.client is not None,
            'has_database': cosmos_service.database is not None,
        }
    }
    
    # Check Cosmos DB
    try:
        if cosmos_service.is_enabled:
            cosmos_stats = cosmos_service.get_performance_stats()
            health_status['components']['cosmos_db'] = {
                'status': 'healthy',
                'total_requests': cosmos_stats.get('total_requests', 0),
                'success_rate': cosmos_stats.get('success_rate_percent', 0)
            }
        else:
            health_status['components']['cosmos_db'] = {
                'status': 'disabled',
                'message': 'Cosmos DB is not configured',
                '_diagnostic': diagnostic  # Add diagnostic info for debugging
            }
    except Exception as e:
        health_status['components']['cosmos_db'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Check Cache Service
    try:
        cache_service = get_cache_service()
        cache_health = cache_service.health_check()
        health_status['components']['cache'] = cache_health
    except Exception as e:
        health_status['components']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Check AI Service
    try:
        azure_client = get_azure_client()
        azure_client.test_connection()
        health_status['components']['ai_service'] = {
            'status': 'healthy',
            'provider': 'azure_openai'
        }
    except Exception as e:
        health_status['components']['ai_service'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Determine overall status
    component_statuses = [comp.get('status') for comp in health_status['components'].values()]
    if 'unhealthy' in component_statuses:
        health_status['status'] = 'unhealthy'
    elif 'degraded' in component_statuses:
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] in ['healthy', 'degraded'] else 503
    
    return StandardResponse.success(
        data=health_status,
        message=f"System status: {health_status['status']}",
        status_code=status_code
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_metrics(request):
    """
    Get performance metrics and statistics.
    
    Returns:
        Detailed performance metrics
    """
    try:
        performance_data = get_performance_summary()
        
        return StandardResponse.success(
            data=performance_data,
            message="Performance metrics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving performance metrics: {e}")
        return StandardResponse.error(
            title="Performance Metrics Error",
            detail="Unable to retrieve performance metrics",
            status_code=500
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_performance_stats(request):
    """
    Reset performance statistics.
    
    Returns:
        Confirmation of reset
    """
    try:
        # Reset Cosmos DB stats
        if cosmos_service.is_enabled:
            cosmos_service.reset_stats()
        
        # Clear cache performance data
        cache_service = get_cache_service()
        cache_service.clear_pattern("performance:*")
        
        return StandardResponse.success(
            data={'reset': True},
            message="Performance statistics reset successfully"
        )
    except Exception as e:
        logger.error(f"Error resetting performance stats: {e}")
        return StandardResponse.error(
            title="Reset Error",
            detail="Unable to reset performance statistics",
            status_code=500
        )