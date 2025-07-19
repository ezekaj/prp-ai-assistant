"""
Security tests for PRP AI Assistant
Tests authentication, authorization, input validation, and security headers
"""

import pytest
import json
from unittest.mock import Mock, patch
from flask import Flask
from flask_jwt_extended import create_access_token

from prp_app_secure import app
from auth import User, create_tokens
from schemas import PRPGenerateSchema, UserLoginSchema


@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return Mock()


@pytest.fixture
def test_user():
    """Test user fixture"""
    user = User(
        id=1,
        username='testuser',
        email='test@example.com',
        role='user',
        is_active=True
    )
    user.set_password('TestPassword123!')
    return user


@pytest.fixture
def admin_user():
    """Admin user fixture"""
    user = User(
        id=2,
        username='admin',
        email='admin@example.com',
        role='admin',
        is_active=True
    )
    user.set_password('AdminPassword123!')
    return user


@pytest.fixture
def auth_headers(test_user):
    """Authorization headers for test user"""
    with app.app_context():
        access_token = create_access_token(
            identity=test_user.username,
            additional_claims={'role': test_user.role, 'email': test_user.email}
        )
        return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture
def admin_auth_headers(admin_user):
    """Authorization headers for admin user"""
    with app.app_context():
        access_token = create_access_token(
            identity=admin_user.username,
            additional_claims={'role': admin_user.role, 'email': admin_user.email}
        )
        return {'Authorization': f'Bearer {access_token}'}


class TestAuthentication:
    """Test authentication functionality"""
    
    def test_login_success(self, client, mock_db_session, test_user):
        """Test successful login"""
        with patch('prp_app_secure.db_session', mock_db_session):
            mock_db_session.query.return_value.filter.return_value.first.return_value = test_user
            
            response = client.post('/auth/login', json={
                'username': 'testuser',
                'password': 'TestPassword123!'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'access_token' in data
            assert 'refresh_token' in data
            assert data['user']['username'] == 'testuser'
    
    def test_login_invalid_credentials(self, client, mock_db_session):
        """Test login with invalid credentials"""
        with patch('prp_app_secure.db_session', mock_db_session):
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post('/auth/login', json={
                'username': 'invalid',
                'password': 'invalid'
            })
            
            assert response.status_code == 401
            data = response.get_json()
            assert data['error'] == 'Invalid credentials'
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post('/auth/login', json={
            'username': 'testuser'
            # Missing password
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Missing username or password' in data['error']
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.post('/api/prp/generate', json={
            'feature_name': 'Test Feature',
            'requirements': 'Test requirements'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['code'] == 'authorization_required'
    
    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        headers = {'Authorization': 'Bearer invalid-token'}
        
        response = client.post('/api/prp/generate',
                             headers=headers,
                             json={
                                 'feature_name': 'Test Feature',
                                 'requirements': 'Test requirements'
                             })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['code'] == 'invalid_token'


class TestAuthorization:
    """Test role-based authorization"""
    
    def test_admin_endpoint_with_user_role(self, client, auth_headers):
        """Test admin endpoint access with user role"""
        response = client.post('/api/admin/cache/clear', headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['code'] == 'forbidden'
        assert 'admin' in data['required_roles']
    
    def test_admin_endpoint_with_admin_role(self, client, admin_auth_headers):
        """Test admin endpoint access with admin role"""
        with patch('prp_app_secure.cache_manager'):
            response = client.post('/api/admin/cache/clear', headers=admin_auth_headers)
            
            assert response.status_code == 200
    
    def test_user_endpoint_with_valid_token(self, client, auth_headers):
        """Test user endpoint access with valid token"""
        with patch('prp_app_secure.StatelessPRPGenerator'):
            response = client.post('/api/prp/generate',
                                 headers=auth_headers,
                                 json={
                                     'feature_name': 'Test Feature',
                                     'requirements': 'Test requirements for the feature',
                                     'complexity': 5
                                 })
            
            # Should not be 401 or 403 (authorization should pass)
            assert response.status_code != 401
            assert response.status_code != 403


class TestInputValidation:
    """Test input validation and schema enforcement"""
    
    def test_prp_generate_valid_input(self, client, auth_headers):
        """Test PRP generation with valid input"""
        with patch('prp_app_secure.StatelessPRPGenerator'):
            valid_data = {
                'feature_name': 'Test Feature',
                'requirements': 'Valid requirements for testing',
                'complexity': 5,
                'project_context': 'Test context'
            }
            
            response = client.post('/api/prp/generate',
                                 headers=auth_headers,
                                 json=valid_data)
            
            # Should pass validation (not 400)
            assert response.status_code != 400
    
    def test_prp_generate_invalid_feature_name(self, client, auth_headers):
        """Test PRP generation with invalid feature name"""
        invalid_data = {
            'feature_name': 'A',  # Too short
            'requirements': 'Valid requirements',
            'complexity': 5
        }
        
        response = client.post('/api/prp/generate',
                             headers=auth_headers,
                             json=invalid_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'validation_error'
        assert 'feature_name' in data['details']
    
    def test_prp_generate_invalid_complexity(self, client, auth_headers):
        """Test PRP generation with invalid complexity"""
        invalid_data = {
            'feature_name': 'Valid Feature Name',
            'requirements': 'Valid requirements',
            'complexity': 15  # Too high
        }
        
        response = client.post('/api/prp/generate',
                             headers=auth_headers,
                             json=invalid_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'validation_error'
        assert 'complexity' in data['details']
    
    def test_prp_generate_xss_attempt(self, client, auth_headers):
        """Test XSS injection attempt in requirements"""
        malicious_data = {
            'feature_name': 'Test Feature',
            'requirements': 'Requirements with <script>alert("xss")</script>',
            'complexity': 5
        }
        
        response = client.post('/api/prp/generate',
                             headers=auth_headers,
                             json=malicious_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'validation_error'
    
    def test_prp_generate_missing_required_fields(self, client, auth_headers):
        """Test PRP generation with missing required fields"""
        incomplete_data = {
            'feature_name': 'Test Feature'
            # Missing requirements
        }
        
        response = client.post('/api/prp/generate',
                             headers=auth_headers,
                             json=incomplete_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'validation_error'
        assert 'requirements' in data['details']


class TestSecurityHeaders:
    """Test security headers and CORS"""
    
    def test_security_headers_present(self, client):
        """Test that security headers are present"""
        response = client.get('/health')
        
        # Check for security headers (these may vary based on Talisman config)
        assert response.headers.get('X-Frame-Options') is not None
        assert response.headers.get('X-Content-Type-Options') is not None
    
    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.options('/api/prp/generate',
                                headers={'Origin': 'http://localhost:3000'})
        
        # CORS headers should be present for allowed origins
        assert response.status_code == 200
    
    def test_request_id_header(self, client):
        """Test that request ID is added to response headers"""
        response = client.get('/health')
        
        assert 'X-Request-ID' in response.headers
        # Should be a valid UUID format
        request_id = response.headers['X-Request-ID']
        assert len(request_id) == 36  # UUID length
        assert request_id.count('-') == 4  # UUID format


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_enforcement(self, client, auth_headers):
        """Test that rate limiting is enforced"""
        # This test would need to be adapted based on your rate limiting rules
        # For example, if PRP generation is limited to 10 per minute
        
        # Make multiple requests quickly
        responses = []
        for i in range(15):  # Exceed the limit
            response = client.post('/api/prp/generate',
                                 headers=auth_headers,
                                 json={
                                     'feature_name': f'Feature {i}',
                                     'requirements': 'Test requirements',
                                     'complexity': 1
                                 })
            responses.append(response.status_code)
        
        # At least one should be rate limited (429)
        assert 429 in responses
    
    def test_rate_limiting_headers(self, client, auth_headers):
        """Test rate limiting headers"""
        response = client.post('/api/prp/generate',
                             headers=auth_headers,
                             json={
                                 'feature_name': 'Test Feature',
                                 'requirements': 'Test requirements',
                                 'complexity': 1
                             })
        
        # Rate limiting headers should be present
        assert 'X-RateLimit-Limit' in response.headers or 'Retry-After' in response.headers


class TestErrorHandling:
    """Test error handling and logging"""
    
    def test_404_error_handling(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent-endpoint')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['code'] == 'not_found'
        assert 'timestamp' in data
    
    def test_500_error_handling(self, client, auth_headers):
        """Test 500 error handling"""
        # Force a 500 error by mocking a function to raise an exception
        with patch('prp_app_secure.StatelessPRPGenerator') as mock_generator:
            mock_generator.side_effect = Exception("Database connection failed")
            
            response = client.post('/api/prp/generate',
                                 headers=auth_headers,
                                 json={
                                     'feature_name': 'Test Feature',
                                     'requirements': 'Test requirements',
                                     'complexity': 5
                                 })
            
            assert response.status_code == 500
            data = response.get_json()
            assert data['code'] == 'generation_error'
            assert 'timestamp' in data or 'details' in data
    
    def test_validation_error_structure(self, client, auth_headers):
        """Test validation error response structure"""
        response = client.post('/api/prp/generate',
                             headers=auth_headers,
                             json={
                                 'feature_name': '',  # Invalid
                                 'requirements': '',  # Invalid
                                 'complexity': 'invalid'  # Invalid type
                             })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'validation_error'
        assert 'details' in data
        assert isinstance(data['details'], dict)
        assert 'timestamp' in data


class TestDataSanitization:
    """Test data sanitization and SQL injection prevention"""
    
    def test_sql_injection_prevention(self, client, auth_headers):
        """Test SQL injection attempt is prevented"""
        malicious_data = {
            'feature_name': "Test'; DROP TABLE users; --",
            'requirements': 'Test requirements',
            'complexity': 5
        }
        
        # This should be safely handled by SQLAlchemy parameterization
        with patch('prp_app_secure.StatelessPRPGenerator'):
            response = client.post('/api/prp/generate',
                                 headers=auth_headers,
                                 json=malicious_data)
            
            # Should not cause internal server error due to SQL injection
            assert response.status_code != 500
    
    def test_json_payload_size_limit(self, client, auth_headers):
        """Test JSON payload size limits"""
        large_data = {
            'feature_name': 'Test Feature',
            'requirements': 'A' * 10000,  # Very large requirements
            'complexity': 5
        }
        
        response = client.post('/api/prp/generate',
                             headers=auth_headers,
                             json=large_data)
        
        # Should be rejected due to validation (max length)
        assert response.status_code == 400