# Paco -> PD response -- Atlas Cycle 1G TLS strategy: OPTION A RATIFIED

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1G (spec v3 section 8.1G) -- Atlas MCP server INBOUND on Beast
**Predecessor:** `docs/paco_request_atlas_v0_1_cycle_1g_tls_strategy.md` (PD, commit `4836315`)
**Status:** **OPTION A RATIFIED.** All 6 PD asks ruled. Build directive dispatches in next handoff turn.

---

## 0. Verified live (2026-05-01 UTC Day 77)

**Per 5th standing rule.** Independent verification of PD's key claims before ratification.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | HEAD on control-plane-lab | `git log --oneline -1` | `4836315 cycle-1g entry: TLS strategy paco_request gate (PRE-implementation)` |
| 2 | **Beast NOT in tailnet** | `tailscale status` from CK | 8 nodes: sloan3 (CK), cortez, iphone181, jesair, kali-rpi, mac-mini, pi3, sloan4. **Beast absent** -- PD's key finding confirmed |
| 3 | CK Tailscale cert on disk | `sudo ls -la /etc/ssl/tailscale/` | `sloan3.tail1216a3.ts.net.crt` (2876B Apr 3) + `.key` (227B Apr 3); 28+ days old, silently auto-renewed |
| 4 | nginx mcp vhost template | `sudo cat /etc/nginx/sites-enabled/mcp` | 25 lines clean: `listen 8443 ssl` + `server_name sloan3.tail1216a3.ts.net` + `ssl_certificate /etc/ssl/tailscale/...` + `proxy_pass http://127.0.0.1:8001/mcp` + Connection upgrade headers. **Direct template for Beast Option A vhost.** |
| 5 | Substrate anchors | (PD captured PRE) | `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` -- bit-identical 96+ hours through entire Phase 3 saga + Cycle 1F close + this paco_request authoring window |
| 6 | Atlas package state | (PD captured) | HEAD `5a9e458` clean working tree |
| 7 | Beast no Atlas listener | (PD captured) | only orchestrator on :8000 (pid=1261) + kokoro-tts; no atlas-* unit, no Atlas listener -- Atlas inbound MCP is NEW infrastructure |

PD's analysis verified accurate.

## 1. Why Option A is correct

### 1.1 Remote CEO access is the dominant trade-off

The single non-negotiable in this decision is **Sloan's actively-used remote workflow.** Today alone we've operated from Mac mini, Cortez (offsite), and JesAir. Option B's LAN-only mode would make Atlas inbound unreachable from any of those when offsite. That's a regression on existing capability for a substrate-savings of one apt install.

LAN-only is defensible for things that genuinely should never leave the LAN (Tier 3 Schlage lock control, IoT MQTT broker authority). Atlas tools (search atlas.events, embedding lookup, inference history) don't have that profile -- they're CEO-introspection tools the CEO will want to hit from any device anywhere on the tailnet.

### 1.2 Pattern consistency compounds across cycles

Cycle 1G is the second TLS-terminating MCP endpoint. Reasonable forecast: Cycles 2/3/4 introduce more (Alexandra agent endpoint, RAG retrieval gateway, possibly robotics-tier API). Each faces the same TLS-posture decision. If Cycle 1G mirrors CK, every subsequent cycle has a 25-line vhost template + a `tailscale cert <fqdn>` one-liner. If Cycle 1G diverges, every subsequent cycle re-litigates.

Not minor cognitive savings -- difference between ONE TLS strategy across the homelab vs N strategies that drift over time.

### 1.3 Failure-domain independence vs A'

A' (CK reverse-proxy) couples Atlas inbound MCP to CK's nginx. CK reboot or nginx hiccup drops both homelab-mcp AND atlas-mcp simultaneously. Today's Phase 3 deploy-restart was a clean ~30s window; tolerable for one endpoint, but cascading both starts to feel like SPOF. Independence worth the lightweight nginx install.

### 1.4 Cert auto-renewal is real

CK's cert from Apr 3, today is May 1 -- 28+ days, silently renewed. Option B's manual cert rotation is an operational incident waiting to surface. Auto-renewal under Option A removes that whole class of failure mode.

### 1.5 Composability with future authn

If v0.2 adds bearer tokens or API keys, Option A drops them in cleanly as nginx middleware or FastMCP middleware -- standard TLS-terminating pattern. Option C (plain HTTP) requires unwinding the posture before adding authn. Lock-in cost matters at v0.1 even if v0.2 isn't here yet.

## 2. Six rulings

### Ask 1 -- Ratify Option A

**RULING: RATIFIED.** Option A is canonical. PD proceeds with Beast-joins-tailnet -> Beast nginx -> Beast's own Tailscale FQDN cert.

Fallback A' is acknowledged but not authorized. If implementation hits an unexpected blocker for Option A (Tailscale install fails, MagicDNS hostname conflicts, etc.), file paco_request before falling back to A'.

### Ask 2 -- Authorize implementation handoff next turn

**RULING: AUTHORIZED.** Build directive dispatches in next `handoff_paco_to_pd.md` turn. Scope:

- Tailscale install on Beast (CEO single-confirm gate via trigger)
- Tailscale up + tailnet-join verification
- `tailscale cert <FQDN>` cert provisioning
- nginx install on Beast
- Beast nginx vhost mirroring CK template
- FastMCP atlas-mcp server skeleton on Beast loopback :8001 (tool surface deferred to subsequent paco_request)
- systemd unit (mirroring `homelab-mcp.service` pattern)
- Smoke test from a tailnet client
- atlas.events telemetry hook with `source='atlas.mcp_server'`
- Anchor preservation invariant capture pre/post

### Ask 3 -- v0.2 P5 candidates

**RULING:**

- **v0.2 P5 #16 BANKED:** Beast joining tailnet enables future tailnet-only services on Beast (direct SSH from non-CK tailnet members; ts-tunnels for git operations; Atlas backplane communication paths). Document side-effect openings in v0.2 hardening notes; consider which to enable selectively.
- **v0.2 P5 #17 SKIPPED:** Conditional on choosing A' ("designate a future migration cycle from CK-reverse-proxy to Beast-direct TLS termination"). Since A' not chosen, no migration debt accrues. Don't bank.

v0.2 P5 backlog total: **16** (was 15; +1 for #16; #17 skipped).

### Ask 4 -- CEO single-confirm gate for Tailscale install on Beast

**RULING: SINGLE-CONFIRM SUFFICIENT.** PD's bias correct.

Per Hot Take memory file software-install classification:
- Tailscale install is `apt-get install tailscale` + `tailscale up --authkey=...` -- no kernel modules, no driver install, no firmware change, no hardware-adjacent operation
- Reversible: `tailscale logout && tailscale down && apt purge tailscale`
- No CMOS/BIOS/PSU touched (the failure mode that makes hardware-adjacent changes warrant double-confirm)
- Existing tailnet-membership precedent: Cortez, JesAir, Mac mini, KaliPi, Goliath all joined tailnet without double-confirm

CEO trigger to execute Cycle 1G build directive constitutes single-confirm. PD does not need separate Sloan ack mid-execution for the Tailscale install step.

### Ask 5 -- Confirm port 8443 on Beast

**RULING: CONFIRMED 8443.** Mirrors CK convention; no collision with Beast :8000 orchestrator; consistent with future agents' mental model (":8443 means MCP").

Not :443 because we want clear separation between standard HTTPS web traffic and MCP-specific TLS-terminating endpoints. :8001 was a candidate but mirroring CK's :8443 has higher pattern-consistency value than numeric separation.

### Ask 6 -- Tool-surface paco_request as next gate

**RULING: CONFIRMED.** Once TLS lands and atlas-mcp server skeleton is operational, PD writes a separate `paco_request_atlas_v0_1_cycle_1g_tool_surface.md` enumerating which Atlas tools the inbound MCP server exposes.

Likely candidates (not ratified at this paco_request, just framed):
- `atlas.events.search` -- read-only query
- `atlas.embeddings.upsert` -- write new embedding row
- `atlas.embeddings.query` -- nearest-neighbor lookup
- `atlas.inference.history` -- read-only query

Don't bundle tool-surface decisions into the build directive. TLS is substrate; tool surface is application layer. Two ratifications, two cycles of focus.

## 3. One refinement to add to the build directive

**Tailscale MagicDNS hostname verification BEFORE cert provisioning:**

PD's paco_request named the FQDN as `beast.tail1216a3.ts.net`, but Tailscale's MagicDNS derives the hostname from the OS hostname (or the `--hostname=` flag). Beast's OS hostname is likely `beast` per `/etc/hostname`, so default is likely correct. But the build directive should:

1. After `tailscale up`, run `tailscale status --self --json | jq -r '.Self.DNSName'` to capture the actual issued FQDN
2. Use the captured FQDN for `tailscale cert <fqdn>` and nginx `server_name`
3. If captured FQDN differs from `beast.tail1216a3.ts.net`, document and proceed with the actual issued name

5-second probe that prevents cert-provisioning failure mid-execution. Direct application of P6 #20 (verify deployed-state names live before authoring references).

## 4. P6 banking

No new P6 lesson this turn. TLS strategy paco_request is a clean architectural-ratification gate working as designed. The MagicDNS hostname-verification refinement is a direct application of existing P6 #20 (verify deployed-state names live).

For Cycle 1G build directive Step 17 (mirroring Phase 3 pattern): no new lessons to append; carry forward through Cycle 1G close.

## 5. Substrate state confirmation

B2b + Garage anchors held bit-identical for 96+ hours through Cycle 1F close + this paco_request authoring window. PD's authoring did not touch substrate (read-only verification commands only). Invariant: HOLDING.

## 6. Counts post-ruling

- Standing rules: 5 (unchanged)
- P6 lessons banked: 27 (unchanged this turn; #27 from Cycle 1F close still pending append to feedback file in next close-out fold)
- v0.2 P5 backlog: **16** (was 15; +1 for #16; #17 skipped)
- Atlas Cycles SHIPPED: 6 of 9 in Cycle 1
- Cumulative findings caught at directive-authorship: 30
- Cumulative findings caught at PD pre-execution review: 2
- Cumulative findings caught at PD execution failure: 1
- Cycle 1F transport saga total findings caught pre-failure-cascade: 33
- Cycle 1G TLS strategy ratification: clean (no findings, no escalations -- architectural gate worked as designed)

## 7. Cycle 1G build directive scope (preview)

Forthcoming `handoff_paco_to_pd.md` build directive covers at minimum:

```
Step 1.  Anchor + state PRE
Step 2.  Tailscale install on Beast (apt + verify)
Step 3.  tailscale up + capture issued FQDN via tailscale status --self --json
Step 4.  Provision cert via tailscale cert <fqdn>
Step 5.  apt install nginx on Beast
Step 6.  Author Beast nginx vhost mirroring CK template
Step 7.  Author atlas-mcp Python skeleton (FastMCP loopback :8001, NO tools yet)
Step 8.  Author atlas-mcp.service systemd unit
Step 9.  Reload systemd + start atlas-mcp.service + verify Active running
Step 10. nginx -t + nginx reload
Step 11. Smoke test from tailnet client: HTTPS POST initialize -> 200 expected
Step 12. atlas.events delta + secrets discipline audit
Step 13. Anchor POST + diff bit-identical
Step 14. Commits to atlas + control-plane-lab fold
Step 15. paco_review with Verified live + 5-gate scorecard for Cycle 1G
Step 16. Cleanup
```

Detailed step-by-step in next handoff. This preview is PD context only.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1g_tls_strategy_ruling.md`

-- Paco
