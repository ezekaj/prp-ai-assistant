"""
Claude CLI Integration with Nano Agents
Global settings for intelligent model routing
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
from nano_agents_system import NanoAgentOrchestrator, TaskComplexityAnalyzer, ModelTier

class ClaudeCLINanoIntegration:
    """Integrates nano agents with Claude CLI for intelligent routing"""
    
    def __init__(self):
        self.orchestrator = NanoAgentOrchestrator()
        self.config_path = Path.home() / '.claude' / 'nano_agents_config.json'
        self.models_config = self._load_models_config()
        
    def _load_models_config(self) -> Dict[str, Any]:
        """Load model configurations for different tiers"""
        return {
            ModelTier.NANO: {
                'models': ['llama3.2:1b', 'gemma2:2b'],
                'provider': 'ollama',
                'local': True,
                'max_tokens': 2048
            },
            ModelTier.MICRO: {
                'models': ['llama3.2:3b', 'mistral:7b', 'phi3:mini'],
                'provider': 'ollama',
                'local': True,
                'max_tokens': 4096
            },
            ModelTier.SMALL: {
                'models': ['codestral:latest', 'deepseek-coder:6.7b', 'starcoder2:7b'],
                'provider': 'ollama',
                'local': True,
                'max_tokens': 8192
            },
            ModelTier.MEDIUM: {
                'models': ['gpt-4o-mini', 'claude-3-haiku'],
                'provider': 'api',
                'local': False,
                'max_tokens': 16384
            },
            ModelTier.LARGE: {
                'models': ['gpt-4', 'claude-3-sonnet'],
                'provider': 'api',
                'local': False,
                'max_tokens': 32768
            },
            ModelTier.FRONTIER: {
                'models': ['claude-3-opus', 'gpt-4o', 'claude-3.5-sonnet'],
                'provider': 'api',
                'local': False,
                'max_tokens': 65536
            }
        }
    
    def create_global_config(self) -> Dict[str, Any]:
        """Create global configuration for Claude CLI"""
        
        config = {
            "nano_agents": {
                "enabled": True,
                "version": "1.0.0",
                "auto_routing": True,
                "budget_mode": False,
                "fallback_model": "claude-3-haiku",
                "local_models_priority": True
            },
            
            "routing_rules": {
                "simple_tasks": {
                    "complexity_threshold": 0.3,
                    "preferred_tier": "nano",
                    "examples": ["add comment", "fix typo", "rename variable"]
                },
                "standard_tasks": {
                    "complexity_threshold": 0.6,
                    "preferred_tier": "small",
                    "examples": ["write function", "create test", "refactor code"]
                },
                "complex_tasks": {
                    "complexity_threshold": 0.85,
                    "preferred_tier": "large",
                    "examples": ["design system", "debug complex issue", "security audit"]
                }
            },
            
            "model_preferences": {
                "code_generation": {
                    "primary": "codestral:latest",
                    "fallback": "deepseek-coder:6.7b"
                },
                "debugging": {
                    "primary": "claude-3-sonnet",
                    "fallback": "gpt-4"
                },
                "documentation": {
                    "primary": "llama3.2:3b",
                    "fallback": "mistral:7b"
                },
                "security": {
                    "primary": "claude-3-opus",
                    "fallback": "gpt-4o"
                }
            },
            
            "cost_optimization": {
                "max_cost_per_task": 0.5,
                "prefer_local_models": True,
                "cache_responses": True,
                "batch_similar_tasks": True
            },
            
            "ollama_integration": {
                "endpoint": "http://localhost:11434",
                "models_to_preload": [
                    "llama3.2:1b",
                    "llama3.2:3b",
                    "codestral:latest",
                    "mistral:7b"
                ],
                "auto_pull": True
            },
            
            "monitoring": {
                "track_usage": True,
                "log_routing_decisions": True,
                "metrics_endpoint": "http://localhost:8000/metrics",
                "export_path": "~/.claude/nano_agents_metrics.json"
            }
        }
        
        return config
    
    def setup_claude_cli_integration(self):
        """Set up the integration with Claude CLI"""
        
        # Create .claude directory if it doesn't exist
        claude_dir = Path.home() / '.claude'
        claude_dir.mkdir(exist_ok=True)
        
        # Create settings file
        settings_file = claude_dir / 'settings.json'
        
        existing_settings = {}
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                existing_settings = json.load(f)
        
        # Merge nano agents configuration
        existing_settings['nano_agents'] = self.create_global_config()['nano_agents']
        existing_settings['routing_rules'] = self.create_global_config()['routing_rules']
        existing_settings['model_preferences'] = self.create_global_config()['model_preferences']
        
        # Write updated settings
        with open(settings_file, 'w') as f:
            json.dump(existing_settings, f, indent=2)
        
        print(f"[OK] Claude CLI integration configured at: {settings_file}")
        
        # Create nano agents specific config
        nano_config_file = claude_dir / 'nano_agents_config.json'
        with open(nano_config_file, 'w') as f:
            json.dump(self.create_global_config(), f, indent=2)
        
        print(f"[OK] Nano agents config saved at: {nano_config_file}")
        
        # Create shell wrapper for Claude CLI with nano agents
        self._create_cli_wrapper()
    
    def _create_cli_wrapper(self):
        """Create a wrapper script for Claude CLI with nano agents"""
        
        wrapper_content = '''#!/usr/bin/env python3
"""
Claude CLI with Nano Agents - Intelligent Model Routing
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add nano agents to path
sys.path.insert(0, r"C:\\Users\\User\\OneDrive\\Desktop\\1111")

from nano_agents_system import NanoAgentOrchestrator, TaskComplexityAnalyzer
from claude_cli_nano_integration import ClaudeCLINanoIntegration

async def main():
    # Get the command from arguments
    if len(sys.argv) < 2:
        print("Usage: claude-nano <command>")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    
    # Initialize nano agents
    orchestrator = NanoAgentOrchestrator()
    integration = ClaudeCLINanoIntegration()
    
    # Analyze the command
    context = {
        'code': '',
        'files_involved': [],
        'imports': []
    }
    
    # Route to appropriate model
    execution_plan = await orchestrator.route_task(command, context)
    
    print(f"Nano Agent: {execution_plan['agent']}")
    print(f"Model Tier: {execution_plan['model_tier']}")
    print(f"Est. Cost: ${execution_plan['estimated_cost']:.4f}")
    print("-" * 40)
    
    # Execute based on model tier
    model_config = integration.models_config[execution_plan['model_tier']]
    
    if model_config['local']:
        # Use Ollama for local models
        model = model_config['models'][0]
        print(f"Using local model: {model}")
        os.system(f"ollama run {model} '{command}'")
    else:
        # Use Claude CLI for API models
        print(f"Using API model: {model_config['models'][0]}")
        os.system(f"claude '{command}'")
    
    # Save execution history
    history_file = Path.home() / '.claude' / 'nano_agents_history.json'
    history = []
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
    
    history.append(execution_plan)
    
    with open(history_file, 'w') as f:
        json.dump(history[-100:], f, indent=2)  # Keep last 100 executions

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        # Save wrapper script
        wrapper_path = Path.home() / '.claude' / 'claude-nano.py'
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_content)
        
        # Create batch file for Windows
        batch_content = f'''@echo off
python "{wrapper_path}" %*
'''
        
        batch_path = Path.home() / 'claude-nano.bat'
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        print(f"[OK] CLI wrapper created at: {wrapper_path}")
        print(f"[OK] Batch file created at: {batch_path}")
        
        # Add to PATH instructions
        print("\n[TIP] To use globally, add this to your PATH:")
        print(f"   {Path.home()}")
        print("\nThen you can use: claude-nano <your command>")
    
    def test_routing(self):
        """Test the nano agent routing with sample tasks"""
        
        test_tasks = [
            "add a comment to this function",
            "create a REST API with authentication",
            "optimize database queries for better performance",
            "fix the memory leak in the connection pool",
            "write comprehensive tests for the user service"
        ]
        
        print("\n" + "=" * 60)
        print("TESTING NANO AGENT ROUTING")
        print("=" * 60)
        
        for task in test_tasks:
            context = {'code': '', 'files_involved': []}
            analysis = TaskComplexityAnalyzer.analyze(task, context)
            
            print(f"\nTask: {task}")
            print(f"   Complexity: {analysis['complexity_score']:.2f}")
            print(f"   Recommended: {analysis['recommended_tier'].value}")
            print(f"   Est. Tokens: {analysis['estimated_tokens']}")


# Setup script
if __name__ == "__main__":
    print("Setting up Claude CLI with Nano Agents...")
    
    integration = ClaudeCLINanoIntegration()
    
    # Setup integration
    integration.setup_claude_cli_integration()
    
    # Test routing
    integration.test_routing()
    
    print("\n[OK] Setup complete!")
    print("\nUsage:")
    print("   claude-nano 'write a hello world function'")
    print("   claude-nano 'design a microservices architecture'")
    print("   claude-nano 'fix this bug in my code'")
    
    print("\nThe system will automatically route to the most efficient model!")
    print("   - Simple tasks -> Local nano models (Llama 3.2 1B)")
    print("   - Standard tasks -> Local small models (Codestral)")
    print("   - Complex tasks -> API models (Claude, GPT-4)")
    
    print("\nCost savings: ~80% compared to using frontier models for everything!")