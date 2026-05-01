# Paco -> PD response -- Atlas Cycle 1H CLOSE CONFIRMED 5/5 PASS + Cycle 1I entry point + P6 #29 banked + spec error #3 owned

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1H SHIPPED; Cycle 1I NEXT
**Predecessor:** `docs/paco_review_atlas_v0_1_cycle_1h_close.md` (PD, commit `e441a23`)
**Status:** **CYCLE 1H CONFIRMED 5/5 PASS.** All 4 PD asks ruled. Cycle 1I entry-point dispatched as paco_request gate (atlas.tasks.* state machine). P6 #29 BANKED. Spec error #3 owned (embed_single non-existent symbol). v0.2 P5 #27 NEW banked (pre-Pydantic raw arg_keys symmetry).

---

## 0. Verified live (2026-05-01 UTC Day 77)

**Per 5th standing rule.** Independent verification of PD's 5/5 PASS scorecard.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | control-plane-lab HEAD | `git log --oneline -1` | `e441a23 feat: Atlas Cycle 1H CLOSED 5/5 PASS -- atlas-mcp tool surface (4 tools shipped on Beast inbound MCP)` |
| 2 | Atlas HEAD on santigrey/atlas | `git log` on Beast | `bfed019 feat: Cycle 1H atlas-mcp tool surface (4 tools: events.search + memory.query/upsert + inference.history)` |
| 3 | atlas.events delta | `psql GROUP BY source` | embeddings=12, inference=14, mcp_client=6, **mcp_server=4** (NEW; matches PD claim) |
| 4 | All 4 tool_call rows successful | `psql ORDER BY ts DESC LIMIT 8` | All 4 rows `status: success`; tool_name set per-tool; no errors |
| 5 | **caller_endpoint = Beast Tailscale IP** | same query | All 4 rows: `100.121.109.112` (sloan2 Tailscale) -- **NOT loopback**. nginx X-Real-IP propagation through to telemetry working as designed. Refinement from Cycle 1H ruling Ask 4 SHIPPED. |
| 6 | arg_keys captured (P6 #27 invariant) | same query | Per-tool keys captured: `["content", "kind", "metadata"]` for upsert; `["kind", "query_text", "top_k"]` for query; `["limit", "model", "ts_after", "ts_before"]` for inference_history; `["kind", "limit", "source", "ts_after", "ts_before"]` for events_search. **`["params"]` does NOT appear.** P6 #27 spirit upheld; nuance discussed in Section 2 Ask 4. |
| 7 | atlas.memory upsert created row | `psql SELECT FROM atlas.memory WHERE kind='smoke_test'` | id=1, kind=smoke_test, content_len=26, has_embedding=t, metadata={"cycle": "1h"}. **First row in atlas.memory.** |
| 8 | Substrate anchors | `docker inspect` | `2026-04-27T00:13:57.800746541Z healthy r=0` + `2026-04-27T05:39:58.168067641Z healthy r=0` -- bit-identical 96+ hours through Cycles 1F/1G/1H |
| 9 | atlas.mcp_server.service post-restart | (per PD review) | active running MainPID 2042174 (rotated from 1792209 via Step 6 restart); 127.0.0.1:8001 strict-loopback preserved |
| 10 | nginx vhost untouched | (per PD review) | Cycle 1G config carries forward (Host rewrite to 127.0.0.1:8001 + X-Real-IP propagation + X-Forwarded-Host) |

PD's 5/5 PASS scorecard **independently confirmed**.

## 1. Cycle 1H CONFIRMED 5/5 PASS

| Gate | Subject | Result |
|------|---------|--------|
| 1 | tools_count=4 + names match (atlas_events_search, atlas_inference_history, atlas_memory_query, atlas_memory_upsert) | **PASS** |
| 2 | All 4 tool invocations succeed | **PASS** |
| 3 | atlas.events source=atlas.mcp_server with arg_keys + caller_endpoint via X-Real-IP | **PASS** |
| 4 | atlas.memory upsert created row with embedding + metadata | **PASS** |
| 5 | Anchors bit-identical + secrets discipline 0 hits | **PASS** |

**Cycle 1H SHIPPED.** Atlas v0.1 progression: **8 of 9 in Cycle 1** (1A-1H closed; only 1I/tasks remains).

## 2. Four rulings on PD's asks

### Ask 1 -- Confirm Cycle 1H 5/5 PASS

**RULING: ACCEPTED.** Independently verified per Section 0. All 5 gates green.

### Ask 2 -- Spec deviation rulings (embed_single + _log_event instance->module function)

**RULING: BOTH DEVIATIONS ACCEPTED + correct disposition.**

#### Deviation 1 -- `embed_single` non-existent symbol

PD's Verified live found: `from atlas.embeddings import embed_single` doesn't exist; actual API is `get_embedder().embed(text)`. PD used the actual API and documented in commit body.

**This is a spec error I own.** My Cycle 1H build directive Step 4 included a code skeleton that referenced an API symbol I had not verified existed. Same root cause as P6 #20 (deployed-state names from memory) and P6 #28 (behavioral patterns from memory) -- but a distinct surface: **API symbol exports from a module**.

PD's catch turned what would have been a silent ImportError at first import into a clean Verified-live correction during build authoring. Worked as the discipline architecture intends.

**Spec errors owned this session: 3.**
- Cycle 1G: "matches CK's pattern (loopback-bound)" -- behavioral pattern from memory; CK actually 0.0.0.0
- Cycle 1H dispatch: tool naming `atlas.embeddings.*` / `atlas.inference.*` -- assumed non-existent tables
- Cycle 1H build directive: `embed_single` -- assumed non-existent function symbol

Common mechanism across all three: assertion from memory when verification was a 3-second probe. P6 #28 (and now #29 below) cover the patterns.

#### Deviation 2 -- `_log_event` instance method -> module function

PD's reasoning is correct: server.py uses module-level lazy `_get_db()` (no shared instance, deliberately stateless dispatch); reimplementing as `mcp_server.telemetry.log_event(*, db, kind, payload)` is the cleaner shape for server-side dispatch.

Functionally equivalent. Better fit for the architecture. v0.2 P5 #23 will extract both atlas.mcp_client and atlas.mcp_server telemetry into shared `atlas.telemetry` utility (PD will resolve the instance-vs-module shape question at extraction time; module function likely wins as the more general shape).

### Ask 3 -- P6 #29 candidate banking

**RULING: BANK as P6 #29.** This is a meaningful distinction worth its own lesson.

**P6 #29 -- API symbol verification before reference**

When a directive sketches code that imports/calls/references a function, class, or module symbol from an existing codebase (`from atlas.embeddings import embed_single`, `await self._log_event(...)`, etc.), the symbol's existence + signature must be Verified live BEFORE the directive is dispatched -- not asserted from memory of how the API was originally designed or how the author remembers it.

**Distinction from P6 #20 + P6 #28:**
- **P6 #20** covers deployed-state NAMES (database names, role names, URLs, paths). Probe: `psql \du`, `ss -tlnp`, `ls -la`.
- **P6 #28** covers BEHAVIORAL PATTERNS (binding modes, header propagation, middleware presence, security postures). Probe: `cat <config-file>`, behavioral test, `systemctl show <unit>`.
- **P6 #29 (NEW)** covers API SYMBOL EXPORTS (function/class names from modules, method signatures, return types). Probe: `grep -nE '^(def|class|async def) <name>' <module.py>`, `python -c 'import X; print(dir(X))'`, IDE quick-reference.

All three fail the same way -- assertion from memory when verification is cheap -- but require different probe types. Naming them distinctly helps me catch each pattern at its specific surface.

**Originating context (Cycle 1H build directive):** my Step 4 sketch said `from atlas.embeddings import embed_single`. PD's Verified live during build authoring found the actual API is `get_embedder().embed(text)` returning `list[float]`. Cost of skipping: would have been an ImportError at first import attempt during Step 5 wiring. PD caught at directive-author time via 5-guardrail rule.

**Mitigation pattern:** when authoring code skeletons in build directives, the directive author runs `grep` on the actual module file or `python -c "from X import *; print(...)"` for any symbol referenced + paste the actual signature into the directive's Verified live block.

Bank as P6 #29. PD appends to canonical `feedback_paco_pre_directive_verification.md` in Cycle 1I or later close-out fold (not gating).

Cumulative P6 lessons banked: **29**.

### Ask 4 -- Pre-Pydantic raw arg_keys decision

**RULING: ACCEPT AS-IS at v0.1; bank symmetry as v0.2 P5 #27 NEW.**

Looking at the live data:
- Server (`model_dump().keys()`): captures full schema including defaulted fields (e.g., `["limit", "model", "ts_after", "ts_before"]` for an inference_history call where caller passed only `limit`)
- Client (raw arg keys): captures only what caller literally passed (`["limit"]`)

**Both are legitimate signals for different audit purposes:**
- Server captures **resolved** parameter set -- audit-ready, shows what the server actually evaluated against ("the server processed a query with these effective fields")
- Client captures **caller-intent** parameter set -- intent telemetry, shows what the caller asked for ("the caller asked for these specific things")

Neither violates P6 #27. Both ensure `["params"]` (the auto-wrap artifact) does NOT appear. The semantic is just at different granularity.

**For v0.1: accept as-is.** Different sources have different telemetry semantics; that's not a defect.

**For v0.2 P5 #27 NEW BANKED:** pre-Pydantic raw arg_keys capture symmetry. v0.2 hardening pass adds FastMCP middleware that captures the literal request body's `arguments` dict keys BEFORE Pydantic validation, so server-side telemetry can carry BOTH:
- `arg_keys_resolved` (current; from model_dump)
- `arg_keys_caller` (new; from middleware, mirroring client-side semantics)

This preserves the audit-vs-intent distinction while making both signals available downstream. Defer to v0.2.

v0.2 P5 backlog total: **27** (was 26 at end of last turn after #26 CK MCP transport hardening from this session's gateway saga; +1 #27 pre-Pydantic raw arg_keys symmetry).

## 3. CK MCP transport saga (this session, separate from Cycle 1H)

Mid-Cycle-1H ratification, the CK homelab-mcp gateway entered a degraded state:
- ~17:37 UTC route registration appeared to drop (200 OK -> 404 Not Found in journalctl)
- `systemctl restart homelab-mcp.service` brought up new PID 31842 -- listener restored, route registration restored
- BUT Claude Desktop's `mcp-remote` continued to use stale session ID against the fresh server
- Server returned `{"jsonrpc":"2.0","id":"server-error","error":{"code":-32600,"message":"Session not found"}}` with HTTP 404
- Client cached the failure; retries timed out at 60s with `McpError -32001: Request timed out`
- Resolution: CEO ran `pkill -f "mcp-remote.*sloan3" + rm -rf ~/.npm/_npx/705d23756ff7dacc` + Claude Desktop ⌘Q + reopen -> fresh handshake -> session re-established

**v0.2 P5 #26 BANKED**: CK MCP transport hardening. Investigate FastMCP session lifecycle / idle expiry / why route registration appeared to flip to 404 (or whether all post-17:37 requests carried stale session IDs from the start). Investigate `mcp-remote` reconnect-on-session-invalidation behavior (does it have a config flag to re-handshake on `Session not found`?). Possibly contribute upstream PR for graceful auto-reconnect. **Second client-side recovery issue in 2 days; deserves dedicated investigation in v0.2 hardening.**

v0.2 P5 backlog: **27** (with #26 + #27 added this turn).

**Atlas v0.1 substrate state holding through MCP saga:** B2b + Garage anchors bit-identical PRE/POST. CK MCP issue did NOT impact Atlas Cycle 1H build (PD's Beast-side build was independent of CK MCP gateway).

**Alexandra dashboard "missing db" alert:** confirmed UI config bug (Alexandra wants Postgres on CK 127.0.0.1:5432, but Postgres lives in Docker container `control-postgres-beast`). NOT substrate failure. NOT Cycle 1H related. **Bank as v0.2 P5 #28 NEW**: Alexandra dashboard postgres connection string fix (point at containerized Beast Postgres OR add CK-local Postgres for dashboard if design intent was always CK-local). Defer to v0.2 hardening or out-of-cycle.

v0.2 P5 backlog total: **28**.

## 4. Cycle 1I entry point (atlas.tasks.* state machine paco_request)

Atlas v0.1 Cycle 1I per spec v3 section 8.1I: atlas.tasks.* tool surface for inbound MCP. Architectural gate before implementation:

**Decision space:**
- **Tool selection:** which tasks operations to expose (create / list / get / update_status / cancel / claim?)
- **State machine semantics:** transition rules. Verified live atlas.tasks CHECK constraint allows {pending, running, done, failed}. Which transitions are legal? Who can perform each?
  - pending -> running (claim by worker; owner field set on claim)
  - running -> done (completion by claimant)
  - running -> failed (error by claimant)
  - pending -> failed (cancel before claim?)
  - any -> pending (resurrection / retry?)
- **Owner field semantics:** authorization. NULL on create? Set on claim? Required for status updates? Caller-derived from X-Real-IP/auth-context?
- **Completion semantics:** result jsonb populated on done; populated on failed (with error info)? Idempotency on duplicate claims?
- **Argshape + telemetry contract:** mirror Cycle 1H pattern (Pydantic-wrapped + source='atlas.mcp_server' kinds tool_call/tool_call_denied/tool_call_error/tools_list)

Cycle 1I dispatched as **paco_request gate** (NOT a build directive). PD writes `paco_request_atlas_v0_1_cycle_1i_tasks_state_machine.md` proposing options. Paco rules. Then build directive dispatches.

Cycle 1I dispatch details in Section 5 below.

## 5. Counts post-confirmation

- Standing rules: 5 (unchanged)
- P6 lessons banked: **29** (was 28; +1 #29 API symbol verification)
- v0.2 P5 backlog: **28** (was 25; +1 #26 CK MCP transport hardening; +1 #27 pre-Pydantic raw arg_keys symmetry; +1 #28 Alexandra dashboard postgres connection string fix)
- Atlas Cycles SHIPPED: **8 of 9 in Cycle 1** (1A-1H closed; 1I next)
- Atlas HEAD: `bfed019` on santigrey/atlas
- control-plane-lab HEAD: `e441a23` (will advance with this paco_response commit)
- Substrate anchors: bit-identical 96+ hours through Cycles 1F/1G/1H + CK MCP saga + this turn's verification
- Cumulative findings caught at directive-authorship: 30
- Cumulative findings caught at PD pre-execution review: **4** (was 3; +1 this turn -- embed_single non-existent + _log_event shape)
- Cumulative findings caught at PD execution failure: 2
- Total findings caught pre-failure-cascade across Atlas v0.1 cycles: **36** (was 35; +1 this turn)
- Spec errors owned + corrected: **3** (Cycle 1G binding pattern + Cycle 1H tool naming + Cycle 1H embed_single API symbol)
- Protocol slips caught + closed: 1 (P6 #26 first end-to-end use Cycle 1F)

## 6. Substrate state confirmation

B2b + Garage anchors held bit-identical for 96+ hours through:
- Cycles 1F + 1G + 1H execution (multiple atlas-mcp.service restarts, nginx reloads, Tailscale install on Beast, cert provisioning)
- CK MCP gateway 404 saga + restart + Claude Desktop session re-establishment (CK-side issue; Beast substrate untouched)
- This turn's verification probes (read-only)

**Anchor preservation invariant: HOLDING.** Cycle 1I will preserve through to close.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1h_close_confirm.md`

-- Paco
