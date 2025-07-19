#!/usr/bin/env python3
"""
PRP-12Factor AI Adaptive Learning System
Learns from successes and failures to improve recommendations
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class LearningEvent:
    """Represents a learning event from user interaction"""
    event_id: str
    event_type: str  # 'success', 'failure', 'partial_success', 'user_override'
    factor: str
    action_taken: str
    context: Dict[str, Any]
    outcome: Dict[str, Any]
    timestamp: datetime
    confidence_before: float
    confidence_after: float
    user_feedback: Optional[str] = None
    
@dataclass
class PatternCluster:
    """Cluster of similar patterns"""
    cluster_id: str
    pattern_type: str
    centroid: Dict[str, float]
    members: List[str]
    success_rate: float
    confidence: float
    last_updated: datetime

@dataclass
class AdaptiveModel:
    """Machine learning model for adaptive recommendations"""
    model_id: str
    model_type: str
    feature_names: List[str]
    model: Any  # sklearn model
    scaler: StandardScaler
    performance_metrics: Dict[str, float]
    training_samples: int
    last_trained: datetime

class AdaptiveLearningSystem:
    """Advanced adaptive learning system with ML capabilities"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.models_dir = self.project_root / "PRPs" / "models"
        self.learning_data_file = self.project_root / "PRPs" / "analytics" / "adaptive-learning.json"
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.learning_data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Learning components
        self.learning_events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.pattern_clusters: Dict[str, PatternCluster] = {}
        self.models: Dict[str, AdaptiveModel] = {}
        
        # Learning parameters
        self.config = {
            'min_samples_for_training': 50,
            'retrain_interval_hours': 24,
            'success_threshold': 0.8,
            'failure_threshold': 0.3,
            'clustering_threshold': 0.85,
            'feature_importance_threshold': 0.05,
            'model_performance_threshold': 0.7,
        }
        
        # Feature engineering components
        self.feature_extractors = {
            'context_features': self._extract_context_features,
            'temporal_features': self._extract_temporal_features,
            'historical_features': self._extract_historical_features,
            'complexity_features': self._extract_complexity_features,
            'user_preference_features': self._extract_user_preference_features,
        }
        
        # Load existing data
        self._load_learning_data()
        self._load_models()
        
        logger.info(f"Adaptive Learning System initialized with {len(self.learning_events)} events")
    
    def _load_learning_data(self):
        """Load historical learning data"""
        if not self.learning_data_file.exists():
            return
        
        try:
            with open(self.learning_data_file, 'r') as f:
                data = json.load(f)
            
            # Load learning events
            for event_data in data.get('learning_events', []):
                event = LearningEvent(
                    event_id=event_data['event_id'],
                    event_type=event_data['event_type'],
                    factor=event_data['factor'],
                    action_taken=event_data['action_taken'],
                    context=event_data['context'],
                    outcome=event_data['outcome'],
                    timestamp=datetime.fromisoformat(event_data['timestamp']),
                    confidence_before=event_data['confidence_before'],
                    confidence_after=event_data['confidence_after'],
                    user_feedback=event_data.get('user_feedback')
                )
                self.learning_events.append(event)
            
            # Load pattern clusters
            for cluster_data in data.get('pattern_clusters', {}).values():
                cluster = PatternCluster(
                    cluster_id=cluster_data['cluster_id'],
                    pattern_type=cluster_data['pattern_type'],
                    centroid=cluster_data['centroid'],
                    members=cluster_data['members'],
                    success_rate=cluster_data['success_rate'],
                    confidence=cluster_data['confidence'],
                    last_updated=datetime.fromisoformat(cluster_data['last_updated'])
                )
                self.pattern_clusters[cluster.cluster_id] = cluster
                
        except Exception as e:
            logger.error(f"Error loading learning data: {e}")
    
    def _load_models(self):
        """Load trained ML models"""
        model_files = list(self.models_dir.glob("*.joblib"))
        
        for model_file in model_files:
            try:
                model_data = joblib.load(model_file)
                model = AdaptiveModel(
                    model_id=model_data['model_id'],
                    model_type=model_data['model_type'],
                    feature_names=model_data['feature_names'],
                    model=model_data['model'],
                    scaler=model_data['scaler'],
                    performance_metrics=model_data['performance_metrics'],
                    training_samples=model_data['training_samples'],
                    last_trained=datetime.fromisoformat(model_data['last_trained'])
                )
                self.models[model.model_id] = model
                logger.info(f"Loaded model: {model.model_id}")
            except Exception as e:
                logger.error(f"Error loading model {model_file}: {e}")
    
    def record_learning_event(self, event: LearningEvent):
        """Record a new learning event and trigger adaptive learning"""
        # Add to event history
        self.learning_events.append(event)
        
        # Update confidence based on outcome
        self._update_confidence_models(event)
        
        # Detect and update patterns
        self._update_pattern_clusters(event)
        
        # Retrain models if needed
        if self._should_retrain_models():
            self._retrain_models()
        
        # Save data periodically
        if len(self.learning_events) % 100 == 0:
            self._save_learning_data()
    
    def _update_confidence_models(self, event: LearningEvent):
        """Update confidence models based on event outcome"""
        # Calculate confidence adjustment
        if event.event_type == 'success':
            confidence_delta = 0.1 * (1 - event.confidence_before)
        elif event.event_type == 'failure':
            confidence_delta = -0.2 * event.confidence_before
        elif event.event_type == 'partial_success':
            confidence_delta = 0.05 * (0.7 - event.confidence_before)
        else:  # user_override
            confidence_delta = -0.15 * event.confidence_before
        
        # Apply learning rate decay
        learning_rate = 0.1 * (0.95 ** (len(self.learning_events) / 1000))
        confidence_delta *= learning_rate
        
        # Update model confidence for similar contexts
        self._propagate_confidence_update(event, confidence_delta)
    
    def _update_pattern_clusters(self, event: LearningEvent):
        """Update or create pattern clusters based on new event"""
        # Extract features from event
        features = self._extract_all_features(event)
        
        # Find similar clusters
        similar_cluster = self._find_similar_cluster(features, event.factor)
        
        if similar_cluster:
            # Update existing cluster
            self._update_cluster(similar_cluster, event, features)
        else:
            # Create new cluster if pattern is novel
            if self._is_pattern_significant(event):
                self._create_new_cluster(event, features)
    
    def _should_retrain_models(self) -> bool:
        """Determine if models should be retrained"""
        if not self.models:
            return len(self.learning_events) >= self.config['min_samples_for_training']
        
        # Check time since last training
        for model in self.models.values():
            time_since_training = datetime.now() - model.last_trained
            if time_since_training > timedelta(hours=self.config['retrain_interval_hours']):
                return True
        
        # Check if performance has degraded
        recent_performance = self._calculate_recent_performance()
        if recent_performance < self.config['model_performance_threshold']:
            return True
        
        return False
    
    def _retrain_models(self):
        """Retrain ML models with latest data"""
        logger.info("Retraining adaptive models...")
        
        # Prepare training data
        X, y = self._prepare_training_data()
        
        if len(X) < self.config['min_samples_for_training']:
            logger.warning("Insufficient data for training")
            return
        
        # Train models for each factor
        factors = set(event.factor for event in self.learning_events)
        
        for factor in factors:
            model_id = f"adaptive_model_{factor}"
            
            # Filter data for this factor
            factor_mask = [event.factor == factor for event in self.learning_events]
            X_factor = X[factor_mask]
            y_factor = y[factor_mask]
            
            if len(X_factor) < 20:  # Minimum samples per factor
                continue
            
            # Train model
            model, scaler, metrics = self._train_factor_model(X_factor, y_factor)
            
            # Store model
            adaptive_model = AdaptiveModel(
                model_id=model_id,
                model_type='RandomForest',
                feature_names=self._get_feature_names(),
                model=model,
                scaler=scaler,
                performance_metrics=metrics,
                training_samples=len(X_factor),
                last_trained=datetime.now()
            )
            
            self.models[model_id] = adaptive_model
            self._save_model(adaptive_model)
            
            logger.info(f"Trained model for {factor}: accuracy={metrics['accuracy']:.2%}")
    
    def predict_success_probability(self, factor: str, action: str, context: Dict[str, Any]) -> float:
        """Predict probability of success for a given action"""
        model_id = f"adaptive_model_{factor}"
        
        if model_id not in self.models:
            # Fallback to historical success rate
            return self._calculate_historical_success_rate(factor, action)
        
        model = self.models[model_id]
        
        # Create dummy event for feature extraction
        dummy_event = LearningEvent(
            event_id="prediction",
            event_type="unknown",
            factor=factor,
            action_taken=action,
            context=context,
            outcome={},
            timestamp=datetime.now(),
            confidence_before=0.5,
            confidence_after=0.5
        )
        
        # Extract features
        features = self._extract_all_features(dummy_event)
        feature_vector = self._features_to_vector(features)
        
        # Scale features
        feature_vector_scaled = model.scaler.transform([feature_vector])
        
        # Predict
        try:
            probability = model.model.predict_proba(feature_vector_scaled)[0][1]
            return float(probability)
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 0.5
    
    def get_adaptive_recommendations(self, factor: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get adaptive recommendations based on learning"""
        recommendations = []
        
        # Get successful patterns for this factor
        successful_patterns = self._get_successful_patterns(factor)
        
        for pattern in successful_patterns:
            # Calculate similarity to current context
            similarity = self._calculate_context_similarity(pattern.centroid, context)
            
            if similarity > 0.7:
                # Generate recommendation based on pattern
                recommendation = {
                    'action': self._pattern_to_action(pattern),
                    'confidence': pattern.confidence * similarity,
                    'success_rate': pattern.success_rate,
                    'based_on_pattern': pattern.cluster_id,
                    'similar_cases': len(pattern.members),
                    'rationale': f"Based on {len(pattern.members)} similar successful cases"
                }
                recommendations.append(recommendation)
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Add predictions for top actions
        for rec in recommendations[:5]:
            rec['predicted_success'] = self.predict_success_probability(
                factor, rec['action'], context
            )
        
        return recommendations
    
    def analyze_failure_patterns(self, factor: str) -> List[Dict[str, Any]]:
        """Analyze patterns that lead to failures"""
        failure_patterns = []
        
        # Get failure events for this factor
        failures = [e for e in self.learning_events 
                   if e.factor == factor and e.event_type == 'failure']
        
        if not failures:
            return []
        
        # Group by action type
        action_failures = defaultdict(list)
        for failure in failures:
            action_failures[failure.action_taken].append(failure)
        
        # Analyze each action type
        for action, events in action_failures.items():
            if len(events) < 3:  # Need minimum samples
                continue
            
            # Extract common context features
            common_features = self._extract_common_features(events)
            
            pattern = {
                'action': action,
                'failure_count': len(events),
                'failure_rate': len(events) / max(1, self._count_action_attempts(factor, action)),
                'common_context': common_features,
                'recent_failures': len([e for e in events 
                                      if e.timestamp > datetime.now() - timedelta(days=7)]),
                'recommendations': self._generate_failure_avoidance_recommendations(
                    action, common_features
                )
            }
            failure_patterns.append(pattern)
        
        # Sort by failure rate
        failure_patterns.sort(key=lambda x: x['failure_rate'], reverse=True)
        
        return failure_patterns
    
    # Feature extraction methods
    def _extract_all_features(self, event: LearningEvent) -> Dict[str, float]:
        """Extract all features from an event"""
        features = {}
        
        for extractor_name, extractor_func in self.feature_extractors.items():
            extractor_features = extractor_func(event)
            features.update(extractor_features)
        
        return features
    
    def _extract_context_features(self, event: LearningEvent) -> Dict[str, float]:
        """Extract features from event context"""
        features = {}
        context = event.context
        
        # File-related features
        features['has_file_path'] = float('file_path' in context)
        features['file_count'] = float(context.get('file_count', 0))
        features['lines_of_code'] = float(context.get('lines_of_code', 0))
        
        # Complexity features
        features['complexity_score'] = context.get('complexity_score', 0.5)
        features['dependency_count'] = float(context.get('dependency_count', 0))
        
        # Project features
        features['project_size'] = float(context.get('project_size', 0))
        features['team_size'] = float(context.get('team_size', 1))
        
        return features
    
    def _extract_temporal_features(self, event: LearningEvent) -> Dict[str, float]:
        """Extract temporal features"""
        features = {}
        
        # Time of day
        hour = event.timestamp.hour
        features['hour_of_day'] = hour / 24.0
        features['is_business_hours'] = float(9 <= hour <= 17)
        features['is_weekend'] = float(event.timestamp.weekday() >= 5)
        
        # Day of week
        features['day_of_week'] = event.timestamp.weekday() / 7.0
        
        # Time since last similar event
        similar_events = [e for e in self.learning_events 
                         if e.factor == event.factor and e.timestamp < event.timestamp]
        if similar_events:
            last_similar = max(similar_events, key=lambda e: e.timestamp)
            time_since = (event.timestamp - last_similar.timestamp).total_seconds()
            features['hours_since_similar'] = min(time_since / 3600, 168)  # Cap at 1 week
        else:
            features['hours_since_similar'] = 168
        
        return features
    
    def _extract_historical_features(self, event: LearningEvent) -> Dict[str, float]:
        """Extract features based on historical performance"""
        features = {}
        
        # Historical success rate for this factor
        factor_events = [e for e in self.learning_events if e.factor == event.factor]
        if factor_events:
            successes = len([e for e in factor_events if e.event_type == 'success'])
            features['historical_success_rate'] = successes / len(factor_events)
        else:
            features['historical_success_rate'] = 0.5
        
        # Recent trend (last 10 events)
        recent_factor_events = [e for e in factor_events[-10:]]
        if recent_factor_events:
            recent_successes = len([e for e in recent_factor_events if e.event_type == 'success'])
            features['recent_success_rate'] = recent_successes / len(recent_factor_events)
        else:
            features['recent_success_rate'] = features['historical_success_rate']
        
        # Action-specific success rate
        action_events = [e for e in factor_events if e.action_taken == event.action_taken]
        if action_events:
            action_successes = len([e for e in action_events if e.event_type == 'success'])
            features['action_success_rate'] = action_successes / len(action_events)
        else:
            features['action_success_rate'] = 0.5
        
        return features
    
    def _extract_complexity_features(self, event: LearningEvent) -> Dict[str, float]:
        """Extract complexity-related features"""
        features = {}
        context = event.context
        
        # Code complexity
        features['cyclomatic_complexity'] = min(context.get('cyclomatic_complexity', 1) / 20, 1.0)
        features['nesting_depth'] = min(context.get('nesting_depth', 0) / 5, 1.0)
        
        # Change complexity
        features['files_affected'] = min(context.get('files_affected', 1) / 10, 1.0)
        features['lines_changed'] = min(context.get('lines_changed', 0) / 100, 1.0)
        
        # Dependency complexity
        features['external_dependencies'] = min(context.get('external_dependencies', 0) / 20, 1.0)
        features['internal_dependencies'] = min(context.get('internal_dependencies', 0) / 30, 1.0)
        
        return features
    
    def _extract_user_preference_features(self, event: LearningEvent) -> Dict[str, float]:
        """Extract user preference features"""
        features = {}
        
        # User feedback sentiment
        if event.user_feedback:
            # Simple sentiment analysis
            positive_words = ['good', 'great', 'excellent', 'perfect', 'yes']
            negative_words = ['bad', 'poor', 'wrong', 'no', 'incorrect']
            
            feedback_lower = event.user_feedback.lower()
            positive_count = sum(word in feedback_lower for word in positive_words)
            negative_count = sum(word in feedback_lower for word in negative_words)
            
            if positive_count + negative_count > 0:
                features['feedback_sentiment'] = (positive_count - negative_count) / (positive_count + negative_count)
            else:
                features['feedback_sentiment'] = 0.0
        else:
            features['feedback_sentiment'] = 0.0
        
        # Confidence alignment
        features['confidence_alignment'] = 1.0 - abs(event.confidence_before - event.confidence_after)
        
        # User override frequency
        user_overrides = len([e for e in self.learning_events 
                             if e.event_type == 'user_override' and e.factor == event.factor])
        total_events = len([e for e in self.learning_events if e.factor == event.factor])
        features['override_frequency'] = user_overrides / max(total_events, 1)
        
        return features
    
    # Helper methods
    def _find_similar_cluster(self, features: Dict[str, float], factor: str) -> Optional[PatternCluster]:
        """Find the most similar existing cluster"""
        factor_clusters = [c for c in self.pattern_clusters.values() 
                          if c.pattern_type.startswith(factor)]
        
        if not factor_clusters:
            return None
        
        best_cluster = None
        best_similarity = 0.0
        
        for cluster in factor_clusters:
            similarity = self._calculate_feature_similarity(features, cluster.centroid)
            if similarity > best_similarity and similarity > self.config['clustering_threshold']:
                best_similarity = similarity
                best_cluster = cluster
        
        return best_cluster
    
    def _calculate_feature_similarity(self, features1: Dict[str, float], 
                                    features2: Dict[str, float]) -> float:
        """Calculate cosine similarity between feature vectors"""
        # Get common keys
        common_keys = set(features1.keys()) & set(features2.keys())
        
        if not common_keys:
            return 0.0
        
        # Calculate cosine similarity
        dot_product = sum(features1[k] * features2[k] for k in common_keys)
        magnitude1 = np.sqrt(sum(features1[k] ** 2 for k in common_keys))
        magnitude2 = np.sqrt(sum(features2[k] ** 2 for k in common_keys))
        
        if magnitude1 * magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _update_cluster(self, cluster: PatternCluster, event: LearningEvent, features: Dict[str, float]):
        """Update existing cluster with new event"""
        # Add to members
        cluster.members.append(event.event_id)
        
        # Update centroid (moving average)
        alpha = 0.1  # Learning rate
        for key, value in features.items():
            if key in cluster.centroid:
                cluster.centroid[key] = (1 - alpha) * cluster.centroid[key] + alpha * value
            else:
                cluster.centroid[key] = value
        
        # Update success rate
        cluster_events = [e for e in self.learning_events if e.event_id in cluster.members]
        successes = len([e for e in cluster_events if e.event_type == 'success'])
        cluster.success_rate = successes / len(cluster_events)
        
        # Update confidence based on consistency
        cluster.confidence = min(cluster.success_rate * (1 + len(cluster.members) / 100), 0.95)
        
        cluster.last_updated = datetime.now()
    
    def _create_new_cluster(self, event: LearningEvent, features: Dict[str, float]):
        """Create a new pattern cluster"""
        cluster_id = f"cluster_{event.factor}_{hashlib.md5(str(features).encode()).hexdigest()[:8]}"
        
        cluster = PatternCluster(
            cluster_id=cluster_id,
            pattern_type=f"{event.factor}_{event.action_taken}",
            centroid=features.copy(),
            members=[event.event_id],
            success_rate=1.0 if event.event_type == 'success' else 0.0,
            confidence=0.5,  # Start with medium confidence
            last_updated=datetime.now()
        )
        
        self.pattern_clusters[cluster_id] = cluster
        logger.info(f"Created new pattern cluster: {cluster_id}")
    
    def _is_pattern_significant(self, event: LearningEvent) -> bool:
        """Determine if an event represents a significant pattern"""
        # Check if it's a strong success or failure
        if event.event_type in ['success', 'failure']:
            # Check confidence change
            confidence_change = abs(event.confidence_after - event.confidence_before)
            return confidence_change > 0.2
        
        return event.event_type == 'user_override'
    
    def _propagate_confidence_update(self, event: LearningEvent, delta: float):
        """Propagate confidence updates to similar contexts"""
        # Find similar recent events
        similar_events = []
        for past_event in self.learning_events:
            if past_event.factor == event.factor and past_event.event_id != event.event_id:
                similarity = self._calculate_context_similarity(
                    self._extract_all_features(past_event),
                    self._extract_all_features(event)
                )
                if similarity > 0.8:
                    similar_events.append((past_event, similarity))
        
        # Apply weighted confidence updates
        for similar_event, similarity in similar_events:
            weighted_delta = delta * similarity * 0.5  # Dampen propagation
            similar_event.confidence_after = max(0.0, min(1.0, 
                similar_event.confidence_after + weighted_delta))
    
    def _calculate_context_similarity(self, context1: Any, context2: Any) -> float:
        """Calculate similarity between two contexts"""
        if isinstance(context1, dict) and isinstance(context2, dict):
            return self._calculate_feature_similarity(context1, context2)
        return 0.0
    
    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for ML models"""
        X = []
        y = []
        
        for event in self.learning_events:
            features = self._extract_all_features(event)
            feature_vector = self._features_to_vector(features)
            
            X.append(feature_vector)
            y.append(1 if event.event_type == 'success' else 0)
        
        return np.array(X), np.array(y)
    
    def _features_to_vector(self, features: Dict[str, float]) -> List[float]:
        """Convert feature dictionary to vector"""
        # Ensure consistent ordering
        feature_names = self._get_feature_names()
        vector = []
        
        for name in feature_names:
            vector.append(features.get(name, 0.0))
        
        return vector
    
    def _get_feature_names(self) -> List[str]:
        """Get consistent list of feature names"""
        # Collect all possible feature names
        all_features = set()
        
        for event in self.learning_events[:100]:  # Sample for efficiency
            features = self._extract_all_features(event)
            all_features.update(features.keys())
        
        return sorted(list(all_features))
    
    def _train_factor_model(self, X: np.ndarray, y: np.ndarray) -> Tuple[Any, StandardScaler, Dict[str, float]]:
        """Train a model for a specific factor"""
        from sklearn.model_selection import train_test_split, cross_val_score
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        model.fit(X_train_scaled, y_train)
        
        # Calculate metrics
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
        
        metrics = {
            'accuracy': test_score,
            'train_accuracy': train_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
        }
        
        return model, scaler, metrics
    
    def _save_model(self, model: AdaptiveModel):
        """Save model to disk"""
        model_data = {
            'model_id': model.model_id,
            'model_type': model.model_type,
            'feature_names': model.feature_names,
            'model': model.model,
            'scaler': model.scaler,
            'performance_metrics': model.performance_metrics,
            'training_samples': model.training_samples,
            'last_trained': model.last_trained.isoformat()
        }
        
        model_path = self.models_dir / f"{model.model_id}.joblib"
        joblib.dump(model_data, model_path)
    
    def _save_learning_data(self):
        """Save learning data to disk"""
        try:
            # Prepare data for JSON serialization
            events_data = []
            for event in list(self.learning_events)[-1000:]:  # Save last 1000 events
                events_data.append({
                    'event_id': event.event_id,
                    'event_type': event.event_type,
                    'factor': event.factor,
                    'action_taken': event.action_taken,
                    'context': event.context,
                    'outcome': event.outcome,
                    'timestamp': event.timestamp.isoformat(),
                    'confidence_before': event.confidence_before,
                    'confidence_after': event.confidence_after,
                    'user_feedback': event.user_feedback
                })
            
            clusters_data = {}
            for cluster_id, cluster in self.pattern_clusters.items():
                clusters_data[cluster_id] = {
                    'cluster_id': cluster.cluster_id,
                    'pattern_type': cluster.pattern_type,
                    'centroid': cluster.centroid,
                    'members': cluster.members[-100:],  # Keep last 100 members
                    'success_rate': cluster.success_rate,
                    'confidence': cluster.confidence,
                    'last_updated': cluster.last_updated.isoformat()
                }
            
            data = {
                'learning_events': events_data,
                'pattern_clusters': clusters_data,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.learning_data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def _calculate_historical_success_rate(self, factor: str, action: str) -> float:
        """Calculate historical success rate for fallback"""
        relevant_events = [e for e in self.learning_events 
                          if e.factor == factor and e.action_taken == action]
        
        if not relevant_events:
            return 0.5  # No data, assume neutral
        
        successes = len([e for e in relevant_events if e.event_type == 'success'])
        return successes / len(relevant_events)
    
    def _calculate_recent_performance(self) -> float:
        """Calculate recent model performance"""
        recent_events = list(self.learning_events)[-100:]
        
        if not recent_events:
            return 1.0
        
        correct_predictions = 0
        total_predictions = 0
        
        for event in recent_events:
            if hasattr(event, 'predicted_outcome'):
                total_predictions += 1
                if event.predicted_outcome == event.event_type:
                    correct_predictions += 1
        
        if total_predictions == 0:
            return 1.0
        
        return correct_predictions / total_predictions
    
    def _get_successful_patterns(self, factor: str) -> List[PatternCluster]:
        """Get successful patterns for a factor"""
        patterns = []
        
        for cluster in self.pattern_clusters.values():
            if (cluster.pattern_type.startswith(factor) and 
                cluster.success_rate >= self.config['success_threshold']):
                patterns.append(cluster)
        
        # Sort by confidence and success rate
        patterns.sort(key=lambda x: x.confidence * x.success_rate, reverse=True)
        
        return patterns
    
    def _pattern_to_action(self, pattern: PatternCluster) -> str:
        """Convert pattern to actionable recommendation"""
        # Extract action from pattern type
        parts = pattern.pattern_type.split('_', 1)
        if len(parts) > 1:
            return parts[1]
        return "apply_best_practice"
    
    def _extract_common_features(self, events: List[LearningEvent]) -> Dict[str, Any]:
        """Extract common features from multiple events"""
        if not events:
            return {}
        
        # Extract features for all events
        all_features = []
        for event in events:
            features = self._extract_all_features(event)
            all_features.append(features)
        
        # Find common patterns
        common_features = {}
        
        # For numeric features, calculate mean and std
        numeric_features = defaultdict(list)
        for features in all_features:
            for key, value in features.items():
                if isinstance(value, (int, float)):
                    numeric_features[key].append(value)
        
        for key, values in numeric_features.items():
            if values:
                mean_val = np.mean(values)
                std_val = np.std(values)
                if std_val < 0.1 * mean_val:  # Low variance indicates commonality
                    common_features[key] = {'mean': mean_val, 'std': std_val}
        
        return common_features
    
    def _count_action_attempts(self, factor: str, action: str) -> int:
        """Count total attempts of an action"""
        return len([e for e in self.learning_events 
                   if e.factor == factor and e.action_taken == action])
    
    def _generate_failure_avoidance_recommendations(self, action: str, 
                                                   common_features: Dict[str, Any]) -> List[str]:
        """Generate recommendations to avoid failures"""
        recommendations = []
        
        # Analyze common features
        if 'complexity_score' in common_features:
            if common_features['complexity_score']['mean'] > 0.7:
                recommendations.append("Consider breaking down complex changes into smaller steps")
        
        if 'is_weekend' in common_features:
            if common_features['is_weekend']['mean'] > 0.5:
                recommendations.append("This action has higher failure rates on weekends")
        
        if 'dependency_count' in common_features:
            if common_features['dependency_count']['mean'] > 10:
                recommendations.append("High dependency count increases failure risk - review dependencies")
        
        # Action-specific recommendations
        if 'auto_fix' in action:
            recommendations.append("Consider manual review before applying auto-fixes")
        
        if 'bulk' in action or 'batch' in action:
            recommendations.append("Test on a small subset before bulk operations")
        
        return recommendations

def main():
    """Demo the adaptive learning system"""
    system = AdaptiveLearningSystem()
    
    print("🧠 Adaptive Learning System Demo")
    print("=" * 50)
    
    # Simulate learning events
    events = [
        LearningEvent(
            event_id="evt_001",
            event_type="success",
            factor="dependencies",
            action_taken="auto_fix_lockfile",
            context={'complexity_score': 0.3, 'file_count': 1, 'dependency_count': 15},
            outcome={'errors_fixed': 0, 'warnings_fixed': 3},
            timestamp=datetime.now() - timedelta(hours=2),
            confidence_before=0.7,
            confidence_after=0.85,
            user_feedback="Good fix, worked perfectly"
        ),
        LearningEvent(
            event_id="evt_002",
            event_type="failure",
            factor="config",
            action_taken="auto_fix_env_vars",
            context={'complexity_score': 0.8, 'file_count': 5, 'has_secrets': True},
            outcome={'errors_introduced': 2},
            timestamp=datetime.now() - timedelta(hours=1),
            confidence_before=0.6,
            confidence_after=0.3,
            user_feedback="Broke the configuration"
        ),
        LearningEvent(
            event_id="evt_003",
            event_type="partial_success",
            factor="dependencies",
            action_taken="update_vulnerable_deps",
            context={'complexity_score': 0.5, 'dependency_count': 25, 'vulnerabilities': 3},
            outcome={'vulnerabilities_fixed': 2, 'vulnerabilities_remaining': 1},
            timestamp=datetime.now() - timedelta(minutes=30),
            confidence_before=0.75,
            confidence_after=0.7
        )
    ]
    
    # Record events
    for event in events:
        system.record_learning_event(event)
        print(f"Recorded: {event.event_type} for {event.factor}")
    
    # Get adaptive recommendations
    print("\n📊 Adaptive Recommendations for 'dependencies':")
    context = {'complexity_score': 0.4, 'dependency_count': 20}
    recommendations = system.get_adaptive_recommendations('dependencies', context)
    
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"\n{i}. {rec['action']}")
        print(f"   Confidence: {rec['confidence']:.2%}")
        print(f"   Success Rate: {rec['success_rate']:.2%}")
        print(f"   Based on: {rec['similar_cases']} similar cases")
        if 'predicted_success' in rec:
            print(f"   Predicted Success: {rec['predicted_success']:.2%}")
    
    # Analyze failure patterns
    print("\n⚠️  Failure Pattern Analysis for 'config':")
    failures = system.analyze_failure_patterns('config')
    
    for pattern in failures:
        print(f"\nAction: {pattern['action']}")
        print(f"Failure Rate: {pattern['failure_rate']:.2%} ({pattern['failure_count']} failures)")
        print("Recommendations:")
        for rec in pattern['recommendations']:
            print(f"  • {rec}")
    
    # Predict success probability
    print("\n🔮 Success Probability Prediction:")
    probability = system.predict_success_probability(
        'dependencies',
        'auto_fix_lockfile',
        {'complexity_score': 0.2, 'dependency_count': 10}
    )
    print(f"Predicted success probability: {probability:.2%}")

if __name__ == "__main__":
    main()