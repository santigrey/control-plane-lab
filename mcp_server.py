#!/usr/bin/env python3
"""
homelab_mcp — Project Ascension MCP Server
Runs on CiscoKid (192.168.1.10), port 8001.
"""

import json
import subprocess
import uuid
from typing import Optional

import psycopg2
import requests
import uvicorn
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

DB_HOST       = "127.0.0.1"
DB_PORT       = 5432
DB_NAME       = "controlplane"
DB_USER       = "admin"
DB_PASS       = "adminpass"
OLLAMA_URL    = "http://192.168.1.152:11434"
EMBED_MODEL   = "mxbai-embed-large"
SSH_USER      = "jes"
SSH_KEY       = "/home/jes/.ssh/id_ed25519"
ALLOWED_HOSTS = {
    "beast":    "192.168.1.152",
    "ciscokid": "192.168.1.10",
    "slimjim":  "192.168.1.40",
    "kalipi":   "192.168.1.254",
    "macmini":  "192.168.1.13",
    "cortez":   "192.168.1.240",
    "goliath":  "192.168.1.20",
    "pi3":      "192.168.1.139",
}
HOST_USERS = {
    "kalipi": "sloan",
    "cortez": "sloan",
    "pi3": "sloanzj",
}

mcp = FastMCP("homelab_mcp", host="0.0.0.0")

def db_connect():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

def get_embedding(text: str) -> list:
    r = requests.post(f"{OLLAMA_URL}/api/embeddings", json={"model": EMBED_MODEL, "prompt": text[:500]}, timeout=60)
    r.raise_for_status()
    return r.json()["embedding"]

def ssh_run(host: str, command: str, timeout: int = 30) -> dict:
    ip = ALLOWED_HOSTS[host]
    user = HOST_USERS.get(host, SSH_USER)
    result = subprocess.run(
        ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", f"{user}@{ip}", command],
        capture_output=True, text=True, timeout=timeout
    )
    return {"host": host, "command": command, "stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "exit_code": result.returncode}

class SSHRunInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    host: str = Field(..., description="Target host: beast, ciscokid, slimjim, kalipi, macmini, cortez, or goliath")
    command: str = Field(..., description="Shell command to run", min_length=1, max_length=100000)
    timeout: Optional[int] = Field(default=30, description="Timeout in seconds", ge=1, le=1800)

class MemorySearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(..., description="Natural language search query", min_length=1, max_length=100000)
    top_k: Optional[int] = Field(default=5, description="Number of results", ge=1, le=20)

class MemoryStoreInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    content: str = Field(..., description="Text content to store", min_length=1, max_length=100000)
    source: Optional[str] = Field(default="mcp", description="Source label")

class FileReadInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    host: str = Field(..., description="Target host name")
    path: str = Field(..., description="Absolute file path", min_length=1)

@mcp.tool(name="homelab_ssh_run", annotations={"readOnlyHint": False, "destructiveHint": False})
async def homelab_ssh_run(params: SSHRunInput) -> str:
    """Execute a shell command on a homelab node via SSH. Allowed hosts: beast, ciscokid, slimjim, kalipi, macmini, cortez, goliath."""
    if params.host not in ALLOWED_HOSTS:
        return json.dumps({"error": f"Unknown host '{params.host}'. Allowed: {list(ALLOWED_HOSTS.keys())}"})
    try:
        return json.dumps(ssh_run(params.host, params.command, params.timeout), indent=2)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Timed out after {params.timeout}s"})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(name="homelab_memory_search", annotations={"readOnlyHint": True, "destructiveHint": False})
async def homelab_memory_search(params: MemorySearchInput) -> str:
    """Semantic similarity search against pgvector memory table on CiscoKid."""
    try:
        embedding = get_embedding(params.query)
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT source, content, 1-(embedding <=> %s::vector) AS sim FROM memory ORDER BY embedding <=> %s::vector LIMIT %s", (embedding, embedding, params.top_k))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return json.dumps({"query": params.query, "results": [{"rank": i+1, "source": r[0], "content": (r[1] or "")[:200], "similarity": round(float(r[2]), 4)} for i, r in enumerate(rows)]}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(name="homelab_memory_store", annotations={"readOnlyHint": False, "destructiveHint": False})
async def homelab_memory_store(params: MemoryStoreInput) -> str:
    """Store a new entry in pgvector memory table on CiscoKid."""
    try:
        embedding = get_embedding(params.content)
        conn = db_connect()
        cur = conn.cursor()
        row_id = str(uuid.uuid4())
        cur.execute("INSERT INTO memory (id, source, content, embedding, embedding_model) VALUES (%s, %s, %s, %s::vector, %s)", (row_id, params.source, params.content, embedding, EMBED_MODEL))
        conn.commit(); cur.close(); conn.close()
        return json.dumps({"status": "stored", "id": row_id, "source": params.source})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(name="homelab_file_read", annotations={"readOnlyHint": True, "destructiveHint": False})
async def homelab_file_read(params: FileReadInput) -> str:
    """Read a file from any homelab node via SSH."""
    if params.host not in ALLOWED_HOSTS:
        return json.dumps({"error": f"Unknown host '{params.host}'"})
    try:
        result = ssh_run(params.host, f"cat {params.path}")
        if result["exit_code"] != 0:
            return json.dumps({"error": result["stderr"]})
        return json.dumps({"host": params.host, "path": params.path, "content": result["stdout"]}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(name="homelab_agent_status", annotations={"readOnlyHint": True, "destructiveHint": False})
async def homelab_agent_status() -> str:
    """Get current status of Agent OS services: orchestrator, ollama, pgvector."""
    status = {}
    try:
        r = requests.get("http://127.0.0.1:8000/healthz", timeout=5)
        status["orchestrator"] = "up" if r.status_code == 200 else f"degraded ({r.status_code})"
    except Exception:
        status["orchestrator"] = "down"
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memory")
        status["pgvector"] = f"up — {cur.fetchone()[0]} memory rows"
        cur.close(); conn.close()
    except Exception as e:
        status["pgvector"] = f"error: {e}"
    try:
        r = requests.get("http://192.168.1.152:11434/api/tags", timeout=5)
        d = r.json()
        status["ollama"] = f"up — {len(d.get('models', []))} models loaded"
    except Exception as e:
        status["ollama"] = f"error: {e}"
    return json.dumps(status, indent=2)

class CreateTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    created_by: str = Field(..., max_length=20)
    assigned_to: str = Field(..., max_length=20)
    title: str = Field(...)
    payload: Optional[dict] = Field(default=None)

class ListTasksInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    assigned_to: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=20)

class UpdateTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    task_id: str = Field(...)
    status: str = Field(..., max_length=20)
    result: Optional[dict] = Field(default=None)

class SendMessageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    from_agent: str = Field(..., max_length=20)
    to_agent: str = Field(..., max_length=20)
    content: str = Field(...)
    thread_id: Optional[str] = Field(default=None)

class ReadMessagesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    to_agent: str = Field(..., max_length=20)
    unread_only: Optional[bool] = Field(default=True)

@mcp.tool(name="homelab_create_task", annotations={"readOnlyHint": False, "destructiveHint": False})
async def homelab_create_task(params: CreateTaskInput) -> str:
    """Create a new task with status=pending_approval."""
    try:
        conn = db_connect(); cur = conn.cursor()
        cur.execute("INSERT INTO agent_tasks (created_by, assigned_to, title, payload) VALUES (%s, %s, %s, %s) RETURNING id, status, created_at",
            (params.created_by, params.assigned_to, params.title, json.dumps(params.payload) if params.payload else None))
        row = cur.fetchone(); conn.commit(); cur.close(); conn.close()
        return json.dumps({"id": str(row[0]), "status": row[1], "created_at": str(row[2])}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(name="homelab_list_tasks", annotations={"readOnlyHint": True, "destructiveHint": False})
async def homelab_list_tasks(params: ListTasksInput) -> str:
    """List tasks, optionally filtered by assigned_to and/or status."""
    try:
        conn = db_connect(); cur = conn.cursor()
        conds, vals = [], []
        if params.assigned_to: conds.append("assigned_to=%s"); vals.append(params.assigned_to)
        if params.status: conds.append("status=%s"); vals.append(params.status)
        w = ("WHERE " + " AND ".join(conds)) if conds else ""
        cur.execute(f"SELECT id,created_by,assigned_to,status,title,payload,result,created_at,updated_at FROM agent_tasks {w} ORDER BY created_at DESC", vals)
        rows = cur.fetchall(); cur.close(); conn.close()
        tasks = [{"id":str(r[0]),"created_by":r[1],"assigned_to":r[2],"status":r[3],"title":r[4],"payload":r[5],"result":r[6],"created_at":str(r[7]),"updated_at":str(r[8])} for r in rows]
        return json.dumps({"count": len(tasks), "tasks": tasks}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(name="homelab_update_task", annotations={"readOnlyHint": False, "destructiveHint": False})
async def homelab_update_task(params: UpdateTaskInput) -> str:
    """Update a task status and optional result."""
    try:
        conn = db_connect(); cur = conn.cursor()
        cur.execute("UPDATE agent_tasks SET status=%s,result=%s,updated_at=NOW() WHERE id=%s::uuid RETURNING id,status,updated_at",
            (params.status, json.dumps(params.result) if params.result else None, params.task_id))
        row = cur.fetchone(); conn.commit(); cur.close(); conn.close()
        if not row: return json.dumps({"error": f"Task {params.task_id} not found"})
        return json.dumps({"id": str(row[0]), "status": row[1], "updated_at": str(row[2])}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(name="homelab_send_message", annotations={"readOnlyHint": False, "destructiveHint": False})
async def homelab_send_message(params: SendMessageInput) -> str:
    """Send a message between agents."""
    try:
        conn = db_connect(); cur = conn.cursor()
        cur.execute("INSERT INTO messages (from_agent,to_agent,content,thread_id) VALUES (%s,%s,%s,%s::uuid) RETURNING id,created_at",
            (params.from_agent, params.to_agent, params.content, params.thread_id))
        row = cur.fetchone(); conn.commit(); cur.close(); conn.close()
        return json.dumps({"id": str(row[0]), "created_at": str(row[1])}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(name="homelab_read_messages", annotations={"readOnlyHint": False, "destructiveHint": False})
async def homelab_read_messages(params: ReadMessagesInput) -> str:
    """Read messages for an agent and mark them as read."""
    try:
        conn = db_connect(); cur = conn.cursor()
        w = "WHERE to_agent=%s" + (" AND read=FALSE" if params.unread_only else "")
        cur.execute(f"SELECT id,from_agent,to_agent,thread_id,content,read,created_at FROM messages {w} ORDER BY created_at ASC", (params.to_agent,))
        rows = cur.fetchall()
        ids = [str(r[0]) for r in rows]
        if ids: cur.execute("UPDATE messages SET read=TRUE WHERE id=ANY(%s::uuid[])", (ids,))
        conn.commit(); cur.close(); conn.close()
        msgs = [{"id":str(r[0]),"from_agent":r[1],"to_agent":r[2],"thread_id":str(r[3]) if r[3] else None,"content":r[4],"read":r[5],"created_at":str(r[6])} for r in rows]
        return json.dumps({"count": len(msgs), "messages": msgs}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


class UpdateProfileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    category: str = Field(..., description="Profile category")
    key: str = Field(..., description="Profile key")
    value: str = Field(..., description="Profile value")
    source: str = Field(default="agent", description="Source label")

@mcp.tool(name="homelab_get_profile", annotations={"readOnlyHint": True, "destructiveHint": False})
async def homelab_get_profile() -> str:
    """Return all user_profile rows grouped by category."""
    try:
        conn = db_connect(); cur = conn.cursor()
        cur.execute("SELECT category, key, value, updated_at FROM user_profile ORDER BY category, key")
        rows = cur.fetchall(); cur.close(); conn.close()
        grouped = {}
        for category, key, value, updated_at in rows:
            grouped.setdefault(category, {})[key] = {"value": value, "updated_at": str(updated_at)}
        return json.dumps(grouped, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool(name="homelab_update_profile", annotations={"readOnlyHint": False, "destructiveHint": False})
async def homelab_update_profile(params: UpdateProfileInput) -> str:
    """Upsert a key/value pair in the user_profile table."""
    try:
        conn = db_connect(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_profile (category, key, value, source) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (category, key) DO UPDATE SET value=EXCLUDED.value, source=EXCLUDED.source, updated_at=NOW()",
            (params.category, params.key, params.value, params.source)
        )
        conn.commit(); cur.close(); conn.close()
        return json.dumps({"category": params.category, "key": params.key, "value": params.value}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(mcp.streamable_http_app(), host="0.0.0.0", port=8001)
