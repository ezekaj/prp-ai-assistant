#!/usr/bin/env python3
"""
Continuous PRP-12Factor Monitoring Script
Runs periodic compliance checks and tracks changes over time
"""

import json
import time
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class ContinuousMonitor:
    def __init__(self, check_interval=300):  # 5 minutes default
        self.check_interval = check_interval
        self.history_file = Path(".prp/monitoring/history.json")
        self.alert_file = Path(".prp/monitoring/alerts.json")
        self.history = self.load_history()
        self.alerts = []
        
    def load_history(self) -> List[Dict]:
        """Load scan history"""
        if self.history_file.exists():
            with open(self.history_file, "r") as f:
                return json.load(f)
        return []
    
    def save_history(self):
        """Save scan history"""
        # Keep only last 100 scans
        self.history = self.history[-100:]
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2)
    
    def run_single_check(self):
        """Run a single compliance check"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running compliance check...")
        
        # Run the monitor script
        result = subprocess.run(
            [sys.executable, ".prp/monitoring/run_monitor.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running compliance check: {result.stderr}")
            return None
        
        # Load the results
        results_file = Path(".prp/monitoring/latest-scan.json")
        if results_file.exists():
            with open(results_file, "r") as f:
                return json.load(f)
        return None
    
    def analyze_changes(self, current_results: Dict):
        """Analyze changes from previous scan"""
        if not self.history:
            return
        
        previous = self.history[-1]
        current_score = current_results["overall_score"]
        previous_score = previous["overall_score"]
        
        # Check for score changes
        score_diff = current_score - previous_score
        if abs(score_diff) > 0.1:
            if score_diff > 0:
                print(f"[IMPROVEMENT] Score increased by {score_diff:.1f}% to {current_score:.1f}%")
            else:
                print(f"[DEGRADATION] Score decreased by {abs(score_diff):.1f}% to {current_score:.1f}%")
                self.create_alert("score_degradation", f"Overall score dropped by {abs(score_diff):.1f}%")
        
        # Check for factor changes
        for factor, data in current_results["factors"].items():
            if factor in previous["factors"]:
                prev_score = previous["factors"][factor]["score"]
                curr_score = data["score"]
                
                if abs(curr_score - prev_score) > 0.1:
                    if curr_score < prev_score:
                        print(f"[ALERT] {factor} compliance degraded: {prev_score*100:.1f}% -> {curr_score*100:.1f}%")
                        self.create_alert(
                            "factor_degradation",
                            f"{factor} score dropped from {prev_score*100:.1f}% to {curr_score*100:.1f}%"
                        )
    
    def create_alert(self, alert_type: str, message: str):
        """Create an alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message
        }
        self.alerts.append(alert)
        
        # Save alerts
        with open(self.alert_file, "w") as f:
            json.dump(self.alerts[-50:], f, indent=2)  # Keep last 50 alerts
    
    def generate_trend_report(self):
        """Generate trend report from history"""
        if len(self.history) < 2:
            return
        
        print("\n[TREND ANALYSIS]")
        print("=" * 50)
        
        # Calculate average scores over time
        recent_scores = [h["overall_score"] for h in self.history[-10:]]
        if recent_scores:
            avg_score = sum(recent_scores) / len(recent_scores)
            print(f"Average score (last 10 scans): {avg_score:.1f}%")
        
        # Find best and worst factors
        latest = self.history[-1]
        factors = latest["factors"]
        sorted_factors = sorted(factors.items(), key=lambda x: x[1]["score"])
        
        print("\nWeakest factors:")
        for factor, data in sorted_factors[:3]:
            print(f"  - {factor}: {data['score']*100:.1f}%")
        
        print("\nStrongest factors:")
        for factor, data in sorted_factors[-3:]:
            print(f"  - {factor}: {data['score']*100:.1f}%")
    
    def run_continuous(self):
        """Run continuous monitoring"""
        print(f"Starting continuous monitoring (check every {self.check_interval} seconds)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                # Run check
                results = self.run_single_check()
                
                if results:
                    # Analyze changes
                    self.analyze_changes(results)
                    
                    # Save to history
                    self.history.append(results)
                    self.save_history()
                    
                    # Generate trend report every 5 checks
                    if len(self.history) % 5 == 0:
                        self.generate_trend_report()
                
                # Wait for next check
                print(f"\nNext check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping continuous monitoring...")
            print(f"Total scans performed: {len(self.history)}")
            if self.alerts:
                print(f"Total alerts generated: {len(self.alerts)}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous PRP-12Factor monitoring")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    monitor = ContinuousMonitor(check_interval=args.interval)
    
    if args.once:
        results = monitor.run_single_check()
        if results:
            print(f"\nCompliance score: {results['overall_score']:.1f}%")
    else:
        monitor.run_continuous()

if __name__ == "__main__":
    main()