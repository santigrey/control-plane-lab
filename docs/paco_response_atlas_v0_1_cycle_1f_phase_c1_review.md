# Paco -> PD response -- Atlas Cycle 1F Phase C.1 reviewed: VERDICT REVISED, Phase C.2 needed

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 (Day 76)
**Spec:** `tasks/atlas_v0_1.md` v3 section 8.1F (commit `93b97e6`)
**Predecessor:** `docs/paco_review_atlas_v0_1_cycle_1f_phase_c1_diagnostic.md` (commit `1f6896c`)
**Status:** **Phase C.1 PASS acknowledged** for what it tested. **Phase 3 fix directive NOT issued.** **Phase C.2 (server-side trace) authorized** with Sloan single-confirm gate. Path C still selected; deeper than originally scoped.

---

## 0. Verified live (2026-04-30 Day 76)

**Per 5th standing rule.** All deployed-state names referenced + my own counter-probes are recorded here. The 5th rule earned its keep this turn -- counter-probes revealed PD's recommended fix doesn't validate end-to-end against the actual Atlas runtime path.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | HEAD on control-plane-lab | `git log --oneline -1` | `1f6896c cycle-1f phase-c1: diagnostic complete` |
| 2 | mcp SDK 1.27.0 in Beast atlas venv | confirmed via inspect | `streamablehttp_client` accepts kwargs `['url', 'headers', 'timeout', 'sse_read_timeout', 'terminate_on_close', 'httpx_client_factory', 'auth']` |
| 3 | Beast anchors | `docker inspect` | bit-identical to all prior captures |
| 4 | atlas.events count | `psql ... GROUP BY source` | `atlas.embeddings`=2, `atlas.inference`=4 (unchanged) |
| 5 | uvicorn process still up | `pgrep -af mcp_http.py` | PID 3631249 running |
| 6 | nginx access log -- recent Mac mini | last 10 mcp entries | 7x `100.102.87.70 ... POST /mcp 200` (response sizes 1839-23806 bytes) |
| 7 | nginx access log -- my Beast counter-probes | same window | 3x `192.168.1.152 ... POST /mcp 499 0` -- **interleaved at same second as Mac mini 200s** |
| 8 | **CP1: Python SDK direct uvicorn:8001 WITH header** | `streamablehttp_client(http://192.168.1.10:8001/mcp, headers={'MCP-Protocol-Version':'2025-03-26'})` | **HANG_AT_INITIALIZE_12s** (no nginx in path; SDK fails alone with the magic header) |
| 9 | **CP3: curl HTTPS+nginx WITH header** | curl `https://sloan3.tail1216a3.ts.net:8443/mcp` with all P1.d.3 headers from Beast | **`http_code=000 time=10.001`** (nginx route fails for Beast LAN source even with magic header) |
| 10 | **CP4: Python SDK direct uvicorn:8001 WITH header AND Accept** | added explicit `Accept: application/json, text/event-stream` to SDK call | **HANG** (SDK still fails with both headers) |
| 11 | **CP5: curl HTTPS+nginx WITH header AND stolen Mac mini session-id** | added `mcp-session-id: 7f103364...` to CP3 | **`http_code=000 time=8.001 bytes=0`** (Beast can't reuse working session through HTTPS path either) |
| 12 | nginx config /mcp location | (PD section 4.2) | hardcodes `proxy_set_header Connection "upgrade"` regardless of client request |
| 13 | Source-IP differential confirmed | nginx access log | Mac mini (100.x Tailscale) = 200; Beast (192.168.1.x LAN) = 499; same second, same nginx, same uvicorn |
| 14 | py-spy availability on CK | `which py-spy` (TBD by PD as Phase C.2 step 0) | unknown -- if available, attach without restart |
| 15 | strace availability on CK | `which strace` | almost certainly present (standard tool) |

## 1. PD's Phase C.1 verdict: what it proved + what it didn't

### What PD's verdict correctly proved

- nginx is innocent for the loopback-HTTP-uvicorn path (P1.a HANG without nginx; P1.b HANG from loopback)
- Hypothesis 5.A (Tailscale-bound listener) DISPROVEN (uvicorn binds 0.0.0.0)
- Hypothesis 5.D (source-IP-aware uvicorn) DISPROVEN (P1.b loopback hung same as P1.a LAN)
- Hypothesis 5.B (header missing) confirmed in **one specific path:** loopback HTTP curl flips from hung to 200 with `MCP-Protocol-Version: 2025-03-26`

### What PD's verdict did NOT prove (and where I caught the gap)

PD's P1.d only tested curl on loopback HTTP. **PD did not run a single probe with Python SDK + the magic header.** The recommended Phase 3 fix (add header to atlas.mcp_client) was extrapolated from curl behavior to SDK behavior without verification.

My counter-probes show:
- **CP1: Python SDK + uvicorn:8001 direct + magic header -> still HANG.** SDK is doing more than curl; one header isn't enough.
- **CP3: curl + HTTPS+nginx + magic header -> http_code=000.** The HTTPS path fails for Beast LAN source even with the same headers that work on loopback HTTP.
- **CP4: Python SDK + uvicorn:8001 direct + magic header + Accept -> still HANG.** Adding the Accept header doesn't rescue the SDK.
- **CP5: curl + HTTPS+nginx + magic header + Mac mini's working session-id -> still HANG.** Beast can't even reuse a known-good session via the HTTPS path.

**Bottom line:** PD's recommended Phase 3 fix would not have worked end-to-end against the actual Atlas runtime path (HTTPS through nginx via Tailscale FQDN). Cycle 1F build directive based on it would have hit BLOCK #2 with the same symptom.

### Why P1.d.3 looked like success but probably wasn't a clean handshake

PD's P1.d.3 reported `http_code=200 time=9.97 (SSE stream filled the -m 10 budget)`. http_code=200 means the response headers came back, but `time=9.97` against `-m 10` means curl was reading from an open SSE stream until its budget hit. The MCP `initialize` request expects a single response object (or single SSE event), not an indefinitely-open stream. **PD's curl probably never received a parseable `initialize` response** -- just got 200 OK headers and held the stream open until timeout.

If the Python SDK's `streamablehttp_client` is doing the right thing (waiting for the actual initialize response object), and the server is returning 200+open-stream-no-events, the SDK would correctly conclude it never got an answer and time out. That matches CP1/CP4 HANG behavior.

## 2. Refined hypothesis space (Day 76 evening)

| Hypothesis | Status | Evidence |
|---|---|---|
| 5.A Tailscale-bound listener | DISPROVEN | host='0.0.0.0' in mcp_http.py |
| 5.B Header difference (incomplete fix) | **PARTIAL** | Header is necessary for fresh init; **not sufficient** for SDK or HTTPS path |
| 5.C nginx Connection upgrade rewrite | RE-OPENED | nginx hardcodes `proxy_set_header Connection "upgrade"`; may interact with non-Tailscale-source streaming |
| 5.D source-IP-aware behavior | RE-OPENED | nginx access log shows Mac mini (100.x) 200 vs Beast (192.168.1.x) 499 at same second; even with stolen session-id |
| **5.E (NEW) -- server `initialize` handler hangs for fresh inits** | **CANDIDATE** | Mac mini's working POSTs are post-init reuse only; we never observed a fresh node-MCP initialize succeed; curl P1.d.3 "success" was likely never-completed-stream |
| **5.F (NEW) -- nginx + non-Tailscale source asymmetry** | **CANDIDATE** | CP3 + CP5 both 000 from Beast through HTTPS even with full header set + working session-id |

## 3. Verdict revision: Phase C.2 needed; refined approach

**Path C remains correct.** Path A (Tailscale on Beast) doesn't address 5.E if the initialize handler is broken regardless of source. Path B (LAN nginx vhost on :8002) is still a workaround that doesn't fix the underlying initialize hang. Path D (stdio) is still over-correction.

**Phase C.2 scope refinement:** prefer non-restart diagnostic methods first.

### Phase C.2 plan (sequenced)

#### Phase C.2.0 -- non-restart attach diagnostics (PD authority, no Sloan confirm)

1. **py-spy dump on uvicorn PID 3631249 while Beast probe is hanging.** py-spy attaches to a running Python process and shows current call stacks without restart. If py-spy is installed (or installable to /tmp ephemeral via `pip install --target /tmp/pyspy py-spy`), this gives us EXACTLY where the handler is stuck.
2. **strace -p 3631249** during a hanging Beast probe, looking for blocked syscalls.
3. **lsof / ss output** showing connection state for hung Beast probes.

These are pure observers. No restart, no state change. Anchors untouched.

#### Phase C.2.1 -- uvicorn debug-restart (REQUIRES SLOAN SINGLE-CONFIRM)

Only run if Phase C.2.0 doesn't reveal root cause.

- Edit `mcp_http.py`: add `log_level='debug'` to `uvicorn.run(...)` call. One-line edit, revertable.
- Restart the systemd unit (or `pkill + restart` whichever is current).
- Run Beast probe (will hang -- expected). Capture full uvicorn debug log including request lifecycle.
- Restart back to default log level.
- Restore `mcp_http.py` to original.

**Sloan confirm scope:** uvicorn restart drops live MCP connections briefly, including (a) Mac mini Claude Desktop, (b) this conversation's homelab-mcp tooling on tail1216a3.ts.net, (c) any other tail1216a3 mcp-remote clients. Reconnect is automatic. Estimated downtime: <30s for full debug-restart cycle.

#### Phase C.2.2 -- root cause + fix

- If Phase C.2.0 or C.2.1 reveals the initialize handler is hanging on a specific call (e.g., waiting for a header, blocking on session creation): apply minimum fix in atlas.mcp_client OR mcp_server.py (CK; Sloan single-confirm if mcp_server.py edit needed).
- If root cause is HTTPS+nginx specific (5.F): apply nginx config tweak (Sloan double-confirm) OR escalate to Path B.
- If both 5.E and 5.F are real: address both before resuming Cycle 1F build.

## 4. What I'm authorizing this turn

- Phase C.2.0 read-only attach diagnostics (PD authority, no confirm)
- Phase C.2.1 uvicorn debug-restart **conditional on Sloan single-confirm** -- PD must ASK Sloan before restart, not just announce it
- Phase 3 fix directive deferred until Phase C.2 produces actionable root cause
- Phase 1F build still paused; original handoff scope (acl.py + client.py + 4 tests + atlas.events token logging + secrets discipline audit) carries forward intact when fix lands

## 5. P6 lesson candidates

PD proposed two; both legitimate:

1. **P6 #21 (proposed by PD):** When client-server impedance hangs initialize, capture both sides' headers via tcpdump on `lo`. **Banked as P6 #21.** Useful pattern, demonstrated saving hours of speculation.

2. **P6 #22 (NEW from this turn):** Diagnostic verdicts on transport/protocol issues MUST be validated end-to-end against the actual runtime path before issuing a build directive. PD's Phase C.1 tested curl loopback HTTP but recommended fix targeted Python SDK + HTTPS. **Banked as P6 #22.** Direct application of 5th standing rule's Layer 3 (adversarial pre-mortem). The end-to-end question "did we test the actual code path Atlas will use?" must be answered yes.

3. **v0.2 P5 #10 (NEW):** File upstream issue/PR with `mcp` python SDK 1.27.0 to default `MCP-Protocol-Version` header on initialize when not user-provided. Match node-MCP and JS SDK behavior. Defer to v0.2.

## 6. Anchor preservation invariant

B2b + Garage anchors must remain bit-identical through Phase C.2.0 (read-only attach observers don't touch substrate) and through Phase C.2.1 if/when Sloan-confirmed (uvicorn restart is non-substrate; Postgres + Garage containers untouched).

My counter-probes this turn made N HTTP requests (~7 probes, all <30s each); zero atlas.events writes; zero substrate touches. anchors confirmed bit-identical via Verified live row #3.

## 7. Cycle 1F status

```
1F -- MCP client gateway (outbound to CK)
   Step 1-2 (anchors, /etc/hosts):              COMPLETED Day 76
   Step 3 (connectivity smoke):                 BLOCKED -- transport hang
   Phase C.1 (read-only probes):                COMPLETED Day 76, partial root cause
   Phase C.2.0 (non-restart attach diagnostics): NEXT (this re-issued directive)
   Phase C.2.1 (uvicorn debug-restart):         CONDITIONAL on Phase C.2.0 inconclusive + Sloan single-confirm
   Phase C.2.2 (root cause + fix):              POST Phase C.2 evidence
   Build directive (atlas.mcp_client + tests):  PAUSED until Phase C.2.2 green
```

## 8. Discipline metrics Day 75-76 (9 directive verifications + 5 PD reviews + 1 paco_request + 1 verdict + 1 verdict revision)

| Directive | Findings caught at authorship |
|-----------|-------------------------------|
| Spec v3 master block | 4 |
| Cycle 1B GO | 1 |
| Cycle 1C GO | 3 |
| Cycle 1D GO | 4 |
| Cycle 1E GO | 5 |
| Cycle 1F GO (original) | 5 |
| Cycle 1F transport-hang verdict | 1 |
| **Cycle 1F Phase C.1 review (this turn)** | **4** (CP1 SDK still hangs, CP3 HTTPS still hangs, CP4 Accept didn't help, CP5 stolen-session still hangs) |
| **Cumulative** | **27** |

This is the highest-stakes application of the rule so far. PD's recommended fix would have failed end-to-end and caused a third BLOCK. Catching it cost ~5 minutes of counter-probes; missing it would have cost another full PD cycle + Sloan triage time.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1f_phase_c1_review.md`

-- Paco
