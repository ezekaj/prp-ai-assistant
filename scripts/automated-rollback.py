#!/usr/bin/env python3
"""
Automated Rollback System
Monitors deployments and automatically triggers rollbacks based on health metrics
"""

import os
import sys
import time
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import requests
from prometheus_client.parser import text_string_to_metric_families
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/rollback-automation.log')
    ]
)
logger = logging.getLogger(__name__)

class RollbackReason(Enum):
    """Reasons for triggering rollback"""
    ERROR_RATE_HIGH = "High error rate detected"
    LATENCY_HIGH = "High latency detected"
    HEALTH_CHECK_FAILED = "Health check failed"
    POD_CRASH_LOOP = "Pods are crash looping"
    MEMORY_PRESSURE = "High memory usage detected"
    CPU_PRESSURE = "High CPU usage detected"
    MANUAL_TRIGGER = "Manual rollback requested"
    CUSTOM_METRIC_FAILED = "Custom metric threshold exceeded"

@dataclass
class DeploymentInfo:
    """Deployment information"""
    namespace: str
    name: str
    version: str
    replicas: int
    start_time: datetime
    strategy: str = "rolling"

@dataclass
class HealthMetrics:
    """Health metrics for deployment"""
    error_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    request_rate: float
    cpu_usage: float
    memory_usage: float
    restart_count: int
    ready_replicas: int
    total_replicas: int

@dataclass
class RollbackConfig:
    """Rollback configuration"""
    error_rate_threshold: float = 0.05  # 5%
    latency_p95_threshold: float = 2.0  # 2 seconds
    latency_p99_threshold: float = 5.0  # 5 seconds
    cpu_threshold: float = 0.8  # 80%
    memory_threshold: float = 0.9  # 90%
    restart_threshold: int = 3
    health_check_retries: int = 3
    health_check_interval: int = 30  # seconds
    monitoring_duration: int = 300  # 5 minutes
    prometheus_url: str = "http://prometheus:9090"
    alertmanager_url: str = "http://alertmanager:9093"

class RollbackAutomation:
    """Main rollback automation system"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.active_deployments: Dict[str, DeploymentInfo] = {}
        self.rollback_history: List[Dict] = []
        self.prometheus_url = self.config.prometheus_url
        self.alertmanager_url = self.config.alertmanager_url
        
    def _load_config(self, config_file: Optional[str]) -> RollbackConfig:
        """Load configuration from file or use defaults"""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                return RollbackConfig(**config_data.get('rollback', {}))
        return RollbackConfig()
    
    async def monitor_deployment(self, deployment: DeploymentInfo) -> Dict:
        """Monitor a deployment and trigger rollback if needed"""
        logger.info(f"Starting monitoring for {deployment.name} version {deployment.version}")
        
        self.active_deployments[deployment.name] = deployment
        monitoring_end = datetime.utcnow() + timedelta(seconds=self.config.monitoring_duration)
        
        try:
            while datetime.utcnow() < monitoring_end:
                # Gather metrics
                metrics = await self._gather_metrics(deployment)
                
                # Check health
                health_check = self._check_health(deployment, metrics)
                
                if not health_check['healthy']:
                    logger.warning(f"Health check failed: {health_check['reason']}")
                    
                    # Attempt rollback
                    rollback_result = await self._execute_rollback(
                        deployment,
                        health_check['reason'],
                        metrics
                    )
                    
                    return rollback_result
                
                # Log current status
                logger.info(f"Health check passed. Metrics: {self._format_metrics(metrics)}")
                
                # Wait before next check
                await asyncio.sleep(self.config.health_check_interval)
            
            # Monitoring completed successfully
            logger.info(f"Monitoring completed successfully for {deployment.name}")
            del self.active_deployments[deployment.name]
            
            return {
                'status': 'success',
                'deployment': asdict(deployment),
                'monitoring_duration': self.config.monitoring_duration
            }
            
        except Exception as e:
            logger.error(f"Error during monitoring: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'deployment': asdict(deployment)
            }
    
    async def _gather_metrics(self, deployment: DeploymentInfo) -> HealthMetrics:
        """Gather metrics from Prometheus and Kubernetes"""
        # Query Prometheus
        error_rate = await self._query_prometheus(
            f'sum(rate(http_requests_total{{deployment="{deployment.name}",status=~"5.."}}[5m])) / '
            f'sum(rate(http_requests_total{{deployment="{deployment.name}"}}[5m]))'
        )
        
        latency_p50 = await self._query_prometheus(
            f'histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket'
            f'{{deployment="{deployment.name}"}}[5m])) by (le))'
        )
        
        latency_p95 = await self._query_prometheus(
            f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket'
            f'{{deployment="{deployment.name}"}}[5m])) by (le))'
        )
        
        latency_p99 = await self._query_prometheus(
            f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket'
            f'{{deployment="{deployment.name}"}}[5m])) by (le))'
        )
        
        request_rate = await self._query_prometheus(
            f'sum(rate(http_requests_total{{deployment="{deployment.name}"}}[5m]))'
        )
        
        # Get Kubernetes metrics
        k8s_metrics = self._get_k8s_metrics(deployment)
        
        return HealthMetrics(
            error_rate=error_rate or 0,
            latency_p50=latency_p50 or 0,
            latency_p95=latency_p95 or 0,
            latency_p99=latency_p99 or 0,
            request_rate=request_rate or 0,
            cpu_usage=k8s_metrics['cpu_usage'],
            memory_usage=k8s_metrics['memory_usage'],
            restart_count=k8s_metrics['restart_count'],
            ready_replicas=k8s_metrics['ready_replicas'],
            total_replicas=k8s_metrics['total_replicas']
        )
    
    async def _query_prometheus(self, query: str) -> Optional[float]:
        """Query Prometheus for metrics"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success' and data['data']['result']:
                    return float(data['data']['result'][0]['value'][1])
            
            return None
            
        except Exception as e:
            logger.error(f"Prometheus query failed: {str(e)}")
            return None
    
    def _get_k8s_metrics(self, deployment: DeploymentInfo) -> Dict:
        """Get metrics from Kubernetes"""
        try:
            # Get deployment status
            cmd = [
                'kubectl', 'get', 'deployment', deployment.name,
                '-n', deployment.namespace, '-o', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                status = data.get('status', {})
                
                # Get pod metrics
                pod_cmd = [
                    'kubectl', 'top', 'pods', '-n', deployment.namespace,
                    '-l', f'app={deployment.name}', '--no-headers'
                ]
                pod_result = subprocess.run(pod_cmd, capture_output=True, text=True)
                
                cpu_usage = 0
                memory_usage = 0
                
                if pod_result.returncode == 0 and pod_result.stdout:
                    lines = pod_result.stdout.strip().split('\n')
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 3:
                            # Parse CPU (remove 'm' suffix)
                            cpu = parts[1].rstrip('m')
                            cpu_usage += int(cpu) / 1000  # Convert to cores
                            
                            # Parse memory (remove 'Mi' suffix)
                            memory = parts[2].rstrip('Mi')
                            memory_usage += int(memory)
                
                # Get restart count
                restart_cmd = [
                    'kubectl', 'get', 'pods', '-n', deployment.namespace,
                    '-l', f'app={deployment.name}',
                    '-o', 'jsonpath={.items[*].status.containerStatuses[*].restartCount}'
                ]
                restart_result = subprocess.run(restart_cmd, capture_output=True, text=True)
                
                restart_count = 0
                if restart_result.returncode == 0 and restart_result.stdout:
                    restarts = restart_result.stdout.split()
                    restart_count = sum(int(r) for r in restarts if r.isdigit())
                
                return {
                    'ready_replicas': status.get('readyReplicas', 0),
                    'total_replicas': status.get('replicas', deployment.replicas),
                    'cpu_usage': cpu_usage / deployment.replicas if deployment.replicas > 0 else 0,
                    'memory_usage': memory_usage / deployment.replicas if deployment.replicas > 0 else 0,
                    'restart_count': restart_count
                }
            
            return {
                'ready_replicas': 0,
                'total_replicas': deployment.replicas,
                'cpu_usage': 0,
                'memory_usage': 0,
                'restart_count': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get K8s metrics: {str(e)}")
            return {
                'ready_replicas': 0,
                'total_replicas': deployment.replicas,
                'cpu_usage': 0,
                'memory_usage': 0,
                'restart_count': 0
            }
    
    def _check_health(self, deployment: DeploymentInfo, metrics: HealthMetrics) -> Dict:
        """Check deployment health against thresholds"""
        # Check error rate
        if metrics.error_rate > self.config.error_rate_threshold:
            return {
                'healthy': False,
                'reason': RollbackReason.ERROR_RATE_HIGH,
                'details': f"Error rate {metrics.error_rate:.2%} exceeds threshold {self.config.error_rate_threshold:.2%}"
            }
        
        # Check latency
        if metrics.latency_p95 > self.config.latency_p95_threshold:
            return {
                'healthy': False,
                'reason': RollbackReason.LATENCY_HIGH,
                'details': f"P95 latency {metrics.latency_p95:.2f}s exceeds threshold {self.config.latency_p95_threshold}s"
            }
        
        # Check pod restarts
        if metrics.restart_count > self.config.restart_threshold:
            return {
                'healthy': False,
                'reason': RollbackReason.POD_CRASH_LOOP,
                'details': f"Restart count {metrics.restart_count} exceeds threshold {self.config.restart_threshold}"
            }
        
        # Check CPU usage
        if metrics.cpu_usage > self.config.cpu_threshold:
            return {
                'healthy': False,
                'reason': RollbackReason.CPU_PRESSURE,
                'details': f"CPU usage {metrics.cpu_usage:.2%} exceeds threshold {self.config.cpu_threshold:.2%}"
            }
        
        # Check memory usage
        if metrics.memory_usage > self.config.memory_threshold:
            return {
                'healthy': False,
                'reason': RollbackReason.MEMORY_PRESSURE,
                'details': f"Memory usage {metrics.memory_usage:.2%} exceeds threshold {self.config.memory_threshold:.2%}"
            }
        
        # Check replica health
        if metrics.ready_replicas < metrics.total_replicas * 0.8:
            return {
                'healthy': False,
                'reason': RollbackReason.HEALTH_CHECK_FAILED,
                'details': f"Only {metrics.ready_replicas}/{metrics.total_replicas} replicas are ready"
            }
        
        return {'healthy': True}
    
    async def _execute_rollback(self, deployment: DeploymentInfo, 
                               reason: RollbackReason, metrics: HealthMetrics) -> Dict:
        """Execute deployment rollback"""
        logger.warning(f"Initiating rollback for {deployment.name}: {reason.value}")
        
        rollback_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'deployment': asdict(deployment),
            'reason': reason.value,
            'metrics': asdict(metrics),
            'status': 'initiated'
        }
        
        try:
            # Execute kubectl rollback
            cmd = ['kubectl', 'rollout', 'undo', f'deployment/{deployment.name}', 
                   '-n', deployment.namespace]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Rollback command failed: {result.stderr}")
            
            # Wait for rollback to complete
            wait_cmd = ['kubectl', 'rollout', 'status', f'deployment/{deployment.name}', 
                        '-n', deployment.namespace, '--timeout=5m']
            wait_result = subprocess.run(wait_cmd, capture_output=True, text=True)
            
            if wait_result.returncode == 0:
                rollback_record['status'] = 'success'
                logger.info(f"Rollback completed successfully for {deployment.name}")
                
                # Send notifications
                await self._send_notifications(rollback_record)
                
                # Create incident ticket
                await self._create_incident(rollback_record)
            else:
                rollback_record['status'] = 'failed'
                rollback_record['error'] = wait_result.stderr
                logger.error(f"Rollback failed for {deployment.name}: {wait_result.stderr}")
            
        except Exception as e:
            rollback_record['status'] = 'error'
            rollback_record['error'] = str(e)
            logger.error(f"Rollback error: {str(e)}")
        
        # Save to history
        self.rollback_history.append(rollback_record)
        self._save_rollback_history()
        
        return rollback_record
    
    async def _send_notifications(self, rollback_record: Dict):
        """Send notifications about rollback"""
        # Send to Alertmanager
        alert = {
            'labels': {
                'alertname': 'DeploymentRolledBack',
                'severity': 'critical',
                'deployment': rollback_record['deployment']['name'],
                'namespace': rollback_record['deployment']['namespace'],
                'version': rollback_record['deployment']['version']
            },
            'annotations': {
                'summary': f"Deployment {rollback_record['deployment']['name']} was rolled back",
                'description': rollback_record['reason'],
                'metrics': json.dumps(rollback_record['metrics'])
            }
        }
        
        try:
            response = requests.post(
                f"{self.alertmanager_url}/api/v1/alerts",
                json=[alert],
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to send alert: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
    
    async def _create_incident(self, rollback_record: Dict):
        """Create incident ticket for rollback"""
        # This would integrate with your incident management system
        logger.info(f"Creating incident for rollback: {rollback_record['deployment']['name']}")
        
        # Example: Create GitHub issue
        if os.getenv('GITHUB_TOKEN'):
            # Implementation would go here
            pass
    
    def _format_metrics(self, metrics: HealthMetrics) -> str:
        """Format metrics for logging"""
        return (f"Error: {metrics.error_rate:.2%}, "
                f"P95: {metrics.latency_p95:.2f}s, "
                f"CPU: {metrics.cpu_usage:.1f}, "
                f"Memory: {metrics.memory_usage:.1f}MB, "
                f"Ready: {metrics.ready_replicas}/{metrics.total_replicas}")
    
    def _save_rollback_history(self):
        """Save rollback history to file"""
        history_file = '/var/log/rollback-history.json'
        try:
            with open(history_file, 'w') as f:
                json.dump(self.rollback_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save rollback history: {str(e)}")
    
    async def watch_deployments(self):
        """Watch for new deployments and monitor them"""
        logger.info("Starting deployment watcher...")
        
        while True:
            try:
                # Get deployments with specific annotation
                cmd = ['kubectl', 'get', 'deployments', '--all-namespaces',
                       '-o', 'json', '-l', 'monitor-rollback=true']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    
                    for item in data.get('items', []):
                        metadata = item['metadata']
                        spec = item['spec']
                        
                        deployment_name = metadata['name']
                        namespace = metadata['namespace']
                        
                        # Check if we're already monitoring this deployment
                        if deployment_name not in self.active_deployments:
                            # Check if it was recently updated
                            generation = metadata.get('generation', 0)
                            observed_generation = item['status'].get('observedGeneration', 0)
                            
                            if generation > observed_generation:
                                # New deployment detected
                                deployment = DeploymentInfo(
                                    namespace=namespace,
                                    name=deployment_name,
                                    version=metadata.get('labels', {}).get('version', 'unknown'),
                                    replicas=spec.get('replicas', 1),
                                    start_time=datetime.utcnow(),
                                    strategy=metadata.get('annotations', {}).get('deployment-strategy', 'rolling')
                                )
                                
                                # Start monitoring in background
                                asyncio.create_task(self.monitor_deployment(deployment))
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in deployment watcher: {str(e)}")
                await asyncio.sleep(60)

async def main():
    """Main entry point"""
    # Load configuration
    config_file = os.getenv('ROLLBACK_CONFIG', '/etc/rollback/config.yaml')
    
    # Create automation instance
    automation = RollbackAutomation(config_file)
    
    # Start watching deployments
    await automation.watch_deployments()

if __name__ == '__main__':
    asyncio.run(main())