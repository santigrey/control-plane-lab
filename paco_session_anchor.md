# Paco Session Anchor

**Last updated:** 2026-05-01 UTC (Day 77)
**Anchor commit:** post-Cycle-2C-close on santigrey/control-plane-lab `main` (this turn's commit pending push)
**Resume Phrase:** "Day 77 close: Atlas Cycle 2C 5/5 PASS (panels-only scope; alexandra-telemetry deferred v0.2 P5 #42 per substrate posture). Capstone-demo readiness achieved -- Memory Browser + Audit Log Viewer + Token Usage Dashboard all live on `https://sloan3.tail1216a3.ts.net/dashboard/{memory,audit,tokens}`. P6=30. Ready for Cycle 2D (polish + demo video + capstone slides + architecture diagram)."

---

## Atlas v0.2 progression

- **Cycle 2A** Alexandra integration paco_request gate: CLOSED (control-plane-lab commit `416049f`); 11 asks ratified at `c3ede72`
- **Cycle 2B** atlas.mcp_client wiring + Memory Browser + ALLOWLIST + P5 #28 fix: CLOSED 5/5 PASS Day 77 (atlas commit `d4f1a81`)
- **Cycle 2C** Audit Log Viewer + Token Usage Dashboard + alexandra-telemetry: **CLOSED 5/5 PASS Day 77** (panels-only scope; telemetry deferred per substrate localhost-bound posture)
  - 1 file extended (dashboard.py +12565 B; HTML_AUDIT + HTML_TOKENS + 4 routes + 2 Pydantic models)
  - Steps 5-6 (atlas_telemetry.py + wiring) DEFERRED to v0.2 P5 #42
  - Beast pg cross-host probe verified NOT_REACHABLE (intentional Docker localhost-bound)
  - Ninth clean PD-side application of 5th standing rule
  - P6 #29 saved a build cycle (probe-first BEFORE authoring; Paco directive's IP was Goliath's not Beast's anyway)
- **Cycle 2D (polish + demo video + slides):** NEXT per Cycle 2A roadmap
- **Optional Cycle 2E (atlas_tasks_* queue panel):** v0.2.1 candidate

## Capstone-demo readiness state ACHIEVED Day 77

3 dashboard panels live on Alexandra:
- `https://sloan3.tail1216a3.ts.net/dashboard/memory` (Cycle 2B)
- `https://sloan3.tail1216a3.ts.net/dashboard/audit` (Cycle 2C)
- `https://sloan3.tail1216a3.ts.net/dashboard/tokens` (Cycle 2C)

All backed by atlas-mcp via Path A AtlasBridge transport. caller_endpoint propagation through nginx X-Real-IP confirmed (CK Tailscale 100.115.56.89). Demo narrative all 5 scenes supportable from this state.

## Atlas v0.1 Cycle 1 -- COMPLETE (carry-forward)

- 1A through 1I shipped; 10 atlas-mcp tools live; Atlas v0.1 Cycle 1 COMPLETE marker confirmed by Paco at HEAD `bbc10e2`

## Substrate -- HOLDING ~96+ hours

- B2b nanosecond anchor: `2026-04-27T00:13:57.800746541Z` -- bit-identical PRE/POST through Cycle 2C
- Garage anchor: `2026-04-27T05:39:58.168067641Z` -- bit-identical
- Cycle 2C atlas.events delta: +2 rows source=atlas.mcp_server (smoke calls; caller_endpoint=100.115.56.89)
- Cycle 2C atlas.memory delta: 0
- atlas-mcp.service: untouched this cycle (still MainPID 2173807 from Cycle 2B)
- orchestrator.service: restarted (MainPID 347400 rotated from 292908; substrate untouched)

## Substrate isolation finding (Cycle 2C):

Beast pg cross-host = NOT_REACHABLE from CK at both 192.168.1.20 (Goliath -- Paco directive typo) and 192.168.1.152 (actual Beast). Intentional posture per hard rule "Docker bypasses UFW. Bind PostgreSQL and other Docker services to localhost in compose.yaml" + Phase G compose-down ESC.

Banked as **v0.2 P5 #42** with PD-recommended **Option 1**: add `atlas_events_create` MCP tool to atlas.mcp_server surface. Preserves substrate isolation; mirrors Cycle 1H/1I argshape pattern; uses existing trusted transport.

## Atlas package state (Beast `/home/jes/atlas/`)

- All Cycle 1 + Cycle 2B EVENTS_SOURCE_ALLOWLIST extension; UNCHANGED Cycle 2C
- Latest commit: `d4f1a81`

## Alexandra-side state (CK `/home/jes/control-plane/orchestrator/`)

- `app.py` (Cycle 2B P5 #28 fix)
- `ai_operator/atlas_bridge.py` (Cycle 2B NEW; UNCHANGED 2C)
- `ai_operator/context_engine.py` (Cycle 2B P5 #28 fix)
- `ai_operator/tools/registry.py` (Cycle 2B P5 #28 fix)
- `ai_operator/dashboard/dashboard.py` (extended Cycle 2B Memory + Cycle 2C Audit + Tokens; 14 routes total)
- `.env` (Cycle 2B P5 #28 fix on-disk; gitignored)
- mcp SDK 1.27.0 in `.venv` (Cycle 2B install)

## atlas-mcp 10 tools live (unchanged Cycle 1H/1I)

- Cycle 1H read/write (4): atlas_events_search / atlas_memory_query / atlas_memory_upsert / atlas_inference_history
- Cycle 1I state machine (6): atlas_tasks_create / atlas_tasks_list / atlas_tasks_get / atlas_tasks_claim / atlas_tasks_complete / atlas_tasks_fail

## Alexandra dashboard surface (Cycle 2B + 2C additions)

- 7 existing dashboard routes
- `/dashboard/memory` (Cycle 2B) + 2 API endpoints
- `/dashboard/audit` (Cycle 2C) + 1 API endpoint
- `/dashboard/tokens` (Cycle 2C) + 1 API endpoint
- 14 routes total

## atlas.events state (cumulative)

- 60 rows total (12 emb + 14 inf + 6 mcp_client + 28 mcp_server)
- atlas.mcp_server +2 this cycle (atlas_events_search 7.1ms + atlas_inference_history 4.9ms; caller_endpoint=100.115.56.89)
- arg_keys preserved (caller field names, NOT ["params"])
- Secrets discipline maintained (0 hits)

## atlas.memory state

- 2 rows unchanged (id=1 Cycle 1H + id=2 Cycle 2B)

## EVENTS_SOURCE_ALLOWLIST (atlas.mcp_server.inputs)

- 5 entries (alexandra source pre-allowed for v0.2 P5 #42 work; not yet exercised by row inserts)

## Service state

- atlas-mcp.service: active MainPID 2173807 (Cycle 2B; unchanged Cycle 2C)
- orchestrator.service: active MainPID 347400 (rotated Cycle 2C from 292908)

## Standing rules: 5 memory files unchanged + Standing Rule #6 banked Day 77 by Paco at HEAD `01ff1a4`

## P6 lessons banked: 30 (P6 #28+29+30 applied as canonical case this cycle: probe-first reachability check before authoring atlas_telemetry.py saved one build cycle)

## v0.2 hardening pass queue: 38 banked + 4 PD candidates (#39 adminpass refactor, #40 declarative deps, #41 Path A telemetry doc, #42 alexandra-telemetry wiring path)

## v0.2 P5 #28: RESOLVED Cycle 2B
## v0.2 P5 #22: RESOLVED prior

## On resume

1. Paco confirms Cycle 2C 5/5 PASS panels-only scope
2. Paco banks v0.2 P5 #42 (or refines)
3. Paco rules on Option 1 (`atlas_events_create` MCP tool) for alexandra-telemetry wiring path
4. Paco issues Cycle 2D directive (polish + demo video script + capstone slides + architecture diagram)

## Notes for Paco

- Cycle 2C: panels-only scope. Two new dashboards verified end-to-end via Path A AtlasBridge transport.
- Beast pg cross-host probe BEFORE authoring atlas_telemetry.py saved one build cycle. Paco's directive named 192.168.1.20 (Goliath's IP, not Beast's). Even if it had been correct (192.168.1.152), substrate is Docker localhost-bound. Both unreachable verified live.
- Capstone-demo readiness achieved: 3 panels live + atlas-mcp 10 tools backing them. Demo narrative supports all 5 scenes from this state.
- Cycle 2D = pure polish work. No code on Atlas-integration axis needed for v0.2.0 capstone demo.
- v0.2 P5 #42 PD recommendation: add `atlas_events_create` MCP tool. Mirrors Cycle 1H/1I. Single tool addition + Alexandra-side AtlasBridge ALLOWED_TOOLS extension. Substrate isolation preserved.
