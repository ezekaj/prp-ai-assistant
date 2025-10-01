"""
Nano Agents System - GPT-5 Style Agentic Coding
Intelligent model routing and specialized agent coordination
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
from datetime import datetime

class ModelTier(Enum):
    """Model tiers based on capability and cost"""
    NANO = "nano"           # Llama 3.2 1B, Gemma 2B - Simple tasks
    MICRO = "micro"         # Llama 3.2 3B, Mistral 7B - Basic coding
    SMALL = "small"         # Codestral, DeepSeek - Standard coding
    MEDIUM = "medium"       # GPT-4o-mini, Claude Haiku - Complex tasks
    LARGE = "large"         # GPT-4, Claude Sonnet - Advanced reasoning
    FRONTIER = "frontier"   # Claude Opus, GPT-4o - Critical thinking

@dataclass
class NanoAgent:
    """Specialized nano agent for specific domains"""
    name: str
    domain: str
    capabilities: List[str]
    preferred_models: Dict[str, ModelTier]
    complexity_threshold: float
    success_rate: float = 1.0
    
class TaskComplexityAnalyzer:
    """Analyzes task complexity to route to appropriate model"""
    
    @staticmethod
    def analyze(task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task complexity and requirements"""
        
        complexity_score = 0.0
        
        # Simple heuristics for complexity
        complexity_factors = {
            'lines_of_code': len(context.get('code', '').split('\n')),
            'dependencies': len(context.get('imports', [])),
            'has_security': any(word in task.lower() for word in ['security', 'auth', 'encrypt', 'password']),
            'has_architecture': any(word in task.lower() for word in ['architect', 'design', 'system', 'scale']),
            'has_debugging': any(word in task.lower() for word in ['debug', 'fix', 'error', 'bug']),
            'has_optimization': any(word in task.lower() for word in ['optimize', 'performance', 'speed', 'efficient']),
            'is_creative': any(word in task.lower() for word in ['create', 'build', 'implement', 'design']),
            'requires_context': len(context.get('files_involved', [])) > 3,
        }
        
        # Calculate complexity score (0-1)
        if complexity_factors['lines_of_code'] > 100:
            complexity_score += 0.3
        if complexity_factors['has_security']:
            complexity_score += 0.25
        if complexity_factors['has_architecture']:
            complexity_score += 0.2
        if complexity_factors['requires_context']:
            complexity_score += 0.15
        if complexity_factors['is_creative']:
            complexity_score += 0.1
            
        complexity_score = min(1.0, complexity_score)
        
        # Determine required capabilities
        required_capabilities = []
        if complexity_factors['has_security']:
            required_capabilities.append('security_analysis')
        if complexity_factors['has_debugging']:
            required_capabilities.append('debugging')
        if complexity_factors['has_optimization']:
            required_capabilities.append('performance_optimization')
            
        return {
            'complexity_score': complexity_score,
            'factors': complexity_factors,
            'required_capabilities': required_capabilities,
            'estimated_tokens': len(task.split()) * 10,  # Rough estimate
            'recommended_tier': TaskComplexityAnalyzer._get_tier(complexity_score)
        }
    
    @staticmethod
    def _get_tier(complexity_score: float) -> ModelTier:
        """Map complexity score to model tier"""
        if complexity_score < 0.2:
            return ModelTier.NANO
        elif complexity_score < 0.35:
            return ModelTier.MICRO
        elif complexity_score < 0.5:
            return ModelTier.SMALL
        elif complexity_score < 0.7:
            return ModelTier.MEDIUM
        elif complexity_score < 0.85:
            return ModelTier.LARGE
        else:
            return ModelTier.FRONTIER

class NanoAgentOrchestrator:
    """Orchestrates nano agents for efficient task execution"""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        self.model_costs = self._initialize_costs()
        self.execution_history = []
        
    def _initialize_agents(self) -> Dict[str, NanoAgent]:
        """Initialize specialized nano agents"""
        return {
            'code_writer': NanoAgent(
                name='CodeWriter',
                domain='code_generation',
                capabilities=['write_functions', 'create_classes', 'implement_algorithms'],
                preferred_models={
                    'simple': ModelTier.MICRO,
                    'standard': ModelTier.SMALL,
                    'complex': ModelTier.MEDIUM
                },
                complexity_threshold=0.5
            ),
            
            'security_auditor': NanoAgent(
                name='SecurityAuditor',
                domain='security',
                capabilities=['security_analysis', 'vulnerability_scanning', 'auth_implementation'],
                preferred_models={
                    'scan': ModelTier.SMALL,
                    'analyze': ModelTier.LARGE,
                    'fix': ModelTier.MEDIUM
                },
                complexity_threshold=0.7
            ),
            
            'test_engineer': NanoAgent(
                name='TestEngineer',
                domain='testing',
                capabilities=['write_tests', 'test_coverage', 'debugging'],
                preferred_models={
                    'unit_tests': ModelTier.MICRO,
                    'integration_tests': ModelTier.SMALL,
                    'e2e_tests': ModelTier.MEDIUM
                },
                complexity_threshold=0.4
            ),
            
            'architect': NanoAgent(
                name='SystemArchitect',
                domain='architecture',
                capabilities=['system_design', 'api_design', 'database_design'],
                preferred_models={
                    'planning': ModelTier.LARGE,
                    'documentation': ModelTier.MEDIUM,
                    'review': ModelTier.FRONTIER
                },
                complexity_threshold=0.8
            ),
            
            'optimizer': NanoAgent(
                name='PerformanceOptimizer',
                domain='optimization',
                capabilities=['performance_optimization', 'memory_optimization', 'query_optimization'],
                preferred_models={
                    'profile': ModelTier.SMALL,
                    'optimize': ModelTier.MEDIUM,
                    'benchmark': ModelTier.MICRO
                },
                complexity_threshold=0.6
            ),
            
            'documenter': NanoAgent(
                name='Documenter',
                domain='documentation',
                capabilities=['write_docs', 'api_docs', 'code_comments'],
                preferred_models={
                    'comments': ModelTier.NANO,
                    'readme': ModelTier.MICRO,
                    'api_docs': ModelTier.SMALL
                },
                complexity_threshold=0.3
            ),
            
            'reviewer': NanoAgent(
                name='CodeReviewer',
                domain='review',
                capabilities=['code_review', 'best_practices', 'refactoring'],
                preferred_models={
                    'syntax': ModelTier.NANO,
                    'logic': ModelTier.SMALL,
                    'architecture': ModelTier.LARGE
                },
                complexity_threshold=0.5
            ),
            
            'debugger': NanoAgent(
                name='Debugger',
                domain='debugging',
                capabilities=['debugging', 'error_analysis', 'stack_trace_analysis'],
                preferred_models={
                    'syntax_errors': ModelTier.NANO,
                    'logic_errors': ModelTier.MEDIUM,
                    'complex_bugs': ModelTier.LARGE
                },
                complexity_threshold=0.6
            )
        }
    
    def _initialize_costs(self) -> Dict[ModelTier, float]:
        """Initialize relative costs per 1K tokens (normalized)"""
        return {
            ModelTier.NANO: 0.01,      # Local models, almost free
            ModelTier.MICRO: 0.02,     # Small local models
            ModelTier.SMALL: 0.05,     # Codestral, DeepSeek
            ModelTier.MEDIUM: 0.15,    # GPT-4o-mini, Claude Haiku
            ModelTier.LARGE: 1.0,      # GPT-4, Claude Sonnet
            ModelTier.FRONTIER: 3.0,   # Claude Opus, GPT-4o
        }
    
    async def route_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route task to appropriate nano agent and model"""
        
        # Analyze task complexity
        analysis = TaskComplexityAnalyzer.analyze(task, context)
        
        # Find best agent for the task
        best_agent = self._select_agent(task, analysis['required_capabilities'])
        
        # Determine optimal model based on complexity and agent preference
        model_tier = self._select_model_tier(
            best_agent, 
            analysis['complexity_score'],
            context.get('budget_constraint', False)
        )
        
        # Calculate estimated cost
        estimated_cost = self._calculate_cost(
            analysis['estimated_tokens'],
            model_tier
        )
        
        # Create execution plan
        execution_plan = {
            'task': task,
            'agent': best_agent.name,
            'model_tier': model_tier.value,
            'complexity_score': analysis['complexity_score'],
            'estimated_cost': estimated_cost,
            'estimated_tokens': analysis['estimated_tokens'],
            'capabilities_required': analysis['required_capabilities'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Log execution
        self.execution_history.append(execution_plan)
        
        return execution_plan
    
    def _select_agent(self, task: str, required_capabilities: List[str]) -> NanoAgent:
        """Select the best agent for the task"""
        
        task_lower = task.lower()
        
        # Domain-specific keywords for agent selection
        domain_keywords = {
            'code_writer': ['write', 'create', 'implement', 'build', 'function', 'class'],
            'security_auditor': ['security', 'auth', 'encrypt', 'password', 'vulnerable'],
            'test_engineer': ['test', 'testing', 'coverage', 'assert', 'mock'],
            'architect': ['architect', 'design', 'system', 'scale', 'structure'],
            'optimizer': ['optimize', 'performance', 'speed', 'efficient', 'memory'],
            'documenter': ['document', 'docs', 'readme', 'comment', 'explain'],
            'reviewer': ['review', 'refactor', 'improve', 'clean', 'best practice'],
            'debugger': ['debug', 'fix', 'error', 'bug', 'issue', 'problem']
        }
        
        # Score each agent
        agent_scores = {}
        for agent_name, agent in self.agents.items():
            score = 0
            
            # Check keyword matches
            for keyword in domain_keywords.get(agent_name, []):
                if keyword in task_lower:
                    score += 1
            
            # Check capability matches
            for capability in required_capabilities:
                if capability in agent.capabilities:
                    score += 2
            
            agent_scores[agent_name] = score
        
        # Select agent with highest score
        best_agent_name = max(agent_scores, key=agent_scores.get)
        
        # Default to code_writer if no clear match
        if agent_scores[best_agent_name] == 0:
            best_agent_name = 'code_writer'
        
        return self.agents[best_agent_name]
    
    def _select_model_tier(self, agent: NanoAgent, complexity: float, budget_mode: bool) -> ModelTier:
        """Select optimal model tier based on agent preference and complexity"""
        
        # In budget mode, cap at MEDIUM tier
        if budget_mode and complexity < 0.9:
            if complexity < 0.3:
                return ModelTier.NANO
            elif complexity < 0.5:
                return ModelTier.MICRO
            elif complexity < 0.7:
                return ModelTier.SMALL
            else:
                return ModelTier.MEDIUM
        
        # Determine tier based on complexity
        if complexity < 0.3:
            tier_key = 'simple'
        elif complexity < 0.7:
            tier_key = 'standard'
        else:
            tier_key = 'complex'
        
        # Get agent's preferred model for this complexity
        preferred_models = agent.preferred_models
        
        # Find matching key or use default
        for key in preferred_models:
            if tier_key in key or key in tier_key:
                return preferred_models[key]
        
        # Fallback to complexity-based selection
        return TaskComplexityAnalyzer._get_tier(complexity)
    
    def _calculate_cost(self, tokens: int, tier: ModelTier) -> float:
        """Calculate estimated cost for the task"""
        cost_per_1k = self.model_costs[tier]
        return (tokens / 1000) * cost_per_1k
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions"""
        if not self.execution_history:
            return {'total_tasks': 0, 'total_cost': 0}
        
        total_cost = sum(e['estimated_cost'] for e in self.execution_history)
        tier_distribution = {}
        agent_distribution = {}
        
        for execution in self.execution_history:
            tier = execution['model_tier']
            agent = execution['agent']
            
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
            agent_distribution[agent] = agent_distribution.get(agent, 0) + 1
        
        return {
            'total_tasks': len(self.execution_history),
            'total_cost': total_cost,
            'average_complexity': sum(e['complexity_score'] for e in self.execution_history) / len(self.execution_history),
            'tier_distribution': tier_distribution,
            'agent_distribution': agent_distribution,
            'cost_savings': self._calculate_savings()
        }
    
    def _calculate_savings(self) -> float:
        """Calculate cost savings vs using frontier model for everything"""
        if not self.execution_history:
            return 0
        
        actual_cost = sum(e['estimated_cost'] for e in self.execution_history)
        frontier_cost = sum(
            (e['estimated_tokens'] / 1000) * self.model_costs[ModelTier.FRONTIER] 
            for e in self.execution_history
        )
        
        return (frontier_cost - actual_cost) / frontier_cost * 100 if frontier_cost > 0 else 0


# Example usage and integration
async def main():
    """Example of using the nano agents system"""
    
    orchestrator = NanoAgentOrchestrator()
    
    # Example tasks with varying complexity
    tasks = [
        ("Write a simple hello world function", {'code': 'def hello(): pass'}),
        ("Implement JWT authentication with role-based access control", {'imports': ['jwt', 'bcrypt'], 'files_involved': ['auth.py', 'models.py', 'config.py']}),
        ("Add a comment to explain this function", {'code': 'def calc(): return 42'}),
        ("Design a microservices architecture for e-commerce platform", {'files_involved': ['api.py', 'db.py', 'cache.py', 'queue.py', 'gateway.py']}),
        ("Fix the database connection pool memory leak", {'code': 'connection = db.connect()\n' * 50}),
        ("Write unit tests for user registration", {'code': 'class User: pass'}),
        ("Optimize this SQL query for better performance", {'code': 'SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)'}),
    ]
    
    print("=" * 60)
    print("NANO AGENTS SYSTEM - Task Routing Demo")
    print("=" * 60)
    
    for task, context in tasks:
        result = await orchestrator.route_task(task, context)
        
        print(f"\nTask: {task[:50]}...")
        print(f"  Agent: {result['agent']}")
        print(f"  Model Tier: {result['model_tier']}")
        print(f"  Complexity: {result['complexity_score']:.2f}")
        print(f"  Est. Cost: ${result['estimated_cost']:.4f}")
    
    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    
    summary = orchestrator.get_execution_summary()
    print(f"Total Tasks: {summary['total_tasks']}")
    print(f"Total Cost: ${summary['total_cost']:.4f}")
    print(f"Average Complexity: {summary['average_complexity']:.2f}")
    print(f"Cost Savings: {summary['cost_savings']:.1f}%")
    print(f"\nModel Tier Distribution:")
    for tier, count in summary['tier_distribution'].items():
        print(f"  {tier}: {count} tasks")
    print(f"\nAgent Distribution:")
    for agent, count in summary['agent_distribution'].items():
        print(f"  {agent}: {count} tasks")

if __name__ == "__main__":
    asyncio.run(main())