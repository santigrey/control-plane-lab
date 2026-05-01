# Paco Review -- Atlas v0.1 Cycle 1I Close (atlas.tasks state machine)

**Filed by:** PD
**Date:** 2026-05-01 UTC (Day 77)
**Cycle:** 1I -- atlas.tasks state machine (6 tools; FINAL Cycle 1 cycle)
**Status:** **CLOSED 5/5 PASS.** Atlas commit `d383fe0` on santigrey/atlas. Atlas v0.1 Cycle 1 (1A through 1I) COMPLETE.

---

## Section 0 -- Verified live (5th standing rule)

18 verifications run live; all evidence below from this session.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | B2b anchor StartedAt PRE | `docker inspect` on Beast | `2026-04-27T00:13:57.800746541Z` healthy r=0 |
| 2 | Garage anchor StartedAt PRE | `docker inspect` on Beast | `2026-04-27T05:39:58.168067641Z` healthy r=0 |
| 3 | atlas.tasks PRE | psql on Beast | 0 rows |
| 4 | atlas.events PRE | psql on Beast | embeddings=12, inference=14, mcp_client=6, mcp_server=4 |
| 5 | atlas-mcp.service PRE | systemctl on Beast | active, MainPID 2042174 |
| 6 | atlas git PRE | git on Beast | `bfed019` clean tree |
| 7 | atlas.db API verified live (P6 #29) | grep + import-introspect | psycopg-style: `db.connection() -> conn -> cursor -> execute(sql, args) %s placeholders + await conn.commit()`. Paco sketch's `db.fetch(sql, $1)` was asyncpg-style; non-existent in atlas.db |
| 8 | All 4 module files AST OK | python ast.parse | inputs / errors / tasks / server |
| 9 | All 4 imports clean | python -c imports | OK; 10 tool functions registered |
| 10 | atlas-mcp.service POST-restart | systemctl on Beast | active, **MainPID 2111126** (rotated from 2042174) |
| 11 | Strict-loopback invariant | ss -tlnp on Beast | `127.0.0.1:8001` LISTEN python pid=2111126 |
| 12 | Smoke from Beast SDK | python script | INITIALIZE_OK + tools_count=10 + names match |
| 13 | Race-safety | concurrent gather | 3 successful claims + 2 null returns (queue exhausted) |
| 14 | caller_endpoint via X-Real-IP | live owner field | `100.121.109.112` (Tailscale, not loopback) |
| 15 | Round-trip success | claim+complete+get | status transitions verified |
| 16 | Round-trip fail | claim+fail+get | status=failed verified |
| 17 | All 3 AtlasTaskStateError kinds | live error responses + atlas.events `error_kind` | not_found + wrong_status + wrong_owner all captured |
| 18 | Anchors POST diff | docker inspect + diff | ANCHORS-BIT-IDENTICAL |
| 19 | atlas.events delta | psql post-tests | mcp_server=24 (was 4, +20); 21 tool_call + 3 tool_call_error |
| 20 | Secrets discipline audit | psql ~* regex | 0 hits on `authkey\|tskey\|password\|secret\|forced fail\|rt_success\|rt_fail\|wo_test\|race_test` |
| 21 | atlas.tasks state distribution | psql GROUP BY status | running=4, done=1, failed=1 |

Seventh in-session application of 5th standing rule.

---

## Section 1 -- TL;DR

**Atlas v0.1 Cycle 1 COMPLETE.** Cycle 1I CLOSED 5/5 PASS. 6 atlas.tasks tools shipped, completing the v0.1 inbound MCP surface (10 tools total: 4 Cycle 1H read/write + 6 Cycle 1I state machine).

State machine: 4 legal transitions (null->pending / pending->running with FOR UPDATE SKIP LOCKED / running->done / running->failed). Owner = caller_endpoint (X-Real-IP). Strict SQL-level owner-equality on complete/fail. AtlasTaskStateError disambiguates 0-row UPDATE outcomes into 4 kinds (not_found / wrong_status / wrong_owner / race), captured in atlas.events `error_kind` discriminator. P6 #29 applied: translated Paco's asyncpg-style sketch to actual atlas.db psycopg-style API. Substrate held bit-identical for ~96+ hours through 8 Atlas cycles + 2 service restarts.

---

## Section 2 -- Cycle 1I 5-gate scorecard

| # | Gate | Status | Evidence |
|---|---|---|---|
| 1 | tools_count=10 + names match | PASS | smoke: `['atlas_events_search', 'atlas_inference_history', 'atlas_memory_query', 'atlas_memory_upsert', 'atlas_tasks_claim', 'atlas_tasks_complete', 'atlas_tasks_create', 'atlas_tasks_fail', 'atlas_tasks_get', 'atlas_tasks_list']` |
| 2 | Round-trip SUCCESS path | PASS | create -> claim -> complete -> get verifies status=done; owner=100.121.109.112 |
| 3 | Round-trip FAIL path | PASS | create -> claim -> fail; status=failed; result jsonb populated |
| 4 | Race-safety + 3 disambiguation kinds | PASS | 3 pending + 5 concurrent claims = 3 success + 2 null; not_found + wrong_status + wrong_owner all error_kind discriminator captured |
| 5 | Anchors bit-identical + secrets discipline | PASS | ANCHORS-BIT-IDENTICAL + 0 hits on representative regex |

Plus 6 standing gates met:
- secret-grep on Atlas commit diff: clean
- B2b subscription `controlplane_sub`: untouched
- Garage cluster status: unchanged
- mcp_server.py on CK: untouched (Cycle 1I is Beast-side)
- atlas-mcp loopback :8001 bind preserved post-restart
- nginx vhost on Beast: untouched

---

## Section 3 -- Tool implementation summary (file inventory)

All under `/home/jes/atlas/src/atlas/mcp_server/`:

| File | Bytes | Status | Role |
|---|---|---|---|
| `inputs.py` | 8508 | EXTENDED (Cycle 1H + 1I) | 10 Pydantic input classes + 50KB jsonb caps + UUID validation + 4-status allowlist |
| `errors.py` | 1529 | NEW (Cycle 1I) | AtlasTaskStateError dataclass with `kind` discriminator + `to_dict()` |
| `tasks.py` | 9112 | NEW (Cycle 1I) | 6 async functions using actual atlas.db psycopg API |
| `server.py` | 12893 | EXTENDED (Cycle 1H + 1I) | 10 @mcp.tool wirings + `_wrap_tool` + `_wrap_tool_with_endpoint` |
| `acl.py` (unchanged) | 2477 | from Cycle 1H | server-side ACL infra (v0.1 patterns minimal) |
| `telemetry.py` (unchanged) | 1628 | from Cycle 1H | log_event module function source=atlas.mcp_server |
| `events.py` (unchanged) | 1593 | from Cycle 1H | search_events |
| `memory.py` (unchanged) | 3894 | from Cycle 1H | query_memory + upsert_memory |
| `inference.py` (unchanged) | 1817 | from Cycle 1H | history_inference |

Atlas commit: `d383fe0` (`bfed019..d383fe0`) -- 4 files changed (2 NEW + 2 MODIFIED), 644 insertions, 10 deletions.

---

## Section 4 -- Pydantic input classes (Cycle 1I additions)

6 classes, all `extra="forbid"` + `str_strip_whitespace=True`:

- **TasksCreateInput**: optional payload dict (Field validator: 50KB jsonb cap)
- **TasksListInput**: status (allowlist validator) + owner + created_after / created_before + limit (1-200, default 50)
- **TasksGetInput**: id (UUID required)
- **TasksClaimInput**: optional payload_kind (filter on payload->>'kind'); caller_endpoint NOT in input (derived from X-Real-IP)
- **TasksCompleteInput**: id + result (required dict, 50KB cap)
- **TasksFailInput**: id + result (required dict, 50KB cap; recommended convention {error_type, error_message, traceback})

Reusable `_jsonb_size_cap` factory shared across TasksCreate/Complete/Fail. TASK_STATUSES allowlist + MAX_PAYLOAD_BYTES + MAX_RESULT_BYTES module constants.

---

## Section 5 -- State machine summary

v0.1 implements 4 legal transitions:

| From | To | Tool | Pattern |
|---|---|---|---|
| `null` | `pending` | `atlas_tasks_create` | INSERT with status='pending', owner=NULL |
| `pending` | `running` | `atlas_tasks_claim` | UPDATE inside SELECT FOR UPDATE SKIP LOCKED subquery; owner=caller_endpoint |
| `running` | `done` | `atlas_tasks_complete` | UPDATE WHERE id=$ AND owner=$ AND status='running'; result jsonb required |
| `running` | `failed` | `atlas_tasks_fail` | UPDATE WHERE id=$ AND owner=$ AND status='running'; result jsonb required |

FOR UPDATE SKIP LOCKED race-safety verified: 3 pending + 5 concurrent claims = 3 success + 2 null returns.

All UPDATE statements include `updated_at = now()` explicitly (no DB trigger; v0.2 P5 #32 candidate).

**v0.1 owner-as-IP-string forward-compat:** documented in tasks.py module docstring + atlas_tasks_claim @mcp.tool description; v0.2 P5 #30 replaces with structured agent/user identity once auth-context propagation lands.

Deferred to v0.2 (per Paco's Cycle 1I ruling): cancel (pending->failed) + resurrect/retry (* -> pending) + free update_status + auth-context-beyond-tailnet + row-level visibility + DB updated_at trigger + structured FailureResult + worker heartbeat.

---

## Section 6 -- Telemetry contract carry-forward

No schema change. Source = `atlas.mcp_server` (unchanged from Cycle 1H). Existing 4 kinds (`tool_call` / `tool_call_denied` / `tool_call_error` / `tools_list`) cover Cycle 1I tools.

New payload field surfaced: `error_kind` discriminator on tool_call_error rows when AtlasTaskStateError raised. Verified live in atlas.events:

```
tool                  | error_kind   | count
atlas_tasks_complete | not_found    |     1
atlas_tasks_complete | wrong_owner  |     1
atlas_tasks_complete | wrong_status |     1
```

P6 #27 invariant: caller_arg_keys captured BEFORE Pydantic transformation (server-side full schema field names; carries forward from Cycle 1H decision).

Secrets discipline: 0 hits in audit. arg VALUES never persisted (smoke used kinds `race_test`, `rt_success`, `rt_fail`, `wo_test`, `forced fail` -- all 0 hits in atlas.events payloads).

---

## Section 7 -- Race-safety test results

```
CREATE 0: id=20c97fa1-... status=pending
CREATE 1: id=dfe62706-... status=pending
CREATE 2: id=3c3770c9-... status=pending

5 concurrent claims (asyncio.gather):
RACE successful_claims: 3 (expected 3)
RACE null_returns: 2 (expected 2)
RACE PASS
```

FOR UPDATE SKIP LOCKED pattern verified: each successful claim grabbed a different task; 2 racers found queue empty after 3 wins. No two claims got the same task. Owner correctly set to caller_endpoint=`100.121.109.112` on all 3 winners.

---

## Section 8 -- Round-trip test results

**SUCCESS path:**
```
created id=550d2c31-... status=pending
claimed id=550d2c31-... status=running owner=100.121.109.112
completed id=550d2c31-... status=done
verified via get: status=done
```

**FAIL path:**
```
created id=c32c6119-...
claimed status=running
failed id=c32c6119-... status=failed
```

Both paths: claim returns the same task that was just created (single-task queue); state transitions are atomic; tasks_get returns the post-transition state.

---

## Section 9 -- Disambiguation error test results

3 AtlasTaskStateError kinds verified end-to-end via MCP error responses:

```
not_found:    isError=True text="AtlasTaskStateError[not_found]: task does not exist (task_id=ce6c8205-...)"
wrong_status: isError=True text="AtlasTaskStateError[wrong_status]: task is in terminal/non-running state 'done'; cannot transition to 'done' (task_id=550d2c31-...)"
wrong_owner:  isError=True text="AtlasTaskStateError[wrong_owner]: task is owned by a different caller (task_id=bb39a201-...)"
```

For wrong_owner: SQL-level UPDATE injected `owner='192.0.2.99'` after claim to simulate ownership by a different caller. PD's caller_endpoint stayed `100.121.109.112` -> SQL-level WHERE owner=%s mismatch -> 0-row UPDATE -> disambiguation SELECT -> wrong_owner branch.

All 3 errors logged to atlas.events with `error_kind` discriminator (Section 6).

---

## Section 10 -- atlas.tasks state distribution post-smoke

```
status  | count
---------+-------
done    |     1
failed  |     1
running |     4
```

Total: 6 tasks. Reflects test outcomes:
- 3 from race test (claimed but not completed; still running)
- 1 round-trip success (now done)
- 1 round-trip fail (now failed)
- 1 wrong_owner test (claimed; SQL-overridden owner; never completable from current caller -> stays running)

No `pending` rows remaining -- all created tasks were claimed during testing.

The wrong_owner-stuck task is a v0.1 minor artifact (no `cancel` tool to free it; no `claim_timeout` to recover it). v0.2 P5 #34 (worker heartbeat / claim-timeout / dead-letter) covers recovery semantics.

---

## Section 11 -- Anchor preservation evidence

```
--- PRE (Step 1) ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- POST (Step 12) ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- diff ---
ANCHORS-BIT-IDENTICAL
```

B2b nanosecond anchor + Garage anchor held bit-identical for **~96+ hours** since Day 71 -- spanning H1 ship + Atlas Cycles 1A through 1I + multiple atlas-mcp.service restarts + ~24 tool calls + SQL-level direct UPDATE on atlas.tasks.owner during wrong_owner test.

---

## Section 12 -- Process observations

**P6 #29 applied (the canonical case it was banked for):** Paco's tasks.py skeleton used asyncpg-style `db.fetch(sql, $1, $2)`. Verified live before authoring: actual atlas.db.Database is psycopg-style with `async with db.connection() as conn: async with conn.cursor() as cur: await cur.execute(sql, args)` and `%s` placeholders. Translated all 6 SQL functions to actual API. Without this verification, the build would have failed at first import (db.fetch attribute not found).

**P6 #28 applied:** verified Cycle 1H acl.py / telemetry.py / inputs.py shapes before mirroring; confirmed psycopg pattern in Cycle 1H code (events.py / memory.py).

**P6 #27 invariant carries forward:** caller_arg_keys captured pre-Pydantic-transformation in `_wrap_tool_with_endpoint`; `["params"]` never appears in atlas.events.

**FastMCP error serialization:** AtlasTaskStateError raised inside the handler propagates to FastMCP, which returns a CallToolResult with `isError=True` and `content` containing the str representation. The `__str__` method on AtlasTaskStateError includes `[<kind>]` so callers can string-match for the discriminator. v0.2 P5 candidate: explicit ToolError wrapping for cleaner structured error response (current path works but parses str rather than structured fields).

**v0.2 P5 candidates surfaced this cycle:**
- (already banked #30) replace owner=IP with structured agent/user identity
- (already banked #32) DB-level updated_at trigger
- (already banked #33) structured FailureResult type
- (already banked #34) worker heartbeat / claim-timeout / dead-letter
- NEW: explicit MCP ToolError wrapping for AtlasTaskStateError so structured `kind` field reaches the client without str-parsing

**Atlas v0.1 Cycle 1 COMPLETE marker:** This commit closes Cycle 1I, the FINAL cycle of Atlas v0.1 Cycle 1. Atlas package now ships:
- 1A package skeleton
- 1B Postgres connection + atlas schema
- 1C Garage S3 client
- 1D Goliath inference RPC + telemetry
- 1E mxbai-embed-large embedding service
- 1F MCP client gateway + ACL + telemetry + auto-wrap
- 1G inbound MCP server skeleton (FastMCP loopback + Option A nginx Host rewrite + Tailscale FQDN cert)
- 1H atlas-mcp tool surface (4 read/write tools)
- 1I atlas.tasks state machine (6 tools)

Total: 10 tools live on `https://sloan2.tail1216a3.ts.net:8443/mcp`. Inflection point: Atlas v0.2 entry (Alexandra integration / capstone demo wiring) becomes the next phase.

---

## Section 13 -- Asks for Paco

1. **Confirm Cycle 1I 5/5 PASS** + ratify the close.
2. **Confirm Atlas v0.1 Cycle 1 COMPLETE** marker.
3. **Bank new v0.2 P5 candidate** (explicit MCP ToolError wrapping for AtlasTaskStateError structured `kind` field).
4. **Confirm Atlas v0.2 entry-point scope** -- Alexandra integration / capstone demo wiring per spec v3 inflection point.
5. **(Optional)** decide if the wrong_owner-stuck task in atlas.tasks should be cleaned up (DELETE row) or left as-is for the v0.2 P5 #34 worker heartbeat / dead-letter recovery semantics smoke test.
