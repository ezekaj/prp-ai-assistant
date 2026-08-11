# PRP AI Assistant

Tooling for **PRP (Product Requirement Prompt)** — a structured approach to
AI-assisted development where each unit of work is specified before an agent
writes any code, rather than prompted conversationally and corrected afterwards.

~25,000 lines of Python across generation, orchestration, monitoring and analytics.

---

## The idea

Conversational AI coding drifts. You ask for a feature, the agent makes assumptions,
you correct them, it makes new ones, and after twenty exchanges nobody can say what
was actually specified versus improvised.

PRP fixes the specification first. Each PRP is a self-contained document describing
context, requirements, constraints and validation criteria — written and reviewed
*before* execution. The agent gets one well-formed brief instead of twenty partial
ones, and the brief is a durable artifact you can diff, review and re-run.

The methodology draws on [12-Factor App](https://12factor.net) thinking: explicit
configuration, reproducible processes, and no hidden state between steps.

## What's here

| Component | What it does |
|---|---|
| `PRPs/scripts/prp-generator.py` | Builds PRP documents from a task description |
| `PRPs/scripts/prp-master.py` | Central control — dispatches PRPs to agents |
| `PRPs/scripts/prp_ai_agent_coordinator.py` | Multi-agent coordination and task routing |
| `PRPs/scripts/prp-ai-code-generator.py` | Code generation against a PRP spec |
| `PRPs/scripts/prp-ai-debugger.py` | Failure diagnosis within a PRP run |
| `PRPs/scripts/prp-ai-learning-engine.py` | Records outcomes to refine later PRPs |
| `PRPs/scripts/prp-analytics.py` · `prp-dashboard.py` | Run metrics and reporting |
| `.prp/monitoring/continuous_monitor.py` | Background compliance scanning |
| `.claude/commands/` | Slash commands wiring the above into Claude Code |

CI workflows for linting, PR validation and deployment live in `.github/workflows/`.

## Usage

```bash
pip install -r requirements.txt
cp .env.example .env          # add your API keys

python PRPs/scripts/prp-generator.py --task "add rate limiting to the API"
python PRPs/scripts/prp-master.py --execute PRPs/generated/<name>.md
```

Inside Claude Code, the same flow is available as slash commands — see
`.claude/commands/development/`.

---

## Status and honest scope

This is **personal tooling**, built to make my own AI-assisted work reproducible.
It is not a packaged product:

- No published benchmarks. Earlier versions of this README quoted success-rate and
  latency figures — those were design targets copied from planning documents, not
  measurements, and have been removed.
- Test coverage is partial (8 test modules against 76 source files).
- The `docs/` and roadmap markdown contain aspirational planning material written
  during development. Treat the code as the source of truth, not the roadmaps.

It is published because the underlying idea — specify before you generate — has
held up well in practice, and the orchestration code may be useful to others
working on agent pipelines.

MIT — Elvi Zekaj
