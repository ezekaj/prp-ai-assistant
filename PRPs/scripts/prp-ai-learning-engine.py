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
            'temporal_patterns': self._extract_temporal_features
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
    
    # Feature extraction methods
    def _extract_code_complexity_features(self, file_path: str) -> Dict[str, Any]:
        """Extract code complexity features"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            return {
                'line_count': len(lines),
                'non_empty_lines': len([line for line in lines if line.strip()]),
                'function_count': len(re.findall(r'def\s+\w+', content)),
                'class_count': len(re.findall(r'class\s+\w+', content)),
                'complexity_score': min(len(lines) / 100, 1.0)  # Simplified complexity
            }
        except:
            return {'error': True}
    
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
                except:
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
            except:
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