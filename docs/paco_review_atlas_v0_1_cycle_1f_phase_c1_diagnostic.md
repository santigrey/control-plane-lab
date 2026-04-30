# Paco Review -- Atlas v0.1 Cycle 1F Phase C.1 Diagnostic

**Filed by:** PD
**Date:** 2026-04-30 (Day 76)
**Phase:** Cycle 1F Phase C.1 (read-only diagnostic probes)
**Status:** PASS, root cause located, recommendation: **Path C-fix** (pure Atlas code change, no infrastructure modification)

---

## Section 0 -- Verified live block (5th standing rule)

14 verifications run live; all evidence below from this session, not memory.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | B2b anchor StartedAt | `docker inspect` on Beast PRE | `2026-04-27T00:13:57.800746541Z` healthy r=0 |
| 2 | Garage anchor StartedAt | `docker inspect` on Beast PRE | `2026-04-27T05:39:58.168067641Z` healthy r=0 |
| 3 | atlas.events count PRE | `psql -U admin` on Beast | embeddings=2, inference=4 |
| 4 | uvicorn proc identity | `ps -eo` on CK | PID 3631249 `python3 /home/jes/control-plane/mcp_http.py` |
| 5 | uvicorn binds 0.0.0.0:8001 | mcp_http.py contents | `host='0.0.0.0', port=8001` |
| 6 | mcp_http.py source-of-truth | cat on CK | 6-line wrapper: imports `mcp_server.mcp` then `uvicorn.run(streamable_http_app(), ...)` |
| 7 | server mcp lib version | system `pip3 show mcp` on CK | 1.26.0 |
| 8 | client mcp lib version | atlas venv `pip show mcp` on Beast | 1.27.0 (skew vs server) |
| 9 | server self-report | P1.d.3 response body | `serverInfo: {name: 'homelab_mcp', version: '1.26.0'}` |
| 10 | /etc/hosts on Beast | `grep sloan3 /etc/hosts` | `192.168.1.10 sloan3.tail1216a3.ts.net` |
| 11 | mcp SDK on CK temp venv | `python -c 'import mcp; from mcp.client.streamable_http import streamablehttp_client'` | OK (Python 3.10.12) |
| 12 | tcpdump captured 62 pkts | tcpdump output | 62 captured / 124 received / 0 dropped |
| 13 | B2b anchor StartedAt POST | `docker inspect` on Beast POST | identical to PRE |
| 14 | Garage anchor POST | `docker inspect` on Beast POST | identical to PRE |
| 15 | atlas.events count POST | psql on Beast | embeddings=2, inference=4 (unchanged) |

Fifth in-session application of 5th standing rule was during the BLOCK report itself (filed `paco_request_atlas_v0_1_cycle_1f_transport_hang.md`). This Phase C.1 review is the sixth.

---

## Section 1 -- TL;DR

**Root cause:** FastMCP server `homelab_mcp v1.26.0` requires the HTTP request header `MCP-Protocol-Version: 2025-03-26` on the `initialize` request. Without it, the server holds the connection open indefinitely (10s curl cap, 15s python SDK cap, both observed). The python `mcp` SDK 1.27.0 used by Beast does NOT send this header on initialize. node-MCP from Mac mini sends it (or sent it on some prior init that established the now-cached session-id `7f103364...`).

**Fix surface area:** Single Atlas code change. Pass `headers={"MCP-Protocol-Version": "2025-03-26"}` to `streamablehttp_client(...)` in `atlas.mcp_client.client.McpClient`. **Zero infrastructure modification. No uvicorn restart. No nginx change. No Phase C.2 needed.**

---

## Section 2 -- Probe results table

| Probe | Command (short) | Outcome | Status |
|---|---|---|---|
| P1.a | Beast `.venv/bin/python` -> `streamablehttp_client('http://192.168.1.10:8001/mcp')` -> `session.initialize()` | TimeoutError after 15s | HANG (nginx bypassed -- nginx is innocent) |
| P1.b | CK `/tmp/mcp-diagnostic/bin/python` -> `streamablehttp_client('http://127.0.0.1:8001/mcp')` -> `session.initialize()` | TimeoutError after 15s | HANG (loopback source -- source-IP not the variable) |
| P1.c | tcpdump `-i lo 'tcp port 8001'` 60s + Beast trigger probe | 62 pkts captured | Headers extracted -- see Section 3 |
| P1.d.1 | curl POST 127.0.0.1:8001/mcp + Content-Type only | http_code=000 time=10.000 | HANG |
| P1.d.2 | curl P1.d.1 + `Accept: application/json, text/event-stream` | http_code=000 time=10.000 | HANG |
| P1.d.3 | curl P1.d.2 + `MCP-Protocol-Version: 2025-03-26` | http_code=200 time=9.97 (SSE stream filled the -m 10 budget) | **SUCCESS** |

---

## Section 3 -- Header comparison (P1.c)

Side-by-side from tcpdump capture of `lo:8001` (60s window, multi-packet POST /mcp requests).

| Header | node-MCP (Mac mini, 200 OK) | python-SDK (Beast, hangs) |
|---|---|---|
| `Host` | sloan3.tail1216a3.ts.net | sloan3.tail1216a3.ts.net |
| `X-Real-IP` | 100.102.87.70 (Tailscale) | 192.168.1.152 (LAN) |
| `Connection` | upgrade | upgrade |
| `Content-Length` | 283 / 264 / 333 | 152 |
| `mcp-session-id` | `7f103364f4ff44b3a34cb22fbc99d24a` (same on all 3 captured) | **MISSING** |
| `content-type` | application/json | application/json |
| `accept` | application/json, text/event-stream | application/json, text/event-stream |
| `accept-language` | `*` | absent |
| `sec-fetch-mode` | cors | absent |
| `user-agent` | node | python-httpx/0.28.1 |
| `accept-encoding` | br, gzip, deflate | gzip, deflate |
| `MCP-Protocol-Version` | **NOT VISIBLE in capture** (3 captured were post-init reuse traffic, not initialize) | **MISSING** |

**Critical asymmetry:** All 3 node-MCP requests captured carry the same `mcp-session-id` -- they are post-init reuse traffic, NOT a fresh initialize. We never observed a fresh node-MCP initialize during the capture window. So this comparison cannot directly observe whether node-MCP sends `MCP-Protocol-Version` on init. P1.d closed that gap by showing the header IS required by the server for fresh initialize regardless of client.

---

## Section 4 -- Hypothesis verdict

From the original paco_request Section 5:

| Hypothesis | Status | Evidence |
|---|---|---|
| 5.A Tailscale-bound listener | DISPROVEN | Paco verified `host='0.0.0.0'` in mcp_http.py before Phase C.1 |
| 5.B header difference python-SDK vs node-MCP | **PROVEN** | P1.d.3 shows `MCP-Protocol-Version: 2025-03-26` is the required header; without it, server hangs init |
| 5.C nginx Connection upgrade rewrite | DISPROVEN | P1.a hangs with no nginx in path |
| 5.D source-IP-aware uvicorn behavior | DISPROVEN | P1.b hangs from loopback (127.0.0.1 source) -- same as P1.a from LAN |

The failure mode is purely client-side: python SDK 1.27.0 does not include the `MCP-Protocol-Version` header on the initialize request that FastMCP 1.26.0 server expects. This is a known impedance between SDK versions; not an infrastructure defect.

---

## Section 5 -- Recommendation to Paco

**Path C-fix.** Pure Atlas code change. Zero infrastructure modification. No Sloan double-confirm needed for nginx/uvicorn/Tailscale (none touched).

Proposed change to `atlas.mcp_client.client.McpClient`:

```python
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

DEFAULT_MCP_URL = "https://sloan3.tail1216a3.ts.net:8443/mcp"
MCP_PROTOCOL_VERSION = "2025-03-26"

class McpClient:
    def __init__(self, url: str = DEFAULT_MCP_URL):
        self._url = url
        self._headers = {"MCP-Protocol-Version": MCP_PROTOCOL_VERSION}

    @asynccontextmanager
    async def session(self):
        async with streamablehttp_client(self._url, headers=self._headers) as (r, w, _):
            async with ClientSession(r, w) as session:
                await session.initialize()
                yield session
```

**Verification path:** atlas.mcp_client smoke against `https://sloan3.tail1216a3.ts.net:8443/mcp` from Beast should now return `INITIALIZE_OK` + `tools_count > 0` matching the server's actual tool list.

**Why not Phase C-deeper / Phase C.2:** Root cause already identified at the protocol header layer. uvicorn debug logs would not add information beyond what P1.d already showed (the server clearly accepts the header when present). No need to restart uvicorn or risk substrate touch.

**Why not Path B-escalate:** Root cause is upstream-fixable in a single client-side line. New nginx vhost on :8002 is unnecessary architecture spread.

**Suggested follow-up (optional, v0.2 scope):**
- File upstream issue/PR with `mcp` python SDK 1.27.0: streamablehttp_client should default `MCP-Protocol-Version` header on initialize if not user-overridden (match node-MCP and JS SDK behavior).
- Bank a P6 lesson: when client-server impedance hangs initialize, capture both sides' headers via tcpdump on `lo` -- 5-minute root-cause vs hours of speculation.

---

## Section 6 -- Anchor preservation evidence

```
--- PRE (Step 0) ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- POST (Step Z) ---
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0

--- diff ---
ANCHORS-BIT-IDENTICAL
```

**B2b nanosecond anchor and Garage S3 anchor held bit-identical through all 4 probes + cleanup.** Substrate invariant maintained -- ~76+ hours since Day 71 establishment.

Atlas events delta:
```
--- PRE ---
atlas.embeddings | 2
atlas.inference  | 4

--- POST ---
atlas.embeddings | 2
atlas.inference  | 4

--- delta = 0 (no Atlas writes during diagnostic) ---
```

---

## Section 7 -- Cleanup confirmation

On CiscoKid:
- `/tmp/mcp-diagnostic` -- removed (rm -rf)
- `/tmp/mcp_capture.pcap` -- removed (sudo rm -f, file was tcpdump-owned)
- `/tmp/mcp_p1c_orchestration.log` -- removed
- `/tmp/mcp_p1b_install.log` -- removed
- `/tmp/atlas_1f_p1b.py` -- removed
- `/tmp/atlas_1f_p1d.sh` + `.log` -- removed
- `/tmp/atlas_1f_p1b.log` -- removed
- Verification: `ls /tmp/ | grep -iE 'mcp_capture|mcp-diagnostic|atlas_1f'` -> NONE

On Beast (per directive, /etc/hosts entry stays; diagnostic scratch in /tmp left as-is):
- `/etc/hosts` `192.168.1.10 sloan3.tail1216a3.ts.net` -- INTACT (per directive)
- `/tmp/atlas_1f_phaseC1_anchors_pre.txt` + `_post.txt` -- left for next-session reference
- `/tmp/atlas_1f_p1a.py` + `.log` -- left (Beast scratch, no spec mandate to remove)
- `/tmp/atlas_1f_p1c_trigger.py` -- left (Beast scratch, no spec mandate to remove)

No system packages installed on either node. No persistent state changes.

---

## Section 8 -- Cross-references

- **paco_request:** `docs/paco_request_atlas_v0_1_cycle_1f_transport_hang.md` (commit `1550eb2`)
- **paco_response:** `docs/paco_response_atlas_v0_1_cycle_1f_transport_resolved.md` (commit `560fb77`)
- **handoff that authorized this phase:** `docs/handoff_paco_to_pd.md` at commit `560fb77` (cleared post-read per directive)
- **this paco_review:** `docs/paco_review_atlas_v0_1_cycle_1f_phase_c1_diagnostic.md`
- **canonical spec:** `tasks/atlas_v0_1.md` v3 section 8.1F (commit `93b97e6`)
- **Atlas package state:** unchanged from Cycle 1E close (commit `6c0b8d6` on `santigrey/atlas`); no Atlas code written this phase.

---

## Section 9 -- Phase 3 dispatch readiness

Ready for Paco to issue Phase 3 fix directive:
- atlas.mcp_client module sketch (acl.py + client.py + __init__.py) per original Cycle 1F handoff
- Pass `headers={"MCP-Protocol-Version": "2025-03-26"}` to `streamablehttp_client(...)` in client.py
- All other Cycle 1F gates (4 tests, 5 acceptance gates, atlas.events token logging, Beast anchor diff, secrets discipline audit) unchanged from original handoff

No close-out fold this turn; the open block stays open until Phase 3 fix lands.
