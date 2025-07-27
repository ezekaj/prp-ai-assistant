#!/usr/bin/env python3
"""
Interactive PRP System for Claude Code
This allows you to use PRP commands directly
"""

import os
import json
from datetime import datetime
from prp_demo_claude import PRPMultiAgentSystem

class PRPInteractiveSystem:
    """Interactive PRP system that responds to commands"""
    
    def __init__(self):
        self.system = PRPMultiAgentSystem()
        self.commands = {
            '/prp-analyze': self.analyze_codebase,
            '/prp-create': self.create_prp,
            '/prp-status': self.show_status,
            '/prp-help': self.show_help,
            '/multi-agent': self.multi_agent_task
        }
        print("[SYSTEM] PRP Interactive System Initialized")
        print("[SYSTEM] Type '/prp-help' for available commands")
    
    def analyze_codebase(self, args=''):
        """Analyze the current codebase"""
        print("\n[ANALYSIS] Analyzing codebase...")
        
        # Count Python files
        py_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
        
        print(f"[FOUND] {len(py_files)} Python files")
        print("\n[12-FACTOR COMPLIANCE CHECK]")
        
        # Simple 12-factor checks
        checks = {
            'Environment Config': os.path.exists('.env.example'),
            'Dependencies Listed': os.path.exists('requirements.txt'),
            'Dockerfile Present': os.path.exists('Dockerfile'),
            'Health Check': any('health' in f for f in py_files),
            'Logging Configured': os.path.exists('logging_config.py')
        }
        
        score = sum(1 for v in checks.values() if v) * 20
        
        for check, passed in checks.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status} {check}")
        
        print(f"\n[SCORE] 12-Factor Compliance: {score}%")
        
        return {
            'files_analyzed': len(py_files),
            'compliance_score': score,
            'checks': checks
        }
    
    def create_prp(self, args=''):
        """Create a new PRP"""
        if not args:
            print("[ERROR] Usage: /prp-create <feature_name> | <requirements>")
            return
        
        parts = args.split('|')
        feature_name = parts[0].strip()
        requirements = parts[1].strip() if len(parts) > 1 else "Standard implementation"
        
        print(f"\n[CREATE] Generating PRP for: {feature_name}")
        prp = self.system.create_prp(feature_name, requirements)
        
        print(f"\n[SUCCESS] PRP created: {prp['id']}")
        return prp
    
    def show_status(self, args=''):
        """Show system status"""
        print("\n[STATUS] PRP System Status")
        print("=" * 50)
        print(f"PRPs Created: {len(self.system.results)}")
        print(f"Active Agents: {len(self.system.agents)}")
        
        print("\n[AGENTS]")
        for name, agent in self.system.agents.items():
            print(f"  - {agent.name}: {agent.role}")
            print(f"    Tasks completed: {len(agent.tasks_completed)}")
        
        if self.system.results:
            print("\n[RECENT PRPs]")
            for prp in self.system.results[-3:]:
                print(f"  - {prp['id']}: {prp['feature']}")
    
    def show_help(self, args=''):
        """Show available commands"""
        print("\n[HELP] Available PRP Commands")
        print("=" * 50)
        print("/prp-analyze          - Analyze current codebase")
        print("/prp-create <name>|<req> - Create new PRP")
        print("/prp-status           - Show system status")
        print("/multi-agent <task>   - Run multi-agent task")
        print("/prp-help            - Show this help")
        print("\n[EXAMPLES]")
        print('/prp-create User Login | Secure authentication with 2FA')
        print('/multi-agent implement REST API with testing')
    
    def multi_agent_task(self, args=''):
        """Execute a multi-agent task"""
        if not args:
            print("[ERROR] Usage: /multi-agent <task description>")
            return
        
        print(f"\n[MULTI-AGENT] Processing: {args}")
        
        # Determine which agents to involve based on keywords
        agents_needed = []
        
        if any(word in args.lower() for word in ['code', 'implement', 'create', 'build']):
            agents_needed.append('CodeAgent')
        if any(word in args.lower() for word in ['test', 'testing', 'verify']):
            agents_needed.append('TestAgent')
        if any(word in args.lower() for word in ['secure', 'security', 'auth']):
            agents_needed.append('SecurityAgent')
        
        if not agents_needed:
            agents_needed = ['CodeAgent', 'TestAgent', 'SecurityAgent']
        
        print(f"[ASSIGNED] Agents: {', '.join(agents_needed)}")
        
        # Create a PRP for this task
        feature_name = args.split()[0:3]  # First 3 words as feature name
        feature_name = ' '.join(feature_name).title()
        
        prp = self.system.create_prp(feature_name, args)
        
        print(f"\n[COMPLETE] Task processed by {len(agents_needed)} agents")
        return prp
    
    def process_command(self, command):
        """Process a single command"""
        parts = command.strip().split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''
        
        if cmd in self.commands:
            return self.commands[cmd](args)
        else:
            print(f"[ERROR] Unknown command: {cmd}")
            print("[TIP] Use /prp-help for available commands")
            return None

def main():
    """Main interactive loop"""
    print("=" * 60)
    print("PRP INTERACTIVE SYSTEM FOR CLAUDE CODE")
    print("=" * 60)
    
    system = PRPInteractiveSystem()
    
    # Example commands to demonstrate
    demo_commands = [
        '/prp-analyze',
        '/prp-create API Gateway | Microservices API gateway with rate limiting',
        '/multi-agent implement user profile management with database',
        '/prp-status'
    ]
    
    print("\n[DEMO] Running example commands...")
    
    for cmd in demo_commands:
        print(f"\n[COMMAND] {cmd}")
        result = system.process_command(cmd)
        
        # Add a separator between commands
        print("\n" + "-" * 50)
    
    print("\n[INFO] PRP Interactive System Ready")
    print("[INFO] You can now use these commands in Claude Code!")

if __name__ == "__main__":
    main()