# Paco Session Anchor

**Last updated:** 2026-04-30 (Day 76)
**Anchor commit:** TBD (this Cycle 1F BLOCK + paco_request commit)
**Resume Phrase:** "Day 76: Atlas Cycle 1F BLOCKED at Step 3 connectivity smoke. paco_request `_transport_hang.md` filed. Beast LAN-source POSTs to /mcp hang via nginx; Tailscale-source POSTs from Mac mini work. Awaiting Paco verdict on Path A/B/C/D."

---

## Atlas v0.1 progression

- **Cycle 1A** package skeleton: CLOSED (atlas commit `3e50a13`)
- **Cycle 1B** Postgres connection layer + atlas schema: CLOSED (atlas commit `42e41b7`)
- **Cycle 1C** Garage S3 client + bucket adoption: CLOSED (atlas commit `81de0b2`)
- **Cycle 1D** Goliath inference RPC + token telemetry: CLOSED (atlas commit `752134f`)
- **Cycle 1E** Embedding service mxbai-embed-large: CLOSED 5/5 PASS Day 75 (atlas commit `6c0b8d6`)
- **Cycle 1F MCP client gateway:** BLOCKED at Step 3 (Day 76). paco_request filed.
- **Cycles 1G-1H + 2 + 3 + 4:** ahead per spec v3

## Cycle 1F BLOCK summary

Step 3 connectivity smoke from Beast against `https://sloan3.tail1216a3.ts.net:8443/mcp`:
- Transport opens (TCP+TLS+POST handshake): OK
- `session.initialize()` hangs indefinitely; client times out at 15s
- Replicated with raw curl POST -> identical hang
- Same MCP server serves Mac mini Tailscale clients fine (23x 200 in last 30 nginx entries)
- Beast LAN clients: 4x 499 0 in nginx access log
- Hypothesis: Tailscale-vs-LAN source asymmetry in FastMCP/nginx stack

Path options for Paco (full diagnostic in `docs/paco_request_atlas_v0_1_cycle_1f_transport_hang.md`):
- A: Install Tailscale on Beast (cleanest match to working topology)
- B: LAN-internal nginx vhost on :8002 (pragmatic, adds unauthenticated LAN endpoint)
- C: FastMCP/uvicorn debug-logged restart (fastest if root cause is fixable in config)
- D: stdio transport via SSH (architectural change to atlas.mcp_client)

## Substrate -- HOLDING through Cycle 1F BLOCK

- B2b nanosecond anchor: `2026-04-27T00:13:57.800746541Z` -- holding ~76+ hours
- Garage anchor: `2026-04-27T05:39:58.168067641Z` -- holding
- B2b subscription `controlplane_sub`: untouched
- Garage cluster: unchanged
- atlas.events delta during Cycle 1F attempt: 0 (no inference/embed calls)

## Atlas package state (Beast `/home/jes/atlas/`)

- src/atlas/db/ (Cycle 1B)
- src/atlas/storage/ (Cycle 1C)
- src/atlas/inference/ (Cycle 1D)
- src/atlas/embeddings/ (Cycle 1E)
- src/atlas/mcp_client/ -- NOT YET CREATED (waiting on Paco verdict)
- ~28 source/test files in repo
- Latest commit: `6c0b8d6`

## atlas.events state (cumulative, unchanged from Cycle 1E close)

- 6 rows total
- 4 from atlas.inference
- 2 from atlas.embeddings
- 0 from atlas.mcp_client (cycle blocked before any tool call)

## CK MCP server state (verified live during Cycle 1F diagnostic)

- nginx :8443 LISTEN (PID 849xxx workers)
- mcp_http.py PID 3631249 -- uvicorn 0.0.0.0:8001
- mcp_server.py = FastMCP, no auth middleware, ALLOWED_HOSTS dict for tool args only
- /etc/nginx/sites-enabled/mcp: location /mcp -> 127.0.0.1:8001/mcp with `Connection "upgrade"` rewrite
- TLS cert SAN: DNS:sloan3.tail1216a3.ts.net (matches via /etc/hosts override)

## Beast state changes during Cycle 1F

- /etc/hosts entry added: `192.168.1.10 sloan3.tail1216a3.ts.net` (revertable; one line)
- /tmp/atlas_mcp_smoke.py + /tmp/atlas_mcp_smoke.log left for diagnostic; not committed
- atlas package: NO new files written (cycle blocked before module authoring)

## Standing rules: 5 memory files (unchanged)

## P6 lessons banked: 20 (unchanged -- new lesson candidate from Cycle 1F BLOCK pending Paco verdict)

## v0.2 hardening pass queue: 9 items (unchanged)

## On resume

1. Paco picks A | B | C | D and re-issues Cycle 1F handoff
2. PD executes the chosen approach
3. Continue through Cycle 1F module + tests, then 1G-1H + 2 + 3 + 4

## Notes for Paco

- Hard-rules guardrails held: no nginx mods, no cert tampering, no token improv, no MCP server restart, no Tailscale install on Beast
- Diagnostic completeness: TCP/TLS/HTTP/server/config/source-IP differential all captured before HALT
- 5th standing rule (Verified live) was followed pre-execution -- identified the /etc/hosts requirement before Step 1 and confirmed SAN match before Step 3
- The hang is NOT a 401, so spec-named `_auth.md` was not used; PD-named `_transport_hang.md` describes actual symptom
