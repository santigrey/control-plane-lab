# Paco Request — Atlas v0.1 Cycle 1F — MCP Transport Hang from Beast

**Filed by:** PD
**Date:** 2026-04-30
**Cycle:** 1F (MCP client gateway)
**Status:** HALTED at Step 3 (connectivity smoke)
**Spec-named file (`_auth.md`) intentionally not used** — this is not a 401 / auth error; symptom is upstream transport hang specific to Beast source.

---

## 1. What was attempted

Step 3 of the Cycle 1F handoff: connectivity smoke from Beast against `https://sloan3.tail1216a3.ts.net:8443/mcp` using `mcp.client.streamable_http.streamablehttp_client` + `ClientSession.list_tools()`.

Pre-flight (Steps 1–2) completed successfully:
- Beast anchors PRE captured (B2b `2026-04-27T00:13:57.800746541Z`, Garage `2026-04-27T05:39:58.168067641Z`)
- atlas.events PRE: `atlas.embeddings=2`, `atlas.inference=4`
- /etc/hosts entry on Beast added: `192.168.1.10 sloan3.tail1216a3.ts.net`
- `getent hosts sloan3.tail1216a3.ts.net` → `192.168.1.10`

## 2. Symptom

`session.initialize()` hangs indefinitely. Internal 15s `asyncio.timeout` fires; transport context exits cleanly; client reports `TimeoutError`. nginx access log shows `499 0` (client closed before nginx responded).

Replicated with raw `curl -X POST` (same Accept headers, same JSON-RPC initialize body) — also hangs ~12s and gets killed by timeout. Confirms not an SDK-specific issue.

## 3. What works

The MCP server itself works fine for other clients. From `/var/log/nginx/access.log` last 30 entries:

```
23  200  100.102.87.70   (Mac mini Claude Desktop, node UA, Tailscale source)
 5  301  127.0.0.1
 2  499  192.168.1.152   (Beast, python-httpx + curl, LAN source)
```

Mac mini POSTs return 200 in <100ms with response bodies 487–4995 bytes. Beast POSTs hang and get 499.

## 4. Diagnostic checks performed

### 4.1 Network reachability (Beast → CK:8443)
- `cat < /dev/tcp/sloan3.tail1216a3.ts.net/8443` — TCP open
- `openssl s_client -connect sloan3.tail1216a3.ts.net:8443 -servername sloan3.tail1216a3.ts.net` — TLS handshake completes
- Cert SAN: `DNS:sloan3.tail1216a3.ts.net` (matches via /etc/hosts override)
- `curl -sk -m 7 https://sloan3.tail1216a3.ts.net:8443/mcp` → `http_code=000 time=7.000` (hung GET — expected since /mcp is POST)

### 4.2 CK-side state
- nginx listening on 0.0.0.0:8443 (PID 849xxx workers)
- `mcp_http.py` running as PID 3631249, uvicorn on 0.0.0.0:8001
- `mcp_server.py` is FastMCP; no auth middleware; no source-IP gating; `ALLOWED_HOSTS` is for tool args, not HTTP auth
- `/etc/nginx/sites-enabled/mcp` proxies `location /mcp { proxy_pass http://127.0.0.1:8001/mcp; ... }` with `Connection "upgrade"` header rewrite
- nginx error log shows unrelated OAuth metadata 404s from a third client (100.86.193.45) — predates my tests

### 4.3 Python SDK trace from Beast
```
step1: opening transport         ← entered
step2: transport open            ← streamablehttp_client context entered (POST connection succeeded)
step3: session created, initializing  ← ClientSession entered
[15s elapsed]
TimeoutError                     ← session.initialize() never received response
```

### 4.4 Raw curl POST from Beast
```
BODY = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.0"}}}'
timeout 12 curl -sk -X POST https://sloan3.tail1216a3.ts.net:8443/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  --data "$BODY"
```
Returned no body within 12s; killed by timeout. nginx logged 499.

## 5. Hypothesis (for Paco)

The MCP server replies normally for Tailscale-source clients (100.102.87.70 — Mac mini) but the same uvicorn+FastMCP stack hangs initialize response for LAN-source clients (192.168.1.152 — Beast routed via /etc/hosts override).

Candidate causes (none of which I can rule in/out without Paco direction):

A. **Tailscale-bound listener.** `mcp.streamable_http_app()` may be binding/preferring a Tailscale interface, with LAN-source POSTs accepted at TCP level but starved at handler dispatch.

B. **Header difference.** node MCP client sends headers (e.g., session-id, MCP-Protocol-Version) the Python SDK or curl doesn't, and FastMCP holds the response open waiting for them. But the same Python SDK works elsewhere per upstream docs, so this would be specific to the Tailscale-vs-LAN environment.

C. **nginx Connection "upgrade" rewrite + LAN client.** node clients negotiate one mode; LAN-source clients another; nginx's hardcoded `Connection "upgrade"` proxy header creates a mismatch only for LAN clients.

D. **/etc/hosts bridge artifact.** Host header is correct (`sloan3.tail1216a3.ts.net`), nginx server_name matches, but FastMCP downstream sees `X-Real-IP: 192.168.1.152` (LAN) vs `100.102.87.70` (Tailscale) and applies different stream behavior.

## 6. What I did NOT do (per hard rules)

- Did not modify nginx config
- Did not bypass nginx (no direct `curl 127.0.0.1:8001/mcp` test from CK)
- Did not generate certs / disable cert verification
- Did not improvise tokens or auth headers
- Did not restart MCP server or uvicorn
- Did not attempt to install Tailscale on Beast

## 7. Decision needed from Paco

Which path forward:

**Path A — Install Tailscale on Beast.** Make Beast a tailnet member; route Atlas MCP client over Tailscale (100.x source) instead of /etc/hosts LAN bridge. Likely matches the working Mac mini topology exactly.

**Path B — Add LAN-internal MCP listener.** Expose mcp_http.py on a separate LAN-only nginx vhost (e.g., `http://192.168.1.10:8002/mcp`) without TLS, since Beast→CK is trusted LAN. Atlas points at the LAN URL.

**Path C — Diagnose deeper inside FastMCP/uvicorn.** Restart with debug logging on uvicorn 8001; trace where the LAN-source request stalls. Possibly a one-line config fix.

**Path D — Different MCP transport.** stdio over SSH from Beast (run mcp_server.py via ssh-tunneled stdio) rather than streamable_http. Requires Atlas package code change but sidesteps the HTTP transport entirely.

My read: Path A is cleanest (matches working topology). Path C is fastest if FastMCP's behavior is fixable. Path B is a pragmatic workaround but adds an unauthenticated LAN endpoint. Path D is a substantive architectural change.

## 8. State on hold

- Atlas Cycle 1F module not yet written (waiting on Paco direction)
- Beast `/etc/hosts` override left in place (revertable; one line)
- atlas.events delta = 0 (no inference/embed calls during smoke)
- B2b + Garage anchors: bit-identical PRE captured, OK to compare POST after resolution
- 16/16 prior tests still pass; 1F tests not yet authored

## 9. Paco verdict requested

Pick A | B | C | D and re-issue Cycle 1F handoff with the chosen approach.
