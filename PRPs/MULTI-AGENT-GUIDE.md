# 🤖 PRP Multi-Agent System - User Guide

## Overview

The enhanced PRP Multi-Agent System provides intelligent, coordinated AI agents that work together to handle complex development tasks. Each agent specializes in specific areas and they collaborate seamlessly to deliver comprehensive solutions.

## Quick Start

### Basic Commands

```bash
# Show help
python PRPs/scripts/prp-master.py help

# Quick multi-agent assessment
python PRPs/scripts/prp-master.py multi-agent quick

# Deep comprehensive analysis
python PRPs/scripts/prp-master.py multi-agent deep

# Auto-fix with agent validation
python PRPs/scripts/prp-master.py multi-agent fix

# Security hardening
python PRPs/scripts/prp-master.py multi-agent security

# Performance optimization
python PRPs/scripts/prp-master.py multi-agent optimize

# Deployment preparation
python PRPs/scripts/prp-master.py multi-agent deploy

# Custom task (natural language)
python PRPs/scripts/prp-master.py multi-agent "create user authentication system with JWT"
```

## Available Agents

### 🔧 Code Agent
- **Capabilities**: Code generation, refactoring, bug fixes
- **Specializations**: API development, database integration, algorithm implementation
- **Proficiency**: 90% code generation, 85% code analysis

### 🧪 Test Agent
- **Capabilities**: Unit tests, integration tests, coverage analysis
- **Specializations**: Test generation, performance testing, test automation
- **Proficiency**: 95% testing, 90% test generation

### 🔒 Security Agent
- **Capabilities**: Vulnerability scanning, security audits, threat modeling
- **Specializations**: OWASP analysis, authentication, encryption
- **Proficiency**: 95% security scanning, 90% vulnerability detection

### 🚀 Deploy Agent
- **Capabilities**: Deployment automation, infrastructure setup, monitoring
- **Specializations**: Docker, Kubernetes, cloud platforms
- **Proficiency**: 90% deployment, 85% infrastructure

### 📊 Analysis Agent
- **Capabilities**: Performance analysis, code review, architecture assessment
- **Specializations**: Database optimization, memory analysis, scalability
- **Proficiency**: 90% code analysis, 85% performance analysis

### 📚 Docs Agent
- **Capabilities**: Documentation generation, API docs, user guides
- **Specializations**: Technical documentation, architecture diagrams
- **Proficiency**: 90% documentation, 85% API docs

## Usage Examples

### Example 1: Quick Security Check
```bash
python PRPs/scripts/prp-master.py multi-agent quick
```
Output:
- Basic compliance check by Analysis Agent
- Critical security scan by Security Agent
- Basic test coverage check by Test Agent

### Example 2: Full Feature Implementation
```bash
python PRPs/scripts/prp-master.py multi-agent "implement REST API for blog system"
```
The system will:
1. Code Agent: Generate API endpoints and models
2. Test Agent: Create comprehensive test suite
3. Security Agent: Review for vulnerabilities
4. Docs Agent: Generate API documentation
5. Deploy Agent: Prepare deployment configuration

### Example 3: Deep Analysis
```bash
python PRPs/scripts/prp-master.py multi-agent deep
```
Comprehensive analysis including:
- 12-factor compliance analysis
- Full code review across all files
- Security audit with vulnerability scanning
- Performance bottleneck identification
- Test coverage analysis
- Documentation completeness review

## Multi-Agent Coordination

### How It Works

1. **Task Submission**: You submit a high-level task
2. **Intelligent Decomposition**: The coordinator analyzes complexity and breaks it into subtasks
3. **Agent Assignment**: Each subtask is assigned to the most qualified agent
4. **Parallel Execution**: Agents work simultaneously when possible
5. **Dependency Management**: Tasks with dependencies wait for prerequisites
6. **Result Integration**: All results are combined into a comprehensive solution

### Coordination Patterns

#### Pattern 1: Sequential Dependencies
```
Code Generation → Testing → Security Review → Documentation
```

#### Pattern 2: Parallel Execution
```
┌─ Code Analysis ─┐
├─ Security Scan  ─┼─→ Integration
└─ Performance    ─┘
```

#### Pattern 3: Complex Orchestration
```
      ┌─→ Test Creation ─→ Test Execution ─┐
Task ─┼─→ Code Generation ─→ Security ────┼─→ Deployment
      └─→ Documentation ──────────────────┘
```

## Advanced Features

### Real-Time Monitoring
- Live status updates during execution
- Agent load distribution visibility
- Task progress tracking
- Performance metrics

### Fault Tolerance
- Automatic task retry on failure
- Agent health monitoring
- Graceful degradation
- Deadlock detection and resolution

### Performance Optimization
- Dynamic load balancing
- Agent performance scoring
- Task prioritization
- Resource optimization

## Configuration

### Customizing Agent Behavior

Edit `.prp/prp-config.json`:
```json
{
  "multi_agent": {
    "enabled": true,
    "max_agents": 10,
    "coordinator_mode": "enhanced",
    "auto_scaling": true,
    "task_timeout_multiplier": 3.0,
    "max_task_retries": 3
  }
}
```

### Agent Registration

To add custom agents, modify the `_get_agents_for_scope` method in `prp-master.py`:
```python
{
    'type': 'custom_agent',
    'capabilities': [
        {'name': 'custom_capability', 'proficiency': 0.9}
    ],
    'max_concurrent_tasks': 2
}
```

## Best Practices

1. **Use Specific Scopes**: Choose the right scope (quick/deep/fix) for your needs
2. **Natural Language Tasks**: Describe tasks clearly for better decomposition
3. **Monitor Progress**: Watch the real-time updates to understand execution
4. **Review Results**: Check detailed results from each agent
5. **Iterative Refinement**: Use agent feedback to improve task descriptions

## Troubleshooting

### Common Issues

1. **"No suitable agent found"**
   - Ensure required agents are registered
   - Check agent capabilities match task requirements

2. **"Task timeout"**
   - Complex tasks may take time
   - Adjust timeout in configuration

3. **"Import error"**
   - Ensure all dependencies are installed
   - Check Python path includes scripts directory

### Debug Mode

Enable detailed logging:
```bash
export PRP_DEBUG=true
python PRPs/scripts/prp-master.py multi-agent deep
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: PRP Multi-Agent Analysis
  run: |
    python PRPs/scripts/prp-master.py multi-agent quick
    if [ $? -ne 0 ]; then
      echo "Multi-agent analysis found issues"
      exit 1
    fi
```

### Pre-commit Hook
```bash
#!/bin/bash
python PRPs/scripts/prp-master.py multi-agent quick
if [ $? -ne 0 ]; then
  echo "Please fix issues before committing"
  exit 1
fi
```

## Future Enhancements

- **Machine Learning**: Agents learn from past performance
- **Custom Agents**: User-defined specialized agents
- **Cross-Project Learning**: Share knowledge between projects
- **Visual Dashboard**: Web-based monitoring interface
- **API Access**: RESTful API for agent coordination

## Getting Help

- Run `prp-master.py help` for command reference
- Check agent logs in `.prp/logs/`
- Submit issues to the project repository

---

The PRP Multi-Agent System revolutionizes development workflow by providing intelligent, collaborative AI assistance that adapts to your project's needs!