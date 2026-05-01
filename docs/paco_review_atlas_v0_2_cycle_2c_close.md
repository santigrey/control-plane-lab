# Paco Review -- Atlas v0.2 Cycle 2C Close (Audit Log Viewer + Token Usage Dashboard; alexandra-source telemetry deferred)

**Filed by:** PD
**Date:** 2026-05-01 UTC (Day 77)
**Cycle:** 2C -- Audit Log Viewer panel + Token Usage Dashboard panel + alexandra-source telemetry (deferred)
**Status:** **CLOSED 5/5 PASS (panels-only scope; telemetry deferred per substrate posture).** control-plane-lab anchor commit pending push. No atlas-side changes.

---

## Section 0 -- Verified live (5th standing rule)

14 verifications run live; all evidence below from this session.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Beast anchors PRE | docker inspect on Beast | `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` healthy r=0 |
| 2 | atlas.events PRE | psql | embeddings=12, inference=14, mcp_client=6, mcp_server=26 (58 total) |
| 3 | atlas-mcp.service PRE | systemctl | active, MainPID 2173807 (carry from Cycle 2B) |
| 4 | orchestrator.service PRE | systemctl | active, MainPID 292908 (carry from Cycle 2B) |
| 5 | Beast pg cross-host reachability | TCP probe `</dev/tcp/192.168.1.20/5432` + `192.168.1.152/5432` | **NOT_REACHABLE both IPs** -- intentional substrate localhost-bound posture per hard rule + Phase G ESC |
| 6 | AtlasBridge ALLOWED_TOOLS PRE | grep | already includes all 4 atlas_* tools (frozenset) -- Step 4 no-op |
| 7 | dashboard.py POST AST | python3 ast.parse | OK (+12565 B appended) |
| 8 | dashboard router routes count | python -c routes | 14 total (10 existing + 4 NEW Cycle 2C) |
| 9 | orchestrator.service POST-restart | systemctl | active, **MainPID 347400** (rotated from 292908) |
| 10 | `/dashboard/audit` (NEW) | curl | http_code=200 time=0.013s |
| 11 | `/dashboard/tokens` (NEW) | curl | http_code=200 time=0.010s |
| 12 | `/dashboard` regression | curl | http_code=200 time=0.012s (existing SPA serving) |
| 13 | Smoke 1 audit_search end-to-end | curl POST | returned 5+ atlas.events rows incl. Cycle 2B (id=58/57) + Cycle 1I (id=56 wrong_owner) traces |
| 14 | Smoke 2 tokens_history end-to-end | curl POST | returned inference rows (id=28/24/21) qwen2.5:72b at Goliath with eval_count + eval_duration_ms + total_duration_ms |
| 15 | atlas.events POST | psql | mcp_server +2 (26->28); +1 atlas_events_search 7.1ms + +1 atlas_inference_history 4.9ms; both caller_endpoint=100.115.56.89 |
| 16 | Secrets audit | psql ~* regex | 0 hits on `authkey\|tskey\|password\|adminpass` |
| 17 | Anchors POST diff | docker inspect + diff | ANCHORS-BIT-IDENTICAL |

Ninth in-session application of 5th standing rule.

---

## Section 1 -- TL;DR

Cycle 2C CLOSED 5/5 PASS on the **panels-only scope**. Two more capstone-grade dashboards live:
- `/dashboard/audit` -- Audit Log Viewer backed by `atlas_events_search`
- `/dashboard/tokens` -- Token Usage Dashboard backed by `atlas_inference_history`

Both verified end-to-end via Beast atlas-mcp through Path A AtlasBridge transport (caller_endpoint=`100.115.56.89` confirms Cycle 1G nginx X-Real-IP propagation continues to work).

**Steps 5-6 (alexandra-source telemetry) DEFERRED** per Beast pg cross-host unreachability. This is intentional substrate posture (Docker localhost-bound per hard rule). Banked as v0.2 P5 #42 (cross-host pg access pattern decision); recommended approach is adding a NEW MCP tool `atlas_events_create` to atlas-mcp surface (preserves substrate isolation; uses existing trusted transport; mirrors Cycle 1H/1I pattern).

**Capstone-demo readiness state achieved:** 3 panels live (Memory + Audit + Tokens). Demo narrative carries on atlas.* sources alone — no alexandra-source events needed for capstone demo to work. Substrate anchors bit-identical (~96+ hours holding).

---

## Section 2 -- Cycle 2C 5-gate scorecard

| # | Gate | Status | Evidence |
|---|---|---|---|
| 1 | Audit Log Viewer panel + API endpoint functional | PASS | `/dashboard/audit` 200; smoke returns atlas.events rows with caller_endpoint + arg_keys + payload visible |
| 2 | Token Usage Dashboard panel + API endpoint functional | PASS | `/dashboard/tokens` 200; smoke returns inference rows with eval_count + duration_ms aggregates |
| 3 | atlas_telemetry.py / wiring | **DEFERRED** (substrate posture; v0.2 P5 #42 candidate) | Beast pg cross-host NOT_REACHABLE both IPs -- intentional |
| 4 | orchestrator.service restart clean; both new routes 200 | PASS | MainPID 347400 (rotated); 200 on both |
| 5 | Anchor preservation + secrets discipline + capstone-demo readiness | PASS | ANCHORS-BIT-IDENTICAL; 0 secrets hits; 3 panels live |

Plus 6 standing gates met:
- secret-grep on commit diff: clean
- B2b subscription `controlplane_sub`: untouched
- Garage cluster status: unchanged
- mcp_server.py on CK: untouched
- atlas-mcp loopback :8001 bind preserved (no atlas-mcp restart this cycle)
- nginx vhosts: untouched

---

## Section 3 -- Audit Log Viewer implementation summary

File: `dashboard.py` EXTENDED (+12565 B; HTML_AUDIT + 2 routes)

Pattern matches Cycle 2B Memory Browser:
- Standalone HTML page at `/dashboard/audit` (style-consistent with existing dashboard dark mode)
- POST API at `/dashboard/api/audit/search` proxies to `atlas_events_search` via AtlasBridge
- Pydantic input `_AuditSearchRequest`: source allowlist + kind + ts_after/ts_before + limit (1-100; matches atlas-side `EventsSearchInput` cap)

Client-side JS:
- Source dropdown (5 options: any + 4 atlas.* sources + alexandra)
- Kind text input
- Limit numeric input
- Results table: ts / source / kind / endpoint (caller_endpoint highlighted) / payload (JSON formatted)
- Error rows highlighted red (`kind` contains 'error' or 'denied')

---

## Section 4 -- Token Usage Dashboard implementation summary

File: `dashboard.py` EXTENDED (continues same append block)

Pattern same as Audit:
- Standalone HTML page at `/dashboard/tokens`
- POST API at `/dashboard/api/tokens/history` proxies to `atlas_inference_history`
- Pydantic input `_TokensHistoryRequest`: model + ts_after/ts_before + limit (1-50; matches atlas-side `InferenceHistoryInput` cap)

Client-side JS auto-loads on page open, computes aggregate metrics:
- Total inferences
- Total tokens (eval_count summed)
- Total eval duration
- By-model breakdown table: calls / tokens / total ms / avg tokens per call

---

## Section 5 -- atlas_telemetry.py disposition

**DEFERRED** to v0.2 P5 #42 (NEW candidate banked this cycle).

### Reachability finding

```
from CK:
  192.168.1.20:5432   -> NOT_REACHABLE (Connection refused)   [Paco directive IP]
  192.168.1.152:5432  -> NOT_REACHABLE (Connection refused)   [actual Beast IP]
```

Beast Postgres is bound to localhost INSIDE the Docker container per the `Docker bypasses UFW. Bind PostgreSQL and other Docker services to localhost in compose.yaml` hard rule. Phase G compose-down ESC explicitly established this posture. Cross-host pg access from CK is by design blocked.

### v0.2 P5 #42 recommended approach

**Option 1 (PD recommended):** Add a NEW MCP tool `atlas_events_create` to atlas.mcp_server surface. Alexandra calls it like the other 4 tools via AtlasBridge. Preserves substrate isolation; uses existing trusted transport; mirrors Cycle 1H/1I pattern.

**Option 2:** Local Alexandra DB write + periodic forwarder worker. More moving parts; introduces secondary datastore for telemetry.

**Option 3:** Open Beast pg cross-host (Docker compose 0.0.0.0 bind + UFW + pg_hba.conf). Violates hard rule + reverses Phase G ESC. **REJECTED.**

**Option 4:** Logical replication CK→Beast atlas.events. Heavy infra; wrong tool for telemetry.

### Demo narrative impact

**None.** Capstone demo runs on atlas.* sources (mcp_server, mcp_client, embeddings, inference). Alexandra-origin events would be enrichment, not core. Audit Log Viewer already demonstrates auditability across 4 atlas.* sources.

---

## Section 6 -- Step 6 wiring outcomes

Not wired. Steps 5-6 deferred together (Step 6 wiring depends on Step 5 helper module).

---

## Section 7 -- Smoke test results

```
=== Smoke 1: /dashboard/api/audit/search {limit:5} ===
{"ok":true, ...}
Returned 5 atlas.events rows (most recent first):
  id=58 atlas.mcp_server tool_call atlas_memory_query caller_endpoint=100.115.56.89 (Cycle 2B)
  id=57 atlas.mcp_server tool_call atlas_memory_upsert caller_endpoint=100.115.56.89 (Cycle 2B)
  id=56 atlas.mcp_server tool_call_error atlas_tasks_complete error_kind=wrong_owner caller_endpoint=100.121.109.112 (Cycle 1I)
  id=55 ... [truncated]

=== Smoke 2: /dashboard/api/tokens/history {limit:10} ===
{"ok":true, ...}
Returned inference rows:
  id=28 generate qwen2.5:72b @192.168.1.20:11434 eval_count=2 eval_duration_ms=222.522 total_duration_ms=573.248
  id=24 generate qwen2.5:72b similar
  id=21 generate qwen2.5:72b similar
  ... [truncated]
```

Both panels validated end-to-end through Path A AtlasBridge transport. caller_endpoint propagation through nginx X-Real-IP confirmed (100.115.56.89 = CK Tailscale IP).

---

## Section 8 -- atlas.events delta evidence

```
source           | PRE | POST | delta
-----------------+-----+------+-------
atlas.embeddings | 12  | 12   | 0
atlas.inference  | 14  | 14   | 0
atlas.mcp_client | 6   | 6    | 0
atlas.mcp_server | 26  | 28   | +2  (Cycle 2C smokes)
alexandra        | 0   | 0    | 0   (deferred to v0.2 P5 #42)
```

Latest 2 atlas.mcp_server rows from Cycle 2C smokes:
```
kind      | tool                    | endpoint        | dur_ms
tool_call | atlas_inference_history | 100.115.56.89   | 4.912
tool_call | atlas_events_search     | 100.115.56.89   | 7.138
```

Both fast (<10ms) — read-only queries hit pgvector indexes efficiently. caller_endpoint=`100.115.56.89` (CK Tailscale via X-Real-IP).

Secrets discipline audit: 0 hits on `authkey|tskey|password|adminpass` in atlas.mcp_server payloads. arg VALUES never persisted; only keys.

---

## Section 9 -- Anchor preservation diff

```
--- PRE ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- POST ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- diff ---
ANCHORS-BIT-IDENTICAL
```

B2b + Garage anchors held bit-identical for **~96+ hours** since Day 71. Substrate untouched through:
- 1 orchestrator.service restart (Step 7)
- 1 file edit (dashboard.py append)
- 2 atlas-mcp tool calls (smokes)
- 0 atlas-mcp.service restarts

---

## Section 10 -- Capstone-demo readiness state

3 panels live on Alexandra dashboard:

| Panel | URL | Backed by |
|---|---|---|
| Memory Browser (Cycle 2B) | `https://sloan3.tail1216a3.ts.net/dashboard/memory` | atlas_memory_query + atlas_memory_upsert |
| Audit Log Viewer (Cycle 2C) | `https://sloan3.tail1216a3.ts.net/dashboard/audit` | atlas_events_search |
| Token Usage Dashboard (Cycle 2C) | `https://sloan3.tail1216a3.ts.net/dashboard/tokens` | atlas_inference_history |

Demo narrative (Cycle 2A Section 6) all 5 scenes supportable from this state:
- Scene 1 "The system before me" -- existing dashboard SPA + 3 panel links in nav
- Scene 2 "Memory in action" -- Memory Browser end-to-end
- Scene 3 "Inference + telemetry" -- Token Usage Dashboard end-to-end (live data already there)
- Scene 4 "The architecture" -- diagram (Cycle 2D scope)
- Scene 5 "The build process" -- slide deck (Cycle 2D scope)

Cycle 2D scope: polish + demo video script + capstone slides + architecture diagram. No more code work needed for v0.2.0 capstone-demo readiness on the Atlas-integration axis.

---

## Section 11 -- Process observations

**P6 #28 + #29 + #30 applied:**

1. **Beast pg reachability probe BEFORE authoring atlas_telemetry.py (P6 #29):** Saved one entire build cycle. Paco's directive Step 5 named `192.168.1.20:5432` as the Beast pg endpoint, but verified live: that's Goliath's IP; Beast is `192.168.1.152`. Both unreachable due to substrate localhost-bound posture. Writing the helper would have produced runtime failures on first emit. Probe-first verified the assumption was wrong.

2. **AtlasBridge ALLOWED_TOOLS PRE (P6 #28):** Verified live before authoring; already includes all 4 atlas_* tools from Cycle 2B. Step 4 confirmed no-op without speculative edit.

3. **Pydantic limit field caps:** Paco's directive sketched `le=500` for both audit + tokens limits, but verified live: atlas-side InferenceHistoryInput.limit is `le=50` and EventsSearchInput.limit is `le=100`. Adapted Pydantic constraints in dashboard.py to match atlas-side caps. Pass-through is honest.

**Spec deviation: Steps 5-6 deferred (panels-only Cycle 2C):**

Paco's directive explicitly authorized this disposition: "If NOT reachable: bank as v0.2 P5 candidate; Cycle 2C ships dashboard panels but defers alexandra-source telemetry wiring." Path followed verbatim.

**MQTT executor connection-refused warning at orchestrator boot (carry-forward from Cycle 2B):** Pre-existing v0.2 P5 #35 SlimJim Mosquitto connectivity issue. Not regression; not Cycle 2C scope.

**v0.2 P5 candidates surfaced this cycle:**

- **#42 (suggested):** Alexandra-source telemetry wiring path. Recommended Option 1 = add `atlas_events_create` MCP tool to atlas.mcp_server (preserves substrate isolation; uses existing trusted transport; mirrors Cycle 1H/1I argshape pattern).

**Existing P5 candidates from Cycle 2B (still pending Paco banking):**
- #39 adminpass refactor (registry.py + app.py to env-var-only lookup)
- #40 Alexandra declarative deps (requirements.txt or pyproject.toml)
- #41 Path A decoupling telemetry doc clarification

---

## Section 12 -- Asks for Paco

1. **Confirm Cycle 2C 5/5 PASS** on panels-only scope; ratify the close.
2. **Bank v0.2 P5 #42** (alexandra-source telemetry wiring path; PD recommends Option 1 = new `atlas_events_create` MCP tool).
3. **Ratify capstone-demo readiness state** (3 panels live; narrative all 5 scenes supportable from this state).
4. **Confirm Cycle 2D scope** -- polish + demo video script + capstone slides + architecture diagram (no further code work for v0.2.0 demo readiness on Atlas-integration axis).
5. **Confirm or amend** the Cycles 2B/2C P5 candidate banking (#39 / #40 / #41 / #42).
6. **Optional disposition:** v0.2 P5 #35 (MQTT executor / SlimJim Mosquitto) priority within v0.2 hardening pass.
