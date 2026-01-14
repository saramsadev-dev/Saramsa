"""
Caching service for performance optimization.
Provides Redis-based caching with fallback to in-memory caching.
Supports both local Redis and Azure Redis Cache with SSL.
"""

import json
import logging
import hashlib
import ssl
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import os

logger = logging.getLogger(__name__)

# Try to import Redis, fall back to in-memory cache if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")

class CacheService:
    """
    Unified caching service with Redis backend and in-memory fallback.
    Supports both local Redis and Azure Redis Cache with SSL.
    """
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        if REDIS_AVAILABLE:
            try:
                redis_url = os.getenv('REDIS_URL')
                
                if not redis_url:
                    logger.warning("REDIS_URL environment variable not set. Using in-memory cache.")
                    return
                
                # Azure Redis requires SSL connections (rediss://)
                if not redis_url.startswith('rediss://'):
                    logger.warning(f"REDIS_URL should use rediss:// for Azure Redis. Got: {redis_url[:20]}... Using in-memory cache.")
                    return
                
                # Azure Redis typically requires SSL with certificate validation disabled
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    ssl_cert_reqs=ssl.CERT_NONE,  # Azure Redis uses CERT_NONE
                    ssl_ca_certs=None,
                    ssl_certfile=None,
                    ssl_keyfile=None
                )
                
                # Test connection
                self.redis_client.ping()
                logger.info("Azure Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Azure Redis connection failed, using in-memory cache: {e}")
                self.redis_client = None
    
    def _generate_key(self, key: str, prefix: str = "saramsa") -> str:
        """Generate a prefixed cache key."""
        return f"{prefix}:{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage."""
        return json.dumps(value, default=str)
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from storage."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        cache_key = self._generate_key(key)
        
        try:
            if self.redis_client:
                value = self.redis_client.get(cache_key)
                if value is not None:
                    self.cache_stats['hits'] += 1
                    return self._deserialize_value(value)
            else:
                # In-memory cache with expiration check
                if cache_key in self.memory_cache:
                    cached_item = self.memory_cache[cache_key]
                    if cached_item['expires_at'] > datetime.now():
                        self.cache_stats['hits'] += 1
                        return cached_item['value']
                    else:
                        # Expired, remove from cache
                        del self.memory_cache[cache_key]
            
            self.cache_stats['misses'] += 1
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.cache_stats['misses'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(key)
        
        try:
            if self.redis_client:
                serialized_value = self._serialize_value(value)
                result = self.redis_client.setex(cache_key, ttl, serialized_value)
                if result:
                    self.cache_stats['sets'] += 1
                return result
            else:
                # In-memory cache
                expires_at = datetime.now() + timedelta(seconds=ttl)
                self.memory_cache[cache_key] = {
                    'value': value,
                    'expires_at': expires_at
                }
                self.cache_stats['sets'] += 1
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(key)
        
        try:
            if self.redis_client:
                result = self.redis_client.delete(cache_key)
                if result:
                    self.cache_stats['deletes'] += 1
                return bool(result)
            else:
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
                    self.cache_stats['deletes'] += 1
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        full_pattern = self._generate_key(pattern)
        deleted_count = 0
        
        try:
            if self.redis_client:
                keys = self.redis_client.keys(full_pattern)
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
            else:
                # In-memory cache pattern matching
                keys_to_delete = [k for k in self.memory_cache.keys() if self._matches_pattern(k, full_pattern)]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                deleted_count = len(keys_to_delete)
            
            self.cache_stats['deletes'] += deleted_count
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern {pattern}: {e}")
            return 0
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for in-memory cache."""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            **self.cache_stats,
            'hit_rate_percent': round(hit_rate, 2),
            'backend': 'redis' if self.redis_client else 'memory',
            'memory_cache_size': len(self.memory_cache) if not self.redis_client else None
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_info'] = {
                    'used_memory_human': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed')
                }
            except Exception as e:
                logger.error(f"Error getting Redis info: {e}")
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Check cache health."""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return {'status': 'healthy', 'backend': 'redis'}
            else:
                return {'status': 'healthy', 'backend': 'memory'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e), 'backend': 'redis' if self.redis_client else 'memory'}


# Global cache instance
_cache_service = None

def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cache_result(key_prefix: str, ttl: int = 3600, use_args: bool = True):
    """
    Decorator to cache function results.
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        use_args: Whether to include function arguments in cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # Generate cache key
            if use_args:
                # Create hash of arguments for cache key
                args_str = str(args) + str(sorted(kwargs.items()))
                args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
                cache_key = f"{key_prefix}:{func.__name__}:{args_hash}"
            else:
                cache_key = f"{key_prefix}:{func.__name__}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache set for {cache_key}")
            
            return result
        return wrapper
    return decorator


# Specific cache decorators for common use cases
def cache_analysis_result(ttl: int = 1800):  # 30 minutes
    """Cache analysis results."""
    return cache_result("analysis", ttl=ttl)

def cache_user_data(ttl: int = 600):  # 10 minutes
    """Cache user data."""
    return cache_result("user", ttl=ttl)

def cache_project_data(ttl: int = 900):  # 15 minutes
    """Cache project data."""
    return cache_result("project", ttl=ttl)