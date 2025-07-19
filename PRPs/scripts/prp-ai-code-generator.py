#!/usr/bin/env python3
"""
PRP-12Factor AI-Powered Intelligent Code Generation
Context-aware code generation with learning capabilities
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from collections import defaultdict
import difflib
import autopep8
import black

logger = logging.getLogger(__name__)

@dataclass
class CodeTemplate:
    """Template for code generation"""
    template_id: str
    language: str
    pattern_type: str  # 'function', 'class', 'module', 'test', 'config'
    template_code: str
    placeholders: Dict[str, str]
    context_requirements: Dict[str, Any]
    quality_score: float
    usage_count: int = 0

@dataclass
class GeneratedCode:
    """Generated code with metadata"""
    code: str
    language: str
    context: Dict[str, Any]
    confidence: float
    suggestions: List[str]
    dependencies: List[str]
    test_code: Optional[str] = None

class IntelligentCodeGenerator:
    """AI-powered code generator with context awareness"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.templates_file = self.project_root / "PRPs" / "templates" / "code-templates.json"
        self.learning_file = self.project_root / "PRPs" / "analytics" / "code-gen-learning.json"
        
        # Create directories
        self.templates_file.parent.mkdir(parents=True, exist_ok=True)
        self.learning_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load templates and learning data
        self.templates: Dict[str, CodeTemplate] = self._load_templates()
        self.style_patterns: Dict[str, Dict[str, Any]] = self._load_style_patterns()
        self.import_patterns: Dict[str, List[str]] = self._load_import_patterns()
        
        # Language-specific generators
        self.generators = {
            'python': self._generate_python_code,
            'javascript': self._generate_javascript_code,
            'typescript': self._generate_typescript_code,
            'go': self._generate_go_code,
            'java': self._generate_java_code,
        }
        
        # Code quality validators
        self.validators = {
            'python': self._validate_python_code,
            'javascript': self._validate_javascript_code,
            'typescript': self._validate_typescript_code,
            'go': self._validate_go_code,
            'java': self._validate_java_code,
        }
        
        logger.info(f"Intelligent Code Generator initialized with {len(self.templates)} templates")
    
    def _load_templates(self) -> Dict[str, CodeTemplate]:
        """Load code templates from storage"""
        if not self.templates_file.exists():
            return self._create_default_templates()
        
        try:
            with open(self.templates_file, 'r') as f:
                data = json.load(f)
            
            templates = {}
            for template_data in data.get('templates', []):
                template = CodeTemplate(
                    template_id=template_data['template_id'],
                    language=template_data['language'],
                    pattern_type=template_data['pattern_type'],
                    template_code=template_data['template_code'],
                    placeholders=template_data['placeholders'],
                    context_requirements=template_data['context_requirements'],
                    quality_score=template_data.get('quality_score', 0.8),
                    usage_count=template_data.get('usage_count', 0)
                )
                templates[template.template_id] = template
            
            return templates
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            return self._create_default_templates()
    
    def _create_default_templates(self) -> Dict[str, CodeTemplate]:
        """Create default code templates"""
        templates = {
            # Python templates
            'python_function': CodeTemplate(
                template_id='python_function',
                language='python',
                pattern_type='function',
                template_code='''def {{function_name}}({{parameters}}) -> {{return_type}}:
    """{{docstring}}"""
    {{body}}
    return {{return_value}}''',
                placeholders={
                    'function_name': 'process_data',
                    'parameters': 'data: Dict[str, Any]',
                    'return_type': 'Dict[str, Any]',
                    'docstring': 'Process the input data',
                    'body': '# Implementation here',
                    'return_value': 'processed_data'
                },
                context_requirements={'has_type_hints': True, 'has_docstring': True},
                quality_score=0.9
            ),
            
            'python_class': CodeTemplate(
                template_id='python_class',
                language='python',
                pattern_type='class',
                template_code='''class {{class_name}}:
    """{{class_docstring}}"""
    
    def __init__(self{{init_params}}):
        """Initialize {{class_name}}"""
        {{init_body}}
    
    {{methods}}''',
                placeholders={
                    'class_name': 'DataProcessor',
                    'class_docstring': 'Process data with various transformations',
                    'init_params': ', param1: str, param2: int',
                    'init_body': 'self.param1 = param1\n        self.param2 = param2',
                    'methods': 'def process(self, data: Any) -> Any:\n        """Process the data"""\n        return data'
                },
                context_requirements={'style': 'pep8', 'has_docstring': True},
                quality_score=0.9
            ),
            
            'python_test': CodeTemplate(
                template_id='python_test',
                language='python',
                pattern_type='test',
                template_code='''import pytest
from {{module_path}} import {{class_or_function}}

class Test{{test_class_name}}:
    """Test suite for {{class_or_function}}"""
    
    def test_{{test_case}}(self):
        """Test {{test_description}}"""
        # Arrange
        {{arrange_code}}
        
        # Act
        {{act_code}}
        
        # Assert
        {{assert_code}}''',
                placeholders={
                    'module_path': 'src.module',
                    'class_or_function': 'process_data',
                    'test_class_name': 'ProcessData',
                    'test_case': 'successful_processing',
                    'test_description': 'successful data processing',
                    'arrange_code': 'data = {"key": "value"}',
                    'act_code': 'result = process_data(data)',
                    'assert_code': 'assert result["key"] == "processed_value"'
                },
                context_requirements={'framework': 'pytest'},
                quality_score=0.85
            ),
            
            # JavaScript templates
            'javascript_function': CodeTemplate(
                template_id='javascript_function',
                language='javascript',
                pattern_type='function',
                template_code='''/**
 * {{jsdoc_description}}
 * @param {{jsdoc_params}}
 * @returns {{jsdoc_returns}}
 */
{{async_keyword}}function {{function_name}}({{parameters}}) {
    {{body}}
    return {{return_value}};
}''',
                placeholders={
                    'jsdoc_description': 'Process the input data',
                    'jsdoc_params': '{Object} data - The input data',
                    'jsdoc_returns': '{Object} The processed data',
                    'async_keyword': '',
                    'function_name': 'processData',
                    'parameters': 'data',
                    'body': '// Implementation here',
                    'return_value': 'processedData'
                },
                context_requirements={'has_jsdoc': True},
                quality_score=0.85
            ),
            
            'javascript_class': CodeTemplate(
                template_id='javascript_class',
                language='javascript',
                pattern_type='class',
                template_code='''/**
 * {{class_description}}
 */
class {{class_name}} {
    /**
     * Create a {{class_name}}
     * {{constructor_params}}
     */
    constructor({{parameters}}) {
        {{constructor_body}}
    }
    
    {{methods}}
}''',
                placeholders={
                    'class_description': 'Handles data processing operations',
                    'class_name': 'DataProcessor',
                    'constructor_params': '@param {string} name - The processor name',
                    'parameters': 'name',
                    'constructor_body': 'this.name = name;',
                    'methods': '/**\n     * Process the data\n     * @param {Object} data\n     * @returns {Object}\n     */\n    process(data) {\n        return data;\n    }'
                },
                context_requirements={'es_version': 'ES6'},
                quality_score=0.85
            ),
        }
        
        # Save default templates
        self._save_templates(templates)
        return templates
    
    def _save_templates(self, templates: Dict[str, CodeTemplate]):
        """Save templates to storage"""
        try:
            data = {
                'templates': [
                    {
                        'template_id': template.template_id,
                        'language': template.language,
                        'pattern_type': template.pattern_type,
                        'template_code': template.template_code,
                        'placeholders': template.placeholders,
                        'context_requirements': template.context_requirements,
                        'quality_score': template.quality_score,
                        'usage_count': template.usage_count
                    }
                    for template in templates.values()
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.templates_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving templates: {e}")
    
    def _load_style_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load learned coding style patterns"""
        if not self.learning_file.exists():
            return {}
        
        try:
            with open(self.learning_file, 'r') as f:
                data = json.load(f)
            return data.get('style_patterns', {})
        except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
            import logging
            logging.warning(f"Failed to load style patterns from {self.learning_file}: {e}")
            return {}
    
    def _load_import_patterns(self) -> Dict[str, List[str]]:
        """Load learned import patterns"""
        if not self.learning_file.exists():
            return {}
        
        try:
            with open(self.learning_file, 'r') as f:
                data = json.load(f)
            return data.get('import_patterns', {})
        except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
            import logging
            logging.warning(f"Failed to load import patterns from {self.learning_file}: {e}")
            return {}
    
    def generate_code(self,
                     request_type: str,
                     language: str,
                     context: Dict[str, Any],
                     requirements: Optional[Dict[str, Any]] = None) -> GeneratedCode:
        """Generate code based on request type and context"""
        
        # Validate language support
        if language not in self.generators:
            return GeneratedCode(
                code="# Language not supported",
                language=language,
                context=context,
                confidence=0.0,
                suggestions=[f"Supported languages: {', '.join(self.generators.keys())}"],
                dependencies=[]
            )
        
        # Analyze context and determine best approach
        analysis = self._analyze_context(context, language)
        
        # Select appropriate template or generate custom code
        if request_type in ['function', 'class', 'module', 'test']:
            template_id = f"{language}_{request_type}"
            if template_id in self.templates:
                return self._generate_from_template(
                    self.templates[template_id],
                    context,
                    requirements or {}
                )
        
        # Use language-specific generator
        generator = self.generators[language]
        return generator(request_type, context, requirements or {})
    
    def _analyze_context(self, context: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Analyze context to understand code requirements"""
        analysis = {
            'existing_style': self._detect_coding_style(context.get('existing_code', ''), language),
            'dependencies': self._detect_dependencies(context.get('file_path', ''), language),
            'patterns': self._detect_patterns(context.get('existing_code', ''), language),
            'naming_convention': self._detect_naming_convention(context.get('existing_code', ''), language),
        }
        
        # Add project-specific patterns
        if context.get('project_path'):
            analysis['project_patterns'] = self._analyze_project_patterns(
                context['project_path'],
                language
            )
        
        return analysis
    
    def _generate_from_template(self,
                               template: CodeTemplate,
                               context: Dict[str, Any],
                               requirements: Dict[str, Any]) -> GeneratedCode:
        """Generate code from a template"""
        # Prepare placeholder values
        placeholders = template.placeholders.copy()
        
        # Override with context-specific values
        for key, value in context.items():
            if key in placeholders:
                placeholders[key] = value
        
        # Apply requirements
        for key, value in requirements.items():
            if key in placeholders:
                placeholders[key] = value
        
        # Generate code
        code = template.template_code
        for placeholder, value in placeholders.items():
            code = code.replace(f"{{{{{placeholder}}}}}", str(value))
        
        # Format code based on language
        if template.language == 'python':
            try:
                code = black.format_str(code, mode=black.Mode())
            except (black.InvalidInput, black.BracketMatchError) as e:
                import logging
                logging.debug(f"Black formatting failed, falling back to autopep8: {e}")
                try:
                    code = autopep8.fix_code(code)
                except (ValueError, TypeError) as e2:
                    logging.debug(f"Autopep8 formatting also failed, keeping original code: {e2}")
                    pass
        
        # Extract dependencies
        dependencies = self._extract_dependencies(code, template.language)
        
        # Generate test code if requested
        test_code = None
        if requirements.get('generate_tests', False):
            test_code = self._generate_test_code(code, template.language, context)
        
        # Update template usage
        template.usage_count += 1
        self._save_templates(self.templates)
        
        return GeneratedCode(
            code=code,
            language=template.language,
            context=context,
            confidence=template.quality_score,
            suggestions=self._generate_suggestions(code, template.language, context),
            dependencies=dependencies,
            test_code=test_code
        )
    
    def _generate_python_code(self,
                             request_type: str,
                             context: Dict[str, Any],
                             requirements: Dict[str, Any]) -> GeneratedCode:
        """Generate Python code"""
        code_parts = []
        dependencies = []
        
        # Add imports based on context
        if context.get('needs_typing', True):
            code_parts.append("from typing import Dict, List, Any, Optional")
            dependencies.append("typing")
        
        if context.get('needs_async', False):
            code_parts.append("import asyncio")
            dependencies.append("asyncio")
        
        # Generate based on request type
        if request_type == 'api_endpoint':
            code = self._generate_python_api_endpoint(context, requirements)
        elif request_type == 'data_processor':
            code = self._generate_python_data_processor(context, requirements)
        elif request_type == 'service_class':
            code = self._generate_python_service_class(context, requirements)
        else:
            code = self._generate_generic_python_code(context, requirements)
        
        # Combine parts
        if code_parts:
            code = "\n".join(code_parts) + "\n\n" + code
        
        # Format code
        try:
            code = black.format_str(code, mode=black.Mode())
        except (black.InvalidInput, black.BracketMatchError) as e:
            import logging
            logging.debug(f"Black formatting failed for generated code: {e}")
            pass
        
        return GeneratedCode(
            code=code,
            language='python',
            context=context,
            confidence=0.85,
            suggestions=self._generate_suggestions(code, 'python', context),
            dependencies=dependencies
        )
    
    def _generate_python_api_endpoint(self, context: Dict[str, Any], requirements: Dict[str, Any]) -> str:
        """Generate Python API endpoint code"""
        framework = context.get('framework', 'flask')
        endpoint_name = context.get('endpoint_name', 'process')
        method = context.get('method', 'POST')
        
        if framework == 'flask':
            code = f'''from flask import request, jsonify, Blueprint
from functools import wraps
import logging

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

def validate_request(f):
    """Validate incoming request data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({{"error": "Content-Type must be application/json"}}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({{"error": "Request body cannot be empty"}}), 400
        
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/{endpoint_name}', methods=['{method}'])
@validate_request
def {endpoint_name}():
    """Process {endpoint_name} request"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = {requirements.get('required_fields', ['data'])}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            return jsonify({{
                "error": f"Missing required fields: {{', '.join(missing_fields)}}"
            }}), 400
        
        # Process the data
        result = {{"status": "success", "data": data}}
        
        logger.info(f"{endpoint_name} processed successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in {endpoint_name}: {{str(e)}}")
        return jsonify({{"error": "Internal server error"}}), 500'''
        
        elif framework == 'fastapi':
            code = f'''from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class {endpoint_name.capitalize()}Request(BaseModel):
    """Request model for {endpoint_name}"""
    data: Dict[str, Any] = Field(..., description="Input data")
    
    class Config:
        schema_extra = {{
            "example": {{
                "data": {{"key": "value"}}
            }}
        }}

class {endpoint_name.capitalize()}Response(BaseModel):
    """Response model for {endpoint_name}"""
    status: str
    data: Dict[str, Any]
    message: Optional[str] = None

@router.post("/{endpoint_name}", response_model={endpoint_name.capitalize()}Response)
async def {endpoint_name}(request: {endpoint_name.capitalize()}Request):
    """
    Process {endpoint_name} request
    
    - **data**: Input data to process
    """
    try:
        # Process the data
        processed_data = request.data
        
        logger.info(f"{endpoint_name} processed successfully")
        return {endpoint_name.capitalize()}Response(
            status="success",
            data=processed_data,
            message="{endpoint_name} completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in {endpoint_name}: {{str(e)}}")
        raise HTTPException(status_code=500, detail=str(e))'''
        
        return code
    
    def _generate_python_data_processor(self, context: Dict[str, Any], requirements: Dict[str, Any]) -> str:
        """Generate Python data processor code"""
        processor_name = context.get('processor_name', 'DataProcessor')
        
        code = f'''import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    success: bool
    data: Optional[Union[pd.DataFrame, Dict[str, Any]]]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

class {processor_name}:
    """Process and transform data with validation and error handling"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the data processor"""
        self.config = config or {{}}
        self.validation_rules = self._setup_validation_rules()
        self.transformations = []
        
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Setup validation rules for data processing"""
        return {{
            'required_columns': self.config.get('required_columns', []),
            'data_types': self.config.get('data_types', {{}}),
            'value_ranges': self.config.get('value_ranges', {{}}),
        }}
    
    def process(self, data: Union[pd.DataFrame, Dict[str, Any]]) -> ProcessingResult:
        """
        Process the input data
        
        Args:
            data: Input data to process
            
        Returns:
            ProcessingResult with processed data and metadata
        """
        errors = []
        warnings = []
        start_time = datetime.now()
        
        try:
            # Convert to DataFrame if needed
            if isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                df = data.copy()
            
            # Validate data
            validation_errors = self._validate_data(df)
            if validation_errors:
                errors.extend(validation_errors)
                return ProcessingResult(
                    success=False,
                    data=None,
                    errors=errors,
                    warnings=warnings,
                    metadata={{'processing_time': (datetime.now() - start_time).total_seconds()}}
                )
            
            # Apply transformations
            df = self._apply_transformations(df)
            
            # Post-processing validation
            post_errors = self._validate_output(df)
            if post_errors:
                warnings.extend(post_errors)
            
            metadata = {{
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'rows_processed': len(df),
                'columns_processed': len(df.columns),
                'transformations_applied': len(self.transformations)
            }}
            
            return ProcessingResult(
                success=True,
                data=df,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in data processing: {{str(e)}}")
            errors.append(f"Processing failed: {{str(e)}}")
            return ProcessingResult(
                success=False,
                data=None,
                errors=errors,
                warnings=warnings,
                metadata={{'processing_time': (datetime.now() - start_time).total_seconds()}}
            )
    
    def _validate_data(self, df: pd.DataFrame) -> List[str]:
        """Validate input data"""
        errors = []
        
        # Check required columns
        missing_cols = set(self.validation_rules['required_columns']) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {{', '.join(missing_cols)}}")
        
        # Check data types
        for col, expected_type in self.validation_rules['data_types'].items():
            if col in df.columns and not df[col].dtype == expected_type:
                errors.append(f"Column '{{col}}' has incorrect data type")
        
        return errors
    
    def _apply_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply data transformations"""
        # Example transformations
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        df = df.fillna(self.config.get('fill_value', 0))
        
        return df
    
    def _validate_output(self, df: pd.DataFrame) -> List[str]:
        """Validate processed output"""
        warnings = []
        
        if df.empty:
            warnings.append("Output DataFrame is empty")
        
        if df.isnull().any().any():
            warnings.append("Output contains null values")
        
        return warnings'''
        
        return code
    
    def _generate_python_service_class(self, context: Dict[str, Any], requirements: Dict[str, Any]) -> str:
        """Generate Python service class code"""
        service_name = context.get('service_name', 'Service')
        
        code = f'''from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for {service_name}"""
    max_retries: int = 3
    timeout: int = 30
    pool_size: int = 10
    rate_limit: Optional[int] = None

class {service_name}:
    """
    {service_name} implementation with async support and error handling
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        """Initialize the service"""
        self.config = config or ServiceConfig()
        self.executor = ThreadPoolExecutor(max_workers=self.config.pool_size)
        self._is_initialized = False
        self._rate_limiter = self._setup_rate_limiter()
        
    def _setup_rate_limiter(self) -> Optional[Any]:
        """Setup rate limiting if configured"""
        if self.config.rate_limit:
            # Simple rate limiter implementation
            return {{'last_call': None, 'min_interval': 1.0 / self.config.rate_limit}}
        return None
    
    async def initialize(self):
        """Initialize service resources"""
        if self._is_initialized:
            return
        
        try:
            # Initialize connections, load resources, etc.
            logger.info(f"Initializing {{self.__class__.__name__}}")
            await self._connect_resources()
            self._is_initialized = True
            logger.info(f"{{self.__class__.__name__}} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize {{self.__class__.__name__}}: {{e}}")
            raise
    
    async def _connect_resources(self):
        """Connect to required resources"""
        # Implementation specific to the service
        await asyncio.sleep(0.1)  # Simulate connection
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data with retry logic and error handling
        
        Args:
            data: Input data to process
            
        Returns:
            Processed result
        """
        if not self._is_initialized:
            await self.initialize()
        
        # Apply rate limiting
        await self._apply_rate_limit()
        
        for attempt in range(self.config.max_retries):
            try:
                result = await self._process_internal(data)
                return result
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    logger.error(f"All retries exhausted: {{e}}")
                    raise
                logger.warning(f"Attempt {{attempt + 1}} failed: {{e}}, retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _process_internal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal processing logic"""
        # Validate input
        self._validate_input(data)
        
        # Process data
        result = {{
            'status': 'success',
            'processed_at': datetime.now().isoformat(),
            'data': data
        }}
        
        # Simulate processing
        await asyncio.sleep(0.1)
        
        return result
    
    def _validate_input(self, data: Dict[str, Any]):
        """Validate input data"""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        # Add specific validation logic
        required_fields = {requirements.get('required_fields', [])}
        missing = required_fields - set(data.keys())
        if missing:
            raise ValueError(f"Missing required fields: {{missing}}")
    
    async def _apply_rate_limit(self):
        """Apply rate limiting if configured"""
        if not self._rate_limiter:
            return
        
        now = datetime.now()
        last_call = self._rate_limiter.get('last_call')
        
        if last_call:
            elapsed = (now - last_call).total_seconds()
            if elapsed < self._rate_limiter['min_interval']:
                await asyncio.sleep(self._rate_limiter['min_interval'] - elapsed)
        
        self._rate_limiter['last_call'] = datetime.now()
    
    async def cleanup(self):
        """Cleanup service resources"""
        if self._is_initialized:
            logger.info(f"Cleaning up {{self.__class__.__name__}}")
            self.executor.shutdown(wait=True)
            self._is_initialized = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()'''
        
        return code
    
    def _generate_generic_python_code(self, context: Dict[str, Any], requirements: Dict[str, Any]) -> str:
        """Generate generic Python code based on requirements"""
        # This would be enhanced with more sophisticated generation logic
        return '''def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process the input data"""
    # TODO: Implement processing logic
    result = {"status": "success", "data": data}
    return result'''
    
    def _generate_javascript_code(self,
                                 request_type: str,
                                 context: Dict[str, Any],
                                 requirements: Dict[str, Any]) -> GeneratedCode:
        """Generate JavaScript code"""
        # Implementation similar to Python but for JavaScript
        code = "// JavaScript code generation not fully implemented yet"
        
        return GeneratedCode(
            code=code,
            language='javascript',
            context=context,
            confidence=0.5,
            suggestions=["Complete JavaScript generator implementation"],
            dependencies=[]
        )
    
    def _generate_typescript_code(self,
                                 request_type: str,
                                 context: Dict[str, Any],
                                 requirements: Dict[str, Any]) -> GeneratedCode:
        """Generate TypeScript code"""
        # Implementation similar to Python but for TypeScript
        code = "// TypeScript code generation not fully implemented yet"
        
        return GeneratedCode(
            code=code,
            language='typescript',
            context=context,
            confidence=0.5,
            suggestions=["Complete TypeScript generator implementation"],
            dependencies=[]
        )
    
    def _generate_go_code(self,
                         request_type: str,
                         context: Dict[str, Any],
                         requirements: Dict[str, Any]) -> GeneratedCode:
        """Generate Go code"""
        # Implementation similar to Python but for Go
        code = "// Go code generation not fully implemented yet"
        
        return GeneratedCode(
            code=code,
            language='go',
            context=context,
            confidence=0.5,
            suggestions=["Complete Go generator implementation"],
            dependencies=[]
        )
    
    def _generate_java_code(self,
                           request_type: str,
                           context: Dict[str, Any],
                           requirements: Dict[str, Any]) -> GeneratedCode:
        """Generate Java code"""
        # Implementation similar to Python but for Java
        code = "// Java code generation not fully implemented yet"
        
        return GeneratedCode(
            code=code,
            language='java',
            context=context,
            confidence=0.5,
            suggestions=["Complete Java generator implementation"],
            dependencies=[]
        )
    
    def _validate_python_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate Python code"""
        errors = []
        
        try:
            # Check syntax
            compile(code, '<string>', 'exec')
            
            # Check with AST
            tree = ast.parse(code)
            
            # Basic quality checks
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.body[0].__class__.__name__ == 'Expr' or \
                       not hasattr(node.body[0].value, 's'):
                        errors.append(f"Function '{node.name}' missing docstring")
                
                if isinstance(node, ast.ClassDef):
                    if not node.body[0].__class__.__name__ == 'Expr' or \
                       not hasattr(node.body[0].value, 's'):
                        errors.append(f"Class '{node.name}' missing docstring")
            
            return len(errors) == 0, errors
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return False, errors
    
    def _validate_javascript_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate JavaScript code"""
        # Simplified validation
        errors = []
        
        # Check for common issues
        if 'var ' in code:
            errors.append("Consider using 'let' or 'const' instead of 'var'")
        
        if '==' in code and '===' not in code:
            errors.append("Use strict equality (===) instead of loose equality (==)")
        
        return len(errors) == 0, errors
    
    def _validate_typescript_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate TypeScript code"""
        # Would use TypeScript compiler API
        return True, []
    
    def _validate_go_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate Go code"""
        # Would use go fmt and go vet
        return True, []
    
    def _validate_java_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate Java code"""
        # Would use Java compiler API
        return True, []
    
    def _extract_dependencies(self, code: str, language: str) -> List[str]:
        """Extract dependencies from code"""
        dependencies = []
        
        if language == 'python':
            # Extract imports
            import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(\S+)'
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                module = match.group(1) or match.group(2)
                if module and not module.startswith('.'):
                    dependencies.append(module.split('.')[0])
        
        elif language in ['javascript', 'typescript']:
            # Extract require/import
            import_patterns = [
                r"require\(['\"]([^'\"]+)['\"]\)",
                r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",
            ]
            for pattern in import_patterns:
                for match in re.finditer(pattern, code):
                    dependencies.append(match.group(1))
        
        return list(set(dependencies))
    
    def _generate_test_code(self, code: str, language: str, context: Dict[str, Any]) -> str:
        """Generate test code for the generated code"""
        if language == 'python':
            # Parse the code to find testable elements
            try:
                tree = ast.parse(code)
                functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                
                test_code = "import pytest\n\n"
                
                for func in functions:
                    test_code += f'''
def test_{func}():
    """Test {func} function"""
    # TODO: Implement test
    assert True
'''
                
                for cls in classes:
                    test_code += f'''
class Test{cls}:
    """Test suite for {cls}"""
    
    def test_initialization(self):
        """Test {cls} initialization"""
        # TODO: Implement test
        assert True
'''
                
                return test_code
            except (SyntaxError, ValueError, TypeError) as e:
                import logging
                logging.error(f"Error generating test code: {e}")
                return "# Error generating test code"
        
        return f"// Test generation for {language} not implemented"
    
    def _generate_suggestions(self, code: str, language: str, context: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions for the code"""
        suggestions = []
        
        if language == 'python':
            # Check for common improvements
            if 'try:' not in code and 'except' not in code:
                suggestions.append("Consider adding error handling with try/except blocks")
            
            if 'logger' not in code and 'print(' in code:
                suggestions.append("Consider using logging instead of print statements")
            
            if 'type hint' not in code and '->' not in code:
                suggestions.append("Consider adding type hints for better code clarity")
            
            if len(code.split('\n')) > 100:
                suggestions.append("Consider breaking this into smaller functions/modules")
        
        return suggestions
    
    def _detect_coding_style(self, code: str, language: str) -> Dict[str, Any]:
        """Detect coding style from existing code"""
        style = {
            'indentation': 'spaces',
            'indent_size': 4,
            'naming_convention': 'snake_case',
            'quotes': 'double',
        }
        
        if not code:
            return style
        
        # Detect indentation
        lines = code.split('\n')
        for line in lines:
            if line and line[0] in ' \t':
                if line[0] == '\t':
                    style['indentation'] = 'tabs'
                else:
                    # Count spaces
                    spaces = len(line) - len(line.lstrip())
                    if spaces > 0:
                        style['indent_size'] = spaces
                break
        
        # Detect naming convention
        if language == 'python':
            if re.search(r'def [a-z_]+\(', code):
                style['naming_convention'] = 'snake_case'
            elif re.search(r'def [a-z][a-zA-Z]+\(', code):
                style['naming_convention'] = 'camelCase'
        
        # Detect quote style
        single_quotes = code.count("'")
        double_quotes = code.count('"')
        style['quotes'] = 'single' if single_quotes > double_quotes else 'double'
        
        return style
    
    def _detect_dependencies(self, file_path: str, language: str) -> List[str]:
        """Detect project dependencies"""
        dependencies = []
        
        if not file_path:
            return dependencies
        
        project_root = Path(file_path).parent
        
        if language == 'python':
            # Check for requirements.txt, setup.py, pyproject.toml
            req_files = ['requirements.txt', 'requirements-dev.txt', 'pyproject.toml']
            for req_file in req_files:
                req_path = project_root / req_file
                if req_path.exists():
                    try:
                        with open(req_path, 'r') as f:
                            content = f.read()
                            # Simple extraction
                            for line in content.split('\n'):
                                if line and not line.startswith('#'):
                                    dep = line.split('==')[0].split('>=')[0].split('<')[0].strip()
                                    if dep:
                                        dependencies.append(dep)
                    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                        import logging
                        logging.debug(f"Failed to read requirements file {req_path}: {e}")
                        pass
        
        return list(set(dependencies))
    
    def _detect_patterns(self, code: str, language: str) -> Dict[str, Any]:
        """Detect code patterns"""
        patterns = {
            'uses_classes': bool(re.search(r'class\s+\w+', code)),
            'uses_functions': bool(re.search(r'def\s+\w+', code)),
            'uses_async': bool(re.search(r'async\s+def', code)),
            'uses_decorators': bool(re.search(r'@\w+', code)),
            'uses_context_managers': bool(re.search(r'with\s+', code)),
            'uses_list_comprehensions': bool(re.search(r'\[.*for.*in.*\]', code)),
        }
        
        return patterns
    
    def _detect_naming_convention(self, code: str, language: str) -> str:
        """Detect naming convention from code"""
        if language == 'python':
            # Check function names
            func_names = re.findall(r'def\s+(\w+)', code)
            if func_names:
                if all('_' in name for name in func_names):
                    return 'snake_case'
                elif all(name[0].islower() and any(c.isupper() for c in name[1:]) for name in func_names):
                    return 'camelCase'
        
        return 'mixed'
    
    def _analyze_project_patterns(self, project_path: str, language: str) -> Dict[str, Any]:
        """Analyze patterns across the project"""
        patterns = {
            'common_imports': [],
            'common_patterns': [],
            'architecture_style': 'unknown',
        }
        
        # This would analyze multiple files to detect project-wide patterns
        # For now, return basic patterns
        
        return patterns

def main():
    """Demo the intelligent code generator"""
    generator = IntelligentCodeGenerator()
    
    print("🤖 Intelligent Code Generator Demo")
    print("=" * 50)
    
    # Example 1: Generate Python API endpoint
    print("\n1. Generating Python API endpoint:")
    result = generator.generate_code(
        request_type='api_endpoint',
        language='python',
        context={
            'framework': 'fastapi',
            'endpoint_name': 'analyze_data',
            'method': 'POST'
        },
        requirements={
            'required_fields': ['data', 'options'],
            'generate_tests': True
        }
    )
    
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Dependencies: {', '.join(result.dependencies)}")
    print("\nGenerated Code:")
    print(result.code)
    
    if result.test_code:
        print("\nGenerated Test Code:")
        print(result.test_code)
    
    print("\nSuggestions:")
    for suggestion in result.suggestions:
        print(f"  • {suggestion}")
    
    # Example 2: Generate from template
    print("\n\n2. Generating from template:")
    result = generator.generate_code(
        request_type='function',
        language='python',
        context={
            'function_name': 'calculate_metrics',
            'parameters': 'data: pd.DataFrame, config: Dict[str, Any]',
            'return_type': 'Dict[str, float]',
            'docstring': 'Calculate various metrics from the DataFrame',
            'body': 'metrics = {}\n    metrics["mean"] = data.mean().to_dict()\n    metrics["std"] = data.std().to_dict()',
            'return_value': 'metrics'
        }
    )
    
    print("\nGenerated Code:")
    print(result.code)

if __name__ == "__main__":
    main()