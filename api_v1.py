"""
API Version 1 Blueprint
Maintains backward compatibility with existing clients
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth import role_required

# Create blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

@api_v1.route('/')
def index():
    """API v1 index"""
    return jsonify({
        'version': '1.0',
        'status': 'active',
        'endpoints': {
            'generate_prp': '/api/v1/prp/generate',
            'analytics': '/api/v1/analytics/dashboard',
            'analyze_prp': '/api/v1/prp/analyze'
        }
    })

@api_v1.route('/prp/generate', methods=['POST'])
@jwt_required()
def generate_prp_v1():
    """V1 PRP generation endpoint - original implementation"""
    from flask import current_app
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('feature_name'):
        return jsonify({'error': 'feature_name is required'}), 400
    
    # Import here to avoid circular imports
    from PRPs.scripts.prp_generator_stateless import StatelessPRPGenerator
    
    # Get backing services from app context
    db_engine = current_app.config.get('db_engine')
    redis_client = current_app.config.get('redis_client')
    
    generator = StatelessPRPGenerator(db_engine, redis_client)
    result = generator.generate_prp(
        feature_name=data['feature_name'],
        requirements=data.get('requirements', ''),
        complexity=data.get('complexity', 5)
    )
    
    return jsonify(result)

@api_v1.route('/analytics/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_v1():
    """V1 Analytics dashboard"""
    from flask import current_app
    from PRPs.scripts.prp_analytics_stateless import StatelessPRPAnalytics
    
    db_engine = current_app.config.get('db_engine')
    redis_client = current_app.config.get('redis_client')
    
    analytics = StatelessPRPAnalytics(db_engine, redis_client)
    dashboard_data = analytics.get_dashboard_data()
    
    return jsonify(dashboard_data)

@api_v1.route('/prp/analyze', methods=['POST'])
@jwt_required()
@role_required('admin', 'analyst', 'user')
def analyze_prp_v1():
    """V1 PRP analysis endpoint"""
    from flask import current_app
    data = request.get_json()
    
    if not data or not data.get('prp_id'):
        return jsonify({'error': 'prp_id is required'}), 400
    
    from PRPs.scripts.prp_analytics_stateless import StatelessPRPAnalytics
    
    db_engine = current_app.config.get('db_engine')
    redis_client = current_app.config.get('redis_client')
    
    analytics = StatelessPRPAnalytics(db_engine, redis_client)
    result = analytics.analyze_prp_performance(
        prp_id=data['prp_id'],
        success_metrics=data.get('success_metrics', {})
    )
    
    return jsonify(result)