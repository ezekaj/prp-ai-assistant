"""
Enhanced performance tests for PRP AI Assistant System
Tests response times, throughput, and resource usage
"""

import pytest
import time
import concurrent.futures
import statistics
import json
import sys
import os
from flask import Flask

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prp_app import app, Config
from auth import User, Base, init_auth, register_auth_routes, create_tokens
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestPerformance:
    """Performance test suite"""
    
    @pytest.fixture(scope='class')
    def test_app(self):
        """Create test application with in-memory database"""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'perf-test-secret'
        app.config['JWT_SECRET_KEY'] = 'perf-test-jwt'
        
        # Use in-memory SQLite for speed
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        app.config['db_engine'] = engine
        app.config['db_session'] = session
        app.config['redis_client'] = None  # Mock for tests
        
        init_auth(app)
        register_auth_routes(app, session)
        
        # Create test user for auth tests
        test_user = User(username='perftest', email='perf@test.com', role='admin')
        test_user.set_password('perfpass123')
        session.add(test_user)
        session.commit()
        
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def auth_token(self, test_app):
        """Get auth token for performance tests"""
        response = test_app.post('/auth/login', json={
            'username': 'perftest',
            'password': 'perfpass123'
        })
        return response.get_json()['access_token']
    
    @pytest.mark.benchmark
    def test_health_check_performance(self, test_app, benchmark):
        """Benchmark health check endpoint"""
        def make_request():
            return test_app.get('/health')
        
        result = benchmark(make_request)
        assert result.status_code == 200
    
    @pytest.mark.benchmark
    def test_auth_login_performance(self, test_app, benchmark):
        """Benchmark authentication performance"""
        def login():
            return test_app.post('/auth/login', json={
                'username': 'perftest',
                'password': 'perfpass123'
            })
        
        result = benchmark(login)
        assert result.status_code == 200
    
    def test_concurrent_requests(self, test_app):
        """Test handling of concurrent requests"""
        num_requests = 100
        num_workers = 10
        
        def make_health_request():
            start = time.time()
            response = test_app.get('/health')
            end = time.time()
            return {
                'status_code': response.status_code,
                'duration': end - start
            }
        
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(make_health_request) for _ in range(num_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['status_code'] == 200)
        durations = [r['duration'] for r in results]
        
        assert successful_requests == num_requests
        assert statistics.mean(durations) < 0.1  # Average under 100ms
        assert max(durations) < 0.5  # Max under 500ms
    
    def test_api_versioning_performance(self, test_app, auth_token):
        """Test performance difference between API versions"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Measure V1 performance
        v1_times = []
        for _ in range(50):
            start = time.time()
            response = test_app.get('/api/v1/', headers=headers)
            v1_times.append(time.time() - start)
            assert response.status_code == 200
        
        # Measure V2 performance
        v2_times = []
        for _ in range(50):
            start = time.time()
            response = test_app.get('/api/v2/', headers=headers)
            v2_times.append(time.time() - start)
            assert response.status_code == 200
        
        # V2 should not be significantly slower than V1
        v1_avg = statistics.mean(v1_times)
        v2_avg = statistics.mean(v2_times)
        assert v2_avg < v1_avg * 1.2  # V2 should be within 20% of V1
    
    def test_jwt_validation_performance(self, test_app, auth_token):
        """Test JWT validation overhead"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Protected endpoint
        protected_times = []
        for _ in range(100):
            start = time.time()
            response = test_app.get('/auth/profile', headers=headers)
            protected_times.append(time.time() - start)
            assert response.status_code == 200
        
        # Unprotected endpoint
        unprotected_times = []
        for _ in range(100):
            start = time.time()
            response = test_app.get('/health')
            unprotected_times.append(time.time() - start)
            assert response.status_code == 200
        
        # JWT validation should add minimal overhead
        protected_avg = statistics.mean(protected_times)
        unprotected_avg = statistics.mean(unprotected_times)
        overhead = protected_avg - unprotected_avg
        
        assert overhead < 0.01  # Less than 10ms overhead
    
    def test_database_connection_pooling(self, test_app, auth_token):
        """Test database connection pooling effectiveness"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Simulate heavy database usage
        response_times = []
        
        for i in range(50):
            start = time.time()
            # This would normally hit the database
            response = test_app.get('/api/v1/analytics/dashboard', headers=headers)
            response_times.append(time.time() - start)
            
            # First requests might be slower (connection establishment)
            if i > 10:
                assert response_times[-1] < 0.1  # Should be fast with pooling
    
    def test_request_size_handling(self, test_app, auth_token):
        """Test handling of different request sizes"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Small request
        small_data = {
            'feature_name': 'Test',
            'requirements': 'Simple requirement'
        }
        start = time.time()
        response = test_app.post('/api/v2/prp/generate', 
                                headers=headers, 
                                json=small_data)
        small_time = time.time() - start
        
        # Large request
        large_data = {
            'feature_name': 'Complex Feature',
            'requirements': 'Very detailed requirements ' * 100,  # ~2KB
            'complexity': 10
        }
        start = time.time()
        response = test_app.post('/api/v2/prp/generate', 
                                headers=headers, 
                                json=large_data)
        large_time = time.time() - start
        
        # Large requests should not take disproportionately longer
        assert large_time < small_time * 2
    
    def test_memory_usage_stability(self, test_app):
        """Test for memory leaks during repeated requests"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests
        for _ in range(1000):
            test_app.get('/health')
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 50MB)
        assert memory_increase < 50
    
    def test_rate_limiting_performance(self, test_app):
        """Test rate limiting doesn't significantly impact performance"""
        # Note: This assumes rate limiting is configured
        response_times = []
        
        for i in range(20):
            start = time.time()
            response = test_app.get('/health')
            response_times.append(time.time() - start)
            
            # Check if we hit rate limit
            if response.status_code == 429:
                break
        
        # Rate limiting checks should be fast
        avg_time = statistics.mean(response_times)
        assert avg_time < 0.01  # Under 10ms average


class TestLoadSimulation:
    """Simulate realistic load patterns"""
    
    def test_burst_traffic(self, test_app):
        """Test handling of burst traffic"""
        # Simulate sudden spike in traffic
        burst_size = 200
        results = []
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(lambda: test_app.get('/health'))
                for _ in range(burst_size)
            ]
            results = [f.result() for f in futures]
        
        total_time = time.time() - start_time
        
        # All requests should succeed
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count == burst_size
        
        # Should handle burst within reasonable time
        assert total_time < 5.0  # 200 requests in 5 seconds
    
    def test_sustained_load(self, test_app, auth_token):
        """Test performance under sustained load"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        duration = 10  # seconds
        request_rate = 10  # requests per second
        
        response_times = []
        errors = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            request_start = time.time()
            
            try:
                response = test_app.get('/api/v1/', headers=headers)
                if response.status_code != 200:
                    errors += 1
            except Exception:
                errors += 1
            
            response_times.append(time.time() - request_start)
            
            # Maintain request rate
            sleep_time = (1.0 / request_rate) - (time.time() - request_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Analyze performance
        p50 = statistics.median(response_times)
        p95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        assert p50 < 0.05  # 50% under 50ms
        assert p95 < 0.1   # 95% under 100ms
        assert p99 < 0.2   # 99% under 200ms
        assert errors == 0  # No errors under normal load


@pytest.mark.benchmark
class TestBenchmarks:
    """Detailed benchmarks for critical operations"""
    
    def test_json_serialization_performance(self, benchmark):
        """Benchmark JSON serialization performance"""
        large_data = {
            'results': [{'id': i, 'data': f'item_{i}' * 10} for i in range(1000)]
        }
        
        result = benchmark(lambda: json.dumps(large_data))
        assert len(result) > 0
    
    def test_database_query_performance(self, benchmark):
        """Benchmark database query performance"""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Add test data
        for i in range(100):
            user = User(username=f'user{i}', email=f'user{i}@test.com', role='user')
            user.set_password('password')
            session.add(user)
        session.commit()
        
        def query_users():
            return session.query(User).filter(User.role == 'user').limit(10).all()
        
        result = benchmark(query_users)
        assert len(result) == 10
        
        session.close()

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--benchmark-only'])