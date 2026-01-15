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
import logging

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
                'message': 'Cosmos DB is not configured'
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