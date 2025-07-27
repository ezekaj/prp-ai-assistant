#!/usr/bin/env python3
"""
Enhanced PRP AI Multi-Agent Coordination Engine
Advanced orchestration system for intelligent agent collaboration
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging
from collections import defaultdict, deque
import networkx as nx
from concurrent.futures import ThreadPoolExecutor
import pickle
import hashlib

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Agent specialization types"""
    COORDINATOR = "coordinator"
    CODE_GENERATOR = "code_generator"
    TEST_CREATOR = "test_creator"
    SECURITY_AUDITOR = "security_auditor"
    PERFORMANCE_ANALYZER = "performance_analyzer"
    DOCUMENTATION_WRITER = "documentation_writer"
    DEPLOYMENT_SPECIALIST = "deployment_specialist"
    MONITOR = "monitor"

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"

@dataclass
class AgentCapability:
    """Agent capability definition"""
    name: str
    proficiency: float  # 0.0 to 1.0
    max_concurrent: int
    resource_cost: float  # Resource units per task
    
@dataclass
class AgentProfile:
    """Agent profile with capabilities and performance metrics"""
    agent_id: str
    agent_type: AgentType
    capabilities: List[AgentCapability]
    status: str = "initializing"
    current_load: int = 0
    max_concurrent_tasks: int = 3
    performance_score: float = 1.0
    reliability_score: float = 1.0
    average_task_time: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_availability_score(self) -> float:
        """Calculate agent availability score"""
        load_factor = 1.0 - (self.current_load / self.max_concurrent_tasks)
        return load_factor * self.performance_score * self.reliability_score

@dataclass
class CoordinationTask:
    """Enhanced task with coordination metadata"""
    task_id: str
    parent_task_id: Optional[str]
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    required_capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    assigned_agents: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    coordination_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_ready_to_execute(self, completed_tasks: Set[str]) -> bool:
        """Check if all dependencies are satisfied"""
        return all(dep in completed_tasks for dep in self.dependencies)

@dataclass
class CoordinationPlan:
    """Execution plan for complex multi-agent tasks"""
    plan_id: str
    root_task_id: str
    task_graph: nx.DiGraph
    execution_order: List[List[str]]  # Topological layers
    estimated_total_duration: float
    resource_requirements: Dict[str, float]
    critical_path: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)

class EnhancedAgentCoordinator:
    """Advanced multi-agent coordination engine"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url
        self.redis_client = None
        
        # Agent management
        self.agents: Dict[str, AgentProfile] = {}
        self.agent_channels: Dict[str, asyncio.Queue] = {}
        
        # Task management
        self.tasks: Dict[str, CoordinationTask] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.completed_tasks: Set[str] = set()
        self.blocked_tasks: Dict[str, CoordinationTask] = {}
        
        # Coordination plans
        self.coordination_plans: Dict[str, CoordinationPlan] = {}
        
        # Performance tracking
        self.performance_metrics = defaultdict(lambda: {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_duration': 0.0,
            'success_rate': 1.0
        })
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Configuration
        self.config = {
            'heartbeat_interval': 30,
            'task_timeout_multiplier': 3.0,
            'max_task_retries': 3,
            'load_balancing_interval': 10,
            'performance_decay_rate': 0.95,
            'reliability_recovery_rate': 0.02
        }
        
        logger.info("Enhanced Agent Coordinator initialized")
    
    async def initialize(self):
        """Initialize coordinator systems"""
        # In-memory implementation for now (can add Redis later)
        
        # Start background tasks
        asyncio.create_task(self._heartbeat_monitor())
        asyncio.create_task(self._task_scheduler())
        asyncio.create_task(self._load_balancer())
        asyncio.create_task(self._deadlock_detector())
        
        logger.info("Coordinator systems started")
    
    async def register_agent(self, agent_config: Dict[str, Any]) -> str:
        """Register a new agent with enhanced profiling"""
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        
        # Create agent profile
        capabilities = [
            AgentCapability(
                name=cap['name'],
                proficiency=cap.get('proficiency', 0.8),
                max_concurrent=cap.get('max_concurrent', 2),
                resource_cost=cap.get('resource_cost', 1.0)
            )
            for cap in agent_config.get('capabilities', [])
        ]
        
        agent = AgentProfile(
            agent_id=agent_id,
            agent_type=AgentType.CODE_GENERATOR,  # Default, can be overridden
            capabilities=capabilities,
            max_concurrent_tasks=agent_config.get('max_concurrent_tasks', 3),
            metadata=agent_config.get('metadata', {})
        )
        
        self.agents[agent_id] = agent
        self.agent_channels[agent_id] = asyncio.Queue()
        
        # Simulate agent activation
        agent.status = "active"
        
        # Publish registration event
        await self._publish_event('agent_registered', {
            'agent_id': agent_id,
            'agent_type': agent_config['type'],
            'capabilities': [cap.name for cap in capabilities]
        })
        
        logger.info(f"Agent {agent_id} registered - type: {agent_config['type']}")
        return agent_id
    
    async def submit_task(self, task_data: Dict[str, Any]) -> str:
        """Submit a task with intelligent decomposition"""
        # Analyze task complexity
        analysis = await self._analyze_task_complexity(task_data)
        
        if analysis['requires_coordination']:
            # Create coordination plan
            plan = await self._create_coordination_plan(task_data, analysis)
            self.coordination_plans[plan.plan_id] = plan
            
            # Submit all tasks from the plan
            for layer in plan.execution_order:
                for task_id in layer:
                    task = self.tasks[task_id]
                    await self.task_queue.put((task.priority.value, task.created_at.timestamp(), task_id))
            
            return plan.root_task_id
        else:
            # Simple single-agent task
            task = await self._create_simple_task(task_data)
            self.tasks[task.task_id] = task
            await self.task_queue.put((task.priority.value, task.created_at.timestamp(), task.task_id))
            return task.task_id
    
    async def _analyze_task_complexity(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task to determine coordination requirements"""
        task_type = task_data.get('type', 'unknown')
        
        # Define coordination patterns
        coordination_patterns = {
            'full_feature_implementation': {
                'requires_coordination': True,
                'subtasks': [
                    {'type': 'design', 'capabilities': ['code_analysis']},
                    {'type': 'code_generation', 'capabilities': ['code_generation']},
                    {'type': 'test_creation', 'capabilities': ['testing']},
                    {'type': 'security_review', 'capabilities': ['security']},
                    {'type': 'documentation', 'capabilities': ['documentation']}
                ]
            },
            '12factor_analysis': {
                'requires_coordination': True,
                'subtasks': [
                    {'type': 'codebase_analysis', 'capabilities': ['code_analysis']},
                    {'type': 'dependency_check', 'capabilities': ['dependency_analysis']},
                    {'type': 'config_audit', 'capabilities': ['security', 'code_analysis']},
                    {'type': 'deployment_readiness', 'capabilities': ['deployment']}
                ]
            },
            'full_code_review': {
                'requires_coordination': True,
                'subtasks': [
                    {'type': 'static_analysis', 'capabilities': ['code_analysis']},
                    {'type': 'complexity_analysis', 'capabilities': ['code_analysis']},
                    {'type': 'best_practices_check', 'capabilities': ['code_analysis']},
                    {'type': 'performance_review', 'capabilities': ['performance_analysis']}
                ]
            },
            'security_audit': {
                'requires_coordination': True,
                'subtasks': [
                    {'type': 'vulnerability_scan', 'capabilities': ['security']},
                    {'type': 'dependency_audit', 'capabilities': ['security', 'dependency_analysis']},
                    {'type': 'code_security_review', 'capabilities': ['security', 'code_analysis']},
                    {'type': 'security_fix_generation', 'capabilities': ['security', 'code_generation']}
                ]
            },
            'deployment_preparation': {
                'requires_coordination': True,
                'subtasks': [
                    {'type': 'final_tests', 'capabilities': ['testing']},
                    {'type': 'security_check', 'capabilities': ['security']},
                    {'type': 'deployment_config', 'capabilities': ['deployment']},
                    {'type': 'monitoring_setup', 'capabilities': ['deployment', 'monitoring_setup']}
                ]
            }
        }
        
        if task_type in coordination_patterns:
            return coordination_patterns[task_type]
        
        # Simple task analysis
        estimated_complexity = task_data.get('complexity', 5)
        if estimated_complexity > 7:
            return {
                'requires_coordination': True,
                'subtasks': self._decompose_complex_task(task_data)
            }
        
        return {'requires_coordination': False}
    
    def _decompose_complex_task(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose a complex task into subtasks"""
        # Default decomposition for unknown complex tasks
        return [
            {'type': 'analysis', 'capabilities': ['code_analysis']},
            {'type': 'implementation', 'capabilities': ['code_generation']},
            {'type': 'validation', 'capabilities': ['testing']},
            {'type': 'documentation', 'capabilities': ['documentation']}
        ]
    
    async def _create_simple_task(self, task_data: Dict[str, Any]) -> CoordinationTask:
        """Create a simple single-agent task"""
        task_id = f"task_{uuid.uuid4().hex[:10]}"
        
        return CoordinationTask(
            task_id=task_id,
            parent_task_id=None,
            task_type=task_data.get('type', 'generic'),
            priority=TaskPriority(task_data.get('priority', TaskPriority.MEDIUM.value)),
            status=TaskStatus.PENDING,
            input_data=task_data,
            required_capabilities=task_data.get('capabilities', []),
            estimated_duration=task_data.get('estimated_duration', 60.0)
        )
    
    async def _create_coordination_plan(self, task_data: Dict[str, Any], 
                                       analysis: Dict[str, Any]) -> CoordinationPlan:
        """Create an execution plan for complex tasks"""
        plan_id = f"plan_{uuid.uuid4().hex[:10]}"
        root_task_id = f"task_{uuid.uuid4().hex[:10]}"
        
        # Create task graph
        task_graph = nx.DiGraph()
        
        # Create root task
        root_task = CoordinationTask(
            task_id=root_task_id,
            parent_task_id=None,
            task_type='coordination_root',
            priority=TaskPriority(task_data.get('priority', TaskPriority.MEDIUM.value)),
            status=TaskStatus.PENDING,
            input_data=task_data
        )
        task_graph.add_node(root_task_id, task=root_task)
        self.tasks[root_task_id] = root_task
        
        # Create subtasks based on analysis
        subtask_ids = []
        for i, subtask_spec in enumerate(analysis['subtasks']):
            subtask_id = f"{root_task_id}_sub_{i}"
            
            subtask = CoordinationTask(
                task_id=subtask_id,
                parent_task_id=root_task_id,
                task_type=subtask_spec['type'],
                priority=root_task.priority,
                status=TaskStatus.PENDING,
                input_data={**task_data, 'subtask_type': subtask_spec['type']},
                required_capabilities=subtask_spec['capabilities'],
                dependencies=subtask_spec.get('dependencies', [])
            )
            
            task_graph.add_node(subtask_id, task=subtask)
            task_graph.add_edge(root_task_id, subtask_id)
            
            # Add dependencies between subtasks
            for dep in subtask.dependencies:
                if dep in subtask_ids:
                    task_graph.add_edge(dep, subtask_id)
            
            self.tasks[subtask_id] = subtask
            subtask_ids.append(subtask_id)
        
        # Calculate execution order (topological sort)
        try:
            execution_order = list(nx.topological_generations(task_graph))
        except nx.NetworkXError:
            # Fallback if graph has cycles
            execution_order = [[root_task_id], subtask_ids]
        
        # Calculate critical path
        critical_path = self._calculate_critical_path(task_graph)
        
        # Estimate resource requirements
        resource_requirements = self._calculate_resource_requirements(task_graph)
        
        plan = CoordinationPlan(
            plan_id=plan_id,
            root_task_id=root_task_id,
            task_graph=task_graph,
            execution_order=execution_order,
            estimated_total_duration=self._estimate_plan_duration(task_graph),
            resource_requirements=resource_requirements,
            critical_path=critical_path
        )
        
        logger.info(f"Created coordination plan {plan_id} - tasks: {len(task_graph.nodes())}, layers: {len(execution_order)}")
        
        return plan
    
    def _calculate_critical_path(self, task_graph: nx.DiGraph) -> List[str]:
        """Calculate the critical path through the task graph"""
        if task_graph.number_of_nodes() <= 1:
            return list(task_graph.nodes())
        
        # Simple implementation - find longest path
        try:
            return nx.dag_longest_path(task_graph)
        except:
            return list(task_graph.nodes())[:5]  # Return first 5 nodes as fallback
    
    def _calculate_resource_requirements(self, task_graph: nx.DiGraph) -> Dict[str, float]:
        """Calculate resource requirements for the plan"""
        requirements = defaultdict(float)
        
        for node_id in task_graph.nodes():
            task = self.tasks.get(node_id)
            if task:
                for cap in task.required_capabilities:
                    requirements[cap] += 1.0
        
        return dict(requirements)
    
    def _estimate_plan_duration(self, task_graph: nx.DiGraph) -> float:
        """Estimate total duration for the plan"""
        # Simple estimation - sum of all task durations divided by parallelism factor
        total_duration = 0.0
        for node_id in task_graph.nodes():
            task = self.tasks.get(node_id)
            if task:
                total_duration += task.estimated_duration
        
        # Assume 50% parallelism
        return total_duration * 0.5
    
    async def _task_scheduler(self):
        """Enhanced task scheduler with dependency management"""
        while True:
            try:
                # Get next task from priority queue
                priority, created_at_ts, task_id = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=1.0
                )
                
                # Get task object
                task = self.tasks.get(task_id)
                if not task:
                    continue
                
                # Check if dependencies are satisfied
                if not task.is_ready_to_execute(self.completed_tasks):
                    self.blocked_tasks[task.task_id] = task
                    continue
                
                # Find best agent for the task
                agent = await self._find_optimal_agent(task)
                
                if agent:
                    # Assign task to agent
                    task.assigned_agents = [agent.agent_id]
                    task.status = TaskStatus.ASSIGNED
                    task.started_at = datetime.utcnow()
                    
                    # Update agent load
                    agent.current_load += 1
                    
                    # Simulate task execution
                    asyncio.create_task(self._simulate_agent_execution(agent, task))
                    
                else:
                    # No suitable agent available, requeue
                    await asyncio.sleep(0.5)
                    await self.task_queue.put((priority, created_at_ts, task_id))
                    
            except asyncio.TimeoutError:
                # No tasks in queue
                continue
            except Exception as e:
                logger.error(f"Task scheduler error: {e}")
                await asyncio.sleep(1)
    
    async def _find_optimal_agent(self, task: CoordinationTask) -> Optional[AgentProfile]:
        """Find the best agent for a task using advanced scoring"""
        candidates = []
        
        for agent_id, agent in self.agents.items():
            # Check if agent has required capabilities
            agent_capabilities = {cap.name for cap in agent.capabilities}
            if task.required_capabilities:
                if not all(req in agent_capabilities for req in task.required_capabilities):
                    continue
            
            # Check if agent has capacity
            if agent.current_load >= agent.max_concurrent_tasks:
                continue
            
            # Check if agent is healthy
            if agent.status not in ['active', 'busy']:
                continue
            
            # Calculate match score
            score = self._calculate_agent_task_match_score(agent, task)
            candidates.append((score, agent))
        
        if not candidates:
            return None
        
        # Sort by score and return best match
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    
    def _calculate_agent_task_match_score(self, agent: AgentProfile, 
                                         task: CoordinationTask) -> float:
        """Calculate how well an agent matches a task"""
        score = 0.0
        
        # Availability score (40%)
        availability = agent.get_availability_score()
        score += availability * 0.4
        
        # Capability match score (30%)
        if task.required_capabilities:
            capability_scores = []
            for req_cap in task.required_capabilities:
                for agent_cap in agent.capabilities:
                    if agent_cap.name == req_cap:
                        capability_scores.append(agent_cap.proficiency)
                        break
            
            if capability_scores:
                capability_match = sum(capability_scores) / len(capability_scores)
                score += capability_match * 0.3
        else:
            score += 0.3  # Full score if no specific capabilities required
        
        # Performance history score (20%)
        performance_score = agent.performance_score * agent.reliability_score
        score += performance_score * 0.2
        
        # Task type affinity score (10%)
        task_type_metrics = self.performance_metrics.get(
            f"{agent.agent_id}:{task.task_type}", 
            {'success_rate': 0.5}
        )
        affinity_score = task_type_metrics['success_rate']
        score += affinity_score * 0.1
        
        return score
    
    async def _simulate_agent_execution(self, agent: AgentProfile, task: CoordinationTask):
        """Simulate agent executing a task"""
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        
        # Simulate work based on task type
        duration = task.estimated_duration * (0.5 + agent.performance_score * 0.5)
        await asyncio.sleep(min(duration / 10, 2.0))  # Scaled down for demo
        
        # Simulate success/failure
        success = agent.reliability_score > 0.2  # High success rate for demo
        
        if success:
            await self.handle_task_completion(agent.agent_id, task.task_id, {
                'result': f"Task {task.task_type} completed successfully",
                'duration': duration
            })
        else:
            await self.handle_task_failure(agent.agent_id, task.task_id, {
                'error': 'Simulated failure for demonstration'
            })
    
    async def handle_task_completion(self, agent_id: str, task_id: str, 
                                   result: Dict[str, Any]):
        """Handle task completion with cascading updates"""
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Unknown task {task_id}")
            return
        
        # Update task status
        task.status = TaskStatus.COMPLETED
        task.output_data = result
        task.completed_at = datetime.utcnow()
        task.actual_duration = result.get('duration', 60.0)
        
        # Update agent metrics
        agent = self.agents[agent_id]
        agent.current_load -= 1
        agent.tasks_completed += 1
        
        # Update performance metrics
        self._update_agent_performance(agent, task, success=True)
        
        # Add to completed tasks
        self.completed_tasks.add(task_id)
        
        # Check for unblocked tasks
        await self._check_unblocked_tasks()
        
        # Check if parent task is complete
        if task.parent_task_id:
            await self._check_parent_task_completion(task.parent_task_id)
        
        # Publish completion event
        await self._publish_event('task_completed', {
            'task_id': task_id,
            'agent_id': agent_id,
            'duration': task.actual_duration
        })
    
    async def handle_task_failure(self, agent_id: str, task_id: str, 
                                error: Dict[str, Any]):
        """Handle task failure with retry logic"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        # Update agent metrics
        agent = self.agents[agent_id]
        agent.current_load -= 1
        agent.tasks_failed += 1
        
        # Update performance metrics
        self._update_agent_performance(agent, task, success=False)
        
        # Check retry logic
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            
            # Adjust priority for retry
            retry_priority = TaskPriority(min(task.priority.value - 1, 1))
            
            # Requeue with higher priority
            await self.task_queue.put((retry_priority.value, task.created_at.timestamp(), task.task_id))
            
            logger.info(f"Task {task_id} queued for retry ({task.retry_count}/{task.max_retries})")
        else:
            # Mark as failed
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            
            # Publish failure event
            await self._publish_event('task_failed', {
                'task_id': task_id,
                'agent_id': agent_id,
                'error': error
            })
    
    def _update_agent_performance(self, agent: AgentProfile, 
                                 task: CoordinationTask, success: bool):
        """Update agent performance metrics with decay"""
        # Update task-specific metrics
        key = f"{agent.agent_id}:{task.task_type}"
        metrics = self.performance_metrics[key]
        
        metrics['tasks_completed'] += 1
        if success:
            metrics['success_rate'] = min(1.0, metrics['success_rate'] + 0.02)
        else:
            metrics['success_rate'] = max(0.0, metrics['success_rate'] - 0.05)
        
        # Update average duration
        if success and task.actual_duration > 0:
            if metrics['average_duration'] == 0:
                metrics['average_duration'] = task.actual_duration
            else:
                metrics['average_duration'] = (
                    metrics['average_duration'] * 0.9 + task.actual_duration * 0.1
                )
        
        # Update agent scores
        if success:
            agent.performance_score = min(1.0, agent.performance_score + 0.01)
            agent.reliability_score = min(1.0, agent.reliability_score + 0.02)
        else:
            agent.performance_score *= self.config['performance_decay_rate']
            agent.reliability_score = max(0.1, agent.reliability_score - 0.05)
    
    async def _check_unblocked_tasks(self):
        """Check if any blocked tasks can now be executed"""
        unblocked = []
        
        for task_id, task in self.blocked_tasks.items():
            if task.is_ready_to_execute(self.completed_tasks):
                unblocked.append(task_id)
                await self.task_queue.put((task.priority.value, task.created_at.timestamp(), task.task_id))
        
        # Remove unblocked tasks
        for task_id in unblocked:
            del self.blocked_tasks[task_id]
            logger.info(f"Task {task_id} unblocked")
    
    async def _check_parent_task_completion(self, parent_task_id: str):
        """Check if all subtasks of a parent are complete"""
        # Find all subtasks
        subtasks = [
            task for task in self.tasks.values()
            if task.parent_task_id == parent_task_id
        ]
        
        # Check if all are complete
        all_complete = all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            for task in subtasks
        )
        
        if all_complete:
            parent_task = self.tasks.get(parent_task_id)
            if parent_task and parent_task.status != TaskStatus.COMPLETED:
                parent_task.status = TaskStatus.COMPLETED
                parent_task.completed_at = datetime.utcnow()
                self.completed_tasks.add(parent_task_id)
                
                # Publish parent completion event
                await self._publish_event('parent_task_completed', {
                    'task_id': parent_task_id,
                    'subtasks': len(subtasks)
                })
    
    async def _heartbeat_monitor(self):
        """Monitor agent heartbeats"""
        while True:
            try:
                await asyncio.sleep(self.config['heartbeat_interval'])
                
                current_time = datetime.utcnow()
                for agent in self.agents.values():
                    # Simulate heartbeat
                    agent.last_heartbeat = current_time
                    
                    # Update status based on load
                    if agent.current_load == 0:
                        agent.status = 'active'
                    elif agent.current_load < agent.max_concurrent_tasks:
                        agent.status = 'busy'
                    else:
                        agent.status = 'overloaded'
                        
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
    
    async def _load_balancer(self):
        """Dynamic load balancing across agents"""
        while True:
            try:
                await asyncio.sleep(self.config['load_balancing_interval'])
                
                # Skip for now - simplified implementation
                
            except Exception as e:
                logger.error(f"Load balancer error: {e}")
    
    async def _deadlock_detector(self):
        """Detect and resolve task deadlocks"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Skip for now - simplified implementation
                    
            except Exception as e:
                logger.error(f"Deadlock detector error: {e}")
    
    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish coordination events"""
        event = {
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        # Notify event handlers
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def subscribe_to_event(self, event_type: str, handler: Callable):
        """Subscribe to coordination events"""
        self.event_handlers[event_type].append(handler)
    
    async def get_coordination_status(self) -> Dict[str, Any]:
        """Get comprehensive coordination status"""
        return {
            'agents': {
                'total': len(self.agents),
                'active': sum(1 for a in self.agents.values() if a.status == 'active'),
                'busy': sum(1 for a in self.agents.values() if a.status == 'busy'),
                'load_distribution': {
                    agent_id: agent.current_load
                    for agent_id, agent in self.agents.items()
                }
            },
            'tasks': {
                'total': len(self.tasks),
                'pending': sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
                'in_progress': sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS),
                'completed': len(self.completed_tasks),
                'failed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
                'blocked': len(self.blocked_tasks)
            },
            'plans': {
                'active': len(self.coordination_plans),
                'completion_rate': self._calculate_plan_completion_rate()
            },
            'performance': {
                'average_task_duration': self._calculate_average_task_duration(),
                'success_rate': self._calculate_overall_success_rate(),
                'throughput': self._calculate_throughput()
            }
        }
    
    def _calculate_plan_completion_rate(self) -> float:
        """Calculate overall plan completion rate"""
        if not self.coordination_plans:
            return 0.0
        
        completion_rates = []
        for plan in self.coordination_plans.values():
            total_tasks = len(plan.task_graph.nodes())
            completed = sum(
                1 for node in plan.task_graph.nodes()
                if self.tasks.get(node) and self.tasks[node].status == TaskStatus.COMPLETED
            )
            completion_rates.append(completed / total_tasks if total_tasks > 0 else 0)
        
        return sum(completion_rates) / len(completion_rates) if completion_rates else 0.0
    
    def _calculate_average_task_duration(self) -> float:
        """Calculate average task completion time"""
        durations = [
            task.actual_duration
            for task in self.tasks.values()
            if task.status == TaskStatus.COMPLETED and task.actual_duration > 0
        ]
        return sum(durations) / len(durations) if durations else 0.0
    
    def _calculate_overall_success_rate(self) -> float:
        """Calculate overall task success rate"""
        total = sum(1 for t in self.tasks.values() if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED])
        if total == 0:
            return 1.0
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        return completed / total
    
    def _calculate_throughput(self) -> float:
        """Calculate tasks completed per minute"""
        # Get tasks completed in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_completed = sum(
            1 for task in self.tasks.values()
            if task.status == TaskStatus.COMPLETED and task.completed_at and task.completed_at > one_hour_ago
        )
        return recent_completed / 60.0  # Tasks per minute