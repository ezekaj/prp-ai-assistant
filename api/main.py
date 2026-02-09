import os
import uuid
import time
import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from analyzer import CodeAnalyzer

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = os.environ.get("DB_PATH", "/data/prp.db")

os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            color TEXT,
            capabilities TEXT,
            enabled INTEGER DEFAULT 1,
            tasks_completed INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0.0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            agent_id TEXT,
            status TEXT DEFAULT 'queued',
            priority TEXT DEFAULT 'medium',
            progress INTEGER DEFAULT 0,
            result TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (datetime('now')),
            tasks_submitted INTEGER DEFAULT 0,
            tasks_completed INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0.0,
            active_agents INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS analysis_results (
            id TEXT PRIMARY KEY,
            code_hash TEXT,
            language TEXT,
            score INTEGER,
            grade TEXT,
            result TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    # Seed default agents if empty
    cursor = conn.execute("SELECT COUNT(*) FROM agents")
    if cursor.fetchone()[0] == 0:
        default_agents = [
            ("code-agent", "CodeAgent", "code_generation", "Code generation, refactoring, and bug fixes", "blue",
             json.dumps(["python", "javascript", "api_design", "refactoring", "bug_fixes"])),
            ("test-agent", "TestAgent", "testing", "Unit, integration, and e2e testing", "green",
             json.dumps(["unit_tests", "integration_tests", "coverage_analysis", "load_testing"])),
            ("security-agent", "SecurityAgent", "security", "Vulnerability scanning and security audits", "red",
             json.dumps(["vulnerability_scanning", "code_audit", "compliance_check", "owasp_analysis"])),
            ("deploy-agent", "DeployAgent", "deployment", "Deployment and infrastructure management", "purple",
             json.dumps(["docker", "kubernetes", "ci_cd", "monitoring", "database_migration"])),
            ("analysis-agent", "AnalysisAgent", "analysis", "Performance analysis and code review", "amber",
             json.dumps(["performance_analysis", "code_review", "architecture_review", "optimization"])),
            ("docs-agent", "DocsAgent", "documentation", "Documentation and API guides", "cyan",
             json.dumps(["api_docs", "markdown", "openapi_specs", "tutorials", "deployment_guides"])),
        ]
        conn.executemany(
            "INSERT INTO agents (id, name, type, description, color, capabilities) VALUES (?, ?, ?, ?, ?, ?)",
            default_agents,
        )

    # Seed some metrics history if empty
    cursor = conn.execute("SELECT COUNT(*) FROM metrics")
    if cursor.fetchone()[0] == 0:
        now = datetime.utcnow()
        for i in range(24):
            ts = (now - timedelta(hours=23 - i)).strftime("%Y-%m-%d %H:%M:%S")
            submitted = [32, 28, 22, 18, 15, 12, 14, 20, 35, 48, 62, 70, 75, 72, 68, 65, 70, 74, 80, 78, 72, 65, 55, 42][i]
            completed = [30, 26, 20, 16, 13, 10, 12, 18, 32, 44, 58, 65, 70, 68, 64, 62, 66, 70, 76, 74, 68, 60, 50, 38][i]
            active = 5 + (1 if i > 6 and i < 22 else 0)
            avg_rt = round(1.0 + (0.5 * (submitted / 80)), 2)
            conn.execute(
                "INSERT INTO metrics (timestamp, tasks_submitted, tasks_completed, avg_response_time, active_agents) VALUES (?, ?, ?, ?, ?)",
                (ts, submitted, completed, avg_rt, active),
            )

    # Seed some tasks if empty
    cursor = conn.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        seed_tasks = [
            (str(uuid.uuid4()), "Generate quarterly report", "Compile Q4 metrics and performance data", "docs-agent", "completed", "medium", 100),
            (str(uuid.uuid4()), "Analyze user behavior data", "Deep analysis of user session patterns", "analysis-agent", "completed", "high", 100),
            (str(uuid.uuid4()), "Refactor auth middleware", "Modernize JWT validation pipeline", "code-agent", "completed", "high", 100),
            (str(uuid.uuid4()), "Security audit: payment module", "Full OWASP scan on payment endpoints", "security-agent", "processing", "critical", 72),
            (str(uuid.uuid4()), "Deploy v2.4.1 to staging", "Rolling deployment with health checks", "deploy-agent", "processing", "medium", 45),
            (str(uuid.uuid4()), "Research competitor API features", "Benchmark competitor API capabilities", "analysis-agent", "processing", "low", 23),
            (str(uuid.uuid4()), "Write integration tests for orders", "Cover order creation and payment flows", "test-agent", "queued", "medium", 0),
            (str(uuid.uuid4()), "Optimize database indexing", "Analyze slow queries and add indexes", "analysis-agent", "queued", "high", 0),
        ]
        for t in seed_tasks:
            conn.execute(
                "INSERT INTO tasks (id, title, description, agent_id, status, priority, progress) VALUES (?, ?, ?, ?, ?, ?, ?)",
                t,
            )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    agent_id: str = "auto"
    priority: str = "medium"


class AnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = "auto"


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PRP-AI Assistant API",
    description="Simplified backend powering the PRP-AI multi-agent dashboard",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = CodeAnalyzer()
_start_time = time.time()


@app.on_event("startup")
def startup():
    init_db()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    uptime = time.time() - _start_time
    return {
        "status": "healthy",
        "version": "2.0.0",
        "uptime_seconds": round(uptime, 1),
        "timestamp": datetime.utcnow().isoformat(),
        "database": "sqlite",
        "environment": os.environ.get("PRP_ENV", "production"),
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/api/dashboard")
def dashboard():
    conn = get_db()
    try:
        agents = conn.execute("SELECT * FROM agents").fetchall()
        active_agents = sum(1 for a in agents if a["enabled"])
        total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        completed_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'").fetchone()[0]
        processing_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'processing'").fetchone()[0]
        queued_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'queued'").fetchone()[0]

        success_rate = round((completed_tasks / max(total_tasks, 1)) * 100, 1)

        last_metric = conn.execute("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1").fetchone()
        avg_response = last_metric["avg_response_time"] if last_metric else 1.2

        return {
            "active_agents": active_agents,
            "total_agents": len(agents),
            "tasks_processed": completed_tasks + processing_tasks,
            "tasks_completed": completed_tasks,
            "tasks_processing": processing_tasks,
            "tasks_queued": queued_tasks,
            "success_rate": success_rate,
            "avg_response_time": avg_response,
            "uptime": 99.97,
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

@app.get("/api/agents")
def list_agents():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM agents ORDER BY name").fetchall()
        agents = []
        for r in rows:
            agents.append({
                "id": r["id"],
                "name": r["name"],
                "type": r["type"],
                "description": r["description"],
                "color": r["color"],
                "capabilities": json.loads(r["capabilities"]) if r["capabilities"] else [],
                "enabled": bool(r["enabled"]),
                "tasks_completed": r["tasks_completed"],
                "avg_response_time": r["avg_response_time"],
            })
        active = sum(1 for a in agents if a["enabled"])
        return {
            "agents": agents,
            "total": len(agents),
            "active": active,
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        conn.close()


@app.post("/api/agents/{agent_id}/toggle")
def toggle_agent(agent_id: str):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        new_state = 0 if row["enabled"] else 1
        conn.execute("UPDATE agents SET enabled = ? WHERE id = ?", (new_state, agent_id))
        conn.commit()
        return {
            "id": agent_id,
            "name": row["name"],
            "enabled": bool(new_state),
            "message": f"{row['name']} {'enabled' if new_state else 'disabled'}",
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@app.get("/api/tasks")
def list_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    conn = get_db()
    try:
        query = "SELECT * FROM tasks"
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(query, params).fetchall()

        total = conn.execute(
            "SELECT COUNT(*) FROM tasks" + (" WHERE status = ?" if status else ""),
            [status] if status else [],
        ).fetchone()[0]

        tasks = []
        for r in rows:
            tasks.append({
                "id": r["id"],
                "title": r["title"],
                "description": r["description"],
                "agent_id": r["agent_id"],
                "status": r["status"],
                "priority": r["priority"],
                "progress": r["progress"],
                "result": json.loads(r["result"]) if r["result"] else None,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "completed_at": r["completed_at"],
            })

        return {"tasks": tasks, "total": total, "limit": limit, "offset": offset}
    finally:
        conn.close()


@app.post("/api/tasks")
def create_task(task: TaskCreate):
    conn = get_db()
    try:
        task_id = str(uuid.uuid4())
        agent_id = task.agent_id

        if agent_id == "auto":
            row = conn.execute(
                "SELECT id FROM agents WHERE enabled = 1 ORDER BY tasks_completed ASC LIMIT 1"
            ).fetchone()
            agent_id = row["id"] if row else "code-agent"

        agent = conn.execute("SELECT name FROM agents WHERE id = ?", (agent_id,)).fetchone()
        agent_name = agent["name"] if agent else agent_id

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO tasks (id, title, description, agent_id, status, priority, progress, created_at, updated_at) VALUES (?, ?, ?, ?, 'queued', ?, 0, ?, ?)",
            (task_id, task.title, task.description, agent_id, task.priority, now, now),
        )
        conn.commit()

        return {
            "id": task_id,
            "title": task.title,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": "queued",
            "priority": task.priority,
            "message": f"Task created and assigned to {agent_name}",
        }
    finally:
        conn.close()


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    conn = get_db()
    try:
        r = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Task not found")
        return {
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "agent_id": r["agent_id"],
            "status": r["status"],
            "priority": r["priority"],
            "progress": r["progress"],
            "result": json.loads(r["result"]) if r["result"] else None,
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "completed_at": r["completed_at"],
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Code Analysis
# ---------------------------------------------------------------------------

@app.post("/api/analyze")
def analyze_code(req: AnalyzeRequest):
    import hashlib

    code_hash = hashlib.sha256(req.code.encode()).hexdigest()[:16]
    result = analyzer.analyze(req.code, req.language)

    analysis_id = str(uuid.uuid4())
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO analysis_results (id, code_hash, language, score, grade, result, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (analysis_id, code_hash, result["language"], result["score"], result["grade"],
             json.dumps(result), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
    finally:
        conn.close()

    result["analysis_id"] = analysis_id
    return result


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@app.get("/api/metrics")
def get_metrics(hours: int = Query(24, ge=1, le=168)):
    conn = get_db()
    try:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute(
            "SELECT * FROM metrics WHERE timestamp >= ? ORDER BY timestamp ASC",
            (cutoff,),
        ).fetchall()

        data_points = []
        for r in rows:
            data_points.append({
                "timestamp": r["timestamp"],
                "tasks_submitted": r["tasks_submitted"],
                "tasks_completed": r["tasks_completed"],
                "avg_response_time": r["avg_response_time"],
                "active_agents": r["active_agents"],
            })

        return {
            "hours": hours,
            "data_points": data_points,
            "total_submitted": sum(d["tasks_submitted"] for d in data_points),
            "total_completed": sum(d["tasks_completed"] for d in data_points),
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "PRP-AI Assistant API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "dashboard": "/api/dashboard",
            "agents": "/api/agents",
            "tasks": "/api/tasks",
            "analyze": "/api/analyze",
            "metrics": "/api/metrics",
        },
    }
