# Paco Session Anchor

**Last updated:** 2026-05-01 UTC (Day 77)
**Anchor commit:** post-Cycle-1H-close on santigrey/control-plane-lab `main` (this turn's commit pending push)
**Resume Phrase:** "Day 77 close: Atlas Cycle 1H 5/5 PASS, atlas-mcp tool surface 4 tools live on santigrey/atlas `bfed019`, P6=28, v0.2 P5 queue +1, ready for Cycle 1I (atlas.tasks state machine paco_request)."

---

## Atlas v0.1 progression (post Cycle 1H close)

- **Cycle 1A** package skeleton: CLOSED (atlas commit `3e50a13`)
- **Cycle 1B** Postgres connection + atlas schema: CLOSED (atlas commit `42e41b7`)
- **Cycle 1C** Garage S3 client + bucket adoption: CLOSED (atlas commit `81de0b2`)
- **Cycle 1D** Goliath inference RPC + token telemetry: CLOSED (atlas commit `752134f`)
- **Cycle 1E** Embedding service mxbai-embed-large: CLOSED (atlas commit `6c0b8d6`)
- **Cycle 1F** MCP client gateway + ACL + telemetry + schema-aware auto-wrap: CLOSED (atlas commit `5a9e458`)
- **Cycle 1G** Inbound MCP server skeleton (Option A nginx Host rewrite + tailnet FQDN cert): CLOSED (atlas commit `2f2c3b7`)
- **Cycle 1H** atlas-mcp tool surface (4 tools): **CLOSED 5/5 PASS Day 77** (atlas commit `bfed019`)
  - 7 files (6 NEW + 1 MODIFIED): inputs.py + acl.py + telemetry.py + events.py + memory.py + inference.py + server.py
  - 636 insertions, 8 deletions
  - 4 tools: atlas_events_search / atlas_memory_query / atlas_memory_upsert / atlas_inference_history
  - Sixth clean PD-side application of 5th standing rule
  - P6 #28 verified live during build (caught Paco's `embed_single` spec error before authoring)
- **Cycle 1I (atlas.tasks.* state machine):** NEXT (paco_request entry-point pending)
- **Cycles ahead per spec v3:** atlas.tasks state machine + atlas.queue + atlas.scheduler

## Substrate -- HOLDING ~96+ hours

- B2b nanosecond anchor: `2026-04-27T00:13:57.800746541Z` -- bit-identical PRE/POST through Cycle 1H
- Garage anchor: `2026-04-27T05:39:58.168067641Z` -- bit-identical
- B2b subscription `controlplane_sub`: untouched
- Garage cluster: unchanged
- atlas-mcp.service: restarted at Step 6 (application-layer; substrate untouched)
- Cycle 1H atlas.events delta: +4 rows source=atlas.mcp_server (one per smoke tool call)
- Cycle 1H atlas.memory delta: +1 row id=1 kind=smoke_test (first row in atlas.memory)

## Atlas package state (Beast `/home/jes/atlas/`)

- src/atlas/db/ (Cycle 1B)
- src/atlas/storage/ (Cycle 1C)
- src/atlas/inference/ (Cycle 1D)
- src/atlas/embeddings/ (Cycle 1E)
- src/atlas/mcp_client/ (Cycle 1F)
- src/atlas/mcp_server/ (Cycle 1G skeleton + **Cycle 1H tool surface**)
  - inputs.py + acl.py + telemetry.py + events.py + memory.py + inference.py + server.py
- ~35 source files in repo
- Latest commit: `bfed019`

## atlas.events state (cumulative)

- 36 rows total
- 12 from atlas.embeddings
- 14 from atlas.inference
- 6 from atlas.mcp_client
- 4 from atlas.mcp_server (Cycle 1H smoke)
- All payloads: secrets discipline maintained (keys-not-values verified 0 hits)

## atlas.memory state

- 1 row total: id=1 kind=smoke_test from Cycle 1H smoke
- has_embedding=true (mxbai-embed-large dim 1024)
- metadata jsonb populated

## atlas-mcp.service (Beast inbound)

- MainPID 2042174 (rotated from 1792209)
- Strict-loopback bind: 127.0.0.1:8001
- Fronted by nginx :8443 with Tailscale FQDN cert
- 4 tools live; verified via Beast atlas venv smoke at `https://sloan2.tail1216a3.ts.net:8443/mcp`
- caller_endpoint extraction WORKS via FastMCP `ctx.request_context.request.headers` -> X-Real-IP=`100.121.109.112` (Tailscale)

## Standing rules: 5 memory files (unchanged)

## P6 lessons banked: 28 (Cycle 1H proposed P6 #29 -- verify spec-named API symbols against module exports before authoring; awaits Paco banking decision)

## v0.2 hardening pass queue: P5 #23 + P5 #25 carry forward; one new candidate (pre-Pydantic raw arg_keys capture for strict caller-only key semantics) -- pending Paco decision

## On resume

1. Paco confirms Cycle 1H 5/5 PASS
2. Paco issues Cycle 1I entry-point (atlas.tasks.* state machine paco_request gate, mirroring Cycle 1H entry-point pattern)
3. PD drafts Cycle 1I tool-surface paco_request when triggered
4. Continue through atlas.tasks state machine + queue + scheduler

## Notes for Paco

- Cycle 1H built clean: 0 spec deviations except 2 honest API-mismatch corrections (embed_single non-existent; _log_event instance->module function)
- 16 verifications run live; sixth clean application of 5th standing rule
- Substrate held bit-identical through 8 Atlas cycles + service restart at Step 6 + 4 smoke tool calls
- caller_endpoint X-Real-IP path validated in production -- Cycle 1G nginx vhost propagation works end-to-end
- v0.2 P5 #23 (shared telemetry utility) becomes more attractive as both client and server now have parallel _log_event implementations
- P6 #29 candidate filed: verify spec-named API symbols against module exports BEFORE authoring (Paco's `embed_single` named function that doesn't exist; would have wasted a build cycle if untested)
