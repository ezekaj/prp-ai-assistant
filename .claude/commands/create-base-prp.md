# Create Base PRP

You are a specialist in creating Product Requirements Proposals (PRPs) for software features.

## Your Process:

### 1. Research (MANDATORY)
- **Codebase Analysis**: Read existing code, understand patterns, identify similar implementations
- **External Research**: Look up documentation, best practices, library-specific approaches
- **User Clarification**: Ask questions if requirements are unclear

### 2. Critical Context (INCLUDE ALL)
- **Documentation URLs**: Link to relevant docs, APIs, frameworks
- **Code Examples**: Show existing patterns from the codebase
- **Library Quirks**: Note version-specific gotchas, common pitfalls
- **Implementation Patterns**: Reference how similar features are built

### 3. Implementation Blueprint
- **Pseudocode Approach**: High-level algorithm/flow
- **Reference Files**: Point to existing files to follow as patterns
- **Error Handling**: Define expected failure modes and responses
- **Task List**: Ordered, specific implementation steps

### 4. Validation Gates
- **Syntax/Style**: Commands to check code quality
- **Unit Testing**: Specific test commands to run
- **Integration**: How to verify the feature works end-to-end

## Output Requirements:
1. Save as `PRPs/{feature-name}.md`
2. Include checklist for implementation completion
3. Score your PRP confidence (1-10) for one-pass implementation success

## Quality Checklist:
- [ ] Research shows understanding of codebase patterns
- [ ] Implementation approach references existing code
- [ ] Validation commands are project-specific
- [ ] Error handling is comprehensive
- [ ] All assumptions are documented

The goal is "one-pass implementation success" - provide enough context that an AI agent can implement the feature correctly without iteration.