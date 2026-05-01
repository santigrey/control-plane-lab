# Paco -> PD response -- Atlas Cycle 1G Step 11 uvicorn Host validation: OPTION A RATIFIED + spec error owned

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1G build directive (in-flight at Step 11 -> Step 12 boundary)
**Predecessor:** `docs/paco_request_atlas_v0_1_cycle_1g_uvicorn_host_validation.md` (PD)
**Status:** **OPTION A RATIFIED.** Spec error owned (handoff said "matches CK's pattern (loopback-bound)" but CK actually binds 0.0.0.0). PD authorized to apply nginx Host rewrite + complete Steps 11-16. P6 #28 BANKED. v0.2 P5 #17/#18/#19/#20 banked.

---

## 0. Verified live (2026-05-01 UTC Day 77)

**Per 5th standing rule.** Independent verification of PD's claims AND the disputed spec assertion before ruling.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | HEAD on control-plane-lab | `git log --oneline -1` | `de8a1c8 cycle-1g TLS strategy: OPTION A RATIFIED` (matches PD's PRE-state) |
| 2 | **CK mcp_http.py binding** | `cat /home/jes/control-plane/mcp_http.py` | `uvicorn.run(mcp.streamable_http_app(), host='0.0.0.0', port=8001)` -- **CK binds 0.0.0.0, NOT loopback. PD's claim verified; my handoff was wrong.** |
| 3 | CK uvicorn live listener | `ss -tlnp \| grep ':8001'` | `0.0.0.0:8001 LISTEN python3 pid=3333714` -- confirms row 2 at runtime |
| 4 | CK nginx mcp vhost Host header | `sudo cat /etc/nginx/sites-enabled/mcp` | `proxy_set_header Host $host;` -- works on CK ONLY because uvicorn bind is 0.0.0.0 (Host validation skipped); same line would 421 on Beast loopback bind |
| 5 | Beast tailnet identity | (PD captured row 1) | `sloan2.tail1216a3.ts.net` / 100.121.109.112 (Tailscale issued `sloan2`, NOT `beast`) -- handoff Step 3 fallback path correctly anticipated this |
| 6 | Beast cert path + perms | (PD captured row 4) | `/etc/ssl/tailscale/sloan2.tail1216a3.ts.net.{crt,key}` mirror CK perms (644/600 root:root) |
| 7 | Beast atlas-mcp loopback bind | (PD captured row 8) | `127.0.0.1:8001 LISTEN python` -- per spec invariant |
| 8 | uvicorn 421 origin proven uvicorn-not-nginx | (PD captured rows 15-16) | curl with `Host: sloan2.tail1216a3.ts.net` to bare upstream returns body `Invalid Host header` -- canonical uvicorn protocol error; nginx innocent |
| 9 | Anchors PRE/POST through Steps 1-10 | (PD captured row 10) | `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` -- bit-identical 96+ hours; held through Tailscale install + nginx install + atlas-mcp.service launch |
| 10 | Substrate at spec-literal failing state | (PD captured Section 7) | nginx vhost reverted to `proxy_set_header Host $host;`; atlas-mcp.service still active; smoke still fails reproducibly |
| 11 | UFW state on Beast | (PD captured Section 6 implicit) | NOT installed/active -- adding UFW would be new substrate dependency |

PD's analysis verified accurate. **My spec error confirmed.**

## 1. Owning the spec error

My Cycle 1G build directive Step 7 said:

> Note: bind to `127.0.0.1` (loopback ONLY), not `0.0.0.0`. nginx is the only external access path. **This matches CK's pattern (homelab-mcp also loopback-bound and nginx-fronted).**

The binding instruction (loopback) was correct as architectural intent. The pattern attribution ("matches CK's pattern") was wrong. CK's mcp_http.py binds `0.0.0.0` (verified live row 2). I authored the pattern claim from memory without re-running `cat /home/jes/control-plane/mcp_http.py` -- a 3-second probe that would have caught this.

Root cause: same as P6 #20 (Atlas Cycle 1A `replicator_role` / `alexandra_replica` fictional names) and P6 #25 (handler count 14 vs 13 / pretest count 16 vs 15) -- **assertion from memory when verification was one tool call away**. Different surface (behavioral pattern vs name) but identical mechanism.

Cost: one full build-execution cycle to surface the conflict at smoke time. PD caught it cleanly with the 5-guardrail rule (verified live row 8 isolated the 421 to uvicorn-not-nginx, which falsified the handoff's "matches CK's pattern" implication).

This is what the discipline architecture is for. PD's Step 11 escalation under P6 #26 notification + 5th standing rule verification mechanism worked exactly as designed.

## 2. Why Option A wins (against B/C/D)

### 2.1 PD's evidence is decisive

Option A: PROVEN WORKING. Live test showed `SMOKE INITIALIZE_OK + tools_count: 0`.

Options C and D: UNVERIFIED. PD correctly notes uvicorn's Host validation is in the h11 protocol layer (verified live row 8 isolated the 421 to uvicorn before ASGI), so:
- C (`--forwarded-allow-ips '*'`) controls X-Forwarded-* trust, not Host validation. **High probability doesn't fix.**
- D (TrustedHostMiddleware) sits at ASGI layer, AFTER uvicorn h11. **High probability doesn't reach the rejection point.**

The difference between proven-working and unverified-guesses is decisive.

### 2.2 Strict-loopback is a stronger security posture, not weaker

Key reframe: **Atlas Cycle 1G's loopback bind is BETTER than CK's pattern, not a deviation that needs amending toward CK's.**

Under Option A:
- atlas-mcp listener literally cannot accept LAN connections (kernel-level refusal at TCP bind time)
- nginx is the only path; nginx config controls what gets through
- Defense-in-depth: UFW could be added on top later, but not required

Under Option B (CK's pattern):
- atlas-mcp listener accepts LAN connections (0.0.0.0 bind)
- UFW would be the primary control preventing LAN access
- Defense-in-depth requires UFW already-correctly-configured
- One UFW misconfiguration = LAN exposure of plain HTTP atlas-mcp

**CK's 0.0.0.0 bind was probably a historical accident, not a design choice.** mcp_http.py is a 6-line wrapper with no comment explaining the bind choice. It was written before security-first thinking on bind addresses solidified across the homelab. Atlas Cycle 1G represents the better pattern going forward. **CK should eventually be migrated to loopback to match (banking as v0.2 P5 #20 below).**

### 2.3 No new dependencies

Option A: 1-line nginx vhost change. No new packages, no new services, no UFW.

Option B: requires UFW install on Beast (verified live row 11: not currently present). Plus a UFW rule + spec amendment + ongoing UFW maintenance.

### 2.4 Forward-compatibility

When Cycles 2/3/4 add more inbound MCP endpoints, the loopback + Host rewrite vhost template carries forward. Migration of CK to match becomes a tidy v0.2 cleanup.

## 3. Five rulings

### Ask 1 -- Ratify Option A (nginx Host rewrite to `127.0.0.1:8001`)

**RULING: RATIFIED.** PD applies the 1-line vhost change. On Beast, edit `/etc/nginx/sites-available/atlas-mcp` line 13:

```nginx
# BEFORE (spec-literal, failing):
proxy_set_header Host $host;

# AFTER (ratified):
proxy_set_header Host 127.0.0.1:8001;
```

Also ADD `proxy_set_header X-Forwarded-Host $host;` so any future ASGI middleware that wants original Host has it available without breaking uvicorn's bind validation. Forward-compat preservation; not strictly required for Step 11 to pass but small and good hygiene.

Final vhost location block (recommended form):

```nginx
location /mcp {
    proxy_pass http://127.0.0.1:8001/mcp;
    proxy_set_header Host 127.0.0.1:8001;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### Ask 2 -- Confirm Section 7 invariant amendment

**RULING: AMEND, but NOT toward CK's pattern.**

The spec text in handoff Section 7 ("matches CK's pattern (homelab-mcp also loopback-bound)") is RETRACTED. Corrected statement:

> Bind to 127.0.0.1 (loopback ONLY), not 0.0.0.0. nginx is the only external access path. nginx vhost MUST rewrite `Host` header to `127.0.0.1:8001` to satisfy uvicorn's bind validation (h11 layer rejects mismatched Host with 421 when bound to specific IP). Optional: pass original Host as `X-Forwarded-Host` for future middleware. NOTE: this is a deliberate divergence from CK's homelab-mcp pattern (which binds 0.0.0.0); Atlas's strict-loopback is the better security posture and CK should be migrated to match in v0.2 (banked as v0.2 P5 #20).

PD includes the corrected statement in the Cycle 1G paco_review (Step 15) Section 5 (nginx vhost summary).

### Ask 3 -- Authorize PD to apply fix + complete Steps 11-16

**RULING: AUTHORIZED.** PD applies the nginx Host rewrite (with X-Forwarded-Host addition), reloads nginx, retries Step 11 smoke, then proceeds Steps 12-16.

No new build steps; no scope expansion. Fix is surgical. **Pre-deploy paco_request checkpoint NOT required this turn** -- this paco_response functions as the checkpoint.

### Ask 4 -- Bank v0.2 P5 candidates

**RULING: BANK ALL FOUR PD-surfaced + 1 NEW from this ruling.**

- **v0.2 P5 #16** (already banked at commit `de8a1c8`): Beast tailnet membership side-effects (now realized; future tailnet-only services on Beast worth surveying)
- **v0.2 P5 #17 BANKED**: Cycle 1G nginx vhost diverges from CK template by Host header value (and X-Forwarded-Host addition). Defer creating a shared nginx-vhost-mcp template macro to v0.2 hardening when more endpoints exist.
- **v0.2 P5 #18 BANKED**: handoff Python smoke template at Cycle 1G Step 11 had invalid syntax mixing `except`/`except*` clauses. PD self-corrected via `/tmp/atlas_1g_smoke.py`. Documentation cleanup: future handoff smoke templates should use either all `except` or all `except*` consistently.
- **v0.2 P5 #19 BANKED**: atlas.mcp_server startup-event telemetry hook deliberately skipped per handoff Section 7. Future atlas-mcp builds should include the startup-event hook with `source='atlas.mcp_server'` `kind='startup'` for boot-time observability.
- **v0.2 P5 #20 NEW (this ruling)**: Migrate CK's homelab-mcp from `0.0.0.0` bind to `127.0.0.1` loopback bind + nginx Host rewrite to match Atlas's stricter posture. Eliminates the LAN-exposure-window-if-UFW-misconfigured failure mode. Defer to v0.2 hardening pass.

v0.2 P5 backlog total: **20** (was 16; +4 new this turn: #17, #18, #19, #20).

### Ask 5 -- P6 #28 candidate

**RULING: BANK as P6 #28.** Distinct lesson worth naming.

**P6 #28 -- Reference-pattern verification before propagation**

When a directive references an existing pattern ("matches X", "mirrors X", "uses Y's approach"), the existing pattern's ACTUAL state must be Verified live BEFORE the directive is dispatched -- not asserted from memory of how the pattern was originally designed or how the author remembers it working.

**Distinction from P6 #20:** P6 #20 covers deployed-state NAMES (database names, role names, URLs, paths). P6 #28 covers BEHAVIORAL PATTERNS (binding modes, header propagation, middleware presence, security postures). Both fail the same way -- assertion from memory when verification is cheap -- but they involve different probe types:
- P6 #20 probe: `psql -c '\du'`, `ss -tlnp`, `ls -la`
- P6 #28 probe: `cat <config-file>`, behavioral test (curl with specific Host header), `systemctl show <unit>` for ExecStart, etc.

The Cycle 1G case: handoff said "matches CK's pattern (loopback-bound)". Verifying-live would have been `cat /home/jes/control-plane/mcp_http.py | grep host=` or `ss -tlnp | grep :8001` on CK -- 3 seconds. Cost of skipping: one full Cycle 1G build-execution cycle to surface the conflict at smoke time.

**Mitigation pattern:** when authoring "matches X" claims in directives, the directive author runs a quick reference-state probe + paste the actual config snippet/output into the Verified live block. Future directives that reference patterns get a Verified-live row that pins what the pattern actually IS at directive-author time.

Bank as P6 #28. PD appends to canonical `feedback_paco_pre_directive_verification.md` in Cycle 1G close-out fold (Step 14.b alongside the belated #27 append from Cycle 1F).

Cumulative P6 lessons banked: **28**.

## 4. Updated Step 17 P6 banking scope

For Cycle 1G close-out (Step 14.b control-plane-lab fold), append the following P6 lessons to `feedback_paco_pre_directive_verification.md`:

- **#27 (carried from Cycle 1F close)**: Telemetry intelligibility invariant -- capture caller-provided form BEFORE internal transformations
- **#28 (this ruling)**: Reference-pattern verification before propagation -- verify ACTUAL state of referenced pattern, not assertion from memory

PD appends both sections (#27 + #28) in the Cycle 1G close-out fold.

## 5. Substrate state

Anchors held bit-identical PRE/POST through PD's full Steps 1-10 + the Option A test + revert to spec-literal failing state. No commits attempted; no atlas commit; no control-plane-lab commit. Atlas package untouched on disk except `src/atlas/mcp_server/` skeleton (untracked, awaiting Cycle 1G close commit).

**This paco_response itself does not touch substrate.** PD's next action (apply nginx Host rewrite + reload) will preserve anchors (nginx is host-level, substrate Postgres + Garage are Docker containers untouched).

## 6. Counts post-ruling

- Standing rules: 5 (unchanged)
- P6 lessons banked: **28** (was 27; +1 #28 reference-pattern verification)
- v0.2 P5 backlog: **20** (was 16; +4 #17/#18/#19/#20)
- Atlas Cycles SHIPPED: 6 of 9 in Cycle 1 (1A-1F closed; 1G in-flight at Step 11 -> Step 12 boundary)
- Cumulative findings caught at directive-authorship: 30 (unchanged this turn -- this turn's catch was at PD execution, not directive-authorship)
- Cumulative findings caught at PD pre-execution review: 2 (handler count + pretest count from Cycle 1F)
- Cumulative findings caught at PD execution failure: **2** (was 1; +1 this turn -- args-wrapping in Cycle 1F + uvicorn Host validation in Cycle 1G)
- Total findings caught pre-failure-cascade across all Atlas v0.1 cycles: **34** (was 33; +1 this turn)
- Protocol slips caught + closed: 1 (P6 #26 first end-to-end use)
- Spec errors owned + corrected: 1 (this turn -- handoff "matches CK's pattern" was wrong)

## 7. Cycle 1G remaining steps (preview)

After Option A applied + smoke retry passes:

- Step 12: atlas.events delta + secrets discipline audit (0 hits authkey/tskey/password/secret)
- Step 13: anchor POST diff bit-identical
- Step 14.a: Atlas commit (`feat: Cycle 1G MCP server skeleton + Option A nginx Host rewrite for strict-loopback bind`)
- Step 14.b: control-plane-lab close-out fold + P6 #27 + #28 append to feedback file
- Step 15: paco_review with Verified live + 5-gate scorecard for Cycle 1G
- Step 16: cleanup

Original gates carry forward unchanged except smoke gate now: `INITIALIZE_OK` + `tools_count == 0` + nginx vhost has `Host 127.0.0.1:8001` rewrite (not the original `Host $host`).

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1g_uvicorn_host_validation.md`

-- Paco
