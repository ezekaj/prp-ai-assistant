#!/usr/bin/env python3
"""
Performance optimization configuration for PRP System
"""

import os
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio
from typing import Optional

class PerformanceConfig:
    """Production performance configuration"""
    
    # Connection pooling
    DATABASE_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '20'))
    DATABASE_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', '40'))
    DATABASE_POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', '3600'))
    DATABASE_POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', '30'))
    
    # Redis pooling
    REDIS_POOL_SIZE = int(os.environ.get('REDIS_POOL_SIZE', '50'))
    REDIS_MAX_CONNECTIONS = int(os.environ.get('REDIS_MAX_CONNECTIONS', '100'))
    
    # Worker configuration
    WORKER_PROCESSES = int(os.environ.get('WEB_CONCURRENCY', '4'))
    WORKER_THREADS = int(os.environ.get('WORKER_THREADS', '2'))
    WORKER_CONNECTIONS = int(os.environ.get('WORKER_CONNECTIONS', '1000'))
    
    # Request handling
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '30'))
    KEEPALIVE_TIMEOUT = int(os.environ.get('KEEPALIVE_TIMEOUT', '5'))
    
    # Caching
    CACHE_TTL_DEFAULT = int(os.environ.get('CACHE_TTL_DEFAULT', '300'))  # 5 minutes
    CACHE_TTL_LONG = int(os.environ.get('CACHE_TTL_LONG', '3600'))  # 1 hour
    CACHE_TTL_SHORT = int(os.environ.get('CACHE_TTL_SHORT', '60'))  # 1 minute
    
    # Batch processing
    BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '100'))
    MAX_BATCH_SIZE = int(os.environ.get('MAX_BATCH_SIZE', '1000'))
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '3600'))  # 1 hour

# Performance optimization utilities
class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=PerformanceConfig.WORKER_THREADS)
        self.process_pool = ProcessPoolExecutor(max_workers=PerformanceConfig.WORKER_PROCESSES)
    
    @lru_cache(maxsize=1000)
    def cached_computation(self, key: str) -> str:
        """LRU cached computation for expensive operations"""
        # Simulate expensive computation
        return f"computed_{key}"
    
    async def batch_process_async(self, items: list, processor_func, batch_size: Optional[int] = None):
        """Asynchronously process items in batches"""
        batch_size = batch_size or PerformanceConfig.BATCH_SIZE
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(*[processor_func(item) for item in batch])
            results.extend(batch_results)
        
        return results
    
    def parallel_process(self, items: list, processor_func, use_processes: bool = False):
        """Process items in parallel using threads or processes"""
        executor = self.process_pool if use_processes else self.thread_pool
        return list(executor.map(processor_func, items))
    
    def cleanup(self):
        """Cleanup resources"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

# Connection pool configuration for SQLAlchemy
def get_sqlalchemy_pool_config():
    """Get SQLAlchemy connection pool configuration"""
    return {
        'pool_size': PerformanceConfig.DATABASE_POOL_SIZE,
        'max_overflow': PerformanceConfig.DATABASE_MAX_OVERFLOW,
        'pool_recycle': PerformanceConfig.DATABASE_POOL_RECYCLE,
        'pool_timeout': PerformanceConfig.DATABASE_POOL_TIMEOUT,
        'pool_pre_ping': True,
        'echo_pool': os.environ.get('DB_ECHO_POOL', 'false').lower() == 'true'
    }

# Redis connection pool configuration
def get_redis_pool_config():
    """Get Redis connection pool configuration"""
    return {
        'max_connections': PerformanceConfig.REDIS_MAX_CONNECTIONS,
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'socket_keepalive': True,
        'socket_keepalive_options': {},
        'connection_pool_kwargs': {
            'max_connections': PerformanceConfig.REDIS_POOL_SIZE
        }
    }

# Gunicorn worker configuration
def get_gunicorn_config():
    """Get Gunicorn worker configuration"""
    return {
        'workers': PerformanceConfig.WORKER_PROCESSES,
        'worker_class': 'gevent',
        'worker_connections': PerformanceConfig.WORKER_CONNECTIONS,
        'threads': PerformanceConfig.WORKER_THREADS,
        'timeout': PerformanceConfig.REQUEST_TIMEOUT,
        'keepalive': PerformanceConfig.KEEPALIVE_TIMEOUT,
        'max_requests': 1000,
        'max_requests_jitter': 50,
        'preload_app': True
    }

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': PerformanceConfig.CACHE_TTL_DEFAULT,
    'CACHE_KEY_PREFIX': 'prp_cache_',
    'CACHE_OPTIONS': {
        'connection_pool_kwargs': get_redis_pool_config()
    }
}

# Performance monitoring decorators
import time
import functools
from typing import Callable

def measure_performance(metric_name: str) -> Callable:
    """Decorator to measure function performance"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                # Log performance metric (integrate with your metrics system)
                print(f"Performance: {metric_name} took {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                print(f"Performance: {metric_name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator

@lru_cache(maxsize=None)
def get_performance_optimizer():
    """Get singleton performance optimizer instance"""
    return PerformanceOptimizer()

# Export configuration
__all__ = [
    'PerformanceConfig',
    'PerformanceOptimizer',
    'get_sqlalchemy_pool_config',
    'get_redis_pool_config',
    'get_gunicorn_config',
    'CACHE_CONFIG',
    'measure_performance',
    'get_performance_optimizer'
]