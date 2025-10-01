"""
Unit tests for authentication module
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from flask import Flask
from flask_jwt_extended import decode_token

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import User, init_auth, create_tokens, role_required, get_current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestAuth:
    """Test authentication functionality"""
    
    @pytest.fixture(scope='class')
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
        app.config['TESTING'] = True
        
        init_auth(app)
        return app
    
    @pytest.fixture
    def test_user(self):
        """Create test user"""
        user = User(
            username='testuser',
            email='test@example.com',
            role='admin'
        )
        user.set_password('securepassword123')
        return user
    
    def test_user_creation(self, test_user):
        """Test user model creation"""
        assert test_user.username == 'testuser'
        assert test_user.email == 'test@example.com'
        assert test_user.role == 'admin'
        assert test_user.is_active == True
        assert test_user.password_hash is not None
    
    def test_password_hashing(self, test_user):
        """Test password hashing and verification"""
        # Password should be hashed, not plain text
        assert test_user.password_hash != 'securepassword123'
        
        # Correct password should verify
        assert test_user.check_password('securepassword123') == True
        
        # Wrong password should not verify
        assert test_user.check_password('wrongpassword') == False
    
    def test_user_to_dict(self, test_user):
        """Test user serialization"""
        user_dict = test_user.to_dict()
        
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['role'] == 'admin'
        assert 'password_hash' not in user_dict  # Should not expose password
    
    def test_create_tokens(self, app, test_user):
        """Test JWT token creation"""
        with app.app_context():
            tokens = create_tokens(test_user)
            
            assert 'access_token' in tokens
            assert 'refresh_token' in tokens
            assert 'token_type' in tokens
            assert tokens['token_type'] == 'Bearer'
            assert 'expires_in' in tokens
            
            # Decode and verify access token claims
            access_payload = decode_token(tokens['access_token'])
            assert access_payload['sub'] == 'testuser'
            assert access_payload['role'] == 'admin'
            assert access_payload['email'] == 'test@example.com'
    
    def test_role_required_decorator(self, app):
        """Test role-based access control decorator"""
        @role_required('admin', 'manager')
        def admin_only_function():
            return "Success"
        
        with app.test_request_context():
            # Create tokens for admin user
            admin_user = User(username='admin', email='admin@example.com', role='admin')
            admin_tokens = create_tokens(admin_user)
            
            # Create tokens for regular user
            regular_user = User(username='user', email='user@example.com', role='user')
            user_tokens = create_tokens(regular_user)
            
            # Admin should have access
            with app.test_request_context(
                headers={'Authorization': f'Bearer {admin_tokens["access_token"]}'}
            ):
                from flask_jwt_extended import verify_jwt_in_request
                verify_jwt_in_request()
                result = admin_only_function()
                assert result == "Success"
            
            # Regular user should be denied
            with app.test_request_context(
                headers={'Authorization': f'Bearer {user_tokens["access_token"]}'}
            ):
                verify_jwt_in_request()
                with pytest.raises(Exception):  # Would return 403 in actual request
                    admin_only_function()
    
    def test_jwt_configuration(self, app):
        """Test JWT configuration"""
        assert app.config['JWT_SECRET_KEY'] is not None
        assert app.config['JWT_ACCESS_TOKEN_EXPIRES'] == timedelta(hours=1)
        assert app.config['JWT_REFRESH_TOKEN_EXPIRES'] == timedelta(days=30)
        assert app.config['JWT_ALGORITHM'] == 'HS256'
    
    def test_token_expiration(self, app, test_user):
        """Test token expiration times"""
        with app.app_context():
            tokens = create_tokens(test_user)
            
            access_payload = decode_token(tokens['access_token'])
            refresh_payload = decode_token(tokens['refresh_token'])
            
            # Check expiration times
            access_exp = datetime.fromtimestamp(access_payload['exp'])
            refresh_exp = datetime.fromtimestamp(refresh_payload['exp'])
            now = datetime.utcnow()
            
            # Access token should expire in ~1 hour
            access_delta = access_exp - now
            assert 3500 < access_delta.total_seconds() < 3700  # Allow some variance
            
            # Refresh token should expire in ~30 days
            refresh_delta = refresh_exp - now
            assert 2591000 < refresh_delta.total_seconds() < 2593000


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    @pytest.fixture
    def client(self, app):
        """Create test client with database"""
        # Setup test database
        engine = create_engine('sqlite:///:memory:')
        from auth import Base
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Register routes
        from auth import register_auth_routes
        register_auth_routes(app, session)
        
        with app.test_client() as client:
            yield client
        
        session.close()
    
    def test_user_registration(self, client):
        """Test user registration endpoint"""
        response = client.post('/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'User created successfully'
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['username'] == 'newuser'
    
    def test_duplicate_registration(self, client):
        """Test duplicate user registration"""
        # Register first user
        client.post('/auth/register', json={
            'username': 'duplicate',
            'email': 'dup@example.com',
            'password': 'password123'
        })
        
        # Try to register same username
        response = client.post('/auth/register', json={
            'username': 'duplicate',
            'email': 'other@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['error'] == 'User already exists'
    
    def test_login_success(self, client):
        """Test successful login"""
        # Register user first
        client.post('/auth/register', json={
            'username': 'logintest',
            'email': 'login@example.com',
            'password': 'testpass123'
        })
        
        # Login
        response = client.post('/auth/login', json={
            'username': 'logintest',
            'password': 'testpass123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Login successful'
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/auth/login', json={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid credentials'
    
    def test_token_refresh(self, client):
        """Test token refresh endpoint"""
        # Register and login
        reg_response = client.post('/auth/register', json={
            'username': 'refreshtest',
            'email': 'refresh@example.com',
            'password': 'testpass123'
        })
        
        refresh_token = reg_response.get_json()['refresh_token']
        
        # Refresh token
        response = client.post('/auth/refresh', 
            headers={'Authorization': f'Bearer {refresh_token}'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' not in data  # Only access token is refreshed
    
    def test_profile_endpoint(self, client):
        """Test profile endpoint with authentication"""
        # Register user
        reg_response = client.post('/auth/register', json={
            'username': 'profiletest',
            'email': 'profile@example.com',
            'password': 'testpass123'
        })
        
        access_token = reg_response.get_json()['access_token']
        
        # Get profile
        response = client.get('/auth/profile',
            headers={'Authorization': f'Bearer {access_token}'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['username'] == 'profiletest'
        assert data['user']['email'] == 'profile@example.com'
    
    def test_profile_unauthorized(self, client):
        """Test profile endpoint without authentication"""
        response = client.get('/auth/profile')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

if __name__ == '__main__':
    pytest.main([__file__, '-v'])