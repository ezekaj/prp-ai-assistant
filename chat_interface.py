#!/usr/bin/env python3
"""
Chat Interface for Multi-Agent PRP System
Interactive chat with multi-agent coordination
"""

import asyncio
import sys
from datetime import datetime
from typing import List, Dict, Any

from multi_agent_coordinator import MultiAgentCoordinator, AgentType
from sample_agent import CodeGenerationAgent, BaseAgent
from logging_config import get_logger

logger = get_logger(__name__)

class ChatInterface:
    """Interactive chat interface for multi-agent system"""
    
    def __init__(self):
        self.coordinator = MultiAgentCoordinator()
        self.agents: List[BaseAgent] = []
        self.is_running = False
    
    async def start(self):
        """Start the chat interface and agents"""
        print("🤖 Multi-Agent PRP Assistant")
        print("=" * 50)
        print("Initializing agents...")
        
        # Start some sample agents
        agents_to_create = [
            ("code-agent-1", CodeGenerationAgent),
            # Add more agent types here as you implement them
        ]
        
        for agent_id, agent_class in agents_to_create:
            if agent_class == CodeGenerationAgent:
                agent = agent_class(agent_id)
            else:
                # For other agent types, you'd pass appropriate parameters
                agent = agent_class(agent_id, AgentType.TESTING, ["write_tests", "run_tests"])
            
            await agent.start()
            self.agents.append(agent)
            print(f"✓ Started {agent_id}")
        
        # Register agents with coordinator
        for agent in self.agents:
            await self.coordinator.register_agent(
                agent.agent_id, 
                agent.agent_type, 
                agent.capabilities
            )
        
        print("\\n✅ All agents ready!")
        print("\\n" + "=" * 50)
        print("CHAT COMMANDS:")
        print("  /help - Show this help")
        print("  /agents - List active agents")
        print("  /tasks - List current tasks")
        print("  /status <task_id> - Check task status")
        print("  /chat <agent_id> <message> - Direct message to agent")
        print("  /broadcast <message> - Message all agents")
        print("  /quit - Exit")
        print("\\nNATURAL LANGUAGE:")
        print("  'write a function to...' - Code generation")
        print("  'test the...' - Testing tasks")
        print("  'security scan...' - Security analysis")
        print("  'deploy...' - Deployment tasks")
        print("=" * 50)
        
        self.is_running = True
        await self._chat_loop()
    
    async def _chat_loop(self):
        """Main chat interaction loop"""
        while self.is_running:
            try:
                # Get user input
                user_input = await self._get_user_input()
                
                if not user_input.strip():
                    continue
                
                if user_input.lower() in ['/quit', 'quit', 'exit']:
                    break
                
                if user_input == '/help':
                    self._show_help()
                    continue
                
                # Process command with coordinator
                response = await self.coordinator.handle_chat_command(user_input)
                print(f"\\n🤖 Assistant: {response}\\n")
                
                # Show recent chat activity
                if user_input.startswith('/chat') or user_input.startswith('/broadcast'):
                    await asyncio.sleep(1)  # Give agents time to respond
                    await self._show_recent_activity()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\\n❌ Error: {e}\\n")
                logger.error("chat_loop_error", error=str(e))
        
        await self._shutdown()
    
    async def _get_user_input(self) -> str:
        """Get user input asynchronously"""
        # For demo purposes, using input(). In a real app, you'd use proper async input
        return input("💬 You: ")
    
    def _show_help(self):
        """Show help information"""
        print("""
🤖 Multi-Agent PRP Assistant Help

SLASH COMMANDS:
  /agents          - List all active agents
  /tasks           - Show current task queue
  /status <id>     - Check status of specific task
  /chat <agent> <msg> - Send direct message to agent
  /broadcast <msg> - Send message to all agents
  /quit            - Exit the system

NATURAL LANGUAGE EXAMPLES:
  "write a function to calculate fibonacci numbers"
  "create a REST API for user management"
  "test the authentication system"
  "run security scan on the login module"
  "deploy the application to production"
  "analyze performance of the database queries"
  "write documentation for the API endpoints"

AGENT TYPES:
  code_generation  - Write, refactor, and fix code
  testing         - Create and run tests
  security        - Security analysis and scanning
  deployment      - Deploy and configure applications
  analysis        - Performance and code analysis
  documentation   - Write docs and guides

TIP: Just describe what you want in natural language!
        """)
    
    async def _show_recent_activity(self):
        """Show recent chat activity"""
        chat_history = self.coordinator.get_chat_history(limit=5)
        
        if chat_history:
            print("\\n📋 Recent Activity:")
            for msg in chat_history[-3:]:  # Show last 3 messages
                timestamp = msg['timestamp'][:19]  # Remove microseconds
                from_agent = msg['from_agent']
                content = msg['content'][:100]  # Truncate long messages
                
                if msg['message_type'] == 'chat':
                    print(f"  {timestamp} | {from_agent}: {content}")
            print()
    
    async def _shutdown(self):
        """Shutdown all agents and cleanup"""
        print("\\n🔄 Shutting down agents...")
        
        for agent in self.agents:
            await agent.stop()
            print(f"✓ Stopped {agent.agent_id}")
        
        print("👋 Goodbye!")
        self.is_running = False


# Enhanced demo with realistic scenarios
async def demo_scenarios():
    """Demo realistic multi-agent scenarios"""
    coordinator = MultiAgentCoordinator()
    
    # Start agents
    code_agent = CodeGenerationAgent("demo-code-agent")
    await code_agent.start()
    await coordinator.register_agent(code_agent.agent_id, code_agent.agent_type, code_agent.capabilities)
    
    print("🎭 Multi-Agent Scenario Demo")
    print("=" * 40)
    
    scenarios = [
        {
            "description": "User wants to build a user authentication system",
            "commands": [
                "write a function to hash passwords securely",
                "create a login validation function",
                "implement JWT token generation"
            ]
        },
        {
            "description": "User needs API development",
            "commands": [
                "create a REST API endpoint for user registration",
                "implement error handling for API responses",
                "add input validation for API requests"
            ]
        },
        {
            "description": "User wants testing coverage",
            "commands": [
                "write unit tests for the password hashing function",
                "create integration tests for the login API",
                "test the JWT token validation"
            ]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\\n📝 Scenario {i}: {scenario['description']}")
        print("-" * 40)
        
        for command in scenario['commands']:
            print(f"\\nUser: {command}")
            response = await coordinator.handle_chat_command(command)
            print(f"Assistant: {response}")
            
            # Simulate some processing time
            await asyncio.sleep(1)
        
        print("\\n" + "=" * 40)
    
    # Cleanup
    await code_agent.stop()
    print("\\nDemo completed!")


async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        await demo_scenarios()
    else:
        chat = ChatInterface()
        await chat.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n\\n👋 Interrupted by user")
    except Exception as e:
        print(f"\\n❌ Fatal error: {e}")
        logger.error("fatal_error", error=str(e))