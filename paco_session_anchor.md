# Paco Session Anchor

**Last updated:** 2026-05-01 UTC (Day 77)
**Anchor commit:** post-Cycle-1I-close on santigrey/control-plane-lab `main` (this turn's commit pending push)
**Resume Phrase:** "Day 77 close: Atlas Cycle 1I 5/5 PASS, atlas.tasks state machine 6 tools live on santigrey/atlas `d383fe0`, Atlas v0.1 Cycle 1 COMPLETE (1A-1I), 10 tools live on atlas-mcp, P6=29, v0.2 P5 queue +1, ready for Atlas v0.2 entry-point (Alexandra integration / capstone demo wiring)."

---

## Atlas v0.1 progression -- COMPLETE

- **Cycle 1A** package skeleton: CLOSED (atlas commit `3e50a13`)
- **Cycle 1B** Postgres + atlas schema: CLOSED (atlas commit `42e41b7`)
- **Cycle 1C** Garage S3 client: CLOSED (atlas commit `81de0b2`)
- **Cycle 1D** Goliath inference RPC + telemetry: CLOSED (atlas commit `752134f`)
- **Cycle 1E** mxbai-embed-large embedding service: CLOSED (atlas commit `6c0b8d6`)
- **Cycle 1F** MCP client gateway + ACL + telemetry + auto-wrap: CLOSED (atlas commit `5a9e458`)
- **Cycle 1G** inbound MCP server skeleton (FastMCP loopback + Option A nginx Host rewrite + Tailscale FQDN cert): CLOSED (atlas commit `2f2c3b7`)
- **Cycle 1H** atlas-mcp tool surface (4 tools): CLOSED 5/5 PASS (atlas commit `bfed019`)
- **Cycle 1I** atlas.tasks state machine (6 tools): **CLOSED 5/5 PASS Day 77** (atlas commit `d383fe0`)
  - 4 files (2 NEW + 2 MODIFIED): errors.py + tasks.py + inputs.py + server.py
  - 644 insertions, 10 deletions
  - 4 transitions: null->pending / pending->running (SKIP LOCKED) / running->done / running->failed
  - AtlasTaskStateError 4 kinds (not_found / wrong_status / wrong_owner / race) with disambiguation pattern
  - Race-safety verified: 3+5=3+2
  - Round-trip success + fail verified
  - All 3 disambiguation kinds verified end-to-end with error_kind discriminator in atlas.events
  - Seventh clean PD-side application of 5th standing rule
  - **P6 #29 applied (canonical case)** -- Paco sketch used asyncpg API; PD verified live and translated to actual psycopg API
- **Atlas v0.1 Cycle 1 COMPLETE.** Inflection point: Atlas v0.2 entry = Alexandra integration / capstone demo wiring.

## Substrate -- HOLDING ~96+ hours

- B2b nanosecond anchor: `2026-04-27T00:13:57.800746541Z` -- bit-identical PRE/POST through Cycle 1I
- Garage anchor: `2026-04-27T05:39:58.168067641Z` -- bit-identical
- B2b subscription `controlplane_sub`: untouched
- Garage cluster: unchanged
- atlas-mcp.service: restarted at Step 6 (application-layer; substrate untouched)
- Cycle 1I atlas.events delta: +20 rows source=atlas.mcp_server (21 tool_call + 3 tool_call_error from disambiguation tests)
- Cycle 1I atlas.tasks delta: +6 rows (running=4, done=1, failed=1)

## Atlas package state (Beast `/home/jes/atlas/`)

- src/atlas/db/ (Cycle 1B)
- src/atlas/storage/ (Cycle 1C)
- src/atlas/inference/ (Cycle 1D)
- src/atlas/embeddings/ (Cycle 1E)
- src/atlas/mcp_client/ (Cycle 1F)
- src/atlas/mcp_server/ (Cycles 1G + 1H + 1I):
  - inputs.py + acl.py + telemetry.py + events.py + memory.py + inference.py + server.py + errors.py + tasks.py
- ~38 source files in repo
- Latest commit: `d383fe0`

## atlas-mcp 10 tools live

- Cycle 1H read/write (4): atlas_events_search / atlas_memory_query / atlas_memory_upsert / atlas_inference_history
- Cycle 1I state machine (6): atlas_tasks_create / atlas_tasks_list / atlas_tasks_get / atlas_tasks_claim / atlas_tasks_complete / atlas_tasks_fail
- Endpoint: `https://sloan2.tail1216a3.ts.net:8443/mcp`
- Strict-loopback :8001 bind (uvicorn behind nginx)
- caller_endpoint extraction WORKING via X-Real-IP (verified Tailscale 100.121.109.112)

## atlas.events state (cumulative)

- 56 rows total
- 12 from atlas.embeddings
- 14 from atlas.inference
- 6 from atlas.mcp_client
- 24 from atlas.mcp_server (Cycle 1H smoke 4 + Cycle 1I tests 20)
- All payloads: secrets discipline maintained (0 hits in audit on Cycle 1I-specific kind names + secret keywords)

## atlas.tasks state

- 6 rows (4 running + 1 done + 1 failed)
- v0.2 P5 #34 candidate covers eventual cleanup (worker heartbeat / claim-timeout / dead-letter recovery)

## atlas.memory state (unchanged from Cycle 1H)

- 1 row (smoke_test from Cycle 1H)

## atlas-mcp.service (Beast inbound)

- MainPID 2111126 (rotated from 2042174 via Step 6 restart)
- Strict-loopback bind: 127.0.0.1:8001
- Fronted by nginx :8443 with Tailscale FQDN cert (Cycle 1G config unchanged)

## Standing rules: 5 memory files (unchanged)

## P6 lessons banked: 29 (P6 #29 applied this cycle as canonical case)

## v0.2 hardening pass queue: P5 #29-#34 banked + new candidate (explicit MCP ToolError wrapping for AtlasTaskStateError structured kind field surfacing)

## v0.2 P5 #22 (Tailscale auth key residual): RESOLVED (1-day expiration confirmed by CEO)

## On resume

1. Paco confirms Cycle 1I 5/5 PASS
2. Paco confirms Atlas v0.1 Cycle 1 COMPLETE marker
3. Paco issues Atlas v0.2 entry-point paco_request directive (Alexandra integration / capstone demo wiring)
4. PD drafts v0.2 entry-point paco_request when triggered

## Notes for Paco

- Atlas v0.1 Cycle 1 fully shipped: 9 cycles (1A-1I) + 10 inbound MCP tools + state machine + atlas.events telemetry (4 sources) + atlas.memory (1 row) + atlas.tasks (6 rows)
- Substrate held bit-identical through 9 Atlas cycles + 2 service restarts + ~24 atlas-mcp tool calls + SQL-level direct UPDATE on atlas.tasks.owner during wrong_owner test
- P6 #29 saved a build cycle (canonical case): Paco's tasks.py asyncpg sketch would have failed at first import; live API verification before authoring caught the gap
- v0.2 P5 candidates surfaced: 6 explicit + 1 new = explicit MCP ToolError wrapping for cleaner structured error responses (current path string-parses error_kind from str repr; works but suboptimal)
