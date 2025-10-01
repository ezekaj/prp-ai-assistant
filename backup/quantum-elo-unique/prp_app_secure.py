#!/usr/bin/env python3
"""
Secure PRP Application - 12-Factor Compliant with Full Security
Enhanced with authentication, caching, pagination, and security headers
"""

import os
import signal
import sys
import time
import uuid
from datetime import datetime

from flask import Flask, request, jsonify, g
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_talisman import Talisman
from sqlalchemy import create_engine
from redis import Redis
from dotenv import load_dotenv
from marshmallow import ValidationError
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from logging_config import configure_logging, get_logger
from config import config
from auth import init_auth, register_auth_routes, role_required, User
from schemas import (
    PRPGenerateSchema, PRPAnalyzeSchema, PaginationSchema, 
    DashboardQuerySchema, validate_request
)
from cache import cache_manager, cached, get_cache_health

# Load environment variables
load_dotenv()

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
CACHE_HITS = Counter('cache_hits_total', 'Total cache hits', ['namespace'])
CACHE_MISSES = Counter('cache_misses_total', 'Total cache misses', ['namespace'])

# Flask app initialization
app = Flask(__name__)
app.config.from_object(config)

# Security Configuration
csrf = None
if config.PRP_ENV != 'development':
    # Enable security headers in production
    Talisman(app, 
             force_https=getattr(config, 'FORCE_HTTPS', True),
             strict_transport_security=True,
             content_security_policy={
                 'default-src': "'self'",
                 'script-src': "'self' 'unsafe-inline'",
                 'style-src': "'self' 'unsafe-inline'",
                 'img-src': "'self' data: https:",
             })

# CORS configuration
allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[os.environ.get('RATE_LIMIT_DEFAULT', '100 per hour')],
    storage_uri=os.environ.get('RATE_LIMIT_STORAGE_URL', config.REDIS_URL)
)

# JWT Authentication
jwt = init_auth(app)

# Database setup with connection pooling
db_engine = None
redis_client = None
db_session = None

def init_backing_services():
    """Initialize all backing services as attached resources"""
    global db_engine, redis_client, db_session
    
    try:
        # Database connection with pooling
        db_engine = create_engine(
            config.DATABASE_URL,
            **config.SQLALCHEMY_ENGINE_OPTIONS
        )
        
        # Redis connection
        redis_client = Redis.from_url(
            config.REDIS_URL,
            socket_timeout=config.REDIS_TIMEOUT,
            socket_connect_timeout=config.REDIS_TIMEOUT,
            socket_keepalive=True,
            max_connections=config.REDIS_POOL_SIZE
        )
        
        # Create database session factory
        from sqlalchemy.orm import sessionmaker, scoped_session
        Session = scoped_session(sessionmaker(bind=db_engine))
        db_session = Session
        
        # Test connections
        with db_engine.connect() as conn:
            conn.execute("SELECT 1")
        redis_client.ping()
        
        logger.info("backing_services_initialized", 
                   database_url=config.DATABASE_URL[:50] + "...",
                   redis_url=config.REDIS_URL[:50] + "...")
        
    except Exception as e:
        logger.error("backing_services_initialization_failed", error=str(e))
        raise

# Request/Response middleware
@app.before_request
def before_request():
    """Log incoming requests and set up request context"""
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())
    
    # Add request ID to response headers
    @app.after_request
    def add_request_id(response):
        response.headers['X-Request-ID'] = g.request_id
        return response
    
    logger.info("incoming_request",
               request_id=g.request_id,
               method=request.method,
               path=request.path,
               remote_addr=request.remote_addr,
               user_agent=request.headers.get('User-Agent', ''))

@app.after_request
def after_request(response):
    """Log outgoing responses and update metrics"""
    duration = time.time() - g.start_time
    
    # Update Prometheus metrics
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.endpoint or 'unknown', 
        status=response.status_code
    ).inc()
    REQUEST_DURATION.observe(duration)
    
    # Log response
    logger.info("outgoing_response",
               request_id=g.request_id,
               status_code=response.status_code,
               duration_ms=round(duration * 1000, 2),
               content_length=response.content_length)
    
    return response

@app.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle marshmallow validation errors"""
    logger.warning("validation_error", 
                  request_id=getattr(g, 'request_id', 'unknown'),
                  errors=e.messages)
    
    return jsonify({
        'error': 'Validation failed',
        'code': 'validation_error',
        'details': e.messages,
        'timestamp': datetime.utcnow().isoformat()
    }), 400

@app.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Resource not found',
        'code': 'not_found',
        'timestamp': datetime.utcnow().isoformat()
    }), 404

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle 500 errors"""
    logger.error("internal_server_error", 
                request_id=getattr(g, 'request_id', 'unknown'),
                error=str(e))
    
    return jsonify({
        'error': 'Internal server error',
        'code': 'internal_error',
        'timestamp': datetime.utcnow().isoformat()
    }), 500

# Health and monitoring endpoints
@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0.0',
            'environment': config.PRP_ENV,
            'checks': {}
        }
        
        # Database health
        try:
            with db_engine.connect() as conn:
                conn.execute("SELECT 1")
            health_data['checks']['database'] = 'ok'
        except Exception as e:
            health_data['checks']['database'] = f'error: {str(e)}'
            health_data['status'] = 'degraded'
        
        # Redis health
        try:
            redis_client.ping()
            health_data['checks']['redis'] = 'ok'
        except Exception as e:
            health_data['checks']['redis'] = f'error: {str(e)}'
            health_data['status'] = 'degraded'
        
        # Cache health
        cache_health = get_cache_health()
        health_data['checks']['cache'] = 'ok' if cache_health['redis_healthy'] else 'error'
        health_data['cache_stats'] = cache_health['stats']
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        logger.info("health_check", **health_data)
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        error_data = {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        logger.error("health_check_failed", **error_data)
        return jsonify(error_data), 503

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/ready')
def readiness_check():
    """Kubernetes readiness probe"""
    return jsonify({'status': 'ready'}), 200

# API Endpoints with authentication and caching

@app.route('/api/prp/generate', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
@validate_request(PRPGenerateSchema)
def generate_prp(validated_data):
    """Secure PRP generation endpoint with caching"""
    current_user = get_jwt_identity()
    
    try:
        # Import here to avoid circular imports
        from PRPs.scripts.prp_generator_stateless import StatelessPRPGenerator
        
        generator = StatelessPRPGenerator(db_engine, redis_client)
        
        # Check cache first
        cache_key = f"prp_{validated_data['feature_name']}_{validated_data['complexity']}"
        cached_result = cache_manager.get('prp_generation', cache_key)
        
        if cached_result:
            CACHE_HITS.labels(namespace='prp_generation').inc()
            logger.info("prp_generation_cache_hit", 
                       user=current_user,
                       feature_name=validated_data['feature_name'])
            return jsonify(cached_result)
        
        CACHE_MISSES.labels(namespace='prp_generation').inc()
        
        # Generate PRP
        result = generator.generate_prp(
            feature_name=validated_data['feature_name'],
            requirements=validated_data['requirements'],
            complexity=validated_data['complexity'],
            project_context=validated_data.get('project_context', ''),
            user=current_user
        )
        
        # Cache result based on complexity (more complex = longer cache)
        ttl = 3600 + (validated_data['complexity'] * 600)
        cache_manager.set('prp_generation', cache_key, result, ttl)
        
        logger.info("prp_generation_success",
                   user=current_user,
                   feature_name=validated_data['feature_name'],
                   complexity=validated_data['complexity'])
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error("prp_generation_failed",
                    user=current_user,
                    feature_name=validated_data['feature_name'],
                    error=str(e))
        
        return jsonify({
            'error': 'PRP generation failed',
            'code': 'generation_error',
            'details': str(e)
        }), 500

@app.route('/api/analytics/dashboard', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
@validate_request(PaginationSchema)
def get_dashboard(validated_data):
    """Secure analytics dashboard with pagination and caching"""
    current_user = get_jwt_identity()
    
    try:
        # Check cache
        cache_key = f"dashboard_{validated_data['page']}_{validated_data['per_page']}"
        cached_result = cache_manager.get('analytics', cache_key)
        
        if cached_result:
            CACHE_HITS.labels(namespace='analytics').inc()
            return jsonify(cached_result)
        
        CACHE_MISSES.labels(namespace='analytics').inc()
        
        from PRPs.scripts.prp_analytics_stateless import StatelessPRPAnalytics
        
        analytics = StatelessPRPAnalytics(db_engine, redis_client)
        dashboard_data = analytics.get_dashboard_data(
            page=validated_data['page'],
            per_page=validated_data['per_page'],
            sort_by=validated_data['sort_by'],
            order=validated_data['order']
        )
        
        # Cache for 30 minutes
        cache_manager.set('analytics', cache_key, dashboard_data, 1800)
        
        logger.info("dashboard_access", user=current_user)
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error("dashboard_access_failed", user=current_user, error=str(e))
        return jsonify({
            'error': 'Dashboard access failed',
            'code': 'dashboard_error'
        }), 500

@app.route('/api/prp/analyze', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
@validate_request(PRPAnalyzeSchema)
def analyze_prp(validated_data):
    """Secure PRP analysis endpoint"""
    current_user = get_jwt_identity()
    
    try:
        from PRPs.scripts.prp_analytics_stateless import StatelessPRPAnalytics
        
        analytics = StatelessPRPAnalytics(db_engine, redis_client)
        result = analytics.analyze_prp_performance(
            prp_id=validated_data['prp_id'],
            actual_time=validated_data['actual_time'],
            success=validated_data['success'],
            issues_encountered=validated_data['issues_encountered'],
            patterns_used=validated_data['patterns_used'],
            user=current_user
        )
        
        # Invalidate related caches
        cache_manager.clear_namespace('analytics')
        
        logger.info("prp_analysis_success",
                   user=current_user,
                   prp_id=validated_data['prp_id'])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("prp_analysis_failed",
                    user=current_user,
                    prp_id=validated_data['prp_id'],
                    error=str(e))
        
        return jsonify({
            'error': 'PRP analysis failed',
            'code': 'analysis_error'
        }), 500

# Admin endpoints
@app.route('/api/admin/cache/clear', methods=['POST'])
@jwt_required()
@role_required('admin')
def clear_cache():
    """Admin endpoint to clear cache"""
    current_user = get_jwt_identity()
    
    data = request.get_json() or {}
    namespace = data.get('namespace')
    
    if namespace:
        cache_manager.clear_namespace(namespace)
        message = f"Cleared cache for namespace: {namespace}"
    else:
        # Clear all namespaces
        for ns in ['prp_generation', 'analytics', 'user_data']:
            cache_manager.clear_namespace(ns)
        message = "Cleared all caches"
    
    logger.info("cache_cleared", user=current_user, namespace=namespace)
    
    return jsonify({
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_admin_stats():
    """Admin endpoint for system statistics"""
    current_user = get_jwt_identity()
    
    stats = {
        'cache': get_cache_health(),
        'database_pool': {
            'size': db_engine.pool.size(),
            'checked_in': db_engine.pool.checkedin(),
            'checked_out': db_engine.pool.checkedout(),
            'overflow': db_engine.pool.overflow(),
        },
        'environment': config.PRP_ENV,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info("admin_stats_accessed", user=current_user)
    return jsonify(stats)

# Register authentication routes
register_auth_routes(app, db_session)

# Graceful shutdown handling
def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("graceful_shutdown_initiated", signal=sig)
    
    try:
        # Close database connections
        if db_engine:
            db_engine.dispose()
            logger.info("database_connections_closed")
        
        # Close Redis connections
        if redis_client:
            redis_client.close()
            logger.info("redis_connections_closed")
        
        # Close session factory
        if db_session:
            db_session.remove()
            logger.info("database_sessions_closed")
            
    except Exception as e:
        logger.error("shutdown_cleanup_error", error=str(e))
    
    logger.info("graceful_shutdown_completed")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    # Validate configuration
    try:
        config.validate()
        logger.info("configuration_validated")
    except ValueError as e:
        logger.error("configuration_validation_failed", error=str(e))
        sys.exit(1)
    
    # Initialize services
    init_backing_services()
    
    # Start application
    port = config.PORT
    debug = config.PRP_ENV == 'development'
    
    logger.info("application_starting", 
               port=port, 
               debug=debug,
               environment=config.PRP_ENV)
    
    app.run(host='0.0.0.0', port=port, debug=debug)