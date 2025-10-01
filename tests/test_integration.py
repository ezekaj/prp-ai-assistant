"""
Integration tests for the PRP AI Assistant System
Tests the complete flow including authentication, API versioning, and multi-agent coordination
"""

import pytest
import json
import os
from datetime import datetime
from flask import Flask
from flask_jwt_extended import create_access_token
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prp_app import app, Config, init_backing_services
from auth import User, Base, init_auth, register_auth_routes
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestIntegration:
    """Integration tests for API endpoints"""
    
    @pytest.fixture(scope='class')
    def test_app(self):
        """Create test application"""
        # Set test configuration
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
        app.config['DATABASE_URL'] = 'sqlite:///:memory:'
        app.config['REDIS_URL'] = 'redis://localhost:6379/15'  # Use test database
        
        # Initialize test database
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Store in app config
        app.config['db_engine'] = engine
        app.config['db_session'] = session
        app.config['redis_client'] = None  # Mock Redis for tests
        
        # Initialize JWT
        jwt = init_auth(app)
        
        # Register auth routes
        register_auth_routes(app, session)
        
        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            role='admin'
        )
        test_user.set_password('testpass123')
        session.add(test_user)
        session.commit()
        
        with app.test_client() as client:
            yield client
            
        # Cleanup
        session.close()
        engine.dispose()
    
    @pytest.fixture
    def auth_headers(self, test_app):
        """Get authentication headers"""
        # Login to get token
        response = test_app.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass123'
        })
        data = json.loads(response.data)
        token = data['access_token']
        
        return {'Authorization': f'Bearer {token}'}
    
    def test_health_check(self, test_app):
        """Test health check endpoint"""
        response = test_app.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] in ['healthy', 'unhealthy']
        assert 'version' in data
        assert 'environment' in data
    
    def test_metrics_endpoint(self, test_app):
        """Test Prometheus metrics endpoint"""
        response = test_app.get('/metrics')
        assert response.status_code == 200
        assert b'http_requests_total' in response.data
    
    def test_authentication_flow(self, test_app):
        """Test complete authentication flow"""
        # Register new user
        response = test_app.post('/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123'
        })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
        
        # Login with new user
        response = test_app.post('/auth/login', json={
            'username': 'newuser',
            'password': 'password123'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        access_token = data['access_token']
        refresh_token = data['refresh_token']
        
        # Access protected endpoint
        headers = {'Authorization': f'Bearer {access_token}'}
        response = test_app.get('/auth/profile', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['username'] == 'newuser'
        
        # Refresh token
        headers = {'Authorization': f'Bearer {refresh_token}'}
        response = test_app.post('/auth/refresh', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
    
    def test_api_versioning(self, test_app):
        """Test API versioning endpoints"""
        # Test v1 endpoint
        response = test_app.get('/api/v1/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['version'] == '1.0'
        
        # Test v2 endpoint
        response = test_app.get('/api/v2/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['version'] == '2.0'
        assert 'features' in data
    
    def test_prp_generation_v1(self, test_app, auth_headers):
        """Test V1 PRP generation"""
        response = test_app.post('/api/v1/prp/generate', 
            headers=auth_headers,
            json={
                'feature_name': 'User Authentication',
                'requirements': 'OAuth2 with JWT',
                'complexity': 7
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'prp_id' in data or 'id' in data
    
    def test_prp_generation_v2(self, test_app, auth_headers):
        """Test V2 PRP generation with enhanced features"""
        response = test_app.post('/api/v2/prp/generate', 
            headers=auth_headers,
            json={
                'feature_name': 'Payment Processing',
                'requirements': 'Stripe integration with webhooks',
                'complexity': 8
            }
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'metadata' in data
        assert data['metadata']['api_version'] == '2.0'
        assert 'request_id' in data['metadata']
    
    def test_validation_errors_v2(self, test_app, auth_headers):
        """Test V2 validation error responses"""
        # Missing feature_name
        response = test_app.post('/api/v2/prp/generate', 
            headers=auth_headers,
            json={'complexity': 5}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'errors' in data
        assert 'request_id' in data
        
        # Short feature_name
        response = test_app.post('/api/v2/prp/generate', 
            headers=auth_headers,
            json={'feature_name': 'ab'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'errors' in data
    
    def test_multi_agent_endpoint(self, test_app, auth_headers):
        """Test multi-agent coordination endpoint"""
        response = test_app.post('/api/v2/prp/multi-agent', 
            headers=auth_headers,
            json={
                'task_description': 'Build a complete REST API for user management',
                'agents': ['code', 'test', 'security', 'docs'],
                'priority': 8
            }
        )
        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'task_id' in data
        assert data['status'] == 'created'
        assert 'tracking_url' in data
    
    def test_agents_listing(self, test_app, auth_headers):
        """Test agents listing endpoint"""
        response = test_app.get('/api/v2/agents', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agents' in data
        assert 'total' in data
        assert 'available' in data
    
    def test_analytics_dashboard_v2(self, test_app, auth_headers):
        """Test V2 analytics with pagination"""
        response = test_app.get('/api/v2/analytics/dashboard?page=1&per_page=10', 
            headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'pagination' in data
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 10
        assert '_links' in data
    
    def test_legacy_endpoint_redirect(self, test_app):
        """Test legacy endpoints return proper deprecation notice"""
        response = test_app.post('/api/prp/generate', json={})
        assert response.status_code == 301
        data = json.loads(response.data)
        assert 'deprecated' in data['error']
        assert '/api/v1/prp/generate' in data['message']
    
    def test_unauthorized_access(self, test_app):
        """Test unauthorized access to protected endpoints"""
        # No token
        response = test_app.post('/api/v1/prp/generate', json={
            'feature_name': 'Test Feature'
        })
        assert response.status_code == 401
        
        # Invalid token
        headers = {'Authorization': 'Bearer invalid-token'}
        response = test_app.post('/api/v1/prp/generate', 
            headers=headers,
            json={'feature_name': 'Test Feature'}
        )
        assert response.status_code in [401, 422]  # Depends on JWT config
    
    def test_role_based_access(self, test_app):
        """Test role-based access control"""
        # Create user with limited role
        with app.app_context():
            session = app.config['db_session']
            limited_user = User(
                username='limited',
                email='limited@example.com',
                role='viewer'
            )
            limited_user.set_password('limited123')
            session.add(limited_user)
            session.commit()
        
        # Login as limited user
        response = test_app.post('/auth/login', json={
            'username': 'limited',
            'password': 'limited123'
        })
        data = json.loads(response.data)
        limited_token = data['access_token']
        limited_headers = {'Authorization': f'Bearer {limited_token}'}
        
        # Try to access admin endpoint
        response = test_app.post('/api/v1/prp/analyze', 
            headers=limited_headers,
            json={'prp_id': '123'}
        )
        assert response.status_code == 403  # Forbidden

class TestMultiAgent:
    """Tests for multi-agent coordination"""
    
    def test_agent_task_creation(self):
        """Test agent task creation and assignment"""
        from PRPs.scripts.multi_agent_coordinator import MultiAgentCoordinator, AgentType
        
        coordinator = MultiAgentCoordinator(redis_url='redis://localhost:6379/15')
        
        # Create task
        task_id = coordinator.create_task(
            description="Generate user authentication module",
            agent_type=AgentType.CODE_GENERATION,
            context={'requirements': 'JWT with refresh tokens'},
            priority=8
        )
        
        assert task_id is not None
        assert len(task_id) == 36  # UUID format
    
    def test_agent_registration(self):
        """Test agent registration and discovery"""
        from PRPs.scripts.multi_agent_coordinator import MultiAgentCoordinator, AgentType
        
        coordinator = MultiAgentCoordinator(redis_url='redis://localhost:6379/15')
        
        # Register agent
        agent_id = "test-code-agent-1"
        coordinator.register_agent(
            agent_id=agent_id,
            agent_type=AgentType.CODE_GENERATION,
            capabilities=['python', 'api_design']
        )
        
        # Find agents
        agents = coordinator.find_available_agents(AgentType.CODE_GENERATION)
        assert len(agents) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])