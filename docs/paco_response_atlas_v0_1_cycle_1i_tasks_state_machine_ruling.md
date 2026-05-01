# Paco -> PD response -- Atlas Cycle 1I tasks state machine: ALL 7 ASKS RATIFIED

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1I -- atlas.tasks state machine + tool surface
**Predecessor:** `docs/paco_request_atlas_v0_1_cycle_1i_tasks_state_machine.md` (PD, commit `f02d5c5`)
**Status:** **ALL 7 ASKS RATIFIED.** Build directive dispatches in next handoff turn. Three refinements on error shape + ownership documentation + Pydantic size validator pattern. Seven v0.2 P5 candidates banked + 1 NEW from this turn's verification (DNS intermittency).

---

## 0. Verified live (2026-05-01 UTC Day 77)

**Per 5th standing rule.** Independent verification of PD's critical schema findings + triggers.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | HEAD on control-plane-lab | `git log --oneline -1` | `f02d5c5 cycle-1i entry: atlas.tasks state machine paco_request gate (PRE-implementation)` (matches PD's PRE-state) |
| 2 | atlas.tasks schema | `psql \d atlas.tasks` | id uuid PK gen_random_uuid + status text NOT NULL + created_at timestamptz NOT NULL DEFAULT now() + updated_at timestamptz NOT NULL DEFAULT now() + owner nullable text + payload jsonb + result jsonb. Confirms PD finding row 2. |
| 3 | CHECK constraint | `psql \d atlas.tasks` | `tasks_status_check CHECK (status = ANY (ARRAY['pending','running','done','failed']))` -- confirms PD row 3 |
| 4 | Index | `psql \d atlas.tasks` | `tasks_status_created_idx btree (status, created_at)` -- queue-shaped; confirms PD row 4 |
| 5 | **0 DB triggers on atlas.tasks** | `information_schema.triggers WHERE event_object_table='tasks'` | **0 rows** -- confirms PD row 6. App-level updated_at handling is correct architectural choice. |
| 6 | atlas.tasks current rows | `SELECT count(*) FROM atlas.tasks` | **0** -- clean slate; confirms PD row 5 |
| 7 | Substrate anchors | `docker inspect` | `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` -- bit-identical 96+ hours through Cycles 1F + 1G + 1H + 1I authoring window |
| 8 | Atlas package HEAD | `git log --oneline -1` on Beast | `bfed019` (Cycle 1H clean tree); confirms PD row 1 |
| 9 | DNS resolution `beast` from CK shell (NEW finding) | `ssh beast 'date'` from CK | `ssh: Could not resolve hostname beast: Temporary failure in name resolution` -- intermittent; happened twice this session (also surfaced in Cycle 1H close-confirm verification turn). Bank as v0.2 P5 #35 NEW; non-blocking (direct host calls work fine). |

PD's analysis verified accurate. Schema + design space well-grounded.

## 1. Why all 7 asks ratify cleanly

PD's paco_request is unusually well-grounded for Cycle 1I. Three things that earn the ratification:

1. **Schema invariants honored.** Every design decision (FOR UPDATE SKIP LOCKED, app-level updated_at, owner=NULL on create, strict SQL equality on terminal transitions) works WITHIN the constraints atlas.tasks already enforces at the DB level. No fights with the schema.

2. **Pattern symmetry with Cycle 1H.** Argshape Path X (Pydantic-wrapped), telemetry source `atlas.mcp_server` reusing existing kinds, X-Real-IP for caller_endpoint -- all carry forward without expansion. Less new surface = less risk.

3. **Honest scope discipline.** PD identified 7 v0.2 P5 candidates (cancel/resurrect/auth-context/row-visibility/DB-trigger/FailureResult/heartbeat) that COULD have been bundled into v0.1 if Option C were chosen. By recommending Option B and surfacing those explicitly as deferred, PD keeps Cycle 1I narrow + ships the queue-shaped state machine cleanly.

No P6 #28 or #29 surfacing this turn -- PD verified live every reference (schema, triggers, CK pattern) and explicitly noted in row 8 that CK targets a DIFFERENT table (`agent_tasks`) so argshape style transfers but schema does NOT. Direct application of the lesson.

## 2. Seven rulings

### Ask 1 -- Scope: Option B (Standard, 6 tools)

**RULING: RATIFIED.** Tools shipped in Cycle 1I build:

| Tool | Direction | Backing | readOnlyHint | destructiveHint |
|------|-----------|---------|--------------|-----------------|
| `atlas_tasks_create` | WRITE | INSERT INTO atlas.tasks (status='pending', owner=NULL) | False | False |
| `atlas_tasks_list` | READ | SELECT FROM atlas.tasks WHERE filters | True | False |
| `atlas_tasks_get` | READ | SELECT FROM atlas.tasks WHERE id=$1 | True | False |
| `atlas_tasks_claim` | WRITE | UPDATE atlas.tasks ... FOR UPDATE SKIP LOCKED (pending->running) | False | False |
| `atlas_tasks_complete` | WRITE | UPDATE atlas.tasks ... WHERE owner=$1 (running->done) | False | False |
| `atlas_tasks_fail` | WRITE | UPDATE atlas.tasks ... WHERE owner=$1 (running->failed) | False | False |

Reject Option A (3 tools) -- queue-shaped index would sit vestigial; tasks become inert records. Reject Option C -- free `atlas_tasks_update_status` is anti-pattern; specific transition tools each enforce their rule.

Tool naming convention: snake_case (matches Cycle 1H + CK).

Total atlas-mcp tool surface post-Cycle-1I: **10 tools** (4 from Cycle 1H + 6 from Cycle 1I).

### Ask 2 -- State transition rules

**RULING: RATIFIED with one refinement on error shape.**

Four transitions, all PD's design correct:

| From | To | Tool | Authorization | Idempotency |
|------|----|------|---------------|-------------|
| `null` | `pending` | atlas_tasks_create | tailnet member | new row each call |
| `pending` | `running` | atlas_tasks_claim | tailnet member; sets owner=caller_endpoint | atomic SKIP LOCKED; null return on empty queue |
| `running` | `done` | atlas_tasks_complete | strict owner-equality | terminal-state action -> ERROR (loud failure) |
| `running` | `failed` | atlas_tasks_fail | strict owner-equality | terminal-state action -> ERROR (loud failure) |

**FOR UPDATE SKIP LOCKED claim pattern: RATIFIED.** PD's SQL is correct. This is the canonical Postgres pattern for race-safe queue claim; well-tested in production systems; FastMCP async dispatch + Postgres MVCC handles concurrent workers correctly.

**Idempotency rule (terminal-state -> error, no silent no-op): RATIFIED.** Loud failure protects callers from masking bugs. "Already done/failed" is a different signal from "task not found" or "wrong owner" and callers should be able to distinguish.

**REFINEMENT -- error shape (NEW this ruling):**

When complete/fail's UPDATE returns 0 rows, the cause matters for caller debugging. Three distinct causes:
1. Task ID not found at all
2. Task exists but wrong status (already done/failed)
3. Task exists, in running status, but owner mismatch (caller is not the claimant)

A generic "task not found in claimable state" error masks all three. Better:

**Implementation pattern:** when 0 rows returned, the handler runs ONE additional SELECT to disambiguate:

```python
async def complete_task(params: TasksCompleteInput, db: Database, caller_endpoint: str) -> dict:
    rows = await db.execute(
        "UPDATE atlas.tasks SET status='done', result=$1, updated_at=now() "
        "WHERE id=$2 AND owner=$3 AND status='running' "
        "RETURNING id, status, owner, updated_at",
        json.dumps(params.result, default=str), params.id, caller_endpoint,
    )
    if rows:
        return rows[0]
    # Disambiguate the 0-row outcome
    row = await db.fetchone("SELECT id, status, owner FROM atlas.tasks WHERE id=$1", params.id)
    if row is None:
        raise AtlasTaskStateError(
            kind="not_found", task_id=str(params.id),
            message="task does not exist",
        )
    if row["status"] != "running":
        raise AtlasTaskStateError(
            kind="wrong_status", task_id=str(params.id),
            current_status=row["status"], expected_status="running",
            message=f"task is in terminal state '{row['status']}'; cannot complete",
        )
    if row["owner"] != caller_endpoint:
        raise AtlasTaskStateError(
            kind="wrong_owner", task_id=str(params.id),
            actual_owner=row["owner"], caller_endpoint=caller_endpoint,
            message="task is owned by a different caller",
        )
    # Race condition: row changed between UPDATE and SELECT (extremely rare)
    raise AtlasTaskStateError(
        kind="race", task_id=str(params.id),
        message="transient race; retry the call",
    )
```

New file: `src/atlas/mcp_server/errors.py` (or fold into `acl.py` -- PD chooses; bias toward separate `errors.py` for clarity).

The disambiguation SELECT is one extra round-trip per failure (failures are infrequent in correct-caller patterns). Worth it for debuggability. AtlasTaskStateError serializes to MCP error response with kind discriminator the caller can branch on.

### Ask 3 -- Owner field semantics

**RULING: RATIFIED with explicit forward-compat documentation.**

PD's design correct:
- create: `owner = NULL` (create is enqueue, not assignment)
- claim: `owner = caller_endpoint` (X-Real-IP via FastMCP Context, mirrors Cycle 1H telemetry)
- complete/fail: SQL-level `WHERE owner = $caller_endpoint` strict equality
- list/get: no owner restriction at v0.1

**FORWARD-COMPAT DOCUMENTATION REQUIREMENT:**

The v0.1 owner-as-IP-string design IS a v0.1 stage. v0.2 will replace caller_endpoint with structured agent/user identity (e.g., `"agent:atlas"`, `"user:sloan"`, possibly bearer-token-derived). Document this explicitly in:
- `src/atlas/mcp_server/tasks.py` module docstring
- Each transition tool's @mcp.tool description
- Cycle 1I paco_review Section 5 (owner semantics)

This prevents future readers from coupling to the IP-as-owner shape as if it were canonical. Banked as v0.2 P5 #30 (auth-context propagation).

### Ask 4 -- Completion semantics

**RULING: RATIFIED with Pydantic size validator pattern carrying forward from Cycle 1H.**

- result jsonb required on done + failed: ratified. Both transitions provide caller-supplied result.
- 50KB cap (10x Cycle 1H metadata 10KB cap): ratified. Tasks may carry larger payloads; 50KB is reasonable while still being bounded.
- v0.1 unstructured: ratified. Recommended convention via tool description docstring. v0.2 P5 #33 will ratify structured FailureResult once we observe usage patterns.
- App-level `updated_at = now()` in every UPDATE: ratified. v0.2 P5 #32 will install DB trigger as defensive backstop.

**Pattern requirement -- Pydantic Field validator (mirror Cycle 1H):**

```python
class TasksCompleteInput(BaseModel):
    id: UUID = Field(...)
    result: dict = Field(..., description="Required result jsonb on success (max 50KB serialized)")

    @field_validator("result")
    @classmethod
    def result_size_cap(cls, v: dict) -> dict:
        import json
        if len(json.dumps(v, default=str)) > 50_000:
            raise ValueError("result serialized form exceeds 50KB cap")
        return v
```

Mirror exactly for `TasksFailInput.result`. Same `default=str` JSON serialization (matches Cycle 1H telemetry pattern).

### Ask 5 -- Argshape Path X + telemetry contract carry forward

**RULING: CONFIRMED unchanged.**

- **Argshape:** Path X (Pydantic-wrapped, mirror Cycle 1H + CK). Every tool: `async def atlas_tasks_X(params: SomeInput, ctx: Context) -> str`
- **Telemetry source:** `atlas.mcp_server` (no expansion)
- **Telemetry kinds:** existing 4 (tool_call / tool_call_denied / tool_call_error / tools_list) cover all 6 new tools
- **caller_endpoint:** X-Real-IP via Cycle 1G nginx propagation; `_extract_caller_endpoint(ctx)` helper from Cycle 1H carries forward
- **P6 #27 invariant:** caller_arg_keys captured BEFORE Pydantic transformation in `_wrap_tool` helper (already in Cycle 1H server.py)

The `_wrap_tool` helper from Cycle 1H needs ONE small extension: claim/complete/fail handlers need access to `caller_endpoint` as a function argument (for owner SQL filter), not just for telemetry. PD wires this in build directive.

### Ask 6 -- Authorize implementation handoff next turn

**RULING: AUTHORIZED.** Build directive dispatches in next `handoff_paco_to_pd.md` turn. Scope:

- 6 input classes (Pydantic BaseModel + Field validators per Section 7 of paco_request)
- 6 @mcp.tool async functions with annotations
- Per-tool implementation in `src/atlas/mcp_server/tasks.py` (NEW module; co-locate the 6 transition functions for clarity)
- `src/atlas/mcp_server/errors.py` NEW (AtlasTaskStateError + disambiguation pattern)
- Extend `src/atlas/mcp_server/server.py` with 6 new @mcp.tool wirings + `_wrap_tool` extension to pass caller_endpoint to handler body
- Extend `src/atlas/mcp_server/inputs.py` with TasksCreateInput / TasksListInput / TasksGetInput / TasksClaimInput / TasksCompleteInput / TasksFailInput
- atlas-mcp.service restart at build close
- End-to-end smoke from CK tailnet member: tools_count=10 (4 + 6); claim race-safety test; state machine round-trip test (create -> claim -> complete + create -> claim -> fail + ERROR cases)
- atlas.events delta + secrets discipline audit
- atlas.tasks state verification (rows present in expected statuses post-smoke)
- Anchor PRE/POST diff bit-identical

### Ask 7 -- Bank v0.2 P5 candidates

**RULING: BANK ALL 7 PD-surfaced + 1 NEW from this turn's verification.**

v0.2 P5 #29 NEW: `atlas_tasks_cancel` (pending -> failed) + `atlas_tasks_resurrect` (terminal -> pending). Authorization complexity warrants explicit ratification: who can cancel? owner only after claim? creator before claim? Resurrect idempotency: clear owner? reset created_at? track retry count?

v0.2 P5 #30 NEW: auth-context propagation. Replace caller_endpoint-as-owner with structured agent/user identity (e.g., `"agent:atlas"`, `"user:sloan"`, bearer-token-derived). Document migration path from v0.1 IP-string owner.

v0.2 P5 #31 NEW: row-level visibility filters on list/get. v0.1: any tailnet member sees all tasks. v0.2: optional filtering modes (e.g., "only my tasks", "only tasks I created", "public/private flag").

v0.2 P5 #32 NEW: DB-level BEFORE UPDATE trigger for `updated_at = now()`. Defensive backstop alongside app-level handling. Belt-and-suspenders.

v0.2 P5 #33 NEW: structured FailureResult type ratification. Once we observe how callers actually populate result on failed status, ratify a TypedDict / nested Pydantic model (e.g., `{error_type, error_message, traceback, retry_after}`).

v0.2 P5 #34 NEW: worker heartbeat / claim-timeout / dead-letter handling. If claim+complete/fail loop in production reveals stuck-running tasks (claimed but never completed), add heartbeat or claim-timeout pattern to release tasks back to pending after timeout.

v0.2 P5 #35 NEW (from Section 0 row 9 verification): DNS resolution intermittency for `beast` hostname from CK shell. Happened multiple times this session (`ssh: Could not resolve hostname beast: Temporary failure in name resolution`). Direct homelab_ssh_run host calls work fine. Investigate `/etc/hosts` on CK, DNS resolver config, or whether SSH alias config in `~/.ssh/config` should explicitly use the Tailscale IP. Non-blocking but affects PD's future ssh-from-CK-to-Beast operations.

v0.2 P5 backlog total: **35** (was 28; +7 this turn: #29-#35).

## 3. Future inflection point worth flagging

Cycle 1I closes Atlas v0.1. With 10 atlas-mcp tools live + queue-shaped task state machine + bit-identical substrate anchors at 96+ hours, **Atlas v0.1 is portfolio-grade**.

The natural next phase post-Cycle-1I:
- **Atlas v0.2 entry:** Alexandra integration. Sloan's capstone demo path. Hook Alexandra dashboard to atlas-mcp tools (replace the broken 127.0.0.1:5432 connection with proper atlas-mcp.* tool calls; bonus: fixes v0.2 P5 #28 alongside).
- **Job-search portfolio crystallization:** Cycle 1I close ships a complete demonstrable artifact (homelab AI platform with strict-loopback security, X-Real-IP-attributed telemetry, layered ACL, vector memory, queue-shaped tasks, inbound + outbound MCP). Worth a portfolio writeup + demo video.

Not a Cycle 1I scope item -- just flagging the inflection. Address after Cycle 1I close.

## 4. P6 banking

No new P6 lesson this turn. PD's paco_request applied #28 (verified live CK pattern + explicitly noted DIFFERENT schema in row 8) and #29 (no API symbol assertions; all references checked) cleanly. Discipline architecture working.

For Cycle 1I build close-out fold: append nothing new; carry forward through Cycle 1I close.

## 5. Substrate state

B2b + Garage anchors held bit-identical 96+ hours through Cycles 1F + 1G + 1H + 1I authoring + my schema verification probes. Anchor preservation invariant: HOLDING. Cycle 1I build cycle must preserve through to close.

No substrate touched this paco_response. atlas-mcp.service still running 4-tool Cycle 1H code on 127.0.0.1:8001 loopback.

## 6. Counts post-ruling

- Standing rules: 5 (unchanged)
- P6 lessons banked: **29** (unchanged this turn)
- v0.2 P5 backlog: **35** (was 28; +7 this turn: #29 cancel/resurrect, #30 auth-context, #31 row-visibility, #32 DB updated_at trigger, #33 FailureResult, #34 heartbeat/timeout, #35 DNS intermittency)
- Atlas Cycles SHIPPED: **8 of 9 in Cycle 1** (1A-1H closed; 1I ratifying scope this turn; FINAL CYCLE NEXT BUILD)
- Atlas HEAD: `bfed019` (unchanged from Cycle 1H close)
- control-plane-lab HEAD: `f02d5c5` (will advance with this paco_response commit)
- Cumulative findings caught at directive-authorship: 30
- Cumulative findings caught at PD pre-execution review: 4
- Cumulative findings caught at PD execution failure: 2
- Total findings caught pre-failure-cascade: 36
- Spec errors owned + corrected: 3
- Protocol slips caught + closed: 1

## 7. Cycle 1I build directive scope (preview)

Forthcoming `handoff_paco_to_pd.md` build directive will cover ~14 steps:

```
Step 1.  Anchor + state PRE
Step 2.  Author 6 input classes + size validators in src/atlas/mcp_server/inputs.py (extend existing 4)
Step 3.  Author src/atlas/mcp_server/errors.py NEW (AtlasTaskStateError + disambiguation pattern)
Step 4.  Author src/atlas/mcp_server/tasks.py NEW (6 transition functions: create/list/get/claim/complete/fail)
Step 5.  Extend src/atlas/mcp_server/server.py:
         - 6 new @mcp.tool wirings with readOnlyHint/destructiveHint
         - _wrap_tool helper extension to pass caller_endpoint to handler body
Step 6.  Restart atlas-mcp.service
Step 7.  Validate import + service active
Step 8.  Smoke test from CK: tools_count=10
Step 9.  Race-safety claim test (concurrent claim attempts)
Step 10. State machine round-trip test (create->claim->complete + create->claim->fail)
Step 11. ERROR cases test (terminal-state action; wrong owner; not found)
Step 12. atlas.events delta + secrets discipline audit
Step 13. atlas.tasks state verification
Step 14. Anchor POST diff + Atlas commit + control-plane-lab fold + paco_review + cleanup
```

Detailed step-by-step in next handoff. This preview is PD context only.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1i_tasks_state_machine_ruling.md`

-- Paco
