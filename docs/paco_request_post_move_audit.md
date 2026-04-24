# Paco Request -- Post-Move Full State & Health Sweep

**From:** Paco
**To:** P2 (Cowork)
**Date:** 2026-04-23 (Day 67 close)
**Priority:** Medium (infrastructure baseline, not blocking Phase 4)

---

## Context

Homelab was torn down, relocated, re-cabled earlier this session. Move is complete and the thermal/acoustic motivation is validated (documented in SESSION.md Day 67). Sloan wants a **full state + health sweep** across the stack before we resume Phase 4 step 6/12.

Known post-move state (from SESSION.md + live agent_status check):
- **CiscoKid** -- up; orchestrator + pgvector (4744 rows) + ollama (3 models) confirmed healthy. Rebooted unexpectedly during move, recovered cleanly. CIMC credential recovery still pending.
- **TheBeast (R640)** -- Day 67 baseline: fans 15% PWM auto, T4 57C idle, CPUs <40C, inlet 27C. Sloan flagged a "PSU issue" this session -- needs verification.
- **SlimJim** -- offline since the move. Not yet physically inspected.
- **Goliath (GB10)** -- status unknown, needs verification.
- **Mac mini** -- reachable (MCP bridge working).
- **JesAir, KaliPi** -- status unknown.
- **Cortez** -- asleep, NOT in scope.

Control plane is alive. Everything else unverified.

## What this audit is

**Non-destructive, read-only** sweep. No restarts, no config changes, no remediation. Observe + report only. Sloan green-lights remediation as separate tasks.

## Scope -- 7 phases

Execute phase-by-phase. After each phase, append results to `docs/paco_response_post_move_audit.md`, commit `audit: phase N of 7 complete`, notify Sloan. Do not proceed without Sloan ack. If a phase surfaces a RED issue (disk SMART fail, PSU fault, postgres corruption, GPU ECC errors, cert expired), STOP and escalate via `docs/paco_request_post_move_audit_escalation_<topic>.md`.

### Phase 1 -- Reachability sweep
For each in-scope node (CiscoKid, TheBeast, Goliath, Mac mini, SlimJim, JesAir, KaliPi):
- Ping from CiscoKid (1 packet, 2s timeout)
- SSH smoke: `echo alive && hostname && uptime && uname -r`
- Record: reachable Y/N, IP matches canonical, uptime (flags unexpected reboots), kernel

**Deliverable:** table `node | ping | ssh | ip_match | uptime | kernel`

### Phase 2 -- Per-node system health (reachable nodes)
Per node:
- `uptime`
- `df -h /`
- `free -h`
- `sensors 2>/dev/null || echo no-sensors`
- `dmesg -T | tail -80 | grep -iE "error|fail|thermal|pcie|ata|nvme|oom|throttl" || echo clean`
- `systemctl --failed --no-pager || echo non-systemd`
- `last reboot | head -5`

**Deliverable:** per-node health block with red flags highlighted.

### Phase 3 -- Service layer
**CiscoKid:**
- `curl -s http://localhost:8000/healthz`
- `systemctl status nginx --no-pager | head -15` + `sudo nginx -t 2>&1`
- `docker ps --format "table {{.Names}}\t{{.Status}}" | grep -iE "postgres|pgvector"`
- MCP: `curl -sk https://sloan3.tail1216a3.ts.net:8443/mcp -o /dev/null -w "%{http_code}\n"`
- Cert: `sudo openssl x509 -in /etc/ssl/tailscale/sloan3.tail1216a3.ts.net.crt -noout -dates 2>/dev/null || echo cert-path-drift`

**TheBeast:**
- Ollama: `curl -s http://localhost:11434/api/tags | head -30`
- GPU: `nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,ecc.errors.uncorrected.aggregate.total --format=csv`
- PSU: `sudo dmesg -T | grep -iE "power|psu|voltage|thermal event" | tail -20`
- IPMI: `sudo ipmitool sdr type "Power Supply" 2>/dev/null || echo ipmitool-skip`

**Goliath:**
- Ollama: `curl -s http://localhost:11434/api/tags | head -30`
- GPU: `nvidia-smi --query-gpu=name,temperature.gpu,memory.used,memory.total --format=csv`
- Tailscale: `tailscale status | head -5` (confirm 100.112.126.63)

**SlimJim:**
- `systemctl status mosquitto --no-pager | head -10`
- MQTT smoke: `mosquitto_pub -h localhost -t paco/audit -m ping && mosquitto_sub -h localhost -t paco/audit -C 1 -W 3`

**Mac mini:**
- `launchctl list | grep -iE "agent|scanner"`

**Deliverable:** service pass/fail matrix.

### Phase 4 -- Model inventory & routing
- Models on TheBeast Ollama
- Models on Goliath Ollama (expected: `llama3.1:70b`, `deepseek-r1:70b`, `qwen2.5:72b`)
- Small/embed models on TheBeast (expected: `mxbai-embed-large`)
- Routing sanity: orchestrator inference call to a small model, then to a 70B; confirm via orchestrator logs that small hit TheBeast and 70B hit Goliath

**Deliverable:** model -> node map + routing pass/fail.

### Phase 5 -- Network integrity
Per reachable node:
- `tailscale status`
- `ip -4 addr show | grep inet | grep -v 127.0.0.1`
- From CiscoKid: `dig +short sloan3.tail1216a3.ts.net`
- nginx proxy chain from CiscoKid: curl 443 (dashboard) and 8443 (MCP) with status codes

**Deliverable:** network state table + drift vs canonical node reference.

### Phase 6 -- Data integrity
On CiscoKid postgres:
- Row counts: `memory`, `agent_tasks`, `messages`
- Last 5 `agent_tasks` rows
- Last 5 `messages` rows
- `pg_isready`
- Venice sanity: `SELECT count(*) FROM memory WHERE tool = 'venice_ingest';` (expect ~3134)
- Phase 1 backfill: `SELECT content_type, count(*) FROM memory GROUP BY content_type;`
- Docker volume: `docker volume ls | grep -iE "postgres|pgvector"`

**Deliverable:** row counts + sanity + confirmation Phase 1/2/3/4-partial work is intact.

### Phase 7 -- Physical/thermal baseline
Per reachable node with sensors:
- CPU temps, GPU temps (TheBeast, Goliath), fan speeds
- TheBeast iDRAC (192.168.1.237) via `/tmp/idrac.exp` wrapper on Mac mini if still present -- pull PSU + fan + thermal. If wrapper gone, flag and skip.
- Goliath GPU idle temp + power draw
- **Compare to Day 67 baseline:** T4 57C, CPUs <40C, inlet 27C, fans 15% PWM. Flag >=5C drift.

**Deliverable:** thermal table + drift vs Day 67 baseline.

## Final deliverable

Consolidated report: `docs/paco_response_post_move_audit.md` (P2 writes, commits, notifies Sloan).

Structure:
1. **Executive summary** -- traffic-light per node (green/yellow/red) + one-line cluster verdict
2. **Phase-by-phase findings**
3. **Prioritized remediation list** -- fix first / can wait / Sloan-in-loop
4. **Drift report** -- deviations from canonical node reference and Day 67 baseline
5. **Open questions for Paco**

## Execution rules (non-negotiable)

- One phase at a time. Commit + notify after each.
- Do NOT proceed to next phase without Sloan ack.
- All `find` commands pipe through `grep -v .venv | head -50`.
- No `sed` for multi-line Python. Write to `/tmp/` then execute.
- Verify output before moving on. No "should work" -- only observed.
- Read-only. No restarts, no config writes, no remediation without separate approved spec.
- RED issue -> STOP and escalate.

## What Paco verified before sending

- `homelab_agent_status`: orchestrator up, pgvector up (4744 rows), ollama up (3 models)
- SESSION.md Day 67 state reviewed
- No pending Paco messages, no tasks awaiting approval
- No prior audit doc in `docs/`
- Git HEAD on main: `a20f553`

## Blocking questions for Paco

None. Spec is complete. Execute on Sloan's green light.
