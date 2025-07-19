#!/usr/bin/env python3
"""
Sample Agent Implementation for Multi-Agent System
Shows how an agent connects and communicates with the coordinator
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

import redis
from multi_agent_coordinator import AgentType, TaskStatus, ChatMessage
from logging_config import get_logger

logger = get_logger(__name__)

class BaseAgent:
    """Base class for all specialized agents"""
    
    def __init__(self, agent_id: str, agent_type: AgentType, 
                 capabilities: list, redis_url: str = "redis://localhost:6379/0"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.redis_client = redis.from_url(redis_url)
        self.pubsub = self.redis_client.pubsub()
        self.current_tasks: Dict[str, Dict[str, Any]] = {}
        self.is_active = False
        
        logger.info("agent_initialized", agent_id=agent_id, agent_type=agent_type.value)
    
    async def start(self):
        """Start the agent and connect to coordinator"""
        self.is_active = True
        
        # Subscribe to agent channel
        channel = f"agent:{self.agent_id}"
        self.pubsub.subscribe(channel)
        
        # Register with coordinator
        await self._register_with_coordinator()
        
        # Start message processing loop
        asyncio.create_task(self._message_processing_loop())
        
        logger.info("agent_started", agent_id=self.agent_id)
    
    async def stop(self):
        """Stop the agent"""
        self.is_active = False
        self.pubsub.unsubscribe()
        logger.info("agent_stopped", agent_id=self.agent_id)
    
    async def _register_with_coordinator(self):
        """Register this agent with the coordinator"""
        registration_data = {
            'action': 'register',
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'capabilities': self.capabilities,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.redis_client.publish("coordinator:register", json.dumps(registration_data))
        logger.info("registration_sent", agent_id=self.agent_id)
    
    async def _message_processing_loop(self):
        """Process incoming messages from coordinator and other agents"""
        while self.is_active:
            try:
                message = self.pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    await self._handle_message(message['data'])
            except Exception as e:
                logger.error("message_processing_error", agent_id=self.agent_id, error=str(e))
                await asyncio.sleep(1)
    
    async def _handle_message(self, message_data: bytes):
        """Handle incoming message"""
        try:
            data = json.loads(message_data.decode('utf-8'))
            message_type = data.get('message_type')
            
            if message_type == 'request':
                await self._handle_task_request(data)
            elif message_type == 'chat':
                await self._handle_chat_message(data)
            elif message_type == 'notification':
                await self._handle_notification(data)
            
        except Exception as e:
            logger.error("message_handling_error", agent_id=self.agent_id, error=str(e))
    
    async def _handle_task_request(self, data: Dict[str, Any]):
        """Handle task assignment from coordinator"""
        task_data = data.get('data', {}).get('task', {})
        task_id = task_data.get('task_id')
        description = task_data.get('description')
        
        logger.info("task_received", agent_id=self.agent_id, task_id=task_id, description=description)
        
        # Store task
        self.current_tasks[task_id] = {
            'task_data': task_data,
            'status': TaskStatus.IN_PROGRESS.value,
            'started_at': datetime.utcnow()
        }
        
        # Send acknowledgment
        await self._send_message_to_coordinator(
            message_type="response",
            content=f"Task {task_id} acknowledged and started",
            data={"task_id": task_id, "status": "in_progress"}
        )
        
        # Process the task
        asyncio.create_task(self._process_task(task_id, task_data))
    
    async def _process_task(self, task_id: str, task_data: Dict[str, Any]):
        """Process the assigned task (to be overridden by specialized agents)"""
        await asyncio.sleep(2)  # Simulate work
        
        # Mock result
        result = {
            'task_id': task_id,
            'status': 'completed',
            'result': f"Task '{task_data.get('description')}' completed by {self.agent_id}",
            'completion_time': datetime.utcnow().isoformat()
        }
        
        # Update task status
        self.current_tasks[task_id]['status'] = TaskStatus.COMPLETED.value
        self.current_tasks[task_id]['result'] = result
        
        # Notify coordinator
        await self._send_message_to_coordinator(
            message_type="response",
            content=f"Task {task_id} completed successfully",
            data=result
        )
        
        logger.info("task_completed", agent_id=self.agent_id, task_id=task_id)
    
    async def _handle_chat_message(self, data: Dict[str, Any]):
        """Handle chat message from user or other agents"""
        from_agent = data.get('from_agent')
        content = data.get('content')
        
        logger.info("chat_message_received", 
                   agent_id=self.agent_id, 
                   from_agent=from_agent, 
                   content=content)
        
        # Generate a response
        response = await self._generate_chat_response(content, from_agent)
        
        if response:
            await self._send_message_to_coordinator(
                message_type="chat",
                content=response,
                data={"in_reply_to": data.get('message_id')}
            )
    
    async def _generate_chat_response(self, content: str, from_agent: str) -> str:
        """Generate response to chat message (to be overridden)"""
        return f"Hello {from_agent}! I'm {self.agent_id} and I received your message: '{content}'"
    
    async def _handle_notification(self, data: Dict[str, Any]):
        """Handle notification from coordinator"""
        content = data.get('content')
        logger.info("notification_received", agent_id=self.agent_id, content=content)
    
    async def _send_message_to_coordinator(self, message_type: str, content: str, 
                                          data: Optional[Dict[str, Any]] = None):
        """Send message to coordinator"""
        message_data = {
            'message_id': str(uuid.uuid4()),
            'from_agent': self.agent_id,
            'to_agent': 'coordinator',
            'message_type': message_type,
            'content': content,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.redis_client.publish("coordinator:inbox", json.dumps(message_data))


class CodeGenerationAgent(BaseAgent):
    """Specialized agent for code generation tasks"""
    
    def __init__(self, agent_id: str = None):
        if not agent_id:
            agent_id = f"code-agent-{str(uuid.uuid4())[:8]}"
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.CODE_GENERATION,
            capabilities=["write_code", "refactor_code", "fix_bugs", "implement_features"]
        )
    
    async def _process_task(self, task_id: str, task_data: Dict[str, Any]):
        """Process code generation task"""
        description = task_data.get('description', '')
        context = task_data.get('context', {})
        
        logger.info("processing_code_task", 
                   agent_id=self.agent_id, 
                   task_id=task_id, 
                   description=description)
        
        # Simulate code generation work
        await asyncio.sleep(3)
        
        # Mock generated code
        generated_code = f'''
def process_data(data):
    """
    Generated function for: {description}
    """
    result = []
    for item in data:
        # Process each item
        processed_item = {{
            'id': item.get('id'),
            'processed_at': datetime.utcnow(),
            'status': 'processed'
        }}
        result.append(processed_item)
    return result
'''
        
        result = {
            'task_id': task_id,
            'status': 'completed',
            'result': {
                'code': generated_code,
                'description': description,
                'files_created': ['data_processor.py'],
                'tests_needed': True
            },
            'completion_time': datetime.utcnow().isoformat()
        }
        
        # Update task status
        self.current_tasks[task_id]['status'] = TaskStatus.COMPLETED.value
        self.current_tasks[task_id]['result'] = result
        
        # Notify coordinator
        await self._send_message_to_coordinator(
            message_type="response",
            content=f"Code generation completed for: {description}",
            data=result
        )
        
        logger.info("code_generation_completed", agent_id=self.agent_id, task_id=task_id)
    
    async def _generate_chat_response(self, content: str, from_agent: str) -> str:
        """Generate code-specific chat response"""
        content_lower = content.lower()
        
        if "function" in content_lower:
            return f"I can help you write functions! What specific functionality do you need?"
        elif "bug" in content_lower:
            return f"I'm great at finding and fixing bugs. Can you share the problematic code?"
        elif "refactor" in content_lower:
            return f"Refactoring is one of my specialties. What code needs improvement?"
        else:
            return f"I'm the Code Generation Agent. I can write code, fix bugs, and refactor existing code. How can I help you?"


# Demo function
async def demo_agent():
    """Demo the agent functionality"""
    print("Starting Code Generation Agent Demo...")
    
    # Create and start agent
    agent = CodeGenerationAgent("demo-code-agent")
    await agent.start()
    
    print(f"Agent {agent.agent_id} started and registered with coordinator")
    print("Agent is now listening for tasks and messages...")
    
    # Keep running for demo
    await asyncio.sleep(10)
    
    await agent.stop()
    print("Agent stopped")

if __name__ == "__main__":
    asyncio.run(demo_agent())