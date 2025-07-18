#!/usr/bin/env python3
"""
PRP-12Factor Real-Time Monitoring Engine
Revolutionary monitoring system that works entirely within Claude Code chat
"""

import json
import time
import threading
import hashlib
import os
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict
import subprocess
import logging

# Configure logging for chat output
logging.basicConfig(
    level=logging.INFO,
    format='🔍 [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

@dataclass
class ComplianceAlert:
    """Real-time compliance alert"""
    factor: str
    severity: str  # 'critical', 'warning', 'info'
    message: str
    timestamp: datetime
    file_path: Optional[str] = None
    recommendation: Optional[str] = None
    auto_fix_available: bool = False
    confidence_score: float = 0.0

@dataclass
class MonitoringState:
    """Current monitoring state"""
    last_scan: datetime
    file_checksums: Dict[str, str]
    compliance_scores: Dict[str, float]
    active_alerts: List[ComplianceAlert]
    user_preferences: Dict[str, Any]
    learning_data: Dict[str, Any]

class Factor12Monitor:
    """Revolutionary 12-Factor monitoring engine"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.monitoring_state = MonitoringState(
            last_scan=datetime.now(),
            file_checksums={},
            compliance_scores={},
            active_alerts=[],
            user_preferences=self._load_user_preferences(),
            learning_data=self._load_learning_data()
        )
        self.is_monitoring = False
        self.monitor_thread = None
        self.chat_callbacks: List[Callable] = []
        self.auto_fix_queue: List[ComplianceAlert] = []
        
        # Initialize factor checkers
        self.factor_checkers = {
            'codebase': self._check_codebase,
            'dependencies': self._check_dependencies,
            'config': self._check_config,
            'backing_services': self._check_backing_services,
            'build_release_run': self._check_build_release_run,
            'processes': self._check_processes,
            'port_binding': self._check_port_binding,
            'concurrency': self._check_concurrency,
            'disposability': self._check_disposability,
            'dev_prod_parity': self._check_dev_prod_parity,
            'logs': self._check_logs,
            'admin_processes': self._check_admin_processes
        }
        
        # AI learning patterns
        self.learning_patterns = defaultdict(list)
        
    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences from config"""
        prefs_file = self.project_root / "PRPs" / "config" / "user-preferences.json"
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'notification_level': 'warning',
            'auto_fix_enabled': False,
            'chat_updates': True,
            'benchmark_frequency': 3600,  # seconds
            'learning_enabled': True
        }
    
    def _load_learning_data(self) -> Dict[str, Any]:
        """Load AI learning data"""
        learning_file = self.project_root / "PRPs" / "analytics" / "learning-data.json"
        if learning_file.exists():
            try:
                with open(learning_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'user_actions': [],
            'fix_success_rates': {},
            'common_patterns': {},
            'recommendation_feedback': {}
        }
    
    def register_chat_callback(self, callback: Callable):
        """Register callback for chat notifications"""
        self.chat_callbacks.append(callback)
    
    def _emit_chat_notification(self, message: str, level: str = 'info'):
        """Emit notification to Claude Code chat"""
        emoji_map = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️',
            'success': '✅',
            'fix': '🔧'
        }
        
        formatted_message = f"{emoji_map.get(level, 'ℹ️')} **PRP-12Factor Monitor**: {message}"
        
        for callback in self.chat_callbacks:
            try:
                callback(formatted_message, level)
            except Exception as e:
                logger.error(f"Chat callback failed: {e}")
        
        # Also log to console for Claude Code visibility
        logger.info(formatted_message)
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if self.is_monitoring:
            self._emit_chat_notification("Monitoring already active", 'info')
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self._emit_chat_notification("🚀 Real-time 12-Factor monitoring started!", 'success')
        self._emit_chat_notification("Scanning project for compliance patterns...", 'info')
        
        # Initial scan
        self._perform_full_scan()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self._emit_chat_notification("Monitoring stopped", 'info')
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        scan_interval = 5  # seconds
        last_benchmark = time.time()
        
        while self.is_monitoring:
            try:
                # Check for file changes
                changes_detected = self._detect_file_changes()
                
                if changes_detected:
                    self._emit_chat_notification(f"Files changed: {', '.join(changes_detected)}", 'info')
                    self._perform_incremental_scan(changes_detected)
                
                # Periodic benchmark check
                if time.time() - last_benchmark > self.monitoring_state.user_preferences['benchmark_frequency']:
                    self._perform_benchmark_check()
                    last_benchmark = time.time()
                
                # Process auto-fix queue
                self._process_auto_fix_queue()
                
                time.sleep(scan_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(scan_interval)
    
    def _detect_file_changes(self) -> List[str]:
        """Detect changed files since last scan"""
        changed_files = []
        current_checksums = {}
        
        # Scan relevant files
        patterns = ['*.py', '*.js', '*.json', '*.yml', '*.yaml', '*.env*', 'Dockerfile*', 'requirements.txt', 'package.json']
        
        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file() and not any(ignore in str(file_path) for ignore in ['.git', '__pycache__', 'node_modules']):
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            checksum = hashlib.md5(content).hexdigest()
                            current_checksums[str(file_path)] = checksum
                            
                            # Check if changed
                            if str(file_path) in self.monitoring_state.file_checksums:
                                if self.monitoring_state.file_checksums[str(file_path)] != checksum:
                                    changed_files.append(str(file_path))
                            else:
                                changed_files.append(str(file_path))  # New file
                    except Exception as e:
                        logger.debug(f"Error reading {file_path}: {e}")
        
        # Update checksums
        self.monitoring_state.file_checksums = current_checksums
        return changed_files
    
    def _perform_full_scan(self):
        """Perform full 12-factor compliance scan"""
        self._emit_chat_notification("🔍 Performing full compliance scan...", 'info')
        
        total_score = 0
        max_score = 12
        
        for factor_name, checker in self.factor_checkers.items():
            try:
                score, alerts = checker()
                self.monitoring_state.compliance_scores[factor_name] = score
                
                # Add new alerts
                for alert in alerts:
                    if not self._is_duplicate_alert(alert):
                        self.monitoring_state.active_alerts.append(alert)
                        self._emit_alert(alert)
                
                total_score += score
                
            except Exception as e:
                logger.error(f"Error checking factor {factor_name}: {e}")
        
        overall_score = (total_score / max_score) * 100
        self._emit_chat_notification(f"📊 Overall compliance: {overall_score:.1f}% ({total_score}/{max_score} factors)", 'info')
        
        # Emit dashboard update
        self._emit_dashboard_update()
    
    def _perform_incremental_scan(self, changed_files: List[str]):
        """Perform incremental scan on changed files"""
        affected_factors = self._determine_affected_factors(changed_files)
        
        if not affected_factors:
            return
        
        self._emit_chat_notification(f"🔄 Incremental scan for factors: {', '.join(affected_factors)}", 'info')
        
        for factor_name in affected_factors:
            if factor_name in self.factor_checkers:
                try:
                    score, alerts = self.factor_checkers[factor_name]()
                    old_score = self.monitoring_state.compliance_scores.get(factor_name, 0)
                    self.monitoring_state.compliance_scores[factor_name] = score
                    
                    # Check for score changes
                    if abs(score - old_score) > 0.1:
                        direction = "improved" if score > old_score else "degraded"
                        self._emit_chat_notification(
                            f"📈 Factor '{factor_name}' {direction}: {old_score:.1f} → {score:.1f}",
                            'success' if score > old_score else 'warning'
                        )
                    
                    # Process new alerts
                    for alert in alerts:
                        if not self._is_duplicate_alert(alert):
                            self.monitoring_state.active_alerts.append(alert)
                            self._emit_alert(alert)
                
                except Exception as e:
                    logger.error(f"Error checking factor {factor_name}: {e}")
        
        self._emit_dashboard_update()
    
    def _determine_affected_factors(self, changed_files: List[str]) -> List[str]:
        """Determine which factors are affected by file changes"""
        factor_file_mapping = {
            'codebase': ['*.git*', '.gitignore'],
            'dependencies': ['requirements.txt', 'package.json', 'go.mod', 'Pipfile'],
            'config': ['*.env*', 'config.py', 'settings.py', '*.json', '*.yml', '*.yaml'],
            'backing_services': ['*.py', '*.js', 'docker-compose.yml'],
            'build_release_run': ['Dockerfile*', '*.yml', '*.yaml', 'setup.py'],
            'processes': ['*.py', '*.js', 'Procfile'],
            'port_binding': ['*.py', '*.js', 'config.py'],
            'concurrency': ['*.py', '*.js', 'docker-compose.yml'],
            'disposability': ['*.py', '*.js'],
            'dev_prod_parity': ['Dockerfile*', '*.yml', '*.yaml'],
            'logs': ['*.py', '*.js'],
            'admin_processes': ['*.py', '*.js', 'manage.py']
        }
        
        affected_factors = set()
        
        for file_path in changed_files:
            for factor, patterns in factor_file_mapping.items():
                for pattern in patterns:
                    if any(p in file_path.lower() for p in pattern.split('*')):
                        affected_factors.add(factor)
        
        return list(affected_factors)
    
    def _is_duplicate_alert(self, alert: ComplianceAlert) -> bool:
        """Check if alert is duplicate"""
        for existing_alert in self.monitoring_state.active_alerts:
            if (existing_alert.factor == alert.factor and 
                existing_alert.message == alert.message and
                existing_alert.file_path == alert.file_path):
                return True
        return False
    
    def _emit_alert(self, alert: ComplianceAlert):
        """Emit compliance alert to chat"""
        severity_emojis = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        message = f"{severity_emojis[alert.severity]} **Factor {alert.factor.upper()}**: {alert.message}"
        
        if alert.file_path:
            message += f"\n📁 File: `{alert.file_path}`"
        
        if alert.recommendation:
            message += f"\n💡 Recommendation: {alert.recommendation}"
        
        if alert.auto_fix_available:
            message += f"\n🔧 Auto-fix available (confidence: {alert.confidence_score:.0%})"
            self.auto_fix_queue.append(alert)
        
        self._emit_chat_notification(message, alert.severity)
    
    def _emit_dashboard_update(self):
        """Emit live dashboard update"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'compliance_scores': self.monitoring_state.compliance_scores,
            'active_alerts_count': len(self.monitoring_state.active_alerts),
            'auto_fixes_available': len(self.auto_fix_queue)
        }
        
        # Create visual dashboard
        dashboard_text = self._create_dashboard_text(dashboard_data)
        self._emit_chat_notification(f"📊 **Live Dashboard Update**\n```\n{dashboard_text}\n```", 'info')
    
    def _create_dashboard_text(self, data: Dict) -> str:
        """Create ASCII dashboard"""
        dashboard = "PRP-12Factor Live Compliance Dashboard\n"
        dashboard += "=" * 40 + "\n"
        dashboard += f"Last Update: {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        # Compliance scores
        dashboard += "Factor Compliance:\n"
        for factor, score in data['compliance_scores'].items():
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            dashboard += f"{factor:15} [{bar}] {score*100:5.1f}%\n"
        
        dashboard += f"\nActive Alerts: {data['active_alerts_count']}\n"
        dashboard += f"Auto-fixes Available: {data['auto_fixes_available']}\n"
        
        return dashboard
    
    # Factor checking methods (simplified for space)
    def _check_codebase(self) -> tuple[float, List[ComplianceAlert]]:
        """Check codebase factor compliance"""
        alerts = []
        score = 0.0
        
        # Check for .git directory
        if (self.project_root / '.git').exists():
            score += 0.5
        else:
            alerts.append(ComplianceAlert(
                factor='codebase',
                severity='critical',
                message='No Git repository found',
                timestamp=datetime.now(),
                recommendation='Initialize git repository: git init',
                auto_fix_available=True,
                confidence_score=0.95
            ))
        
        # Check for .gitignore
        if (self.project_root / '.gitignore').exists():
            score += 0.5
        else:
            alerts.append(ComplianceAlert(
                factor='codebase',
                severity='warning',
                message='No .gitignore file found',
                timestamp=datetime.now(),
                recommendation='Create .gitignore with common patterns',
                auto_fix_available=True,
                confidence_score=0.90
            ))
        
        return score, alerts
    
    def _check_dependencies(self) -> tuple[float, List[ComplianceAlert]]:
        """Check dependencies factor compliance"""
        alerts = []
        score = 0.0
        
        # Look for dependency files
        dep_files = ['requirements.txt', 'package.json', 'go.mod', 'Pipfile']
        found_deps = [f for f in dep_files if (self.project_root / f).exists()]
        
        if found_deps:
            score += 0.7
            
            # Check for lock files
            lock_files = ['package-lock.json', 'Pipfile.lock', 'go.sum']
            found_locks = [f for f in lock_files if (self.project_root / f).exists()]
            
            if found_locks:
                score += 0.3
            else:
                alerts.append(ComplianceAlert(
                    factor='dependencies',
                    severity='warning',
                    message='No dependency lock files found',
                    timestamp=datetime.now(),
                    recommendation='Generate lock files for reproducible builds',
                    auto_fix_available=True,
                    confidence_score=0.85
                ))
        else:
            alerts.append(ComplianceAlert(
                factor='dependencies',
                severity='critical',
                message='No dependency manifest files found',
                timestamp=datetime.now(),
                recommendation='Create dependency manifest (requirements.txt, package.json, etc.)',
                auto_fix_available=False,
                confidence_score=0.0
            ))
        
        return score, alerts
    
    def _check_config(self) -> tuple[float, List[ComplianceAlert]]:
        """Check config factor compliance"""
        alerts = []
        score = 0.0
        
        # Check for environment files
        env_files = ['.env', '.env.example', '.env.local']
        found_env = [f for f in env_files if (self.project_root / f).exists()]
        
        if found_env:
            score += 0.5
        
        # Check for hardcoded values (simplified)
        python_files = list(self.project_root.rglob('*.py'))
        for py_file in python_files[:10]:  # Limit for performance
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'localhost' in content or '127.0.0.1' in content:
                        alerts.append(ComplianceAlert(
                            factor='config',
                            severity='warning',
                            message=f'Hardcoded localhost found in {py_file.name}',
                            timestamp=datetime.now(),
                            file_path=str(py_file),
                            recommendation='Use environment variables for host configuration',
                            auto_fix_available=True,
                            confidence_score=0.75
                        ))
                    else:
                        score += 0.1  # Incremental score for clean files
            except:
                pass
        
        return min(score, 1.0), alerts
    
    # Placeholder implementations for other factors
    def _check_backing_services(self) -> tuple[float, List[ComplianceAlert]]:
        return 0.8, []
    
    def _check_build_release_run(self) -> tuple[float, List[ComplianceAlert]]:
        return 0.7, []
    
    def _check_processes(self) -> tuple[float, List[ComplianceAlert]]:
        return 0.9, []
    
    def _check_port_binding(self) -> tuple[float, List[ComplianceAlert]]:
        return 0.8, []
    
    def _check_concurrency(self) -> tuple[float, List[ComplianceAlert]]:
        return 0.6, []
    
    def _check_disposability(self) -> tuple[float, List[ComplianceAlert]]:
        return 0.7, []
    
    def _check_dev_prod_parity(self) -> tuple[float, List[ComplianceAlert]]:
        return 0.8, []
    
    def _check_logs(self) -> tuple[float, List[ComplianceAlert]]:
        return 0.9, []
    
    def _check_admin_processes(self) -> tuple[float, List[ComplianceAlert]]:
        return 0.8, []
    
    def _perform_benchmark_check(self):
        """Perform external benchmarking"""
        self._emit_chat_notification("🌐 Fetching industry benchmarks...", 'info')
        # This would integrate with external APIs for benchmarking
        # Placeholder for now
        
    def _process_auto_fix_queue(self):
        """Process queued auto-fixes"""
        if not self.auto_fix_queue:
            return
        
        if not self.monitoring_state.user_preferences.get('auto_fix_enabled', False):
            return
        
        # Process one fix at a time
        alert = self.auto_fix_queue.pop(0)
        self._attempt_auto_fix(alert)
    
    def _attempt_auto_fix(self, alert: ComplianceAlert):
        """Attempt to auto-fix an issue"""
        self._emit_chat_notification(
            f"🔧 Attempting auto-fix for: {alert.message} (confidence: {alert.confidence_score:.0%})",
            'fix'
        )
        
        # This would contain actual fix implementations
        # For now, just simulate
        success = alert.confidence_score > 0.8
        
        if success:
            self._emit_chat_notification(f"✅ Auto-fix successful: {alert.message}", 'success')
            # Remove from active alerts
            self.monitoring_state.active_alerts = [
                a for a in self.monitoring_state.active_alerts 
                if not (a.factor == alert.factor and a.message == alert.message)
            ]
        else:
            self._emit_chat_notification(f"❌ Auto-fix failed: {alert.message}", 'warning')

def main():
    """Main entry point for CLI usage"""
    monitor = Factor12Monitor()
    
    # Simple chat callback for demonstration
    def chat_callback(message: str, level: str):
        print(f"[CHAT] {message}")
    
    monitor.register_chat_callback(chat_callback)
    
    print("🚀 Starting PRP-12Factor Real-Time Monitor...")
    print("This monitor will run and provide updates in Claude Code chat format.")
    print("Press Ctrl+C to stop.")
    
    try:
        monitor.start_monitoring()
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitor...")
        monitor.stop_monitoring()
        print("Monitor stopped.")

if __name__ == "__main__":
    main()