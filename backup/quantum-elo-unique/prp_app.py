#!/usr/bin/env python3
"""
Stateless PRP Application - 12-Factor Compliant
"""

import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from redis import Redis
from dotenv import load_dotenv
from logging_config import configure_logging, get_logger
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import uuid

# Load environment variables
load_dotenv()

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

app = Flask(__name__)

# Configuration from environment
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_URL = os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    ANALYTICS_RETENTION_DAYS = int(os.environ.get('ANALYTICS_RETENTION_DAYS', '90'))
    MAX_PRP_COMPLEXITY = int(os.environ.get('MAX_PRP_COMPLEXITY', '10'))
    DEFAULT_SUCCESS_THRESHOLD = float(os.environ.get('DEFAULT_SUCCESS_THRESHOLD', '0.8'))

app.config.from_object(Config)

# Backing services initialization
def init_backing_services():
    """Initialize all backing services as attached resources"""
    global db_engine, redis_client
    
    # Database connection
    if Config.DATABASE_URL:
        db_engine = create_engine(Config.DATABASE_URL)
    else:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Redis connection
    redis_client = Redis.from_url(Config.REDIS_URL)
    
    # Test connections
    try:
        db_engine.execute("SELECT 1")
        redis_client.ping()
        logger.info("backing_services_initialized", database_url=Config.DATABASE_URL, redis_url=Config.REDIS_URL)
    except Exception as e:
        logger.error("backing_services_initialization_failed", error=str(e))
        raise

# Request logging middleware
from flask import g

@app.before_request
def before_request():
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())
    logger.info("incoming_request",
               request_id=g.request_id,
               method=request.method,
               path=request.path,
               remote_addr=request.remote_addr)

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint or 'unknown', status=response.status_code).inc()
    REQUEST_DURATION.observe(duration)
    
    logger.info("outgoing_response",
               request_id=g.request_id,
               status_code=response.status_code,
               duration_ms=duration * 1000)
    return response

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health_check():
    """Health check endpoint for load balancers"""
    try:
        # Check database
        db_engine.execute("SELECT 1")
        # Check Redis
        redis_client.ping()
        
        health_data = {
            'status': 'healthy',
            'timestamp': os.environ.get('DYNO_STARTED_AT'),
            'version': '2.0.0',
            'checks': {
                'database': 'ok',
                'redis': 'ok'
            }
        }
        logger.info("health_check_successful", **health_data)
        return jsonify(health_data), 200
    except Exception as e:
        error_data = {
            'status': 'unhealthy',
            'error': str(e)
        }
        logger.error("health_check_failed", **error_data)
        return jsonify(error_data), 503

@app.route('/api/prp/generate', methods=['POST'])
def generate_prp():
    """Stateless PRP generation endpoint"""
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('feature_name'):
        return jsonify({'error': 'feature_name is required'}), 400
    
    # Import here to avoid circular imports
    from PRPs.scripts.prp_generator_stateless import StatelessPRPGenerator
    
    generator = StatelessPRPGenerator(db_engine, redis_client)
    result = generator.generate_prp(
        feature_name=data['feature_name'],
        requirements=data.get('requirements', ''),
        complexity=data.get('complexity', 5)
    )
    
    return jsonify(result)

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard():
    """Stateless analytics dashboard"""
    from PRPs.scripts.prp_analytics_stateless import StatelessPRPAnalytics
    
    analytics = StatelessPRPAnalytics(db_engine, redis_client)
    dashboard_data = analytics.get_dashboard_data()
    
    return jsonify(dashboard_data)

@app.route('/api/prp/analyze', methods=['POST'])
def analyze_prp():
    """Stateless PRP analysis endpoint"""
    data = request.get_json()
    
    if not data or not data.get('prp_id'):
        return jsonify({'error': 'prp_id is required'}), 400
    
    from PRPs.scripts.prp_analytics_stateless import StatelessPRPAnalytics
    
    analytics = StatelessPRPAnalytics(db_engine, redis_client)
    result = analytics.analyze_prp_performance(
        prp_id=data['prp_id'],
        success_metrics=data.get('success_metrics', {})
    )
    
    return jsonify(result)

# Process signal handlers for graceful shutdown
import signal
import sys

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("graceful_shutdown_initiated", signal=sig)
    # Close database connections
    if 'db_engine' in globals():
        db_engine.dispose()
    # Close Redis connections
    if 'redis_client' in globals():
        redis_client.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    init_backing_services()
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)