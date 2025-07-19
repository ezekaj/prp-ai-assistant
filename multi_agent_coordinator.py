#!/usr/bin/env python3
"""
Multi-Agent Coordinator for PRP AI Assistant
Enables chat-based multi-agent coordination
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import redis
from celery import Celery
from logging_config import get_logger

logger = get_logger(__name__)

class AgentType(Enum):
    CODE_GENERATION = "code_generation"
    TESTING = "testing"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DELEGATED = "delegated"

@dataclass
class AgentTask:
    """Represents a task for an agent"""
    task_id: str
    agent_type: AgentType
    description: str
    context: Dict[str, Any]
    priority: int = 5  # 1-10, 10 is highest
    dependencies: List[str] = None
    parent_task_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class ChatMessage:
    """Chat message for multi-agent communication"""
    message_id: str
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    message_type: str  # 'request', 'response', 'notification', 'chat'
    content: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class MultiAgentCoordinator:
    """Central coordinator for multi-agent system"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.task_queue: Dict[str, AgentTask] = {}
        self.chat_history: List[ChatMessage] = []
        self.agent_capabilities: Dict[AgentType, List[str]] = {
            AgentType.CODE_GENERATION: [
                "write_code", "refactor_code", "fix_bugs", "implement_features"
            ],
            AgentType.TESTING: [
                "write_tests", "run_tests", "analyze_coverage", "performance_testing"
            ],
            AgentType.SECURITY: [
                "security_scan", "vulnerability_analysis", "penetration_testing"
            ],
            AgentType.DEPLOYMENT: [
                "deploy_application", "configure_infrastructure", "monitoring_setup"
            ],
            AgentType.ANALYSIS: [
                "code_analysis", "performance_analysis", "architecture_review"
            ],
            AgentType.DOCUMENTATION: [
                "write_docs", "api_documentation", "user_guides"
            ]
        }
        
        logger.info("multi_agent_coordinator_initialized")
    
    async def register_agent(self, agent_id: str, agent_type: AgentType, capabilities: List[str]) -> bool:
        """Register a new agent with the coordinator"""
        agent_info = {
            'agent_id': agent_id,
            'agent_type': agent_type.value,
            'capabilities': capabilities,
            'status': 'active',
            'last_heartbeat': datetime.utcnow().isoformat(),
            'current_tasks': []
        }
        
        self.active_agents[agent_id] = agent_info
        
        # Notify other agents
        await self.broadcast_message(
            from_agent="coordinator",
            message_type="notification",
            content=f"Agent {agent_id} ({agent_type.value}) has joined the system",
            data={"agent_info": agent_info}
        )
        
        logger.info("agent_registered", agent_id=agent_id, agent_type=agent_type.value)
        return True
    
    async def create_task(self, description: str, agent_type: AgentType, 
                         context: Dict[str, Any], priority: int = 5) -> str:
        """Create a new task for an agent"""
        task_id = str(uuid.uuid4())
        task = AgentTask(
            task_id=task_id,
            agent_type=agent_type,
            description=description,
            context=context,
            priority=priority
        )
        
        self.task_queue[task_id] = task
        
        # Find best available agent
        assigned_agent = await self.assign_task_to_agent(task)
        
        if assigned_agent:
            await self.send_message(
                from_agent="coordinator",
                to_agent=assigned_agent,
                message_type="request",
                content=f"New task assigned: {description}",
                data={"task": asdict(task)}
            )
            
            logger.info("task_created_and_assigned", 
                       task_id=task_id, 
                       agent_id=assigned_agent,
                       description=description)
        else:
            logger.warning("no_available_agent", task_id=task_id, agent_type=agent_type.value)
        
        return task_id
    
    async def assign_task_to_agent(self, task: AgentTask) -> Optional[str]:
        """Assign a task to the best available agent"""
        suitable_agents = []
        
        for agent_id, agent_info in self.active_agents.items():
            if (agent_info['agent_type'] == task.agent_type.value and 
                agent_info['status'] == 'active'):
                
                # Calculate agent score based on current load and capabilities
                current_tasks = len(agent_info['current_tasks'])
                score = 100 - (current_tasks * 10)  # Lower score for busier agents
                
                suitable_agents.append((agent_id, score))
        
        if suitable_agents:
            # Sort by score and pick the best agent
            suitable_agents.sort(key=lambda x: x[1], reverse=True)
            best_agent = suitable_agents[0][0]
            
            # Update agent's task list
            self.active_agents[best_agent]['current_tasks'].append(task.task_id)
            task.status = TaskStatus.DELEGATED
            
            return best_agent
        
        return None
    
    async def send_message(self, from_agent: str, to_agent: str, message_type: str, 
                          content: str, data: Optional[Dict[str, Any]] = None):
        """Send a message to a specific agent"""
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            data=data
        )
        
        self.chat_history.append(message)
        
        # Publish to Redis channel
        channel = f"agent:{to_agent}"
        await self._publish_message(channel, message)
        
        logger.info("message_sent", 
                   from_agent=from_agent, 
                   to_agent=to_agent, 
                   message_type=message_type)
    
    async def broadcast_message(self, from_agent: str, message_type: str, 
                               content: str, data: Optional[Dict[str, Any]] = None):
        """Broadcast a message to all agents"""
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=None,
            message_type=message_type,
            content=content,
            data=data
        )
        
        self.chat_history.append(message)
        
        # Broadcast to all agents
        for agent_id in self.active_agents.keys():
            channel = f"agent:{agent_id}"
            await self._publish_message(channel, message)
        
        logger.info("message_broadcasted", 
                   from_agent=from_agent, 
                   message_type=message_type)
    
    async def _publish_message(self, channel: str, message: ChatMessage):
        """Publish message to Redis channel"""
        try:
            message_data = {
                'message_id': message.message_id,
                'from_agent': message.from_agent,
                'to_agent': message.to_agent,
                'message_type': message.message_type,
                'content': message.content,
                'data': message.data,
                'timestamp': message.timestamp.isoformat()
            }
            
            self.redis_client.publish(channel, json.dumps(message_data))
        except Exception as e:
            logger.error("failed_to_publish_message", error=str(e), channel=channel)
    
    async def handle_chat_command(self, user_input: str) -> str:
        """Handle chat commands for multi-agent coordination"""
        
        # Parse command
        if user_input.startswith("/"):
            return await self._handle_slash_command(user_input)
        
        # Natural language processing for task creation
        return await self._process_natural_language(user_input)
    
    async def _handle_slash_command(self, command: str) -> str:
        """Handle slash commands"""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == "/agents":
            return await self._list_agents()
        
        elif cmd == "/tasks":
            return await self._list_tasks()
        
        elif cmd == "/create":
            if len(parts) < 3:
                return "Usage: /create <agent_type> <description>"
            
            agent_type_str = parts[1].upper()
            description = " ".join(parts[2:])
            
            try:
                agent_type = AgentType(agent_type_str.lower())
                task_id = await self.create_task(description, agent_type, {})
                return f"Task created: {task_id}"
            except ValueError:
                return f"Invalid agent type. Available: {[t.value for t in AgentType]}"
        
        elif cmd == "/status":
            if len(parts) < 2:
                return "Usage: /status <task_id>"
            
            task_id = parts[1]
            task = self.task_queue.get(task_id)
            if task:
                return f"Task {task_id}: {task.status.value} - {task.description}"
            else:
                return f"Task {task_id} not found"
        
        elif cmd == "/chat":
            if len(parts) < 3:
                return "Usage: /chat <agent_id> <message>"
            
            agent_id = parts[1]
            message = " ".join(parts[2:])
            
            if agent_id in self.active_agents:
                await self.send_message("user", agent_id, "chat", message)
                return f"Message sent to {agent_id}"
            else:
                return f"Agent {agent_id} not found"
        
        elif cmd == "/broadcast":
            if len(parts) < 2:
                return "Usage: /broadcast <message>"
            
            message = " ".join(parts[1:])
            await self.broadcast_message("user", "chat", message)
            return "Message broadcasted to all agents"
        
        else:
            return f"Unknown command: {cmd}"
    
    async def _process_natural_language(self, user_input: str) -> str:
        """Process natural language for task creation"""
        
        # Simple keyword matching for demo
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["write code", "implement", "develop", "create function"]):
            task_id = await self.create_task(user_input, AgentType.CODE_GENERATION, {"user_request": user_input})
            return f"Code generation task created: {task_id}\\nAssigned to Code Agent for implementation."
        
        elif any(word in user_input_lower for word in ["test", "unit test", "integration test"]):
            task_id = await self.create_task(user_input, AgentType.TESTING, {"user_request": user_input})
            return f"Testing task created: {task_id}\\nAssigned to Testing Agent."
        
        elif any(word in user_input_lower for word in ["security", "vulnerability", "secure", "audit"]):
            task_id = await self.create_task(user_input, AgentType.SECURITY, {"user_request": user_input})
            return f"Security analysis task created: {task_id}\\nAssigned to Security Agent."
        
        elif any(word in user_input_lower for word in ["deploy", "deployment", "production", "release"]):
            task_id = await self.create_task(user_input, AgentType.DEPLOYMENT, {"user_request": user_input})
            return f"Deployment task created: {task_id}\\nAssigned to Deployment Agent."
        
        elif any(word in user_input_lower for word in ["analyze", "review", "performance", "optimization"]):
            task_id = await self.create_task(user_input, AgentType.ANALYSIS, {"user_request": user_input})
            return f"Analysis task created: {task_id}\\nAssigned to Analysis Agent."
        
        elif any(word in user_input_lower for word in ["document", "documentation", "docs", "readme"]):
            task_id = await self.create_task(user_input, AgentType.DOCUMENTATION, {"user_request": user_input})
            return f"Documentation task created: {task_id}\\nAssigned to Documentation Agent."
        
        else:
            return "I can help you with code generation, testing, security analysis, deployment, code analysis, or documentation. Please specify what you'd like to do."
    
    async def _list_agents(self) -> str:
        """List all active agents"""
        if not self.active_agents:
            return "No agents are currently active."
        
        result = "Active Agents:\\n"
        for agent_id, info in self.active_agents.items():
            current_tasks = len(info['current_tasks'])
            result += f"- {agent_id} ({info['agent_type']}) - {current_tasks} active tasks\\n"
        
        return result
    
    async def _list_tasks(self) -> str:
        """List all tasks"""
        if not self.task_queue:
            return "No tasks in queue."
        
        result = "Task Queue:\\n"
        for task_id, task in self.task_queue.items():
            result += f"- {task_id[:8]}... ({task.status.value}): {task.description[:50]}...\\n"
        
        return result
    
    def get_chat_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent chat history"""
        recent_messages = self.chat_history[-limit:] if limit else self.chat_history
        return [asdict(msg) for msg in recent_messages]


# Demo chat interface
async def demo_multi_agent_chat():
    """Demo the multi-agent chat interface"""
    coordinator = MultiAgentCoordinator()
    
    print("Multi-Agent PRP Assistant - Chat Demo")
    print("=" * 50)
    print("Commands:")
    print("  /agents - List active agents")
    print("  /tasks - List current tasks")
    print("  /create <agent_type> <description> - Create a task")
    print("  /status <task_id> - Check task status")
    print("  /chat <agent_id> <message> - Send message to agent")
    print("  /broadcast <message> - Broadcast to all agents")
    print("  Or just type natural language requests!")
    print("=" * 50)
    
    # Simulate some agents registering
    await coordinator.register_agent("code-agent-1", AgentType.CODE_GENERATION, 
                                    ["write_code", "refactor_code", "fix_bugs"])
    await coordinator.register_agent("test-agent-1", AgentType.TESTING, 
                                    ["write_tests", "run_tests", "analyze_coverage"])
    await coordinator.register_agent("security-agent-1", AgentType.SECURITY, 
                                    ["security_scan", "vulnerability_analysis"])
    
    print("\\n3 agents registered and ready!")
    print("Try: 'write a function to process user data'")
    print("Or: '/agents' to see active agents\\n")
    
    # Demo some interactions
    demo_inputs = [
        "write a function to process user data",
        "/agents",
        "/tasks",
        "run security analysis on the authentication module",
        "/status task_id_here"
    ]
    
    for user_input in demo_inputs:
        print(f"User: {user_input}")
        response = await coordinator.handle_chat_command(user_input)
        print(f"Assistant: {response}\\n")

if __name__ == "__main__":
    asyncio.run(demo_multi_agent_chat())