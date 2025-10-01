#!/usr/bin/env python3
"""
Simplified Multi-Agent Chat Demo
Shows how to use the multi-agent system in chat without Redis dependency
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

# Simplified versions without Redis dependency
@dataclass
class SimpleTask:
    task_id: str
    agent_type: str
    description: str
    status: str = "pending"
    result: str = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class SimpleMultiAgentChat:
    """Simplified multi-agent chat system for demo"""
    
    def __init__(self):
        self.agents = {
            "code-agent": {
                "type": "code_generation",
                "status": "active",
                "capabilities": ["write_code", "refactor_code", "fix_bugs"]
            },
            "test-agent": {
                "type": "testing", 
                "status": "active",
                "capabilities": ["write_tests", "run_tests", "coverage_analysis"]
            },
            "security-agent": {
                "type": "security",
                "status": "active", 
                "capabilities": ["security_scan", "vulnerability_analysis"]
            },
            "deploy-agent": {
                "type": "deployment",
                "status": "active",
                "capabilities": ["deploy_app", "configure_infrastructure"]
            }
        }
        self.tasks: Dict[str, SimpleTask] = {}
        self.chat_history: List[Dict[str, Any]] = []
    
    async def handle_chat(self, user_input: str) -> str:
        """Handle user chat input and return response"""
        
        # Handle slash commands
        if user_input.startswith("/"):
            return await self._handle_command(user_input)
        
        # Handle natural language
        return await self._process_natural_language(user_input)
    
    async def _handle_command(self, command: str) -> str:
        """Handle slash commands"""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == "/help":
            return self._get_help()
        
        elif cmd == "/agents":
            result = "🤖 Active Agents:\\n"
            for agent_id, info in self.agents.items():
                result += f"  • {agent_id} ({info['type']}) - {info['status']}\\n"
            return result
        
        elif cmd == "/tasks":
            if not self.tasks:
                return "📋 No tasks in queue"
            
            result = "📋 Current Tasks:\\n"
            for task_id, task in self.tasks.items():
                status_icon = "✅" if task.status == "completed" else "⏳" if task.status == "in_progress" else "📝"
                result += f"  {status_icon} {task_id[:8]}... ({task.status}): {task.description[:50]}...\\n"
            return result
        
        elif cmd == "/status":
            if len(parts) < 2:
                return "Usage: /status <task_id>"
            
            task_id = parts[1]
            # Find task by partial ID
            matching_task = None
            for tid, task in self.tasks.items():
                if tid.startswith(task_id):
                    matching_task = task
                    break
            
            if matching_task:
                return f"📊 Task Status:\\n  ID: {matching_task.task_id}\\n  Status: {matching_task.status}\\n  Description: {matching_task.description}\\n  Created: {matching_task.created_at}"
            else:
                return f"❌ Task not found: {task_id}"
        
        elif cmd == "/chat":
            if len(parts) < 3:
                return "Usage: /chat <agent_id> <message>"
            
            agent_id = parts[1]
            message = " ".join(parts[2:])
            
            if agent_id in self.agents:
                response = await self._send_direct_message(agent_id, message)
                return f"💬 Message sent to {agent_id}:\\n  Agent response: {response}"
            else:
                return f"❌ Agent not found: {agent_id}. Available: {', '.join(self.agents.keys())}"
        
        else:
            return f"❌ Unknown command: {cmd}. Type /help for available commands."
    
    async def _process_natural_language(self, user_input: str) -> str:
        """Process natural language input"""
        user_input_lower = user_input.lower()
        
        # Code generation keywords
        if any(keyword in user_input_lower for keyword in [
            "write", "code", "function", "implement", "create", "develop", "build"
        ]):
            return await self._create_code_task(user_input)
        
        # Testing keywords  
        elif any(keyword in user_input_lower for keyword in [
            "test", "unit test", "integration", "coverage", "testing"
        ]):
            return await self._create_test_task(user_input)
        
        # Security keywords
        elif any(keyword in user_input_lower for keyword in [
            "security", "secure", "vulnerability", "audit", "scan", "penetration"
        ]):
            return await self._create_security_task(user_input)
        
        # Deployment keywords
        elif any(keyword in user_input_lower for keyword in [
            "deploy", "deployment", "production", "release", "infrastructure"
        ]):
            return await self._create_deploy_task(user_input)
        
        else:
            return ("🤔 I can help you with:\\n"
                   "  • Code generation (write, implement, create)\\n"
                   "  • Testing (test, unit test, coverage)\\n" 
                   "  • Security (security scan, audit)\\n"
                   "  • Deployment (deploy, production)\\n\\n"
                   "Try: 'write a function to process user data' or '/help'")
    
    async def _create_code_task(self, description: str) -> str:
        """Create a code generation task"""
        task_id = str(uuid.uuid4())
        task = SimpleTask(
            task_id=task_id,
            agent_type="code_generation", 
            description=description
        )
        
        self.tasks[task_id] = task
        
        # Simulate task processing
        asyncio.create_task(self._process_code_task(task_id))
        
        return (f"🔧 Code Generation Task Created\\n"
               f"  Task ID: {task_id[:8]}...\\n"
               f"  Assigned to: code-agent\\n"
               f"  Description: {description}\\n"
               f"  Status: Processing...")
    
    async def _create_test_task(self, description: str) -> str:
        """Create a testing task"""
        task_id = str(uuid.uuid4())
        task = SimpleTask(
            task_id=task_id,
            agent_type="testing",
            description=description
        )
        
        self.tasks[task_id] = task
        asyncio.create_task(self._process_test_task(task_id))
        
        return (f"🧪 Testing Task Created\\n"
               f"  Task ID: {task_id[:8]}...\\n"
               f"  Assigned to: test-agent\\n"
               f"  Description: {description}\\n"
               f"  Status: Processing...")
    
    async def _create_security_task(self, description: str) -> str:
        """Create a security task"""
        task_id = str(uuid.uuid4())
        task = SimpleTask(
            task_id=task_id,
            agent_type="security",
            description=description
        )
        
        self.tasks[task_id] = task
        asyncio.create_task(self._process_security_task(task_id))
        
        return (f"🔒 Security Task Created\\n"
               f"  Task ID: {task_id[:8]}...\\n"
               f"  Assigned to: security-agent\\n"
               f"  Description: {description}\\n"
               f"  Status: Processing...")
    
    async def _create_deploy_task(self, description: str) -> str:
        """Create a deployment task"""
        task_id = str(uuid.uuid4())
        task = SimpleTask(
            task_id=task_id,
            agent_type="deployment",
            description=description
        )
        
        self.tasks[task_id] = task
        asyncio.create_task(self._process_deploy_task(task_id))
        
        return (f"🚀 Deployment Task Created\\n"
               f"  Task ID: {task_id[:8]}...\\n"
               f"  Assigned to: deploy-agent\\n"
               f"  Description: {description}\\n"
               f"  Status: Processing...")
    
    async def _process_code_task(self, task_id: str):
        """Simulate code generation processing"""
        await asyncio.sleep(2)  # Simulate work
        
        task = self.tasks[task_id]
        task.status = "in_progress"
        
        await asyncio.sleep(3)  # More work
        
        # Generate mock code result
        task.result = f"""
Generated code for: {task.description}

```python
def process_user_data(data):
    \"\"\"
    Process user data with validation and transformation
    Generated by Code Agent
    \"\"\"
    if not data:
        return None
    
    processed = {{
        'user_id': data.get('id'),
        'username': data.get('username', '').lower(),
        'email': data.get('email', '').lower(),
        'processed_at': datetime.utcnow(),
        'status': 'active'
    }}
    
    return processed
```

Files created: user_processor.py
Next steps: Add unit tests, security review
"""
        task.status = "completed"
        
        # Add to chat history
        self.chat_history.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": "code-agent",
            "message": f"Completed code generation for task {task_id[:8]}..."
        })
    
    async def _process_test_task(self, task_id: str):
        """Simulate testing processing"""
        await asyncio.sleep(1.5)
        
        task = self.tasks[task_id]
        task.status = "in_progress"
        
        await asyncio.sleep(2.5)
        
        task.result = f"""
Test suite generated for: {task.description}

```python
import unittest
from user_processor import process_user_data

class TestUserProcessor(unittest.TestCase):
    
    def test_valid_user_data(self):
        data = {{'id': 123, 'username': 'JohnDoe', 'email': 'JOHN@EXAMPLE.COM'}}
        result = process_user_data(data)
        
        self.assertEqual(result['user_id'], 123)
        self.assertEqual(result['username'], 'johndoe')
        self.assertEqual(result['email'], 'john@example.com')
    
    def test_empty_data(self):
        result = process_user_data(None)
        self.assertIsNone(result)
```

Test Results: 15 tests, 15 passed ✅
Coverage: 95%
"""
        task.status = "completed"
        
        self.chat_history.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": "test-agent", 
            "message": f"Completed test generation for task {task_id[:8]}..."
        })
    
    async def _process_security_task(self, task_id: str):
        """Simulate security processing"""
        await asyncio.sleep(2)
        
        task = self.tasks[task_id]
        task.status = "in_progress"
        
        await asyncio.sleep(4)  # Security scans take longer
        
        task.result = f"""
Security Analysis for: {task.description}

CRITICAL ISSUES FOUND: 0 ✅
HIGH ISSUES FOUND: 1 ⚠️
MEDIUM ISSUES FOUND: 2 ⚠️

HIGH PRIORITY:
- Missing input validation for email field
  Recommendation: Add email format validation

MEDIUM PRIORITY:  
- No rate limiting on user registration
- Missing CSRF protection
  Recommendations: Implement rate limiting, add CSRF tokens

OVERALL SECURITY SCORE: 7.5/10
"""
        task.status = "completed"
        
        self.chat_history.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": "security-agent",
            "message": f"Completed security analysis for task {task_id[:8]}..."
        })
    
    async def _process_deploy_task(self, task_id: str):
        """Simulate deployment processing"""
        await asyncio.sleep(1)
        
        task = self.tasks[task_id]
        task.status = "in_progress"
        
        await asyncio.sleep(5)  # Deployment takes time
        
        task.result = f"""
Deployment completed for: {task.description}

DEPLOYMENT SUMMARY:
- Environment: Production
- Instance: 3 containers deployed
- Load Balancer: Configured ✅
- Database: Connected ✅
- SSL Certificate: Valid ✅

ENDPOINTS:
- API: https://api.yourapp.com
- Web: https://yourapp.com
- Health Check: https://api.yourapp.com/health

MONITORING:
- Uptime: 99.9%
- Response Time: <100ms
- Error Rate: 0.01%
"""
        task.status = "completed"
        
        self.chat_history.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": "deploy-agent",
            "message": f"Completed deployment for task {task_id[:8]}..."
        })
    
    async def _send_direct_message(self, agent_id: str, message: str) -> str:
        """Simulate direct message to agent"""
        agent_type = self.agents[agent_id]["type"]
        
        responses = {
            "code-agent": f"Code Agent here! I can help with: {message}. What specific functionality do you need?",
            "test-agent": f"Test Agent ready! For '{message}' - I can create comprehensive test suites.",
            "security-agent": f"Security Agent active! Regarding '{message}' - I'll analyze potential vulnerabilities.",
            "deploy-agent": f"Deploy Agent standing by! For '{message}' - I can handle the deployment pipeline."
        }
        
        return responses.get(agent_id, f"Agent {agent_id} received your message: {message}")
    
    def _get_help(self) -> str:
        """Get help text"""
        return """
🤖 Multi-Agent PRP Assistant Help

SLASH COMMANDS:
  /help            - Show this help
  /agents          - List all active agents  
  /tasks           - Show current task queue
  /status <id>     - Check status of specific task (use first 8 chars of ID)
  /chat <agent> <msg> - Send direct message to specific agent

NATURAL LANGUAGE EXAMPLES:
  "write a function to calculate fibonacci numbers"
  "create a REST API for user management" 
  "test the authentication system"
  "run security scan on the login module"
  "deploy the application to production"

AVAILABLE AGENTS:
  code-agent    - Write, refactor, and fix code
  test-agent    - Create and run comprehensive tests
  security-agent - Security analysis and vulnerability scanning  
  deploy-agent  - Application deployment and infrastructure

TIP: Just describe what you want in natural language!
Example: "write a function to process user data"
"""

# Interactive demo
async def interactive_demo():
    """Run interactive multi-agent chat demo"""
    chat = SimpleMultiAgentChat()
    
    print("🤖 Multi-Agent PRP Assistant Demo")
    print("=" * 50)
    print("4 specialized agents are ready to help!")
    print("Type /help for commands or just describe what you need.")
    print("Type 'quit' to exit.\\n")
    
    example_commands = [
        "write a function to hash passwords securely",
        "/agents",
        "test the password hashing function", 
        "run security scan on authentication",
        "/tasks",
        "deploy the application to production"
    ]
    
    print("Example session:")
    for cmd in example_commands:
        print(f"\\n💬 You: {cmd}")
        response = await chat.handle_chat(cmd)
        print(f"🤖 Assistant: {response}")
        
        # Show task completion
        if not cmd.startswith("/"):
            await asyncio.sleep(0.5)  # Brief pause
            print("   [Task processing in background...]")
    
    print("\\n" + "=" * 50)
    print("\\n🎯 Try it yourself! Enter commands below:")
    
    # Interactive portion
    while True:
        try:
            user_input = input("\\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                continue
                
            response = await chat.handle_chat(user_input)
            print(f"🤖 Assistant: {response}")
            
            # Show recent activity
            if chat.chat_history:
                recent = chat.chat_history[-3:]
                if recent:
                    print("\\n📋 Recent Agent Activity:")
                    for activity in recent:
                        print(f"  {activity['timestamp']} | {activity['agent']}: {activity['message']}")
            
        except KeyboardInterrupt:
            break
    
    print("\\n👋 Thanks for trying the Multi-Agent PRP Assistant!")

if __name__ == "__main__":
    asyncio.run(interactive_demo())