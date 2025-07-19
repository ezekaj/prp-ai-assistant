#!/usr/bin/env python3
"""
PRP-12Factor Webhook-Style Notification System
Revolutionary notification system for real-time compliance changes in Claude Code chat
"""

import json
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import threading
from queue import Queue
import logging

logger = logging.getLogger(__name__)

@dataclass
class WebhookEvent:
    """Webhook-style event for compliance changes"""
    event_type: str  # 'compliance_change', 'alert_triggered', 'fix_applied', 'benchmark_updated'
    factor: str
    severity: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    correlation_id: str
    source: str = "prp-monitor"

@dataclass
class NotificationRule:
    """Rule for filtering and routing notifications"""
    name: str
    event_types: List[str]
    severity_filter: List[str]
    factor_filter: List[str]
    callback: Callable
    enabled: bool = True
    rate_limit: int = 60  # seconds between notifications of same type

class WebhookNotificationEngine:
    """Revolutionary webhook-style notification engine for Claude Code chat"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.event_queue = Queue()
        self.notification_rules: List[NotificationRule] = []
        self.rate_limiters: Dict[str, datetime] = {}
        self.event_history: List[WebhookEvent] = []
        self.is_running = False
        self.processor_thread = None
        
        # Chat integration callbacks
        self.chat_channels: Dict[str, Callable] = {}
        
        # Initialize default notification rules
        self._initialize_default_rules()
        
        # Load configuration
        self.config = self._load_notification_config()
        
    def _load_notification_config(self) -> Dict[str, Any]:
        """Load notification configuration"""
        config_file = self.project_root / "PRPs" / "config" / "notification-config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
                import logging
                logging.debug(f"Failed to load notification config from {config_file}: {e}")
                pass
        
        # Default configuration
        return {
            "channels": {
                "claude_chat": {
                    "enabled": True,
                    "format": "rich",
                    "include_metadata": True
                },
                "console": {
                    "enabled": True,
                    "format": "simple"
                }
            },
            "rate_limits": {
                "critical": 0,      # No rate limit for critical
                "warning": 30,      # 30 seconds between warnings
                "info": 60          # 60 seconds between info
            },
            "aggregation": {
                "enabled": True,
                "window_seconds": 300,  # 5 minute window
                "max_events": 10
            },
            "learning": {
                "enabled": True,
                "feedback_weight": 0.8,
                "pattern_detection": True
            }
        }
    
    def _initialize_default_rules(self):
        """Initialize default notification rules"""
        
        # Critical compliance changes - immediate notification
        self.add_notification_rule(
            NotificationRule(
                name="critical_compliance",
                event_types=["compliance_change", "alert_triggered"],
                severity_filter=["critical"],
                factor_filter=[],  # All factors
                callback=self._emit_critical_notification,
                rate_limit=0  # No rate limit for critical
            )
        )
        
        # Warning aggregation - group related warnings
        self.add_notification_rule(
            NotificationRule(
                name="warning_aggregation",
                event_types=["compliance_change", "alert_triggered"],
                severity_filter=["warning"],
                factor_filter=[],
                callback=self._emit_aggregated_warning,
                rate_limit=60
            )
        )
        
        # Success notifications - fixes and improvements
        self.add_notification_rule(
            NotificationRule(
                name="success_notifications",
                event_types=["fix_applied", "compliance_improved"],
                severity_filter=["info", "success"],
                factor_filter=[],
                callback=self._emit_success_notification,
                rate_limit=30
            )
        )
        
        # Benchmark updates - external API results
        self.add_notification_rule(
            NotificationRule(
                name="benchmark_updates",
                event_types=["benchmark_updated"],
                severity_filter=["info"],
                factor_filter=[],
                callback=self._emit_benchmark_notification,
                rate_limit=300  # 5 minutes
            )
        )
        
        # Learning insights - AI recommendations
        self.add_notification_rule(
            NotificationRule(
                name="learning_insights",
                event_types=["pattern_detected", "recommendation_generated"],
                severity_filter=["info"],
                factor_filter=[],
                callback=self._emit_learning_notification,
                rate_limit=600  # 10 minutes
            )
        )
    
    def add_notification_rule(self, rule: NotificationRule):
        """Add a notification rule"""
        self.notification_rules.append(rule)
        logger.info(f"Added notification rule: {rule.name}")
    
    def register_chat_channel(self, channel_name: str, callback: Callable):
        """Register a chat channel callback"""
        self.chat_channels[channel_name] = callback
        logger.info(f"Registered chat channel: {channel_name}")
    
    def start(self):
        """Start the notification processor"""
        if self.is_running:
            return
        
        self.is_running = True
        self.processor_thread = threading.Thread(target=self._process_events, daemon=True)
        self.processor_thread.start()
        
        # Emit startup notification
        startup_event = WebhookEvent(
            event_type="system_start",
            factor="system",
            severity="info",
            message="🚀 Webhook notification system started",
            timestamp=datetime.now(),
            metadata={"channels": list(self.chat_channels.keys()), "rules": len(self.notification_rules)},
            correlation_id=self._generate_correlation_id()
        )
        self.emit_event(startup_event)
    
    def stop(self):
        """Stop the notification processor"""
        self.is_running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
    
    def emit_event(self, event: WebhookEvent):
        """Emit a webhook event"""
        # Add to queue for processing
        self.event_queue.put(event)
        
        # Add to history
        self.event_history.append(event)
        
        # Keep history manageable
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-500:]
    
    def _process_events(self):
        """Process events from the queue"""
        aggregation_buffer = []
        last_aggregation = time.time()
        
        while self.is_running:
            try:
                # Check for aggregation flush
                if (time.time() - last_aggregation > self.config["aggregation"]["window_seconds"] 
                    and aggregation_buffer):
                    self._flush_aggregation_buffer(aggregation_buffer)
                    aggregation_buffer = []
                    last_aggregation = time.time()
                
                # Get event from queue (with timeout)
                try:
                    event = self.event_queue.get(timeout=1)
                except queue.Empty:
                    continue
                except Exception as e:
                    import logging
                    logging.error(f"Unexpected error getting event from queue: {e}")
                    continue
                
                # Check if event should be aggregated
                if self._should_aggregate(event):
                    aggregation_buffer.append(event)
                    if len(aggregation_buffer) >= self.config["aggregation"]["max_events"]:
                        self._flush_aggregation_buffer(aggregation_buffer)
                        aggregation_buffer = []
                        last_aggregation = time.time()
                else:
                    # Process immediately
                    self._process_single_event(event)
                
                self.event_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    def _should_aggregate(self, event: WebhookEvent) -> bool:
        """Determine if event should be aggregated"""
        if not self.config["aggregation"]["enabled"]:
            return False
        
        # Don't aggregate critical events
        if event.severity == "critical":
            return False
        
        # Don't aggregate system events
        if event.event_type in ["system_start", "system_stop"]:
            return False
        
        return event.event_type in ["alert_triggered", "compliance_change"] and event.severity == "warning"
    
    def _flush_aggregation_buffer(self, buffer: List[WebhookEvent]):
        """Flush aggregated events"""
        if not buffer:
            return
        
        # Group by factor
        by_factor = {}
        for event in buffer:
            if event.factor not in by_factor:
                by_factor[event.factor] = []
            by_factor[event.factor].append(event)
        
        # Create aggregated event
        total_events = len(buffer)
        factors_affected = list(by_factor.keys())
        
        aggregated_event = WebhookEvent(
            event_type="aggregated_alerts",
            factor="multiple",
            severity="warning",
            message=f"📊 {total_events} compliance alerts across {len(factors_affected)} factors",
            timestamp=datetime.now(),
            metadata={
                "aggregated_count": total_events,
                "factors_affected": factors_affected,
                "by_factor": {k: len(v) for k, v in by_factor.items()},
                "time_window": self.config["aggregation"]["window_seconds"]
            },
            correlation_id=self._generate_correlation_id()
        )
        
        self._process_single_event(aggregated_event)
    
    def _process_single_event(self, event: WebhookEvent):
        """Process a single event through notification rules"""
        for rule in self.notification_rules:
            if not rule.enabled:
                continue
            
            # Check if rule matches event
            if not self._rule_matches_event(rule, event):
                continue
            
            # Check rate limiting
            rate_key = f"{rule.name}_{event.factor}_{event.severity}"
            if self._is_rate_limited(rate_key, rule.rate_limit):
                continue
            
            # Execute rule callback
            try:
                rule.callback(event, rule)
                self.rate_limiters[rate_key] = datetime.now()
            except Exception as e:
                logger.error(f"Error executing rule {rule.name}: {e}")
    
    def _rule_matches_event(self, rule: NotificationRule, event: WebhookEvent) -> bool:
        """Check if rule matches event"""
        # Check event type
        if rule.event_types and event.event_type not in rule.event_types:
            return False
        
        # Check severity
        if rule.severity_filter and event.severity not in rule.severity_filter:
            return False
        
        # Check factor
        if rule.factor_filter and event.factor not in rule.factor_filter:
            return False
        
        return True
    
    def _is_rate_limited(self, rate_key: str, rate_limit: int) -> bool:
        """Check if notification is rate limited"""
        if rate_limit <= 0:
            return False
        
        if rate_key not in self.rate_limiters:
            return False
        
        elapsed = (datetime.now() - self.rate_limiters[rate_key]).total_seconds()
        return elapsed < rate_limit
    
    def _generate_correlation_id(self) -> str:
        """Generate correlation ID for event tracking"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    # Notification callback implementations
    
    def _emit_critical_notification(self, event: WebhookEvent, rule: NotificationRule):
        """Emit critical notification with immediate delivery"""
        message = f"🚨 **CRITICAL COMPLIANCE ALERT**\n"
        message += f"**Factor**: {event.factor.upper()}\n"
        message += f"**Message**: {event.message}\n"
        message += f"**Time**: {event.timestamp.strftime('%H:%M:%S')}\n"
        message += f"**Correlation ID**: `{event.correlation_id}`"
        
        if event.metadata:
            if 'file_path' in event.metadata:
                message += f"\n📁 **File**: `{event.metadata['file_path']}`"
            if 'recommendation' in event.metadata:
                message += f"\n💡 **Action Required**: {event.metadata['recommendation']}"
        
        self._broadcast_to_chat_channels(message, "critical", event)
    
    def _emit_aggregated_warning(self, event: WebhookEvent, rule: NotificationRule):
        """Emit aggregated warning notification"""
        if event.event_type == "aggregated_alerts":
            message = f"⚠️ **COMPLIANCE SUMMARY**\n"
            message += f"{event.message}\n"
            message += f"**Time Window**: {event.metadata['time_window']}s\n"
            
            # Break down by factor
            message += "**Factor Breakdown**:\n"
            for factor, count in event.metadata['by_factor'].items():
                message += f"  • {factor}: {count} alerts\n"
            
            message += f"**Correlation ID**: `{event.correlation_id}`"
        else:
            message = f"⚠️ **{event.factor.upper()}**: {event.message}"
            if event.metadata.get('recommendation'):
                message += f"\n💡 {event.metadata['recommendation']}"
        
        self._broadcast_to_chat_channels(message, "warning", event)
    
    def _emit_success_notification(self, event: WebhookEvent, rule: NotificationRule):
        """Emit success notification"""
        if event.event_type == "fix_applied":
            message = f"✅ **AUTO-FIX APPLIED**\n"
            message += f"**Factor**: {event.factor.upper()}\n"
            message += f"**Fix**: {event.message}\n"
            
            if event.metadata.get('confidence_score'):
                message += f"**Confidence**: {event.metadata['confidence_score']:.0%}\n"
            
            if event.metadata.get('before_score') and event.metadata.get('after_score'):
                before = event.metadata['before_score']
                after = event.metadata['after_score']
                message += f"**Improvement**: {before:.1f} → {after:.1f} ({after-before:+.1f})"
        
        elif event.event_type == "compliance_improved":
            message = f"📈 **COMPLIANCE IMPROVED**\n"
            message += f"**Factor**: {event.factor.upper()}\n"
            message += f"{event.message}"
        
        else:
            message = f"✅ **{event.factor.upper()}**: {event.message}"
        
        self._broadcast_to_chat_channels(message, "success", event)
    
    def _emit_benchmark_notification(self, event: WebhookEvent, rule: NotificationRule):
        """Emit benchmark update notification"""
        message = f"🌐 **INDUSTRY BENCHMARK UPDATE**\n"
        message += f"{event.message}\n"
        
        if event.metadata:
            if 'industry_average' in event.metadata:
                message += f"**Industry Average**: {event.metadata['industry_average']:.1f}%\n"
            if 'your_score' in event.metadata:
                message += f"**Your Score**: {event.metadata['your_score']:.1f}%\n"
                diff = event.metadata['your_score'] - event.metadata.get('industry_average', 0)
                emoji = "📈" if diff >= 0 else "📉"
                message += f"**Difference**: {emoji} {diff:+.1f}%"
        
        self._broadcast_to_chat_channels(message, "info", event)
    
    def _emit_learning_notification(self, event: WebhookEvent, rule: NotificationRule):
        """Emit AI learning insight notification"""
        if event.event_type == "pattern_detected":
            message = f"🧠 **PATTERN DETECTED**\n"
            message += f"{event.message}\n"
            
            if event.metadata.get('pattern_type'):
                message += f"**Pattern Type**: {event.metadata['pattern_type']}\n"
            if event.metadata.get('confidence'):
                message += f"**Confidence**: {event.metadata['confidence']:.0%}\n"
            if event.metadata.get('recommendation'):
                message += f"💡 **Suggestion**: {event.metadata['recommendation']}"
        
        elif event.event_type == "recommendation_generated":
            message = f"💡 **AI RECOMMENDATION**\n"
            message += f"**Factor**: {event.factor.upper()}\n"
            message += f"{event.message}\n"
            
            if event.metadata.get('priority'):
                message += f"**Priority**: {event.metadata['priority']}\n"
            if event.metadata.get('effort'):
                message += f"**Effort**: {event.metadata['effort']}\n"
            if event.metadata.get('impact'):
                message += f"**Expected Impact**: {event.metadata['impact']}"
        
        else:
            message = f"🧠 **LEARNING INSIGHT**: {event.message}"
        
        self._broadcast_to_chat_channels(message, "info", event)
    
    def _broadcast_to_chat_channels(self, message: str, level: str, event: WebhookEvent):
        """Broadcast message to all registered chat channels"""
        for channel_name, callback in self.chat_channels.items():
            try:
                # Add channel-specific formatting
                formatted_message = self._format_for_channel(message, channel_name, level, event)
                callback(formatted_message, level, event)
            except Exception as e:
                logger.error(f"Error broadcasting to channel {channel_name}: {e}")
    
    def _format_for_channel(self, message: str, channel: str, level: str, event: WebhookEvent) -> str:
        """Format message for specific channel"""
        channel_config = self.config["channels"].get(channel, {})
        
        if channel_config.get("format") == "simple":
            # Simple format - just the core message
            return event.message
        
        # Rich format (default)
        formatted = message
        
        if channel_config.get("include_metadata", True) and event.metadata:
            # Add webhook-style metadata
            formatted += f"\n\n**Webhook Details**:"
            formatted += f"\n• Event Type: `{event.event_type}`"
            formatted += f"\n• Timestamp: `{event.timestamp.isoformat()}`"
            formatted += f"\n• Source: `{event.source}`"
        
        return formatted

    def get_event_history(self, hours: int = 1) -> List[WebhookEvent]:
        """Get event history for the past N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [event for event in self.event_history if event.timestamp >= cutoff]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        recent_events = self.get_event_history(24)  # Last 24 hours
        
        stats = {
            "total_events_24h": len(recent_events),
            "events_by_type": {},
            "events_by_severity": {},
            "events_by_factor": {},
            "active_channels": len(self.chat_channels),
            "active_rules": len([r for r in self.notification_rules if r.enabled]),
            "rate_limited_notifications": len(self.rate_limiters)
        }
        
        for event in recent_events:
            # By type
            stats["events_by_type"][event.event_type] = stats["events_by_type"].get(event.event_type, 0) + 1
            # By severity
            stats["events_by_severity"][event.severity] = stats["events_by_severity"].get(event.severity, 0) + 1
            # By factor
            stats["events_by_factor"][event.factor] = stats["events_by_factor"].get(event.factor, 0) + 1
        
        return stats

# Integration with main monitor
class ChatIntegrationNotifier:
    """Integration notifier for Claude Code chat"""
    
    def __init__(self, webhook_engine: WebhookNotificationEngine):
        self.webhook_engine = webhook_engine
        self.chat_callbacks = []
    
    def register_callback(self, callback: Callable):
        """Register chat callback"""
        self.chat_callbacks.append(callback)
    
    def notify_compliance_change(self, factor: str, old_score: float, new_score: float, details: Dict[str, Any]):
        """Notify about compliance score changes"""
        severity = "critical" if new_score < 0.3 else "warning" if new_score < 0.7 else "info"
        
        direction = "improved" if new_score > old_score else "degraded"
        message = f"Compliance {direction}: {old_score:.1f} → {new_score:.1f}"
        
        event = WebhookEvent(
            event_type="compliance_change",
            factor=factor,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            metadata={
                "before_score": old_score,
                "after_score": new_score,
                "change": new_score - old_score,
                **details
            },
            correlation_id=self.webhook_engine._generate_correlation_id()
        )
        
        self.webhook_engine.emit_event(event)
    
    def notify_fix_applied(self, factor: str, fix_description: str, confidence: float, metadata: Dict[str, Any]):
        """Notify about applied fixes"""
        event = WebhookEvent(
            event_type="fix_applied",
            factor=factor,
            severity="success",
            message=fix_description,
            timestamp=datetime.now(),
            metadata={
                "confidence_score": confidence,
                **metadata
            },
            correlation_id=self.webhook_engine._generate_correlation_id()
        )
        
        self.webhook_engine.emit_event(event)
    
    def notify_pattern_detected(self, pattern_type: str, description: str, confidence: float, recommendation: str):
        """Notify about detected patterns"""
        event = WebhookEvent(
            event_type="pattern_detected",
            factor="ai_learning",
            severity="info",
            message=description,
            timestamp=datetime.now(),
            metadata={
                "pattern_type": pattern_type,
                "confidence": confidence,
                "recommendation": recommendation
            },
            correlation_id=self.webhook_engine._generate_correlation_id()
        )
        
        self.webhook_engine.emit_event(event)

def main():
    """Demo the webhook notification system"""
    engine = WebhookNotificationEngine()
    
    # Register demo chat callback
    def demo_chat_callback(message: str, level: str, event: WebhookEvent):
        print(f"\n[{level.upper()}] {message}")
        print("-" * 60)
    
    engine.register_chat_channel("demo", demo_chat_callback)
    engine.start()
    
    print("🚀 Webhook Notification System Demo")
    print("Simulating compliance events...")
    
    # Simulate some events
    time.sleep(1)
    
    # Critical event
    critical_event = WebhookEvent(
        event_type="alert_triggered",
        factor="config",
        severity="critical",
        message="Hardcoded credentials detected in production config",
        timestamp=datetime.now(),
        metadata={
            "file_path": "config/production.py",
            "recommendation": "Move credentials to environment variables immediately"
        },
        correlation_id=engine._generate_correlation_id()
    )
    engine.emit_event(critical_event)
    
    time.sleep(2)
    
    # Success event
    success_event = WebhookEvent(
        event_type="fix_applied",
        factor="dependencies",
        severity="success",
        message="Lock file generated automatically",
        timestamp=datetime.now(),
        metadata={
            "confidence_score": 0.95,
            "before_score": 0.7,
            "after_score": 1.0
        },
        correlation_id=engine._generate_correlation_id()
    )
    engine.emit_event(success_event)
    
    time.sleep(2)
    
    # Learning insight
    learning_event = WebhookEvent(
        event_type="pattern_detected",
        factor="processes",
        severity="info",
        message="Detected frequent use of file-based session storage",
        timestamp=datetime.now(),
        metadata={
            "pattern_type": "anti_pattern",
            "confidence": 0.85,
            "recommendation": "Consider Redis or database-backed sessions for scalability"
        },
        correlation_id=engine._generate_correlation_id()
    )
    engine.emit_event(learning_event)
    
    # Wait a bit then show stats
    time.sleep(3)
    stats = engine.get_statistics()
    print(f"\nNotification Statistics: {json.dumps(stats, indent=2)}")
    
    engine.stop()

if __name__ == "__main__":
    main()