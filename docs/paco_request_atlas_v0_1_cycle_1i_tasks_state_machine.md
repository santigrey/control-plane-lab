# Paco Request -- Atlas v0.1 Cycle 1I -- atlas.tasks.* state machine + tool surface

**Filed by:** PD
**Date:** 2026-05-01 UTC (Day 77)
**Predecessor:** `docs/handoff_paco_to_pd.md` at HEAD `808e0df` (Cycle 1I entry directive) + `docs/paco_response_atlas_v0_1_cycle_1h_close_confirm.md` (Cycle 1H ratification)
**Status:** PRE-implementation. Awaiting Paco rulings on scope + transitions + owner + completion. NO code lands this turn.

---

## Section 0 -- Verified live block (5th standing rule)

10 verifications run live; all evidence below from this session.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Atlas git HEAD | `git log --oneline -1` on Beast | `bfed019 feat: Cycle 1H atlas-mcp tool surface ...` (clean tree) |
| 2 | atlas.tasks schema | psql `\d atlas.tasks` on Beast | id uuid PK gen_random_uuid + status text NOT NULL + created_at timestamptz NOT NULL default now() + updated_at timestamptz NOT NULL default now() + owner nullable text + payload nullable jsonb + result nullable jsonb |
| 3 | atlas.tasks CHECK constraint | same | `tasks_status_check CHECK (status IN ('pending','running','done','failed'))` |
| 4 | atlas.tasks index | same | `tasks_status_created_idx btree (status, created_at)` (queue-shaped) |
| 5 | atlas.tasks current rows | psql GROUP BY status | **0 rows** (empty pre-1I) |
| 6 | atlas.tasks DB triggers | psql `information_schema.triggers` filter | **0 triggers** (app-level updated_at handling required) |
| 7 | Cycle 1H acl.py / telemetry.py / inputs.py | head on Beast | all present; mirror shape ready for reuse |
| 8 | CK mcp_server.py task pattern | grep on CK | targets `agent_tasks` (DIFFERENT table from atlas.tasks); P6 #28: argshape style transfers, schema does NOT |
| 9 | B2b + Garage anchors PRE | docker inspect on Beast | bit-identical w/ Day 71 (`2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`) |
| 10 | v0.2 P5 #22 (Tailscale auth key residual) | CEO confirmation in chat | RESOLVED -- key invalidated by 1-day expiration; no manual revocation needed |

---

## Section 1 -- TL;DR

atlas.tasks state machine is constrained at DB level to {pending, running, done, failed}. Cycle 1I ratifies the v0.1 tool surface + transition rules + owner-field semantics + completion semantics.

**PD recommendation: Option B (Standard) -- 6 tools:**
- `atlas_tasks_create` (WRITE; creates pending row, owner=NULL)
- `atlas_tasks_list` (READ; filter by status / owner / created_at range)
- `atlas_tasks_get` (READ; single task by id)
- `atlas_tasks_claim` (WRITE; pending->running, atomic SKIP LOCKED race-safety, owner=caller_endpoint)
- `atlas_tasks_complete` (WRITE; running->done, owner-equality required, result jsonb required)
- `atlas_tasks_fail` (WRITE; running->failed, owner-equality required, result jsonb required)

Deferred to v0.2: cancel, resurrect/retry, auth-context beyond X-Real-IP, rate limiting, scheduling. Substrate untouched. atlas-mcp.service restart at build close (mirroring Cycle 1H).

---

## Section 2 -- atlas.tasks schema invariants (informational)

Non-negotiable; Cycle 1I tool design works WITHIN these constraints:

```sql
CREATE TABLE atlas.tasks (
  id          uuid        NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
  status      text        NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  owner       text,
  payload     jsonb,
  result      jsonb,
  CONSTRAINT  tasks_status_check
    CHECK (status IN ('pending','running','done','failed'))
);
CREATE INDEX tasks_status_created_idx ON atlas.tasks (status, created_at);
```

Observations:
- `id` is server-generated; never user-supplied
- `status` CHECK enforces 4-state invariant at DB level (defense-in-depth alongside app state machine)
- `created_at` + `updated_at` default to `now()`; NOT NULL
- **NO database trigger for updated_at** (verified live row 6) -- app-level handling required: every UPDATE must set `updated_at = now()` explicitly
- `owner` is nullable text -- semantics ratified in Section 5
- `payload` (input) and `result` (output) both nullable jsonb -- size caps in Section 6
- Index on `(status, created_at)` is queue-shaped -- the schema EXPECTS claim/complete/fail workflow

---

## Section 3 -- Tool surface options

### Option A -- Minimum Viable (read + create only; 3 tools)

Tools: `atlas_tasks_create`, `atlas_tasks_list`, `atlas_tasks_get`

Rationale: simplest scope; no state-transition complexity; tasks are write-once-then-read records

Drawback: no claim/complete/fail; state machine effectively unused; queue-shaped index sits idle; tasks become inert records (just fancy event log). Index designed for queue workload would be vestigial.

### Option B -- Standard (queue-style; 6 tools) -- PD RECOMMENDED

Tools: Option A + `atlas_tasks_claim` (pending->running) + `atlas_tasks_complete` (running->done) + `atlas_tasks_fail` (running->failed)

Rationale: full task-queue semantics; matches schema design intent (queue-shaped index); state machine actually used; mirrors typical job-runner patterns. Forward-compat for future workers (Atlas as Head of Operations needs queue semantics for scheduled work).

Drawback: more ACL surface (caller authorization for claim/complete/fail); SQL-level race-safety design needed for claim.

### Option C -- Full (Standard + cancel + free update_status; 8 tools)

Tools: Option B + `atlas_tasks_cancel` (pending->failed by anyone-or-owner) + `atlas_tasks_update_status` (any free transition)

Rationale: maximum flexibility

Drawback: free `update_status` UNDERMINES state machine discipline; better to ship narrow transition tools that each enforce a specific rule than a single tool that bypasses them. Cancel adds value but introduces v0.1 authorization questions (who can cancel? owner only after claim? anyone before claim?) that are better deferred.

### PD Recommendation: Option B (Standard)

Reasons:
1. Schema design intent matches Option B (queue-shaped index + state machine CHECK constraint)
2. Atlas as Head of Operations needs claim/complete/fail for any scheduled work
3. cancel/resurrect adds authorization complexity better answered at v0.2 with auth-context
4. Option C's free `update_status` is anti-pattern -- specific transition tools enforce rules; free tool sidesteps them

---

## Section 4 -- State transition rules (PD-proposed)

Legal v0.1 transitions:

| From | To | Tool | Authorization | Idempotency |
|---|---|---|---|---|
| `null` | `pending` | atlas_tasks_create | any tailnet member | each call creates new row (always succeeds; never duplicate) |
| `pending` | `running` | atlas_tasks_claim | any tailnet member; sets owner=caller_endpoint | atomic SKIP LOCKED; if no pending row matches filter, returns null |
| `running` | `done` | atlas_tasks_complete | strict owner-equality (caller_endpoint == row.owner) | already-done/failed: ERROR (caller is authoritative; no silent no-op) |
| `running` | `failed` | atlas_tasks_fail | strict owner-equality | already-done/failed: ERROR |

NOT in v0.1 scope:
- `pending -> failed` (cancel before claim) -- defer to v0.2 (authorization complexity: caller-derived from X-Real-IP doesn't answer "who created this task" without storing creator separately)
- `* -> pending` (resurrect/retry) -- defer to v0.2 (idempotency complexity: should this clear owner? Reset created_at? Increment retry count?)
- `done <-> failed` (mistake-correction) -- defer to v0.2 (terminal states should stay terminal at v0.1)

### Race-safety on claim

Claim must be atomic. Standard Postgres pattern:

```sql
UPDATE atlas.tasks
SET status = 'running',
    owner  = %s,
    updated_at = now()
WHERE id = (
  SELECT id FROM atlas.tasks
  WHERE status = 'pending'
  -- + optional caller-supplied filters: e.g. payload->>'kind' = %s
  ORDER BY created_at
  LIMIT 1
  FOR UPDATE SKIP LOCKED
)
RETURNING id, status, owner, payload, created_at, updated_at;
```

This pattern:
- locks one pending row at a time (`FOR UPDATE SKIP LOCKED`)
- skips rows already locked by other workers (no blocking; concurrent workers each get a different task)
- atomically transitions pending -> running with owner set
- returns the claimed row OR no row (caller knows queue was empty)

### Idempotency rule for terminal-state actions

If caller invokes complete/fail on a row that's NOT in `running` state (or not owned by caller), the SQL update returns 0 rows. Handler raises a structured error: `{"error": "task not found in claimable state for this caller", "task_id": ..., "current_status": ...}`.

Rationale: complete/fail are state-changing assertions; silent no-op would mask caller bugs. Better to fail loud.

---

## Section 5 -- Owner field semantics + authorization

### On create

- `owner = NULL` (creator is not necessarily the worker; create is a queue-enqueue operation)
- caller_endpoint is captured in atlas.events telemetry (not in tasks.owner)

### On claim

- `owner = caller_endpoint` (X-Real-IP from nginx; matches Cycle 1H telemetry pattern)
- v0.1 trust boundary: tailnet membership IS the authentication. caller_endpoint values are tailnet IPs (verified live in Cycle 1H: `100.121.109.112`)
- v0.2 P5: introduce auth-context propagation (e.g., bearer token, agent identity); tasks.owner becomes a structured identifier (e.g., `"agent:atlas"` or `"user:sloan"`) instead of raw IP

### On complete/fail

- SQL-level enforcement: `WHERE id = %s AND owner = %s AND status = 'running'`
- Strict equality on owner (no impersonation; v0.1 ACL boundary is tailnet membership + IP equality)
- 0 rows returned -> handler raises error (see idempotency rule, Section 4)

### On list / get (READ tools)

- No owner restriction; any tailnet member can list/get any task at v0.1
- v0.2 P5: row-level visibility (e.g., "only see tasks I own" or "only see tasks created by me")

---

## Section 6 -- Completion semantics

### result jsonb on done

- Caller-supplied; arbitrary jsonb shape
- Pydantic Field validator: max 50KB serialized (10x Cycle 1H memory metadata cap; tasks may carry larger results)
- No required schema; convention encouraged via tool description (e.g., `{"output": "...", "summary": "..."}`)

### result jsonb on failed

- Caller-supplied; recommended convention `{"error_type": "...", "error_message": "...", "traceback": "..."}`
- Same 50KB cap
- Not enforced as required schema at v0.1 (Pydantic-validated dict is sufficient)
- v0.2 P5 candidate: ratify a structured FailureResult type (TypedDict / nested Pydantic model) once we observe how callers actually use it

### updated_at handling

- App-level: every UPDATE statement sets `updated_at = now()` explicitly
- NO database trigger (verified live row 6)
- All UPDATE statements in v0.1 tool implementations must include `updated_at = now()` in the SET clause
- v0.2 P5 candidate: install a DB-level BEFORE UPDATE trigger to reduce app-side responsibility (defensive)

### created_at

- Default `now()` at INSERT (DB-level)
- App never sets created_at
- Useful for queue ordering (`ORDER BY created_at` in claim)

---

## Section 7 -- Argshape + telemetry contract

### Argshape: Path X (Pydantic-wrapped) -- mirror Cycle 1H ratification

All 6 tools accept a single `params: <ToolInput>` Pydantic class with `extra="forbid"` + `str_strip_whitespace=True`. Field-level validators carry per-tool allow-list constraints.

Proposed input classes:

```python
class TasksCreateInput(BaseModel):
    payload: Optional[dict] = Field(default=None, description="Task payload")
    # Optional payload size cap via Field validator (mirror Cycle 1H metadata 10KB pattern; tasks payload cap = 50KB)

class TasksListInput(BaseModel):
    status: Optional[str] = Field(default=None, max_length=20)  # validator: in {pending, running, done, failed}
    owner: Optional[str] = Field(default=None, max_length=200)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=200)

class TasksGetInput(BaseModel):
    id: UUID = Field(...)

class TasksClaimInput(BaseModel):
    payload_kind: Optional[str] = Field(default=None, max_length=50)  # optional filter on payload->>'kind'
    # caller_endpoint NOT in this input -- always derived from X-Real-IP via Context

class TasksCompleteInput(BaseModel):
    id: UUID = Field(...)
    result: dict = Field(..., description="Required result jsonb on success")
    # Pydantic validator: serialized result <= 50KB

class TasksFailInput(BaseModel):
    id: UUID = Field(...)
    result: dict = Field(..., description="Required failure result (recommended: error_type, error_message)")
    # Pydantic validator: serialized result <= 50KB
```

### Telemetry contract

- **source = `atlas.mcp_server`** (existing Cycle 1H source; no expansion)
- **kinds**: existing `tool_call` / `tool_call_denied` / `tool_call_error` cover all 6 tools without expansion
- **payload fields**: tool_name + arg_keys + status + duration_ms + caller_endpoint (existing schema)
- **caller_endpoint**: from X-Real-IP via Cycle 1G nginx propagation (verified live in Cycle 1H -- 100.121.109.112)

P6 #27 invariant: arg_keys captured pre-internal-transform; auto-wrap layer invisible. (Server-side captures post-Pydantic full schema field names per Cycle 1H decision; carries forward.)

---

## Section 8 -- Substrate impact + scope boundary

### What this cycle touches

- `/home/jes/atlas/src/atlas/mcp_server/` -- adds tasks module + extends server.py with 6 new @mcp.tool wirings
- Pydantic input classes added to inputs.py (extending existing 4)
- atlas-mcp.service requires restart at build close (mirroring Cycle 1H Step 6)

### What this cycle does NOT touch

- Postgres anchor: substrate Docker container untouched
- Garage anchor: untouched
- Schema migrations: NONE (atlas.tasks schema unchanged; existing schema covers all options)
- nginx vhost on Beast: unchanged (Cycle 1G config carries forward)
- mcp_server.py on CK: unrelated to this cycle
- atlas.mcp_client: untouched
- atlas.events / atlas.embeddings / atlas.inference / atlas.memory schemas: unchanged

### OUT of scope this paco_request (deferred to v0.2 or later)

- Implementation code (waits for build handoff)
- `atlas_tasks_cancel` (pending -> failed)
- `atlas_tasks_resurrect` / `atlas_tasks_retry` (* -> pending)
- Free `atlas_tasks_update_status` (any transition)
- Auth-context propagation beyond X-Real-IP / tailnet membership (v0.2)
- Per-tool rate-limiting (v0.2 P5)
- Server-side observability dashboards (v0.2)
- Task scheduling / cron-style triggers
- Task dependencies / DAG semantics
- Worker heartbeat / claim-timeout / dead-letter handling (v0.2 if claim/complete loop in production reveals need)

---

## Section 9 -- Asks for Paco

1. **Ratify scope** -- Option A / Option B (PD-recommended) / Option C / amend?
2. **Ratify state-transition rules** (Section 4):
   - 4 transitions only (create / claim / complete / fail), all others deferred?
   - Atomic SKIP LOCKED claim pattern accepted?
   - Idempotency rule: terminal-state action -> error (not silent no-op) accepted?
3. **Ratify owner field semantics** (Section 5):
   - owner = NULL on create, caller_endpoint on claim, strict SQL-level equality on complete/fail?
   - v0.1 trust boundary = tailnet membership + IP equality (no row-level visibility filtering on list/get)?
4. **Ratify completion semantics** (Section 6):
   - result jsonb required on done + failed; 50KB cap; v0.1 unstructured (recommended convention only)?
   - app-level updated_at = now() in every UPDATE; v0.2 P5 candidate to add DB trigger?
5. **Confirm argshape Path X + telemetry contract** carries forward unchanged from Cycle 1H?
6. **Authorize implementation handoff next turn** with this scope?
7. **Bank v0.2 P5 candidates surfaced** this cycle:
   - Cancel + Resurrect tools (pending -> failed and * -> pending)
   - Auth-context propagation (replace caller_endpoint as owner with structured agent/user identity)
   - Row-level visibility on list/get
   - DB-level updated_at trigger
   - Structured FailureResult type ratification
   - Worker heartbeat / claim-timeout / dead-letter handling
   - (Pending Paco decision: are these the right v0.2 P5 entries?)

No close-out fold this turn. PD has discharged Steps 1-2 of Cycle 1I entry directive.
