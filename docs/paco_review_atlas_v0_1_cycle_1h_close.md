# Paco Review -- Atlas v0.1 Cycle 1H Close (atlas-mcp tool surface)

**Filed by:** PD
**Date:** 2026-05-01 UTC (Day 77)
**Cycle:** 1H -- atlas-mcp tool surface (4 tools)
**Status:** **CLOSED 5/5 PASS.** Atlas commit `bfed019` on santigrey/atlas. All standing gates met.

---

## Section 0 -- Verified live (5th standing rule)

14 verifications run live; all evidence below from this session.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | B2b anchor StartedAt PRE | `docker inspect` on Beast | `2026-04-27T00:13:57.800746541Z` healthy r=0 |
| 2 | Garage anchor StartedAt PRE | `docker inspect` on Beast | `2026-04-27T05:39:58.168067641Z` healthy r=0 |
| 3 | atlas.events PRE | psql on Beast | embeddings=12, inference=14, mcp_client=6, no atlas.mcp_server |
| 4 | atlas-mcp.service PRE | systemctl on Beast | active, MainPID 1792209 |
| 5 | atlas git PRE | git on Beast | `2f2c3b7` clean tree |
| 6 | All 7 module files AST OK | python ast.parse | inputs / acl / telemetry / events / memory / inference / server |
| 7 | All 7 imports OK | python -c imports | clean |
| 8 | atlas-mcp.service POST-restart | systemctl on Beast | active, MainPID **2042174** (rotated) |
| 9 | Strict-loopback invariant | ss -tlnp on Beast | `127.0.0.1:8001` LISTEN python pid=2042174 |
| 10 | Smoke from Beast SDK | python script | INITIALIZE_OK + tools_count=4 |
| 11 | All 4 tool calls succeed | smoke output | events_search / inference_history / memory_query / memory_upsert all returned |
| 12 | atlas.events POST | psql | atlas.mcp_server=4 NEW rows |
| 13 | caller_endpoint via X-Real-IP | psql payload->>'caller_endpoint' | `100.121.109.112` (Tailscale IP, **not loopback**) |
| 14 | atlas.memory smoke_test row | psql | id=1, content_len=26, embedding NOT NULL, metadata=`{"cycle":"1h"}` |
| 15 | Anchors POST diff | diff PRE/POST | ANCHORS-BIT-IDENTICAL |
| 16 | Secrets audit | psql ~* regex | 0 hits on `authkey\|tskey\|password\|secret\|smoke_test\|Cycle 1H` |

Sixth in-session application of 5th standing rule.

---

## Section 1 -- TL;DR

Cycle 1H CLOSED 5/5 PASS. 4 atlas-mcp tools live on Beast inbound MCP at `https://sloan2.tail1216a3.ts.net:8443/mcp`:
- atlas_events_search (READ; atlas.events with source/kind/ts filter)
- atlas_memory_query (READ; vector similarity, server embeds query_text)
- atlas_memory_upsert (WRITE; server embeds content, INSERTs into atlas.memory)
- atlas_inference_history (READ; atlas.events WHERE source='atlas.inference')

Server-side ACL = authoritative boundary (v0.1 deny patterns minimal; Pydantic Field validators carry the allow-list weight). Telemetry source=`atlas.mcp_server` mirrors mcp_client _log_event pattern. caller_endpoint extracted from nginx X-Real-IP (verified Tailscale IP, not loopback). Strict-loopback invariant preserved. Substrate anchors bit-identical for ~96+ hours since Day 71. Atlas commit `bfed019` (santigrey/atlas).

---

## Section 2 -- Cycle 1H 5-gate scorecard

| # | Gate | Status | Evidence |
|---|---|---|---|
| 1 | tools_count=4 + names match | PASS | `['atlas_events_search', 'atlas_inference_history', 'atlas_memory_query', 'atlas_memory_upsert']` |
| 2 | All 4 sample invocations succeed | PASS | events_search returned 5 rows; inference_history returned 5 rows; memory_query returned [] (atlas.memory was empty pre-upsert); memory_upsert returned `{id:1, kind:smoke_test, ts:...}` |
| 3 | atlas.events shows source=atlas.mcp_server with arg_keys + caller_endpoint via X-Real-IP | PASS | 4 NEW tool_call rows; arg_keys are full schema field names (NOT `["params"]`); caller_endpoint=`100.121.109.112` (Tailscale, not loopback) |
| 4 | atlas.memory upsert created row with embedding + metadata | PASS | id=1, content_len=26, has_embedding=`t`, metadata=`{"cycle":"1h"}` |
| 5 | Anchors bit-identical pre/post + secrets audit clean | PASS | ANCHORS-BIT-IDENTICAL + 0 hits on representative regex |

Plus standing gates:
- secret-grep on Atlas commit diff: clean
- B2b subscription `controlplane_sub`: untouched (anchor preservation)
- Garage cluster status: unchanged (anchor preservation)
- mcp_server.py on CK: untouched (this cycle is Beast-side)
- atlas-mcp loopback :8001 bind preserved: ss -tlnp showed `127.0.0.1:8001` post-restart
- nginx vhost on Beast: untouched (no config changes; Cycle 1G Host rewrite + X-Real-IP propagation honored)

---

## Section 3 -- Tool implementation summary (file inventory)

All under `/home/jes/atlas/src/atlas/mcp_server/`:

| File | Bytes | Role |
|---|---|---|
| `inputs.py` | 3821 | 4 Pydantic input classes with Field validators + EVENTS_SOURCE_ALLOWLIST |
| `acl.py` | 2477 | ServerAclDenyPattern dataclass + check_server_acl + AtlasMcpServerAclDenied |
| `telemetry.py` | 1628 | log_event module function (mirror of mcp_client._log_event); source=atlas.mcp_server |
| `events.py` | 1593 | search_events: parameterized SQL with optional filters |
| `memory.py` | 3894 | query_memory + upsert_memory; module-level lazy embedder; vector literal helper |
| `inference.py` | 1817 | history_inference: atlas.events WHERE source='atlas.inference' + 7-day default |
| `server.py` | 6490 | FastMCP instance + 4 @mcp.tool wirings + _wrap_tool helper + _extract_caller_endpoint |

Atlas commit: `bfed019` -- 7 files changed (6 NEW + 1 MODIFIED `server.py`). 636 insertions, 8 deletions (the 8-line Cycle 1G placeholder skeleton replaced).

---

## Section 4 -- Pydantic input classes

4 classes, all `extra="forbid"` + `str_strip_whitespace=True`:

- **EventsSearchInput**: source (Optional, allowlist validator), kind (Optional), ts_after / ts_before (Optional datetime), limit (1-100, default 50)
- **MemoryQueryInput**: query_text (1-10000), top_k (1-20, default 5), kind (Optional, max 50)
- **MemoryUpsertInput**: kind (1-50, regex `^[a-z][a-z0-9_]*$`), content (1-100000), metadata (Optional dict, 10KB serialized cap)
- **InferenceHistoryInput**: model (Optional, max 200), ts_after / ts_before (Optional), limit (1-50, default 20)

Fields enforced declaratively at parse time. Validators give Pydantic-native error messages on bad input.

---

## Section 5 -- Server-side ACL

`AtlasMcpServerAclDenied` exception + `ServerAclDenyPattern` frozen dataclass + `check_server_acl(tool_name, arguments)` function.

**v0.1 patterns:** empty list. Pydantic Field validators carry the allow-list weight. ACL infrastructure is forward-compat for future deny needs (block specific kinds, block writes from certain caller IPs, etc.).

**Posture:** server-side ACL is the AUTHORITATIVE control. Client-side (atlas.mcp_client.acl) is defense-in-depth. Mirrors mcp_client/acl.py shape (verified live per P6 #28).

**Nested-params lookup:** check_server_acl looks in top-level args AND nested `'params'` dict (handles auto-wrapped form per Cycle 1F Refinement 2 mirror).

---

## Section 6 -- Telemetry contract

Source: `atlas.mcp_server`. Kinds shipped:
- `tool_call` (success path)
- `tool_call_denied` (ACL deny path; includes deny_reason + deny_layer='server')
- `tool_call_error` (exception path; includes error_type)
- `tools_list` (reserved; not yet emitted -- Cycle 1H tests didn't trigger an explicit list_tools event because FastMCP handles list_tools internally)

Payload fields per row:
- `tool_name`
- `arg_keys` -- sorted list (P6 #27 invariant)
- `status` -- 'success' | 'denied' | 'error'
- `duration_ms` -- ns -> ms via local _ns_to_ms helper
- `caller_endpoint` -- nginx X-Real-IP value, fallback 'loopback' if FastMCP Context lacks request headers

SECRETS DISCIPLINE: arg VALUES never persisted; only the keys.

**caller_endpoint extraction outcome:** WORKED. Smoke captured `100.121.109.112` (Tailscale IP, not loopback). FastMCP Context API path `ctx.request_context.request.headers` is functional in mcp 1.27.0; v0.2 P5 #25 (alternative-path fallback) banked but not blocking.

---

## Section 7 -- End-to-end smoke output

From Beast atlas venv against `https://sloan2.tail1216a3.ts.net:8443/mcp`:

```
SMOKE INITIALIZE_OK
SMOKE tools_count: 4
SMOKE tool_names: ['atlas_events_search', 'atlas_inference_history', 'atlas_memory_query', 'atlas_memory_upsert']
SMOKE events_search OK; returned: <id 32 atlas.mcp_client tool_call ...>
SMOKE inference_history OK; returned: <id 28 atlas.inference generate ...>
SMOKE memory_query OK; returned: [] (atlas.memory empty pre-upsert)
SMOKE memory_upsert OK; returned: {id:1, ts:2026-05-01 16:28:18.357539+00:00, kind:smoke_test}
EXIT=0
```

All 4 tool calls returned. Total smoke runtime ~15s (memory_query took 1554ms due to mxbai-embed-large query embedding generation; memory_upsert took 136ms with cache hit).

---

## Section 8 -- atlas.events sample (post-cycle)

Counts by source POST:
```
atlas.embeddings | 12   (unchanged from PRE)
atlas.inference  | 14   (unchanged)
atlas.mcp_client |  6   (unchanged)
atlas.mcp_server |  4   (NEW)
```

arg_keys preservation evidence (full payloads):
```
tool_call | atlas_events_search     | arg_keys=["kind","limit","source","ts_after","ts_before"] | dur_ms=48.126
tool_call | atlas_inference_history | arg_keys=["limit","model","ts_after","ts_before"]         | dur_ms=6.234
tool_call | atlas_memory_query      | arg_keys=["kind","query_text","top_k"]                    | dur_ms=1554.009
tool_call | atlas_memory_upsert     | arg_keys=["content","kind","metadata"]                    | dur_ms=136.443
```

All caller_endpoint values: `100.121.109.112` (Tailscale).

---

## Section 9 -- atlas.memory upsert evidence

```
 id |              ts               |    kind    | content_len | has_embedding |   metadata     
----+-------------------------------+------------+-------------+---------------+----------------
  1 | 2026-05-01 16:28:18.357539+00 | smoke_test |          26 | t             | {"cycle":"1h"}
```

This is the FIRST row in atlas.memory (id=1). embedding column is NOT NULL (mxbai-embed-large generated server-side; vector(1024)). metadata jsonb persisted as `{"cycle":"1h"}`. content_len=26 matches `len('Cycle 1H smoke test memory')`.

---

## Section 10 -- Anchor preservation diff

```
--- PRE (Step 1) ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- POST (Step 10) ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- diff ---
ANCHORS-BIT-IDENTICAL
```

B2b nanosecond anchor + Garage anchor held bit-identical for **~96+ hours** since Day 71 (2026-04-27 establishment) -- spanning H1 ship + Atlas Cycles 1A through 1H + multiple atlas-mcp.service restarts.

---

## Section 11 -- Process observations

**P6 #28 verified live during build.** Before authoring 7 modules, read existing patterns to mirror:
- mcp_client/acl.py shape (frozen dataclass + check_acl pattern)
- mcp_client/_log_event method (telemetry insertion pattern)
- atlas.db.Database API (constructor + connection() asynccontextmanager)
- atlas.embeddings.EmbeddingClient API
- atlas.inference.telemetry._ns_to_ms helper

**Spec deviation #1 (P6 #28 caught):** Paco's directive sketch named `from atlas.embeddings import embed_single`. Verified live: no such function exists. Actual API is `EmbeddingClient.embed(text)` returning `list[float]` for str input or `list[list[float]]` for list[str] input. Used `get_embedder()` factory + `.embed()` method. Documented in Atlas commit body.

**Spec deviation #2:** Paco's sketch had _log_event as instance method (mirroring McpClient). Used module-level `log_event(*, db, kind, payload)` function in `mcp_server.telemetry` since server.py uses module-level lazy `_get_db()` (no shared instance). Functionally equivalent; cleaner shape for the server-side dispatch model. v0.2 P5 #23 will extract both into shared atlas.telemetry utility regardless.

**P6 #27 nuance:** my `_wrap_tool` captures `params.model_dump().keys()` which is post-Pydantic-validation (includes default-value fields). atlas.mcp_client captures raw arg keys pre-Pydantic. Both satisfy spirit (`["params"]` never appears in atlas.events). Server-side captures full schema field names; client-side captures literal caller-provided subset. Honest deviation; spec's actual P6 #27 wording ("BEFORE any internal transformation") is preserved -- ours captures BEFORE the auto-wrap layer that would have shown `["params"]`. Candidate v0.2 P5 if Cycle 1H tests show this matters.

**FastMCP Context API outcome:** `ctx.request_context.request.headers` works in mcp 1.27.0. Smoke captured X-Real-IP=`100.121.109.112` (Tailscale IP, not loopback). Cycle 1G nginx vhost X-Real-IP propagation verified end-to-end.

**Service restart impact on substrate:** None. atlas-mcp.service restart at Step 6 is application-layer; Postgres + Garage Docker containers untouched (anchor diff confirms bit-identical).

**v0.2 P5 candidates surfaced this cycle:**
- v0.2 P5 #25: alternate FastMCP Context path for X-Real-IP (current path works; the fallback is banked just in case API changes)
- v0.2 P5 #N: pre-Pydantic raw arg_keys capture (only if downstream tests need strict caller-only keys vs full schema)
- v0.2 P5 #23 (already banked): extract telemetry _log_event to shared atlas.telemetry utility

---

## Section 12 -- Asks for Paco

1. **Confirm Cycle 1H 5/5 PASS** -- 5 gates met + 6 standing gates met (Sections 2+3); ratify the close.
2. **Confirm Cycle 1I entry-point as atlas.tasks.* state machine paco_request** -- per directive's deferred-scope notes, atlas.tasks.* lands next. PD will draft entry-point paco_request when triggered.
3. **P6 #29 candidate:** "Verify spec-named API symbols against actual module exports BEFORE authoring; Paco's spec sketches name functions that may not exist." (Caught Paco's `embed_single` reference; would have wasted a build cycle if untested.)
4. **Decision on pre-Pydantic raw arg_keys capture:** is the post-Pydantic-validation full-schema-keys representation acceptable, or should server-side mirror client-side strict subset? If strict, file as v0.2 P5; if acceptable, document as accepted divergence.

No close-out fold deviation requested. PD has discharged Steps 1-13 per directive.
