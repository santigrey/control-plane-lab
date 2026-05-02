# paco_request_atlas_v0_1_phase0_blocker

**Spec:** Atlas v0.1 Operations Agent Loop Build (`tasks/atlas_v0_1_agent_loop.md`, 600 lines, commit `23ab09f`)
**Step:** Phase 0 pre-flight verification BLOCKER
**Status:** ESCALATION -- 3 of 7 pre-flight checks failed; 1 is spec-author dep-name error (false blocker), 2 are real architectural gap. Filing per directive Phase 0 explicit clause + P6 #26 notification protocol.
**Predecessor:** `docs/handoff_paco_to_pd.md` (cleared after read per Step 0); `tasks/atlas_v0_1_agent_loop.md` Phase 0 (lines 73-99); `docs/paco_request_atlas_v0_1_agent_loop_picks.md` (8 ratified picks)
**Author:** PD (Cortez session, post Mac mini transition)
**Date:** 2026-05-02 UTC (Day 78 morning — cycle dispatched Day 77 evening)
**Target host:** Beast (atlas operations agent runtime); fleet (CK + Goliath + SlimJim + KaliPi)

---

## TL;DR

Phase 0 ran 7 pre-flight checks. **4 pass, 3 fail.** Of the 3 failures:

1. **0.3 + 0.5** -- REAL BLOCKER. Beast has no outbound SSH private key (`/home/jes/.ssh/` contains only `authorized_keys` + `known_hosts`; no `id_ed25519`). Beast cannot SSH to ANY fleet node (ck/goliath/slimjim/kalipi all return `Permission denied (publickey,password)`). This is a material architectural gap for an operations agent that needs to ssh-execute fleet commands.
2. **0.7** -- FALSE BLOCKER. Spec wording says `"asyncpg, httpx, etc"`. Reality: atlas pyproject.toml uses `psycopg[binary,pool]>=3.2`, NOT asyncpg. Venv has all real deps installed correctly (psycopg 3.3.3 + psycopg-pool 3.3.0 + httpx 0.28.1 + mcp 1.27.0 + structlog 25.5.0 + pydantic 2.13.3). Functional imports `from atlas.db import Database; from atlas.db.pool import AsyncConnectionPool; import httpx, mcp, structlog` all clean. Spec PURPOSE satisfied (deps exist); literal NAME mismatched. Third instance this cycle-family of P6 #25 (directive-author hedge propagation: count/name claims from memory).

**Per directive:** PD halted; not proceeding to Phase 1. Awaiting Paco ruling on (a) Beast outbound-SSH key strategy, (b) spec wording correction asyncpg→psycopg, (c) bank as P6 #25 third instance / new banking.

B2b + Garage anchors bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` (96+ hours holding through Cycles 1F-1I + 2A-2C close). atlas-mcp.service active, MainPID 2173807, ~5h uptime since 2026-05-01 22:05:42 UTC.

---

## 1. Pre-flight check results (full table)

| # | Check | Result | Detail |
|---|---|---|---|
| 0.1 | atlas HEAD on /home/jes/atlas/ git log -3 | ✅ PASS | `d4f1a81` Cycle 2B (exceeds spec's `"d4f1a81 or later"` -- Cycle 2B == d4f1a81; current). 3 commits: d4f1a81 (Cycle 2B alexandra source allowlist), d383fe0 (Cycle 1I tasks state machine), bfed019 (Cycle 1H atlas-mcp tool surface) |
| 0.2 | systemctl is-active atlas-mcp.service | ✅ PASS | active; MainPID 2173807; ActiveEnterTimestamp `Fri 2026-05-01 22:05:42 UTC` (~5h uptime) |
| 0.3 | mercury-scanner.service via Beast→CK SSH | ❌ FAIL | `jes@192.168.1.10: Permission denied (publickey,password)` -- Beast→CK SSH auth fails |
| 0.4 | Prometheus from Beast `curl http://192.168.1.40:9090/api/v1/query?query=up` | ✅ PASS | HTTP 200; 2.6ms; real metrics returned (`{"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"up","fleet":"santigrey","instance":"192.168.1.152:9100",...]}`) |
| 0.5 | SSH Beast→4 nodes (ck/goliath/slimjim/kalipi) | ❌ FAIL ALL 4 | All 4 return `Permission denied (publickey,password)` -- ck (jes@192.168.1.10), goliath (jes@192.168.1.20), slimjim (jes@192.168.1.40), kalipi (sloan@192.168.1.254) |
| 0.6 | Beast container anchors | ✅ PASS | postgres `2026-04-27T00:13:57.800746541Z`; garage `2026-04-27T05:39:58.168067641Z` -- bit-identical to canonical values, holding 96+ hours |
| 0.7 | atlas .venv exists with deps | ✅ PASS (on PURPOSE; spec wording wrong) | venv at `/home/jes/atlas/.venv` exists; pyproject deps `psycopg[binary,pool], boto3, pydantic, httpx, structlog, mcp` all installed; functional imports clean. **Spec literal said `asyncpg, httpx, etc` -- atlas does NOT use asyncpg, uses psycopg.** Spec wording error |

---

## 2. 0.3 + 0.5 root cause analysis

### 2.1 Beast .ssh state probe (diagnostic)

```
$ ssh beast 'ls -la /home/jes/.ssh/'
total 20
drwx------  2 jes jes 4096 Apr 20 00:16 .
drwxr-x--- 27 jes jes 4096 May  1 22:41 ..
-rw-------  1 jes jes  474 Mar 26 00:51 authorized_keys
-rw-------  1 jes jes 3802 May  2 03:24 known_hosts

$ ssh beast 'ssh-keygen -lf /home/jes/.ssh/id_ed25519.pub'
ssh-keygen: /home/jes/.ssh/id_ed25519.pub: No such file or directory
```

Beast has **no SSH private key**. Only `authorized_keys` (so OTHER hosts can SSH TO Beast) and `known_hosts` (host fingerprint cache).

### 2.2 Architectural impact

The build spec architecture (line 45) and Phase 3 onwards (Domain 1: Infrastructure monitoring) require Atlas to ssh-execute commands across fleet nodes from Beast. Without outbound SSH auth from Beast, the agent loop cannot:
- Phase 3.x: query host metrics via SSH (Domain 1 Infrastructure)
- Phase 4.x: probe employment/contractor SSH state (Domain 2 Talent if applicable)
- Phase 5.x: vendor host operations (Domain 3 Vendor)
- Phase 6.x: supervise mercury-scanner.service on CK (Domain 4 Mercury Supervision; explicitly tied to mercury-scanner status checks)

Every domain that touches fleet state through SSH is blocked.

### 2.3 Resolution options

#### Option A: Generate ed25519 key on Beast + deploy to authorized_keys on 4 nodes

```bash
# On Beast
ssh-keygen -t ed25519 -f /home/jes/.ssh/id_ed25519 -N "" -C "jes@beast-atlas-agent"

# Copy public key to each node's authorized_keys
for node in 192.168.1.10 192.168.1.20 192.168.1.40; do
  ssh-copy-id -i /home/jes/.ssh/id_ed25519.pub jes@$node  # interactive password prompt the first time
done
ssh-copy-id -i /home/jes/.ssh/id_ed25519.pub sloan@192.168.1.254

# Verify
for entry in ck:192.168.1.10:jes goliath:192.168.1.20:jes slimjim:192.168.1.40:jes kalipi:192.168.1.254:sloan; do
  name=${entry%%:*}; rest=${entry#*:}; ip=${rest%:*}; user=${rest#*:}
  ssh -o BatchMode=yes ${user}@${ip} 'hostname'
done
```

Trade-off: requires CEO to enter passwords for ssh-copy-id (or PD provides keys to CEO and CEO does it). One-time setup. After setup, key is permanent and Beast can ssh out indefinitely.

#### Option B: Use Tailscale SSH instead of plain SSH

Tailscale supports SSH over Tailscale identity (no key management needed; Tailscale handles auth). Per memory + earlier session findings, Tailscale is deployed across fleet (CK, Cortez, JesAir, KaliPi, MacMini, Pi3, Goliath all enrolled). Beast appears NOT enrolled per Cycle 1A Path B (Tailscale-skip with /etc/hosts substitution).

Enrolling Beast in Tailscale + enabling Tailscale SSH would solve the auth problem differently. But:
- Cycle 1A Path B explicitly skipped Tailscale on Beast for substrate-isolation reasons (B2b + Garage anchors holding for 96+ hours)
- Adding Tailscale to Beast may disturb substrate (UFW changes, daemon installation, network reconfiguration)
- Conflicts with Standing Gate "control-postgres-beast / control-garage-beast untouched"

Option B unrecommended unless Paco wants to revisit Cycle 1A Path B decision.

#### Option C: Run agent commands FROM CK via MCP, not from Beast directly

Atlas-agent could run on CK instead of Beast, leveraging existing CK→fleet SSH (which works). But:
- Build spec architecture (line 45) explicitly places atlas-agent on Beast alongside atlas-mcp.service
- 8 ratified picks (commit `c5b08c2`) include this architectural decision
- Re-architecting to CK would invalidate ratification + require new Paco ratification cycle

Option C unrecommended unless CEO wants to revisit ratified picks.

#### Option D: Use Beast→CK proxy via atlas-mcp itself (eat own dog food)

Atlas-agent on Beast calls atlas-mcp.service via loopback (already running, MainPID 2173807). atlas-mcp tool `homelab_ssh_run` executes via CK's MCP server (which has the working SSH key). This puts CK MCP in the proxy path. The chain:

```
atlas-agent on Beast
  -> atlas-mcp.service on Beast (loopback)
  -> CK MCP at https://sloan3.tail1216a3.ts.net:8443/mcp (via Beast /etc/hosts FQDN bridge)
  -> CK ssh_run helper (uses CK's SSH key to fleet)
  -> target fleet node
```

Requires:
- atlas-mcp.service has the proxy tool wired (Cycle 1H added 4 tools per `bfed019`; need to verify if homelab_ssh_run-equivalent exists or if Atlas-MCP needs Cycle-1J to add it)
- Architectural review for whether agent should depend on CK MCP for fleet operations

This is the cleanest "don't touch Beast SSH state" option but adds latency + dependency.

### 2.4 PD recommendation

**Option A** -- generate Beast ed25519 + deploy to 4 nodes' authorized_keys. Simplest; one-time setup; matches the architectural assumption Paco made when authoring the spec (spec assumes Beast can SSH out — implies expectation that the key would be deployed). This is the path of least architectural disruption.

CEO action required: provide passwords (or directly run ssh-copy-id) for the 4 nodes during one-time setup. Maybe ~5 minutes of operator work.

Fallback to Option D if CEO prefers the agent-loop to stay decoupled from Beast SSH state.

---

## 3. 0.7 spec wording correction

### 3.1 What the spec says

Line 92 (Phase 0 check 0.7):
> "atlas package venv exists at `/home/jes/atlas/.venv` and has the existing dependencies (asyncpg, httpx, etc)."

### 3.2 What's actually in the venv

```
psycopg                   3.3.3
psycopg-binary            3.3.3
psycopg-pool              3.3.0
httpx                     0.28.1
httpx-sse                 0.4.3
mcp                       1.27.0
pydantic                  2.13.3
pydantic-settings         2.14.0
pytest                    9.0.3
pytest-asyncio            1.3.0
structlog                 25.5.0
```

Matches `pyproject.toml`:
```toml
dependencies = [
    "psycopg[binary,pool]>=3.2",
    "boto3>=1.34",
    "pydantic>=2.7",
    "httpx>=0.27",
    "structlog>=24.1",
    "mcp>=1.0",
]
```

No asyncpg. atlas.db.pool uses `from psycopg_pool import AsyncConnectionPool`.

### 3.3 Pattern recognition

This is the 3rd instance this cycle-family of directive-author memory error:
1. Cycle 1F Phase 3: handler count claimed 14, actual 13 (paco_response `77759f8`)
2. Cycle 1F Phase 3 Step 7: prior-test count claimed 16, actual 15 (paco_response part of `eadc2e7`)
3. **Cycle 1F → v0.1 Agent Loop Phase 0**: dep name claimed `asyncpg`, actual `psycopg`

All three caught at PD pre-execution review under 5-guardrail rule + SR #6. Pattern named in P6 #25 (directive-author hedge propagation). Worth banking as P6 #31 (third-instance confirmation that the pattern is recurring) OR documenting in the close paco_review without new banking.

### 3.4 Proposed spec amendment

Line 92 of `tasks/atlas_v0_1_agent_loop.md`: change `(asyncpg, httpx, etc)` to `(psycopg, httpx, mcp, structlog, pydantic)`. PD can self-correct under 5-guardrail rule guardrail 1-4 (no auth/security boundary touched), OR Paco issues a small spec-correction paco_response. PD recommends the latter for clean audit trail.

---

## 4. Asks of Paco

1. **Ratify** Phase 0 verification result: 4 PASS, 2 real-fail (0.3 + 0.5 same root cause), 1 false-fail (0.7 spec wording).
2. **Rule** on Beast outbound SSH key strategy: Option A (recommended), B, C, or D from §2.3.
3. **Approve** spec amendment line 92 `asyncpg` → `psycopg` (per §3.4).
4. **Bank decision** on P6 #31 -- third instance of P6 #25 pattern. Either:
   a) bank P6 #31 as "confirmed recurring pattern; spec authors should run `pip list` / `git log` / `grep -c` before claiming counts/names from memory"
   b) note in close paco_review without new banking; pattern already covered by P6 #25
5. **Acknowledge** PD halted per directive ("Do NOT proceed to Phase 1"). PD ready to resume after Paco rulings 1-4.

## 5. PD recommendation

- Option A for SSH key (CEO sets up keys via ssh-copy-id; one-time ~5min)
- Spec amendment via small paco_response (clean audit trail)
- Bank P6 #31 (option 4a) -- 3 confirmed instances now, worth elevating to its own line in the feedback file for visibility

## 6. State at this pause

- Phase 0 verification COMPLETE (3 of 7 fail, blocker filed per directive)
- Phases 1-10 NOT started
- handoff_paco_to_pd.md cleared (per Step 0 protocol)
- handoff_pd_to_paco.md notification line for THIS paco_request to follow per P6 #26
- Substrate: B2b + Garage anchors bit-identical, atlas-mcp.service active, no changes
- This is the 4th paco_request this cycle-family (handler count 14→13 / pretest flake / args-wrapping / Phase 0 blocker). All caught at PD pre-execution review under 5-guardrail rule. Discipline metrics +1.

---

**File:** `docs/paco_request_atlas_v0_1_phase0_blocker.md` (untracked, transient until close-out per correspondence triad standing rule)

-- PD
