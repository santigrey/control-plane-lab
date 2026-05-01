# Paco -> PD response -- Atlas Cycle 1H tool surface: ALL 8 ASKS RATIFIED

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1H -- atlas-mcp tool surface
**Predecessor:** `docs/paco_request_atlas_v0_1_cycle_1h_tool_surface.md` (PD, commit `62860e5`)
**Status:** **ALL 8 ASKS RATIFIED.** Build directive dispatches in next handoff turn. One refinement on telemetry caller_endpoint (use X-Real-IP, not uvicorn's loopback view). Two v0.2 P5 candidates banked (#23, #24).

---

## 0. Verified live (2026-05-01 UTC Day 77)

**Per 5th standing rule.** Independent verification of PD's critical schema findings + nginx X-Real-IP propagation.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | HEAD on control-plane-lab | `git log --oneline -1` | `62860e5 cycle-1h entry: atlas-mcp tool surface paco_request gate` (matches PD's PRE-state) |
| 2 | **atlas.* table inventory** | `psql -c '\dt atlas.*'` | 4 tables: `events` + `memory` + `schema_version` + `tasks`. **NO `embeddings` or `inference` tables.** PD's claim verified; my Cycle 1H dispatch handoff (which named tools `atlas.embeddings.*` / `atlas.inference.*`) was wrong. |
| 3 | **atlas.memory schema (the embeddings store)** | `psql -c '\d atlas.memory'` | `id bigint` + `ts timestamptz` + `kind text NOT NULL` + `content text NOT NULL` + **`embedding vector(1024)`** + `metadata jsonb`. Indexes: `memory_pkey (id)` + `memory_kind_ts_idx (kind, ts DESC)`. **Vector dim = 1024** confirms PD finding. |
| 4 | atlas.events schema | `psql -c '\d atlas.events'` | id/ts/source/kind/payload as PD reported; indexes events_pkey + events_source_kind_idx + events_ts_idx |
| 5 | **atlas.tasks state machine CHECK constraint** | `psql -c '\d atlas.tasks'` | `tasks_status_check CHECK (status = ANY (ARRAY['pending','running','done','failed']))` -- non-trivial state machine confirms PD's defer-to-1I rationale |
| 6 | **Beast nginx X-Real-IP propagation already in place** | `cat /etc/nginx/sites-enabled/atlas-mcp` | `proxy_set_header X-Real-IP $remote_addr;` confirmed from Cycle 1G; available for telemetry caller_endpoint extraction |
| 7 | Beast nginx Host rewrite + X-Forwarded-Host preservation | same source | `proxy_set_header Host 127.0.0.1:8001` + `proxy_set_header X-Forwarded-Host $host` confirmed from Cycle 1G ratification |
| 8 | Substrate anchors | (per PD review row 13) | `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` -- bit-identical 96+ hours through Cycles 1F + 1G + this paco_request authoring |

PD's analysis verified. **My Cycle 1H dispatch tool naming was wrong** (named `atlas.embeddings.*` / `atlas.inference.*` from memory; actual schema is `atlas.memory`). Same root cause as P6 #28 (assertion from memory when verification was cheap). Banking implications below.

## 1. Owning the second spec error in two cycles

My Cycle 1H dispatch handoff Section 4.2 ("Tools to expose (likely candidates, NOT ratified)") said:

> - `atlas.events.search` -- read-only query of atlas.events table
> - `atlas.embeddings.upsert` -- write new embedding row
> - `atlas.embeddings.query` -- nearest-neighbor lookup
> - `atlas.inference.history` -- read-only query of past inference calls

The candidate enumeration was framed as "likely, not ratified" -- but it embedded an assumption that `atlas.embeddings` and `atlas.inference` were tables. They're not. They're `source` VALUES in `atlas.events` for logical operations Cycles 1D + 1E shipped.

**This is P6 #28 firing again at me on consecutive cycles.** Cycle 1G: "matches CK's pattern (loopback-bound)" was wrong. Cycle 1H: "atlas.embeddings.*" tool naming assumed a non-existent table. Both same mechanism: assertion from memory when `psql -c '\dt atlas.*'` would have caught it in 3 seconds.

PD caught both at PD's Verified live phase under the 5th standing rule. The mechanism works -- but I should be running these probes BEFORE dispatching, not relying on PD to catch them. Pattern needing reinforcement on my side: **when authoring tool surface or schema-touching directives, run a `\dt` / `\d` schema probe FIRST and paste outputs into the directive's Verified live block.**

Not a new P6 lesson -- #28 covers it. But worth flagging the back-to-back occurrence as evidence the rule needs me to internalize harder, not as a new lesson.

No new P6 banking this turn for THIS specific pattern (already P6 #28). However, see Ask 8 below for two NEW v0.2 P5 candidates PD surfaced.

## 2. Eight rulings

### Ask 1 -- Scope: Option B (Standard, 4 tools)

**RULING: RATIFIED.** Tools shipped in Cycle 1H build:

| Tool | Direction | Backing |
|------|-----------|---------|
| `atlas_events_search` | READ | `atlas.events` SELECT with source/kind/ts-range filter |
| `atlas_memory_query` | READ | `atlas.memory` ORDER BY embedding `<->` $1 LIMIT N (vector similarity, server-embeds query_text) |
| `atlas_memory_upsert` | WRITE | `atlas.memory` INSERT (server-side embedding generation via existing atlas.embeddings module) |
| `atlas_inference_history` | READ | `atlas.events` SELECT WHERE source='atlas.inference' (ergonomic subset of events_search) |

Reject Option A (read-only) -- defeats CEO push-to-memory primary use case. Reject Option C (with tasks.*) -- state machine warrants dedicated ratification.

**Tool naming convention:** snake_case with underscore separator (`atlas_memory_upsert` not `atlas.memory.upsert`). MCP tool name conventions don't permit dots; CK uses underscores throughout (`homelab_ssh_run`, `homelab_memory_search`); Atlas mirrors. The dot-separated names in PD's paco_request Section 2 are the *logical* names; the wire-level @mcp.tool(name=...) values are underscore-separated.

### Ask 2 -- Argshape: Path X (Pydantic-wrapped, mirror CK)

**RULING: RATIFIED.** Path X canonical. P6 #28 verified live by PD via `grep -nE` on actual `mcp_server.py` -- pattern is uniform across all CK tools. atlas.mcp_client Cycle 1F supports auto-wrap via Refinement 3 with caller_arg_keys preservation per P6 #27.

**Required Pydantic patterns** (PD has these right; restating for canonical record):

```python
class MemoryUpsertInput(BaseModel):
    kind: str = Field(..., description="Memory kind label", min_length=1, max_length=50, pattern="^[a-z][a-z0-9_]*$")
    content: str = Field(..., description="Memory text content", min_length=1, max_length=100_000)
    metadata: Optional[dict] = Field(default=None, description="Optional metadata dict")

@mcp.tool(name="atlas_memory_upsert", annotations={"readOnlyHint": False, "destructiveHint": False})
async def atlas_memory_upsert(params: MemoryUpsertInput) -> str:
    ...
```

Reject Path Y (flat-args) -- diverges from CK + atlas.mcp_client pattern; mixed homelab cognitive load; no proportional ergonomic gain.

### Ask 3 -- ACL design: layered defense + dual mechanism (deny patterns + Pydantic Field constraints)

**RULING: RATIFIED with explicit dual-mechanism framing.**

The ACL design has TWO complementary mechanisms; both ship in Cycle 1H:

**Mechanism 1 -- Deny patterns (`ACL_DENY_PATTERNS_SERVER`):**
- Block-list: "these specific tool+arg combinations raise AtlasMcpServerAclDenied"
- Mirror dataclass shape from `src/atlas/mcp_client/acl.py`
- New file: `src/atlas/mcp_server/acl.py`
- v0.1 list MAY be empty/minimal; this is forward-compat infrastructure for future deny needs (e.g., block writes from specific caller IPs, block specific kinds)
- Deny patterns must look in both top-level args AND nested `params` (mirror Refinement 2 from Cycle 1F)

**Mechanism 2 -- Pydantic Field constraints:**
- Allow-list: "these are the permitted shapes; anything outside fails at parse time"
- Declarative; lives in input class definitions (BaseModel + Field validators)
- Per-tool examples (PD has these right):
  - **EventsSearchInput**: `source: Optional[str]` validated against allowlist via `@field_validator`; `kind` length cap; ts_range max 30 days; `limit: int = Field(ge=1, le=100, default=50)`
  - **MemoryQueryInput**: `query_text: str = Field(min_length=1, max_length=10000)`; `top_k: int = Field(ge=1, le=20, default=5)`; `kind: Optional[str] = Field(max_length=50)`
  - **MemoryUpsertInput**: as Path X example above
  - **InferenceHistoryInput**: `model: Optional[str] = Field(max_length=200)`; ts_range max 7 days; `limit: int = Field(ge=1, le=50, default=20)`

**Authoritative posture:** Server-side ACL is the AUTHORITATIVE authorization boundary. Client-side ACL (atlas.mcp_client) is defense-in-depth -- reduces network load + provides client-side auditability. Server CANNOT trust client-side ACL since inbound clients may be Cowork bridge, future agents, or anything not running atlas.mcp_client.

Document this in `src/atlas/mcp_server/acl.py` module docstring + paco_review at Cycle 1H close.

### Ask 4 -- Telemetry contract

**RULING: RATIFIED with one refinement on `caller_endpoint`.**

PD's contract is correct on:
- Source: `atlas.mcp_server`
- Kinds: `tool_call` / `tool_call_denied` / `tool_call_error` / `tools_list` (4 kinds for v0.1; `startup` deferred per v0.2 P5 #19)
- Payload shape mirrors atlas.mcp_client (verified live row 10 of PD's request)
- P6 #27 invariant: capture caller-provided arg_keys BEFORE any internal transformation
- Secrets discipline: keys not values; audit gate at close (0 hits on authkey/tskey/password/secret regex)
- Reuse `_log_event` pattern

**REFINEMENT on `caller_endpoint`:**

PD's spec showed `caller_endpoint: "100.115.56.89:54321"` (a tailnet caller IP). But uvicorn's perspective is **127.0.0.1:NNNNN** (the nginx loopback proxy), NOT the original tailnet caller. Without nginx header propagation, telemetry would log loopback IP for every call.

**Verified live row 6 confirms** Beast's atlas-mcp nginx vhost ALREADY has `proxy_set_header X-Real-IP $remote_addr;` from Cycle 1G. This means uvicorn sees the original tailnet caller IP in the `X-Real-IP` header.

**Implementation requirement for Cycle 1H build:** server-side `_log_event` for `tool_call*` kinds extracts `caller_endpoint` from the FastMCP request's `X-Real-IP` header (or falls back to peer IP if header absent). Specifically:

```python
# Inside the @mcp.tool async function or via FastMCP middleware:
# X-Real-IP is set by nginx (Cycle 1G vhost: proxy_set_header X-Real-IP $remote_addr)
# FastMCP exposes it via the request context.

from mcp.server.fastmcp import Context

async def atlas_memory_upsert(params: MemoryUpsertInput, ctx: Context) -> str:
    caller_arg_keys = sorted(params.model_dump().keys())  # P6 #27 capture FIRST
    caller_endpoint = ctx.request_context.request.headers.get("X-Real-IP", "unknown")
    # ... ACL check, work, telemetry write with caller_endpoint ...
```

If FastMCP's Context doesn't expose request headers directly (PD verifies during build), fall back options:
- A: ASGI middleware extracts X-Real-IP and stashes in contextvar; `_log_event` reads contextvar
- B: log `caller_endpoint="loopback"` for v0.1 + bank as v0.2 P5 #25 (caller IP propagation hardening)

PD selects A vs B during build based on FastMCP capability; if B is chosen due to FastMCP API limitation, document in Cycle 1H paco_review.

### Ask 5 -- Authorize implementation handoff next turn

**RULING: AUTHORIZED.** Build directive dispatches in next `handoff_paco_to_pd.md` turn. Scope:

- 4 input classes (Pydantic BaseModel + Field validators per Ask 3)
- 4 @mcp.tool async functions with readOnlyHint/destructiveHint annotations
- Per-tool implementation modules (DB queries, embedding generation calls)
- `src/atlas/mcp_server/acl.py` (server-side ACL, mirror dataclass shape)
- Telemetry integration (mirror atlas.mcp_client `_log_event`; X-Real-IP for caller_endpoint per Ask 4 refinement)
- atlas-mcp.service restart at build close
- End-to-end smoke from CK (4 tools listed; sample tool invocation success per tool)
- atlas.events delta + secrets discipline audit (`source='atlas.mcp_server'` rows present; 0 hits on representative arg-value samples)
- Anchor PRE/POST diff bit-identical

### Ask 6 -- atlas.tasks.* deferral to Cycle 1I

**RULING: CONFIRMED.** Deferred. Cycle 1I will be a paco_request gate ratifying atlas.tasks state machine semantics (transition rules, owner authorization, completion semantics) BEFORE the build directive for tasks tools.

### Ask 7 -- v0.2 deferrals

**RULING: CONFIRMED on all three deferrals.**

- Per-tool rate-limiting -> v0.2 (no rate-limit infra in v0.1; tailnet membership is a soft authorization boundary)
- Auth-context propagation beyond tailnet -> v0.2 (caller_endpoint via X-Real-IP gives us per-IP attribution in v0.1 telemetry; bearer-token / OAuth integration is v0.2)
- Server-side observability dashboards -> v0.2 (atlas.events provides the data; dashboards are downstream visualization, not gating for v0.1 functionality)

### Ask 8 -- Bank v0.2 P5 candidates

**RULING: BANK BOTH + 1 NEW from Ask 4 refinement.**

- **v0.2 P5 #23 BANKED**: Extract `_log_event` pattern from atlas.mcp_client into shared `atlas.telemetry` utility module. Currently atlas.mcp_client has the canonical implementation; Cycle 1H atlas.mcp_server will REUSE the pattern by reimplementation; v0.2 hardening extracts to single module + both modules import it. Reduces duplication; centralizes secrets-discipline audit surface.
- **v0.2 P5 #24 BANKED**: Retroactive `atlas.events.source` allowlist enforcement at the schema layer. Current schema has `source text NOT NULL` (free-form); deny-list approach via ACL works for v0.1 but a CHECK constraint or PostgreSQL ENUM type would be more robust. v0.2 hardening adds: `ALTER TABLE atlas.events ADD CONSTRAINT events_source_check CHECK (source IN (...allowlist...))`.
- **v0.2 P5 #25 NEW (from Ask 4 refinement)**: caller IP propagation hardening if Cycle 1H build hits FastMCP Context API limitations and falls back to `caller_endpoint="loopback"`. v0.2 hardening either upgrades FastMCP, adds ASGI middleware, or contributes upstream PR for header access in Context.

v0.2 P5 backlog total: **25** (was 22; +1 #23 + 1 #24 + 1 #25).

## 3. CEO action item folded (Tailscale auth key residual)

v0.2 P5 #22 (auth key residual confirmation from Cycle 1G PO1) is non-blocking for Cycle 1H paco_request authoring per PD's Verified live row 14. **Folding here for resolution:**

CEO confirms via `https://login.tailscale.com/admin/settings/keys` within 24-72 hours whether the Cycle 1G auth key is consumed (one-time-use auto-exhausted at Beast tailnet join; expected default behavior) or revoked (manual action only if reusable was selected).

If consumed: nothing further; v0.2 P5 #22 closes as "verified consumed at Cycle 1G close + 24h".

If reusable: CEO revokes manually. v0.2 P5 #22 closes as "manually revoked".

PD captures CEO's confirmation (key fingerprint or status, NOT the key value) in the Cycle 1H paco_review's Verified live block as a closure row, OR as a separate one-line audit comment if CEO confirms after Cycle 1H close.

## 4. P6 banking

No new P6 lesson this turn. P6 #28 (reference-pattern verification before propagation) covers the spec error pattern that surfaced in Cycle 1H dispatch ("atlas.embeddings.*" / "atlas.inference.*" tool naming from memory). Back-to-back occurrence (Cycle 1G binding pattern + Cycle 1H tool naming) reinforces the rule rather than spawning a new lesson. Internalization burden is on me.

For Cycle 1H build close-out fold: append nothing new this turn; carry forward through Cycle 1H close.

## 5. Substrate state

B2b + Garage anchors held bit-identical 96+ hours through Cycles 1F + 1G + this paco_request authoring + my schema verification probes. Anchor preservation invariant: HOLDING. Cycle 1H build cycle must preserve through to close.

No substrate touched this paco_response. atlas-mcp.service still running 0-tool skeleton on 127.0.0.1:8001 loopback.

## 6. Counts post-ruling

- Standing rules: 5 (unchanged)
- P6 lessons banked: **28** (unchanged this turn; #28 already covers Cycle 1H spec error pattern)
- v0.2 P5 backlog: **25** (was 22; +1 #23 _log_event utility extraction; +1 #24 atlas.events.source allowlist enforcement; +1 #25 caller IP propagation hardening)
- Atlas Cycles SHIPPED: **7 of 9 in Cycle 1** (1A-1G closed; 1H ratifying scope this turn; 1I/tasks deferred)
- Atlas HEAD: `2f2c3b7` (unchanged from Cycle 1G close)
- control-plane-lab HEAD: `62860e5` (will advance with this paco_response commit)
- Cumulative findings caught at directive-authorship: 30 (unchanged this turn -- catch was at PD pre-execution review under 5-guardrail rule)
- Cumulative findings caught at PD pre-execution review: **3** (was 2; +1 this turn -- atlas.embeddings/inference tool naming caught BEFORE I authored a build directive based on it)
- Cumulative findings caught at PD execution failure: 2
- Total findings caught pre-failure-cascade across all Atlas v0.1 cycles: **35** (was 34; +1 this turn)
- Spec errors owned + corrected: **2** (Cycle 1G "matches CK's pattern" + Cycle 1H "atlas.embeddings.*" tool naming)
- Protocol slips caught + closed: 1

## 7. Cycle 1H build directive scope (preview)

The forthcoming `handoff_paco_to_pd.md` build directive will cover:

```
Step 1.  Anchor + state PRE
Step 2.  Author 4 input classes (Pydantic BaseModel + Field validators) in src/atlas/mcp_server/inputs.py OR co-located with each tool module
Step 3.  Author server-side ACL src/atlas/mcp_server/acl.py (mirror dataclass shape; v0.1 list may be minimal/empty; document authoritative posture)
Step 4.  Author per-tool implementation modules (events.py, memory.py, inference.py)
Step 5.  Wire 4 @mcp.tool async functions in server.py with readOnlyHint/destructiveHint annotations
Step 6.  Wire telemetry _log_event + X-Real-IP caller_endpoint extraction (via FastMCP Context if available, OR ASGI middleware fallback per Ask 4)
Step 7.  Restart atlas-mcp.service
Step 8.  Smoke test from CK tailnet member: tools_count=4 + sample invocation per tool (search returns rows; query returns vectors; upsert succeeds + atlas.events row appears with source=atlas.mcp_server; inference_history returns rows)
Step 9.  atlas.events delta + secrets discipline audit (source=atlas.mcp_server rows present; 0 hits on representative arg-value samples)
Step 10. Anchor POST + diff bit-identical
Step 11. Atlas commit + control-plane-lab close-out fold
Step 12. paco_review with Verified live + 5-gate scorecard for Cycle 1H
Step 13. Cleanup
```

Detailed step-by-step in next handoff. This preview is PD context only.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1h_tool_surface_ruling.md`

-- Paco
