# Paco Session Anchor

**Last updated:** 2026-04-30 (Day 76 evening)
**Anchor commit:** `f998883` on santigrey/control-plane-lab `main`
**Resume Phrase:** "Day 76: Atlas Cycle 1F Phase 3 GO dispatched (commit f998883). PD has armed Phase 3 directive at /home/jes/control-plane/docs/handoff_paco_to_pd.md. Awaiting CEO trigger to PD: 'Read docs/handoff_paco_to_pd.md and execute.' Sloan is on Cortez. After PD finishes, CEO will trigger Paco: 'Paco, PD finished Cycle 1F, check handoff.'"

---

## Atlas v0.1 progression

- **Cycle 1A** package skeleton: CLOSED (atlas commit `3e50a13`)
- **Cycle 1B** Postgres connection layer + atlas schema: CLOSED (atlas commit `42e41b7`)
- **Cycle 1C** Garage S3 client + bucket adoption: CLOSED (atlas commit `81de0b2`)
- **Cycle 1D** Goliath inference RPC + token telemetry: CLOSED (atlas commit `752134f`)
- **Cycle 1E** Embedding service mxbai-embed-large: CLOSED 5/5 PASS Day 75 (atlas commit `6c0b8d6`)
- **Cycle 1F** MCP client gateway: Phase 3 GO dispatched (Day 76); BUILD pending PD execution
- **Cycles 1G-1H + 2 + 3 + 4:** ahead per spec v3

## Cycle 1F transport saga (Day 76, in chronological order)

1. **BLOCK at Step 3** (commit `1550eb2`): connectivity smoke from Beast hung; PD filed paco_request_transport_hang.md with 4 candidate paths (A install Tailscale / B new nginx vhost / C diagnostic / D stdio).
2. **Path C verdict** (commit `560fb77`): Paco selected diagnostic-first; Verified live disproved 5.A (uvicorn binds 0.0.0.0); Phase C.1 dispatched.
3. **Phase C.1 diagnostic complete** (commit `1f6896c`): PD identified MCP-Protocol-Version: 2025-03-26 header missing in python SDK 1.27.0 vs FastMCP 1.26.0 server. Recommended single-line atlas.mcp_client header fix.
4. **Phase C.1 verdict revision** (commit `61b663b`): Paco's counter-probes (CP1-CP5) caught the gap -- header alone insufficient. Python SDK still hangs even with header on direct uvicorn HTTP; HTTPS+nginx still fails for Beast LAN source. Phase C.2 attach diagnostic dispatched.
5. **Phase C.2.0 root cause PROVEN** (commit `3bb9517`): PD's py-spy stack on uvicorn PID 3631249 showed event loop parked in subprocess.run inside async homelab_ssh_run handler with NO asyncio.to_thread wrapper. Recv-Q=450 on uvicorn loopback socket = POST body queued unread because event loop blocked. Mechanism: event-loop blocking, not init-handler malfunction. Hypothesis 5.E PROVEN.
6. **Phase 3 GO** (commit `f998883`, this anchor commit): combined fix dispatched -- (a) server patch mcp_server.py adds `import asyncio` + wraps 14 @mcp.tool handlers' sync helper calls in asyncio.to_thread; (b) atlas client patch adds MCP-Protocol-Version header; (c) deploy-restart via `sudo systemctl restart homelab-mcp.service` (CEO trigger == single-confirm); (d) end-to-end Beast smoke; (e) full Cycle 1F build per original handoff (4 tests + 5 acceptance gates + token logging + ACL + secrets discipline audit); (f) commits to santigrey/atlas + control-plane-lab close-out fold.

## Pre-directive verification catches (5th standing rule)

This cycle, the 5th rule earned its keep at every directive turn:

- **Path C verdict:** Paco caught `host='0.0.0.0'` in mcp_http.py -> disproved 5.A before authoring directive
- **Phase C.1 review:** Paco's CP1-CP5 (4 counter-probes from Beast) revealed PD's recommended Phase 3 fix was incomplete -- would have caused BLOCK #2
- **Phase C.2.0 confirm:** Paco's Verified live caught (a) `asyncio` not yet imported in mcp_server.py; (b) PD's recommended `nohup` relaunch would orphan the systemd-managed process (PPID=1, unit at /etc/systemd/system/homelab-mcp.service) -- correct restart is `sudo systemctl restart homelab-mcp.service`

Cumulative findings caught at directive-authorship across all 10 directive verifications: **30**.

## P6 lessons banked from Cycle 1F transport saga

- **#21** tcpdump-on-lo for client-server impedance pattern (PD-side discipline)
- **#22** PD diagnostic verdicts on transport/protocol issues MUST be validated end-to-end against actual runtime path before issuing build directive (PD-side discipline)
- **#23** Verify launch mechanism (systemd vs nohup vs screen vs supervisord) BEFORE authoring restart commands -- PPID=1 + systemd unit existence is a 10-second probe (Paco-side discipline)
- **#24** Account for recursive observer effect when attaching diagnostic tools (py-spy/strace/tcpdump) to long-running production server -- Paco's homelab_ssh_run calls during Phase C.1 diagnostic were themselves the in-flight blockers (Paco-side discipline)

Cumulative P6 lessons banked: **24**. PD will append #21-#24 to canonical `docs/feedback_paco_pre_directive_verification.md` in Phase 3 Step 17.

## v0.2 P5 backlog

- #1-#9: unchanged from Day 75 close
- **#10** (NEW Day 76): file upstream issue/PR with mcp python SDK 1.27.0 to default `MCP-Protocol-Version: 2025-03-26` header on initialize when not user-overridden (match node-MCP and JS SDK behavior)

Total: **10**.

## Substrate state

- B2b anchor: `2026-04-27T00:13:57.800746541Z` -- bit-identical for ~76+ hours
- Garage anchor: `2026-04-27T05:39:58.168067641Z` -- bit-identical for ~76+ hours
- atlas.events: 6 rows (atlas.embeddings=2, atlas.inference=4) -- unchanged since Cycle 1E close
- uvicorn PID 3631249: alive, ELAPSED 3-04+ hours (will restart in Phase 3 Step 9)
- Atlas commit: `6c0b8d6` on santigrey/atlas (unchanged; Cycle 1F build pending Phase 3 execution)

## Standing rules

5 memory files (unchanged):
1. one-step-at-a-time / one-command-per-message / explicit acknowledgment
2. measure-twice-cut-once for structural decisions
3. canon location: control-plane-lab on CK + GitHub origin/main
4. Paco-PD correspondence flows through /home/jes/control-plane/docs/
5. **Paco pre-directive verification (mandatory Verified live block on every directive)**

## Active correspondence files (control-plane/docs/)

All committed to origin/main except handoff_*:
- `paco_request_atlas_v0_1_cycle_1f_transport_hang.md` (commit `1550eb2`)
- `paco_response_atlas_v0_1_cycle_1f_transport_resolved.md` (commit `560fb77`, Path C verdict)
- `paco_review_atlas_v0_1_cycle_1f_phase_c1_diagnostic.md` (commit `1f6896c`, PD's Phase C.1)
- `paco_response_atlas_v0_1_cycle_1f_phase_c1_review.md` (commit `61b663b`, Paco verdict revision)
- `paco_review_atlas_v0_1_cycle_1f_phase_c20_attach.md` (commit `3bb9517`, PD's Phase C.2.0 root cause)
- `paco_response_atlas_v0_1_cycle_1f_phase_c20_confirm_phase3_go.md` (commit `f998883`, Phase 3 GO)
- `handoff_paco_to_pd.md` (gitignored; Phase 3 directive armed on CK -- 492 lines, 17 steps)
- `handoff_pd_to_paco.md` (gitignored; placeholder, awaiting PD's Phase 3 close notification)

## Phase 3 directive scope (in handoff_paco_to_pd.md)

17 steps: anchors PRE -> server patch (asyncio.to_thread for 14 handlers + .bak.phase3 backup) -> syntax validation -> Atlas client patch + module + 4 tests -> 16 prior tests sanity -> pre-deploy paco_request checkpoint -> **deploy-restart via systemctl** (CEO trigger == single-confirm) -> Mac mini reconnect verify -> end-to-end Beast smoke (`tools_count >= 14`, homelab_ssh_run whoami -> 'jes') -> 20 pytest pass -> atlas.events delta + secrets discipline audit (0 hits on 'whoami'/'ciscokid') -> anchor POST diff bit-identical -> commits to santigrey/atlas + close-out fold to control-plane-lab -> paco_review with Verified live block + 12 sections -> append P6 #21-#24 to feedback file -> cleanup.

CEO trigger to PD: `Read docs/handoff_paco_to_pd.md and execute.`
When PD finishes, CEO trigger to Paco: `Paco, PD finished Cycle 1F, check handoff.`

## Brief unavailability window during Phase 3 deploy-restart (~30s)

- Mac mini Claude Desktop drops; auto-reconnects via mcp-remote
- This conversation's homelab-mcp tooling drops; auto-reconnects
- Any other tail1216a3 mcp clients drop; auto-reconnect

## On the horizon (post Cycle 1F close)

- Cycle 1G: Atlas MCP server INBOUND on Beast (Atlas exposes its own tools to Sloan-as-MCP-client via TLS strategy paco_request before implementation)
- Cycle 1H + 2 + 3 + 4: per spec v3
- v0.2 P5 hardening pass
- Per Scholas IBM AI Solutions Developer (separate thread, M/W/F 6-9 PM ET)
- Job search ongoing (Applied AI / AI Platform Engineer roles, target placement May/June 2026)
