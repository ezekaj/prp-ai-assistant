"""
Shared test fixtures and configuration for pytest
"""

import pytest
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis
from unittest.mock import Mock, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from auth import Base, User, init_auth, register_auth_routes
from prp_app import app as flask_app


@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application"""
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'DATABASE_URL': 'sqlite:///:memory:',
        'REDIS_URL': 'redis://localhost:6379/15',  # Test database
        'WTF_CSRF_ENABLED': False,
        'JWT_COOKIE_CSRF_PROTECT': False,
    })
    
    # Initialize JWT
    init_auth(flask_app)
    
    yield flask_app


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application"""
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope='function')
def db_session():
    """Create a test database session"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture(scope='function')
def test_user(db_session):
    """Create a test user"""
    user = User(
        username='testuser',
        email='test@example.com',
        role='admin'
    )
    user.set_password('testpassword123')
    user.created_at = datetime.utcnow()
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture(scope='function')
def auth_headers(client, test_user, db_session):
    """Get authentication headers with a valid JWT token"""
    # Register auth routes with test database
    register_auth_routes(client.application, db_session)
    
    # Login to get token
    response = client.post('/auth/login', json={
        'username': test_user.username,
        'password': 'testpassword123'
    })
    
    assert response.status_code == 200
    token = response.get_json()['access_token']
    
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture(scope='function')
def mock_redis():
    """Create a mock Redis client"""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    mock.ping.return_value = True
    mock.pipeline.return_value = mock
    mock.execute.return_value = []
    
    return mock


@pytest.fixture(scope='function')
def mock_db_engine():
    """Create a mock database engine"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope='function')
def sample_prp_data():
    """Sample PRP data for testing"""
    return {
        'feature_name': 'User Authentication System',
        'requirements': 'Implement JWT-based authentication with refresh tokens',
        'complexity': 7,
        'context': {
            'tech_stack': ['Python', 'Flask', 'PostgreSQL'],
            'timeline': '2 weeks',
            'team_size': 3
        }
    }


@pytest.fixture(scope='function')
def sample_multi_agent_task():
    """Sample multi-agent task data"""
    return {
        'task_description': 'Build a complete REST API for user management',
        'agents': ['code', 'test', 'security', 'docs'],
        'priority': 8,
        'context': {
            'requirements': [
                'CRUD operations for users',
                'Role-based access control',
                'API documentation',
                'Security best practices'
            ]
        }
    }


@pytest.fixture(autouse=True)
def reset_database(db_session):
    """Reset database before each test"""
    # Clear all tables
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()


@pytest.fixture(scope='session')
def redis_available():
    """Check if Redis is available for tests"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=15)
        r.ping()
        return True
    except:
        return False


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "requires_redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as benchmark test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Add integration marker to test files
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Skip Redis tests if not available
        if "redis" in item.nodeid.lower():
            item.add_marker(pytest.mark.requires_redis)


# Test utilities
def create_test_users(session, count=5):
    """Create multiple test users"""
    users = []
    for i in range(count):
        user = User(
            username=f'user{i}',
            email=f'user{i}@example.com',
            role='user' if i > 0 else 'admin'
        )
        user.set_password(f'password{i}')
        session.add(user)
        users.append(user)
    
    session.commit()
    return users


def assert_valid_jwt(token):
    """Assert that a token is a valid JWT"""
    parts = token.split('.')
    assert len(parts) == 3  # Header, payload, signature
    
    # Could decode and verify further if needed
    return True


def assert_datetime_recent(dt, seconds=60):
    """Assert that a datetime is recent (within seconds)"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    diff = abs((datetime.utcnow() - dt).total_seconds())
    assert diff < seconds, f"Datetime {dt} is not within {seconds} seconds of now"