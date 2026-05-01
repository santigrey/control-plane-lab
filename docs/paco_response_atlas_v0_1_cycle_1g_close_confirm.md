# Paco -> PD response -- Atlas Cycle 1G CLOSE CONFIRMED 5/5 PASS + Cycle 1H entry point (atlas-mcp tool surface)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1G SHIPPED; Cycle 1H NEXT
**Predecessor:** `docs/paco_review_atlas_v0_1_cycle_1g_close.md` (PD, commit `c04a35d`)
**Status:** **CYCLE 1G CONFIRMED 5/5 PASS.** All 5 PD asks ruled. Cycle 1H entry-point dispatched as paco_request gate (atlas-mcp tool surface ratification BEFORE build, per Cycle 1G Ask 6 ruling and measure-twice-cut-once standing rule). One minor formatting note flagged.

---

## 0. Verified live (2026-05-01 UTC Day 77)

**Per 5th standing rule.** Independent verification of PD's 5/5 PASS scorecard before confirming close.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | control-plane-lab HEAD | `git log --oneline -1` | `c04a35d feat: Atlas Cycle 1G CLOSED 5/5 PASS -- inbound MCP server on Beast (Option A: tailnet + nginx + Tailscale FQDN cert)` |
| 2 | Atlas HEAD on santigrey/atlas | (per PD review) | `2f2c3b7 feat: Cycle 1G MCP server skeleton (FastMCP loopback :8001 + Option A nginx Host rewrite)` |
| 3 | Beast in tailnet as sloan2 | `tailscale status \| grep sloan2` from CK | `100.121.109.112  sloan2  james.3sloan@  linux  idle, tx 16636 rx 38196` -- live tx/rx confirms tailnet membership active |
| 4 | Tailscale ping CK->Beast | `tailscale ping --c 1 sloan2.tail1216a3.ts.net` | `pong from sloan2 (100.121.109.112) via 192.168.1.152:41641 in 1ms` |
| 5 | **End-to-end smoke from CK** | `curl -sI --max-time 10 https://sloan2.tail1216a3.ts.net:8443/mcp` | **HTTP/1.1 405 Method Not Allowed** + `Server: nginx/1.18.0` + `allow: GET, POST, DELETE` + `mcp-session-id: 44fb96cb15324e25b0db3f4704576cef` -- Atlas inbound MCP fully operational; full chain (TLS + nginx + uvicorn h11 Host validation + FastMCP) green |
| 6 | P6 #27 banked in feedback file | `grep` on `feedback_paco_pre_directive_verification.md` | `## P6 #27 -- Telemetry intelligibility invariant (Cycle 1F belated bank)` -- full statement + originating context + application pattern present |
| 7 | P6 #28 banked in feedback file | `grep` on `feedback_paco_pre_directive_verification.md` | `## P6 #28 -- Reference-pattern verification before propagation (Cycle 1G this turn)` -- full statement + distinction from P6 #20 + originating context + mitigation pattern + Cycle 1G resolution present |
| 8 | Cumulative footer | tail of feedback file | `Cumulative count: P6 lessons banked = 28 (was 26 at end of Cycle 1F; +1 #27 telemetry intelligibility, +1 #28 reference-pattern verification)` |
| 9 | atlas-mcp.service loopback bind preserved | (PD review Verified live row 8) | `127.0.0.1:8001 LISTEN python` -- strict-loopback security invariant intact |
| 10 | Cycle 1G total commit chain | `git log --oneline` | `c04a35d` (close fold) + `4f045e4` (Step 11 ruling) + `f1785e9` (Step 11 escalation) + `de8a1c8` (TLS strategy ratification) + `4836315` (TLS strategy paco_request) -- 5 commits across the cycle, clean trail |
| 11 | Substrate anchors | (per PD review row 10) | `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` -- bit-identical 96+ hours through entire Cycle 1G saga (Tailscale install + cert + nginx install + vhost twice + atlas-mcp.service start/restart + Step 11 diagnostic + revert + re-apply + commits + push) |
| 12 | handoff_paco_to_pd.md cleared | `wc -c` | 0 bytes -- per P6 #26 protocol PD cleared after read; ready to receive Cycle 1H directive |

PD's 5/5 PASS scorecard is **independently confirmed**.

## 1. Cycle 1G CONFIRMED 5/5 PASS

Canonical scorecard:

| Gate | Subject | Result |
|------|---------|--------|
| 1 | Beast tailnet membership (sloan2.tail1216a3.ts.net) | **PASS** |
| 2 | Tailscale-issued cert on Beast (mirror CK perms; Let's Encrypt CN=E7; expires 2026-07-30) | **PASS** |
| 3 | nginx vhost :8443 active + atlas-mcp.service Active running on 127.0.0.1:8001 strict-loopback | **PASS** |
| 4 | End-to-end smoke from CK tailnet member: HTTP 405 + `mcp-session-id` cookie + Python SDK INITIALIZE_OK + tools_count=0 | **PASS** |
| 5 | Anchor preservation + secrets discipline (anchors bit-identical PRE/POST 96+ hours; 0 hits authkey/tskey/password/secret) | **PASS** |

**Cycle 1G SHIPPED.** Atlas v0.1 progression: 1A-1G closed. 1H + Cycles 2/3/4 ahead per spec v3.

## 2. Rulings on PD's 5 asks

### Ask 1 -- Confirm Cycle 1G 5/5 PASS scorecard accepted

**RULING: ACCEPTED.** Independently verified per Section 0 above. All 5 gates green.

### Ask 2 -- Confirm P6 #27 + #28 banking landed

**RULING: CONFIRMED.** Both lessons present in canonical feedback file with full statement, originating context, and (for #27) application pattern + (for #28) distinction from P6 #20 + mitigation pattern + Cycle 1G resolution.

**Minor formatting note (NOT a halt-condition):** P6 #21-#26 used `### P6 #N` (H3) section headers; #27 and #28 used `## P6 #N` (H2). Mixed heading levels in the same lesson list. Not a content issue (text is complete and correct), just style drift. Bank as v0.2 P5 #21 (NEW): normalize all P6 lesson section headers to consistent H3 in v0.2 hardening pass. Not blocking; do not fix in-cycle.

v0.2 P5 backlog total: **21** (was 20; +1 for #21 P6 heading normalization).

### Ask 3 -- Direct Cycle 1H entry point

**RULING:** Cycle 1H is **atlas-mcp tool surface paco_request** per Cycle 1G TLS strategy Ruling Ask 6 anticipation.

Atlas inbound MCP server is operational with skeleton (FastMCP, no @mcp.tool definitions). Cycle 1H ratifies WHICH tools the server exposes, with what semantics, what argument schemas, what ACL constraints. Architectural decision space is non-trivial:

- Read-only vs read-write semantics per tool
- Server-side ACL design (deny patterns mirror atlas.mcp_client v0.1 pattern, but inbound has additional considerations)
- Per-tool argument-shape discipline (Pydantic-wrapped vs flat-args; learned from Cycle 1F P6 #28 + auto-wrap reality)
- Auth-context propagation (caller identity from tailnet membership? from future bearer-token middleware? not yet)
- Telemetry shape (mirror atlas.mcp_client's `source='atlas.mcp_client'` -> `source='atlas.mcp_server'` pattern; what kinds; what payload shape)

**Cycle 1H dispatched as paco_request gate (NOT a build directive).** PD writes `paco_request_atlas_v0_1_cycle_1h_tool_surface.md` proposing options. Paco rules. Then build handoff dispatches.

Details for the paco_request in Section 4 below.

### Ask 4 -- Bank PO1 (auth key residual surface)

**RULING: BANK as v0.2 P5 #22 (NEW).** Document post-cycle confirmation that the Tailscale auth key used at Cycle 1G Step 3 has been consumed (one-time-use exhausted) or revoked. CEO confirms via Tailscale admin console (`https://login.tailscale.com/admin/settings/keys`) within next 24 hours.

**Preferred resolution path for Cycle 1G:** if the auth key was generated as one-time-use per the original handoff guidance ("Reusable: NO"), it auto-consumed on Beast's join and is now inert. If it was reusable, CEO should manually revoke it via the admin console.

v0.2 P5 backlog total: **22** (was 21; +1 for #22 auth key residual surface).

PD documents this in Cycle 1H paco_request as a Section 0 Verified live row OR as a separate one-line audit task -- doesn't need its own cycle.

### Ask 5 -- Confirm v0.2 P5 #20 (CK migrate to loopback) carries into v0.2 hardening pass

**RULING: CONFIRMED.** v0.2 P5 backlog as of this turn:

| # | Item | Source |
|---|------|--------|
| 10 | mcp Python SDK upstream PR for default MCP-Protocol-Version header | Cycle 1F |
| 11 | Beast SSH alias on CK ssh config | Cycle 1F |
| 12 | pytest async test isolation race in atlas.inference + atlas.embeddings token_logging | Cycle 1F |
| 13 | telemetry status field reflect MCP CallToolResult isError | Cycle 1F |
| 14 | remove .bak.phase3 rollback artifacts at v0.2 hardening close | Cycle 1F |
| 15 | rename streamablehttp_client to streamable_http_client per upstream MCP SDK | Cycle 1F |
| 16 | Beast tailnet membership side-effects (now realized) -- selectively enable tailnet-only services | Cycle 1G TLS |
| 17 | shared nginx-vhost-mcp template macro (Atlas vs CK Host header drift) | Cycle 1G Step 11 |
| 18 | handoff Python smoke template `except`/`except*` syntax cleanup | Cycle 1G Step 11 |
| 19 | atlas.mcp_server startup-event telemetry hook | Cycle 1G Step 11 |
| 20 | **CK migrate from 0.0.0.0 to 127.0.0.1 loopback bind + nginx Host rewrite** | Cycle 1G Step 11 |
| 21 | normalize P6 lesson heading levels (h2 vs h3 drift Cycle 1F #27 + Cycle 1G #28) | THIS RULING |
| 22 | Tailscale auth key residual confirmation (one-time-use consumed or manually revoked) | THIS RULING |

v0.2 P5 total: **22**. Items #14-#22 = 9 items added since v0.2 P5 #13 closed. Visibility tracker carries forward.

## 3. Cycle 1G saga retrospective (3-line summary)

Atlas Cycle 1G shipped after a TLS-strategy paco_request (Option A ratified mirroring CK Tailscale FQDN+nginx+cert pattern) + 10 clean build steps + Step 11 BLOCKER (uvicorn h11 Host validation rejecting nginx-forwarded `Host: sloan2.tail1216a3.ts.net` as 421 Misdirected Request because atlas-mcp loopback-binds while CK 0.0.0.0-binds) + my owned spec error ("matches CK's pattern (loopback-bound)" was wrong; CK is 0.0.0.0) + Option A nginx Host rewrite to `127.0.0.1:8001` + X-Forwarded-Host enhancement ratified + 5/5 PASS scorecard + commits + close. Net result: 2 paco_requests + 2 paco_responses + 1 close confirm, 1 spec error owned + corrected, 2 P6 lessons banked (#27 carried + #28 NEW), 5 v0.2 P5 candidates banked (#16-#20), Cycle SHIPPED with strict-loopback BETTER security posture than CK's 0.0.0.0+UFW pattern.

## 4. Cycle 1H dispatch -- atlas-mcp tool surface paco_request gate

### 4.1 Why paco_request first (not build directive)

Atlas inbound MCP server with NO tools is operational. Cycle 1H decides:

1. Which Atlas tools to expose at v0.1 (subset of {atlas.events.search, atlas.embeddings.upsert, atlas.embeddings.query, atlas.inference.history, plus possibly atlas.tasks.* if the spec calls for it})
2. Per-tool argument schema (Pydantic-wrapped consistent with mcp_server.py CK pattern; or flat-args)
3. Server-side ACL design (deny patterns; per-tool arg constraints; mirror or diverge from atlas.mcp_client client-side ACL)
4. Telemetry shape (kinds, payload structure for source='atlas.mcp_server')
5. Read-only vs read-write classification per tool
6. Error response shape (when ACL denies; when DB unavailable; when input invalid)

Getting these wrong has compounding cost (callers couple to schemas; ACL design changes are migration-painful). Better to ratify shape first.

### 4.2 PD authority for Cycle 1H paco_request

PD writes `docs/paco_request_atlas_v0_1_cycle_1h_tool_surface.md` proposing options + recommendation. Required content:

1. **Verified live** (per 5th standing rule): atlas package state, atlas.events schema (`\d atlas.events` for canonical column inventory), atlas.embeddings vector column dimensions, atlas.inference table schema, mcp_server.py CK pattern (for argument-shape reference -- this time Verified live, applying P6 #28!), Tailscale auth key residual confirmation per Ask 4
2. **Tool surface options:** at minimum 2-3 surface scopes (Minimum Viable -- read-only only; Standard -- read + curated writes; Full -- all sensible operations including writes). With per-option enumeration of which tools are in scope.
3. **Argument schema decision**: Pydantic-wrapped (mirror CK + auto-wrap learned from Cycle 1F) vs flat-args; PD recommendation with rationale.
4. **Server-side ACL design**: deny patterns; per-tool arg constraints; relationship to atlas.mcp_client client-side ACL. Authoritative or advisory? Mirror or diverge?
5. **Telemetry contract**: kinds, payload shape for `source='atlas.mcp_server'`. P6 #27 telemetry intelligibility invariant applies (capture caller-provided form before any internal transformation).
6. **Substrate impact**: anchors must remain bit-identical; what touches what.
7. **Asks**: ratify scope + shape + ACL + telemetry; authorize implementation handoff next turn.

### 4.3 Cycle 1H scope boundary (firm)

IN scope this paco_request: tool surface enumeration, argument shape, ACL shape, telemetry shape -- ALL ratification decisions before code lands.

OUT of scope this paco_request:
- Implementation code (waits for build handoff)
- Auth-context propagation beyond tailnet membership (v0.2 P5 candidate)
- Per-tool rate limiting (v0.2 P5 candidate)
- Server-side observability dashboards (v0.2)

### 4.4 No build directive this turn

PD writes paco_request only. Notification line in `handoff_pd_to_paco.md` per P6 #26. CEO triggers: "Paco, PD escalated, check handoff." Paco rules. Then PD gets the build directive.

This preserves measure-twice-cut-once on architectural decisions before code lands.

## 5. P6 banking

No new P6 lesson this turn. Cycle 1G close ran clean. P6 #27 + #28 from Cycle 1G already canonically banked.

For Cycle 1H paco_request authoring: P6 #28 directly applies (Verified live the CK mcp_server.py argument-shape pattern before referencing it). PD has internalized the lesson based on Step 11 escalation pattern.

## 6. Counts post-confirmation

- Standing rules: 5 (unchanged)
- P6 lessons banked: **28** (unchanged this turn)
- v0.2 P5 backlog: **22** (was 20; +1 #21 P6 heading normalization; +1 #22 auth key residual confirmation)
- Atlas Cycles SHIPPED: **7 of 9 in Cycle 1** (1A-1G closed)
- Atlas HEAD: `2f2c3b7` on santigrey/atlas
- control-plane-lab HEAD: `c04a35d` on santigrey/control-plane-lab
- Substrate anchors: bit-identical 96+ hours through 2 full cycle close-outs (1F + 1G) + Tailscale install + nginx install + atlas-mcp.service launch
- Cumulative findings caught at directive-authorship: 30
- Cumulative findings caught at PD pre-execution review: 2
- Cumulative findings caught at PD execution failure: 2
- Total findings caught pre-failure-cascade (Atlas v0.1): 34
- Spec errors owned + corrected: 1 (Cycle 1G "matches CK's pattern")
- Protocol slips caught + closed: 1 (P6 #26 first end-to-end use Cycle 1F close)

## 7. Cycle 1H entry-point trigger

**For PD:** read this response, write notification per P6 #26, then write `paco_request_atlas_v0_1_cycle_1h_tool_surface.md` per Section 4 above.

**For CEO Sloan:** when PD pings via handoff: `Paco, PD escalated, check handoff.` (Section 4.4 confirms paco_request flow, not build directive flow.)

## 8. Anchor preservation invariant

B2b + Garage anchors held bit-identical for 96+ hours through Cycles 1A-1G + Phase 3 saga + 1G build saga. Substrate (Postgres + Garage containers) untouched throughout. Invariant: SHIPPED.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1g_close_confirm.md`

-- Paco
