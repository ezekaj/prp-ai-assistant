#!/usr/bin/env python3
"""
Test script for PRP Multi-Agent System
Demonstrates the enhanced coordination capabilities
"""

import asyncio
import sys
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from prp_ai_agent_coordinator import EnhancedAgentCoordinator, TaskPriority

async def main():
    """Test the multi-agent coordination system"""
    print("🧪 Testing PRP Multi-Agent System")
    print("=" * 70)
    
    # Initialize coordinator
    coordinator = EnhancedAgentCoordinator()
    await coordinator.initialize()
    print("✅ Coordinator initialized")
    
    # Register test agents
    print("\n📋 Registering agents...")
    
    agents = [
        {
            'name': 'Code Agent',
            'type': 'code_agent',
            'capabilities': [
                {'name': 'code_generation', 'proficiency': 0.9},
                {'name': 'code_analysis', 'proficiency': 0.85}
            ]
        },
        {
            'name': 'Test Agent',
            'type': 'test_agent',
            'capabilities': [
                {'name': 'testing', 'proficiency': 0.95},
                {'name': 'test_generation', 'proficiency': 0.9}
            ]
        },
        {
            'name': 'Security Agent',
            'type': 'security_agent',
            'capabilities': [
                {'name': 'security', 'proficiency': 0.95},
                {'name': 'vulnerability_scan', 'proficiency': 0.9}
            ]
        }
    ]
    
    agent_ids = {}
    for agent in agents:
        agent_id = await coordinator.register_agent(agent)
        agent_ids[agent['name']] = agent_id
        print(f"   ✅ {agent['name']} registered: {agent_id}")
    
    # Submit test tasks
    print("\n📋 Submitting test tasks...")
    
    # Task 1: Simple task
    task1_id = await coordinator.submit_task({
        'type': 'code_analysis',
        'priority': TaskPriority.MEDIUM.value,
        'description': 'Analyze project structure',
        'capabilities': ['code_analysis']
    })
    print(f"   ✅ Simple task submitted: {task1_id}")
    
    # Task 2: Complex coordinated task
    task2_id = await coordinator.submit_task({
        'type': 'full_feature_implementation',
        'priority': TaskPriority.HIGH.value,
        'feature': 'User Authentication System',
        'requirements': ['JWT tokens', 'OAuth support', 'Rate limiting']
    })
    print(f"   ✅ Complex task submitted: {task2_id}")
    
    # Monitor execution
    print("\n📊 Monitoring execution...")
    print("-" * 70)
    
    for i in range(10):
        status = await coordinator.get_coordination_status()
        
        print(f"\r⏱️  [{i+1}/10] "
              f"Agents: {status['agents']['active']}/{status['agents']['total']} active | "
              f"Tasks: {status['tasks']['in_progress']} running, "
              f"{status['tasks']['completed']} done, "
              f"{status['tasks']['failed']} failed", 
              end='', flush=True)
        
        await asyncio.sleep(1)
    
    # Final status
    print("\n\n📊 Final Status:")
    print("-" * 70)
    
    final_status = await coordinator.get_coordination_status()
    print(f"✅ Tasks Completed: {final_status['tasks']['completed']}")
    print(f"❌ Tasks Failed: {final_status['tasks']['failed']}")
    print(f"📈 Success Rate: {final_status['performance']['success_rate']:.1%}")
    print(f"⏱️  Avg Duration: {final_status['performance']['average_task_duration']:.1f}s")
    print(f"🚀 Throughput: {final_status['performance']['throughput']:.2f} tasks/min")
    
    # Agent performance
    print("\n🤖 Agent Performance:")
    for name, agent_id in agent_ids.items():
        agent = coordinator.agents[agent_id]
        print(f"   {name}: {agent.tasks_completed} completed, "
              f"Performance: {agent.performance_score:.2f}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())