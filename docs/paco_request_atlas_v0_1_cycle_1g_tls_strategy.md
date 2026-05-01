# PD -> Paco request -- Atlas v0.1 Cycle 1G TLS strategy (PRE-implementation gate)

**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1G (spec v3 section 8.1G) -- Atlas MCP server INBOUND on Beast
**Predecessors:** `docs/paco_response_atlas_v0_1_cycle_1f_close_confirm.md` (Paco, HEAD `3baa455`) + `docs/paco_review_atlas_v0_1_cycle_1f_phase3_close.md` (PD, commit `34838bd`)
**Status:** **paco_request gate. NO implementation this turn.** PD surfaces 4 TLS posture options + 1 sub-variant + recommendation. Paco rules. Then build directive dispatches.

---

## 0. Verified live (per 5th standing rule)

Captured 2026-05-01 UTC (Day 77) immediately before authoring this paco_request. All rows independently observed via direct MCP-to-host queries.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Atlas HEAD on Beast | `cd /home/jes/atlas && git log --oneline -1` | `5a9e458 feat: Cycle 1F MCP client gateway + ACL + telemetry + schema-aware auto-wrap` |
| 2 | Atlas working tree clean | `git status -s` | (empty -- no modifications) |
| 3 | Beast network identity | `ip -4 addr show \| grep "inet "` | `192.168.1.152/24 eno3` (LAN); 3x docker bridges (172.17/172.18/172.19); **NO Tailscale interface** |
| 4 | Beast Tailscale state | `which tailscale` | **NOT INSTALLED** -- critical input for option analysis |
| 5 | Beast listeners :8000-:8443 | `ss -tlnp` | `0.0.0.0:8000 uvicorn pid=1261` -- `/home/jes/control-plane/orchestrator/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000` (orchestrator service, not Atlas) |
| 6 | Beast Atlas listeners | grep filter on (5) | NONE -- Atlas has NO server-side process on Beast yet |
| 7 | Beast running services | `systemctl list-units --state=running \| grep atlas\|uvicorn` | `kokoro-tts.service` (TTS, unrelated); no atlas-* unit |
| 8 | CK Tailscale tailnet | `tailscale status` | 8 nodes: sloan3 (CK), cortez, iphone181, jesair, kali-rpi, mac-mini (active), pi3, sloan4 (Goliath/GX10). **Beast absent.** |
| 9 | CK TLS certs (Tailscale-issued) | `ls -la /etc/ssl/tailscale/` | `sloan3.tail1216a3.ts.net.crt` (2876B) + `.key` (227B), root:root, mode 644/600, dated 2026-04-03 |
| 10 | CK nginx vhosts | `sudo nginx -T \| grep -E 'server_name\|listen\|ssl_certificate'` | 443 SSL + 80 + 8443 SSL on `sloan3.tail1216a3.ts.net` (and 192.168.1.10 on 443/80); ssl_certificate from `/etc/ssl/tailscale/` |
| 11 | CK nginx sites-enabled | `ls /etc/nginx/sites-enabled/` | `alexandra` + `mcp` (homelab MCP at 8443) |
| 12 | Substrate B2b anchor | `docker inspect control-postgres-beast` | `2026-04-27T00:13:57.800746541Z h=healthy r=0` (96+ hrs bit-identical through entire Phase 3 saga) |
| 13 | Substrate Garage anchor | `docker inspect control-garage-beast` | `2026-04-27T05:39:58.168067641Z h=healthy r=0` (96+ hrs bit-identical) |

**Anchor preservation invariant established PRE.** Substrate B2b + Garage MUST remain bit-identical through this paco_request (no substrate touched; document-only).

---

## 1. TL;DR

Atlas v0.1 Cycle 1G exposes Atlas tools (search atlas.events, atlas.embeddings store-and-retrieve, atlas.inference query) to external MCP clients via an INBOUND MCP server on Beast (192.168.1.152). The TLS posture for this server has 4 defensible options (A/B/C/D) plus 1 sub-variant of A. Beast is currently NOT a tailnet member; that fact materially shifts the trade-off space.

**PD recommends Option A** (Beast joins tailnet -> Beast nginx -> Beast's own Tailscale FQDN cert at e.g. `beast.tail1216a3.ts.net:8443/mcp`), mirroring the CK MCP pattern. Rationale: zero client onboarding cost, cert auto-renewal via Tailscale, remote CEO access preserved (Cortez offsite / mobile JesAir), pattern consistency with CK reduces cognitive load over time, Tailscale install on Beast is software-only (apt + `tailscale up`) per Hot Take classification.

**Substrate impact:** anchors untouched in all options. Beast gets new infrastructure (apt-installed Tailscale + nginx) under Option A; Option A' shifts that infrastructure to CK; Option B/C/D each have distinct Beast-side touches.

---

## 2. Atlas MCP server scope (informational; not in scope for this paco_request decision)

This section frames the surface area the TLS posture must defend. The actual tool surface is **out of scope for this paco_request** -- ratified separately after TLS lands.

- **Listener host:** Beast (192.168.1.152). NOT CK (CK already serves homelab MCP on 8443; mixing Atlas + homelab MCP on one host couples failure domains).
- **Underlying framework:** FastMCP (mirroring CK pattern, validated through Cycle 1A-1F).
- **Proposed port:** **Beast :8443** (avoids collision with orchestrator on :8000; mirrors CK's `:8443` convention; uses Beast's local 8443 since CK's 8443 stays on CK).
- **Tools to expose (likely candidates, NOT ratified):** `atlas.events.search` (read-only), `atlas.embeddings.upsert` (write), `atlas.embeddings.query` (read), `atlas.inference.history` (read). Exact surface decided in subsequent paco_request after TLS ratified.
- **Expected clients:**
  - CEO (Sloan) Claude Desktop on Mac mini (already tailnet-attached)
  - CEO Claude Desktop on Cortez (Windows; tailnet-attached; offsite use case is real)
  - CEO Claude Desktop on JesAir (MacBook; tailnet-attached; mobile)
  - Cowork bridge (path TBD)
  - Future agents (Alexandra-tier, robotics-tier, etc.)
- **Telemetry:** writes to `atlas.events` with `source='atlas.mcp_server'` (mirrors mcp_client's `source='atlas.mcp_client'` from Cycle 1F).
- **ACL pattern:** mirrors mcp_client's `ACL_DENY_PATTERNS` allowlist + per-tool arg-constraint check; designed in subsequent paco_request.
- **Authn beyond TLS:** v0.2 unless surfaced as need during build.

---

## 3. TLS posture options

### Option A -- Mirror CK pattern (Beast joins tailnet; Beast nginx; Beast's own Tailscale FQDN cert)

**Architecture:**
```
[tailnet client]                                                        [Beast]
                                                                            |
  https://beast.tail1216a3.ts.net:8443/mcp -----[Tailscale tunnel]------> nginx :8443
                                                                          |
                                                                          | (proxy_pass)
                                                                          v
                                                                       FastMCP :8001 (loopback bound)
                                                                          |
                                                                          v
                                                                       Atlas tools (psql, etc.)
```

**Steps to land:**
1. `apt install tailscale` on Beast (single-confirm gate per Hot Take software-install classification)
2. `tailscale up --authkey=...` to join tailnet (auto-receives Tailscale-issued FQDN like `beast.tail1216a3.ts.net`)
3. `tailscale cert beast.tail1216a3.ts.net` to provision auto-renewing cert
4. apt install nginx on Beast (if not present)
5. New nginx vhost on Beast :8443 mirroring CK `/etc/nginx/sites-enabled/mcp` template, with `proxy_pass http://127.0.0.1:8001/mcp/`
6. FastMCP-based Atlas MCP server runs on Beast loopback :8001 (not exposed to LAN)
7. systemd unit for Atlas MCP server (mirror existing pattern)

**Pros:**
- Zero client onboarding cost (any tailnet member already authenticated)
- Cert auto-renewal via Tailscale's mechanism (CK cert is 28+ days old and silently renewed via the same path)
- Pattern consistency with CK: PD/Paco/CEO mental model has ONE TLS strategy across homelab
- Remote CEO access preserved (Cortez offsite / mobile JesAir hit FQDN with no friction)
- FastMCP loopback bind = no LAN exposure of plain HTTP
- Future agents/clients use the same FQDN+port convention

**Cons:**
- Adds Tailscale to Beast (one-time install + auto-update afterward)
- Adds nginx to Beast (lightweight; ~50-line vhost config)
- Two nginx instances to maintain (CK + Beast); minor cognitive load
- Tailscale install on Beast IS software-adjacent (per Hot Take memory: NOT hardware-adjacent in Beast-CMOS sense; CEO single-confirm sufficient)

**Hardware-adjacency classification:** software-only (`apt-get install tailscale` + `tailscale up`); CEO single-confirm gate per Hot Take memory.

### Option A' -- Sub-variant: CK nginx reverse-proxies to Beast LAN

**Architecture:**
```
[tailnet client]                                  [CK]                          [Beast]
                                                                                  |
  https://sloan3.tail1216a3.ts.net:8443/atlas ----> nginx :8443  ---LAN--->  FastMCP :8001
         (existing FQDN, new path /atlas)            new vhost path             (LAN-bound)
```

**Steps to land:**
1. NO Tailscale install on Beast (Beast stays LAN-only)
2. NO nginx install on Beast
3. New `/atlas` location block in CK's existing `mcp` nginx vhost (or new sites-enabled file)
4. CK nginx `proxy_pass http://192.168.1.152:8001/mcp/` over LAN
5. FastMCP-based Atlas MCP server runs on Beast `:8001` LAN-bound (no TLS termination on Beast)

**Pros (vs Option A):**
- ZERO new install on Beast (no Tailscale, no nginx)
- Single TLS-terminating endpoint in the homelab (CK)
- Mirrors single-cert management pattern

**Cons (vs Option A):**
- CK becomes a SPOF for two MCP endpoints (CK reboot kills both homelab-mcp and atlas-mcp)
- Atlas inbound traffic = `tailnet -> CK nginx -> Beast LAN`; minor latency increase, negligible for MCP
- Beast's plain-HTTP listener still present on LAN (mitigated by binding to `192.168.1.152` and CK-only ACL via UFW)
- Doesn't establish Beast as a first-class TLS-terminating host; future Atlas surface growth (more agents reaching Beast directly) requires either (a) keeping CK as proxy forever, or (b) eventual migration to Option A pattern -- migration cost is non-zero
- Couples Atlas's failure domain to CK's failure domain (currently they're independent)

**Hardware-adjacency classification:** none (no Beast-side install).

### Option B -- Beast-local self-signed cert + LAN-only access

**Architecture:**
```
[client device on LAN]                                            [Beast]
                                                                     |
  https://beast.lan:8443/mcp  (self-signed cert, manual trust) ---> nginx :8443
                                                                     |
                                                                     v
                                                                  FastMCP :8001 (loopback)
```

**Steps to land:**
1. NO Tailscale on Beast
2. apt install nginx on Beast
3. `openssl req` self-signed cert pinned to Beast's hostname (or 192.168.1.152 IP SAN)
4. nginx vhost with self-signed cert + manual trust on each client device
5. UFW rule restricts inbound to LAN subnet 192.168.1.0/24
6. FastMCP loopback :8001

**Pros:**
- Lightest install footprint (no Tailscale)
- No tailnet-coupling for Atlas

**Cons:**
- **LAN-ONLY access** -- Cortez offsite, JesAir on travel, mobile sessions all blocked (significant for Sloan's mobile workflow)
- Per-client cert pinning burden (each device's cert trust store needs the self-signed cert added, including future agents)
- Cert rotation is manual (no auto-renewal); rotation incident likelihood non-trivial over time
- Doesn't mirror CK pattern (cognitive load: 2 different TLS strategies)
- Future remote-access need forces migration off this option

**Hardware-adjacency classification:** none (no Tailscale install).

### Option C -- Plain HTTP over Tailscale-only ACL (no TLS at app layer)

**Architecture:**
```
[tailnet client]                                                 [Beast]
                                                                    |
  http://beast.tail1216a3.ts.net:8001/mcp ---[Tailscale tunnel]---> FastMCP :8001 (Tailscale-bound)
        (encryption + auth at WireGuard layer)                       (no nginx)
```

**Steps to land:**
1. apt install tailscale on Beast (same gate as Option A)
2. `tailscale up`
3. NO cert provisioning, NO nginx
4. FastMCP binds directly to Tailscale interface IP (or `0.0.0.0` with Tailscale ACL restricting access)
5. Tailscale ACL permits inbound to Beast :8001 from specified tailnet members

**Pros:**
- Simplest infrastructure (no nginx, no certs)
- Tailscale's WireGuard provides encryption + identity at the network layer (genuinely secure if ACL is correct)
- Single new install (Tailscale only)

**Cons:**
- **Breaks scheme convention** -- clients must use `http://` not `https://`. Some MCP SDKs auto-upgrade to https or refuse plain http; risk of subtle client incompatibility (mcp-python streamablehttp_client handles either, but not all clients tested)
- If Tailscale ACL misconfigured, exposes plain HTTP openly to tailnet-and-LAN combo (config-error blast radius higher than Options A/B)
- Doesn't compose with future authn additions (bearer tokens, API keys) which expect TLS by default
- Still requires Tailscale install on Beast (same gate as A, less gain)
- MCP-Protocol-Version header convention assumes HTTPS in many SDK code paths; not technically required but breaks naive expectation

**Hardware-adjacency classification:** software-only (Tailscale install).

### Option D -- mTLS with client certs (recommend reject)

**Architecture:**
```
[client device with client cert]                              [Beast]
                                                                 |
  https://beast.tail1216a3.ts.net:8443/mcp (mTLS) ----> nginx :8443 (verify client cert)
                                                                 |
                                                                 v
                                                            FastMCP :8001 (loopback)
```

**Steps to land:**
1. Same as Option A baseline (Tailscale + nginx + Tailscale FQDN cert)
2. PLUS: provision a CA, issue per-client certs, install on each device, configure nginx `ssl_verify_client on`
3. Client cert rotation/revocation procedure designed and operationalized

**Pros:**
- Strongest auth model (mutual cert verification)
- Cert pin = strong device identity

**Cons:**
- Per-device client cert provisioning is a chore (CEO's Mac mini, Cortez, JesAir, future agents = each needs cert)
- Cert rotation operational overhead (CA expiry, client cert expiry, revocation list)
- Disproportionate to v0.1 threat model -- Tailscale's tailnet membership already provides device-level auth
- Doesn't compose with Cowork bridge (which can't easily install client certs)
- v0.1 prematurely buys into a complex auth layer when simpler suffices

**Recommendation:** REJECT for v0.1. Reconsider in v0.2+ if specific threat model emerges that tailnet-membership doesn't address.

**Hardware-adjacency classification:** software-only (Tailscale install).

---

## 4. Trade-off matrix

| Dimension | A (Tailscale+nginx mirror) | A' (CK reverse-proxy) | B (self-signed local) | C (plain HTTP via TS) | D (mTLS) |
|---|---|---|---|---|---|
| **Client onboarding cost** | Zero (FQDN works tailnet-wide) | Zero (existing FQDN, new path) | Per-device cert pin | Zero (URL change) | Per-device client cert |
| **Cert provisioning complexity** | Auto via Tailscale | Reuses CK cert | Manual + per-client trust | None | Per-client + CA |
| **Remote CEO access** | Yes (tailnet) | Yes (tailnet via CK) | **LAN-only** | Yes (tailnet) | Yes |
| **Failure domain coupling** | Atlas independent of CK | Atlas couples to CK | Atlas independent | Atlas independent | Atlas independent |
| **Substrate impact on Beast** | apt+nginx | NONE | nginx + manual cert | apt only | apt + nginx |
| **Substrate impact on CK** | NONE | new vhost path | NONE | NONE | NONE |
| **Failure modes** | nginx misconfig; stale cert (mitigated by auto-renewal) | CK SPOF for 2 endpoints | pin drift; LAN-only blocks remote | TS ACL misconfig openly exposes HTTP | cert expiry/rotation; revocation pain |
| **Pattern consistency w/ CK** | Mirrors | Reuses (different) | Diverges | Diverges (HTTP vs HTTPS) | Diverges |
| **Future scaling** (more agents) | High (FQDN-per-host model) | Medium (CK becomes hub) | Medium (per-device pin grows) | Medium (TS ACL hygiene grows) | Low (cert rotation overhead grows) |
| **Hardware-adjacency** | Software install (Tailscale) | None | None | Software install (Tailscale) | Software install (Tailscale) |
| **CEO confirm gate** | Single (Tailscale install) | None | None | Single (Tailscale install) | Single (Tailscale install) |
| **Composability w/ future authn** | High (TLS standard) | High | Medium (cert chain assumptions) | Low (HTTP) | High but redundant |

---

## 5. PD recommendation

**RECOMMEND: Option A** (Beast joins tailnet -> Beast nginx -> Beast's own Tailscale FQDN cert at `beast.tail1216a3.ts.net:8443/mcp` or analogous).

**Rationale (in priority order):**

1. **Zero client onboarding cost is the dominant factor for v0.1.** Every tailnet member -- CEO devices already attached, future agents joining tailnet on first deploy -- gets HTTPS access with valid cert and zero trust-store changes. The savings compound as the agent population grows.

2. **Pattern consistency with CK MCP** means PD/Paco/CEO mental model has ONE TLS strategy across the homelab. Cycle 1G is the second TLS-terminating MCP endpoint; subsequent inbound services (future Alexandra agent endpoints, future RAG retrieval gateways) will reach for the same pattern. Cognitive load minimized over the multi-cycle horizon.

3. **Cert auto-renewal via Tailscale** removes the rotation burden. CK's cert is 28+ days old and has silently renewed via Tailscale's mechanism with zero PD/CEO intervention; same will work for Beast. Manual cert rotation (Option B) is a future operational incident waiting to surface.

4. **Remote CEO access preserved.** Sloan's workflow includes Cortez offsite (coffee shops, travel) and JesAir mobile. Option B's LAN-only mode would force these to fail or fall back to LAN-tethered connectivity -- materially degrades CEO experience.

5. **Tailscale install on Beast is software-only** (`apt-get install tailscale && tailscale up`) per the Hot Take classification. NOT hardware-adjacent in the Beast-CMOS sense. CEO single-confirm gate at implementation-handoff time is sufficient.

6. **Substrate impact contained.** Anchors untouched (B2b + Garage in Docker, unaffected by host-level apt installs). nginx on Beast is lightweight; existing CK `/etc/nginx/sites-enabled/mcp` serves as a 50-line template.

7. **Failure domain independence.** Option A keeps Atlas inbound MCP independent of CK's nginx. CK reboot/restart doesn't take Atlas down. Compared to Option A' which couples both MCP endpoints to CK's uptime.

8. **Composability with future authn.** Option A is standard TLS termination; future bearer-token / API-key middleware drops in as nginx layer or FastMCP middleware. Option C (plain HTTP) requires unwinding a posture before adding authn.

**Option A' as fallback:** If Paco rules that adding Tailscale to Beast is undesirable for non-classification reasons (e.g., wanting Beast's failure domain to remain entirely LAN-isolated, or strategic reasons around Beast's role), Option A' (CK reverse-proxy) is the cleanest fallback. PD bias: still A canonical, but A' is the natural plan-B if A is blocked.

**Option B reject reasoning:** LAN-only blocks the remote CEO access workflow that's already in active use (Cortez offsite). Accepting this regression for the install-footprint savings is not the right trade for v0.1.

**Option C reject reasoning:** Same install footprint as A (Tailscale on Beast) but loses TLS-scheme convention + makes ACL misconfig blast radius bigger. Marginal substrate savings (no nginx, no cert) don't justify the convention break.

**Option D reject reasoning:** Disproportionate complexity for v0.1. Tailnet-membership already provides device-level auth; mTLS adds cert-rotation operational pain without proportional security gain.

---

## 6. Substrate impact detail

**Anchor preservation invariant (must hold across all options):**
- `control-postgres-beast` = `2026-04-27T00:13:57.800746541Z h=healthy r=0` (96+ hrs bit-identical at PRE)
- `control-garage-beast` = `2026-04-27T05:39:58.168067641Z h=healthy r=0` (96+ hrs bit-identical at PRE)
- These are Docker containers; host-level apt installs and nginx config changes do NOT touch them. Anchors survive all 5 options including A's Tailscale install (Tailscale runs as a host-level daemon outside Docker).

**Existing infrastructure NOT touched in any option:**
- mcp_server.py on CK (homelab MCP) -- untouched
- CK nginx config -- untouched in A/B/C/D; extended in A' only (one new vhost path)
- CK `/etc/ssl/tailscale/` certs -- untouched in all options (Beast gets its own under A; CK's stay)
- CK Tailscale state -- untouched in all options
- Beast orchestrator on :8000 (pid=1261, started Apr 23, running ~7 days) -- untouched in all options; new Atlas listener on different port (proposed :8443)
- Beast `kokoro-tts.service` -- untouched
- All Goliath / SlimJim / KaliPi state -- untouched (out of Cycle 1G scope)

**New infrastructure on Beast (varies by option):**
- Option A: `tailscale` package + `nginx` package + `/etc/nginx/sites-enabled/atlas-mcp` vhost + `/var/lib/tailscale/certs/beast.tail1216a3.ts.net.{crt,key}` + atlas-mcp systemd unit
- Option A': none on Beast; new `/atlas` location block in CK `mcp` vhost (or new sites-enabled file) + atlas-mcp systemd unit on Beast (LAN-bound)
- Option B: `nginx` package + self-signed cert at `/etc/ssl/atlas/beast.{crt,key}` + nginx vhost + UFW LAN-only rule + atlas-mcp systemd unit
- Option C: `tailscale` package + atlas-mcp systemd unit (Tailscale-interface-bound)
- Option D: Option A baseline + CA infrastructure + per-client cert provisioning procedure

**Failure mode classification:**
- Options A/A'/D (TLS termination): cert expiry is the primary stale-state risk. Mitigated by auto-renewal in A; manual in B/D.
- Option B (self-signed): per-client trust drift over time as new devices join.
- Option C (plain HTTP + Tailscale ACL): ACL misconfig blast radius highest -- a one-character mistake exposes plain HTTP openly.

---

## 7. Asks for Paco

1. **Ratify Option A** (or amend with additional consideration). PD's recommendation is Option A canonical (Beast joins tailnet, Beast hosts nginx, Beast's own Tailscale FQDN cert). PD's fallback if A is blocked is Option A' (CK reverse-proxy).

2. **Authorize implementation handoff next turn.** Once Option ratified, dispatch build directive in `handoff_paco_to_pd.md` covering: Tailscale install on Beast (CEO single-confirm gate), cert provisioning, nginx vhost, FastMCP loopback bind, atlas-mcp systemd unit, smoke test from a tailnet client.

3. **Bank any v0.2 P5 candidates** surfaced during option exploration. Candidates from this analysis:
   - **v0.2 P5 #16 candidate**: Beast joins tailnet (a side-effect of Option A). May enable other tailnet-only services on Beast in future cycles (e.g., direct SSH from non-CK tailnet members, ts-tunnels for git operations).
   - **v0.2 P5 #17 candidate** (if A' chosen): designate a future migration cycle from CK-reverse-proxy to Beast-direct TLS termination, since growth pressures will eventually push for it.

4. **Confirm CEO single-confirm gate** is sufficient for the Tailscale install on Beast (PD bias: single, per Hot Take software-install classification). Or rule double-confirm if Paco considers tailnet-join consequential enough to warrant heavier gate.

5. **Confirm port 8443 on Beast** as the Atlas inbound MCP listener. Or amend (e.g., :8001 if Paco prefers numeric separation from CK's :8443; or :443 if Paco wants standard HTTPS port).

6. **Confirm tool-surface paco_request as next gate** (separate from build directive) -- once TLS lands, PD writes a tool-surface paco_request enumerating which Atlas tools the inbound MCP server exposes (atlas.events.search, atlas.embeddings.upsert, atlas.embeddings.query, atlas.inference.history were named in Section 2 as likely candidates but not ratified).

---

## Cross-references

- **Predecessor:** `docs/paco_response_atlas_v0_1_cycle_1f_close_confirm.md` (Section 4 dispatched this paco_request gate)
- **Spec:** Atlas v0.1 spec v3 section 8.1G (Atlas MCP server INBOUND on Beast)
- **Pattern reference:** CK MCP at `https://sloan3.tail1216a3.ts.net:8443/mcp` (template for Option A)
- **Hot Take memory:** software-install classification for Tailscale install (CEO single-confirm gate sufficient)
- **5th standing rule:** Verified live block at Section 0 (this document) per the independent verification invariant

-- PD
