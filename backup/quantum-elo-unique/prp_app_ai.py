#!/usr/bin/env python3
"""
AI-Enhanced Stateless PRP Application - 12-Factor Compliant
Integrates advanced AI capabilities for intelligent assistance
"""

import os
import asyncio
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from sqlalchemy import create_engine
from redis import Redis
from dotenv import load_dotenv
from logging_config import configure_logging, get_logger
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Import AI modules
from PRPs.scripts.prp_ai_learning_engine import AILearningEngine, UserAction
from PRPs.scripts.prp_ai_adaptive_learning import AdaptiveLearningSystem, LearningEvent
from PRPs.scripts.prp_ai_code_generator import IntelligentCodeGenerator
from PRPs.scripts.prp_ai_realtime_assistant import RealTimeAssistant
from PRPs.scripts.prp_ai_debugger import AdvancedDebugger

# Load environment variables
load_dotenv()

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
AI_OPERATIONS = Counter('ai_operations_total', 'Total AI operations', ['operation_type', 'status'])
AI_CONFIDENCE = Histogram('ai_confidence_score', 'AI confidence scores', ['operation_type'])

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Enhanced Configuration with AI settings
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_URL = os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # AI Configuration
    AI_ENABLED = os.environ.get('AI_ENABLED', 'true').lower() == 'true'
    AI_LEARNING_ENABLED = os.environ.get('AI_LEARNING_ENABLED', 'true').lower() == 'true'
    AI_AUTO_SUGGEST = os.environ.get('AI_AUTO_SUGGEST', 'true').lower() == 'true'
    AI_CONFIDENCE_THRESHOLD = float(os.environ.get('AI_CONFIDENCE_THRESHOLD', '0.7'))
    AI_MAX_SUGGESTIONS = int(os.environ.get('AI_MAX_SUGGESTIONS', '10'))
    
    # Original PRP settings
    ANALYTICS_RETENTION_DAYS = int(os.environ.get('ANALYTICS_RETENTION_DAYS', '90'))
    MAX_PRP_COMPLEXITY = int(os.environ.get('MAX_PRP_COMPLEXITY', '10'))
    DEFAULT_SUCCESS_THRESHOLD = float(os.environ.get('DEFAULT_SUCCESS_THRESHOLD', '0.8'))

app.config.from_object(Config)

# Global AI components
ai_components = {
    'learning_engine': None,
    'adaptive_system': None,
    'code_generator': None,
    'realtime_assistant': None,
    'debugger': None
}

def init_ai_components():
    """Initialize AI components"""
    if not Config.AI_ENABLED:
        logger.info("AI components disabled by configuration")
        return
    
    try:
        # Initialize AI Learning Engine
        ai_components['learning_engine'] = AILearningEngine()
        logger.info("AI Learning Engine initialized")
        
        # Initialize Adaptive Learning System
        ai_components['adaptive_system'] = AdaptiveLearningSystem()
        logger.info("Adaptive Learning System initialized")
        
        # Initialize Code Generator
        ai_components['code_generator'] = IntelligentCodeGenerator()
        logger.info("Intelligent Code Generator initialized")
        
        # Initialize Real-time Assistant
        ai_components['realtime_assistant'] = RealTimeAssistant(
            ai_engine=ai_components['learning_engine']
        )
        logger.info("Real-time Assistant initialized")
        
        # Initialize Advanced Debugger
        ai_components['debugger'] = AdvancedDebugger(
            ai_engine=ai_components['learning_engine']
        )
        logger.info("Advanced Debugger initialized")
        
        logger.info("All AI components initialized successfully")
    except Exception as e:
        logger.error("AI component initialization failed", error=str(e))
        # Continue without AI features
        Config.AI_ENABLED = False

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
    
    # Record AI learning event if applicable
    if Config.AI_LEARNING_ENABLED and hasattr(g, 'ai_action'):
        record_ai_learning_event(g.ai_action, response.status_code == 200)
    
    return response

def record_ai_learning_event(action: Dict[str, Any], success: bool):
    """Record AI learning event"""
    if not ai_components['learning_engine']:
        return
    
    try:
        user_action = UserAction(
            action_type='api_call_success' if success else 'api_call_failure',
            factor=action.get('endpoint', 'unknown'),
            context=action.get('context', {}),
            timestamp=datetime.now()
        )
        ai_components['learning_engine'].record_user_action(user_action)
    except Exception as e:
        logger.error("Failed to record AI learning event", error=str(e))

# Health and metrics endpoints
@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health_check():
    """Enhanced health check with AI status"""
    try:
        # Check database
        db_engine.execute("SELECT 1")
        # Check Redis
        redis_client.ping()
        
        # Check AI components
        ai_status = {}
        if Config.AI_ENABLED:
            for name, component in ai_components.items():
                ai_status[name] = 'ok' if component else 'not_initialized'
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '3.0.0-ai',
            'checks': {
                'database': 'ok',
                'redis': 'ok',
                'ai_enabled': Config.AI_ENABLED,
                'ai_components': ai_status
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

# Original PRP endpoints (maintained for compatibility)
@app.route('/api/prp/generate', methods=['POST'])
def generate_prp():
    """AI-enhanced PRP generation endpoint"""
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('feature_name'):
        return jsonify({'error': 'feature_name is required'}), 400
    
    # Import here to avoid circular imports
    from PRPs.scripts.prp_generator_stateless import StatelessPRPGenerator
    
    generator = StatelessPRPGenerator(db_engine, redis_client)
    
    # Get AI recommendations if enabled
    ai_recommendations = {}
    if Config.AI_ENABLED and ai_components['learning_engine']:
        recommendations = ai_components['learning_engine'].get_recommendations(
            factor='prp_generation',
            limit=5
        )
        ai_recommendations = {
            'suggestions': [
                {
                    'title': rec.title,
                    'description': rec.description,
                    'confidence': rec.confidence
                }
                for rec in recommendations
            ]
        }
    
    result = generator.generate_prp(
        feature_name=data['feature_name'],
        requirements=data.get('requirements', ''),
        complexity=data.get('complexity', 5)
    )
    
    # Enhance result with AI insights
    if ai_recommendations:
        result['ai_insights'] = ai_recommendations
    
    # Record for learning
    g.ai_action = {
        'endpoint': 'prp_generate',
        'context': {
            'feature_name': data['feature_name'],
            'complexity': data.get('complexity', 5)
        }
    }
    
    return jsonify(result)

# AI-powered endpoints
@app.route('/api/ai/analyze-code', methods=['POST'])
async def analyze_code():
    """AI-powered code analysis endpoint"""
    if not Config.AI_ENABLED:
        return jsonify({'error': 'AI features are disabled'}), 503
    
    data = request.get_json()
    if not data or not data.get('code'):
        return jsonify({'error': 'code is required'}), 400
    
    try:
        assistant = ai_components['realtime_assistant']
        if not assistant:
            return jsonify({'error': 'Real-time assistant not available'}), 503
        
        # Perform analysis
        review = await assistant.analyze_file(
            file_path=data.get('file_path', 'input.py'),
            content=data['code']
        )
        
        # Track AI operation
        AI_OPERATIONS.labels(operation_type='code_analysis', status='success').inc()
        AI_CONFIDENCE.labels(operation_type='code_analysis').observe(review.overall_score / 100)
        
        # Convert to JSON-serializable format
        result = {
            'overall_score': review.overall_score,
            'issues': [
                {
                    'type': issue.suggestion_type,
                    'title': issue.title,
                    'description': issue.description,
                    'line': issue.line_number,
                    'priority': issue.priority,
                    'confidence': issue.confidence,
                    'fix': issue.fix_snippet
                }
                for issue in review.issues
            ],
            'strengths': review.strengths,
            'metrics': review.metrics
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error("Code analysis failed", error=str(e))
        AI_OPERATIONS.labels(operation_type='code_analysis', status='failure').inc()
        return jsonify({'error': 'Analysis failed', 'details': str(e)}), 500

@app.route('/api/ai/generate-code', methods=['POST'])
def generate_code():
    """AI-powered code generation endpoint"""
    if not Config.AI_ENABLED:
        return jsonify({'error': 'AI features are disabled'}), 503
    
    data = request.get_json()
    if not data or not data.get('request_type'):
        return jsonify({'error': 'request_type is required'}), 400
    
    try:
        generator = ai_components['code_generator']
        if not generator:
            return jsonify({'error': 'Code generator not available'}), 503
        
        # Generate code
        result = generator.generate_code(
            request_type=data['request_type'],
            language=data.get('language', 'python'),
            context=data.get('context', {}),
            requirements=data.get('requirements', {})
        )
        
        # Track AI operation
        AI_OPERATIONS.labels(operation_type='code_generation', status='success').inc()
        AI_CONFIDENCE.labels(operation_type='code_generation').observe(result.confidence)
        
        # Convert to JSON-serializable format
        response = {
            'code': result.code,
            'language': result.language,
            'confidence': result.confidence,
            'suggestions': result.suggestions,
            'dependencies': result.dependencies
        }
        
        if result.test_code:
            response['test_code'] = result.test_code
        
        return jsonify(response)
    except Exception as e:
        logger.error("Code generation failed", error=str(e))
        AI_OPERATIONS.labels(operation_type='code_generation', status='failure').inc()
        return jsonify({'error': 'Generation failed', 'details': str(e)}), 500

@app.route('/api/ai/debug-error', methods=['POST'])
async def debug_error():
    """AI-powered debugging endpoint"""
    if not Config.AI_ENABLED:
        return jsonify({'error': 'AI features are disabled'}), 503
    
    data = request.get_json()
    if not data or not data.get('error'):
        return jsonify({'error': 'error information is required'}), 400
    
    try:
        debugger = ai_components['debugger']
        if not debugger:
            return jsonify({'error': 'Debugger not available'}), 503
        
        # Perform debugging
        report = await debugger.debug_error(
            error=data['error'],
            context=data.get('context', {})
        )
        
        # Track AI operation
        AI_OPERATIONS.labels(operation_type='debugging', status='success').inc()
        
        # Convert to JSON-serializable format
        result = {
            'error_context': {
                'type': report.error_context.error_type,
                'message': report.error_context.error_message,
                'file': report.error_context.file_path,
                'line': report.error_context.line_number
            },
            'root_causes': [
                {
                    'type': cause.cause_type,
                    'description': cause.description,
                    'confidence': cause.confidence,
                    'impact': cause.impact_scope
                }
                for cause in report.root_causes
            ],
            'solutions': [
                {
                    'title': solution.title,
                    'description': solution.description,
                    'steps': solution.implementation_steps,
                    'confidence': solution.confidence,
                    'effort': solution.estimated_effort,
                    'risk': solution.risk_level
                }
                for solution in report.solutions
            ],
            'prevention_tips': report.prevention_tips
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error("Debugging failed", error=str(e))
        AI_OPERATIONS.labels(operation_type='debugging', status='failure').inc()
        return jsonify({'error': 'Debugging failed', 'details': str(e)}), 500

@app.route('/api/ai/get-recommendations', methods=['GET'])
def get_recommendations():
    """Get AI recommendations for current context"""
    if not Config.AI_ENABLED:
        return jsonify({'error': 'AI features are disabled'}), 503
    
    factor = request.args.get('factor', 'general')
    
    try:
        learning_engine = ai_components['learning_engine']
        if not learning_engine:
            return jsonify({'error': 'Learning engine not available'}), 503
        
        # Get recommendations
        recommendations = learning_engine.get_recommendations(
            factor=factor,
            limit=Config.AI_MAX_SUGGESTIONS
        )
        
        # Get adaptive recommendations
        adaptive_recs = []
        if ai_components['adaptive_system']:
            context = {
                'time_of_day': datetime.now().hour,
                'day_of_week': datetime.now().weekday()
            }
            adaptive_recs = ai_components['adaptive_system'].get_adaptive_recommendations(
                factor=factor,
                context=context
            )
        
        result = {
            'recommendations': [
                {
                    'id': rec.recommendation_id,
                    'title': rec.title,
                    'description': rec.description,
                    'rationale': rec.rationale,
                    'confidence': rec.confidence,
                    'priority': rec.priority,
                    'auto_fixable': rec.auto_fixable
                }
                for rec in recommendations
            ],
            'adaptive_recommendations': adaptive_recs[:5]  # Top 5
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error("Failed to get recommendations", error=str(e))
        return jsonify({'error': 'Failed to get recommendations', 'details': str(e)}), 500

@app.route('/api/ai/provide-feedback', methods=['POST'])
def provide_feedback():
    """Provide feedback on AI recommendations"""
    if not Config.AI_ENABLED or not Config.AI_LEARNING_ENABLED:
        return jsonify({'error': 'AI learning is disabled'}), 503
    
    data = request.get_json()
    if not data or not data.get('recommendation_id'):
        return jsonify({'error': 'recommendation_id is required'}), 400
    
    try:
        learning_engine = ai_components['learning_engine']
        if not learning_engine:
            return jsonify({'error': 'Learning engine not available'}), 503
        
        # Record feedback
        learning_engine.provide_feedback(
            recommendation_id=data['recommendation_id'],
            feedback=data.get('feedback', 'neutral'),
            rating=data.get('rating', 3.0)
        )
        
        return jsonify({'status': 'feedback recorded'})
    except Exception as e:
        logger.error("Failed to record feedback", error=str(e))
        return jsonify({'error': 'Failed to record feedback', 'details': str(e)}), 500

@app.route('/api/ai/learning-progress', methods=['GET'])
def get_learning_progress():
    """Get AI learning progress and statistics"""
    if not Config.AI_ENABLED:
        return jsonify({'error': 'AI features are disabled'}), 503
    
    try:
        progress = {}
        
        # Get learning engine progress
        if ai_components['learning_engine']:
            progress['learning_engine'] = ai_components['learning_engine'].analyze_learning_progress()
        
        # Get adaptive system metrics
        if ai_components['adaptive_system']:
            # Simple metrics for now
            progress['adaptive_system'] = {
                'total_events': len(ai_components['adaptive_system'].learning_events),
                'pattern_clusters': len(ai_components['adaptive_system'].pattern_clusters),
                'models_trained': len(ai_components['adaptive_system'].models)
            }
        
        return jsonify(progress)
    except Exception as e:
        logger.error("Failed to get learning progress", error=str(e))
        return jsonify({'error': 'Failed to get progress', 'details': str(e)}), 500

@app.route('/api/ai/config', methods=['GET'])
def get_ai_config():
    """Get current AI configuration"""
    config = {
        'enabled': Config.AI_ENABLED,
        'learning_enabled': Config.AI_LEARNING_ENABLED,
        'auto_suggest': Config.AI_AUTO_SUGGEST,
        'confidence_threshold': Config.AI_CONFIDENCE_THRESHOLD,
        'max_suggestions': Config.AI_MAX_SUGGESTIONS,
        'components': {
            name: 'initialized' if component else 'not_initialized'
            for name, component in ai_components.items()
        }
    }
    return jsonify(config)

# WebSocket support for real-time assistance (requires additional setup)
@app.route('/api/ai/realtime/start', methods=['POST'])
async def start_realtime_monitoring():
    """Start real-time code monitoring"""
    if not Config.AI_ENABLED or not Config.AI_AUTO_SUGGEST:
        return jsonify({'error': 'Real-time assistance is disabled'}), 503
    
    data = request.get_json()
    paths = data.get('paths', [])
    
    try:
        assistant = ai_components['realtime_assistant']
        if not assistant:
            return jsonify({'error': 'Real-time assistant not available'}), 503
        
        # Start monitoring
        await assistant.start_monitoring(paths)
        
        return jsonify({
            'status': 'monitoring started',
            'paths': paths
        })
    except Exception as e:
        logger.error("Failed to start monitoring", error=str(e))
        return jsonify({'error': 'Failed to start monitoring', 'details': str(e)}), 500

# Process signal handlers for graceful shutdown
import signal
import sys

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("graceful_shutdown_initiated", signal=sig)
    
    # Stop real-time monitoring
    if ai_components['realtime_assistant']:
        asyncio.run(ai_components['realtime_assistant'].stop_monitoring())
    
    # Save AI learning data
    if ai_components['learning_engine']:
        ai_components['learning_engine']._save_learning_data()
    
    if ai_components['adaptive_system']:
        ai_components['adaptive_system']._save_learning_data()
    
    # Close database connections
    if 'db_engine' in globals():
        db_engine.dispose()
    # Close Redis connections
    if 'redis_client' in globals():
        redis_client.close()
    
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error("Internal server error", error=str(error))
    return jsonify({'error': 'Internal server error'}), 500

# Main entry point
if __name__ == '__main__':
    # Initialize services
    init_backing_services()
    init_ai_components()
    
    # Run the application
    port = int(os.environ.get('PORT', 8000))
    
    # Note: In production, use a proper ASGI server like uvicorn for async support
    logger.info(f"Starting AI-Enhanced PRP Application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')