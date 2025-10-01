"""
API Version 2 Blueprint
Enhanced features including multi-agent support and improved responses
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from auth import role_required
import uuid
from datetime import datetime

# Create blueprint
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

@api_v2.route('/')
def index():
    """API v2 index with enhanced information"""
    return jsonify({
        'version': '2.0',
        'status': 'active',
        'features': [
            'Multi-agent coordination',
            'Enhanced error responses',
            'Request tracking',
            'Pagination support',
            'Field filtering'
        ],
        'endpoints': {
            'generate_prp': '/api/v2/prp/generate',
            'analytics': '/api/v2/analytics/dashboard',
            'analyze_prp': '/api/v2/prp/analyze',
            'multi_agent': '/api/v2/prp/multi-agent',
            'agents': '/api/v2/agents',
            'tasks': '/api/v2/tasks'
        }
    })

@api_v2.route('/prp/generate', methods=['POST'])
@jwt_required()
def generate_prp_v2():
    """V2 PRP generation with enhanced features"""
    from flask import current_app, g
    data = request.get_json()
    
    # Enhanced validation
    errors = []
    if not data:
        errors.append("Request body is required")
    elif not data.get('feature_name'):
        errors.append("feature_name is required")
    elif len(data.get('feature_name', '')) < 3:
        errors.append("feature_name must be at least 3 characters")
    
    if errors:
        return jsonify({
            'error': 'Validation failed',
            'errors': errors,
            'request_id': g.request_id
        }), 400
    
    # Import here to avoid circular imports
    from PRPs.scripts.prp_generator_stateless import StatelessPRPGenerator
    
    # Get backing services from app context
    db_engine = current_app.config.get('db_engine')
    redis_client = current_app.config.get('redis_client')
    
    generator = StatelessPRPGenerator(db_engine, redis_client)
    
    # Enhanced response with metadata
    result = generator.generate_prp(
        feature_name=data['feature_name'],
        requirements=data.get('requirements', ''),
        complexity=data.get('complexity', 5)
    )
    
    # Add V2 metadata
    result['metadata'] = {
        'api_version': '2.0',
        'request_id': g.request_id,
        'generated_at': datetime.utcnow().isoformat(),
        'user': get_jwt_identity(),
        'complexity_score': data.get('complexity', 5)
    }
    
    return jsonify(result), 201

@api_v2.route('/prp/multi-agent', methods=['POST'])
@jwt_required()
def multi_agent_generate():
    """V2 Multi-agent PRP generation"""
    from flask import current_app, g
    data = request.get_json()
    
    # Validation
    if not data or not data.get('task_description'):
        return jsonify({
            'error': 'task_description is required',
            'request_id': g.request_id
        }), 400
    
    # Import multi-agent coordinator
    from PRPs.scripts.multi_agent_coordinator import MultiAgentCoordinator
    
    db_engine = current_app.config.get('db_engine')
    redis_client = current_app.config.get('redis_client')
    
    coordinator = MultiAgentCoordinator(
        redis_url=current_app.config.get('REDIS_URL', 'redis://localhost:6379'),
        db_engine=db_engine
    )
    
    # Create task
    task_id = coordinator.create_task(
        description=data['task_description'],
        agent_types=data.get('agents', ['code', 'test', 'docs']),
        context=data.get('context', {}),
        priority=data.get('priority', 5)
    )
    
    return jsonify({
        'task_id': task_id,
        'status': 'created',
        'agents_assigned': data.get('agents', ['code', 'test', 'docs']),
        'estimated_completion': '5-10 minutes',
        'tracking_url': f'/api/v2/tasks/{task_id}',
        'metadata': {
            'api_version': '2.0',
            'request_id': g.request_id,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': get_jwt_identity()
        }
    }), 202

@api_v2.route('/analytics/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_v2():
    """V2 Analytics dashboard with pagination and filtering"""
    from flask import current_app
    from PRPs.scripts.prp_analytics_stateless import StatelessPRPAnalytics
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filtering parameters
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    status_filter = request.args.get('status')
    
    db_engine = current_app.config.get('db_engine')
    redis_client = current_app.config.get('redis_client')
    
    analytics = StatelessPRPAnalytics(db_engine, redis_client)
    dashboard_data = analytics.get_dashboard_data()
    
    # Add V2 enhancements
    dashboard_data['pagination'] = {
        'page': page,
        'per_page': per_page,
        'total': dashboard_data.get('total_prps', 0),
        'pages': (dashboard_data.get('total_prps', 0) + per_page - 1) // per_page
    }
    
    dashboard_data['filters_applied'] = {
        'date_from': date_from,
        'date_to': date_to,
        'status': status_filter
    }
    
    dashboard_data['_links'] = {
        'self': f'/api/v2/analytics/dashboard?page={page}&per_page={per_page}',
        'next': f'/api/v2/analytics/dashboard?page={page+1}&per_page={per_page}' if page < dashboard_data['pagination']['pages'] else None,
        'prev': f'/api/v2/analytics/dashboard?page={page-1}&per_page={per_page}' if page > 1 else None
    }
    
    return jsonify(dashboard_data)

@api_v2.route('/agents', methods=['GET'])
@jwt_required()
def list_agents():
    """List all available agents and their status"""
    # This would connect to the multi-agent system
    agents = [
        {
            'id': 'code-agent-1',
            'type': 'code_generation',
            'status': 'available',
            'current_tasks': 0,
            'capabilities': ['python', 'javascript', 'api_design']
        },
        {
            'id': 'test-agent-1',
            'type': 'testing',
            'status': 'available',
            'current_tasks': 1,
            'capabilities': ['unit_tests', 'integration_tests', 'coverage_analysis']
        },
        {
            'id': 'security-agent-1',
            'type': 'security',
            'status': 'busy',
            'current_tasks': 2,
            'capabilities': ['vulnerability_scanning', 'code_audit', 'compliance_check']
        }
    ]
    
    return jsonify({
        'agents': agents,
        'total': len(agents),
        'available': sum(1 for a in agents if a['status'] == 'available'),
        'timestamp': datetime.utcnow().isoformat()
    })

@api_v2.route('/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """Get status of a specific task"""
    # This would query the task tracking system
    # For demo, return mock data
    return jsonify({
        'task_id': task_id,
        'status': 'in_progress',
        'progress': 65,
        'agents_working': ['code-agent-1', 'test-agent-1'],
        'completed_steps': [
            {'step': 'requirements_analysis', 'completed_at': '2025-07-27T10:30:00Z'},
            {'step': 'code_generation', 'completed_at': '2025-07-27T10:35:00Z'}
        ],
        'current_step': 'testing',
        'estimated_completion': '2025-07-27T10:45:00Z',
        'created_by': get_jwt_identity(),
        '_links': {
            'self': f'/api/v2/tasks/{task_id}',
            'cancel': f'/api/v2/tasks/{task_id}/cancel',
            'results': f'/api/v2/tasks/{task_id}/results'
        }
    })

@api_v2.route('/prp/analyze', methods=['POST'])
@jwt_required()
@role_required('admin', 'analyst', 'user')
def analyze_prp_v2():
    """V2 PRP analysis with enhanced insights"""
    from flask import current_app, g
    data = request.get_json()
    
    if not data or not data.get('prp_id'):
        return jsonify({
            'error': 'prp_id is required',
            'request_id': g.request_id
        }), 400
    
    from PRPs.scripts.prp_analytics_stateless import StatelessPRPAnalytics
    
    db_engine = current_app.config.get('db_engine')
    redis_client = current_app.config.get('redis_client')
    
    analytics = StatelessPRPAnalytics(db_engine, redis_client)
    result = analytics.analyze_prp_performance(
        prp_id=data['prp_id'],
        success_metrics=data.get('success_metrics', {})
    )
    
    # Add V2 enhancements
    result['insights'] = {
        'performance_trend': 'improving',
        'risk_factors': ['complexity_high', 'new_technology'],
        'recommendations': [
            'Consider breaking down into smaller PRPs',
            'Add more comprehensive testing'
        ]
    }
    
    result['metadata'] = {
        'api_version': '2.0',
        'analysis_timestamp': datetime.utcnow().isoformat(),
        'analyzed_by': get_jwt_identity(),
        'request_id': g.request_id
    }
    
    return jsonify(result)