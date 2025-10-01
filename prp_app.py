#!/usr/bin/env python3
"""
Stateless PRP Application - 12-Factor Compliant
"""

import os
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from redis import Redis
from dotenv import load_dotenv
from logging_config import configure_logging, get_logger
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import uuid

# Import authentication
from auth import init_auth, register_auth_routes, jwt_required, role_required, User, Base

# Load environment variables
load_dotenv()

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

app = Flask(__name__)

# Enable CORS for frontend integration
CORS(app, origins=os.environ.get('ALLOWED_ORIGINS', '*').split(','))

# Initialize JWT authentication
jwt = init_auth(app)

# Configuration from environment
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')  # No fallback for security
    DATABASE_URL = os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    ANALYTICS_RETENTION_DAYS = int(os.environ.get('ANALYTICS_RETENTION_DAYS', '90'))
    MAX_PRP_COMPLEXITY = int(os.environ.get('MAX_PRP_COMPLEXITY', '10'))
    DEFAULT_SUCCESS_THRESHOLD = float(os.environ.get('DEFAULT_SUCCESS_THRESHOLD', '0.8'))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required")
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")

app.config.from_object(Config)

# Import backing services manager
from backing_services import init_backing_services as init_services, get_backing_services

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

@app.route('/api')
def api_info():
    """API information in JSON format"""
    return jsonify({
        'service': 'PRP AI Assistant System',
        'version': '2.0.0',
        'status': 'running',
        'environment': os.environ.get('PRP_ENV', 'development'),
        'api_versions': {
            'v1': '/api/v1/',
            'v2': '/api/v2/' 
        },
        'endpoints': {
            'health': '/health',
            'metrics': '/metrics',
            'auth': '/auth/*',
            'api_v1': {
                'generate_prp': '/api/v1/prp/generate',
                'analytics': '/api/v1/analytics/dashboard',
                'analyze_prp': '/api/v1/prp/analyze'
            },
            'api_v2': {
                'generate_prp': '/api/v2/prp/generate',
                'analytics': '/api/v2/analytics/dashboard',
                'analyze_prp': '/api/v2/prp/analyze',
                'multi_agent': '/api/v2/prp/multi-agent'
            }
        },
        'documentation': 'See README.md for API documentation'
    })

@app.route('/')
def home():
    """Home page with beautiful HTML interface"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PRP AI Assistant System</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }}
            .container {{ 
                background: rgba(255,255,255,0.1); 
                padding: 30px; 
                border-radius: 15px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }}
            h1 {{ 
                color: #ffffff; 
                text-align: center;
                font-size: 2.5em;
                margin-bottom: 30px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            .status {{ 
                background: #4CAF50; 
                color: white; 
                padding: 10px 20px; 
                border-radius: 25px; 
                display: inline-block;
                margin: 10px 0;
                font-weight: bold;
            }}
            .endpoint {{ 
                background: rgba(255,255,255,0.2); 
                margin: 10px 0; 
                padding: 15px; 
                border-radius: 8px;
                border-left: 4px solid #FFD700;
            }}
            .endpoint h3 {{ 
                margin-top: 0; 
                color: #FFD700;
            }}
            .endpoint-url {{ 
                font-family: 'Courier New', monospace; 
                background: rgba(0,0,0,0.3); 
                padding: 8px; 
                border-radius: 4px;
                margin: 5px 0;
                word-break: break-all;
            }}
            .feature {{ 
                background: rgba(255,255,255,0.1); 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 8px;
                border-left: 4px solid #00E676;
            }}
            .grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 20px; 
                margin: 20px 0;
            }}
            a {{ 
                color: #FFD700; 
                text-decoration: none;
            }}
            a:hover {{ 
                text-decoration: underline;
            }}
            .button {{ 
                background: #FF6B6B; 
                color: white; 
                padding: 12px 24px; 
                border: none; 
                border-radius: 6px; 
                cursor: pointer; 
                text-decoration: none; 
                display: inline-block;
                margin: 5px;
                font-weight: bold;
                transition: background 0.3s;
            }}
            .button:hover {{ 
                background: #FF5252;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 PRP AI Assistant System</h1>
            
            <div class="status">
                ✅ System Status: ACTIVE & RUNNING - Version 2.0.0
            </div>
            <div class="status" style="background: #2196F3;">
                🌍 Environment: {os.environ.get('PRP_ENV', 'development')}
            </div>
            
            <h2>🎯 Quick Actions</h2>
            <div>
                <a href="/health" class="button">🏥 Health Check</a>
                <a href="/metrics" class="button">📊 Metrics</a>
                <a href="/api/v2/" class="button">🔧 API v2</a>
            </div>
            
            <div class="grid">
                <div class="endpoint">
                    <h3>🔐 Authentication</h3>
                    <div class="endpoint-url">POST /auth/register</div>
                    <div class="endpoint-url">POST /auth/login</div>
                    <div class="endpoint-url">POST /auth/refresh</div>
                    <p>JWT-based authentication with role-based access control</p>
                </div>
                
                <div class="endpoint">
                    <h3>🤖 Multi-Agent System</h3>
                    <div class="endpoint-url">POST /api/v2/prp/multi-agent</div>
                    <div class="endpoint-url">GET /api/v2/agents/</div>
                    <div class="endpoint-url">GET /api/v2/tasks/{{id}}</div>
                    <p>Coordinate multiple AI agents for complex tasks</p>
                </div>
                
                <div class="endpoint">
                    <h3>📊 Analytics & PRP</h3>
                    <div class="endpoint-url">POST /api/v2/prp/generate</div>
                    <div class="endpoint-url">POST /api/v2/prp/analyze</div>
                    <div class="endpoint-url">GET /api/v2/analytics/dashboard</div>
                    <p>Generate and analyze Problem-Resolution Plans</p>
                </div>
                
                <div class="endpoint">
                    <h3>⚙️ System Monitoring</h3>
                    <div class="endpoint-url">GET /health</div>
                    <div class="endpoint-url">GET /metrics</div>
                    <p>Health checks, Prometheus metrics, and system status</p>
                </div>
            </div>
            
            <h2>✨ System Features</h2>
            <div class="grid">
                <div class="feature">
                    <h3>🔒 Enterprise Security</h3>
                    <p>JWT authentication, password hashing, role-based access control, CORS protection</p>
                </div>
                
                <div class="feature">
                    <h3>🚀 High Performance</h3>
                    <p>Database connection pooling, Redis caching, structured logging, Prometheus metrics</p>
                </div>
                
                <div class="feature">
                    <h3>🔄 API Versioning</h3>
                    <p>v1 (backward compatible) and v2 (enhanced features) with automatic routing</p>
                </div>
                
                <div class="feature">
                    <h3>🧪 Production Ready</h3>
                    <p>Comprehensive tests, Kubernetes configs, CI/CD pipeline, health monitoring</p>
                </div>
            </div>
            
            <h2>📖 Getting Started</h2>
            <div class="endpoint">
                <h3>1. Register a User</h3>
                <pre style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 5px; overflow-x: auto;">
curl -X POST http://127.0.0.1:8000/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "admin", "email": "admin@example.com", "password": "securepass123", "role": "admin"}}'</pre>
            </div>
            
            <div class="endpoint">
                <h3>2. Login & Get Token</h3>
                <pre style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 5px; overflow-x: auto;">
curl -X POST http://127.0.0.1:8000/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "admin", "password": "securepass123"}}'</pre>
            </div>
            
            <div class="endpoint">
                <h3>3. Use Multi-Agent System</h3>
                <pre style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 5px; overflow-x: auto;">
curl -X POST http://127.0.0.1:8000/api/v2/prp/multi-agent \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"task_description": "Build secure API", "agents": ["code", "test", "security"]}}'</pre>
            </div>
            
            <footer style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
                <p>🎉 <strong>PRP AI Assistant System v2.0.0</strong> - Production Ready with Multi-Agent Coordination</p>
                <p>Built with Flask, SQLAlchemy, JWT, Redis, and ❤️</p>
            </footer>
        </div>
    </body>
    </html>
    """

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health_check():
    """Health check endpoint for load balancers"""
    try:
        services = get_backing_services()
        health = services.health_check()
        
        overall_healthy = (
            health['database'] == 'healthy' and 
            (health['redis'] == 'healthy' or health['redis'] == 'not_configured')
        )
        
        health_data = {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'version': '2.0.0',
            'environment': os.environ.get('PRP_ENV', 'development'),
            'checks': {
                'database': health['database'],
                'redis': health['redis']
            },
            'details': health.get('details', {})
        }
        
        status_code = 200 if overall_healthy else 503
        logger.info("health_check_completed", **health_data)
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }), 503

# Legacy endpoints - redirect to versioned API
@app.route('/api/prp/generate', methods=['POST'])
def legacy_generate_prp():
    """Legacy endpoint - redirects to v1"""
    return jsonify({
        'error': 'This endpoint has been deprecated',
        'message': 'Please use /api/v1/prp/generate instead',
        'documentation': '/api/v1/'
    }), 301

@app.route('/api/analytics/dashboard', methods=['GET'])
def legacy_dashboard():
    """Legacy endpoint - redirects to v1"""
    return jsonify({
        'error': 'This endpoint has been deprecated',
        'message': 'Please use /api/v1/analytics/dashboard instead',
        'documentation': '/api/v1/'
    }), 301

@app.route('/api/prp/analyze', methods=['POST'])
def legacy_analyze():
    """Legacy endpoint - redirects to v1"""
    return jsonify({
        'error': 'This endpoint has been deprecated',
        'message': 'Please use /api/v1/prp/analyze instead',
        'documentation': '/api/v1/'
    }), 301

# Import API blueprints
from api_v1 import api_v1
from api_v2 import api_v2

# Register blueprints
app.register_blueprint(api_v1)
app.register_blueprint(api_v2)

# Initialize services if not in import-only mode
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or __name__ == '__main__':
    try:
        # Initialize backing services with config
        services_config = {
            'DATABASE_URL': Config.DATABASE_URL,
            'REDIS_URL': Config.REDIS_URL,
            'DB_POOL_SIZE': 20,
            'DB_MAX_OVERFLOW': 40,
            'REDIS_MAX_CONNECTIONS': 50,
            'REDIS_TIMEOUT': 5
        }
        
        services = init_services(services_config)
        services.init_flask_app(app)
        
        # Store backing services reference for blueprints
        app.config['backing_services'] = services
        app.config['db_engine'] = services.db_engine
        app.config['redis_client'] = services.redis_client
        
        # Create auth tables
        Base.metadata.create_all(services.db_engine)
        
        # Register authentication routes with a session
        with services.db_session_scope() as session:
            register_auth_routes(app, session)
            
    except Exception as e:
        logger.error("Failed to initialize backing services", error=str(e))
        raise

# Process signal handlers for graceful shutdown
import signal
import sys

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("graceful_shutdown_initiated", signal=sig)
    
    # Cleanup backing services
    try:
        from backing_services import cleanup_backing_services
        cleanup_backing_services()
        logger.info("Backing services cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    # Validate configuration before starting
    try:
        Config.validate()
    except ValueError as e:
        logger.error("configuration_validation_failed", error=str(e))
        sys.exit(1)
    
    # Ensure services are initialized
    try:
        get_backing_services()
    except RuntimeError:
        # Services not initialized yet
        services_config = {
            'DATABASE_URL': Config.DATABASE_URL,
            'REDIS_URL': Config.REDIS_URL,
            'DB_POOL_SIZE': 20,
            'DB_MAX_OVERFLOW': 40,
            'REDIS_MAX_CONNECTIONS': 50,
            'REDIS_TIMEOUT': 5
        }
        services = init_services(services_config)
        services.init_flask_app(app)
        app.config['backing_services'] = services
    
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)