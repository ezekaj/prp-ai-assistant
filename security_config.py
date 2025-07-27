#!/usr/bin/env python3
"""
Security configuration for PRP System - Production-ready security settings
"""

from flask import Flask
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os

def configure_security(app: Flask):
    """Configure comprehensive security for the application"""
    
    # Force HTTPS in production
    if os.environ.get('PRP_ENV', 'development').lower() == 'production':
        Talisman(app, 
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,  # 1 year
            session_cookie_secure=True,
            session_cookie_http_only=True,
            session_cookie_samesite='Lax',
            content_security_policy={
                'default-src': "'self'",
                'img-src': '*',
                'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
                'style-src': "'self' 'unsafe-inline'",
                'font-src': "'self' data:",
                'connect-src': "'self'",
                'frame-ancestors': "'none'",
                'form-action': "'self'",
                'base-uri': "'self'"
            },
            content_security_policy_nonce_in=['script-src', 'style-src']
        )
    
    # Configure CORS with specific origins
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS(app, 
         origins=cors_origins,
         supports_credentials=True,
         max_age=3600)
    
    # Configure rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[os.environ.get('RATE_LIMIT_DEFAULT', '100 per hour')],
        storage_uri=os.environ.get('RATE_LIMIT_STORAGE_URL', 'redis://localhost:6379/2'),
        strategy='fixed-window'
    )
    
    # Additional security headers
    @app.after_request
    def set_security_headers(response):
        """Set additional security headers"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Remove server header
        response.headers.pop('Server', None)
        
        return response
    
    return limiter

def generate_secret_key():
    """Generate a secure secret key"""
    import secrets
    return secrets.token_hex(32)

def validate_api_key(api_key: str) -> bool:
    """Validate API key format and strength"""
    if not api_key:
        return False
    
    # Check minimum length
    if len(api_key) < 32:
        return False
    
    # Check for common weak patterns
    weak_patterns = ['12345', 'abcdef', '00000', 'password', 'secret']
    for pattern in weak_patterns:
        if pattern in api_key.lower():
            return False
    
    return True

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Export security utilities
__all__ = [
    'configure_security',
    'generate_secret_key',
    'validate_api_key',
    'hash_password',
    'verify_password'
]