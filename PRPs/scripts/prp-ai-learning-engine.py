#!/usr/bin/env python3
"""
PRP-12Factor AI-Powered Learning & Recommendation Engine
Revolutionary AI system that learns from user actions and provides intelligent recommendations
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import pickle
import logging
from collections import defaultdict, Counter
import re
import ast
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class UserAction:
    """User action for learning"""
    action_type: str  # 'fix_applied', 'fix_rejected', 'manual_fix', 'feedback_positive', 'feedback_negative'
    factor: str
    context: Dict[str, Any]
    timestamp: datetime
    user_id: str = "default"
    session_id: str = ""

@dataclass
class LearningPattern:
    """Detected learning pattern"""
    pattern_id: str
    pattern_type: str  # 'user_preference', 'fix_effectiveness', 'timing_pattern', 'context_pattern'
    factor: str
    description: str
    confidence: float
    metadata: Dict[str, Any]
    discovered_at: datetime
    usage_count: int = 0

@dataclass
class SmartRecommendation:
    """AI-generated recommendation"""
    recommendation_id: str
    factor: str
    priority: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: str
    rationale: str
    confidence: float
    estimated_effort: str  # 'low', 'medium', 'high'
    estimated_impact: float  # 0.0 to 1.0
    auto_fixable: bool
    learning_basis: List[str]  # Pattern IDs that influenced this recommendation
    generated_at: datetime

class AILearningEngine:
    """Revolutionary AI learning engine for 12-Factor compliance"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.learning_data_file = self.project_root / "PRPs" / "analytics" / "learning-data.json"
        self.models_dir = self.project_root / "PRPs" / "analytics" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Learning data
        self.user_actions: List[UserAction] = []
        self.patterns: List[LearningPattern] = []
        self.recommendations: List[SmartRecommendation] = []
        
        # ML models (simplified for this implementation)
        self.preference_model = {}
        self.effectiveness_model = {}
        self.timing_model = {}
        
        # Learning configuration
        self.config = {
            "learning_rate": 0.1,
            "pattern_confidence_threshold": 0.7,
            "recommendation_refresh_hours": 6,
            "max_patterns": 100,
            "feedback_weight": 0.8,
            "temporal_decay": 0.95  # Older actions have less weight
        }
        
        # Load existing data
        self._load_learning_data()
        
        # Initialize feature extractors
        self.feature_extractors = {
            'code_complexity': self._extract_code_complexity_features,
            'file_patterns': self._extract_file_pattern_features,
            'dependency_patterns': self._extract_dependency_features,
            'config_patterns': self._extract_config_features,
            'temporal_patterns': self._extract_temporal_features,
            'semantic_analysis': self._extract_semantic_features,
            'performance_patterns': self._extract_performance_features,
            'security_patterns': self._extract_security_features,
            'architecture_patterns': self._extract_architecture_features
        }
        
        logger.info("AI Learning Engine initialized with {len(self.user_actions)} historical actions")
    
    def _load_learning_data(self):
        """Load historical learning data"""
        if not self.learning_data_file.exists():
            return
        
        try:
            with open(self.learning_data_file, 'r') as f:
                data = json.load(f)
            
            # Load user actions
            for action_data in data.get('user_actions', []):
                action = UserAction(
                    action_type=action_data['action_type'],
                    factor=action_data['factor'],
                    context=action_data['context'],
                    timestamp=datetime.fromisoformat(action_data['timestamp']),
                    user_id=action_data.get('user_id', 'default'),
                    session_id=action_data.get('session_id', '')
                )
                self.user_actions.append(action)
            
            # Load patterns
            for pattern_data in data.get('patterns', []):
                pattern = LearningPattern(
                    pattern_id=pattern_data['pattern_id'],
                    pattern_type=pattern_data['pattern_type'],
                    factor=pattern_data['factor'],
                    description=pattern_data['description'],
                    confidence=pattern_data['confidence'],
                    metadata=pattern_data['metadata'],
                    discovered_at=datetime.fromisoformat(pattern_data['discovered_at']),
                    usage_count=pattern_data.get('usage_count', 0)
                )
                self.patterns.append(pattern)
            
            # Load models
            self.preference_model = data.get('preference_model', {})
            self.effectiveness_model = data.get('effectiveness_model', {})
            self.timing_model = data.get('timing_model', {})
            
        except Exception as e:
            logger.error(f"Error loading learning data: {e}")
    
    def _save_learning_data(self):
        """Save learning data to disk"""
        try:
            data = {
                'user_actions': [
                    {
                        'action_type': action.action_type,
                        'factor': action.factor,
                        'context': action.context,
                        'timestamp': action.timestamp.isoformat(),
                        'user_id': action.user_id,
                        'session_id': action.session_id
                    }
                    for action in self.user_actions[-1000:]  # Keep last 1000 actions
                ],
                'patterns': [
                    {
                        'pattern_id': pattern.pattern_id,
                        'pattern_type': pattern.pattern_type,
                        'factor': pattern.factor,
                        'description': pattern.description,
                        'confidence': pattern.confidence,
                        'metadata': pattern.metadata,
                        'discovered_at': pattern.discovered_at.isoformat(),
                        'usage_count': pattern.usage_count
                    }
                    for pattern in self.patterns
                ],
                'preference_model': self.preference_model,
                'effectiveness_model': self.effectiveness_model,
                'timing_model': self.timing_model,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.learning_data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def record_user_action(self, action: UserAction):
        """Record a user action for learning"""
        self.user_actions.append(action)
        
        # Trigger incremental learning
        self._update_models_incremental(action)
        
        # Check for new patterns
        new_patterns = self._detect_patterns_incremental(action)
        for pattern in new_patterns:
            self.patterns.append(pattern)
            logger.info(f"New pattern detected: {pattern.description}")
        
        # Generate new recommendations if needed
        if len(self.user_actions) % 10 == 0:  # Every 10 actions
            self._refresh_recommendations()
        
        # Save periodically
        if len(self.user_actions) % 50 == 0:  # Every 50 actions
            self._save_learning_data()
    
    def _update_models_incremental(self, action: UserAction):
        """Update ML models incrementally"""
        # Update preference model
        if action.action_type in ['fix_applied', 'fix_rejected']:
            factor_prefs = self.preference_model.setdefault(action.factor, {})
            
            # Track fix acceptance rate
            if 'fix_acceptance' not in factor_prefs:
                factor_prefs['fix_acceptance'] = {'accepted': 0, 'rejected': 0}
            
            if action.action_type == 'fix_applied':
                factor_prefs['fix_acceptance']['accepted'] += 1
            else:
                factor_prefs['fix_acceptance']['rejected'] += 1
            
            # Track context preferences
            if 'context_preferences' not in factor_prefs:
                factor_prefs['context_preferences'] = {}
            
            for key, value in action.context.items():
                if key not in factor_prefs['context_preferences']:
                    factor_prefs['context_preferences'][key] = defaultdict(int)
                factor_prefs['context_preferences'][key][str(value)] += 1
        
        # Update effectiveness model
        if action.action_type == 'fix_applied':
            effectiveness_key = f"{action.factor}_{action.context.get('fix_type', 'unknown')}"
            if effectiveness_key not in self.effectiveness_model:
                self.effectiveness_model[effectiveness_key] = {'successes': 0, 'total': 0}
            
            self.effectiveness_model[effectiveness_key]['total'] += 1
            
            # Assume success unless explicitly marked as failed
            if action.context.get('success', True):
                self.effectiveness_model[effectiveness_key]['successes'] += 1
        
        # Update timing model
        hour = action.timestamp.hour
        day_of_week = action.timestamp.weekday()
        timing_key = f"{action.factor}_{action.action_type}"
        
        if timing_key not in self.timing_model:
            self.timing_model[timing_key] = {'hour_distribution': [0] * 24, 'day_distribution': [0] * 7}
        
        self.timing_model[timing_key]['hour_distribution'][hour] += 1
        self.timing_model[timing_key]['day_distribution'][day_of_week] += 1
    
    def _detect_patterns_incremental(self, action: UserAction) -> List[LearningPattern]:
        """Detect new patterns based on recent action"""
        new_patterns = []
        
        # Pattern 1: Consistent preferences
        if len(self.user_actions) >= 5:
            recent_actions = [a for a in self.user_actions[-10:] if a.factor == action.factor]
            if len(recent_actions) >= 3:
                # Check for consistent fix rejection
                rejections = [a for a in recent_actions if a.action_type == 'fix_rejected']
                if len(rejections) >= 2:
                    pattern = LearningPattern(
                        pattern_id=f"rejection_pattern_{action.factor}_{datetime.now().timestamp()}",
                        pattern_type="user_preference",
                        factor=action.factor,
                        description=f"User consistently rejects auto-fixes for {action.factor}",
                        confidence=len(rejections) / len(recent_actions),
                        metadata={'rejection_rate': len(rejections) / len(recent_actions)},
                        discovered_at=datetime.now()
                    )
                    new_patterns.append(pattern)
        
        # Pattern 2: Time-based patterns
        if action.action_type == 'fix_applied':
            hour = action.timestamp.hour
            similar_time_actions = [
                a for a in self.user_actions
                if abs(a.timestamp.hour - hour) <= 1 and a.action_type == 'fix_applied'
            ]
            
            if len(similar_time_actions) >= 5:
                pattern = LearningPattern(
                    pattern_id=f"timing_pattern_{hour}_{datetime.now().timestamp()}",
                    pattern_type="timing_pattern",
                    factor="general",
                    description=f"User most active around {hour}:00",
                    confidence=min(len(similar_time_actions) / 10, 0.9),
                    metadata={'preferred_hour': hour, 'action_count': len(similar_time_actions)},
                    discovered_at=datetime.now()
                )
                new_patterns.append(pattern)
        
        # Pattern 3: Context-based patterns
        if action.context.get('file_path'):
            file_ext = Path(action.context['file_path']).suffix
            similar_file_actions = [
                a for a in self.user_actions
                if a.context.get('file_path', '').endswith(file_ext)
            ]
            
            if len(similar_file_actions) >= 3:
                success_rate = len([a for a in similar_file_actions if a.context.get('success', True)]) / len(similar_file_actions)
                
                if success_rate > 0.8:
                    pattern = LearningPattern(
                        pattern_id=f"file_pattern_{file_ext}_{datetime.now().timestamp()}",
                        pattern_type="context_pattern",
                        factor=action.factor,
                        description=f"High success rate for {file_ext} files in {action.factor}",
                        confidence=success_rate,
                        metadata={'file_extension': file_ext, 'success_rate': success_rate},
                        discovered_at=datetime.now()
                    )
                    new_patterns.append(pattern)
        
        return new_patterns
    
    def _refresh_recommendations(self):
        """Generate new AI recommendations based on learned patterns"""
        new_recommendations = []
        
        # Clear old recommendations
        cutoff = datetime.now() - timedelta(hours=self.config['recommendation_refresh_hours'])
        self.recommendations = [r for r in self.recommendations if r.generated_at >= cutoff]
        
        # Generate recommendations for each factor
        for factor in ['codebase', 'dependencies', 'config', 'backing_services', 'build_release_run',
                       'processes', 'port_binding', 'concurrency', 'disposability', 'dev_prod_parity',
                       'logs', 'admin_processes']:
            
            recommendations = self._generate_factor_recommendations(factor)
            new_recommendations.extend(recommendations)
        
        # Add pattern-based recommendations
        pattern_recommendations = self._generate_pattern_recommendations()
        new_recommendations.extend(pattern_recommendations)
        
        # Sort by priority and confidence
        new_recommendations.sort(key=lambda r: (
            {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[r.priority],
            r.confidence
        ), reverse=True)
        
        # Keep top 10
        self.recommendations.extend(new_recommendations[:10])
        
        logger.info(f"Generated {len(new_recommendations)} new recommendations")
    
    def _generate_factor_recommendations(self, factor: str) -> List[SmartRecommendation]:
        """Generate recommendations for a specific factor"""
        recommendations = []
        
        # Get user preferences for this factor
        factor_prefs = self.preference_model.get(factor, {})
        fix_acceptance = factor_prefs.get('fix_acceptance', {})
        
        if fix_acceptance:
            total = fix_acceptance.get('accepted', 0) + fix_acceptance.get('rejected', 0)
            if total > 0:
                acceptance_rate = fix_acceptance.get('accepted', 0) / total
                
                if acceptance_rate < 0.3:
                    # User frequently rejects fixes - recommend manual approach
                    recommendation = SmartRecommendation(
                        recommendation_id=f"manual_approach_{factor}_{datetime.now().timestamp()}",
                        factor=factor,
                        priority="medium",
                        title=f"Consider manual {factor} improvements",
                        description=f"You've rejected {fix_acceptance.get('rejected', 0)} automatic fixes for {factor}. Manual review might be more effective.",
                        rationale=f"Low auto-fix acceptance rate ({acceptance_rate:.1%}) suggests preference for manual control",
                        confidence=1.0 - acceptance_rate,
                        estimated_effort="medium",
                        estimated_impact=0.6,
                        auto_fixable=False,
                        learning_basis=[f"user_preference_{factor}"],
                        generated_at=datetime.now()
                    )
                    recommendations.append(recommendation)
                
                elif acceptance_rate > 0.8:
                    # User accepts most fixes - recommend more aggressive auto-fixing
                    recommendation = SmartRecommendation(
                        recommendation_id=f"auto_fix_{factor}_{datetime.now().timestamp()}",
                        factor=factor,
                        priority="low",
                        title=f"Enable auto-fix for {factor} issues",
                        description=f"You've accepted {fix_acceptance.get('accepted', 0)} of {total} auto-fixes. Consider enabling automatic fixing for this factor.",
                        rationale=f"High auto-fix acceptance rate ({acceptance_rate:.1%}) indicates trust in automated solutions",
                        confidence=acceptance_rate,
                        estimated_effort="low",
                        estimated_impact=0.4,
                        auto_fixable=True,
                        learning_basis=[f"user_preference_{factor}"],
                        generated_at=datetime.now()
                    )
                    recommendations.append(recommendation)
        
        # Check effectiveness patterns
        for effectiveness_key, stats in self.effectiveness_model.items():
            if effectiveness_key.startswith(factor):
                if stats['total'] >= 3:
                    success_rate = stats['successes'] / stats['total']
                    
                    if success_rate < 0.5:
                        fix_type = effectiveness_key.split('_', 1)[1] if '_' in effectiveness_key else 'unknown'
                        recommendation = SmartRecommendation(
                            recommendation_id=f"avoid_fix_{effectiveness_key}_{datetime.now().timestamp()}",
                            factor=factor,
                            priority="medium",
                            title=f"Review {fix_type} approach for {factor}",
                            description=f"The {fix_type} approach has low success rate ({success_rate:.1%}) for {factor} issues.",
                            rationale=f"Historical data shows {stats['successes']}/{stats['total']} successes",
                            confidence=1.0 - success_rate,
                            estimated_effort="medium",
                            estimated_impact=0.7,
                            auto_fixable=False,
                            learning_basis=[f"effectiveness_{effectiveness_key}"],
                            generated_at=datetime.now()
                        )
                        recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_pattern_recommendations(self) -> List[SmartRecommendation]:
        """Generate recommendations based on detected patterns"""
        recommendations = []
        
        for pattern in self.patterns:
            if pattern.confidence < self.config['pattern_confidence_threshold']:
                continue
            
            if pattern.pattern_type == "timing_pattern":
                preferred_hour = pattern.metadata.get('preferred_hour')
                if preferred_hour is not None:
                    recommendation = SmartRecommendation(
                        recommendation_id=f"timing_rec_{pattern.pattern_id}",
                        factor="general",
                        priority="low",
                        title="Optimize monitoring schedule",
                        description=f"You're most active around {preferred_hour}:00. Consider scheduling important compliance checks during this time.",
                        rationale=f"Pattern shows {pattern.metadata.get('action_count', 0)} actions around this time",
                        confidence=pattern.confidence,
                        estimated_effort="low",
                        estimated_impact=0.3,
                        auto_fixable=True,
                        learning_basis=[pattern.pattern_id],
                        generated_at=datetime.now()
                    )
                    recommendations.append(recommendation)
            
            elif pattern.pattern_type == "context_pattern":
                file_ext = pattern.metadata.get('file_extension')
                success_rate = pattern.metadata.get('success_rate', 0)
                
                if file_ext and success_rate > 0.8:
                    recommendation = SmartRecommendation(
                        recommendation_id=f"context_rec_{pattern.pattern_id}",
                        factor=pattern.factor,
                        priority="medium",
                        title=f"Prioritize {file_ext} files for {pattern.factor}",
                        description=f"You have high success rate ({success_rate:.1%}) with {file_ext} files in {pattern.factor} improvements.",
                        rationale="Historical success pattern suggests focusing on these file types first",
                        confidence=pattern.confidence,
                        estimated_effort="low",
                        estimated_impact=0.6,
                        auto_fixable=True,
                        learning_basis=[pattern.pattern_id],
                        generated_at=datetime.now()
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    def get_recommendations(self, factor: Optional[str] = None, limit: int = 5) -> List[SmartRecommendation]:
        """Get current recommendations, optionally filtered by factor"""
        recommendations = self.recommendations
        
        if factor:
            recommendations = [r for r in recommendations if r.factor == factor or r.factor == "general"]
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda r: (
            {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[r.priority],
            r.confidence
        ), reverse=True)
        
        return recommendations[:limit]
    
    def provide_feedback(self, recommendation_id: str, feedback: str, rating: float):
        """Provide feedback on a recommendation"""
        feedback_action = UserAction(
            action_type=f"feedback_{feedback}",
            factor="ai_system",
            context={
                'recommendation_id': recommendation_id,
                'rating': rating,
                'feedback_text': feedback
            },
            timestamp=datetime.now()
        )
        
        self.record_user_action(feedback_action)
        
        # Update recommendation confidence based on feedback
        for rec in self.recommendations:
            if rec.recommendation_id == recommendation_id:
                # Adjust confidence based on rating
                weight = self.config['feedback_weight']
                rec.confidence = rec.confidence * (1 - weight) + (rating / 5.0) * weight
                break
    
    def analyze_learning_progress(self) -> Dict[str, Any]:
        """Analyze learning progress and provide insights"""
        if not self.user_actions:
            return {"status": "no_data", "message": "No learning data available"}
        
        # Time range analysis
        first_action = min(self.user_actions, key=lambda a: a.timestamp)
        last_action = max(self.user_actions, key=lambda a: a.timestamp)
        learning_period = (last_action.timestamp - first_action.timestamp).days
        
        # Action analysis
        action_counts = Counter(action.action_type for action in self.user_actions)
        factor_activity = Counter(action.factor for action in self.user_actions)
        
        # Pattern analysis
        pattern_types = Counter(pattern.pattern_type for pattern in self.patterns)
        high_confidence_patterns = len([p for p in self.patterns if p.confidence >= 0.8])
        
        # Recommendation analysis
        active_recommendations = len(self.recommendations)
        high_priority_recs = len([r for r in self.recommendations if r.priority in ['critical', 'high']])
        
        # Calculate learning effectiveness
        fix_applied_count = action_counts.get('fix_applied', 0)
        fix_rejected_count = action_counts.get('fix_rejected', 0)
        total_fixes = fix_applied_count + fix_rejected_count
        
        learning_effectiveness = 0.0
        if total_fixes > 0:
            # Base effectiveness on fix acceptance and pattern discovery
            acceptance_rate = fix_applied_count / total_fixes
            pattern_rate = len(self.patterns) / max(len(self.user_actions), 1)
            learning_effectiveness = (acceptance_rate * 0.6 + pattern_rate * 0.4) * 100
        
        return {
            "status": "active",
            "learning_period_days": learning_period,
            "total_actions": len(self.user_actions),
            "action_breakdown": dict(action_counts),
            "most_active_factor": factor_activity.most_common(1)[0][0] if factor_activity else "none",
            "patterns_discovered": len(self.patterns),
            "pattern_types": dict(pattern_types),
            "high_confidence_patterns": high_confidence_patterns,
            "active_recommendations": active_recommendations,
            "high_priority_recommendations": high_priority_recs,
            "learning_effectiveness": learning_effectiveness,
            "recommendations_per_factor": {
                factor: len([r for r in self.recommendations if r.factor == factor])
                for factor in factor_activity.keys()
            }
        }
    
    # Enhanced Feature extraction methods with contextual understanding
    def _extract_code_complexity_features(self, file_path: str) -> Dict[str, Any]:
        """Extract advanced code complexity features with semantic analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Basic metrics
            features = {
                'line_count': len(lines),
                'non_empty_lines': len([line for line in lines if line.strip()]),
                'comment_lines': len([line for line in lines if line.strip().startswith(('#', '//', '/*', '*'))]),
                'function_count': len(re.findall(r'(def|function|func|fn)\s+\w+', content)),
                'class_count': len(re.findall(r'(class|interface|struct)\s+\w+', content)),
                'import_count': len(re.findall(r'(import|from\s+\w+\s+import|require|use)\s+', content)),
            }
            
            # Advanced semantic analysis
            features.update(self._analyze_code_patterns(content, file_path))
            features.update(self._analyze_code_quality(content))
            features.update(self._detect_architectural_patterns(content))
            
            # Calculate composite complexity score
            complexity_factors = [
                features['line_count'] / 500,  # Line complexity
                features.get('cyclomatic_complexity', 0) / 10,  # Cyclomatic complexity
                features.get('nesting_depth', 0) / 5,  # Nesting complexity
                features.get('coupling_score', 0),  # Coupling complexity
            ]
            features['complexity_score'] = min(sum(complexity_factors) / len(complexity_factors), 1.0)
            
            return features
        except Exception as e:
            logger.error(f"Error extracting code complexity: {e}")
            return {'error': True, 'error_message': str(e)}
    
    def _extract_file_pattern_features(self, file_path: str) -> Dict[str, Any]:
        """Extract file pattern features"""
        path = Path(file_path)
        return {
            'extension': path.suffix,
            'name_length': len(path.name),
            'depth': len(path.parts),
            'has_numbers': bool(re.search(r'\d', path.name)),
            'has_special_chars': bool(re.search(r'[^a-zA-Z0-9._-]', path.name))
        }
    
    def _extract_dependency_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract dependency-related features"""
        features = {}
        
        # Check for common dependency files
        dep_files = ['requirements.txt', 'package.json', 'go.mod', 'Pipfile']
        for dep_file in dep_files:
            file_path = self.project_root / dep_file
            if file_path.exists():
                features[f'has_{dep_file}'] = True
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        features[f'{dep_file}_lines'] = len(content.split('\n'))
                except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                    import logging
                    logging.debug(f"Failed to read dependency file {file_path}: {e}")
                    pass
            else:
                features[f'has_{dep_file}'] = False
        
        return features
    
    def _extract_config_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract configuration-related features"""
        features = {}
        
        # Check for environment files
        env_files = ['.env', '.env.example', '.env.local', '.env.production']
        for env_file in env_files:
            file_path = self.project_root / env_file
            features[f'has_{env_file.replace(".", "_")}'] = file_path.exists()
        
        # Check for hardcoded values in Python files
        hardcoded_count = 0
        python_files = list(self.project_root.rglob('*.py'))[:10]  # Limit for performance
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'localhost' in content or '127.0.0.1' in content:
                        hardcoded_count += 1
            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                import logging
                logging.debug(f"Failed to read Python file {py_file} for hardcoded values check: {e}")
                pass
        
        features['hardcoded_values_found'] = hardcoded_count
        return features
    
    def _extract_temporal_features(self, timestamp: datetime) -> Dict[str, Any]:
        """Extract temporal features"""
        return {
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'is_weekend': timestamp.weekday() >= 5,
            'is_business_hours': 9 <= timestamp.hour <= 17,
            'month': timestamp.month,
            'quarter': (timestamp.month - 1) // 3 + 1
        }
    
    def _analyze_code_patterns(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze code patterns and anti-patterns"""
        patterns = {
            'has_error_handling': bool(re.search(r'(try|catch|except|finally|rescue)', content)),
            'has_logging': bool(re.search(r'(log|logger|logging|console\.log|print)', content)),
            'has_tests': bool(re.search(r'(test_|_test|Test|describe|it\(|assert|expect)', content)),
            'has_documentation': bool(re.search(r'("""[^"]+"""|/\*\*[^*]+\*/|///)', content)),
            'uses_async': bool(re.search(r'(async|await|Promise|Future|coroutine)', content)),
            'uses_types': bool(re.search(r'(: \w+|-> \w+|<\w+>|interface|type\s+\w+)', content)),
        }
        
        # Detect common anti-patterns
        anti_patterns = {
            'hardcoded_values': len(re.findall(r'["\']\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}["\']|localhost|password\s*=\s*["\'][^"\'
]+["\']', content)),
            'global_variables': len(re.findall(r'(global\s+\w+|window\.\w+\s*=|GLOBALS)', content)),
            'long_functions': len([m for m in re.finditer(r'(def|function|func)\s+\w+', content) if self._estimate_function_length(content, m.start()) > 50]),
            'deep_nesting': self._calculate_max_nesting_depth(content),
            'duplicate_code': self._detect_duplicate_patterns(content),
        }
        
        patterns['anti_pattern_score'] = sum(1 for v in anti_patterns.values() if v > 0) / len(anti_patterns)
        patterns.update({f'anti_{k}': v for k, v in anti_patterns.items()})
        
        return patterns
    
    def _analyze_code_quality(self, content: str) -> Dict[str, Any]:
        """Analyze code quality metrics"""
        lines = content.split('\n')
        
        # Calculate cyclomatic complexity (simplified)
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'case', 'catch', 'except']
        cyclomatic_complexity = 1  # Base complexity
        for line in lines:
            for keyword in decision_keywords:
                if re.search(rf'\b{keyword}\b', line):
                    cyclomatic_complexity += 1
        
        # Code style consistency
        indent_style = self._detect_indent_style(lines)
        naming_conventions = self._analyze_naming_conventions(content)
        
        return {
            'cyclomatic_complexity': cyclomatic_complexity,
            'average_line_length': sum(len(line) for line in lines) / max(len(lines), 1),
            'max_line_length': max((len(line) for line in lines), default=0),
            'indent_consistency': indent_style['consistency_score'],
            'naming_consistency': naming_conventions['consistency_score'],
            'code_to_comment_ratio': len([l for l in lines if l.strip() and not l.strip().startswith(('#', '//'))])
                                     / max(len([l for l in lines if l.strip().startswith(('#', '//'))]), 1),
        }
    
    def _detect_architectural_patterns(self, content: str) -> Dict[str, Any]:
        """Detect architectural patterns in code"""
        patterns = {
            'mvc_pattern': self._detect_mvc_pattern(content),
            'singleton_pattern': bool(re.search(r'(getInstance|_instance|Singleton)', content)),
            'factory_pattern': bool(re.search(r'(Factory|create\w+|build\w+)', content)),
            'observer_pattern': bool(re.search(r'(Observer|Listener|EventEmitter|subscribe|notify)', content)),
            'repository_pattern': bool(re.search(r'(Repository|\w+Repo|DataAccess)', content)),
            'dependency_injection': bool(re.search(r'(inject|@Inject|Container|ServiceProvider)', content)),
        }
        
        # Detect layered architecture
        layer_keywords = {
            'presentation': ['Controller', 'View', 'Handler', 'Route'],
            'business': ['Service', 'Manager', 'Logic', 'UseCase'],
            'data': ['Repository', 'Model', 'Entity', 'DAO'],
        }
        
        detected_layers = {}
        for layer, keywords in layer_keywords.items():
            detected_layers[f'{layer}_layer'] = any(keyword in content for keyword in keywords)
        
        patterns.update(detected_layers)
        patterns['architecture_score'] = sum(1 for v in patterns.values() if v) / len(patterns)
        
        return patterns
    
    def _extract_semantic_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic understanding of code intent"""
        features = {
            'intent_classification': self._classify_code_intent(context),
            'domain_concepts': self._extract_domain_concepts(context),
            'api_patterns': self._analyze_api_patterns(context),
            'data_flow': self._analyze_data_flow(context),
        }
        return features
    
    def _extract_performance_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance-related features"""
        file_path = context.get('file_path', '')
        if not file_path or not Path(file_path).exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            features = {
                'has_caching': bool(re.search(r'(cache|memoize|lru_cache|Cache)', content)),
                'has_lazy_loading': bool(re.search(r'(lazy|defer|Lazy|Promise\.all)', content)),
                'has_pagination': bool(re.search(r'(paginate|pagination|limit|offset|page)', content)),
                'has_indexing': bool(re.search(r'(index|Index|KEY|createIndex)', content)),
                'uses_bulk_operations': bool(re.search(r'(bulk|batch|Bulk|insertMany|updateMany)', content)),
                'has_connection_pooling': bool(re.search(r'(pool|Pool|connectionPool|maxConnections)', content)),
            }
            
            # Detect potential performance issues
            issues = {
                'nested_loops': len(re.findall(r'for.*:\s*\n\s*for', content)),
                'synchronous_io': len(re.findall(r'(readFileSync|requests\.get(?!\s*\(.*async)|open\([^)]+\)(?!.*async))', content)),
                'inefficient_queries': len(re.findall(r'SELECT\s+\*|N\+1|findAll\(\)|getAll\(\)', content, re.IGNORECASE)),
            }
            
            features['performance_score'] = 1.0 - (sum(1 for v in issues.values() if v > 0) / len(issues))
            features.update({f'perf_issue_{k}': v for k, v in issues.items()})
            
            return features
        except Exception as e:
            logger.error(f"Error extracting performance features: {e}")
            return {}
    
    def _extract_security_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract security-related features"""
        file_path = context.get('file_path', '')
        if not file_path or not Path(file_path).exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            features = {
                'has_input_validation': bool(re.search(r'(validate|sanitize|escape|clean)', content)),
                'has_authentication': bool(re.search(r'(auth|Auth|authenticate|jwt|token)', content)),
                'has_authorization': bool(re.search(r'(authorize|permission|role|access)', content)),
                'has_encryption': bool(re.search(r'(encrypt|decrypt|hash|bcrypt|crypto)', content)),
                'uses_prepared_statements': bool(re.search(r'(\?|prepare|parameterized|bindParam)', content)),
                'has_rate_limiting': bool(re.search(r'(rateLimit|throttle|rate.limit)', content)),
            }
            
            # Detect security vulnerabilities
            vulnerabilities = {
                'sql_injection_risk': len(re.findall(r'["\']\s*\+.*\+\s*["\'].*(?:SELECT|INSERT|UPDATE|DELETE)', content, re.IGNORECASE)),
                'xss_risk': len(re.findall(r'innerHTML\s*=|document\.write|eval\(', content)),
                'hardcoded_secrets': len(re.findall(r'(api_key|secret|password)\s*=\s*["\'][^"\'{]+["\']', content)),
                'insecure_random': len(re.findall(r'Math\.random|rand\(\)|random\.random\(\)', content)),
            }
            
            features['security_score'] = 1.0 - (sum(1 for v in vulnerabilities.values() if v > 0) / len(vulnerabilities))
            features.update({f'vuln_{k}': v for k, v in vulnerabilities.items()})
            
            return features
        except Exception as e:
            logger.error(f"Error extracting security features: {e}")
            return {}
    
    def _extract_architecture_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract architectural features and patterns"""
        features = {
            'modularity_score': self._calculate_modularity_score(context),
            'coupling_score': self._calculate_coupling_score(context),
            'cohesion_score': self._calculate_cohesion_score(context),
            'abstraction_level': self._determine_abstraction_level(context),
        }
        return features
    
    # Helper methods for advanced analysis
    def _estimate_function_length(self, content: str, start_pos: int) -> int:
        """Estimate the length of a function starting at given position"""
        lines = content[start_pos:].split('\n')
        indent_level = len(lines[0]) - len(lines[0].lstrip())
        function_lines = 1
        
        for line in lines[1:]:
            if line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                break
            function_lines += 1
        
        return function_lines
    
    def _calculate_max_nesting_depth(self, content: str) -> int:
        """Calculate maximum nesting depth in code"""
        max_depth = 0
        current_depth = 0
        
        for char in content:
            if char in '{([':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in '})]':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _detect_duplicate_patterns(self, content: str) -> int:
        """Detect duplicate code patterns"""
        lines = content.split('\n')
        duplicates = 0
        
        # Simple duplicate detection - look for similar lines
        line_hashes = {}
        for line in lines:
            if len(line.strip()) > 10:  # Only consider meaningful lines
                line_hash = hashlib.md5(line.strip().encode()).hexdigest()
                if line_hash in line_hashes:
                    duplicates += 1
                else:
                    line_hashes[line_hash] = 1
        
        return duplicates
    
    def _detect_indent_style(self, lines: List[str]) -> Dict[str, Any]:
        """Detect indentation style and consistency"""
        space_count = 0
        tab_count = 0
        indent_sizes = []
        
        for line in lines:
            if line and line[0] in ' \t':
                if line[0] == ' ':
                    space_count += 1
                    indent_size = len(line) - len(line.lstrip())
                    if indent_size > 0:
                        indent_sizes.append(indent_size)
                else:
                    tab_count += 1
        
        consistency_score = 1.0
        if space_count > 0 and tab_count > 0:
            consistency_score = 0.5  # Mixed indentation
        elif indent_sizes:
            # Check if indent sizes are consistent multiples
            common_indent = min(indent_sizes) if indent_sizes else 0
            if common_indent > 0:
                consistent_indents = sum(1 for size in indent_sizes if size % common_indent == 0)
                consistency_score = consistent_indents / len(indent_sizes)
        
        return {
            'style': 'spaces' if space_count > tab_count else 'tabs',
            'consistency_score': consistency_score,
            'common_indent_size': min(indent_sizes) if indent_sizes else 0,
        }
    
    def _analyze_naming_conventions(self, content: str) -> Dict[str, Any]:
        """Analyze naming conventions used in code"""
        # Extract various identifiers
        function_names = re.findall(r'(?:def|function|func)\s+(\w+)', content)
        class_names = re.findall(r'(?:class|interface)\s+(\w+)', content)
        variable_names = re.findall(r'(?:let|const|var|=)\s+(\w+)\s*[=:]', content)
        
        conventions = {
            'camelCase': 0,
            'snake_case': 0,
            'PascalCase': 0,
            'kebab-case': 0,
        }
        
        all_names = function_names + variable_names
        for name in all_names:
            if re.match(r'^[a-z][a-zA-Z0-9]*$', name):
                conventions['camelCase'] += 1
            elif re.match(r'^[a-z][a-z0-9_]*$', name):
                conventions['snake_case'] += 1
        
        for name in class_names:
            if re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                conventions['PascalCase'] += 1
        
        total = sum(conventions.values())
        consistency_score = max(conventions.values()) / total if total > 0 else 1.0
        
        return {
            'dominant_convention': max(conventions, key=conventions.get),
            'consistency_score': consistency_score,
            'convention_distribution': conventions,
        }
    
    def _detect_mvc_pattern(self, content: str) -> bool:
        """Detect if code follows MVC pattern"""
        mvc_keywords = {
            'model': ['Model', 'Entity', 'Schema', 'Table'],
            'view': ['View', 'Template', 'Component', 'render'],
            'controller': ['Controller', 'Handler', 'Route', 'Action'],
        }
        
        detected_components = 0
        for component, keywords in mvc_keywords.items():
            if any(keyword in content for keyword in keywords):
                detected_components += 1
        
        return detected_components >= 2
    
    def _classify_code_intent(self, context: Dict[str, Any]) -> str:
        """Classify the intent/purpose of code"""
        file_path = context.get('file_path', '')
        if not file_path:
            return 'unknown'
        
        file_name = Path(file_path).name.lower()
        
        # Common patterns for intent classification
        if 'test' in file_name or 'spec' in file_name:
            return 'testing'
        elif 'config' in file_name or 'settings' in file_name:
            return 'configuration'
        elif 'model' in file_name or 'entity' in file_name:
            return 'data_model'
        elif 'controller' in file_name or 'handler' in file_name:
            return 'request_handling'
        elif 'service' in file_name or 'manager' in file_name:
            return 'business_logic'
        elif 'util' in file_name or 'helper' in file_name:
            return 'utility'
        elif 'migration' in file_name:
            return 'database_migration'
        else:
            return 'general'
    
    def _extract_domain_concepts(self, context: Dict[str, Any]) -> List[str]:
        """Extract domain-specific concepts from code"""
        # This would ideally use NLP, but for now we'll use pattern matching
        file_path = context.get('file_path', '')
        if not file_path or not Path(file_path).exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract class and function names as potential domain concepts
            concepts = set()
            
            # Class names often represent domain entities
            class_names = re.findall(r'class\s+(\w+)', content)
            concepts.update(class_names)
            
            # Extract meaningful function names
            function_names = re.findall(r'def\s+(\w+)', content)
            for name in function_names:
                # Split camelCase or snake_case to extract concepts
                parts = re.split(r'_|(?=[A-Z])', name)
                concepts.update(part.lower() for part in parts if len(part) > 2)
            
            # Common domain indicators
            domain_patterns = [
                r'\b(User|Customer|Order|Product|Payment|Invoice|Account)\b',
                r'\b(create|update|delete|fetch|process|validate|calculate)\w*\b',
            ]
            
            for pattern in domain_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                concepts.update(match.lower() for match in matches)
            
            return list(concepts)[:20]  # Limit to top 20 concepts
        except Exception as e:
            logger.error(f"Error extracting domain concepts: {e}")
            return []
    
    def _analyze_api_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze API design patterns"""
        file_path = context.get('file_path', '')
        if not file_path or not Path(file_path).exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            patterns = {
                'rest_api': bool(re.search(r'(GET|POST|PUT|DELETE|PATCH)\s*[\(\'"]', content)),
                'graphql': bool(re.search(r'(query|mutation|subscription|GraphQL)', content)),
                'rpc': bool(re.search(r'(RPC|jsonrpc|grpc)', content, re.IGNORECASE)),
                'websocket': bool(re.search(r'(WebSocket|ws:|socket\.io)', content)),
                'uses_versioning': bool(re.search(r'(/v\d+/|version\s*=|api_version)', content)),
                'has_pagination': bool(re.search(r'(page|limit|offset|cursor|next|previous)', content)),
                'has_filtering': bool(re.search(r'(filter|where|query|search)', content)),
                'has_sorting': bool(re.search(r'(sort|order|orderBy)', content)),
            }
            
            return patterns
        except Exception as e:
            logger.error(f"Error analyzing API patterns: {e}")
            return {}
    
    def _analyze_data_flow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data flow patterns in code"""
        file_path = context.get('file_path', '')
        if not file_path or not Path(file_path).exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple data flow analysis
            data_flow = {
                'input_sources': len(re.findall(r'(request\.|input\(|argv|environ|query)', content)),
                'output_destinations': len(re.findall(r'(response\.|print\(|write\(|send\()', content)),
                'data_transformations': len(re.findall(r'(map\(|filter\(|reduce\(|transform|convert|parse)', content)),
                'data_validations': len(re.findall(r'(validate|check|verify|assert|require)', content)),
                'data_persistence': len(re.findall(r'(save\(|insert\(|update\(|delete\(|persist)', content)),
            }
            
            # Calculate data flow complexity
            total_operations = sum(data_flow.values())
            data_flow['complexity'] = min(total_operations / 20, 1.0)  # Normalize to 0-1
            
            return data_flow
        except Exception as e:
            logger.error(f"Error analyzing data flow: {e}")
            return {}
    
    def _calculate_modularity_score(self, context: Dict[str, Any]) -> float:
        """Calculate modularity score of code"""
        # Simplified modularity calculation
        file_path = context.get('file_path', '')
        if not file_path:
            return 0.5
        
        # Check file organization
        path_parts = Path(file_path).parts
        depth_score = min(len(path_parts) / 5, 1.0)  # Reasonable depth
        
        # Check for module patterns
        if any(part in ['src', 'lib', 'modules', 'components'] for part in path_parts):
            return min(depth_score + 0.3, 1.0)
        
        return depth_score
    
    def _calculate_coupling_score(self, context: Dict[str, Any]) -> float:
        """Calculate coupling score (lower is better)"""
        file_path = context.get('file_path', '')
        if not file_path or not Path(file_path).exists():
            return 0.5
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count imports/dependencies
            imports = len(re.findall(r'(import|require|include|use)\s+', content))
            
            # Normalize (assuming > 20 imports is high coupling)
            return min(imports / 20, 1.0)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, re.error) as e:
            import logging
            logging.debug(f"Failed to calculate coupling score for {context.get('file_path', 'unknown')}: {e}")
            return 0.5
    
    def _calculate_cohesion_score(self, context: Dict[str, Any]) -> float:
        """Calculate cohesion score (higher is better)"""
        # Simplified cohesion - based on related functionality
        file_path = context.get('file_path', '')
        if not file_path or not Path(file_path).exists():
            return 0.5
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if functions/methods are related (simplified)
            functions = re.findall(r'def\s+(\w+)', content)
            if not functions:
                return 0.7  # No functions, assume cohesive
            
            # Check for common prefixes/patterns in function names
            common_prefixes = 0
            for i in range(len(functions)):
                for j in range(i + 1, len(functions)):
                    if functions[i][:3] == functions[j][:3]:
                        common_prefixes += 1
            
            if len(functions) > 1:
                cohesion = common_prefixes / (len(functions) * (len(functions) - 1) / 2)
                return min(cohesion * 2, 1.0)  # Scale up
            
            return 0.7
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, re.error) as e:
            import logging
            logging.debug(f"Failed to calculate cohesion score for {context.get('file_path', 'unknown')}: {e}")
            return 0.5
    
    def _determine_abstraction_level(self, context: Dict[str, Any]) -> str:
        """Determine the abstraction level of code"""
        file_path = context.get('file_path', '')
        if not file_path:
            return 'unknown'
        
        file_name = Path(file_path).name.lower()
        
        # Determine based on common patterns
        if any(pattern in file_name for pattern in ['interface', 'abstract', 'base']):
            return 'high'
        elif any(pattern in file_name for pattern in ['impl', 'concrete', 'handler']):
            return 'low'
        elif any(pattern in file_name for pattern in ['service', 'manager', 'controller']):
            return 'medium'
        else:
            return 'unknown'

def main():
    """Demo the AI learning engine"""
    engine = AILearningEngine()
    
    print("🧠 AI Learning Engine Demo")
    print("Simulating user interactions...")
    
    # Simulate some user actions
    actions = [
        UserAction(
            action_type="fix_applied",
            factor="dependencies",
            context={"fix_type": "lock_file", "file_path": "requirements.txt", "success": True},
            timestamp=datetime.now() - timedelta(hours=1)
        ),
        UserAction(
            action_type="fix_rejected",
            factor="config",
            context={"fix_type": "env_vars", "reason": "prefer_manual"},
            timestamp=datetime.now() - timedelta(minutes=30)
        ),
        UserAction(
            action_type="feedback_positive",
            factor="ai_system",
            context={"recommendation_id": "test_rec_1", "rating": 4.5},
            timestamp=datetime.now() - timedelta(minutes=10)
        )
    ]
    
    for action in actions:
        engine.record_user_action(action)
        print(f"Recorded action: {action.action_type} for {action.factor}")
    
    # Get recommendations
    print("\n📋 Current Recommendations:")
    recommendations = engine.get_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. [{rec.priority.upper()}] {rec.title}")
        print(f"   {rec.description}")
        print(f"   Confidence: {rec.confidence:.1%}, Impact: {rec.estimated_impact:.1%}")
        print()
    
    # Analyze learning progress
    print("📊 Learning Progress Analysis:")
    progress = engine.analyze_learning_progress()
    for key, value in progress.items():
        print(f"{key}: {value}")
    
    print(f"\n💾 Detected {len(engine.patterns)} learning patterns")
    for pattern in engine.patterns:
        print(f"  • {pattern.description} (confidence: {pattern.confidence:.1%})")

if __name__ == "__main__":
    main()