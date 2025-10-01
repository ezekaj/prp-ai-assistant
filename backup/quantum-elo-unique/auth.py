"""
Authentication module for PRP System
Implements JWT-based authentication with role-based access control
"""

import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any

from flask import jsonify, request, current_app
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, verify_jwt_in_request,
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


def init_auth(app):
    """Initialize authentication for the Flask app"""
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex())
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_ALGORITHM'] = 'HS256'
    
    jwt = JWTManager(app)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'code': 'token_expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'code': 'invalid_token'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Authorization required',
            'code': 'authorization_required'
        }), 401
    
    return jwt


def role_required(*allowed_roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role', 'user')
            
            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'code': 'forbidden',
                    'required_roles': list(allowed_roles),
                    'user_role': user_role
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def create_tokens(user: User) -> Dict[str, str]:
    """Create access and refresh tokens for user"""
    # Create tokens with additional claims
    additional_claims = {
        'role': user.role,
        'email': user.email
    }
    
    access_token = create_access_token(
        identity=user.username,
        additional_claims=additional_claims
    )
    
    refresh_token = create_refresh_token(
        identity=user.username,
        additional_claims=additional_claims
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
    }


def get_current_user() -> Optional[str]:
    """Get current authenticated user"""
    try:
        verify_jwt_in_request()
        return get_jwt_identity()
    except Exception:
        return None


# Authentication endpoints to be added to main app
def register_auth_routes(app, db_session):
    """Register authentication routes"""
    
    @app.route('/auth/register', methods=['POST'])
    def register():
        """Register new user"""
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        existing_user = db_session.query(User).filter(
            (User.username == data['username']) | 
            (User.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])
        
        db_session.add(user)
        db_session.commit()
        
        # Create tokens
        tokens = create_tokens(user)
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict(),
            **tokens
        }), 201
    
    @app.route('/auth/login', methods=['POST'])
    def login():
        """Login user"""
        data = request.get_json()
        
        if not data or not all(k in data for k in ('username', 'password')):
            return jsonify({'error': 'Missing username or password'}), 400
        
        # Find user
        user = db_session.query(User).filter(
            User.username == data['username']
        ).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'User account is disabled'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db_session.commit()
        
        # Create tokens
        tokens = create_tokens(user)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            **tokens
        }), 200
    
    @app.route('/auth/refresh', methods=['POST'])
    @jwt_required(refresh=True)
    def refresh():
        """Refresh access token"""
        identity = get_jwt_identity()
        claims = get_jwt()
        
        # Create new access token
        access_token = create_access_token(
            identity=identity,
            additional_claims={
                'role': claims.get('role'),
                'email': claims.get('email')
            }
        )
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
        }), 200
    
    @app.route('/auth/profile', methods=['GET'])
    @jwt_required()
    def profile():
        """Get current user profile"""
        username = get_jwt_identity()
        user = db_session.query(User).filter(User.username == username).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
    
    @app.route('/auth/logout', methods=['POST'])
    @jwt_required()
    def logout():
        """Logout user (client should remove tokens)"""
        # In a production app, you might want to blacklist the token here
        return jsonify({'message': 'Logout successful'}), 200