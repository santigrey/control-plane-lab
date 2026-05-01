# PD -> Paco request -- Atlas v0.1 Cycle 1H tool surface (PRE-implementation gate)

**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1H -- atlas-mcp tool surface (which tools the inbound MCP server exposes; arg schemas; server-side ACL; telemetry contract)
**Predecessors:** `docs/paco_response_atlas_v0_1_cycle_1g_close_confirm.md` (Paco, HEAD `61d72fc`) + `docs/paco_review_atlas_v0_1_cycle_1g_close.md` (PD, commit `c04a35d`)
**Status:** **paco_request gate. NO implementation this turn.** PD surfaces 3 scope options + 2 argshape paths + ACL design + telemetry contract + recommendations. Paco rules. Then build directive dispatches.

---

## 0. Verified live (per 5th standing rule)

Captured 2026-05-01 UTC (Day 77) immediately before authoring this paco_request. All schema/code rows independently observed via direct queries against deployed state.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Atlas HEAD on Beast | `cd /home/jes/atlas && git log --oneline -1` | `2f2c3b7 feat: Cycle 1G MCP server skeleton (FastMCP loopback :8001 + Option A nginx Host rewrite)`; clean working tree |
| 2 | atlas-mcp.service state | `systemctl is-active atlas-mcp.service` + `pgrep -af atlas.mcp_server` + `ss -tlnp` | `active`; MainPID `1792209` running `/home/jes/atlas/.venv/bin/python -m atlas.mcp_server.server`; listener `127.0.0.1:8001 LISTEN` (loopback per Cycle 1G strict-loopback invariant) |
| 3 | atlas.* tables (4) | `psql -c '\dt atlas.*'` | `events` + `memory` + `schema_version` + `tasks`. **NO separate `atlas.embeddings` or `atlas.inference` tables** -- those names are `source` VALUES in atlas.events for logical operations, not table names. |
| 4 | atlas.events schema | `psql -c '\d atlas.events'` | Columns: `id bigint NOT NULL DEFAULT nextval(...)` + `ts timestamptz NOT NULL DEFAULT now()` + `source text NOT NULL` + `kind text NOT NULL` + `payload jsonb`. Indexes: `events_pkey (id)` + `events_source_kind_idx (source, kind)` + `events_ts_idx (ts DESC)` |
| 5 | **atlas.memory schema** (the embeddings store) | `psql -c '\d atlas.memory'` | Columns: `id bigint` + `ts timestamptz` + `kind text NOT NULL` + `content text NOT NULL` + **`embedding vector(1024)`** + `metadata jsonb`. Indexes: `memory_pkey (id)` + `memory_kind_ts_idx (kind, ts DESC)`. **Vector dimension = 1024.** |
| 6 | atlas.tasks schema | `psql -c '\d atlas.tasks'` | Columns: `id uuid DEFAULT gen_random_uuid()` + `status text NOT NULL` + `created_at timestamptz` + `updated_at timestamptz` + `owner text` + `payload jsonb` + `result jsonb`. **CHECK constraint: `status = ANY (ARRAY['pending','running','done','failed'])`**. Indexes: `tasks_pkey (id)` + `tasks_status_created_idx (status, created_at)` |
| 7 | atlas.schema_version migrations | `psql -c 'SELECT * FROM atlas.schema_version ORDER BY version'` | 5 migrations applied 2026-04-30 17:04:20 UTC: 1 create_atlas_schema, 2 atlas_schema_version, 3 atlas_tasks, 4 atlas_events, 5 atlas_memory |
| 8 | atlas.events GROUP BY source/kind | `psql -c 'SELECT source, kind, count(*) ...'` | `atlas.embeddings/embed_single = 12`; `atlas.inference/generate = 14`; `atlas.mcp_client/tool_call = 3`; `atlas.mcp_client/tools_list = 3` |
| 9 | atlas.mcp_client ACL pattern | `cat src/atlas/mcp_client/acl.py` | `@dataclass(frozen=True) AclDenyPattern(tool_name, arg, pattern: re.Pattern, reason)`; `ACL_DENY_PATTERNS: list[AclDenyPattern]` (1 entry: blocks Atlas writing to /home/jes/control-plane/); `check_acl(tool_name, arguments)` raises `AtlasAclDenied`; **looks in top-level args AND nested 'params'** (handles auto-wrapped form per Cycle 1F Refinement 2) |
| 10 | atlas.mcp_client telemetry payload shape | `psql -c "SELECT kind, payload FROM atlas.events WHERE source='atlas.mcp_client' ORDER BY ts DESC LIMIT 4;"` | `tool_call: {status, arg_keys, endpoint, tool_name, duration_ms}`; `tools_list: {status, arg_keys, endpoint, tool_name (null), duration_ms, tools_count}`. Sample arg_keys: `["command", "host"]` (caller-provided form per P6 #27 Refinement 3). |
| 11 | atlas.mcp_client `_log_event` write pattern | `sed -n` on client.py | `INSERT INTO atlas.events (source, kind, payload) VALUES (%s, %s, %s::jsonb)` with `json.dumps(payload, default=str)`; secrets discipline KEYS only, NEVER values; falls back to structlog if no db wired |
| 12 | **CK mcp_server.py argshape (P6 #28 VERIFIED LIVE, NOT memory-asserted)** | `grep -nE '^class \|async def \|@mcp.tool\|BaseModel\|Field' /home/jes/control-plane/mcp_server.py` | **Pydantic-wrapped uniformly across ALL CK tools.** Pattern: `class FooInput(BaseModel): foo: T = Field(..., description, min_length, max_length, ge, le, pattern)`; `@mcp.tool(name="homelab_X", annotations={"readOnlyHint": bool, "destructiveHint": bool})`; `async def homelab_X(params: FooInput) -> str:`. Examples observed: SSHRunInput, MemorySearchInput, MemoryStoreInput, FileReadInput, FileWriteInput, CreateTaskInput, ListTasksInput. Read-only tools annotated `readOnlyHint=True`; mutation tools `False`. |
| 13 | Substrate anchors PRE | `docker inspect ... --format` | `control-postgres-beast 2026-04-27T00:13:57.800746541Z healthy r=0` + `control-garage-beast 2026-04-27T05:39:58.168067641Z healthy r=0`; bit-identical 96+ hours through entire Cycle 1F + 1G saga |
| 14 | Tailscale auth key residual (PO1 from Cycle 1G; v0.2 P5 #22) | CEO action via `https://login.tailscale.com/admin/settings/keys` admin console | **PENDING CEO confirmation** -- preferred resolution: one-time-use key auto-consumed at Beast tailnet join (Cycle 1G Step 3); CEO confirms key listed as consumed/expired OR manually revokes if reusable. PD captures fingerprint confirmation (NOT key value) once CEO confirms. Banking is non-blocking for Cycle 1H paco_request authoring. |

**Anchor preservation invariant established PRE.** Substrate B2b + Garage MUST remain bit-identical through this paco_request authoring (no substrate touched; document-only).

**Critical schema-driven design implications:**
- Embeddings/inference are NOT separate tables; **`atlas.memory` is the embeddings store with `vector(1024)`**. Tool naming should reflect this (`atlas.memory.upsert/query`, not `atlas.embeddings.*`).
- atlas.tasks state machine has explicit CHECK constraint on status transitions; warrants dedicated ratification cycle, not bundling into 1H tool surface.
- atlas.mcp_client telemetry payload + ACL pattern are well-formed reusable templates; server-side mirrors them with `source='atlas.mcp_server'` swap.

---

## 1. TL;DR

Atlas inbound MCP server (skeleton, no @mcp.tool defs) is operational at `https://sloan2.tail1216a3.ts.net:8443/mcp`. Cycle 1H ratifies the **tool surface**: which Atlas tools to expose (subset of {events.search, memory.query, memory.upsert, inference.history, tasks.*}), with what argument schema (Pydantic-wrapped vs flat-args), what server-side ACL, what telemetry shape.

**PD recommends:**
- **Scope: Option B (Standard, read + curated writes)** -- 4 tools: `atlas.events.search` + `atlas.memory.query` + `atlas.memory.upsert` + `atlas.inference.history`. Defer `atlas.tasks.*` to Cycle 1I (state machine warrants dedicated ratification).
- **Argshape: Path X (Pydantic-wrapped, mirror CK)** -- verified live per P6 #28; CK uses Pydantic-wrapped uniformly; atlas.mcp_client supports auto-wrap per Refinement 3; uniform homelab pattern.
- **ACL: layered defense** -- atlas.mcp_client client-side ACL = first line; server-side `ACL_DENY_PATTERNS_SERVER` mirroring AclDenyPattern dataclass = LAST line authoritative; per-tool arg constraints declarative in Pydantic Field validators (size, dimension, range, pattern).
- **Telemetry: mirror atlas.mcp_client** with `source='atlas.mcp_server'`; kinds `tool_call/tool_call_denied/tools_list`; P6 #27 capture caller-provided arg_keys BEFORE any internal transformation.
- **Defer to v0.2:** atlas.tasks.*, per-tool rate-limiting, auth-context propagation beyond tailnet, server-side observability dashboards.

Anchors held bit-identical PRE. No substrate touched this paco_request.

---

## 2. Atlas v0.1 tool surface universe (informational; corrected per Verified live)

Canonical candidate tools as logical operations across atlas.* schema (NOT 1:1 to table names since some operations span tables/sources):

| Tool name | Backing | Direction | Argshape (proposed) | ACL surface |
|---|---|---|---|---|
| `atlas.events.search` | atlas.events SELECT with source/kind/ts-range filter | READ | EventsSearchInput {source: Optional[str], kind: Optional[str], ts_after, ts_before, limit} | source allowlist; ts_range max window; limit max 100 |
| `atlas.memory.query` | atlas.memory ORDER BY embedding <-> $1 LIMIT N (vector similarity) | READ | MemoryQueryInput {query_text: str (server-embeds via atlas.embeddings), top_k: int 1-20, kind: Optional[str]} | top_k max 20; query_text length cap |
| `atlas.memory.upsert` | atlas.memory INSERT (with server-side embedding generation) | WRITE | MemoryUpsertInput {kind: str, content: str, metadata: Optional[dict]} | content max length; kind allowlist; metadata size cap; rate considerations deferred to v0.2 |
| `atlas.inference.history` | atlas.events SELECT WHERE source='atlas.inference' (ergonomic subset of events.search) | READ | InferenceHistoryInput {model: Optional[str], ts_after, ts_before, limit} | limit max 50; ts_range max window |
| ~~`atlas.tasks.create`~~ | atlas.tasks INSERT | DEFERRED to Cycle 1I | -- | state machine ratification needed first |
| ~~`atlas.tasks.list`~~ | atlas.tasks SELECT | DEFERRED to Cycle 1I | -- | state machine ratification needed first |
| ~~`atlas.tasks.update`~~ | atlas.tasks UPDATE status | DEFERRED to Cycle 1I | -- | status transition rules need explicit ratification |
| ~~`atlas.events.append`~~ | atlas.events INSERT | NOT in scope v0.1 | -- | too low-level; users invoke specific kind operations |

---

## 3. Tool surface scope options

### Option A -- Minimum Viable (read-only only)

**Tools (3):** `atlas.events.search`, `atlas.memory.query`, `atlas.inference.history`

**Pros:**
- Smallest surface area; no write paths
- ACL is trivial (allowlist-only filtering on source/kind/ts-range)
- Fastest to ship + lowest risk of breaking changes
- Matches v0.1 "read your own data" CEO use case if Alexandra/CEO push memories via OTHER paths

**Cons:**
- No memory.upsert means CEO can't push notes/memories via Atlas inbound MCP -- defeats one of the primary use cases
- atlas.embeddings/embeddings.upsert paths (Cycle 1A-1E) remain only via direct DB or via atlas.mcp_client OUTBOUND from CK; inbound MCP can't write

### Option B -- Standard (read + curated writes) [PD RECOMMEND]

**Tools (4):** Option A + `atlas.memory.upsert`

**Pros:**
- Enables CEO/Alexandra push-to-memory via inbound (the primary v0.1 use case enabled)
- Server-side validates upsert (size limits via Pydantic Field; kind allowlist; metadata size cap)
- ACL surface manageable (1 deny pattern + Pydantic Field constraints)
- Slight schema design discipline overhead -- but the discipline forms a v0.1 reusable template for future write tools

**Cons:**
- Need server-side write validation discipline
- Upsert means Atlas tools can grow atlas.memory; rate considerations deferred to v0.2 P5

### Option C -- Full (all sensible operations including tasks)

**Tools (7):** Option B + `atlas.tasks.create` + `atlas.tasks.list` + `atlas.tasks.update`

**Pros:**
- Full surface for v0.1
- Task orchestration available via inbound MCP

**Cons:**
- atlas.tasks state machine (status: pending/running/done/failed) deserves dedicated ratification (transition rules: who can move pending->running? what's the owner field's authorization semantics? completion semantics for done vs failed?)
- Bundling into 1H makes paco_request scope creep + harder to ratify cleanly
- Migration pain higher if tasks tool shape needs revision (every caller couples to schemas)

### Option D (consider but reject) -- Surface includes `atlas.events.append`

**Reject reason:** atlas.events.append is too low-level. Users should invoke specific kind operations (memory.upsert writes its own atlas.events row internally per `_log_event` pattern) rather than directly authoring atlas.events records. This preserves source/kind discipline and avoids polluting atlas.events with arbitrary inbound payloads.

---

## 4. Argument schema decision

### Path X -- Pydantic-wrapped (mirror CK) [PD RECOMMEND]

**Pattern (mirror CK Verified live row 12):**

```python
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("atlas-mcp")

class MemoryUpsertInput(BaseModel):
    kind: str = Field(..., description="Memory kind label", min_length=1, max_length=50, pattern="^[a-z][a-z0-9_]*$")
    content: str = Field(..., description="Memory text content", min_length=1, max_length=100_000)
    metadata: Optional[dict] = Field(default=None, description="Optional metadata dict")

@mcp.tool(name="atlas_memory_upsert", annotations={"readOnlyHint": False, "destructiveHint": False})
async def atlas_memory_upsert(params: MemoryUpsertInput) -> str:
    ...
```

**Pros:**
- **P6 #28 Verified live**: CK uses this pattern uniformly (SSHRunInput, MemorySearchInput, MemoryStoreInput, FileReadInput, FileWriteInput, CreateTaskInput, ListTasksInput)
- Pattern consistency with CK + atlas.mcp_client (which already supports auto-wrap per Refinement 3 with caller_arg_keys preservation per P6 #27)
- Schema introspection is uniform (every tool's required: ["params"] + properties.params.* declares constraints)
- Pydantic Field validators are declarative + serializable + enforce server-side at decode time
- @mcp.tool annotations (`readOnlyHint`/`destructiveHint`) carry forward from CK pattern

**Cons:**
- Clients must auto-wrap or know to wrap manually (atlas.mcp_client Cycle 1F handles this via Refinement 3)
- Schema doesn't expose individual fields at top level (introspection wraps them under `params`)

### Path Y -- Flat args (reject)

**Reject reasons:**
- Diverges from CK pattern -- mixed homelab cognitive load ("Atlas server uses flat, CK MCP uses wrapped")
- Future agents/clients (Alexandra, Cowork bridge) would need conditional wrapping based on which server they target
- atlas.mcp_client Cycle 1F's Refinement 3 auto-wrap is targeted at the wrapped pattern; flat-args negates that work
- No proportional ergonomic gain over the wrapped approach (Pydantic validators apply either way)

---

## 5. Server-side ACL design

### 5.1 Layered defense architecture

- **Client-side ACL (atlas.mcp_client `ACL_DENY_PATTERNS`)** = FIRST line of defense; declines BEFORE network call (saves round-trip; preserves auditable client-side decision)
- **Server-side ACL (atlas.mcp_server `ACL_DENY_PATTERNS_SERVER`)** = LAST line of defense; AUTHORITATIVE because inbound clients can be Cowork bridge, future agents, or anything not running atlas.mcp_client
- Both layers should be present and not redundant
- Each layer logs its own denial to atlas.events (`source='atlas.mcp_client'` kind=`tool_call_denied` for client; `source='atlas.mcp_server'` kind=`tool_call_denied` for server)

### 5.2 Mirror dataclass shape; separate file

Server-side ACL lives at `src/atlas/mcp_server/acl.py` mirroring client-side `src/atlas/mcp_client/acl.py`:

```python
from dataclasses import dataclass
import re

class AtlasMcpServerAclDenied(Exception):
    """Raised when an inbound tool call matches a server-side ACL deny pattern."""

@dataclass(frozen=True)
class ServerAclDenyPattern:
    tool_name: str
    arg: str
    pattern: re.Pattern
    reason: str

ACL_DENY_PATTERNS_SERVER: list[ServerAclDenyPattern] = [
    # v0.1 placeholder examples; final list in Cycle 1H build directive:
    # - atlas.memory.upsert with kind values not in {note, observation, ...}
    # - atlas.events.search with source values outside the allowlist
    # - any tool from non-tailnet clients (deferred to v0.2 auth-context)
]

def check_server_acl(tool_name: str, arguments: dict) -> None:
    """Same pattern as client check_acl; looks top-level + nested 'params'."""
```

### 5.3 Per-tool argument constraints (Pydantic Field declarative)

Distinct from deny patterns -- these are CLAIMS validated at parse time:

- **EventsSearchInput**: source ∈ allowlist (atlas.embeddings, atlas.inference, atlas.mcp_client, atlas.mcp_server) OR `null`; kind length cap; ts_range max 30 days; limit ge 1 le 100
- **MemoryQueryInput**: query_text length 1..10000; top_k ge 1 le 20; kind optional length cap
- **MemoryUpsertInput**: content length 1..100000; kind regex `^[a-z][a-z0-9_]*$` length 1..50; metadata size cap (serialized JSON max 10KB)
- **InferenceHistoryInput**: model optional length cap; ts_range max 7 days; limit ge 1 le 50

### 5.4 Authoritative posture explicit in design doc

The server-side ACL design doc (forthcoming in Cycle 1H build) explicitly states: "Server-side ACL is the authoritative authorization boundary for all inbound MCP traffic. Client-side ACL is a defense-in-depth layer that reduces network load and provides client-side auditability; it MUST NOT be relied on as the only authorization control."

---

## 6. Telemetry contract

### 6.1 Source + kinds

- **Source:** `atlas.mcp_server`
- **Kinds:**
  - `tool_call` -- successful tool invocation
  - `tool_call_denied` -- ACL denied (server-side)
  - `tool_call_error` -- tool raised exception (DB unavailable, validation error, etc.)
  - `tools_list` -- handshake/list_tools call
  - `startup` (deferred per v0.2 P5 #19) -- server boot event with version + bind address

### 6.2 Payload shape (mirror atlas.mcp_client; canonical via Verified live row 10)

**tool_call:**
```json
{
  "tool_name": "atlas_memory_upsert",
  "arg_keys": ["content", "kind", "metadata"],
  "status": "success",
  "duration_ms": 42.3,
  "caller_endpoint": "100.115.56.89:54321"
}
```

**tool_call_denied** (server-side ACL):
```json
{
  "tool_name": "atlas_memory_upsert",
  "arg_keys": ["content", "kind"],
  "status": "denied",
  "deny_reason": "kind not in allowlist",
  "deny_layer": "server",
  "caller_endpoint": "100.x.y.z:port"
}
```

**tool_call_error:**
```json
{
  "tool_name": "atlas_memory_query",
  "arg_keys": ["query_text", "top_k"],
  "status": "error",
  "error_type": "DatabaseError",
  "duration_ms": 5.0
}
```

**tools_list:**
```json
{
  "tool_name": null,
  "arg_keys": [],
  "status": "success",
  "duration_ms": 1.5,
  "tools_count": 4
}
```

### 6.3 P6 #27 invariant application

**Capture caller-provided arg_keys BEFORE any internal transformation.** Specifically, in the FastMCP-dispatched async function body, the FIRST line captures `caller_arg_keys = sorted(params.dict().keys())` (Pydantic v1) or `sorted(params.model_dump().keys())` (Pydantic v2) BEFORE:
- SQL query construction
- Vector embedding generation (memory.upsert/query)
- ACL evaluation
- Any default-value injection or coercion

This ensures telemetry intelligibility regardless of internal processing changes.

### 6.4 Secrets discipline (audit gate)

- arg VALUES NEVER persisted to atlas.events; only KEYS
- Audit gate at Cycle 1H build close: `psql LIKE '%authkey%|%tskey%|%password%|%secret%'` returns 0 hits in atlas.mcp_server payload column
- Match Cycle 1F + 1G secrets discipline pattern

### 6.5 Reuse `_log_event` pattern

Server-side telemetry write reuses atlas.mcp_client's `_log_event` pattern (banked v0.2 P5 #19 for extraction as standalone utility): `INSERT INTO atlas.events (source, kind, payload) VALUES (%s, %s, %s::jsonb)` with `json.dumps(payload, default=str)` + structlog fallback.

---

## 7. Substrate impact

**Anchor preservation invariant (must hold across paco_request authoring this turn AND through subsequent build cycle):**
- `control-postgres-beast` = `2026-04-27T00:13:57.800746541Z healthy r=0` (96+ hrs at PRE)
- `control-garage-beast` = `2026-04-27T05:39:58.168067641Z healthy r=0` (96+ hrs at PRE)
- These are Docker containers; tool definition additions to atlas-mcp.service are application-layer code changes, do NOT touch substrate

**Existing infrastructure NOT touched in any option:**
- atlas.events / atlas.memory / atlas.tasks / atlas.schema_version schemas -- NO migrations needed for Option B (existing schema covers events.search, memory.query, memory.upsert, inference.history)
- mcp_server.py on CK (homelab MCP) -- untouched
- nginx vhost on Beast -- untouched (already routes /mcp to loopback :8001)
- atlas-mcp.service systemd unit -- untouched (ExecStart already runs `python -m atlas.mcp_server.server`)
- Beast Tailscale state -- untouched
- atlas.mcp_client (Cycle 1F outbound) -- untouched

**Build-cycle changes (subsequent paco_request after this ratifies):**
- `src/atlas/mcp_server/server.py` adds @mcp.tool definitions for the ratified surface
- `src/atlas/mcp_server/acl.py` NEW file mirroring client/acl.py shape
- `src/atlas/mcp_server/{events,memory,inference}.py` -- per-tool implementation modules (DB queries, embedding generation calls, etc.)
- atlas-mcp.service restart at build close
- Smoke test from CK verifies non-zero tools_count + sample tool invocation

**Schema migration:** NONE for Option B (uses existing tables). Option C (with atlas.tasks.*) also NONE since atlas.tasks already exists.

---

## 8. Asks for Paco

1. **Ratify scope: Option B** (4 tools: events.search + memory.query + memory.upsert + inference.history) OR amend to A/C.

2. **Ratify argshape: Path X** (Pydantic-wrapped mirror CK + atlas.mcp_client auto-wrap support) OR amend to Path Y.

3. **Ratify ACL design:** layered defense (client-side first line + server-side LAST line authoritative); mirror AclDenyPattern dataclass shape in `src/atlas/mcp_server/acl.py`; per-tool arg constraints declarative in Pydantic Field validators. OR amend.

4. **Ratify telemetry contract:** source=atlas.mcp_server; 4 kinds (tool_call/tool_call_denied/tool_call_error/tools_list); payload shape mirroring atlas.mcp_client + Verified live row 10 + P6 #27 invariant capture. OR amend.

5. **Authorize implementation handoff next turn.** Once shape ratified, dispatch build directive with: per-tool input class (Pydantic BaseModel with Field validators), per-tool implementation, server-side ACL file, telemetry write integration, restart atlas-mcp.service, smoke test (tools_count=4 expected; sample tool invocation success).

6. **Confirm atlas.tasks.* deferral** to Cycle 1I (state machine warrants dedicated ratification; status transitions, owner field semantics, completion semantics).

7. **Confirm v0.2 deferrals:** per-tool rate-limiting, auth-context propagation beyond tailnet membership, server-side observability dashboards. PD bias: defer all three.

8. **Bank v0.2 P5 candidates surfaced this turn:**
   - **#23 NEW**: extract `_log_event` pattern from atlas.mcp_client into shared `atlas.telemetry` utility module so server + client + future modules don't duplicate the INSERT logic (currently banked separately as #19 server-side startup hook -- this #23 is the broader utility extraction)
   - **#24 NEW**: design retroactive `atlas.events.source` allowlist enforcement (current schema has source as free-form text; deny-list approach via ACL works v0.1 but a CHECK constraint or enum would be more robust at v0.2 hardening)

---

## Cross-references

- **Predecessor**: `paco_response_atlas_v0_1_cycle_1g_close_confirm.md` Section 4 (Cycle 1H dispatch)
- **Cycle 1F atlas.mcp_client** (mirror reference): `src/atlas/mcp_client/{acl.py, client.py}` on Beast at HEAD `2f2c3b7`; ACL pattern verified live row 9; telemetry payload verified live row 10
- **Cycle 1G strict-loopback invariant** (preserved): atlas-mcp.service still 127.0.0.1:8001 loopback; nginx rewrites Host on the way through
- **CK mcp_server.py argshape pattern** (P6 #28 verified live): `/home/jes/control-plane/mcp_server.py` lines 65-93 (input classes) + lines 97-204 (tool definitions); `params: SomeInput` uniform pattern
- **Spec**: Atlas v0.1 spec v3 section 8.1H (atlas-mcp tool surface)
- **Hot Take memory**: layered-defense pattern (client+server ACL) parallels homelab security-posture discipline

-- PD
