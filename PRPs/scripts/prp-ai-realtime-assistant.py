#!/usr/bin/env python3
"""
PRP-12Factor AI Real-Time Assistant
Live assistance with code review, suggestions, and problem detection
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import deque
import difflib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ast
import time

logger = logging.getLogger(__name__)

@dataclass
class CodeChange:
    """Represents a code change event"""
    file_path: str
    change_type: str  # 'added', 'modified', 'deleted'
    timestamp: datetime
    old_content: Optional[str]
    new_content: Optional[str]
    line_changes: List[Tuple[int, str, str]]  # (line_no, old_line, new_line)

@dataclass
class LiveSuggestion:
    """Real-time suggestion for code improvement"""
    suggestion_id: str
    file_path: str
    line_number: Optional[int]
    suggestion_type: str  # 'error', 'warning', 'improvement', 'security', 'performance'
    title: str
    description: str
    code_snippet: Optional[str]
    fix_snippet: Optional[str]
    confidence: float
    priority: str  # 'critical', 'high', 'medium', 'low'
    created_at: datetime

@dataclass
class CodeReview:
    """Automated code review result"""
    file_path: str
    overall_score: float
    issues: List[LiveSuggestion]
    strengths: List[str]
    metrics: Dict[str, Any]
    reviewed_at: datetime

class RealTimeAssistant:
    """AI-powered real-time coding assistant"""
    
    def __init__(self, project_root: str = ".", ai_engine=None):
        self.project_root = Path(project_root).resolve()
        self.ai_engine = ai_engine  # Reference to AI learning engine
        
        # Real-time components
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.suggestion_queue: deque = deque(maxlen=1000)
        self.file_cache: Dict[str, str] = {}
        self.observer = None
        
        # Analysis patterns
        self.error_patterns = self._load_error_patterns()
        self.security_patterns = self._load_security_patterns()
        self.performance_patterns = self._load_performance_patterns()
        self.best_practices = self._load_best_practices()
        
        # Configuration
        self.config = {
            'auto_suggest_delay': 0.5,  # Seconds to wait before suggesting
            'max_suggestions_per_file': 10,
            'confidence_threshold': 0.6,
            'watch_extensions': ['.py', '.js', '.ts', '.java', '.go', '.rb'],
            'ignore_patterns': ['__pycache__', 'node_modules', '.git', 'venv'],
        }
        
        # Suggestion handlers
        self.suggestion_handlers: List[Callable] = []
        
        logger.info("Real-Time Assistant initialized")
    
    def _load_error_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load common error patterns"""
        return {
            'python': [
                {
                    'pattern': r'except\s*:',
                    'message': 'Bare except clause catches all exceptions',
                    'suggestion': 'except Exception as e:',
                    'type': 'error'
                },
                {
                    'pattern': r'print\s*\(',
                    'message': 'Consider using logging instead of print',
                    'suggestion': 'logger.info(...)',
                    'type': 'improvement'
                },
                {
                    'pattern': r'==\s*None|!=\s*None',
                    'message': 'Use "is None" or "is not None" for None comparison',
                    'suggestion': 'is None',
                    'type': 'warning'
                },
            ],
            'javascript': [
                {
                    'pattern': r'var\s+\w+',
                    'message': 'Use const or let instead of var',
                    'suggestion': 'const',
                    'type': 'improvement'
                },
                {
                    'pattern': r'==(?!=)',
                    'message': 'Use === for strict equality',
                    'suggestion': '===',
                    'type': 'warning'
                },
            ]
        }
    
    def _load_security_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load security vulnerability patterns"""
        return {
            'python': [
                {
                    'pattern': r'eval\s*\(',
                    'message': 'eval() is a security risk - arbitrary code execution',
                    'type': 'security',
                    'severity': 'critical'
                },
                {
                    'pattern': r'pickle\.load',
                    'message': 'pickle.load() can execute arbitrary code',
                    'type': 'security',
                    'severity': 'high'
                },
                {
                    'pattern': r'password\s*=\s*["\'][^"\']+["\']',
                    'message': 'Hardcoded password detected',
                    'type': 'security',
                    'severity': 'critical'
                },
            ],
            'javascript': [
                {
                    'pattern': r'innerHTML\s*=',
                    'message': 'innerHTML can lead to XSS vulnerabilities',
                    'suggestion': 'Use textContent or sanitize input',
                    'type': 'security',
                    'severity': 'high'
                },
                {
                    'pattern': r'document\.write',
                    'message': 'document.write can be a security risk',
                    'type': 'security',
                    'severity': 'medium'
                },
            ]
        }
    
    def _load_performance_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load performance issue patterns"""
        return {
            'python': [
                {
                    'pattern': r'for .+ in .+:\s*for .+ in .+:',
                    'message': 'Nested loops can be performance bottlenecks',
                    'type': 'performance',
                    'suggestion': 'Consider using list comprehensions or numpy operations'
                },
                {
                    'pattern': r'\.append\(.+\)\s*inside\s*loop',
                    'message': 'Repeated append in loops is inefficient',
                    'type': 'performance',
                    'suggestion': 'Consider list comprehension or pre-allocation'
                },
            ],
            'javascript': [
                {
                    'pattern': r'document\.querySelector.*inside.*loop',
                    'message': 'DOM queries in loops are expensive',
                    'type': 'performance',
                    'suggestion': 'Cache DOM queries outside the loop'
                },
            ]
        }
    
    def _load_best_practices(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load coding best practices"""
        return {
            'python': [
                {
                    'check': 'function_length',
                    'max_lines': 50,
                    'message': 'Function is too long - consider breaking it down',
                    'type': 'improvement'
                },
                {
                    'check': 'class_methods',
                    'max_methods': 20,
                    'message': 'Class has too many methods - consider splitting',
                    'type': 'improvement'
                },
            ],
            'general': [
                {
                    'check': 'file_length',
                    'max_lines': 500,
                    'message': 'File is getting large - consider splitting into modules',
                    'type': 'improvement'
                },
            ]
        }
    
    async def start_monitoring(self, paths: Optional[List[str]] = None):
        """Start monitoring files for real-time assistance"""
        if paths is None:
            paths = [str(self.project_root)]
        
        # Set up file watcher
        event_handler = CodeChangeHandler(self)
        self.observer = Observer()
        
        for path in paths:
            self.observer.schedule(event_handler, path, recursive=True)
        
        self.observer.start()
        logger.info(f"Started monitoring {len(paths)} paths")
        
        # Start suggestion processor
        asyncio.create_task(self._process_suggestions())
    
    async def stop_monitoring(self):
        """Stop file monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped monitoring")
    
    async def analyze_file(self, file_path: str, content: Optional[str] = None) -> CodeReview:
        """Perform comprehensive analysis on a file"""
        file_path = Path(file_path)
        
        # Read content if not provided
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                return CodeReview(
                    file_path=str(file_path),
                    overall_score=0.0,
                    issues=[],
                    strengths=[],
                    metrics={},
                    reviewed_at=datetime.now()
                )
        
        # Determine language
        language = self._detect_language(file_path)
        
        # Run analyses
        issues = []
        metrics = {}
        
        # Syntax and error checking
        syntax_issues = await self._check_syntax(content, language)
        issues.extend(syntax_issues)
        
        # Security scanning
        security_issues = await self._scan_security(content, language)
        issues.extend(security_issues)
        
        # Performance analysis
        performance_issues = await self._analyze_performance(content, language)
        issues.extend(performance_issues)
        
        # Best practices
        practice_issues = await self._check_best_practices(content, language)
        issues.extend(practice_issues)
        
        # Code metrics
        metrics = await self._calculate_metrics(content, language)
        
        # Identify strengths
        strengths = self._identify_strengths(content, language, issues)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(issues, metrics)
        
        return CodeReview(
            file_path=str(file_path),
            overall_score=overall_score,
            issues=issues,
            strengths=strengths,
            metrics=metrics,
            reviewed_at=datetime.now()
        )
    
    async def get_live_suggestions(self, file_path: str, cursor_position: Optional[Tuple[int, int]] = None) -> List[LiveSuggestion]:
        """Get context-aware suggestions for current cursor position"""
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            import logging
            logging.debug(f"Failed to read file {file_path} for live suggestions: {e}")
            return suggestions
        
        language = self._detect_language(file_path)
        lines = content.split('\n')
        
        if cursor_position:
            line_no, col_no = cursor_position
            if 0 <= line_no < len(lines):
                current_line = lines[line_no]
                
                # Context-aware completions
                completions = await self._get_completions(
                    current_line[:col_no],
                    language,
                    lines[:line_no]
                )
                
                for completion in completions:
                    suggestion = LiveSuggestion(
                        suggestion_id=f"completion_{time.time()}",
                        file_path=file_path,
                        line_number=line_no,
                        suggestion_type='improvement',
                        title=f"Complete: {completion['display']}",
                        description=completion['description'],
                        code_snippet=current_line,
                        fix_snippet=current_line[:col_no] + completion['text'],
                        confidence=completion['confidence'],
                        priority='low',
                        created_at=datetime.now()
                    )
                    suggestions.append(suggestion)
        
        # Add file-level suggestions
        file_suggestions = await self._get_file_suggestions(content, language)
        suggestions.extend(file_suggestions)
        
        # Sort by priority and confidence
        suggestions.sort(key=lambda x: (
            {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[x.priority],
            x.confidence
        ), reverse=True)
        
        return suggestions[:self.config['max_suggestions_per_file']]
    
    async def auto_fix_suggestion(self, suggestion: LiveSuggestion) -> bool:
        """Automatically apply a suggestion fix"""
        if not suggestion.fix_snippet:
            return False
        
        try:
            with open(suggestion.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if suggestion.line_number is not None:
                if 0 <= suggestion.line_number < len(lines):
                    lines[suggestion.line_number] = suggestion.fix_snippet + '\n'
                    
                    with open(suggestion.file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    
                    logger.info(f"Applied fix to {suggestion.file_path}:{suggestion.line_number}")
                    return True
        except Exception as e:
            logger.error(f"Error applying fix: {e}")
        
        return False
    
    # Analysis methods
    async def _check_syntax(self, content: str, language: str) -> List[LiveSuggestion]:
        """Check for syntax errors"""
        issues = []
        
        if language == 'python':
            try:
                compile(content, '<string>', 'exec')
            except SyntaxError as e:
                issue = LiveSuggestion(
                    suggestion_id=f"syntax_{time.time()}",
                    file_path='<current>',
                    line_number=e.lineno - 1 if e.lineno else None,
                    suggestion_type='error',
                    title='Syntax Error',
                    description=str(e),
                    code_snippet=e.text,
                    fix_snippet=None,
                    confidence=1.0,
                    priority='critical',
                    created_at=datetime.now()
                )
                issues.append(issue)
        
        # Pattern-based syntax checking
        patterns = self.error_patterns.get(language, [])
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            for pattern_info in patterns:
                if re.search(pattern_info['pattern'], line):
                    issue = LiveSuggestion(
                        suggestion_id=f"pattern_{time.time()}_{i}",
                        file_path='<current>',
                        line_number=i,
                        suggestion_type=pattern_info['type'],
                        title=pattern_info['message'],
                        description=pattern_info.get('description', ''),
                        code_snippet=line,
                        fix_snippet=re.sub(
                            pattern_info['pattern'],
                            pattern_info.get('suggestion', ''),
                            line
                        ) if 'suggestion' in pattern_info else None,
                        confidence=0.8,
                        priority='medium',
                        created_at=datetime.now()
                    )
                    issues.append(issue)
        
        return issues
    
    async def _scan_security(self, content: str, language: str) -> List[LiveSuggestion]:
        """Scan for security vulnerabilities"""
        issues = []
        patterns = self.security_patterns.get(language, [])
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            for pattern_info in patterns:
                if re.search(pattern_info['pattern'], line):
                    issue = LiveSuggestion(
                        suggestion_id=f"security_{time.time()}_{i}",
                        file_path='<current>',
                        line_number=i,
                        suggestion_type='security',
                        title=pattern_info['message'],
                        description=f"Security {pattern_info['severity']}: {pattern_info.get('description', '')}",
                        code_snippet=line,
                        fix_snippet=pattern_info.get('suggestion'),
                        confidence=0.9,
                        priority=pattern_info.get('severity', 'high'),
                        created_at=datetime.now()
                    )
                    issues.append(issue)
        
        return issues
    
    async def _analyze_performance(self, content: str, language: str) -> List[LiveSuggestion]:
        """Analyze performance issues"""
        issues = []
        patterns = self.performance_patterns.get(language, [])
        
        # Pattern matching
        for pattern_info in patterns:
            matches = re.finditer(pattern_info['pattern'], content, re.MULTILINE | re.DOTALL)
            for match in matches:
                line_no = content[:match.start()].count('\n')
                issue = LiveSuggestion(
                    suggestion_id=f"perf_{time.time()}_{line_no}",
                    file_path='<current>',
                    line_number=line_no,
                    suggestion_type='performance',
                    title=pattern_info['message'],
                    description=pattern_info.get('suggestion', ''),
                    code_snippet=match.group(0),
                    fix_snippet=None,
                    confidence=0.7,
                    priority='medium',
                    created_at=datetime.now()
                )
                issues.append(issue)
        
        return issues
    
    async def _check_best_practices(self, content: str, language: str) -> List[LiveSuggestion]:
        """Check against coding best practices"""
        issues = []
        practices = self.best_practices.get(language, []) + self.best_practices.get('general', [])
        
        lines = content.split('\n')
        
        for practice in practices:
            if practice['check'] == 'function_length' and language == 'python':
                # Check function lengths
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_lines = node.end_lineno - node.lineno
                        if func_lines > practice['max_lines']:
                            issue = LiveSuggestion(
                                suggestion_id=f"practice_{time.time()}_{node.lineno}",
                                file_path='<current>',
                                line_number=node.lineno - 1,
                                suggestion_type='improvement',
                                title=f"Function '{node.name}' is too long ({func_lines} lines)",
                                description=practice['message'],
                                code_snippet=None,
                                fix_snippet=None,
                                confidence=0.8,
                                priority='low',
                                created_at=datetime.now()
                            )
                            issues.append(issue)
            
            elif practice['check'] == 'file_length':
                if len(lines) > practice['max_lines']:
                    issue = LiveSuggestion(
                        suggestion_id=f"practice_file_{time.time()}",
                        file_path='<current>',
                        line_number=None,
                        suggestion_type='improvement',
                        title=f"File is too long ({len(lines)} lines)",
                        description=practice['message'],
                        code_snippet=None,
                        fix_snippet=None,
                        confidence=0.7,
                        priority='low',
                        created_at=datetime.now()
                    )
                    issues.append(issue)
        
        return issues
    
    async def _calculate_metrics(self, content: str, language: str) -> Dict[str, Any]:
        """Calculate code quality metrics"""
        lines = content.split('\n')
        
        metrics = {
            'total_lines': len(lines),
            'non_empty_lines': len([l for l in lines if l.strip()]),
            'comment_lines': len([l for l in lines if l.strip().startswith(('#', '//', '/*'))]),
        }
        
        if language == 'python':
            try:
                tree = ast.parse(content)
                metrics['functions'] = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                metrics['classes'] = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
                metrics['imports'] = len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
            except (SyntaxError, ValueError, TypeError) as e:
                import logging
                logging.debug(f"Failed to parse Python AST for metrics: {e}")
                pass
        
        # Calculate ratios
        if metrics['non_empty_lines'] > 0:
            metrics['comment_ratio'] = metrics['comment_lines'] / metrics['non_empty_lines']
        else:
            metrics['comment_ratio'] = 0.0
        
        return metrics
    
    def _identify_strengths(self, content: str, language: str, issues: List[LiveSuggestion]) -> List[str]:
        """Identify positive aspects of the code"""
        strengths = []
        
        # Check for good practices
        if language == 'python':
            if 'from typing import' in content:
                strengths.append("Uses type hints for better code clarity")
            
            if re.search(r'""".*"""', content, re.DOTALL):
                strengths.append("Includes docstrings for documentation")
            
            if 'import logging' in content:
                strengths.append("Uses proper logging instead of print statements")
            
            try:
                tree = ast.parse(content)
                has_error_handling = any(isinstance(node, ast.Try) for node in ast.walk(tree))
                if has_error_handling:
                    strengths.append("Implements error handling")
            except (SyntaxError, ValueError, TypeError) as e:
                import logging
                logging.debug(f"Failed to parse Python AST for strengths analysis: {e}")
                pass
        
        # General strengths
        lines = content.split('\n')
        if len(lines) < 200:
            strengths.append("Maintains reasonable file size")
        
        critical_issues = [i for i in issues if i.priority == 'critical']
        if not critical_issues:
            strengths.append("No critical issues found")
        
        return strengths
    
    def _calculate_overall_score(self, issues: List[LiveSuggestion], metrics: Dict[str, Any]) -> float:
        """Calculate overall code quality score"""
        score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.priority == 'critical':
                score -= 10
            elif issue.priority == 'high':
                score -= 5
            elif issue.priority == 'medium':
                score -= 2
            else:
                score -= 0.5
        
        # Bonus for good metrics
        if metrics.get('comment_ratio', 0) > 0.1:
            score += 5
        
        # Ensure score is in valid range
        return max(0.0, min(100.0, score))
    
    async def _get_completions(self, partial_line: str, language: str, context_lines: List[str]) -> List[Dict[str, Any]]:
        """Get intelligent code completions"""
        completions = []
        
        # Simple keyword completions for demo
        if language == 'python':
            if partial_line.endswith('def '):
                completions.append({
                    'text': 'process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:',
                    'display': 'process_data(...)',
                    'description': 'Create a data processing method',
                    'confidence': 0.8
                })
            elif partial_line.endswith('import '):
                common_imports = ['os', 'sys', 'json', 'logging', 'pathlib']
                for imp in common_imports:
                    if imp not in '\n'.join(context_lines):
                        completions.append({
                            'text': imp,
                            'display': imp,
                            'description': f'Import {imp} module',
                            'confidence': 0.7
                        })
        
        return completions
    
    async def _get_file_suggestions(self, content: str, language: str) -> List[LiveSuggestion]:
        """Get file-level improvement suggestions"""
        suggestions = []
        
        # Missing imports suggestion
        if language == 'python':
            # Check for common patterns without imports
            if 'Path(' in content and 'from pathlib import Path' not in content:
                suggestions.append(LiveSuggestion(
                    suggestion_id=f"import_{time.time()}",
                    file_path='<current>',
                    line_number=0,
                    suggestion_type='improvement',
                    title='Missing import: pathlib.Path',
                    description='Add "from pathlib import Path" at the top',
                    code_snippet=None,
                    fix_snippet='from pathlib import Path',
                    confidence=0.9,
                    priority='medium',
                    created_at=datetime.now()
                ))
        
        return suggestions
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rb': 'ruby',
            '.cpp': 'cpp',
            '.c': 'c',
        }
        
        return ext_map.get(file_path.suffix, 'unknown')
    
    async def _process_suggestions(self):
        """Process queued suggestions"""
        while True:
            try:
                if self.suggestion_queue:
                    suggestion = self.suggestion_queue.popleft()
                    
                    # Notify handlers
                    for handler in self.suggestion_handlers:
                        await handler(suggestion)
                
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing suggestions: {e}")
    
    def add_suggestion_handler(self, handler: Callable):
        """Add a handler for new suggestions"""
        self.suggestion_handlers.append(handler)
    
    def handle_code_change(self, change: CodeChange):
        """Handle a code change event"""
        asyncio.create_task(self._analyze_change(change))
    
    async def _analyze_change(self, change: CodeChange):
        """Analyze a code change and generate suggestions"""
        if change.change_type == 'deleted':
            return
        
        # Quick analysis of the change
        review = await self.analyze_file(change.file_path, change.new_content)
        
        # Add high-priority issues to suggestion queue
        for issue in review.issues:
            if issue.confidence >= self.config['confidence_threshold']:
                self.suggestion_queue.append(issue)

class CodeChangeHandler(FileSystemEventHandler):
    """Handles file system events for real-time monitoring"""
    
    def __init__(self, assistant: RealTimeAssistant):
        self.assistant = assistant
        self.last_change_times = {}
        
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if file should be monitored
        if file_path.suffix not in self.assistant.config['watch_extensions']:
            return
        
        # Debounce rapid changes
        current_time = time.time()
        last_time = self.last_change_times.get(str(file_path), 0)
        
        if current_time - last_time < self.assistant.config['auto_suggest_delay']:
            return
        
        self.last_change_times[str(file_path)] = current_time
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            import logging
            logging.debug(f"Failed to read file {file_path} for file change handling: {e}")
            return
        
        # Get old content from cache
        old_content = self.assistant.file_cache.get(str(file_path), '')
        
        # Create change event
        change = CodeChange(
            file_path=str(file_path),
            change_type='modified',
            timestamp=datetime.now(),
            old_content=old_content,
            new_content=new_content,
            line_changes=self._get_line_changes(old_content, new_content)
        )
        
        # Update cache
        self.assistant.file_cache[str(file_path)] = new_content
        
        # Handle change
        self.assistant.handle_code_change(change)
    
    def _get_line_changes(self, old_content: str, new_content: str) -> List[Tuple[int, str, str]]:
        """Get line-by-line changes"""
        old_lines = old_content.split('\n') if old_content else []
        new_lines = new_content.split('\n') if new_content else []
        
        changes = []
        differ = difflib.unified_diff(old_lines, new_lines, lineterm='')
        
        line_no = 0
        for line in differ:
            if line.startswith('@@'):
                # Parse line number
                match = re.match(r'@@ -\d+,?\d* \+(\d+)', line)
                if match:
                    line_no = int(match.group(1)) - 1
            elif line.startswith('-') and not line.startswith('---'):
                changes.append((line_no, line[1:], ''))
            elif line.startswith('+') and not line.startswith('+++'):
                changes.append((line_no, '', line[1:]))
                line_no += 1
            else:
                line_no += 1
        
        return changes

async def demo_real_time_assistant():
    """Demo the real-time assistant"""
    assistant = RealTimeAssistant()
    
    print("🤖 Real-Time AI Assistant Demo")
    print("=" * 50)
    
    # Example Python code with issues
    sample_code = '''
def process_data(data):
    print("Processing data...")
    
    try:
        result = []
        for item in data:
            for subitem in item:  # Nested loop
                result.append(subitem)
    except:  # Bare except
        pass
    
    password = "admin123"  # Security issue
    
    if data == None:  # Should use 'is None'
        return None
    
    eval(user_input)  # Critical security issue
    
    return result
'''
    
    # Analyze the code
    print("\n📝 Analyzing sample code...")
    review = await assistant.analyze_file("sample.py", sample_code)
    
    print(f"\n📊 Overall Score: {review.overall_score:.1f}/100")
    
    print("\n❌ Issues Found:")
    for issue in review.issues:
        icon = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(issue.priority, '⚪')
        
        print(f"\n{icon} [{issue.priority.upper()}] {issue.title}")
        if issue.line_number is not None:
            print(f"   Line {issue.line_number + 1}: {issue.code_snippet}")
        print(f"   {issue.description}")
        if issue.fix_snippet:
            print(f"   Suggested fix: {issue.fix_snippet}")
    
    print("\n✅ Strengths:")
    for strength in review.strengths:
        print(f"   • {strength}")
    
    print("\n📈 Metrics:")
    for metric, value in review.metrics.items():
        print(f"   {metric}: {value}")
    
    # Demo live suggestions
    print("\n\n💡 Getting live suggestions...")
    suggestions = await assistant.get_live_suggestions("sample.py", cursor_position=(2, 8))
    
    print(f"Found {len(suggestions)} suggestions:")
    for suggestion in suggestions[:3]:
        print(f"\n   • {suggestion.title}")
        print(f"     {suggestion.description}")

if __name__ == "__main__":
    asyncio.run(demo_real_time_assistant())