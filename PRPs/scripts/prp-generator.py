#!/usr/bin/env python3
"""
Intelligent PRP Generator
Analyzes codebase and generates context-aware PRPs
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import ast
import re

class PRPGenerator:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.codebase_patterns = {}
        self.dependencies = set()
        
    def analyze_codebase(self):
        """Analyze codebase for patterns and dependencies"""
        patterns = {
            'components': [],
            'utilities': [],
            'apis': [],
            'tests': [],
            'configs': []
        }
        
        for file_path in self.project_root.rglob("*.py"):
            if self._should_analyze(file_path):
                patterns.update(self._extract_patterns(file_path))
                
        return patterns
    
    def _should_analyze(self, file_path):
        """Determine if file should be analyzed"""
        exclude_dirs = {'.git', 'node_modules', '__pycache__', '.venv'}
        return not any(part in exclude_dirs for part in file_path.parts)
    
    def _extract_patterns(self, file_path):
        """Extract code patterns from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract imports, classes, functions
            tree = ast.parse(content)
            patterns = {
                'imports': [node.names[0].name for node in ast.walk(tree) 
                           if isinstance(node, ast.Import)],
                'classes': [node.name for node in ast.walk(tree) 
                           if isinstance(node, ast.ClassDef)],
                'functions': [node.name for node in ast.walk(tree) 
                             if isinstance(node, ast.FunctionDef)]
            }
            return patterns
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, SyntaxError) as e:
            import logging
            logging.debug(f"Failed to analyze codebase patterns: {e}")
            return {}
    
    def generate_prp(self, feature_name, requirements, complexity=5):
        """Generate intelligent PRP"""
        prp_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        # Analyze codebase for similar patterns
        patterns = self.analyze_codebase()
        
        # Generate PRP content
        prp_content = self._build_prp_content(
            prp_id, timestamp, feature_name, requirements, complexity, patterns
        )
        
        # Save PRP
        prp_path = self.project_root / "PRPs" / f"{feature_name.lower().replace(' ', '-')}.md"
        with open(prp_path, 'w') as f:
            f.write(prp_content)
            
        return prp_path
    
    def _build_prp_content(self, prp_id, timestamp, feature_name, requirements, complexity, patterns):
        """Build PRP content with intelligence"""
        return f"""# PRP: {feature_name}

## Meta Information
- **PRP ID**: {prp_id}
- **Created**: {timestamp}
- **Complexity Score**: {complexity}/10
- **Estimated Implementation Time**: {complexity * 2} hours

## 🎯 Feature Specification
### Core Requirement
{requirements}

### Success Metrics
- [ ] Functional: Feature works as specified
- [ ] Performance: Meets performance benchmarks
- [ ] UX: Provides good user experience

## 🔍 Codebase Intelligence
### Pattern Analysis
```markdown
Similar patterns found in codebase:
{self._format_patterns(patterns)}
```

## 🧠 Implementation Strategy
### Approach Rationale
Based on codebase analysis, following existing patterns for consistency.

### Risk Mitigation
- **High Risk**: Breaking existing functionality → Comprehensive testing
- **Medium Risk**: Performance impact → Benchmarking

## 📋 Execution Blueprint
### Phase 1: Foundation
- [ ] Create base structure following existing patterns
- [ ] Set up configuration and dependencies

### Phase 2: Core Implementation
- [ ] Implement core functionality
- [ ] Add error handling and validation

### Phase 3: Integration & Testing
- [ ] Write comprehensive tests
- [ ] Integrate with existing systems
- [ ] Performance optimization

## 🔬 Validation Matrix
### Automated Tests
```bash
# Run existing test suite
python -m pytest

# Run specific feature tests
python -m pytest tests/test_{feature_name.lower().replace(' ', '_')}.py
```

### Manual Verification
- [ ] Feature works in development environment
- [ ] Feature works in production-like environment

## 🎯 Confidence Score: {min(complexity + 2, 10)}/10
**Reasoning**: Based on codebase analysis and pattern matching

## 🔄 Post-Implementation
### Monitoring
- Performance metrics
- Error rates
- User adoption

### Future Enhancements
- Additional features based on user feedback
- Performance optimizations
"""

    def _format_patterns(self, patterns):
        """Format patterns for display"""
        if not patterns:
            return "No similar patterns found"
            
        formatted = []
        for category, items in patterns.items():
            if items:
                formatted.append(f"- {category.title()}: {', '.join(items[:3])}")
        
        return '\n'.join(formatted) if formatted else "No patterns detected"

if __name__ == "__main__":
    generator = PRPGenerator()
    
    # Example usage
    feature_name = input("Feature name: ")
    requirements = input("Requirements: ")
    complexity = int(input("Complexity (1-10): ") or "5")
    
    prp_path = generator.generate_prp(feature_name, requirements, complexity)
    print(f"PRP generated: {prp_path}")