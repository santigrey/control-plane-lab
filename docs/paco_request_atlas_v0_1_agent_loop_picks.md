# paco_request -- Atlas v0.1 agent loop architectural ratification gate

**From:** Paco (COO)
**To:** CEO Sloan
**Date:** 2026-05-01 (Day 77 evening)
**Re:** Atlas-as-Operations-agent v0.1 build cycle entry; 8 architectural picks for ratification
**Status:** **ALL 8 PICKS RATIFIED by CEO via single "ratify all" response.** This doc captures the canonical record.
**Companion docs:**
- `CHARTERS_v0.1.md` Sub-agent Definitions section (Mercury TBD slot closed in same commit)
- `docs/atlas_sop_v1_0.md` (Atlas operating procedures, ratified Day 77)
- `docs/inter_department_sops_v1_0.md` (handoff patterns)
- `tasks/atlas_v0_1_agent_loop.md` (build spec, NEXT artifact -- to be authored after this doc commits)

---

## Context

Atlas v0.1 substrate ship complete (Cycles 1A-1I; 10 atlas-mcp tools live on Beast at `https://sloan2.tail1216a3.ts.net:8443/mcp`). What's missing is the **agent loop itself**: an always-on Python process on Beast that polls `atlas.tasks` for `pending` work, claims via SKIP LOCKED, executes per playbook, writes results, and escalates per Atlas SOP three-tier model.

CEO ratified Option A (all 3 Charter 5 domains at min-viable depth) as the v0.1 scope, plus Mercury sub-agent management added Day 77 evening when Mercury TBD slot was closed.

## The eight picks

### Pick 1 -- Runtime substrate **[RATIFIED A]**

How does Atlas's agent loop process get launched, supervised, restarted?

- **A: systemd service on Beast** -- mirror `atlas-mcp.service` pattern from Cycle 1G (proven; auto-restart on failure; logs via journalctl; native Beast)
- B: Docker container -- extra layer; substrate isolation; harder to debug
- C: nohup detached process -- worst (no auto-restart, no log management)

**Build implication:** `/etc/systemd/system/atlas-agent.service` unit file with `ExecStart=/home/jes/atlas/.venv/bin/python -m atlas.agent`, `WorkingDirectory=/home/jes/atlas`, `Restart=on-failure`, `User=jes`. Atlas package gains a new entry point at `src/atlas/agent/__main__.py`.

### Pick 2 -- Loop architecture **[RATIFIED my recommendation: asyncio task graph]**

How does Atlas concurrently handle scheduled work + task-queue work + future event subscriptions?

- **A: asyncio task graph** -- native fit (atlas package is already async throughout: AsyncConnectionPool, atlas.inference, atlas.embeddings, atlas.mcp_client). Three concurrent coroutines:
  - `task_poller` -- polls `atlas.tasks` for `pending` rows (5-second cadence; SKIP LOCKED claim)
  - `scheduler` -- runs cron-like scheduled work (system vitals every 5min, vendor checks daily 06:00, recruiter scan daily 08:00, weekly digest Mondays 07:00)
  - `event_subscriber` -- placeholder for v0.2 Mr Robot integration (subscribes to `source='atlas.operations' kind='security_signal'` writes); SKELETON ONLY at v0.1
- B: dual-thread (poller + scheduler) -- threading overhead; less native
- C: single-threaded with cron-like scheduler -- simpler but blocks on long-running work

**Build implication:** `src/atlas/agent/loop.py` orchestrates the asyncio.gather of 3 coroutines. Each coroutine has its own try/except/sleep wrapper for crash isolation -- one coroutine crashing does not bring down the loop.

### Pick 3 -- Domain 1 (Infrastructure monitoring) initial scope **[RATIFIED]**

What does Atlas v0.1 actually monitor on day 1?

**System health (every 5min, threshold-based alerting):**
- Per-node: CPU sustained >85% for 5min, RAM >90%, disk >85%
- Nodes monitored: CK, Beast, Goliath, SlimJim, KaliPi (Mac mini SSH currently unreachable from CK shell -- v0.2 P5 #35 DNS intermittency; defer Mac mini)
- Mechanism: SSH probe via existing key-based auth; OR atlas-agent-on-Beast queries Prometheus on SlimJim if reachable (preferred since H1 ship Day 74 already has Prometheus + node_exporter on every node). **Implementation pick: query Prometheus first; fall back to direct SSH if Prometheus unavailable.**

**Service uptime (every 1min):**
- CK: control-postgres container, orchestrator.service, homelab-mcp.service, nginx
- Beast: control-postgres-beast container, control-garage-beast container, atlas-mcp.service, atlas-agent.service (self-check via separate liveness probe -- failsafe pattern)
- Goliath: ollama service
- SlimJim: mosquitto, prometheus container, grafana container, netdata

**Substrate anchor preservation (hourly):**
- Beast `docker inspect control-postgres-beast control-garage-beast` for `StartedAt`
- Compare to canonical anchors: `2026-04-27T00:13:57.800746541Z` (postgres) + `2026-04-27T05:39:58.168067641Z` (garage)
- Tier 3 escalation if drift detected

### Pick 4 -- Domain 2 (Talent operations) initial scope **[RATIFIED]**

**Job application logging (on inbound trigger + daily 08:00):**
- Read `/home/jes/control-plane/job_search_log.json` (currently `{"seen_urls": []}`; will populate as Sloan logs applications)
- Detect new entries -> write `atlas.events` row with `kind='applicant_logged'`
- v0.1 STUB: just the reader/parser. Real talent ops happens once Sloan starts logging applications (job-search workstream is hedge per CEO Day 77 direction).

**Recruiter watcher: DEFERRED.**
- Requires email integration (Gmail MCP exists in available tools but not wired into Atlas)
- Bank as Atlas v0.1.1 cycle once Gmail bridge is decided

**Weekly digest compilation (Mondays 07:00):**
- Aggregate job_search_log entries + recruiter signals (when wired) over rolling 7 days
- Write to `atlas.events` with `kind='weekly_digest_talent'`
- Surfaced to Sloan via Alexandra dashboard

### Pick 5 -- Domain 3 (Vendor & admin) initial scope **[RATIFIED]**

**Static vendor metadata table (NEW migration):**
- `0006_atlas_vendors.sql` creates `atlas.vendors` table:
  - id, name, plan_tier, billing_cycle (monthly/annual), renewal_date, monthly_cost_usd, primary_contact_url, status (active/paused/cancelled), notes
- Initial seed: Anthropic, GitHub, Twilio, ElevenLabs, Per Scholas, Google, Tailscale (renewal dates filled in by Sloan via dashboard or direct INSERT; v0.1 lands schema + seed structure, not real renewal dates)

**Tailscale auth key expiration check (daily 06:00):**
- Beast is on tailnet (Cycle 1G); `tailscale status --json` returns auth-key metadata
- 14-day + 3-day warnings via Tier 2 alert

**GitHub PAT expiration check (daily 06:00):**
- GitHub API `/user` returns nothing about token expiry directly; Atlas v0.1 reads PAT expiration from `atlas.vendors` notes field where Sloan logged it manually. Real API-driven expiration check deferred to v0.1.1.

**Renewal warning escalation (per Atlas SOP Section 3.2):**
- 14-day warning -> Tier 2 (notify Paco)
- 3-day warning -> Tier 3 (Telegram + dashboard banner)

### Pick 6 -- Mercury management scope at v0.1 **[RATIFIED B]**

**Liveness + start/stop control (NO trade event subscription at v0.1).**

Live state at ratification (Day 77 evening probe):
- Mercury already a systemd unit: `mercury-scanner.service` loaded active running on CK
- mercury.trades has 142 trade rows; latest opened 2026-04-26 (Day 72)
- 2 trades currently open
- paper_trade=true (default)

**Atlas v0.1 actions on Mercury:**
- Liveness check (every 5min): `systemctl is-active mercury-scanner.service` (via SSH to CK)
- Start/stop control: `systemctl start|stop mercury-scanner.service` (only on Tier 2 cancel-window approval; Atlas SOP Section 3.3 prohibits autonomous service modification without playbook authorization)
- Trade activity check (daily 08:00): query mercury.trades for new rows since last check; if Mercury is `is-active running` but no trades in 7+ days, raise Tier 2 alert (could indicate strategy issue or market quiet)

**EXPLICITLY DEFERRED to Mercury v2 (later cycle):**
- Trade event subscription (atlas listens to mercury.trades INSERTs and relays each to Alexandra/Telegram)
- Real-money flag flip (paper_trade=false) -- gated behind Pick 8

### Pick 7 -- Alexandra <-> Atlas communication channel **[RATIFIED C]**

**Both atlas.events stream + Telegram (redundant by tier).**

- **Tier 1 alerts:** atlas.events only (no notification)
- **Tier 2 alerts:** atlas.events + Alexandra dashboard banner (Alexandra subscribes to `kind` allowlist)
- **Tier 3 alerts:** atlas.events + Telegram (immediate via existing Twilio bot) + Alexandra dashboard banner

Alexandra dashboard subscriber implementation lives in Alexandra's orchestrator (NOT Atlas's repo). Atlas v0.1 build spec just defines the contract (which kinds get which severity tags). Alexandra-side wiring is a downstream cycle (Alexandra v0.3+ scope).

Telegram delivery uses the existing Twilio bot endpoint already wired via `mqtt_publisher.py` / `mqtt_subscriber.py` infrastructure. Atlas writes a Telegram-bound message via dedicated atlas helper.

### Pick 8 -- Real-money trigger gate definition **[RATIFIED -- policy gate, not v0.1 build]**

When Sloan ever wants to flip Mercury's `paper_trade=false`, the following must ALL be true (canonical pre-flight checklist):

1. Mercury paper-trade has run >=30 days continuous with rolling-30-day positive P&L (verifiable via `mercury.daily_performance` aggregate)
2. Mercury v2 build complete: trade-event subscription from atlas to mercury.trades; trade alerts wired to Telegram
3. Mercury has dollar-cap circuit breaker:
   - Per-trade max position size (configurable; v2 spec)
   - Per-day max loss (configurable; auto-stop on breach)
4. Explicit CEO ratification in writing (canon-doc level, not chat-level)
5. Pre-flight clean state:
   - Wazuh agents reporting clean from CK + Mercury process (Mr Robot v0.1 build prerequisite)
   - Mr Robot SOP active
   - Atlas SOP escalation playbook updated for real-money Tier 3 (any losing trade >$N gets immediate Telegram)
6. Sloan acknowledges loss-of-capital risk in writing

Atlas v0.1 enforcement: agent loop reads `mercury.trades.paper_trade=false` rows and raises Tier 3 IMMEDIATELY unless this checklist's documented ratification path is canonical (`docs/mercury_real_money_ratification.md` exists with Sloan signature). This is a fail-closed safety pattern.

## What this gate produces

The build spec (next artifact) at `tasks/atlas_v0_1_agent_loop.md` operates on these 8 ratified picks as immutable architectural decisions. PD does not relitigate them at execution time -- if PD finds a verified-live mismatch, paco_request escalation per existing discipline.

## Build spec scope (preview; not the spec itself)

The build spec will cover ~10 phases:

1. atlas-agent.service systemd unit + enable + start
2. src/atlas/agent/__main__.py + loop.py + 3 coroutine modules (poller, scheduler, event_subscriber)
3. src/atlas/agent/domains/infrastructure.py (Domain 1: vitals + service uptime + anchor)
4. src/atlas/agent/domains/talent.py (Domain 2: job_search_log reader + digest)
5. src/atlas/agent/domains/vendor.py (Domain 3: vendor metadata + Tailscale + GitHub PAT)
6. src/atlas/agent/domains/mercury.py (Mercury supervision; Pick 6 scope only)
7. src/atlas/agent/communication.py (atlas.events writes + Telegram dispatch helper)
8. migrations/0006_atlas_vendors.sql + initial seed
9. pytest coverage for each domain + loop
10. Smoke test end-to-end + ship report

6-gate acceptance scorecard expected:
- Gate 1: atlas-agent.service Up and running, MainPID rotates clean on restart
- Gate 2: 3 asyncio coroutines all running concurrently (visible via logs)
- Gate 3: at least one alert from each Domain successfully written to atlas.events with correct severity
- Gate 4: Mercury liveness check running; recognizes mercury-scanner.service is currently active
- Gate 5: Substrate anchors bit-identical pre/post (Atlas agent doing schema-INSERTs only; no substrate restart)
- Gate 6: secret-grep clean on commit + dependency tree audit

Plus 6 standing gates: 5th standing rule application; B2b subscription untouched; Garage cluster untouched; mcp_server.py on CK untouched; atlas-mcp loopback :8001 bind preserved; nginx vhosts unchanged.

## Counts post-ratification

- Standing rules: 6 (unchanged)
- P6 lessons banked: 30 (unchanged)
- v0.2 P5 backlog: 42 (unchanged this turn; Mercury closure may surface 1-2 new items at build time)
- Canon docs updated this commit: 2 (CHARTERS_v0.1.md Mercury slot closure + this paco_request)
- Build spec to be authored: `tasks/atlas_v0_1_agent_loop.md` (NEXT turn after CEO confirms picks-record)

---

**File location:** `/home/jes/control-plane/docs/paco_request_atlas_v0_1_agent_loop_picks.md`

-- Paco (COO)
