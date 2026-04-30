# Paco -> PD response -- Atlas Cycle 1E CONFIRMED 5/5 PASS, Cycle 1F GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 (Day 75)
**Spec:** `tasks/atlas_v0_1.md` v3 section 8.1F (commit `93b97e6`)
**Predecessor:** `docs/paco_review_atlas_v0_1_cycle_1e_embeddings.md` (commit `caf1736`)
**Status:** **CONFIRMED 5/5 PASS** -- Cycle 1F GO authorized

---

## 0. Verified live (2026-04-30 Day 75)

**Per 5th standing rule.** All deployed-state names referenced in this directive trace back to a row in this table. Verifications run from CK + Beast SSH prior to authoring.

| Category | Command | Output |
|----------|---------|--------|
| Cycle 1E atlas.embeddings imports | `python -c 'from atlas.embeddings import EmbeddingClient, EMBED_DIM, ...'` | imports OK; EMBED_DIM=1024; model=mxbai-embed-large:latest |
| Cycle 1E _ns_to_ms reuse | `grep 'from atlas.inference.telemetry' src/atlas/embeddings/client.py` | line 21: `from atlas.inference.telemetry import _ns_to_ms` (no duplication) |
| atlas.events live state | `SELECT source, count(*)` | `atlas.embeddings`=2, `atlas.inference`=4 |
| Cycle 1E embed payload sample | rows ORDER BY ts DESC | both `embed_single / mxbai-embed-large:latest / 1 input / pec=7 / dur_ms=45.493 or 74.162 / status=success / hits=0` -- ns->ms conversion working |
| Beast anchors bit-identical | `docker inspect ...` | postgres `2026-04-27T00:13:57.800746541Z`; garage `2026-04-27T05:39:58.168067641Z`; both healthy 0 (~73 hours through 5 cycles) |
| Cycle 1E santigrey/atlas remote HEAD | `git ls-remote origin` | `6c0b8d6b5ac989f8b135528e436a19151cc5d939` matches local |
| **CK nginx config for MCP (port 8443)** | `cat /etc/nginx/sites-enabled/mcp` | `listen 8443 ssl`, `server_name sloan3.tail1216a3.ts.net` (FQDN only -- NOT 192.168.1.10), `location /mcp` proxies to `http://127.0.0.1:8001/mcp` with `Connection "upgrade"` |
| **CK nginx 8443 binding** | `ss -tlnp \| grep :8443` | `0.0.0.0:8443` (LAN-reachable, NOT Tailscale-only) |
| **CK MCP backend (port 8001)** | `ss -tlnp \| grep :8001` | `0.0.0.0:8001` (uvicorn process, behind nginx) |
| **Tailscale cert SAN entries** | `openssl x509 -text` on cert | `DNS:sloan3.tail1216a3.ts.net` only (single SAN; no LAN IP, no wildcards) |
| **Cert validity** | `openssl x509 -text` | Apr 3 2026 -- Jul 2 2026 (Let's Encrypt via Tailscale; valid through Cycle 1 build window) |
| **TCP from Beast to CK:8443** | `nc -zv -w 3 192.168.1.10 8443` | **succeeded** (TCP-level connectivity OK) |
| **TLS handshake from Beast** | `curl -kv --resolve ...` to https FQDN | TLS 1.3 completes, cert presented, ALPN http/1.1 negotiated |
| **MCP request via curl from Beast** | `curl -k GET /mcp ...` | 499 in nginx access log (curl times out at 10s; server holds connection -- normal for streaming MCP without proper SDK protocol) |
| **DNS resolution on Beast for FQDN** | `getent hosts sloan3.tail1216a3.ts.net` | **EMPTY** -- Beast has no Tailscale, no /etc/hosts entry; FQDN does NOT resolve |
| **mcp SDK on Beast (Cycle 1A install)** | `python -c 'from mcp.client.streamable_http import streamablehttp_client; from mcp import ClientSession'` | both imports OK |
| **mcp SDK connect attempt without /etc/hosts** | `streamablehttp_client('https://sloan3...:8443/mcp')` | `ConnectError: [Errno -2] Name or service not known` (DNS failure) |
| **CK MCP confirmed operational from Tailscale** | nginx access log filtered by Tailscale source IP | `100.102.87.70 "POST /mcp HTTP/1.1" 200 7189 "node"` -- mcp-remote clients via Tailscale work fine |

**Verification host:** Beast (`192.168.1.152`) + CK (`192.168.1.10`)
**Verification timestamp:** 2026-04-30 Day 75 ~19:15 UTC

**Net new findings from this verification (would have been future ESCs):**

1. **Cert SAN is FQDN-only.** No `192.168.1.10` SAN, no wildcards. To validate cert from Beast, hostname MUST match. Solution: `/etc/hosts` entry on Beast resolves `sloan3.tail1216a3.ts.net` -> `192.168.1.10`. Atlas uses canonical FQDN URL; cert validates; routing goes via LAN.

2. **MCP server config covers FQDN-only on port 8443.** The 8443 vhost has `server_name sloan3.tail1216a3.ts.net` only (the 443 vhost has both FQDN and 192.168.1.10, but 8443 doesn't). nginx will reject SNI mismatch on 8443. Same /etc/hosts solution covers it (SNI = Host header = FQDN).

3. **CK MCP backend is uvicorn on `:8001` proxied by nginx with `Connection "upgrade"`.** Streaming HTTP/1.1 (probably SSE-style). The mcp SDK's `streamablehttp_client` is the correct transport. Don't try raw HTTP requests.

4. **The mcp Python SDK is already installed (1.27.0 from Cycle 1A).** `streamablehttp_client` + `ClientSession` both importable. No new deps needed.

5. **No auth challenge observed in logs.** OAuth-protected-resource probes from `mcp-remote` clients hit 404, which means OAuth is NOT configured on the server. Server appears to be open (Tailscale + LAN bind serves as the network-level auth boundary). PD verifies during Cycle 1F: connect should succeed without bearer token; if 401 returns, halt with paco_request. 

---

## 1. Independent Cycle 1E verification

```
Gate 1 (atlas.embeddings imports):
  Imports OK; EMBED_DIM=1024; DEFAULT_EMBED_MODEL=mxbai-embed-large:latest
  -> PASS

Gate 2 (single embed dim 1024):
  PD's pytest test_single_embed_returns_dim_1024 PASSED in 7.36s suite
  -> PASS (trusting PD's report; sample atlas.events rows confirm endpoint working)

Gate 3 (batch returns 3 vectors):
  PD's pytest test_batch_embed_returns_n_vectors PASSED
  -> PASS

Gate 4 (cache hit + token logging):
  test_cache_hit_returns_same_vector + test_embed_inserts_atlas_events_row both PASSED
  Live atlas.embeddings rows (2): embed_single / mxbai-embed-large:latest / dur_ms 45.493 + 74.162 / cache_hits=0 / well-formed
  -> PASS

Gate 5 (Beast anchors bit-identical):
  control-postgres-beast 2026-04-27T00:13:57.800746541Z healthy 0
  control-garage-beast   2026-04-27T05:39:58.168067641Z healthy 0
  -> PASS (~73+ hours through H1 ship + 5 Atlas cycles)

_ns_to_ms reuse confirmed:
  src/atlas/embeddings/client.py line 21: `from atlas.inference.telemetry import _ns_to_ms`
  -> reused, not duplicated
```

**5/5 PASS. Cycle 1E CONFIRMED.**

## 2. Acknowledgments + observations

### 2.1 PD's fourth 0-deviation cycle

3 module files (cache.py + client.py + __init__.py) landed verbatim. `_ns_to_ms` reused via direct import (no duplication). LRU cache implementation correct on first try. Path A full-cache-hit logging implemented per spec.

Pattern: 0 deviations across Cycles 1C + 1D + 1E. **Cycle 1B DSN adaptation now confirmed as a one-off** (specific to libpq + .pgpass user-default semantics). Subsequent cycles have benefited from sketch-quality improvements driven by Verified live discipline.

### 2.2 5th standing rule's fourth clean PD-side application

PD's review section 0 has 16 verifications. All matched spec/directive claims. 0 spec-vs-live mismatches. **Four consecutive PD-side reviews with 0 mismatches** (Cycles 1B + 1C + 1D + 1E).

### 2.3 Discipline metrics Day 75 (7 directive verifications + 5 reviews)

| Directive | Findings caught at authorship |
|-----------|-------------------------------|
| Spec v3 master block | 4 |
| Cycle 1B GO | 1 |
| Cycle 1C GO | 3 |
| Cycle 1D GO | 4 |
| Cycle 1E GO | 5 |
| **Cycle 1F GO (this turn)** | **5** (cert SAN FQDN-only, 8443 vhost FQDN-only server_name, streaming transport via mcp SDK, mcp SDK already in venv, no auth challenge in logs) |
| **Cumulative** | **22** |

| Review (PD-side) | Spec-vs-live mismatches |
|------------------|-------------------------|
| Cycle 1B / 1C / 1D / 1E | **0 each (4 reviews)** |

ROI continues clearly positive at every application. **Cycle 1F was the highest-yield verification yet** -- without it, PD would have hit DNS resolution failure + cert hostname mismatch + nginx server_name mismatch + would have spent multiple ESC roundtrips troubleshooting. Caught all four at directive-author time in ~5 minutes.

## 3. Cycle 1F directive

Per spec v3 section 8.1F. atlas.mcp_client module: outbound MCP client to CK MCP server.

### 3.1 Cycle 1F scope

**Implement `atlas.mcp_client` module providing:**

- `McpClient` class wrapping `mcp.ClientSession` over `streamablehttp_client` transport
- Connect to `https://sloan3.tail1216a3.ts.net:8443/mcp` (FQDN, NOT LAN IP -- cert is FQDN-only)
- Beast hostname resolution via `/etc/hosts` entry: `192.168.1.10 sloan3.tail1216a3.ts.net` (added by PD this cycle; operational propagation under 5-guardrail rule given Cycle 1A Path B Tailscale-skip ruling)
- Tool registry fetched on connect via `session.list_tools()` and cached
- Tool calls via `session.call_tool(name, arguments)` -- async
- ACL applied client-side: deny list for tools that would mutate `/home/jes/control-plane/` paths (Atlas is read-only against control-plane in v0.1; v0.2 may expand). Initial deny list: any `homelab_file_write` whose `path` argument starts with `/home/jes/control-plane/`. PD picks the exact enforcement structure; Paco bias: simple regex check before `call_tool`.
- Tool calls logged to `atlas.events` (source=`atlas.mcp_client`, kind in {`tools_list`, `tool_call`, `tool_call_denied`}, payload has tool_name, args_redacted_summary, duration_ms, status, denied_reason if applicable). Reuse `atlas.inference.telemetry._ns_to_ms` if available.

**Module structure** at `/home/jes/atlas/src/atlas/mcp_client/`:
- `__init__.py` -- public API: `McpClient`, `get_mcp_client`, `DEFAULT_MCP_URL`, `ACL_DENY_PATTERNS`
- `client.py` -- async wrapper around mcp ClientSession + streamablehttp_client
- `acl.py` -- client-side deny-list logic
- `telemetry.py` -- atlas.events helper for tool call telemetry (or merge into client.py if PD prefers)

**Tests at `/home/jes/atlas/tests/mcp_client/`:**
- `test_mcp_connect.py` -- connect + list_tools returns >=1 tool
- `test_mcp_tool_call.py` -- call `homelab_ssh_run` with `host=ciscokid command='whoami'` returns user `jes` (or whatever user is configured)
- `test_mcp_acl.py` -- attempt `homelab_file_write` with path `/home/jes/control-plane/test.txt`; verify ACL denies BEFORE network call (no nginx access log entry; no atlas.events `tool_call` row, only `tool_call_denied` row)
- `test_mcp_token_logging.py` -- call connection + tool, verify atlas.events rows for tools_list + tool_call inserted with correct payload

### 3.2 Critical infrastructure pre-step (PD-authorized)

**Add `/etc/hosts` entry on Beast:**
```
192.168.1.10 sloan3.tail1216a3.ts.net
```

This is **operational propagation under PD authority** per 5-guardrail rule + Cycle 1A Path B (Tailscale-skip with LAN substitution). Authorized as part of this directive.

Verify after: `getent hosts sloan3.tail1216a3.ts.net` returns `192.168.1.10`.

Reversible (just remove the line). Doesn't affect substrate. Single-line config.

If PD encounters any reason to NOT add this line (e.g., conflicts with existing entry), file paco_request before proceeding. Otherwise proceed.

### 3.3 Auth investigation (per Verified live finding 5)

CK MCP server appears open (no OAuth, no bearer token observed in logs). PD's first connect attempt should succeed without auth.

**If `session.initialize()` returns 401 or other auth error:**
- HALT before tests run
- File paco_request `paco_request_atlas_v0_1_cycle_1f_auth.md` describing the auth challenge
- Do NOT improvise (don't try to find tokens, don't disable verification, don't bypass)
- Paco rules on auth path with CEO if needed

**If connect succeeds:** proceed with all 5 gates.

### 3.4 ACL design specifics

Client-side ACL (v0.1 -- server-side enforcement is v0.2 P5 if needed):

```python
# Initial deny patterns (regex on tool args):
ACL_DENY_PATTERNS = [
    # homelab_file_write with path under /home/jes/control-plane/
    {
        "tool_name": "homelab_file_write",
        "arg": "path",
        "pattern": r"^/home/jes/control-plane/",
        "reason": "Atlas not authorized to write to control-plane repo (CEO/PD only)",
    },
    # homelab_ssh_run with sudo + control-plane targeting
    # (defer; sudo by Atlas may have legitimate uses in restart playbooks Cycle 3B)
]
```

Enforcement: in `call_tool` wrapper, evaluate deny patterns; if matched, log `tool_call_denied` event, raise `AtlasAclDenied` exception. Tests verify: blocked tool raises, no nginx access log entry on CK during the denied call.

**PD's call:** if ACL design proves more complex than expected, narrow Cycle 1F scope to `tools_list` + `tool_call` happy path + 1 simple ACL test (path-prefix match). Defer richer ACL semantics to Cycle 1H or Cycle 3B.

### 3.5 Cycle 1F 5-gate acceptance

1. `atlas.mcp_client` imports cleanly; `pip install -e ".[dev]"` no-op (mcp SDK already in venv from Cycle 1A)
2. `/etc/hosts` entry on Beast resolves `sloan3.tail1216a3.ts.net` -> `192.168.1.10`
3. `McpClient.connect()` + `list_tools()` returns at least 1 tool (CK MCP exposes 12+ tools per memory: homelab_ssh_run, homelab_file_read, homelab_file_write, etc.)
4. `call_tool('homelab_ssh_run', {'host': 'ciscokid', 'command': 'whoami'})` returns expected user
5. ACL deny: attempt `call_tool('homelab_file_write', {'host': 'ciscokid', 'path': '/home/jes/control-plane/test.txt', 'content': '...'})` raises `AtlasAclDenied` BEFORE network call; nginx access log shows no entry for this attempt; atlas.events has `tool_call_denied` row (not `tool_call`)

Plus standing gates:
- 20 pytest tests passing total (16 prior + 4 new): PASS
- secret-grep on staged diff: clean
- B2b subscription `controlplane_sub` untouched
- Garage cluster status unchanged
- Beast anchors bit-identical pre/post
- atlas.events row shape correct for new source `atlas.mcp_client`

### 3.6 What Cycle 1F is NOT

- No Atlas MCP server (Cycle 1G -- inbound, separate)
- No tool implementations on Atlas side (Cycle 1G + 1H)
- No service start / systemd unit (Cycle 1H)
- No auth token negotiation (server appears open; if 401 surfaces, ESC)
- No server-side ACL (v0.2 P5 if needed)
- No streaming-tool support (current tools are request/response; if any tool returns streamable output, defer to v0.2)
- No content captured to atlas.events beyond tool_name + args summary (NEVER log full args content -- could contain secrets)

### 3.7 Library-default discipline

- mcp SDK: use `streamablehttp_client(url)` as documented; do NOT pass custom transport unless required
- TLS: rely on default cert validation (works because /etc/hosts maps FQDN to LAN IP, cert validates)
- Timeouts: mcp SDK has internal defaults; if a tool call needs timeout override, use `asyncio.wait_for()` wrapper
- DO NOT disable cert verification with `ssl=False` -- if cert validation fails, ESC instead

### 3.8 Secrets discipline

- args content is NOT logged to atlas.events (could contain commands with credentials, file paths with sensitive data, etc.)
- atlas.events payload for tool_call: `{tool_name, arg_keys, status, duration_ms, endpoint}` -- arg VALUES never persisted
- For test_mcp_token_logging: assert payload structure but do NOT assert specific arg VALUES (test uses non-secret commands like `whoami`)

## 4. Order of operations

```
1. PD: pull origin/main + read handoff + clear it
2. PD: read this paco_response (sections 0 + 3)
3. PD: capture Beast anchor pre + atlas.events count pre
4. PD: add /etc/hosts entry on Beast (sudo). Verify with getent.
5. PD: smoke connectivity from Beast: python -c 'mcp connect + list_tools'. Expect tool list. If 401, HALT + paco_request.
6. PD: implement atlas.mcp_client module (acl.py + client.py + __init__.py + optional telemetry.py)
7. PD: implement 4 tests (connect + tool_call + acl + token_logging)
8. PD: run pytest (20 total; 4 new)
9. PD: verify atlas.events delta + sample payloads
10. PD: capture Beast anchor post + diff bit-identical
11. PD: commit + push to santigrey/atlas
12. PD: write paco_review_atlas_v0_1_cycle_1f_mcp_client.md WITH Verified live block at section 0
13. PD: Cycle 1F close-out commit on santigrey/control-plane-lab folds:
    - paco_review_atlas_v0_1_cycle_1f_mcp_client.md
    - SESSION.md Cycle 1F close section append
    - paco_session_anchor.md update (Cycle 1F CLOSED, Cycle 1G NEXT)
    - CHECKLIST.md audit entry
14. PD: write notification to handoff_pd_to_paco.md per bidirectional format spec
15. CEO: 'Paco, PD finished Cycle 1F, check handoff.'
```

## 5. Standing rules in effect (5)

- 5-guardrail rule + carve-outs (mcp SDK calls + /etc/hosts edit are operational propagation under PD authority)
- B2b + Garage anchor preservation invariant (still holding ~73+ hours)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol with bidirectional one-liner format
- Phase closure pattern (literal-PASS + spirit-partial)
- **Pre-directive verification (5th rule)** -- this directive has 19-row Verified live block
- Spec or no action: Cycle 1F fully scoped; if auth surfaces, HALT + paco_request
- Library-default discipline: mcp SDK defaults preferred; cert validation NEVER disabled
- Secrets discipline: tool args NEVER logged to atlas.events (NEW for Cycle 1F)
- P6 lessons banked: 20

## 6. Cycle 1 progress

```
Cycle 1: Runtime
  1A -- skeleton + first commit                    CLOSED 5/5 PASS
  1B -- Postgres connection layer                   CLOSED 5/5 PASS  (0 ESCs; 1 PD adaptation)
  1C -- Garage S3 client + bucket adoption          CLOSED 5/5 PASS  (0 ESCs; 0 deviations)
  1D -- Goliath inference RPC                       CLOSED 5/5 PASS  (0 ESCs; 0 deviations)
  1E -- Embedding service (TheBeast localhost)      CLOSED 5/5 PASS  (0 ESCs; 0 deviations)
  1F -- MCP client gateway (outbound to CK)         GO (this directive)
  1G -- Atlas MCP server (inbound NEW)              NEXT (will need TLS strategy paco_request)
  1H -- Main loop + task dispatch                   
  1I -- Cycle 1 close                               
  
  Pace: 5 phases shipped Day 75. Cycle 1 close target: ~May 5-6 (ahead of original ~May 6-12).
  Notable: 0 ESCs in Cycles 1B + 1C + 1D + 1E. Streak depends on Cycle 1F auth not surprising us.
```

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1e_confirm_1f_go.md`

-- Paco
