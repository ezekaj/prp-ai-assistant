"""
Request/Response validation schemas using Marshmallow
Ensures data integrity and prevents injection attacks
"""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from typing import Dict, Any


class PRPGenerateSchema(Schema):
    """Schema for PRP generation requests"""
    feature_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=200),
            validate.Regexp(r'^[a-zA-Z0-9\s\-_]+$', error='Invalid characters in feature name')
        ],
        error_messages={'required': 'Feature name is required'}
    )
    
    requirements = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=5000),
        error_messages={'required': 'Requirements are required'}
    )
    
    complexity = fields.Int(
        validate=validate.Range(min=1, max=10),
        missing=5,
        error_messages={'invalid': 'Complexity must be between 1 and 10'}
    )
    
    project_context = fields.Str(
        validate=validate.Length(max=2000),
        missing=''
    )
    
    @validates_schema
    def validate_requirements(self, data, **kwargs):
        """Additional validation for requirements"""
        if 'requirements' in data:
            # Check for potential injection patterns
            dangerous_patterns = ['<script', 'javascript:', 'onclick', 'onerror']
            requirements_lower = data['requirements'].lower()
            
            for pattern in dangerous_patterns:
                if pattern in requirements_lower:
                    raise ValidationError(f'Invalid content detected: {pattern}')


class PRPAnalyzeSchema(Schema):
    """Schema for PRP analysis requests"""
    prp_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={'required': 'PRP ID is required'}
    )
    
    actual_time = fields.Float(
        required=True,
        validate=validate.Range(min=0.1, max=10000),
        error_messages={'required': 'Actual time is required'}
    )
    
    success = fields.Bool(
        required=True,
        error_messages={'required': 'Success status is required'}
    )
    
    issues_encountered = fields.List(
        fields.Str(validate=validate.Length(max=500)),
        validate=validate.Length(max=20),
        missing=[]
    )
    
    patterns_used = fields.List(
        fields.Str(validate=validate.Length(max=100)),
        validate=validate.Length(max=50),
        missing=[]
    )


class UserLoginSchema(Schema):
    """Schema for user login"""
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=80),
            validate.Regexp(r'^[a-zA-Z0-9_-]+$', error='Invalid username format')
        ]
    )
    
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128),
        load_only=True
    )


class UserRegisterSchema(Schema):
    """Schema for user registration"""
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=80),
            validate.Regexp(r'^[a-zA-Z0-9_-]+$', error='Invalid username format')
        ]
    )
    
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120)
    )
    
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=128),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                error='Password must contain uppercase, lowercase, number and special character'
            )
        ],
        load_only=True
    )
    
    role = fields.Str(
        validate=validate.OneOf(['user', 'admin', 'developer']),
        missing='user'
    )


class PaginationSchema(Schema):
    """Schema for pagination parameters"""
    page = fields.Int(
        validate=validate.Range(min=1),
        missing=1
    )
    
    per_page = fields.Int(
        validate=validate.Range(min=1, max=100),
        missing=20
    )
    
    sort_by = fields.Str(
        validate=validate.OneOf(['created_at', 'updated_at', 'complexity', 'success_rate']),
        missing='created_at'
    )
    
    order = fields.Str(
        validate=validate.OneOf(['asc', 'desc']),
        missing='desc'
    )


class DashboardQuerySchema(Schema):
    """Schema for dashboard queries"""
    start_date = fields.DateTime(
        format='%Y-%m-%d',
        missing=None
    )
    
    end_date = fields.DateTime(
        format='%Y-%m-%d',
        missing=None
    )
    
    include_analytics = fields.Bool(missing=True)
    include_patterns = fields.Bool(missing=True)
    include_metrics = fields.Bool(missing=True)
    
    @validates_schema
    def validate_dates(self, data, **kwargs):
        """Ensure end_date is after start_date"""
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] < data['start_date']:
                raise ValidationError('End date must be after start date')


class ErrorResponseSchema(Schema):
    """Schema for error responses"""
    error = fields.Str(required=True)
    code = fields.Str(required=True)
    details = fields.Dict(missing={})
    timestamp = fields.DateTime(dump_only=True)


class SuccessResponseSchema(Schema):
    """Schema for success responses"""
    message = fields.Str(required=True)
    data = fields.Dict(missing={})
    timestamp = fields.DateTime(dump_only=True)


def validate_request(schema_class: Schema):
    """Decorator to validate request data"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            schema = schema_class()
            try:
                # Get JSON data or query params
                if hasattr(request, 'json') and request.json:
                    data = schema.load(request.json)
                else:
                    data = schema.load(request.args)
                
                # Add validated data to kwargs
                kwargs['validated_data'] = data
                return f(*args, **kwargs)
                
            except ValidationError as err:
                return jsonify({
                    'error': 'Validation failed',
                    'code': 'validation_error',
                    'details': err.messages
                }), 400
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


# Export commonly used schemas
__all__ = [
    'PRPGenerateSchema',
    'PRPAnalyzeSchema',
    'UserLoginSchema',
    'UserRegisterSchema',
    'PaginationSchema',
    'DashboardQuerySchema',
    'ErrorResponseSchema',
    'SuccessResponseSchema',
    'validate_request'
]