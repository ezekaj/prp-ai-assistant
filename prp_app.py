#!/usr/bin/env python3
"""
Stateless PRP Application - 12-Factor Compliant
"""

import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from redis import Redis
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        app.logger.info("Backing services initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize backing services: {e}")
        raise

# Logging configuration
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.route('/health')
def health_check():
    """Health check endpoint for load balancers"""
    try:
        # Check database
        db_engine.execute("SELECT 1")
        # Check Redis
        redis_client.ping()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': os.environ.get('DYNO_STARTED_AT'),
            'version': '2.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

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
    app.logger.info('Shutting down gracefully...')
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