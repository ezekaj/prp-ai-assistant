"""
Redis-based caching system for PRP System
Provides intelligent caching with TTL, compression, and performance monitoring
"""

import json
import pickle
import hashlib
import time
import logging
from functools import wraps
from typing import Any, Optional, Dict, Union, Callable
from datetime import datetime, timedelta
import redis
from redis.connection import ConnectionPool
import gzip

from config import config

logger = logging.getLogger(__name__)


class CacheManager:
    """Intelligent cache manager with Redis backend"""
    
    def __init__(self, redis_url: str = None, pool_size: int = None):
        self.redis_url = redis_url or config.REDIS_URL
        self.pool_size = pool_size or config.REDIS_POOL_SIZE
        
        # Create connection pool
        self.pool = ConnectionPool.from_url(
            self.redis_url,
            max_connections=self.pool_size,
            socket_timeout=config.REDIS_TIMEOUT,
            socket_connect_timeout=config.REDIS_TIMEOUT,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        
        self.client = redis.Redis(connection_pool=self.pool, decode_responses=False)
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
    
    def _generate_key(self, namespace: str, key: str, *args, **kwargs) -> str:
        """Generate a unique cache key"""
        # Create deterministic key from arguments
        key_data = f"{key}:{str(args)}:{str(sorted(kwargs.items()))}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"prp:{namespace}:{key}:{key_hash}"
    
    def _serialize_data(self, data: Any, compress: bool = True) -> bytes:
        """Serialize data with optional compression"""
        try:
            # Use pickle for complex objects, JSON for simple ones
            if isinstance(data, (dict, list, str, int, float, bool, type(None))):
                serialized = json.dumps(data).encode('utf-8')
            else:
                serialized = pickle.dumps(data)
            
            # Compress if data is large
            if compress and len(serialized) > 1024:
                serialized = gzip.compress(serialized)
                return b'compressed:' + serialized
            
            return b'raw:' + serialized
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize cached data"""
        try:
            if data.startswith(b'compressed:'):
                data = gzip.decompress(data[11:])
                
                # Try JSON first, then pickle
                try:
                    return json.loads(data.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return pickle.loads(data)
            
            elif data.startswith(b'raw:'):
                data = data[4:]
                
                try:
                    return json.loads(data.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return pickle.loads(data)
            
            else:
                # Legacy format
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise
    
    def get(self, namespace: str, key: str, *args, **kwargs) -> Optional[Any]:
        """Get cached value"""
        cache_key = self._generate_key(namespace, key, *args, **kwargs)
        
        try:
            data = self.client.get(cache_key)
            if data is None:
                self.stats['misses'] += 1
                return None
            
            self.stats['hits'] += 1
            return self._deserialize_data(data)
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache get error for key {cache_key}: {e}")
            return None
    
    def set(self, namespace: str, key: str, value: Any, ttl: int = 3600, 
            compress: bool = True, *args, **kwargs):
        """Set cached value with TTL"""
        cache_key = self._generate_key(namespace, key, *args, **kwargs)
        
        try:
            serialized = self._serialize_data(value, compress)
            self.client.setex(cache_key, ttl, serialized)
            self.stats['sets'] += 1
            
            logger.debug(f"Cached {cache_key} with TTL {ttl}s")
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache set error for key {cache_key}: {e}")
    
    def delete(self, namespace: str, key: str, *args, **kwargs):
        """Delete cached value"""
        cache_key = self._generate_key(namespace, key, *args, **kwargs)
        
        try:
            self.client.delete(cache_key)
            logger.debug(f"Deleted cache key {cache_key}")
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache delete error for key {cache_key}: {e}")
    
    def clear_namespace(self, namespace: str):
        """Clear all keys in a namespace"""
        try:
            pattern = f"prp:{namespace}:*"
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"Cleared {len(keys)} keys from namespace {namespace}")
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache clear error for namespace {namespace}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_operations = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_operations * 100) if total_operations > 0 else 0
        
        return {
            **self.stats,
            'hit_rate': round(hit_rate, 2),
            'total_operations': total_operations,
            'connection_pool_info': {
                'max_connections': self.pool.max_connections,
                'created_connections': self.pool.created_connections
            }
        }
    
    def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global cache manager instance
cache_manager = CacheManager()


def cached(namespace: str = 'default', ttl: int = 3600, compress: bool = True,
          key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = func.__name__
            
            # Try to get from cache
            cached_result = cache_manager.get(namespace, cache_key, *args, **kwargs)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Only cache if execution took significant time (> 0.1s)
            if execution_time > 0.1:
                cache_manager.set(namespace, cache_key, result, ttl, compress, *args, **kwargs)
                logger.debug(f"Cached result for {func.__name__} (took {execution_time:.3f}s)")
            
            return result
        
        # Add cache control methods to function
        wrapper.cache_clear = lambda *args, **kwargs: cache_manager.delete(
            namespace, key_func(*args, **kwargs) if key_func else func.__name__, *args, **kwargs
        )
        wrapper.cache_info = lambda: cache_manager.get_stats()
        
        return wrapper
    
    return decorator


def cache_prp_result(complexity: int, feature_type: str = 'default'):
    """Specialized caching for PRP generation results"""
    def key_func(*args, **kwargs):
        return f"prp_gen_{complexity}_{feature_type}"
    
    # Cache longer for complex PRPs (they take more time to generate)
    ttl = 3600 + (complexity * 600)  # 1-7 hours based on complexity
    
    return cached(namespace='prp_generation', ttl=ttl, key_func=key_func)


def cache_analytics_data(timeframe: str = 'daily'):
    """Specialized caching for analytics data"""
    ttl_map = {
        'hourly': 300,    # 5 minutes
        'daily': 1800,    # 30 minutes
        'weekly': 3600,   # 1 hour
        'monthly': 7200   # 2 hours
    }
    
    return cached(
        namespace='analytics',
        ttl=ttl_map.get(timeframe, 1800),
        key_func=lambda *args, **kwargs: f"analytics_{timeframe}"
    )


def cache_codebase_analysis(project_path: str):
    """Specialized caching for codebase analysis"""
    def key_func(*args, **kwargs):
        # Use project path hash as key
        path_hash = hashlib.md5(project_path.encode()).hexdigest()[:12]
        return f"codebase_analysis_{path_hash}"
    
    # Cache codebase analysis for 24 hours
    return cached(namespace='codebase', ttl=86400, key_func=key_func)


# Convenience functions
def invalidate_prp_cache(complexity: int = None, feature_type: str = None):
    """Invalidate PRP generation cache"""
    if complexity and feature_type:
        cache_manager.delete('prp_generation', f'prp_gen_{complexity}_{feature_type}')
    else:
        cache_manager.clear_namespace('prp_generation')


def invalidate_analytics_cache():
    """Invalidate all analytics cache"""
    cache_manager.clear_namespace('analytics')


def get_cache_health() -> Dict[str, Any]:
    """Get comprehensive cache health information"""
    return {
        'redis_healthy': cache_manager.health_check(),
        'stats': cache_manager.get_stats(),
        'connection_info': {
            'redis_url': cache_manager.redis_url,
            'pool_size': cache_manager.pool_size
        }
    }


# Example usage patterns:

@cache_prp_result(complexity=5, feature_type='api')
def generate_api_prp(feature_name: str, requirements: str):
    """Example PRP generation function with caching"""
    # This would be your actual PRP generation logic
    pass


@cache_analytics_data(timeframe='daily')
def get_daily_analytics():
    """Example analytics function with caching"""
    # This would be your actual analytics logic
    pass


@cached(namespace='user_data', ttl=1800)
def get_user_preferences(user_id: int):
    """Example user data caching"""
    # This would be your actual user data logic
    pass