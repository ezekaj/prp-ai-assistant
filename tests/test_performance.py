"""
Performance tests for PRP AI Assistant
Tests caching, database performance, and API response times
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import threading
from concurrent.futures import ThreadPoolExecutor

from cache import CacheManager, cached, cache_manager
from prp_app_secure import app


@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = Mock()
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.ping.return_value = True
    return redis_mock


@pytest.fixture
def cache_test_manager(mock_redis):
    """Test cache manager with mocked Redis"""
    with patch('cache.redis.Redis') as mock_redis_class:
        mock_redis_class.return_value = mock_redis
        manager = CacheManager('redis://localhost:6379/0')
        yield manager


class TestCachePerformance:
    """Test caching system performance"""
    
    def test_cache_hit_performance(self, cache_test_manager, mock_redis):
        """Test cache hit is faster than miss"""
        # Setup cache hit
        test_data = {'result': 'cached_value', 'computation': 'expensive'}
        serialized_data = cache_test_manager._serialize_data(test_data)
        mock_redis.get.return_value = serialized_data
        
        # Measure cache hit time
        start_time = time.time()
        result = cache_test_manager.get('test', 'key')
        hit_time = time.time() - start_time
        
        assert result == test_data
        assert hit_time < 0.01  # Should be very fast
    
    def test_cache_compression_performance(self, cache_test_manager):
        """Test cache compression for large data"""
        # Large data that should be compressed
        large_data = {'data': 'x' * 2000, 'numbers': list(range(1000))}
        
        start_time = time.time()
        serialized = cache_test_manager._serialize_data(large_data, compress=True)
        compression_time = time.time() - start_time
        
        # Compression should not be too slow
        assert compression_time < 0.1
        
        # Compressed data should be smaller than raw
        raw_serialized = cache_test_manager._serialize_data(large_data, compress=False)
        assert len(serialized) < len(raw_serialized)
    
    def test_cache_concurrent_access(self, cache_test_manager, mock_redis):
        """Test cache performance under concurrent access"""
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        def cache_operation(thread_id):
            """Simulate cache operations"""
            for i in range(10):
                cache_test_manager.set('test', f'key_{thread_id}_{i}', f'value_{i}')
                cache_test_manager.get('test', f'key_{thread_id}_{i}')
            return thread_id
        
        start_time = time.time()
        
        # Run concurrent cache operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(cache_operation, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        
        # Should complete reasonably fast even under load
        assert total_time < 5.0
        assert len(results) == 5
    
    def test_cache_decorator_performance(self):
        """Test cached decorator performance"""
        call_count = 0
        
        @cached(namespace='test', ttl=3600)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # Simulate expensive operation
            return x + y
        
        with patch.object(cache_manager, 'get', return_value=None) as mock_get, \
             patch.object(cache_manager, 'set') as mock_set:
            
            # First call should execute function
            start_time = time.time()
            result1 = expensive_function(1, 2)
            first_call_time = time.time() - start_time
            
            assert result1 == 3
            assert call_count == 1
            assert first_call_time >= 0.1  # Should include sleep time
            
            # Mock cache hit for second call
            mock_get.return_value = 3
            
            start_time = time.time()
            result2 = expensive_function(1, 2)
            second_call_time = time.time() - start_time
            
            assert result2 == 3
            assert call_count == 1  # Function not called again
            assert second_call_time < 0.01  # Much faster due to cache


class TestDatabasePerformance:
    """Test database connection pooling and query performance"""
    
    def test_connection_pool_configuration(self):
        """Test database connection pool is properly configured"""
        from config import config
        
        # Check pool configuration exists
        assert hasattr(config, 'SQLALCHEMY_ENGINE_OPTIONS')
        pool_config = config.SQLALCHEMY_ENGINE_OPTIONS
        
        assert 'pool_size' in pool_config
        assert 'max_overflow' in pool_config
        assert 'pool_recycle' in pool_config
        assert pool_config['pool_size'] >= 10  # Reasonable pool size
    
    def test_database_connection_reuse(self):
        """Test database connections are reused from pool"""
        from sqlalchemy import create_engine
        from config import config
        
        # Create engine with pool configuration
        engine = create_engine(
            'sqlite:///:memory:',  # Use in-memory SQLite for testing
            **config.SQLALCHEMY_ENGINE_OPTIONS
        )
        
        connections = []
        
        # Get multiple connections
        for _ in range(5):
            conn = engine.connect()
            connections.append(conn)
        
        # Close connections
        for conn in connections:
            conn.close()
        
        # Pool should be configured and connections reused
        assert engine.pool.size() == config.SQLALCHEMY_ENGINE_OPTIONS['pool_size']
    
    def test_query_performance_monitoring(self):
        """Test query performance can be monitored"""
        from sqlalchemy import create_engine, event, text
        
        query_times = []
        
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            query_times.append(total)
        
        # Create engine with event listeners
        engine = create_engine('sqlite:///:memory:')
        event.listen(engine, "before_cursor_execute", receive_before_cursor_execute)
        event.listen(engine, "after_cursor_execute", receive_after_cursor_execute)
        
        # Execute test queries
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.execute(text("SELECT 2"))
        
        # Should have recorded query times
        assert len(query_times) == 2
        for query_time in query_times:
            assert query_time < 1.0  # Simple queries should be fast


class TestAPIPerformance:
    """Test API endpoint performance"""
    
    def test_health_check_performance(self, client):
        """Test health check endpoint performance"""
        with patch('prp_app_secure.db_engine') as mock_db, \
             patch('prp_app_secure.redis_client') as mock_redis:
            
            # Mock successful health checks
            mock_db.connect.return_value.__enter__.return_value.execute.return_value = None
            mock_redis.ping.return_value = True
            
            start_time = time.time()
            response = client.get('/health')
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            assert response_time < 0.5  # Health check should be fast
    
    def test_metrics_endpoint_performance(self, client):
        """Test metrics endpoint performance"""
        start_time = time.time()
        response = client.get('/metrics')
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Metrics generation should be fast
    
    def test_concurrent_requests_performance(self, client):
        """Test API performance under concurrent load"""
        def make_request():
            """Make a health check request"""
            with patch('prp_app_secure.db_engine') as mock_db, \
                 patch('prp_app_secure.redis_client') as mock_redis:
                
                mock_db.connect.return_value.__enter__.return_value.execute.return_value = None
                mock_redis.ping.return_value = True
                
                response = client.get('/health')
                return response.status_code
        
        start_time = time.time()
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        # Should handle concurrent load reasonably well
        assert total_time < 10.0
    
    def test_response_time_consistency(self, client):
        """Test API response time consistency"""
        response_times = []
        
        with patch('prp_app_secure.db_engine') as mock_db, \
             patch('prp_app_secure.redis_client') as mock_redis:
            
            mock_db.connect.return_value.__enter__.return_value.execute.return_value = None
            mock_redis.ping.return_value = True
            
            # Make multiple requests and measure times
            for _ in range(10):
                start_time = time.time()
                response = client.get('/health')
                response_time = time.time() - start_time
                
                assert response.status_code == 200
                response_times.append(response_time)
        
        # Check response time consistency
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Response times should be consistent (not too much variation)
        assert max_time - min_time < 1.0
        assert avg_time < 0.5


class TestMemoryPerformance:
    """Test memory usage and optimization"""
    
    def test_cache_memory_management(self, cache_test_manager, mock_redis):
        """Test cache doesn't leak memory"""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform many cache operations
        for i in range(100):
            cache_test_manager.set('test', f'key_{i}', f'value_{i}' * 100)
            cache_test_manager.get('test', f'key_{i}')
        
        # Force garbage collection after operations
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory usage should not increase dramatically
        object_increase = final_objects - initial_objects
        assert object_increase < 1000  # Reasonable memory increase
    
    def test_large_data_handling(self, cache_test_manager):
        """Test handling of large data structures"""
        import sys
        
        # Create large data structure
        large_data = {
            'arrays': [list(range(1000)) for _ in range(10)],
            'strings': ['x' * 1000 for _ in range(10)],
            'nested': {'level1': {'level2': {'level3': 'data'}}}
        }
        
        # Test serialization doesn't consume excessive memory
        start_size = sys.getsizeof(large_data)
        serialized = cache_test_manager._serialize_data(large_data)
        
        # Compressed serialized data should be reasonable size
        assert len(serialized) < start_size * 2  # Not more than 2x original


class TestNetworkPerformance:
    """Test network-related performance"""
    
    def test_redis_connection_pooling(self):
        """Test Redis connection pooling performance"""
        from redis.connection import ConnectionPool
        
        # Create connection pool
        pool = ConnectionPool.from_url(
            'redis://localhost:6379/0',
            max_connections=10,
            socket_timeout=5
        )
        
        # Test pool configuration
        assert pool.max_connections == 10
        assert hasattr(pool, 'connection_kwargs')
    
    def test_timeout_configuration(self):
        """Test timeout settings are appropriate"""
        from config import config
        
        # Check timeout configurations exist and are reasonable
        assert hasattr(config, 'REDIS_TIMEOUT')
        assert config.REDIS_TIMEOUT > 0
        assert config.REDIS_TIMEOUT < 30  # Not too long
        
        if hasattr(config, 'SQLALCHEMY_ENGINE_OPTIONS'):
            pool_config = config.SQLALCHEMY_ENGINE_OPTIONS
            if 'pool_timeout' in pool_config:
                assert pool_config['pool_timeout'] > 0
                assert pool_config['pool_timeout'] < 60


class TestScalabilityMetrics:
    """Test scalability indicators"""
    
    def test_stateless_design_verification(self):
        """Verify application is truly stateless"""
        # Check no global state variables (except configuration)
        import prp_app_secure
        
        # These should be initialized per request or from environment
        stateful_indicators = ['user_sessions', 'cached_data', 'global_state']
        
        for indicator in stateful_indicators:
            assert not hasattr(prp_app_secure, indicator), f"Found stateful indicator: {indicator}"
    
    def test_resource_cleanup(self):
        """Test proper resource cleanup"""
        from prp_app_secure import signal_handler
        import signal
        
        # Mock cleanup functions
        with patch('prp_app_secure.db_engine') as mock_db, \
             patch('prp_app_secure.redis_client') as mock_redis, \
             patch('prp_app_secure.db_session') as mock_session, \
             patch('sys.exit') as mock_exit:
            
            # Test signal handler cleans up properly
            signal_handler(signal.SIGTERM, None)
            
            # Verify cleanup was called
            mock_db.dispose.assert_called_once()
            mock_redis.close.assert_called_once()
            mock_session.remove.assert_called_once()
            mock_exit.assert_called_once_with(0)
    
    def test_horizontal_scaling_readiness(self):
        """Test application readiness for horizontal scaling"""
        # Verify no file-based state storage
        import os
        import tempfile
        
        # Application should not write state to local files
        # (except logs, which should go to stdout/stderr)
        
        # Check no hardcoded file paths for state storage
        state_patterns = ['.state', '.session', '.data', '.cache']
        
        # This is a simplified check - in reality you'd scan the codebase
        temp_dir = tempfile.gettempdir()
        for pattern in state_patterns:
            state_files = [f for f in os.listdir(temp_dir) if pattern in f]
            # Should not create state files in temp directory
            assert len(state_files) == 0 or all('prp' not in f for f in state_files)