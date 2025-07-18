#!/usr/bin/env python3
"""
PRP Dashboard - Visual analytics and management interface
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

class PRPDashboard:
    def __init__(self, prp_directory="PRPs"):
        self.prp_dir = Path(prp_directory)
        self.analytics_dir = self.prp_dir / "analytics"
        
    def generate_dashboard(self):
        """Generate comprehensive PRP dashboard"""
        print("🚀 PRP Analytics Dashboard")
        print("=" * 50)
        
        # Load analytics data
        analytics_data = self._load_analytics()
        
        if not analytics_data:
            print("No analytics data available. Implement some PRPs first!")
            return
        
        # Generate various reports
        self._print_summary_stats(analytics_data)
        self._print_success_trends(analytics_data)
        self._print_complexity_analysis(analytics_data)
        self._print_time_analysis(analytics_data)
        self._print_issue_analysis(analytics_data)
        self._print_recommendations(analytics_data)
        
    def _load_analytics(self):
        """Load analytics data"""
        analytics_file = self.analytics_dir / "prp_metrics.json"
        if not analytics_file.exists():
            return None
            
        with open(analytics_file, 'r') as f:
            data = json.load(f)
            
        return data.get('prp_analytics', [])
    
    def _print_summary_stats(self, analytics_data):
        """Print summary statistics"""
        print("\n📊 Summary Statistics")
        print("-" * 30)
        
        total_prps = len(analytics_data)
        avg_success = sum(a['success_rate'] for a in analytics_data) / total_prps
        avg_complexity = sum(a['complexity'] for a in analytics_data) / total_prps
        
        print(f"Total PRPs Implemented: {total_prps}")
        print(f"Average Success Rate: {avg_success:.1%}")
        print(f"Average Complexity: {avg_complexity:.1f}/10")
        
        # Recent performance
        recent_data = [a for a in analytics_data 
                      if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(days=30)]
        
        if recent_data:
            recent_success = sum(a['success_rate'] for a in recent_data) / len(recent_data)
            print(f"Recent Success Rate (30 days): {recent_success:.1%}")
    
    def _print_success_trends(self, analytics_data):
        """Print success trends"""
        print("\n📈 Success Trends")
        print("-" * 30)
        
        # Group by month
        monthly_success = defaultdict(list)
        for a in analytics_data:
            month = datetime.fromisoformat(a['timestamp']).strftime('%Y-%m')
            monthly_success[month].append(a['success_rate'])
        
        print("Monthly Success Rates:")
        for month in sorted(monthly_success.keys()):
            avg_success = sum(monthly_success[month]) / len(monthly_success[month])
            count = len(monthly_success[month])
            print(f"  {month}: {avg_success:.1%} ({count} PRPs)")
    
    def _print_complexity_analysis(self, analytics_data):
        """Print complexity analysis"""
        print("\n🎯 Complexity Analysis")
        print("-" * 30)
        
        complexity_stats = defaultdict(list)
        for a in analytics_data:
            complexity_stats[a['complexity']].append(a['success_rate'])
        
        print("Success Rate by Complexity:")
        for complexity in sorted(complexity_stats.keys()):
            success_rates = complexity_stats[complexity]
            avg_success = sum(success_rates) / len(success_rates)
            count = len(success_rates)
            print(f"  Complexity {complexity}: {avg_success:.1%} ({count} PRPs)")
    
    def _print_time_analysis(self, analytics_data):
        """Print time estimation analysis"""
        print("\n⏱️ Time Estimation Analysis")
        print("-" * 30)
        
        time_accuracies = []
        for a in analytics_data:
            if a['estimated_time'] > 0 and a['actual_time'] > 0:
                accuracy = min(a['estimated_time'], a['actual_time']) / max(a['estimated_time'], a['actual_time'])
                time_accuracies.append(accuracy)
        
        if time_accuracies:
            avg_accuracy = sum(time_accuracies) / len(time_accuracies)
            print(f"Average Time Estimation Accuracy: {avg_accuracy:.1%}")
            
            # Categorize accuracy
            accurate_count = sum(1 for acc in time_accuracies if acc > 0.8)
            print(f"Highly Accurate Estimates (>80%): {accurate_count}/{len(time_accuracies)}")
        else:
            print("No time estimation data available")
    
    def _print_issue_analysis(self, analytics_data):
        """Print common issues analysis"""
        print("\n🐛 Issue Analysis")
        print("-" * 30)
        
        issue_counts = defaultdict(int)
        for a in analytics_data:
            for issue in a.get('issues_encountered', []):
                issue_counts[issue] += 1
        
        if issue_counts:
            print("Most Common Issues:")
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {issue}: {count} occurrences")
        else:
            print("No issues recorded")
    
    def _print_recommendations(self, analytics_data):
        """Print AI-generated recommendations"""
        print("\n🤖 AI Recommendations")
        print("-" * 30)
        
        # Analyze patterns and generate recommendations
        recommendations = []
        
        # Success rate recommendations
        avg_success = sum(a['success_rate'] for a in analytics_data) / len(analytics_data)
        if avg_success < 0.8:
            recommendations.append("🎯 Focus on improving PRP detail - success rate below 80%")
        
        # Complexity recommendations
        complexity_success = defaultdict(list)
        for a in analytics_data:
            complexity_success[a['complexity']].append(a['success_rate'])
        
        best_complexity = max(complexity_success.keys(), 
                            key=lambda k: sum(complexity_success[k]) / len(complexity_success[k]))
        recommendations.append(f"🎯 Optimal complexity level appears to be {best_complexity}")
        
        # Time estimation recommendations
        time_accuracies = []
        for a in analytics_data:
            if a['estimated_time'] > 0 and a['actual_time'] > 0:
                accuracy = min(a['estimated_time'], a['actual_time']) / max(a['estimated_time'], a['actual_time'])
                time_accuracies.append(accuracy)
        
        if time_accuracies:
            avg_accuracy = sum(time_accuracies) / len(time_accuracies)
            if avg_accuracy < 0.7:
                recommendations.append("⏱️ Improve time estimation accuracy - consider historical data")
        
        # Issue-based recommendations
        issue_counts = defaultdict(int)
        for a in analytics_data:
            for issue in a.get('issues_encountered', []):
                issue_counts[issue] += 1
        
        if issue_counts:
            top_issue = max(issue_counts.keys(), key=lambda k: issue_counts[k])
            recommendations.append(f"🐛 Address recurring issue: {top_issue}")
        
        for rec in recommendations:
            print(f"  {rec}")
    
    def export_dashboard(self, format='json'):
        """Export dashboard data"""
        analytics_data = self._load_analytics()
        if not analytics_data:
            return None
        
        dashboard_data = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_prps': len(analytics_data),
                'average_success_rate': sum(a['success_rate'] for a in analytics_data) / len(analytics_data),
                'average_complexity': sum(a['complexity'] for a in analytics_data) / len(analytics_data)
            },
            'raw_data': analytics_data
        }
        
        export_file = self.analytics_dir / f"dashboard_export.{format}"
        
        if format == 'json':
            with open(export_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2)
        
        return export_file

if __name__ == "__main__":
    dashboard = PRPDashboard()
    dashboard.generate_dashboard()
    
    # Export dashboard
    export_file = dashboard.export_dashboard()
    if export_file:
        print(f"\n📁 Dashboard exported to: {export_file}")