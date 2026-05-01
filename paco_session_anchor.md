# Paco Session Anchor

**Last updated:** 2026-05-01 UTC (Day 77)
**Anchor commit:** post-Cycle-1G-close on santigrey/control-plane-lab `main` (this turn's commit pending push)
**Resume Phrase:** "Day 77: Atlas Cycle 1G SHIPPED 5/5 PASS (control-plane-lab `c04a35d` + santigrey/atlas `2f2c3b7`). Atlas inbound MCP server operational at https://sloan2.tail1216a3.ts.net:8443/mcp. Cycle 1H entry-point dispatched as tool-surface paco_request gate at /home/jes/control-plane/docs/handoff_paco_to_pd.md. Awaiting CEO trigger to PD: 'Read docs/handoff_paco_to_pd.md and execute.' After PD writes paco_request, CEO triggers Paco: 'Paco, PD escalated, check handoff.'"

---

## Atlas v0.1 progression (post Cycle 1G close)

- **Cycle 1A** package skeleton: CLOSED (atlas commit `3e50a13`)
- **Cycle 1B** Postgres connection layer + atlas schema: CLOSED (atlas commit `42e41b7`)
- **Cycle 1C** Garage S3 client + bucket adoption: CLOSED (atlas commit `81de0b2`)
- **Cycle 1D** Goliath inference RPC + token telemetry: CLOSED (atlas commit `752134f`)
- **Cycle 1E** Embedding service mxbai-embed-large: CLOSED (atlas commit `6c0b8d6`)
- **Cycle 1F** MCP client gateway: CLOSED 5/5 PASS (atlas commit `5a9e458`)
- **Cycle 1G** Atlas MCP server INBOUND on Beast: **CLOSED 5/5 PASS** (atlas commit `2f2c3b7`; control-plane-lab `c04a35d`)
- **Cycle 1H** atlas-mcp tool surface: **NEXT (tool-surface paco_request gate dispatched)**
- **Cycles 1I + 2 + 3 + 4:** ahead per spec v3 (if applicable)

## Cycle 1G saga -- final tally

Multi-phase cycle: TLS strategy paco_request -> Option A ratified (Beast joins tailnet + Beast nginx + Tailscale FQDN cert mirroring CK pattern) -> 10 clean build steps -> Step 11 BLOCKER (uvicorn h11 Host validation rejecting nginx-forwarded `Host: sloan2.tail1216a3.ts.net` as 421 Misdirected Request) -> Paco spec error owned (handoff said "matches CK's pattern (loopback-bound)" but CK actually binds 0.0.0.0) -> Option A nginx Host rewrite to `127.0.0.1:8001` + X-Forwarded-Host enhancement ratified -> 5/5 PASS -> commits + close.
- 2 paco_requests + 2 paco_responses + 1 close confirm
- 1 spec error owned + corrected (P6 #28 banked from this)
- 2 P6 lessons banked (#27 carried from Cycle 1F + #28 NEW from Cycle 1G)
- 5 v0.2 P5 candidates banked (#16-#20)
- Anchors held bit-identical 96+ hours through entire saga
- Strict-loopback security posture stronger than CK's 0.0.0.0+UFW pattern (CK migrates to match in v0.2 P5 #20)

## Atlas inbound MCP -- operational state

- Endpoint: `https://sloan2.tail1216a3.ts.net:8443/mcp`
- Beast tailnet membership: `100.121.109.112 sloan2 james.3sloan@ linux`
- Tailscale-issued cert: `/etc/ssl/tailscale/sloan2.tail1216a3.ts.net.{crt,key}` (Let's Encrypt CN=E7, expires 2026-07-30)
- nginx vhost on Beast :8443 with strict-loopback Host rewrite to `127.0.0.1:8001` + X-Forwarded-Host preservation
- atlas-mcp.service Active running with FastMCP skeleton on `127.0.0.1:8001` loopback
- Tools exposed: 0 (skeleton; tool surface ratified in Cycle 1H)
- Smoke verified: HTTP 405 + `allow: GET, POST, DELETE` + `mcp-session-id` cookie + Python SDK INITIALIZE_OK
- Telemetry: source='atlas.mcp_server' contract pending Cycle 1H

## Cycle 1H entry-point

Atlas v0.1 Cycle 1H: atlas-mcp tool surface ratification (which tools the inbound server exposes; arg schemas; server-side ACL; telemetry contract).

**Architectural gate before implementation:** tool surface has scope dimension (Min-Viable / Standard / Full), argshape dimension (Pydantic-wrapped vs flat), ACL design dimension, telemetry contract dimension. Per measure-twice-cut-once, paco_request ratifies BEFORE build directive dispatches.

Handoff at `/home/jes/control-plane/docs/handoff_paco_to_pd.md` (gitignored, this turn) contains:
- Cycle 1G close acknowledgments (rulings on PD's 5 asks)
- Cycle 1H tool surface scope summary
- Verified live PRE capture commands (atlas schemas; CK mcp_server.py argshape per P6 #28; atlas.mcp_client ACL/telemetry references)
- 8-section paco_request structure
- P6 #26 notification format
- Step 4 commit/push

## P6 lessons banked

#21 tcpdump-on-lo / #22 PD validate end-to-end / #23 verify launch mechanism / #24 recursive observer / #25 hedge propagation / #26 handoff notification protocol / #27 telemetry intelligibility invariant / **#28 reference-pattern verification before propagation** (Cycle 1G NEW)

Cumulative P6 banked: **28**.

## v0.2 P5 backlog (22 items)

#10 mcp Python SDK upstream PR / #11 Beast SSH alias on CK / #12 pytest async test isolation / #13 telemetry isError reflection / #14 .bak.phase3 cleanup / #15 streamablehttp_client rename / #16 Beast tailnet side-effects / #17 nginx-vhost-mcp template macro / #18 except*/except syntax cleanup / #19 atlas.mcp_server startup-event hook / #20 CK migrate to 127.0.0.1 loopback / #21 P6 heading normalization (h2 vs h3 drift) / #22 Tailscale auth key residual confirmation (NEW Cycle 1G close)

## Substrate state

- B2b anchor: `2026-04-27T00:13:57.800746541Z` -- bit-identical 96+ hours
- Garage anchor: `2026-04-27T05:39:58.168067641Z` -- bit-identical 96+ hours
- atlas.events: embeddings=12, inference=14, mcp_client=6 (no atlas.mcp_server rows yet; startup hook deferred to v0.2 P5 #19)
- mcp_server.py on CK: 388 lines (Cycle 1F asyncio.to_thread patch); committed at `34838bd`
- uvicorn PID 3333714 on CK still running asyncio-wrapped code since 03:11:03 UTC
- Beast atlas-mcp.service running on 127.0.0.1:8001 (NEW from Cycle 1G)
- Beast nginx on :8443 fronting atlas-mcp (NEW from Cycle 1G)
- Beast Tailscale `sloan2` (NEW from Cycle 1G)
- Atlas package: HEAD `2f2c3b7` on santigrey/atlas; mcp_server/ skeleton shipped

## Standing rules

5 memory files (unchanged):
1. one-step-at-a-time / one-command-per-message / explicit acknowledgment
2. measure-twice-cut-once for structural decisions (Cycle 1H tool surface gate is direct application)
3. canon location: control-plane-lab on CK + GitHub origin/main
4. Paco-PD correspondence flows through /home/jes/control-plane/docs/
5. Paco pre-directive verification (mandatory Verified live block on every directive)

## CEO startup sequence (next turn)

1. CEO trigger to PD: `Read docs/handoff_paco_to_pd.md and execute.`
2. PD writes paco_request_atlas_v0_1_cycle_1h_tool_surface.md + commits + writes notification
3. CEO trigger to Paco: `Paco, PD escalated, check handoff.`
4. Paco rules on tool surface scope + argshape + ACL + telemetry
5. Paco dispatches Cycle 1H build directive
6. PD executes
7. Cycle 1H close: same flow as Cycles 1F/1G

**Pending CEO action (24-hour window):** confirm Tailscale auth key from Cycle 1G is consumed (one-time-use exhausted) or revoked via https://login.tailscale.com/admin/settings/keys -- per v0.2 P5 #22.
