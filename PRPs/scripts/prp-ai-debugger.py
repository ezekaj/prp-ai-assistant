#!/usr/bin/env python3
"""
PRP-12Factor AI-Powered Advanced Debugging System
Intelligent root cause analysis and solution recommendations
"""

import ast
import json
import re
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import subprocess
import difflib
from collections import defaultdict, Counter
import networkx as nx
import sys
import io
import contextlib

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Context information for an error"""
    error_type: str
    error_message: str
    file_path: Optional[str]
    line_number: Optional[int]
    code_snippet: Optional[str]
    stack_trace: List[Dict[str, Any]]
    variables: Dict[str, Any]
    system_info: Dict[str, Any]
    timestamp: datetime

@dataclass
class RootCause:
    """Identified root cause of an issue"""
    cause_id: str
    cause_type: str  # 'syntax', 'logic', 'dependency', 'configuration', 'environment'
    description: str
    confidence: float
    evidence: List[str]
    related_code: List[Dict[str, Any]]
    impact_scope: str  # 'local', 'module', 'application'

@dataclass
class DebugSolution:
    """Proposed solution for debugging"""
    solution_id: str
    solution_type: str  # 'code_fix', 'config_change', 'dependency_update', 'refactor'
    title: str
    description: str
    implementation_steps: List[str]
    code_changes: List[Dict[str, Any]]
    confidence: float
    estimated_effort: str  # 'trivial', 'small', 'medium', 'large'
    risk_level: str  # 'low', 'medium', 'high'

@dataclass
class DebugReport:
    """Comprehensive debugging report"""
    error_context: ErrorContext
    root_causes: List[RootCause]
    solutions: List[DebugSolution]
    analysis_duration: float
    test_scenarios: List[Dict[str, Any]]
    prevention_tips: List[str]
    generated_at: datetime

class AdvancedDebugger:
    """AI-powered advanced debugging system"""
    
    def __init__(self, project_root: str = ".", ai_engine=None):
        self.project_root = Path(project_root).resolve()
        self.ai_engine = ai_engine
        
        # Knowledge base
        self.error_patterns = self._load_error_patterns()
        self.solution_templates = self._load_solution_templates()
        self.dependency_graph = nx.DiGraph()
        
        # Debugging history
        self.debug_history: List[DebugReport] = []
        self.solution_effectiveness: Dict[str, float] = {}
        
        # Configuration
        self.config = {
            'max_stack_depth': 20,
            'code_context_lines': 5,
            'max_solutions': 5,
            'confidence_threshold': 0.6,
            'enable_auto_fix': False,
            'test_generation': True,
        }
        
        logger.info("Advanced Debugger initialized")
    
    def _load_error_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load common error patterns and their causes"""
        return {
            'python': {
                'ImportError': [
                    {
                        'pattern': r"No module named '(\w+)'",
                        'cause': 'missing_dependency',
                        'solution': 'install_package'
                    },
                    {
                        'pattern': r"cannot import name '(\w+)'",
                        'cause': 'circular_import',
                        'solution': 'refactor_imports'
                    }
                ],
                'AttributeError': [
                    {
                        'pattern': r"'NoneType' object has no attribute",
                        'cause': 'null_reference',
                        'solution': 'add_null_check'
                    },
                    {
                        'pattern': r"module '(\w+)' has no attribute '(\w+)'",
                        'cause': 'wrong_import',
                        'solution': 'fix_import_path'
                    }
                ],
                'TypeError': [
                    {
                        'pattern': r"unsupported operand type",
                        'cause': 'type_mismatch',
                        'solution': 'type_conversion'
                    },
                    {
                        'pattern': r"missing \d+ required positional argument",
                        'cause': 'missing_arguments',
                        'solution': 'add_arguments'
                    }
                ],
                'KeyError': [
                    {
                        'pattern': r"KeyError: '(\w+)'",
                        'cause': 'missing_key',
                        'solution': 'add_key_check'
                    }
                ],
                'IndexError': [
                    {
                        'pattern': r"list index out of range",
                        'cause': 'index_bounds',
                        'solution': 'add_bounds_check'
                    }
                ],
            },
            'javascript': {
                'TypeError': [
                    {
                        'pattern': r"Cannot read prop.* of undefined",
                        'cause': 'undefined_reference',
                        'solution': 'add_optional_chaining'
                    },
                    {
                        'pattern': r"is not a function",
                        'cause': 'not_a_function',
                        'solution': 'check_function_type'
                    }
                ],
                'ReferenceError': [
                    {
                        'pattern': r"(\w+) is not defined",
                        'cause': 'undefined_variable',
                        'solution': 'declare_variable'
                    }
                ],
            }
        }
    
    def _load_solution_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load solution templates"""
        return {
            'install_package': {
                'title': 'Install missing package',
                'steps': [
                    'Identify the missing package name',
                    'Check if it\'s in requirements.txt or package.json',
                    'Install using pip install {package} or npm install {package}',
                    'Add to dependency file'
                ],
                'code_template': 'pip install {package}\necho "{package}" >> requirements.txt'
            },
            'add_null_check': {
                'title': 'Add null/undefined check',
                'steps': [
                    'Identify where the null value originates',
                    'Add defensive check before accessing attributes',
                    'Consider using optional chaining or safe navigation'
                ],
                'code_template': '''if {variable} is not None:
    {original_code}
else:
    # Handle null case
    {alternative_action}'''
            },
            'refactor_imports': {
                'title': 'Refactor circular imports',
                'steps': [
                    'Identify the circular dependency',
                    'Move shared code to a separate module',
                    'Use lazy imports if necessary',
                    'Consider restructuring module hierarchy'
                ],
                'code_template': '''# Move to separate module
# shared.py
{shared_code}

# Original modules import from shared
from .shared import {imports}'''
            },
            'add_bounds_check': {
                'title': 'Add array bounds checking',
                'steps': [
                    'Check array length before accessing',
                    'Use safe access methods',
                    'Handle edge cases'
                ],
                'code_template': '''if 0 <= index < len(array):
    value = array[index]
else:
    # Handle out of bounds
    value = default_value'''
            }
        }
    
    async def debug_error(self, error: Union[Exception, str], context: Optional[Dict[str, Any]] = None) -> DebugReport:
        """Perform comprehensive debugging of an error"""
        start_time = datetime.now()
        
        # Extract error context
        error_context = self._extract_error_context(error, context)
        
        # Analyze root causes
        root_causes = await self._analyze_root_causes(error_context)
        
        # Generate solutions
        solutions = await self._generate_solutions(error_context, root_causes)
        
        # Create test scenarios
        test_scenarios = self._generate_test_scenarios(error_context, solutions)
        
        # Generate prevention tips
        prevention_tips = self._generate_prevention_tips(root_causes)
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Create report
        report = DebugReport(
            error_context=error_context,
            root_causes=root_causes,
            solutions=solutions,
            analysis_duration=duration,
            test_scenarios=test_scenarios,
            prevention_tips=prevention_tips,
            generated_at=datetime.now()
        )
        
        # Store in history
        self.debug_history.append(report)
        
        return report
    
    def _extract_error_context(self, error: Union[Exception, str], context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """Extract comprehensive error context"""
        if isinstance(error, str):
            # Parse error string
            error_type = "UnknownError"
            error_message = error
            stack_trace = []
        else:
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = self._extract_stack_trace(error)
        
        # Extract file and line info
        file_path = None
        line_number = None
        code_snippet = None
        
        if stack_trace:
            # Get the most relevant frame (usually the last one in user code)
            for frame in reversed(stack_trace):
                if self._is_user_code(frame['file']):
                    file_path = frame['file']
                    line_number = frame['line']
                    code_snippet = self._get_code_context(file_path, line_number)
                    break
        
        # Extract variables from context
        variables = {}
        if context:
            variables.update(context.get('locals', {}))
            variables.update(context.get('globals', {}))
        
        # Get system info
        system_info = {
            'python_version': sys.version,
            'platform': sys.platform,
            'cwd': str(Path.cwd()),
        }
        
        return ErrorContext(
            error_type=error_type,
            error_message=error_message,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            stack_trace=stack_trace,
            variables=variables,
            system_info=system_info,
            timestamp=datetime.now()
        )
    
    def _extract_stack_trace(self, error: Exception) -> List[Dict[str, Any]]:
        """Extract detailed stack trace"""
        stack_trace = []
        
        tb = error.__traceback__
        while tb and len(stack_trace) < self.config['max_stack_depth']:
            frame = tb.tb_frame
            
            stack_frame = {
                'file': frame.f_code.co_filename,
                'line': tb.tb_lineno,
                'function': frame.f_code.co_name,
                'locals': {k: self._safe_repr(v) for k, v in frame.f_locals.items()},
                'code': self._get_line_code(frame.f_code.co_filename, tb.tb_lineno)
            }
            
            stack_trace.append(stack_frame)
            tb = tb.tb_next
        
        return stack_trace
    
    def _safe_repr(self, obj: Any, max_length: int = 100) -> str:
        """Safe string representation of object"""
        try:
            repr_str = repr(obj)
            if len(repr_str) > max_length:
                return repr_str[:max_length] + '...'
            return repr_str
        except (TypeError, AttributeError, RecursionError) as e:
            import logging
            logging.debug(f"Failed to get repr for object of type {type(obj).__name__}: {e}")
            return f"<{type(obj).__name__} object>"
    
    def _get_code_context(self, file_path: str, line_number: int) -> Optional[str]:
        """Get code context around error line"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            context_range = self.config['code_context_lines']
            start = max(0, line_number - context_range - 1)
            end = min(len(lines), line_number + context_range)
            
            context_lines = []
            for i in range(start, end):
                prefix = '>>> ' if i == line_number - 1 else '    '
                context_lines.append(f"{i+1:4d}{prefix}{lines[i].rstrip()}")
            
            return '\n'.join(context_lines)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, IndexError) as e:
            import logging
            logging.debug(f"Failed to get code context for {file_path}:{line_number}: {e}")
            return None
    
    def _get_line_code(self, file_path: str, line_number: int) -> Optional[str]:
        """Get specific line of code"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if 0 < line_number <= len(lines):
                return lines[line_number - 1].strip()
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, IndexError) as e:
            import logging
            logging.debug(f"Failed to get line code for {file_path}:{line_number}: {e}")
            pass
        return None
    
    def _is_user_code(self, file_path: str) -> bool:
        """Check if file is user code (not library)"""
        if not file_path:
            return False
        
        # Skip standard library and site-packages
        skip_patterns = ['site-packages', 'lib/python', '<frozen', '<string>']
        return not any(pattern in file_path for pattern in skip_patterns)
    
    async def _analyze_root_causes(self, context: ErrorContext) -> List[RootCause]:
        """Analyze root causes of the error"""
        root_causes = []
        
        # Pattern-based analysis
        language = self._detect_language(context.file_path) if context.file_path else 'python'
        error_patterns = self.error_patterns.get(language, {}).get(context.error_type, [])
        
        for pattern_info in error_patterns:
            match = re.search(pattern_info['pattern'], context.error_message)
            if match:
                cause = RootCause(
                    cause_id=f"pattern_{pattern_info['cause']}",
                    cause_type=pattern_info['cause'],
                    description=self._generate_cause_description(pattern_info['cause'], match.groups()),
                    confidence=0.8,
                    evidence=[f"Error matches pattern: {pattern_info['pattern']}"],
                    related_code=self._find_related_code(context, pattern_info['cause']),
                    impact_scope=self._determine_impact_scope(pattern_info['cause'])
                )
                root_causes.append(cause)
        
        # Code analysis
        if context.code_snippet:
            code_causes = await self._analyze_code_causes(context)
            root_causes.extend(code_causes)
        
        # Stack trace analysis
        if context.stack_trace:
            trace_causes = self._analyze_stack_trace_causes(context.stack_trace)
            root_causes.extend(trace_causes)
        
        # Variable state analysis
        if context.variables:
            var_causes = self._analyze_variable_causes(context.variables, context)
            root_causes.extend(var_causes)
        
        # Sort by confidence
        root_causes.sort(key=lambda x: x.confidence, reverse=True)
        
        return root_causes[:5]  # Top 5 causes
    
    async def _analyze_code_causes(self, context: ErrorContext) -> List[RootCause]:
        """Analyze code for potential causes"""
        causes = []
        
        if not context.code_snippet:
            return causes
        
        # Extract the error line
        lines = context.code_snippet.split('\n')
        error_line = None
        for line in lines:
            if '>>>' in line:
                error_line = line.split('>>>', 1)[1].strip()
                break
        
        if not error_line:
            return causes
        
        # Check for common code issues
        if context.error_type == 'AttributeError' and ' = None' in context.code_snippet:
            causes.append(RootCause(
                cause_id="null_assignment",
                cause_type="logic",
                description="Variable might be assigned None before attribute access",
                confidence=0.7,
                evidence=["Found None assignment in code context"],
                related_code=[{'line': error_line, 'issue': 'Accessing attribute on potentially None object'}],
                impact_scope="local"
            ))
        
        if context.error_type == 'KeyError' and '[' in error_line and ']' in error_line:
            causes.append(RootCause(
                cause_id="dict_key_access",
                cause_type="logic",
                description="Accessing dictionary key that might not exist",
                confidence=0.8,
                evidence=["Direct dictionary key access without checking"],
                related_code=[{'line': error_line, 'issue': 'Unsafe dictionary access'}],
                impact_scope="local"
            ))
        
        return causes
    
    def _analyze_stack_trace_causes(self, stack_trace: List[Dict[str, Any]]) -> List[RootCause]:
        """Analyze stack trace for causes"""
        causes = []
        
        # Look for patterns in the call stack
        function_calls = [frame['function'] for frame in stack_trace]
        
        # Check for recursion
        if len(function_calls) > 10:
            call_counts = Counter(function_calls)
            for func, count in call_counts.items():
                if count > 5:
                    causes.append(RootCause(
                        cause_id="possible_recursion",
                        cause_type="logic",
                        description=f"Possible infinite recursion in function '{func}'",
                        confidence=0.6,
                        evidence=[f"Function '{func}' appears {count} times in stack"],
                        related_code=[],
                        impact_scope="module"
                    ))
        
        return causes
    
    def _analyze_variable_causes(self, variables: Dict[str, Any], context: ErrorContext) -> List[RootCause]:
        """Analyze variable states for causes"""
        causes = []
        
        # Check for None/null values
        none_vars = [var for var, val in variables.items() if val is None]
        if none_vars and context.error_type == 'AttributeError':
            causes.append(RootCause(
                cause_id="null_variables",
                cause_type="logic",
                description=f"Variables are None: {', '.join(none_vars)}",
                confidence=0.7,
                evidence=[f"Found {len(none_vars)} None variables"],
                related_code=[],
                impact_scope="local"
            ))
        
        # Check for empty collections
        empty_collections = []
        for var, val in variables.items():
            if isinstance(val, (list, dict, set, tuple)) and len(val) == 0:
                empty_collections.append(var)
        
        if empty_collections and context.error_type in ['IndexError', 'KeyError']:
            causes.append(RootCause(
                cause_id="empty_collections",
                cause_type="logic",
                description=f"Empty collections: {', '.join(empty_collections)}",
                confidence=0.6,
                evidence=["Operating on empty collections"],
                related_code=[],
                impact_scope="local"
            ))
        
        return causes
    
    async def _generate_solutions(self, context: ErrorContext, root_causes: List[RootCause]) -> List[DebugSolution]:
        """Generate solutions based on root causes"""
        solutions = []
        
        for cause in root_causes:
            # Get solution templates
            template_name = self._get_solution_template_for_cause(cause.cause_type)
            if template_name in self.solution_templates:
                template = self.solution_templates[template_name]
                
                # Generate specific solution
                solution = DebugSolution(
                    solution_id=f"sol_{cause.cause_id}",
                    solution_type=self._determine_solution_type(template_name),
                    title=template['title'],
                    description=self._customize_solution_description(template, cause, context),
                    implementation_steps=self._customize_steps(template['steps'], cause, context),
                    code_changes=self._generate_code_changes(template, cause, context),
                    confidence=cause.confidence * 0.9,  # Slightly lower than cause confidence
                    estimated_effort=self._estimate_effort(template_name),
                    risk_level=self._assess_risk(template_name)
                )
                solutions.append(solution)
        
        # Add generic solutions if needed
        if len(solutions) < 3:
            generic_solutions = self._generate_generic_solutions(context)
            solutions.extend(generic_solutions)
        
        # Sort by confidence and effort
        solutions.sort(key=lambda x: (x.confidence, -self._effort_score(x.estimated_effort)), reverse=True)
        
        return solutions[:self.config['max_solutions']]
    
    def _generate_code_changes(self, template: Dict[str, Any], cause: RootCause, context: ErrorContext) -> List[Dict[str, Any]]:
        """Generate specific code changes"""
        changes = []
        
        if 'code_template' in template and context.file_path and context.line_number:
            # Customize template
            code = template['code_template']
            
            # Replace placeholders
            if context.error_type == 'KeyError':
                match = re.search(r"KeyError: '(\w+)'", context.error_message)
                if match:
                    key = match.group(1)
                    code = code.replace('{key}', key)
            
            change = {
                'file': context.file_path,
                'line': context.line_number,
                'action': 'replace',
                'original': context.code_snippet,
                'replacement': code,
                'description': f"Apply fix for {cause.cause_type}"
            }
            changes.append(change)
        
        return changes
    
    def _generate_test_scenarios(self, context: ErrorContext, solutions: List[DebugSolution]) -> List[Dict[str, Any]]:
        """Generate test scenarios to verify fixes"""
        scenarios = []
        
        for solution in solutions:
            if context.error_type == 'KeyError':
                scenarios.append({
                    'name': 'Test with missing key',
                    'setup': 'data = {"existing_key": "value"}',
                    'test': 'result = data.get("missing_key", "default")',
                    'expected': 'No KeyError raised'
                })
            
            elif context.error_type == 'AttributeError':
                scenarios.append({
                    'name': 'Test with None object',
                    'setup': 'obj = None',
                    'test': 'if obj is not None: obj.attribute',
                    'expected': 'No AttributeError raised'
                })
            
            elif context.error_type == 'IndexError':
                scenarios.append({
                    'name': 'Test with empty list',
                    'setup': 'lst = []',
                    'test': 'if lst: value = lst[0]',
                    'expected': 'No IndexError raised'
                })
        
        return scenarios
    
    def _generate_prevention_tips(self, root_causes: List[RootCause]) -> List[str]:
        """Generate tips to prevent similar errors"""
        tips = []
        
        cause_types = set(cause.cause_type for cause in root_causes)
        
        if 'null_reference' in cause_types:
            tips.append("Always check for None/null before accessing attributes")
            tips.append("Use optional chaining (?.)")
            tips.append("Initialize variables with appropriate defaults")
        
        if 'missing_key' in cause_types:
            tips.append("Use .get() method with default values for dictionaries")
            tips.append("Check key existence with 'in' operator")
            tips.append("Consider using defaultdict for automatic defaults")
        
        if 'type_mismatch' in cause_types:
            tips.append("Use type hints to catch type errors early")
            tips.append("Validate input types at function boundaries")
            tips.append("Use isinstance() for runtime type checking")
        
        if 'missing_dependency' in cause_types:
            tips.append("Keep requirements.txt/package.json up to date")
            tips.append("Use virtual environments to isolate dependencies")
            tips.append("Document all external dependencies")
        
        # General tips
        tips.extend([
            "Enable linting and type checking in your IDE",
            "Write unit tests for edge cases",
            "Use defensive programming practices",
            "Log important state before critical operations"
        ])
        
        return list(set(tips))[:5]  # Top 5 unique tips
    
    async def analyze_code_flow(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """Analyze code execution flow"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Find the function
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    return self._analyze_function_flow(node)
            
            return {'error': 'Function not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_function_flow(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze function execution flow"""
        flow = {
            'name': func_node.name,
            'parameters': [arg.arg for arg in func_node.args.args],
            'branches': [],
            'loops': [],
            'returns': [],
            'exceptions': [],
            'calls': []
        }
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.If):
                flow['branches'].append({
                    'type': 'if',
                    'line': node.lineno,
                    'condition': ast.unparse(node.test) if hasattr(ast, 'unparse') else 'condition'
                })
            
            elif isinstance(node, (ast.For, ast.While)):
                flow['loops'].append({
                    'type': type(node).__name__.lower(),
                    'line': node.lineno
                })
            
            elif isinstance(node, ast.Return):
                flow['returns'].append({
                    'line': node.lineno,
                    'value': ast.unparse(node.value) if node.value and hasattr(ast, 'unparse') else None
                })
            
            elif isinstance(node, ast.Raise):
                flow['exceptions'].append({
                    'line': node.lineno,
                    'type': type(node.exc).__name__ if node.exc else 'Exception'
                })
            
            elif isinstance(node, ast.Call):
                if hasattr(node.func, 'id'):
                    flow['calls'].append({
                        'function': node.func.id,
                        'line': node.lineno
                    })
        
        return flow
    
    async def simulate_fix(self, solution: DebugSolution, context: ErrorContext) -> Dict[str, Any]:
        """Simulate applying a fix and test it"""
        result = {
            'success': False,
            'output': None,
            'error': None,
            'side_effects': []
        }
        
        if not solution.code_changes:
            result['error'] = "No code changes to apply"
            return result
        
        # Create temporary fix
        for change in solution.code_changes:
            if change['action'] == 'replace':
                # Simulate the change
                try:
                    # Create a safe execution environment
                    safe_globals = {'__builtins__': {}}
                    safe_locals = {}
                    
                    # Execute the replacement code
                    exec(change['replacement'], safe_globals, safe_locals)
                    
                    result['success'] = True
                    result['output'] = "Fix applied successfully (simulation)"
                except Exception as e:
                    result['error'] = str(e)
                    result['side_effects'].append(f"Fix would cause: {type(e).__name__}")
        
        return result
    
    # Helper methods
    def _detect_language(self, file_path: Optional[str]) -> str:
        """Detect programming language"""
        if not file_path:
            return 'python'
        
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
        }
        
        return ext_map.get(Path(file_path).suffix, 'python')
    
    def _generate_cause_description(self, cause_type: str, match_groups: Tuple) -> str:
        """Generate human-readable cause description"""
        descriptions = {
            'missing_dependency': f"Module '{match_groups[0] if match_groups else 'unknown'}' is not installed",
            'circular_import': f"Circular import detected when importing '{match_groups[0] if match_groups else 'module'}'",
            'null_reference': "Attempting to access attribute on None/null object",
            'type_mismatch': "Operation between incompatible types",
            'missing_arguments': "Function called with insufficient arguments",
            'missing_key': f"Dictionary key '{match_groups[0] if match_groups else 'unknown'}' does not exist",
            'index_bounds': "List index is out of valid range",
        }
        
        return descriptions.get(cause_type, f"Issue type: {cause_type}")
    
    def _find_related_code(self, context: ErrorContext, cause_type: str) -> List[Dict[str, Any]]:
        """Find code related to the cause"""
        related = []
        
        if context.code_snippet:
            lines = context.code_snippet.split('\n')
            for line in lines:
                if '>>>' not in line:  # Skip the error line itself
                    # Look for patterns related to cause
                    if cause_type == 'null_reference' and ' = None' in line:
                        related.append({
                            'line': line.strip(),
                            'issue': 'None assignment'
                        })
                    elif cause_type == 'missing_key' and '.get(' not in line and '[' in line:
                        related.append({
                            'line': line.strip(),
                            'issue': 'Direct key access'
                        })
        
        return related
    
    def _determine_impact_scope(self, cause_type: str) -> str:
        """Determine the scope of impact"""
        module_level = ['circular_import', 'missing_dependency']
        app_level = ['configuration', 'environment']
        
        if cause_type in module_level:
            return 'module'
        elif cause_type in app_level:
            return 'application'
        else:
            return 'local'
    
    def _get_solution_template_for_cause(self, cause_type: str) -> str:
        """Map cause type to solution template"""
        mapping = {
            'missing_dependency': 'install_package',
            'null_reference': 'add_null_check',
            'circular_import': 'refactor_imports',
            'index_bounds': 'add_bounds_check',
            'missing_key': 'add_null_check',  # Similar solution
        }
        
        return mapping.get(cause_type, 'generic_fix')
    
    def _determine_solution_type(self, template_name: str) -> str:
        """Determine solution type from template"""
        if 'install' in template_name:
            return 'dependency_update'
        elif 'refactor' in template_name:
            return 'refactor'
        elif 'config' in template_name:
            return 'config_change'
        else:
            return 'code_fix'
    
    def _customize_solution_description(self, template: Dict[str, Any], cause: RootCause, context: ErrorContext) -> str:
        """Customize solution description"""
        desc = template.get('description', template['title'])
        
        # Add specific details
        if cause.cause_type == 'missing_dependency':
            match = re.search(r"No module named '(\w+)'", context.error_message)
            if match:
                desc += f"\n\nSpecifically, install the '{match.group(1)}' package."
        
        return desc
    
    def _customize_steps(self, steps: List[str], cause: RootCause, context: ErrorContext) -> List[str]:
        """Customize solution steps"""
        customized = []
        
        for step in steps:
            # Replace placeholders
            if '{package}' in step and cause.cause_type == 'missing_dependency':
                match = re.search(r"No module named '(\w+)'", context.error_message)
                if match:
                    step = step.replace('{package}', match.group(1))
            
            customized.append(step)
        
        return customized
    
    def _estimate_effort(self, template_name: str) -> str:
        """Estimate implementation effort"""
        trivial = ['add_null_check', 'add_bounds_check']
        small = ['install_package', 'fix_import_path']
        medium = ['refactor_imports', 'type_conversion']
        
        if template_name in trivial:
            return 'trivial'
        elif template_name in small:
            return 'small'
        elif template_name in medium:
            return 'medium'
        else:
            return 'large'
    
    def _assess_risk(self, template_name: str) -> str:
        """Assess risk level of solution"""
        low_risk = ['add_null_check', 'install_package']
        medium_risk = ['fix_import_path', 'type_conversion']
        high_risk = ['refactor_imports']
        
        if template_name in low_risk:
            return 'low'
        elif template_name in medium_risk:
            return 'medium'
        elif template_name in high_risk:
            return 'high'
        else:
            return 'medium'
    
    def _effort_score(self, effort: str) -> int:
        """Convert effort to numeric score"""
        scores = {
            'trivial': 1,
            'small': 2,
            'medium': 3,
            'large': 4
        }
        return scores.get(effort, 3)
    
    def _generate_generic_solutions(self, context: ErrorContext) -> List[DebugSolution]:
        """Generate generic solutions as fallback"""
        solutions = []
        
        # Generic error handling
        solutions.append(DebugSolution(
            solution_id="generic_try_except",
            solution_type="code_fix",
            title="Add error handling",
            description="Wrap the code in try-except block to handle the error gracefully",
            implementation_steps=[
                "Identify the code section that raises the error",
                "Wrap it in a try-except block",
                "Log the error for debugging",
                "Provide a fallback behavior"
            ],
            code_changes=[],
            confidence=0.5,
            estimated_effort="trivial",
            risk_level="low"
        ))
        
        # Logging solution
        solutions.append(DebugSolution(
            solution_id="add_logging",
            solution_type="code_fix",
            title="Add debug logging",
            description="Add logging to understand the state before the error",
            implementation_steps=[
                "Import logging module",
                "Add log statements before the error line",
                "Log relevant variable values",
                "Run again to gather more information"
            ],
            code_changes=[],
            confidence=0.4,
            estimated_effort="trivial",
            risk_level="low"
        ))
        
        return solutions

async def demo_debugger():
    """Demo the advanced debugger"""
    debugger = AdvancedDebugger()
    
    print("🔍 Advanced AI Debugger Demo")
    print("=" * 50)
    
    # Example 1: Debug a KeyError
    print("\n1. Debugging KeyError:")
    
    try:
        data = {'name': 'John', 'age': 30}
        print(data['email'])  # This will raise KeyError
    except Exception as e:
        report = await debugger.debug_error(e, context={'locals': locals()})
        
        print(f"\n❌ Error: {report.error_context.error_type}")
        print(f"Message: {report.error_context.error_message}")
        
        print("\n🔍 Root Causes:")
        for cause in report.root_causes:
            print(f"\n  • {cause.description}")
            print(f"    Confidence: {cause.confidence:.1%}")
            print(f"    Impact: {cause.impact_scope}")
            for evidence in cause.evidence:
                print(f"    - {evidence}")
        
        print("\n💡 Solutions:")
        for i, solution in enumerate(report.solutions, 1):
            print(f"\n  {i}. {solution.title}")
            print(f"     {solution.description}")
            print(f"     Effort: {solution.estimated_effort} | Risk: {solution.risk_level}")
            print("     Steps:")
            for step in solution.implementation_steps:
                print(f"     - {step}")
        
        print("\n🧪 Test Scenarios:")
        for scenario in report.test_scenarios:
            print(f"  • {scenario['name']}")
            print(f"    Setup: {scenario['setup']}")
            print(f"    Test: {scenario['test']}")
        
        print("\n🛡️ Prevention Tips:")
        for tip in report.prevention_tips:
            print(f"  • {tip}")
    
    # Example 2: Debug AttributeError
    print("\n\n2. Debugging AttributeError:")
    
    try:
        result = None
        print(result.upper())  # This will raise AttributeError
    except Exception as e:
        report = await debugger.debug_error(e, context={'locals': locals()})
        
        print(f"\n❌ Error: {report.error_context.error_type}")
        print("\n💡 Top Solution:")
        if report.solutions:
            solution = report.solutions[0]
            print(f"  {solution.title}")
            for step in solution.implementation_steps:
                print(f"  - {step}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_debugger())