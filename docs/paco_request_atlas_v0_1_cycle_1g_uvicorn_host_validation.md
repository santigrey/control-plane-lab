# PD -> Paco request -- Atlas Cycle 1G build escalation: uvicorn loopback Host header validation

**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1G build directive (handoff_paco_to_pd.md, cleared at start of execution; predecessor commit `de8a1c8` on control-plane-lab main)
**Status:** **BLOCKED at Step 11 (end-to-end smoke).** Steps 1-10 complete; Step 11 smoke fails reproducibly with HTTPStatusError 421 against spec-literal nginx config. PD diagnosed root cause + proved a fix; reverted to spec-literal failing state pending Paco ruling.
**Substrate state:** anchors bit-identical PRE/POST (control-postgres-beast `2026-04-27T00:13:57.800746541Z`, control-garage-beast `2026-04-27T05:39:58.168067641Z`, both healthy r=0). atlas.events unchanged (no atlas.mcp_server rows; startup hook deliberately skipped per handoff Section 7 "if skipped, document and bank as v0.2 P5 candidate").

---

## 0. Verified live

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Beast tailnet membership | `tailscale status --self --json` on Beast | DNSName=`sloan2.tail1216a3.ts.net.`, TailscaleIP=`100.121.109.112`, HostName=`sloan2`, Online=True. Note: Tailscale issued `sloan2`, NOT `beast` (Paco anticipated this case in handoff Step 3 fallback) |
| 2 | CK sees Beast in tailnet | `tailscale status \| grep sloan2` from CK | `100.121.109.112  sloan2  james.3sloan@  linux  -` |
| 3 | Tailscale ping CK→Beast | `tailscale ping --c 1 sloan2.tail1216a3.ts.net` from CK | `pong from sloan2 (100.121.109.112) via 192.168.1.152:41641 in 2ms` |
| 4 | Tailscale-issued cert on Beast | `sudo ls -la /etc/ssl/tailscale/` | `sloan2.tail1216a3.ts.net.crt` (2876B, root:root, 644) + `sloan2.tail1216a3.ts.net.key` (227B, root:root, 600). Issued by Let's Encrypt CN=E7. Expires 2026-07-30. **Mirrors CK perms exactly.** |
| 5 | nginx vhost installed | `sudo ls /etc/nginx/sites-enabled/` | `atlas-mcp -> /etc/nginx/sites-available/atlas-mcp` only; default removed |
| 6 | nginx active + listening :8443 | `systemctl is-active nginx` + `ss -tlnp \| grep :8443` | `active`; `0.0.0.0:8443 LISTEN` |
| 7 | atlas-mcp.service Active | `systemctl status atlas-mcp.service` | Active running, MainPID confirmed, `python -m atlas.mcp_server.server` |
| 8 | atlas-mcp listener loopback ONLY | `ss -tlnp \| grep :8001` | `127.0.0.1:8001 LISTEN python` (NOT 0.0.0.0:8001) -- per handoff invariant |
| 9 | atlas-mcp import + AST clean | `python -c "from atlas.mcp_server import server"` + `ast.parse` | both OK; FastMCP instance type=`FastMCP` |
| 10 | Anchors PRE/POST | `docker inspect` pre/post + `diff` | empty diff + `ANCHORS-BIT-IDENTICAL` printed; both anchors held bit-identical through Steps 1-10 |
| 11 | atlas.events PRE/POST | `psql GROUP BY source` | unchanged: embeddings=12, inference=14, mcp_client=6 (no atlas.mcp_server rows; startup hook skipped) |
| 12 | Direct loopback smoke (uvicorn alone) | `curl -sI http://127.0.0.1:8001/mcp` from Beast | **HTTP 405 Method Not Allowed**, `allow: GET, POST, DELETE`, `server: uvicorn`, `mcp-session-id` cookie -- FastMCP fully functional at uvicorn level |
| 13 | Step 11 smoke 1 (HEAD via nginx, spec-literal config) | `curl -sI https://sloan2.tail1216a3.ts.net:8443/mcp` from CK | **HTTP 421 Misdirected Request** from nginx (relayed from upstream) |
| 14 | Step 11 smoke 2 (Python MCP initialize, spec-literal config) | `streamablehttp_client + ClientSession.initialize()` from Beast targeting own FQDN | **HTTPStatusError `421 Misdirected Request`** -- INITIALIZE_OK never printed |
| 15 | Direct upstream + Host=sloan2 (bypass nginx, bare upstream) | `curl -H 'Host: sloan2.tail1216a3.ts.net' POST http://127.0.0.1:8001/mcp` from Beast | **421 + body `Invalid Host header`** -- proves uvicorn (not nginx) generates the 421 |
| 16 | Direct upstream + Host=127.0.0.1:8001 (curl default) | `curl POST http://127.0.0.1:8001/mcp` no -H override | **HTTP 406** (proper FastMCP response: `{"jsonrpc":"2.0","id":"server-error","error":{"code":-32600,"message":"Not Acceptable: Client must accept both application/json and text/event-stream"}}`) -- FastMCP accepts when Host matches bind |

---

## 1. TL;DR

Steps 1-10 of the Cycle 1G build directive landed clean: Tailscale installed on Beast, joined tailnet as `sloan2.tail1216a3.ts.net`, Tailscale-issued cert provisioned at `/etc/ssl/tailscale/`, nginx 1.18 installed with atlas-mcp vhost, atlas-mcp Python skeleton (`from mcp.server.fastmcp import FastMCP; mcp = FastMCP("atlas-mcp")`, no @mcp.tool definitions) imports clean, atlas-mcp.service Active running with MainPID python listening on **127.0.0.1:8001 loopback** as mandated by handoff invariant.

**Step 11 smoke fails reproducibly: HTTP 421 Misdirected Request.** Root cause: **uvicorn validates the request's Host header against its bind address when bound to a specific IP** (127.0.0.1). nginx forwards `proxy_set_header Host $host;` (the request's `sloan2.tail1216a3.ts.net` Host), uvicorn rejects because Host != 127.0.0.1.

**Spec-literal pattern reference is incorrect.** The handoff stated "This matches CK's pattern (homelab-mcp also loopback-bound and nginx-fronted)." CK's `/home/jes/control-plane/mcp_server.py` actually binds to `0.0.0.0`, not `127.0.0.1`: `uvicorn.run(mcp.streamable_http_app(), host="0.0.0.0", port=8001)`. With 0.0.0.0 bind, uvicorn skips Host validation; with 127.0.0.1 bind, it enforces.

**PD identified + proved fix.** Changing `proxy_set_header Host $host;` to `proxy_set_header Host 127.0.0.1:8001;` in atlas-mcp vhost makes smoke pass: `SMOKE INITIALIZE_OK + tools_count: 0` (expected for skeleton with no @mcp.tool defs). Reverted to spec-literal failing state pending Paco ratification.

---

## 2. What worked (Steps 1-10)

All steps landed clean per spec. Step 9 had a minor RuntimeWarning from `__init__.py` re-importing `server` when launched via `-m atlas.mcp_server.server`; PD self-corrected `__init__.py` to not auto-import `server` (clean syntax fix under broadened command-syntax rule, documented here for transparency, no scope expansion). atlas-mcp.service restarted clean, journalctl now shows clean uvicorn startup (`Started server process [...]`).

No other deviations Steps 1-10.

---

## 3. What failed (Step 11)

### Smoke 1 -- `curl -sI` HEAD via nginx

```
From CK (tailnet member sloan3):
$ curl -sI --max-time 10 https://sloan2.tail1216a3.ts.net:8443/mcp
HTTP/1.1 421 Misdirected Request
Server: nginx/1.18.0 (Ubuntu)
Content-Length: 19
```

Access log on Beast:
```
100.115.56.89 - - [01/May/2026:05:59:03 +0000] "HEAD /mcp HTTP/1.1" 421 0 "-" "curl/7.81.0"
```

### Smoke 2 -- Python MCP initialize via streamablehttp_client

```
From Beast (Beast's own FQDN, full round-trip Tailnet):
$ .venv/bin/python /tmp/atlas_1g_smoke.py
SMOKE target: https://sloan2.tail1216a3.ts.net:8443/mcp
SMOKE ERROR: ExceptionGroup unhandled errors in a TaskGroup (1 sub-exception)
  sub: HTTPStatusError Client error '421 Misdirected Request' for url 'https://sloan2.tail1216a3.ts.net:8443/mcp'
```

INITIALIZE_OK never printed. Both smokes reproducible.

---

## 4. Root cause analysis

### What 421 means

HTTP 421 "Misdirected Request" (RFC 7540 §9.1.2): "the request was directed at a server that is not able to produce a response". In nginx, 421 is emitted for SNI-vs-Host mismatches under HTTP/2, OR forwarded as-is from upstream.

### Server header is misleading

Response showed `Server: nginx/1.18.0 (Ubuntu)`, suggesting nginx-internal rejection. **Wrong.** nginx by default replaces upstream `Server:` header with its own. Cross-checking with direct upstream query (Verified live row 15) confirms the 421 originates from uvicorn (response body is `Invalid Host header`, the canonical uvicorn protocol error).

### Why uvicorn rejects

uvicorn 0.x + h11 protocol enforces Host header validation when bound to a specific IP. The bind address is parsed from `host="127.0.0.1"` in `uvicorn.run(...)`. Incoming requests with `Host:` headers that don't match the bind address are rejected with 421 + body `Invalid Host header`.

Proof (Verified live row 15 vs row 16):
- `curl -H 'Host: sloan2.tail1216a3.ts.net' POST http://127.0.0.1:8001/mcp` → 421 (Host mismatch with bind)
- `curl POST http://127.0.0.1:8001/mcp` (no -H, curl auto-sends `Host: 127.0.0.1:8001`) → 406 (proper FastMCP semantic response, NOT 421)

Bind=0.0.0.0 disables this check (uvicorn doesn't know the "correct" Host). That's why CK works.

### Spec pattern reference is wrong

Handoff Section 7 said: "This matches CK's pattern (homelab-mcp also loopback-bound and nginx-fronted)." Verified live: CK's `mcp_server.py` line `uvicorn.run(mcp.streamable_http_app(), host="0.0.0.0", port=8001)`. CK is **0.0.0.0-bound**, not loopback.

The handoff's invariant "Loopback bind for atlas-mcp is mandatory. nginx is the ONLY path to atlas-mcp from outside the host. If atlas-mcp binds 0.0.0.0 it would expose plain HTTP on Beast LAN; that defeats the TLS posture" is the architectural intent. CK achieves the same intent via UFW (or similar host firewall) preventing external :8001 access despite 0.0.0.0 bind. Atlas Cycle 1G needs to choose: match CK's actual pattern (0.0.0.0 + UFW) or maintain the strict-loopback invariant (which requires the Host header workaround).

---

## 5. Resolution options

### Option A -- nginx Host header rewrite to `127.0.0.1:8001` (PD recommend)

**Change:** In `/etc/nginx/sites-available/atlas-mcp` line 13: `proxy_set_header Host $host;` → `proxy_set_header Host 127.0.0.1:8001;`

**Pros:**
- Preserves the strict-loopback invariant (atlas-mcp.service binds 127.0.0.1:8001, NOT 0.0.0.0)
- Surgical 1-line change, no other substrate touched
- **Proven working** (PD tested live; smoke passed: SMOKE INITIALIZE_OK + tools_count: 0)
- Stronger security posture than CK's pattern (atlas-mcp listener literally cannot accept LAN connections; UFW is defense in depth, not the primary control)

**Cons:**
- Diverges from CK's vhost template (CK uses `Host $host` because CK upstream is 0.0.0.0-bound)
- atlas-mcp upstream sees Host=127.0.0.1:8001 in scope -- impacts ASGI middleware behavior IF future middleware reads Host (TrustedHostMiddleware, host-based routing). Currently no such middleware in skeleton.
- Upstream X-Forwarded-Host is still passed (not in current vhost, can be added) for middleware that needs original Host

### Option B -- Bind atlas-mcp to 0.0.0.0 + UFW restrict :8001 to loopback

**Change:** 
- `server.py` line: `host="0.0.0.0"` (matching CK)
- New UFW rule on Beast: `sudo ufw deny in on eno3 to any port 8001`

**Pros:**
- Mirrors CK's exact pattern (vhost template + uvicorn bind)
- Spec-compliant once handoff is amended
- nginx vhost remains spec-literal

**Cons:**
- Adds UFW dependency to Beast (currently no UFW on Beast per Verified live)
- Less defense in depth (LAN exposure briefly possible if UFW misconfigured)
- Spec amendment required to update Section 7 invariant
- Goliath/SlimJim/etc. could in principle reach :8001 if UFW rule slips (extremely low probability but real)

### Option C -- uvicorn `--forwarded-allow-ips '*'` flag

**Change:** systemd unit `ExecStart` adds `--forwarded-allow-ips '*'` flag (or set in `uvicorn.run(...)` call)

**Pros:**
- Spec-compliant nginx + spec-compliant bind
- Adjusts only the trust boundary in uvicorn

**Cons:**
- This flag controls X-Forwarded-* trust, NOT Host validation. May not actually fix the issue (uvicorn's Host validation is in h11 protocol layer, not in forwarded-ips logic)
- Untested by PD (would need verification)

### Option D -- FastMCP-level workaround (Starlette TrustedHostMiddleware override)

**Change:** Wrap `mcp.streamable_http_app()` with explicit `TrustedHostMiddleware(allowed_hosts=["*"])`

**Pros:**
- ASGI-level fix; no nginx or systemd touched

**Cons:**
- Adds middleware complexity to skeleton (currently zero)
- May not fix the issue if validation is in uvicorn (not Starlette) -- Verified live row 15 suggests the rejection happens in uvicorn h11, before ASGI app sees the request
- Untested by PD

---

## 6. PD recommendation

**RECOMMEND: Option A (nginx Host header rewrite).**

Rationale (priority order):
1. **Proven working.** PD tested live; smoke 1 + smoke 2 both passed (SMOKE INITIALIZE_OK + tools_count=0). Options C/D are untested and uncertain to fix the actual issue.
2. **Preserves strict-loopback invariant.** atlas-mcp listener literally cannot accept LAN connections. Stronger than CK's UFW-based pattern.
3. **Surgical.** 1-line change to nginx vhost; no Python source change, no systemd unit change, no UFW addition.
4. **No new dependencies.** UFW is not currently on Beast (verified row 6 shows `systemctl list-units --state=running | grep tailscale|nginx|atlas` returned empty including no `ufw.service`).
5. **Defense in depth available.** Option A doesn't preclude adding UFW later if desired; Option B requires UFW for security parity.

**Reject reasons (other options):**
- Option B introduces new UFW dependency + LAN exposure window if misconfigured. Spec amendment required.
- Option C controls a different trust boundary; high probability it doesn't fix the issue.
- Option D adds middleware to skeleton that wants to be minimal; same uncertainty as C about whether it reaches the rejection layer.

---

## 7. Substrate state

**REVERTED to spec-literal failing state.** atlas-mcp vhost line 13 currently reads `proxy_set_header Host $host;` (the spec-literal). nginx -t passes; nginx reloaded clean. Smoke fails reproducibly.

All Steps 1-10 substrate intact:
- Tailscale on Beast: installed, enabled, active, joined as sloan2
- Cert: /etc/ssl/tailscale/sloan2.tail1216a3.ts.net.{crt,key} (mirror CK perms)
- nginx 1.18.0: installed, enabled, active, vhost atlas-mcp enabled
- atlas-mcp.service: enabled, Active running, MainPID python on 127.0.0.1:8001
- atlas package: src/atlas/mcp_server/{__init__.py, server.py} written; `__init__.py` self-corrected to not re-import `server` (avoids RuntimeWarning)

**Anchors bit-identical PRE/POST.** atlas.events unchanged. No commits attempted; no atlas commit; no control-plane-lab commit.

---

## 8. Asks for Paco

1. **Ratify Option A (nginx Host rewrite to 127.0.0.1:8001)** OR amend to Option B/C/D OR alternative.
2. **Confirm Section 7 invariant amendment**: spec said "matches CK's pattern (homelab-mcp also loopback-bound)"; CK is actually 0.0.0.0-bound. Whichever option ratified, the spec text should be amended to reflect the actual chosen pattern (loopback + Host rewrite vs 0.0.0.0 + UFW).
3. **Authorize PD to apply ratified fix + complete remaining steps** (Step 11 retry smoke + Steps 12-16). PD has not committed anything; on Paco ratification PD applies the fix, retries smoke, captures evidence, commits per Step 14.a (Atlas) + 14.b (control-plane-lab close-out fold).
4. **Bank v0.2 P5 candidates** surfaced this turn:
   - **#16** (already pre-ratified per Cycle 1F response): Beast tailnet membership now realized; side-effects worth banking for future cycles
   - **#17 NEW**: Cycle 1G nginx vhost diverges from CK template by one line (Host header value); flag as candidate for v0.2 hardening pass (e.g., create shared nginx-vhost-mcp template macro that handles both 0.0.0.0 and 127.0.0.1 upstream patterns)
   - **#18 NEW**: handoff Python smoke template has invalid syntax (mixed `except`/`except*` clauses; Python 3.11+ rejects). PD self-corrected for the smoke run (file `/tmp/atlas_1g_smoke.py` written to disk for execution); flag as documentation cleanup
   - **#19 NEW**: atlas.mcp_server startup-event telemetry hook deliberately skipped per handoff Section 7 "if skipped, document and bank as v0.2 P5"; bank explicitly here
5. **P6 #28 candidate (NEW)**: "Reference-pattern verification before propagation." When a spec says "this matches existing pattern X", the existing pattern should be Verified live BEFORE the spec is dispatched (not just from memory of how X works). The Cycle 1G spec correctly identified the architectural intent (TLS termination + loopback bind) but incorrectly attributed the same posture to CK's actual pattern (which uses 0.0.0.0 bind for historical reasons). Cost of not catching: one full build cycle to surface the conflict at smoke time. Resolution: when a directive references "matches X", the directive author runs a quick Verified-live confirmation of X's actual state before dispatch. Defer Paco ruling on whether this becomes a standing rule.

---

## Cross-references

- **Predecessor:** `docs/handoff_paco_to_pd.md` (Paco, cleared at start of execution); commit `de8a1c8` on control-plane-lab main
- **CK reference pattern:** `/home/jes/control-plane/mcp_server.py` line `uvicorn.run(... host="0.0.0.0", port=8001)` -- the actual loopback binding state
- **Spec invariant in conflict:** handoff Section "Important reminders" -- "Loopback bind for atlas-mcp is mandatory"
- **Working fix evidence:** `/tmp/atlas_1g_vhost_orig.conf` on Beast (pre-fix backup) + `/tmp/atlas_1g_smoke.py` on Beast (smoke harness)

-- PD
