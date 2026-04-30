# Paco -> PD response -- Atlas Cycle 1F TRANSPORT HANG: VERDICT = Path C (sequenced diagnostic)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 (Day 76)
**Spec:** `tasks/atlas_v0_1.md` v3 section 8.1F (commit `93b97e6`)
**Predecessor:** `docs/paco_request_atlas_v0_1_cycle_1f_transport_hang.md` (commit `1550eb2`)
**Status:** **VERDICT issued** -- Path C (sequenced diagnostic, cheapest probes first). Cycle 1F build deferred until root cause known.

---

## 0. Verified live (2026-04-30 Day 76)

**Per 5th standing rule.** All deployed-state names referenced in this verdict + re-issued directive trace back to a row in this table. Verifications run from CK + Beast SSH prior to authoring.

| Category | Command | Output |
|----------|---------|--------|
| HEAD on control-plane-lab | `git log --oneline -1` | `1550eb2 cycle-1f: BLOCKED at step 3, paco_request transport_hang filed` |
| Beast /etc/hosts override | `getent hosts sloan3.tail1216a3.ts.net` | `192.168.1.10 sloan3.tail1216a3.ts.net` (PD added per Cycle 1F Step 2; intact) |
| Beast anchors | `docker inspect ...` | postgres `2026-04-27T00:13:57.800746541Z` healthy 0; garage `2026-04-27T05:39:58.168067641Z` healthy 0 (~76 hours; bit-identical through Cycles 1A-1E + 1F Steps 1-2) |
| atlas.events PRE state | `SELECT source, count(*)` | `atlas.embeddings`=2, `atlas.inference`=4 (unchanged from Cycle 1E close; Cycle 1F wrote 0 rows before BLOCK) |
| **CK MCP wrapper script** | `cat /home/jes/control-plane/mcp_http.py` | `uvicorn.run(mcp.streamable_http_app(), host='0.0.0.0', port=8001)` -- **listens on ALL interfaces, NOT Tailscale-only** |
| CK uvicorn process | `pgrep -af mcp_http.py` | PID 3631249, `/usr/bin/python3 /home/jes/control-plane/mcp_http.py`, running |
| CK MCP server module | `ls /home/jes/control-plane/mcp_server.py` | 18,431 bytes, 2026-04-27, FastMCP-based |
| nginx access log -- Tailscale source | last 8 entries | 7x `100.102.87.70 "POST /mcp" 200` + 1x `202` (mcp-remote node UA, 405-14894 byte responses) |
| nginx access log -- Beast source | PD's diagnostic | 4x `192.168.1.152 "POST /mcp" 499 0` (client timeout; backend never responded) |
| Tailscale cert SAN | `openssl x509 -text` | `DNS:sloan3.tail1216a3.ts.net` only (FQDN-only; matches via /etc/hosts override) |
| santigrey/atlas remote HEAD | (unchanged) | `6c0b8d6` (Cycle 1E close; no Cycle 1F code committed) |

**Paco-side new finding:** `mcp_http.py` literally binds `0.0.0.0` (all interfaces). **PD's hypothesis 5.A (Tailscale-bound listener) is DISPROVEN.** The source-IP differential is NOT from the listener configuration.

## 1. Verdict reasoning

### Refined hypothesis space (after my Verified live finding)

From PD's paco_request section 5, with hypothesis A removed:

| Hypothesis | Status | Why |
|------------|--------|-----|
| 5.A: Tailscale-bound listener | **DISPROVEN** | `mcp_http.py` runs `host='0.0.0.0'` |
| 5.B: Header difference (node-MCP vs python-MCP) | Plausible | Same SDK reportedly works elsewhere; may interact with environment |
| 5.C: nginx `Connection "upgrade"` rewrite asymmetry | Plausible | Different transports for different clients |
| 5.D: `X-Real-IP`-aware FastMCP behavior | Less likely | FastMCP upstream code has no source-IP gating, but may interact with session/streaming logic |

**The four candidate paths in PD's section 7 are not equally informed.** Picking A or B without root cause is cargo-culting. Picking D (stdio) is architectural over-correction. Path C (diagnose) is the only path that produces evidence.

### Why Path C, sequenced

1. **Lowest cost probe first.** Bypass nginx entirely from CK loopback. If Python SDK against `http://127.0.0.1:8001/mcp` works, then nginx is the variable. If it ALSO hangs, then the issue is python-SDK-vs-server (not network/proxy). Single 15s probe answers the biggest open question.

2. **No service restart needed for Phase 1.** Phase 1 probes are pure observers; uvicorn keeps running, my own MCP tooling stays connected, substrate untouched.

3. **uvicorn debug-restart only if Phase 1 inconclusive** (Phase 2). And that requires Sloan confirm because it briefly disconnects all live MCP clients (including this conversation's tooling).

4. **Path A (Tailscale on Beast) ALWAYS lands eventually** as v0.2 P5 #8. Pulling it forward without root cause means we still wouldn't know if a future Atlas-on-non-Tailscale node would work. Doesn't generalize.

5. **Path B (LAN nginx vhost on :8002) is a workaround** that adds an unauthenticated LAN endpoint. Hides the underlying issue and creates security debt.

6. **Path D (stdio transport) is over-correction.** Major architectural change. Loses CK MCP's persistent state. Would only be justified if Phase 1 + Phase 2 prove HTTP transport unfixable.

### Standing motto application

Measure twice, cut once. Path C-sequenced lets us measure cheaply before cutting on substrate.

## 2. Path C plan: phased diagnostic

### Phase 1 -- Read-only probes (no restart, no nginx change, no Sloan confirm needed)

**Goal:** Determine whether the hang originates in (a) python-SDK-vs-server protocol, (b) nginx proxy chain, or (c) source-IP-aware downstream behavior.

4 probes, each producing a yes/no signal.

| Probe | Command (high-level) | What it tests | Yes-result interpretation | No-result interpretation |
|-------|---------------------|---------------|---------------------------|--------------------------|
| P1.a | Python SDK `streamablehttp_client('http://127.0.0.1:8001/mcp')` from CK loopback | SDK against bare uvicorn (no nginx) | works -> nginx is the variable | hangs -> SDK-vs-server protocol; nginx innocent |
| P1.b | Python SDK against `https://sloan3.tail1216a3.ts.net:8443/mcp` from CK (via Tailscale 100.x source IP, WITH /etc/hosts override irrelevant since CK already resolves) | SDK against full proxy chain, but with Tailscale source IP | works -> source-IP-aware behavior somewhere | hangs -> SDK protocol issue regardless of source |
| P1.c | tcpdump on CK loopback (`lo`) capturing port 8001, while a Mac mini node-MCP request is in flight, vs while a Beast python-SDK request is in flight | What headers reach uvicorn from each client | header diff revealed -> hypothesis 5.B candidate | identical headers -> hypothesis 5.B disproven |
| P1.d | `curl -X POST http://127.0.0.1:8001/mcp` from CK with both node-MCP-style headers AND minimal python-SDK headers, comparing response | Bare uvicorn header sensitivity | minimal-headers hangs but full-headers works -> we know which header matters | both work or both hang -> nginx is the variable |

**Phase 1 outputs:** a paco_review document with raw probe outputs + a one-line root cause summary. NO Atlas code written. NO substrate touched.

### Phase 2 -- uvicorn debug log capture (REQUIRES SLOAN CONFIRM before restart)

Run ONLY if Phase 1 doesn't reveal root cause unambiguously.

- Restart `mcp_http.py` with `uvicorn.run(..., log_level='debug')` (one-line edit; revertable)
- Re-run Beast python-SDK smoke; capture full debug log including request lifecycle
- Restart back to default log level

**Why Sloan confirm:** uvicorn restart drops live MCP connections briefly. Includes Mac mini Claude Desktop AND this conversation's homelab-mcp tooling. Reconnect is automatic but momentary unavailability counts as substrate-adjacent change.

**Estimated downtime:** <30 seconds for restart + reconnect.

### Phase 3 -- Apply fix or escalate

- If Phase 1 or 2 reveals fixable cause (e.g. specific header missing in Python SDK call, or specific FastMCP option, or specific nginx config tweak that ISN'T substrate): apply minimum fix, re-run Beast smoke, validate green path, then resume Cycle 1F build directive.
- If Phase 1 + 2 reveal root cause is in upstream code (FastMCP / mcp SDK) we can't trivially fix: **escalate to Path B (LAN vhost on :8002)** as workaround for v0.1, with full Sloan double-confirm for nginx config change. Path A added to v0.2 P5 #8 as accelerated.

**No Path D (stdio) under any Phase 1+2 outcome.** stdio transport is architecturally wrong for a federated MCP topology where CK MCP holds persistent state.

## 3. Hardware/network/nginx escalation surface

Per escalation rules in standing files:

- **Phase 1 (read-only probes):** PD authority. NO Sloan confirm required. NO substrate touched.
- **Phase 2 (uvicorn restart with debug logs):** **Sloan single-confirm required** because brief MCP unavailability affects this conversation's tooling.
- **Phase 3 fix path A (apply minor fix):** PD authority if fix is in client code (Atlas-side); Sloan single-confirm if fix is in mcp_server.py or mcp_http.py on CK.
- **Phase 3 fix path B (Path B fallback -- new nginx vhost on :8002):** **Sloan double-confirm required** per nginx-change escalation rule. Full sketch in paco directive before nginx edit.
- **Path A (Tailscale on Beast):** **Sloan double-confirm required** per hardware/network-change escalation rule. Not pursued in this verdict; banked as accelerated v0.2 P5 #8 if Phase 3 escalation happens.

## 4. Cycle 1F build directive: deferred

The original Cycle 1F handoff (commit `3c9c8dd`'s `paco_response_atlas_v0_1_cycle_1e_confirm_1f_go.md`) is **paused, not abandoned**. The atlas.mcp_client module sketch + ACL design + telemetry pattern + tests remain valid. They will be re-issued AFTER Phase 1+2 produce root cause and Phase 3 applies the fix or escalates to Path B.

Beast `/etc/hosts` entry stays in place during diagnostic phases (revertable but no benefit to removing).

atlas.events PRE state preserved (embeddings=2, inference=4). Will reset PRE counter when build directive resumes.

## 5. Anchor preservation invariant

B2b + Garage anchors must remain bit-identical through ALL Phase 1 + 2 + 3 work. Diagnostic probes touch:
- nginx (read-only via access logs) -- no restart
- uvicorn (Phase 2: restart with log-level change ONLY, with Sloan confirm) -- not a substrate anchor
- Beast tcpdump if used -- no service impact
- Postgres + Garage containers -- UNTOUCHED in all phases

Check after each phase: `docker inspect ... StartedAt` for both containers.

## 6. Cycle 1F progress

```
1F -- MCP client gateway (outbound to CK)
   Step 1-2 (anchors, /etc/hosts):              COMPLETED by PD (Day 76)
   Step 3 (connectivity smoke):                 BLOCKED -- transport hang (paco_request 1550eb2)
   Phase C.1 (read-only probes):                NEXT (this re-issued directive)
   Phase C.2 (uvicorn debug logs):              IF Phase 1 inconclusive, w/ Sloan confirm
   Phase C.3 (apply fix or escalate):           POST Phase 2 root cause
   Build directive (atlas.mcp_client + tests):  PAUSED until Phase 3 green
```

## 7. Standing rules in effect (5)

- 5-guardrail rule + carve-outs (Phase 1 probes are pure observers under PD authority)
- B2b + Garage anchor preservation invariant (still holding ~76+ hours)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol with bidirectional one-liner format
- Phase closure pattern (literal-PASS + spirit-partial)
- **Pre-directive verification (5th rule)** -- this verdict has 11-row Verified live block with Paco-side new finding (host='0.0.0.0' disproves hypothesis A)
- Spec or no action: Phase 1 fully scoped; Phase 2 requires Sloan confirm; Phase 3 has decision tree
- Library-default discipline (carries to re-issued build directive when Phase 3 green)
- Secrets discipline (carries to re-issued build directive when Phase 3 green)
- P6 lessons banked: 20 (no new ones until Phase 3 reveals lesson)

## 8. Discipline metrics Day 75-76 (8 directive verifications + 4 PD reviews + 1 paco_request)

| Directive | Findings caught at authorship |
|-----------|-------------------------------|
| Spec v3 master block | 4 |
| Cycle 1B GO | 1 |
| Cycle 1C GO | 3 |
| Cycle 1D GO | 4 |
| Cycle 1E GO | 5 |
| Cycle 1F GO (original) | 5 |
| **Cycle 1F transport-hang verdict (this turn)** | **1** (host='0.0.0.0' disproves PD's hypothesis A; reshapes the candidate path tradeoffs) |
| **Cumulative** | **23** |

The rule continues to earn its keep. Even on a BLOCK turn, verifying deployed state (mcp_http.py contents) eliminated one hypothesis from the candidate space. Smaller yield than Cycle 1F GO's 5 findings, but real.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1f_transport_resolved.md`

-- Paco
