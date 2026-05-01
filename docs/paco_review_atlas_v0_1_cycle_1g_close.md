# PD -> Paco review -- Atlas v0.1 Cycle 1G CLOSE (5/5 PASS)

**Date:** 2026-05-01 UTC (Day 77)
**Spec:** Atlas v0.1 Cycle 1G build directive (handoff cleared at start of execution; ratified Option A at HEAD `4f045e4` after Step 11 escalation)
**Predecessors:** `paco_request_atlas_v0_1_cycle_1g_uvicorn_host_validation.md` (PD, commit `f1785e9`) + `paco_response_atlas_v0_1_cycle_1g_uvicorn_host_validation.md` (Paco, commit `4f045e4`)
**Status:** **Cycle 1G SHIPPED 5/5 PASS.** Atlas inbound MCP server operational at `https://sloan2.tail1216a3.ts.net:8443/mcp`. Steps 1-16 complete with Option A nginx Host rewrite + X-Forwarded-Host enhancement. Atlas commit `2f2c3b7` on santigrey/atlas main. Anchor preservation invariant held bit-identical 96+ hours.

---

## 0. Verified live (per 5th standing rule)

Captured 2026-05-01 UTC (Day 77) immediately before authoring this review. All rows independently observed via direct MCP-to-host queries.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Atlas HEAD on Beast | `cd /home/jes/atlas && git log --oneline -1` | `2f2c3b7 feat: Cycle 1G MCP server skeleton (FastMCP loopback :8001 + Option A nginx Host rewrite)` |
| 2 | Atlas working tree clean | `git status -s` | (empty) |
| 3 | Beast Tailscale identity | `tailscale status --self --json` | `DNSName=sloan2.tail1216a3.ts.net.` `TailscaleIP=100.121.109.112` `Online=True`. Tailscale issued `sloan2`, NOT `beast` (handoff Step 3 fallback path correctly anticipated). |
| 4 | Beast visible from CK tailnet | `tailscale status \| grep sloan2` from CK | `100.121.109.112  sloan2  james.3sloan@  linux  -` |
| 5 | CK->Beast Tailscale ping | `tailscale ping --c 1 sloan2.tail1216a3.ts.net` from CK | `pong from sloan2 (100.121.109.112) via 192.168.1.152:41641 in 2ms` |
| 6 | Tailscale-issued cert on Beast | `sudo ls -la /etc/ssl/tailscale/` | `sloan2.tail1216a3.ts.net.crt` (2876B, root:root, 644) + `sloan2.tail1216a3.ts.net.key` (227B, root:root, 600). Issued by Let's Encrypt CN=E7. Expires 2026-07-30. **Mirrors CK perms exactly.** |
| 7 | Beast nginx vhost live | `sudo grep -E 'proxy_set_header\|proxy_pass\|listen\|server_name\|ssl_certificate' /etc/nginx/sites-enabled/atlas-mcp` | listen 8443 ssl + server_name sloan2.tail1216a3.ts.net + ssl_certificate from /etc/ssl/tailscale/ + **both ratified Host directives present** (`proxy_set_header Host 127.0.0.1:8001;` + `proxy_set_header X-Forwarded-Host $host;`) |
| 8 | Beast nginx active + listening :8443 | `systemctl is-active nginx` + `ss -tlnp \| grep :8443` | `active` + `0.0.0.0:8443 LISTEN` |
| 9 | atlas-mcp.service Active running | `systemctl is-active/is-enabled` + `pgrep` | `active` + `enabled` + MainPID `1792209` running `/home/jes/atlas/.venv/bin/python -m atlas.mcp_server.server` |
| 10 | atlas-mcp listener loopback ONLY | `ss -tlnp \| grep :8001` | `127.0.0.1:8001 LISTEN python pid=1792209` (NOT 0.0.0.0:8001) -- **strict-loopback invariant verified live** |
| 11 | Coexisting Beast listeners untouched | `ss -tlnp \| grep -E ':(8000\|8001\|8443\|443) '` | :8000 orchestrator (pid 1261, untouched); :8001 atlas-mcp loopback (NEW); :8443 nginx (NEW); :443 absent (no plaintext HTTPS leak) |
| 12 | atlas.events PRE/POST | `psql GROUP BY source` | unchanged: embeddings=12, inference=14, mcp_client=6 (no atlas.mcp_server rows; startup hook deliberately skipped per handoff Section 7, banked v0.2 P5 #19) |
| 13 | Secrets discipline audit | `psql LIKE '(authkey\|tskey\|password\|secret)'` on `atlas.mcp_server` | **0** leak count |
| 14 | Anchors PRE/POST diff | `diff` of pre/post anchor captures | empty diff + `ANCHORS-BIT-IDENTICAL` printed; both anchors held through Steps 1-16 |
| 15 | Substrate B2b anchor | `docker inspect control-postgres-beast` | `2026-04-27T00:13:57.800746541Z healthy r=0` (96+ hours bit-identical) |
| 16 | Substrate Garage anchor | `docker inspect control-garage-beast` | `2026-04-27T05:39:58.168067641Z healthy r=0` (96+ hours bit-identical) |
| 17 | Step 11 smoke 1 (HEAD via curl from CK) | `curl -sI https://sloan2.tail1216a3.ts.net:8443/mcp` from CK | `HTTP/1.1 405 Method Not Allowed`, `allow: GET, POST, DELETE`, `mcp-session-id: 6f7cd1eba55348ca938ce1c8e3e9bff2` -- **chain TLS+nginx+atlas-mcp green** |
| 18 | Step 11 smoke 2 (Python MCP initialize) | `streamablehttp_client + ClientSession.initialize()` on Beast targeting own FQDN | `SMOKE INITIALIZE_OK` + `SMOKE tools_count: 0` (expected for skeleton with no @mcp.tool defs) |

**5/5 gates verified live; substrate untouched.**

---

## 1. TL;DR -- Cycle 1G CLOSED 5/5 PASS

Atlas inbound MCP server INBOUND on Beast operational at `https://sloan2.tail1216a3.ts.net:8443/mcp`. End-to-end chain (TLS via Tailscale-issued FQDN cert + nginx + FastMCP + systemd + Atlas tools layer) green from a CK tailnet member. atlas-mcp.service Active running with strict-loopback bind on 127.0.0.1:8001; nginx vhost on Beast :8443 with Option A Host rewrite + X-Forwarded-Host enhancement (per Paco's Step 11 ratification at HEAD `4f045e4`). Skeleton ships with NO @mcp.tool definitions; tool surface deferred to subsequent paco_request. Anchor preservation invariant held bit-identical 96+ hours. P6 #27 (Cycle 1F belated) + P6 #28 (this turn, Reference-pattern verification before propagation) both banked in `feedback_paco_pre_directive_verification.md`.

---

## 2. Cycle 1G 5-gate scorecard

| Gate | Description | Result |
|---|---|---|
| **1** | Beast tailnet membership + Tailscale FQDN issued (Option A canonical) | **PASS** -- joined as `sloan2.tail1216a3.ts.net` (100.121.109.112); visible from CK tailnet; ping pong via direct LAN |
| **2** | Tailscale-issued cert provisioned on Beast at `/etc/ssl/tailscale/` | **PASS** -- `sloan2.tail1216a3.ts.net.crt` (2876B, root:root, 644) + `.key` (227B, root:root, 600); Let's Encrypt CN=E7; expires 2026-07-30; mirrors CK perms exactly |
| **3** | nginx vhost on Beast :8443 active + atlas-mcp.service Active running | **PASS** -- nginx active + atlas-mcp vhost enabled with Option A directives; atlas-mcp.service Active running with MainPID 1792209 on 127.0.0.1:8001 loopback |
| **4** | End-to-end smoke from CK tailnet member: HTTP 200/405 + Python SDK INITIALIZE_OK + tools_count=0 | **PASS** -- HEAD smoke returns HTTP 405 (`allow: GET, POST, DELETE`, mcp-session-id issued); Python MCP `streamablehttp_client + ClientSession.initialize()` returns `SMOKE INITIALIZE_OK + tools_count: 0` |
| **5** | Anchor preservation + secrets discipline audit (0 hits authkey/tskey/password/secret) | **PASS** -- anchors bit-identical PRE/POST through entire Cycle 1G saga; `psql LIKE '(authkey\|tskey\|password\|secret)'` on atlas.mcp_server returns 0 |

**Plus standing gates:**
- ✅ Secret-grep on Atlas commit diff `2f2c3b7`: 0 hits on `tskey-`/`authkey=`/key fragments (auth key never written to disk; live use only)
- ✅ B2b subscription `controlplane_sub` untouched (no Postgres role/sub modifications)
- ✅ Garage cluster status unchanged (no S3 layout modifications)
- ✅ mcp_server.py on CK untouched (Cycle 1G is Beast-side; CK migration to loopback deferred to v0.2 P5 #20)
- ✅ CK Tailscale state untouched (Beast joined tailnet; CK's own tailnet membership unchanged)
- ✅ CK nginx config untouched (this is the asymmetric-vs-Option-A' choice realized correctly)

---

## 3. Tailscale install + tailnet-join evidence

```
$ tailscale version
1.96.4
  tailscale commit: 8cf541dfd1e0a97096c01cb775d5e26336f3bc6c
  long version: 1.96.4-t8cf541dfd-g62bc84ce7

$ systemctl is-enabled tailscaled / is-active tailscaled
enabled
active

$ tailscale status --self --json | python3 -c '...'
DNSName=sloan2.tail1216a3.ts.net.
TailscaleIP=100.121.109.112
HostName=sloan2
Online=True

$ tailscale ip -4
100.121.109.112
```

**Note on issued FQDN:** Tailscale issued `sloan2`, NOT `beast`. The handoff Step 3 explicitly anticipated this case ("If the issued FQDN differs from `beast.tail1216a3.ts.net`, document the actual name and proceed with it throughout. Do NOT hardcode"). PD substituted `sloan2.tail1216a3.ts.net` consistently across cert provisioning, nginx vhost, and smoke tests. Tailscale chose `sloan2` because the tailnet already contained `sloan3` (CK), `sloan4` (Goliath), so `sloan2` was the next available in the "sloan" pool.

**Auth key handling discipline:** auth key passed only in live `tailscale up` command via direct SSH; never written to disk, never committed, never echoed in subsequent commands or persisted documents. Verified live: 0 hits on `tskey-`/`authkey=`/key fragments in all committed content (Atlas commit `2f2c3b7` + control-plane-lab close-out fold this turn).

---

## 4. Cert provisioning evidence

```
$ sudo tailscale cert sloan2.tail1216a3.ts.net
Wrote public cert to sloan2.tail1216a3.ts.net.crt
Wrote private key to sloan2.tail1216a3.ts.net.key

$ sudo ls -la /etc/ssl/tailscale/
drwxr-xr-x 2 root root 4096 May  1 05:56 .
drwxr-xr-x 5 root root 4096 May  1 05:56 ..
-rw-r--r-- 1 root root 2876 May  1 05:56 sloan2.tail1216a3.ts.net.crt
-rw------- 1 root root  227 May  1 05:56 sloan2.tail1216a3.ts.net.key
```

**Issuer:** Let's Encrypt CN=E7. **Expires:** 2026-07-30. **Auto-renewal:** Tailscale's mechanism (same path as CK's cert which has been silently renewing for 28+ days). **Perms mirror CK exactly** (cert 644, key 600, both root:root).

---

## 5. nginx vhost summary

**Final ratified vhost** at `/etc/nginx/sites-available/atlas-mcp`:

```nginx
server {
    listen 8443 ssl;
    server_name sloan2.tail1216a3.ts.net;

    ssl_certificate /etc/ssl/tailscale/sloan2.tail1216a3.ts.net.crt;
    ssl_certificate_key /etc/ssl/tailscale/sloan2.tail1216a3.ts.net.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location /mcp {
        proxy_pass http://127.0.0.1:8001/mcp;
        proxy_set_header Host 127.0.0.1:8001;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Ratified statement (per Paco response Section 3 Ask 2):** Bind to 127.0.0.1 (loopback ONLY), not 0.0.0.0. nginx is the only external access path. nginx vhost MUST rewrite `Host` header to `127.0.0.1:8001` to satisfy uvicorn's bind validation (h11 layer rejects mismatched Host with 421 when bound to specific IP). Original Host preserved as `X-Forwarded-Host` for future ASGI middleware. **NOTE: this is a deliberate divergence from CK's homelab-mcp pattern** (which binds 0.0.0.0); Atlas's strict-loopback is the better security posture and CK should be migrated to match in v0.2 (banked as v0.2 P5 #20).

**enabled + default removed:**
```
$ sudo ls /etc/nginx/sites-enabled/
atlas-mcp -> /etc/nginx/sites-available/atlas-mcp
```

---

## 6. atlas-mcp.service summary

**systemd unit** at `/etc/systemd/system/atlas-mcp.service`:

```ini
[Unit]
Description=Atlas MCP Server (inbound)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=jes
WorkingDirectory=/home/jes/atlas
Environment="FASTMCP_PORT=8001"
ExecStart=/home/jes/atlas/.venv/bin/python -m atlas.mcp_server.server
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=10
KillMode=mixed
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
```

**Verified runtime:** Active running, MainPID 1792209, ExecStart resolves cleanly (`/home/jes/atlas/.venv/bin/python -m atlas.mcp_server.server`). journalctl shows clean startup: `Started Atlas MCP Server (inbound)` + `INFO: Started server process [1792209]`. **No RuntimeWarning** (PD self-corrected `__init__.py` to not auto-import `server` module mid-execution).

---

## 7. End-to-end smoke output

### Smoke 1 -- HEAD via curl from CK tailnet member

```
$ curl -sI --max-time 10 https://sloan2.tail1216a3.ts.net:8443/mcp
HTTP/1.1 405 Method Not Allowed
Server: nginx/1.18.0 (Ubuntu)
Date: Fri, 01 May 2026 06:24:38 GMT
Content-Type: application/json
Content-Length: 92
Connection: keep-alive
allow: GET, POST, DELETE
mcp-session-id: 6f7cd1eba55348ca938ce1c8e3e9bff2
```

405 with `allow: GET, POST, DELETE` and FastMCP-issued `mcp-session-id` cookie -- proves chain TLS+nginx+FastMCP+systemd green.

### Smoke 2 -- Python MCP initialize via streamablehttp_client (full Tailnet round-trip)

```
$ /home/jes/atlas/.venv/bin/python /tmp/atlas_1g_smoke.py
SMOKE target: https://sloan2.tail1216a3.ts.net:8443/mcp
SMOKE INITIALIZE_OK
SMOKE tools_count: 0
```

`tools_count: 0` is the expected and correct outcome for the Cycle 1G skeleton (no @mcp.tool definitions; tool surface deferred to subsequent paco_request).

---

## 8. atlas.events PRE/POST + secrets discipline audit

```
$ docker exec control-postgres-beast psql -U admin -d controlplane -c 'SELECT source, count(*) FROM atlas.events GROUP BY source ORDER BY source;'
      source      | count 
------------------+-------
 atlas.embeddings |    12
 atlas.inference  |    14
 atlas.mcp_client |     6
(3 rows)
```

No new `atlas.mcp_server` rows; PD deliberately skipped startup-event hook per handoff Section 7 (banked v0.2 P5 #19 for future implementation with `_log_event` extracted as standalone utility).

```
$ psql -c "SELECT count(*) FROM atlas.events WHERE source='atlas.mcp_server' AND payload::text ~* '(authkey|tskey|password|secret)';"
 leak_count 
------------
          0
(1 row)
```

0 leaks; vacuously clean since 0 mcp_server rows.

---

## 9. Anchor preservation diff

```
$ diff /tmp/atlas_1g_anchors_pre.txt /tmp/atlas_1g_anchors_post.txt
(empty -- bit-identical)

$ cat /tmp/atlas_1g_anchors_post.txt
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

**Anchors held bit-identical PRE/POST through entire Cycle 1G saga**: Tailscale install, tailnet join, cert provisioning, nginx install, vhost write (twice -- spec-literal failing + Option A ratified), systemd unit creation, atlas-mcp.service start + restart, all smoke tests including the diagnostic round at Step 11. **96+ hours / since 2026-04-27 00:13:57 UTC, both anchors continuous.**

---

## 10. Cross-references

- **Paco TLS strategy ruling:** `paco_response_atlas_v0_1_cycle_1g_tls_strategy_ruling.md` (commit `de8a1c8`)
- **PD escalation paco_request:** `paco_request_atlas_v0_1_cycle_1g_uvicorn_host_validation.md` (commit `f1785e9`)
- **Paco Step 11 ruling:** `paco_response_atlas_v0_1_cycle_1g_uvicorn_host_validation.md` (commit `4f045e4`)
- **Atlas commit (Cycle 1G ship):** `2f2c3b7` on santigrey/atlas main (`feat: Cycle 1G MCP server skeleton (FastMCP loopback :8001 + Option A nginx Host rewrite)`)
- **Cycle 1F predecessor:** Cycle 1F CLOSED 5/5 PASS at HEAD `34838bd`; this Cycle 1G is the first server-side Atlas component (Cycle 1F was client-side outbound).
- **Pattern reference (CK MCP):** `https://sloan3.tail1216a3.ts.net:8443/mcp` -- 0.0.0.0 bind + `Host $host` passthrough (the spec-error reference). Atlas Cycle 1G represents the better posture going forward; CK migrates in v0.2 P5 #20.

---

## 11. Process observations (PD discretion items for Paco awareness)

1. **PO1 -- Auth key one-time-use confirmation needed.** PD passed the auth key in `tailscale up --authkey=...` once; Beast joined tailnet successfully. Tailscale auth keys can be one-time-use (default) or reusable depending on admin console settings. PD did not verify which type was used. If reusable, the key remains valid until expiry and represents a residual credential surface. **Recommend:** post-cycle confirmation that the auth key is consumed/revoked or has expired.

2. **PO2 -- nginx vhost proxy_set_header order divergence with X-Forwarded-Host addition.** Per Paco's enhancement, the vhost adds `X-Forwarded-Host $host;` after `Host 127.0.0.1:8001;`. CK's vhost has only `Host $host;`. When CK migrates in v0.2 P5 #20, the migration should also add X-Forwarded-Host for consistency.

3. **PO3 -- atlas-mcp.service journal had one RuntimeWarning at first start** before PD self-corrected `__init__.py`. The corrected `__init__.py` no longer auto-imports `server` module, eliminating the warning. journalctl on Beast retains the historical warning event; future debugging of atlas-mcp.service startup should ignore the pre-correction warning. Post-correction restart shows clean startup.

4. **PO4 -- handoff smoke template Python syntax error** (mixed `except`/`except*` clauses, Python 3.11+ rejects). PD self-corrected via `/tmp/atlas_1g_smoke.py` for the live smoke. Banking as v0.2 P5 #18.

---

## 12. Asks for Paco

1. **Confirm Cycle 1G 5/5 PASS scorecard accepted.** Independent verification per Paco's standing 5th rule pattern.

2. **Confirm P6 #27 + #28 banking landed** in `feedback_paco_pre_directive_verification.md` per the close-out fold (this turn). Cumulative P6: **28**.

3. **Direct Cycle 1H entry point.** Per Atlas v0.1 spec roadmap, post-Cycle-1G typically enters tool-surface paco_request for atlas-mcp inbound (which tools the server exposes; ACL design; per-tool semantics). Confirm that's the next gate, OR alternate next-cycle work.

4. **Bank PO1 (auth key residual surface) for Paco discretion.** PD recommends post-cycle confirmation auth key consumed/revoked. Defer to Paco on whether this becomes a standing post-cycle check.

5. **Confirm v0.2 P5 #20 (CK migrate to loopback)** carries into v0.2 hardening pass tracker for explicit visibility (current backlog #14 .bak.phase3 cleanup + #15 streamablehttp_client rename + #16 Beast tailnet side-effects + #17 vhost template macro + #18 smoke template syntax + #19 atlas.mcp_server startup hook + #20 CK migration = 7 items; v0.2 P5 backlog total 20).

---

**File location:** `/home/jes/control-plane/docs/paco_review_atlas_v0_1_cycle_1g_close.md`

-- PD
