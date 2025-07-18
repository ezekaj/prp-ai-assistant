#!/usr/bin/env python3
"""
PRP Analytics & Learning System
Analyzes PRP success patterns and improves future PRPs
"""

import json
import os
from datetime import datetime
from pathlib import Path
import re
from collections import defaultdict

class PRPAnalytics:
    def __init__(self, prp_directory="PRPs"):
        self.prp_dir = Path(prp_directory)
        self.analytics_file = self.prp_dir / "analytics" / "prp_metrics.json"
        self.patterns_file = self.prp_dir / "analytics" / "success_patterns.json"
        
        # Ensure analytics directory exists
        (self.prp_dir / "analytics").mkdir(exist_ok=True)
        
    def analyze_prp_success(self, prp_file, success_metrics):
        """Analyze and record PRP implementation success"""
        prp_data = self._parse_prp_file(prp_file)
        
        analytics = {
            'prp_id': prp_data.get('id', 'unknown'),
            'complexity': prp_data.get('complexity', 5),
            'estimated_time': prp_data.get('estimated_time', 0),
            'actual_time': success_metrics.get('actual_time', 0),
            'success_rate': success_metrics.get('success_rate', 0),
            'test_coverage': success_metrics.get('test_coverage', 0),
            'performance_score': success_metrics.get('performance_score', 0),
            'timestamp': datetime.now().isoformat(),
            'patterns_used': prp_data.get('patterns', []),
            'issues_encountered': success_metrics.get('issues', [])
        }
        
        self._save_analytics(analytics)
        self._update_success_patterns(analytics)
        
    def _parse_prp_file(self, prp_file):
        """Extract metadata from PRP file"""
        with open(prp_file, 'r') as f:
            content = f.read()
            
        # Extract key information using regex
        prp_data = {}
        
        # Extract PRP ID
        id_match = re.search(r'\*\*PRP ID\*\*:\s*(\S+)', content)
        if id_match:
            prp_data['id'] = id_match.group(1)
            
        # Extract complexity
        complexity_match = re.search(r'\*\*Complexity Score\*\*:\s*(\d+)', content)
        if complexity_match:
            prp_data['complexity'] = int(complexity_match.group(1))
            
        # Extract estimated time
        time_match = re.search(r'\*\*Estimated Implementation Time\*\*:\s*(\d+)', content)
        if time_match:
            prp_data['estimated_time'] = int(time_match.group(1))
            
        return prp_data
    
    def _save_analytics(self, analytics):
        """Save analytics data"""
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r') as f:
                data = json.load(f)
        else:
            data = {'prp_analytics': []}
            
        data['prp_analytics'].append(analytics)
        
        with open(self.analytics_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _update_success_patterns(self, analytics):
        """Update success patterns based on analytics"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                patterns = json.load(f)
        else:
            patterns = {
                'high_success_patterns': [],
                'complexity_success_rates': {},
                'common_issues': defaultdict(int),
                'time_estimation_accuracy': []
            }
        
        # Update patterns based on success rate
        if analytics['success_rate'] > 0.8:  # High success
            for pattern in analytics['patterns_used']:
                if pattern not in patterns['high_success_patterns']:
                    patterns['high_success_patterns'].append(pattern)
        
        # Update complexity success rates
        complexity = str(analytics['complexity'])
        if complexity not in patterns['complexity_success_rates']:
            patterns['complexity_success_rates'][complexity] = []
        patterns['complexity_success_rates'][complexity].append(analytics['success_rate'])
        
        # Track common issues
        for issue in analytics['issues_encountered']:
            patterns['common_issues'][issue] += 1
        
        # Track time estimation accuracy
        if analytics['estimated_time'] > 0:
            accuracy = analytics['actual_time'] / analytics['estimated_time']
            patterns['time_estimation_accuracy'].append(accuracy)
        
        with open(self.patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2, default=list)
    
    def generate_insights(self):
        """Generate insights from analytics data"""
        if not self.analytics_file.exists():
            return "No analytics data available"
        
        with open(self.analytics_file, 'r') as f:
            data = json.load(f)
        
        analytics = data['prp_analytics']
        
        insights = {
            'total_prps': len(analytics),
            'average_success_rate': sum(a['success_rate'] for a in analytics) / len(analytics),
            'average_complexity': sum(a['complexity'] for a in analytics) / len(analytics),
            'time_estimation_accuracy': self._calculate_time_accuracy(analytics),
            'most_successful_complexity': self._find_most_successful_complexity(analytics),
            'common_issues': self._get_common_issues(analytics)
        }
        
        return insights
    
    def _calculate_time_accuracy(self, analytics):
        """Calculate time estimation accuracy"""
        accuracies = []
        for a in analytics:
            if a['estimated_time'] > 0 and a['actual_time'] > 0:
                accuracy = min(a['estimated_time'], a['actual_time']) / max(a['estimated_time'], a['actual_time'])
                accuracies.append(accuracy)
        
        return sum(accuracies) / len(accuracies) if accuracies else 0
    
    def _find_most_successful_complexity(self, analytics):
        """Find complexity level with highest success rate"""
        complexity_success = defaultdict(list)
        
        for a in analytics:
            complexity_success[a['complexity']].append(a['success_rate'])
        
        best_complexity = max(complexity_success.keys(), 
                            key=lambda k: sum(complexity_success[k]) / len(complexity_success[k]))
        
        return best_complexity
    
    def _get_common_issues(self, analytics):
        """Get most common issues"""
        issue_counts = defaultdict(int)
        
        for a in analytics:
            for issue in a['issues_encountered']:
                issue_counts[issue] += 1
        
        return dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5])
    
    def generate_recommendations(self):
        """Generate recommendations for improving PRPs"""
        insights = self.generate_insights()
        
        recommendations = []
        
        if insights['average_success_rate'] < 0.8:
            recommendations.append("Consider adding more detailed implementation steps")
        
        if insights['time_estimation_accuracy'] < 0.7:
            recommendations.append("Improve time estimation by analyzing similar past implementations")
        
        if insights['common_issues']:
            top_issue = list(insights['common_issues'].keys())[0]
            recommendations.append(f"Add specific guidance for handling: {top_issue}")
        
        return recommendations

if __name__ == "__main__":
    analytics = PRPAnalytics()
    
    # Example usage
    insights = analytics.generate_insights()
    recommendations = analytics.generate_recommendations()
    
    print("PRP Analytics Insights:")
    print(json.dumps(insights, indent=2))
    print("\nRecommendations:")
    for rec in recommendations:
        print(f"- {rec}")