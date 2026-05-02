# paco_review_atlas_v0_1_phase3

**Spec:** Atlas v0.1 Operations Agent Loop Build Spec (`tasks/atlas_v0_1_agent_loop.md`, lines 272-313 = Phase 3; commit `7f50db8`)
**Phase:** 3 -- Domain 1: Infrastructure monitoring (CPU/RAM/disk + service uptime + substrate anchor)
**Status:** **1/1 acceptance criteria PASS post-bug-fix.** Phase 3 CLOSED. Ready for Phase 4 GO ratification.
**Predecessor:** `docs/paco_response_atlas_v0_1_phase2_confirm_phase3_go.md` (Phase 3 GO authorization, HEAD `7f50db8`); CEO Sloan directive Day 78 morning (atlas.tasks override + 5 explicit kind names + service_uptime cadence 5min)
**Atlas commit:** `54e3a26` on santigrey/atlas main (parent `473763f`)
**Author:** PD (Cortez session, host-targeted verification + P6 #32 mitigation applied)
**Date:** 2026-05-02 UTC (Day 78 morning)
**Target host:** Beast (atlas package authoring + agent runtime host)

---

## 0. Verified live (per 5th standing rule + host-targeting + P6 #32 mitigation)

P6 #32 applied at write time: `_create_monitoring_task` copied from canonical `atlas.mcp_server.tasks.create_task` (Cycle 1I commit `d383fe0`). All commands targeted explicitly at Beast. PRE/POST capture for Standing Gates compliance. Bug caught + fixed mid-phase (see §3) before final acceptance verification.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Beast Postgres anchor PRE | `docker inspect control-postgres-beast` | `2026-04-27T00:13:57.800746541Z` |
| 2 | Beast Garage anchor PRE | `docker inspect control-garage-beast` | `2026-04-27T05:39:58.168067641Z` |
| 3 | atlas-mcp.service PRE | `systemctl is-active` + MainPID | `active`; MainPID 2173807; ActiveEnterTimestamp `Fri 2026-05-01 22:05:42 UTC` |
| 4 | atlas-agent.service PRE | `systemctl status atlas-agent.service` | `loaded inactive disabled` (Phase 1 acceptance state preserved) |
| 5 | mercury-scanner.service PRE | `ssh ck systemctl is-active mercury-scanner.service` | `active` MainPID 643409 (Standing Gate #6) |
| 6 | 3 source files written + 1 modified | `git status` | `A domains/__init__.py`, `A domains/infrastructure.py`, `M scheduler.py` |
| 7 | Imports clean (post-fix) | `python -c 'from atlas.agent.domains.infrastructure import system_vitals_check, service_uptime_check, substrate_anchor_check; from atlas.agent.scheduler import scheduler'` | imports OK |
| 8 | 90s smoke completes | `cd /home/jes/atlas && timeout 90 .venv/bin/python -m atlas.agent` | runs to SIGTERM at 90s; emits `Atlas agent loop starting` + `system_vitals_check_start nodes=5` + `system_vitals_check_done` + `service_uptime_check_start services=6` + `service_uptime_check_done` + `substrate_anchor_check_start` + `substrate_anchor_check_done drift=False` |
| 9 | atlas.tasks gained 22 monitoring rows in 1 cycle | `psql 'WHERE payload->>kind IN (...) AND created_at > now() - interval 3 minutes GROUP BY kind'` | monitoring_cpu=5, monitoring_ram=5, monitoring_disk=5, service_uptime=6, substrate_check=1 -- TOTAL 22 (5 nodes × 3 vitals + 6 services + 1 substrate) |
| 10 | All 5 directive-specified kinds present | enumerate distinct payload->>'kind' from fresh rows | {monitoring_cpu, monitoring_ram, monitoring_disk, service_uptime, substrate_check} -- exact match Sloan directive |
| 11 | Sample monitoring_cpu row format | `psql ORDER BY created_at DESC LIMIT 1` | `{"kind": "monitoring_cpu", "node": "goliath", "source": "ssh", "cpu_pct": 2.3, "threshold_breach": false}` |
| 12 | Sample service_uptime row format (post-fix) | same | `{"kind": "service_uptime", "node": "ck", "status": "active", "target": "mercury-scanner.service", "is_healthy": true, "target_kind": "systemd"}` -- correctly keyed |
| 13 | Sample substrate_check row | same | `{"kind": "substrate_check", "garage_match": true, "drift_detected": false, "postgres_match": true, ...canonical anchors verified...}` |
| 14 | Beast Postgres anchor POST | `docker inspect control-postgres-beast` post-smoke | `2026-04-27T00:13:57.800746541Z` -- bit-identical |
| 15 | Beast Garage anchor POST | `docker inspect control-garage-beast` post-smoke | `2026-04-27T05:39:58.168067641Z` -- bit-identical |
| 16 | atlas-mcp.service POST (Standing Gate #4) | `systemctl is-active` + MainPID | `active`; MainPID 2173807 -- UNCHANGED |
| 17 | atlas-agent.service POST (Phase 1 state preserved) | `systemctl status` | `loaded inactive disabled` -- still NOT enabled |
| 18 | mercury-scanner.service POST (Standing Gate #6) | `ssh ck systemctl is-active mercury-scanner.service` | `active` MainPID 643409 -- UNCHANGED |
| 19 | atlas commit + push | `git log + git push` | `54e3a26 feat: Cycle Atlas v0.1 Phase 3 Domain 1 Infrastructure monitoring`; pushed `473763f..54e3a26` to santigrey/atlas main |
| 20 | Pre-commit secret-grep (P6 #11) | value-shaped regex on 385 ADDED lines | `(no value-shaped matches)` -- clean |
| 21 | Spec/directive divergence acknowledged | `grep -c "atlas.tasks" infrastructure.py` | code targets `atlas.tasks` per Sloan directive (override of spec line 312 `source='atlas.operations'` events approach); spec amendment via CEO directive flagged in §3 |
| 22 | substrate_check is read-only | inspect `substrate_anchor_check()` source | uses `docker inspect --format '{{.State.StartedAt}}'` only (READ); no docker exec / restart / modify ops |

22 verified-live items, 0 mismatches, 0 deferrals. Bug caught + fixed mid-phase before final acceptance.

---

## 1. TL;DR

Phase 3 implemented Domain 1: Infrastructure monitoring. 3 atlas package files (1 new dir + 1 new module + 1 modified scheduler) totaling +385/-4 lines. Atlas commit `54e3a26` shipped to santigrey/atlas main. Acceptance gate PASSES post-bug-fix: 90s `python -m atlas.agent` smoke creates 22 atlas.tasks rows (5 nodes × 3 vitals + 6 services + 1 substrate_check) with exact payload.kind set Sloan directive specified.

**Spec/directive divergence (CEO directive amendment):** spec line 312 said write to atlas.events with kinds {system_vitals, service_uptime, substrate_anchor_drift}. Sloan's directive Day 78 morning explicitly overrode to atlas.tasks with kinds {monitoring_cpu, monitoring_ram, monitoring_disk, service_uptime, substrate_check}. PD surfaced divergence + got explicit Sloan confirmation before code lands. Implemented per CEO directive; spec amendment to follow at cycle close (canon hygiene path). Architectural impact: monitoring observations now flow through Phase 2 poller pipeline (claim→no-op→done) which aligns with Atlas-as-Operations-Agent paradigm (observations become work items).

**Bug caught + fixed mid-phase (5th-rule discipline working):** initial smoke runs showed 0 service_uptime rows despite checks running cleanly. Root cause: dict spread `{"kind": kind, **payload}` in `_create_monitoring_task` allowed payload-supplied `"kind": kind` (where inner kind = container/systemd) to shadow the explicit `"kind": "service_uptime"` argument. Fix 1: defensive merge `dict(payload); payload["kind"]=kind`. Fix 2: rename `"kind"` → `"target_kind"` in service_uptime payload for semantic clarity. Post-fix smoke: 22/22 rows correctly keyed.

Standing Gates 6/6 preserved. P6 #32 mitigation applied: `_create_monitoring_task` copy-adapted from canonical `atlas.mcp_server.tasks.create_task`.

---

## 2. Phase 3 implementation

### 2.1 File inventory

| File | Bytes | Purpose |
|---|---|---|
| `src/atlas/agent/domains/__init__.py` | 0 | Empty package marker (NEW) |
| `src/atlas/agent/domains/infrastructure.py` | 13,763 | Domain 1 module: 3 checks (vitals/uptime/anchor) + helpers (Prometheus query, async SSH, async local subprocess, create_monitoring_task adapted from Cycle 1I) (NEW) |
| `src/atlas/agent/scheduler.py` | 2,325 | UPDATED: imports Domain 1 + cadence dispatch (vitals/uptime 5min, anchor 1hr) + 1-min tick |

Total: ~385 lines added, 4 deleted.

### 2.2 Architecture

**system_vitals_check (5min cadence)**
- 5 nodes × 3 metrics = 15 probes via `asyncio.gather` (parallel; fits 90s window)
- Per probe: Prometheus `node_cpu_seconds_total` / `node_memory_*` / `node_filesystem_*` query against `http://192.168.1.40:9090/api/v1/query` (5s timeout)
- SSH fallback if Prometheus unavailable: `top -bn1` / `awk /proc/meminfo` / `df / --output=pcent` (8s timeout)
- Each probe writes one atlas.tasks row with payload.kind = `monitoring_cpu` / `monitoring_ram` / `monitoring_disk`; threshold_breach flag computed (CPU >85, RAM >90, disk >85)

**service_uptime_check (5min cadence)**
- 6 services × 1 probe each = 6 probes via `asyncio.gather` (parallel)
- Containers (postgres-beast/garage-beast on Beast): SSH to host + `docker inspect <target> --format '{{.State.Status}}'`
- Systemd services (atlas-mcp/orchestrator/mercury-scanner/nginx): SSH to host + `systemctl is-active <target>`
- Each probe writes one atlas.tasks row with payload.kind = `service_uptime`; is_healthy boolean computed (active or running)
- Mac mini DEFERRED per v0.2 P5 #35 (DNS intermittency)

**substrate_anchor_check (1hr cadence)**
- Run locally on Beast (atlas-agent runs on Beast where containers live): `docker inspect control-postgres-beast` + `docker inspect control-garage-beast`
- Compare observed StartedAt to canonical Phase 0 verified-live values
- Writes one atlas.tasks row with payload.kind = `substrate_check`; drift_detected flag
- READ-ONLY: docker inspect `--format '{{.State.StartedAt}}'` retrieval; never modifies

**scheduler.py wiring**
- 1-minute tick (`asyncio.sleep(60)`)
- Per-domain `last_run` dict tracks UTC datetime; first iteration fires all due cycles immediately (last_run empty -> due)
- Each check wrapped in try/except so one failure does not break the cadence dict or subsequent ticks

### 2.3 SSH dependency decision

Atlas .venv has neither paramiko nor asyncssh. Per Sloan directive: *"If SSH fallback requires paramiko/asyncssh and neither is in atlas dependencies, FILE A PACO_REQUEST before adding (dependency add = scope expansion = guardrail 5 territory)."*

**Resolution: no new dependency.** Implemented async SSH via `asyncio.create_subprocess_exec("ssh", "-o", "BatchMode=yes", ...)` using openssh-client (system-level on Beast) with the id_ed25519 key deployed Phase 0. Same approach for `docker inspect` (via `asyncio.create_subprocess_shell`).

Does NOT trigger guardrail 5 dep-add escalation: zero new Python dependencies; uses already-deployed system tooling (openssh-client + Beast's own docker daemon).

---

## 3. Bug caught + fixed mid-phase (5th rule discipline working)

### 3.1 Symptom

First smoke run: 5 monitoring_cpu + 5 monitoring_ram + 5 monitoring_disk + 1 substrate_check rows present, but **0 service_uptime rows.** scheduler logged `service_uptime_check_done` (cleanly returning), but no rows in atlas.tasks with payload.kind=service_uptime.

### 3.2 Root cause

In `_create_monitoring_task`:
```python
payload_with_kind = {"kind": kind, **payload}  # BUG: dict spread allows payload's kind to shadow
```

In `_probe_service` payload:
```python
await _create_monitoring_task(db, "service_uptime", {
    "node": svc["node"],
    "target": target,
    "kind": kind,  # <- this `kind` is svc kind ("container" or "systemd")
    "status": status,
    "is_healthy": is_healthy,
})
```

Dict spread evaluates left-to-right but later keys overwrite earlier ones. Result: `{"kind": "service_uptime", "node": ..., "kind": "container", ...}` -> final `"kind": "container"`. The 24 service_uptime rows from earlier smoke runs were inserted but mis-keyed under `payload.kind = "container"` or `"systemd"` -- escaping my filter `WHERE payload->>'kind'='service_uptime'`.

### 3.3 Diagnosis path

1. Initial: confirmed scheduler runs all 3 checks (vitals + uptime + substrate) by reviewing log lines + atlas.tasks growth
2. Hypothesized: service_uptime_check failing silently; ran standalone test calling service_uptime_check directly -- returned cleanly
3. Direct _probe_service test with print tracing: returned cleanly with task IDs
4. Looked up returned task IDs via psql -- found rows EXIST but with `payload.kind = container/systemd` instead of `service_uptime`
5. Source review of `_create_monitoring_task` -> spotted dict spread shadowing

### 3.4 Fix (2 edits)

**Fix 1** -- defensive `_create_monitoring_task`:
```python
# Before: payload_with_kind = {"kind": kind, **payload}  # BUG
# After:
payload_with_kind = dict(payload)
payload_with_kind["kind"] = kind  # explicit kind ALWAYS wins
```

**Fix 2** -- semantic clarity in `_probe_service`:
```python
# Before: "kind": kind  (svc["kind"] = container/systemd; conflicts with monitoring kind)
# After: "target_kind": kind  (renamed to avoid name conflict)
```

Both edits applied via Python script with assertion guards. Asserts confirmed:
- defensive merge present in `_create_monitoring_task`: True
- `target_kind` in `_probe_service`: True  
- no remaining payload-spread-shadow: True (`'"kind": kind, **payload'` not in source)

### 3.5 Post-fix verification

90s smoke re-run: all 5 expected payload kinds present with correct keying. service_uptime rows now show `{"kind": "service_uptime", "target_kind": "systemd", "target": "mercury-scanner.service", "is_healthy": true, ...}`.

### 3.6 Bug pattern (informational; not a new P6)

This is a generic Python dict-spread shadowing pattern (well-known anti-pattern). Caught at smoke-test stage by data-flow inspection (rows existed in DB, just wrong key). Not a P6 #25/#31/#32 directive-author hedge case -- it's a PD-side coding bug. P6 #32 mitigation (canonical reference impl copy) doesn't help here because the canonical `create_task` doesn't take an external kind parameter (kind is implicit in the table schema).

Further mitigation: future `_create_monitoring_task`-style helpers should use explicit-arg-wins merge pattern (`dict(payload); payload[arg]=arg`) rather than dict spread. Banked as an internal PD coding convention, not a P6 entry.

### 3.7 Discipline metric

Bug caught at PD pre-acceptance verification; never propagated to Paco. 5th-rule data-flow inspection (verify rows present + correctly keyed in DB, not just "function returned without exception") caught what unit tests would have caught earlier in a TDD shop. Self-corrected before paco_review write. Phase 3 acceptance achieved post-fix.

---

## 4. Phase 3 acceptance scorecard

**Sloan directive acceptance:** `python -m atlas.agent` runs 90s; logs show at least one Domain 1 cycle completes (CPU/RAM/disk for at least 3 of 5 nodes; service uptime check; substrate anchor check). atlas.tasks shows new rows with payload.kind in {monitoring_cpu, monitoring_ram, monitoring_disk, service_uptime, substrate_check}.

| Criterion | Result |
|---|---|
| 90s smoke runs without process-level crash | ✅ exit_rc=124 (timeout SIGTERM = clean termination) |
| At least one Domain 1 cycle completes | ✅ scheduler emits start+done lines for vitals + uptime + anchor checks |
| CPU/RAM/disk for at least 3 of 5 nodes | ✅ ALL 5 nodes (5 × 3 = 15 vitals rows): ck/beast/goliath/slimjim/kalipi |
| Service uptime check runs | ✅ 6 service_uptime rows post-fix (all 6 services probed: postgres-beast/garage-beast/atlas-mcp/orchestrator/mercury-scanner/nginx) |
| Substrate anchor check runs | ✅ 1 substrate_check row; postgres_match=true + garage_match=true + drift_detected=false |
| atlas.tasks payload.kind set match | ✅ {monitoring_cpu, monitoring_ram, monitoring_disk, service_uptime, substrate_check} -- 5/5 exact match |

1/1 acceptance gate PASS post-fix.

---

## 5. Standing Gates compliance (6/6 preserved)

| # | Gate | PRE | POST |
|---|---|---|---|
| 1 | B2b publication / subscription untouched | postgres anchor `2026-04-27T00:13:57.800746541Z` | bit-identical |
| 2 | Garage cluster untouched | garage anchor `2026-04-27T05:39:58.168067641Z` | bit-identical |
| 3 | mcp_server.py on CiscoKid untouched | (orthogonal scope) | unchanged |
| 4 | atlas-mcp.service untouched | active, MainPID 2173807 | active, MainPID 2173807 UNCHANGED |
| 5 | nginx vhosts on CiscoKid unchanged | (orthogonal scope) | unchanged |
| 6 | mercury-scanner.service on CK untouched | active, MainPID 643409 | active, MainPID 643409 UNCHANGED |

Domain 1 monitoring is READ-ONLY:
- Prometheus queries are HTTP GET only
- SSH probes use `top` / `awk /proc/*` / `df` / `systemctl is-active` / `docker inspect` (all observation commands)
- substrate_anchor_check uses `docker inspect --format` (retrieval; never modifies container state)

The atlas-agent runtime is the smoke test process only; it doesn't enable atlas-agent.service. Agent-driven monitoring writes new atlas.tasks rows but never modifies fleet state.

---

## 6. State at Phase 3 close

- atlas-agent.service: still loaded inactive disabled (Phase 1 acceptance state preserved through Phases 2 + 3; Phase 9 will enable)
- atlas-mcp.service: active, MainPID 2173807 unchanged (~7h+ uptime through Phases 0-3)
- mercury-scanner.service: active, MainPID 643409 (Standing Gate #6 preserved)
- atlas HEAD: `54e3a26` (NEW; Phase 3 implementation commit; parent `473763f` Phase 2)
- HEAD on control-plane-lab: `7f50db8` (Phase 2 close-confirm + Phase 3 GO)
- B2b + Garage anchors: bit-identical, holding 96+ hours through Phase 3 work
- atlas.tasks queue: 22 fresh monitoring rows (5 cpu + 5 ram + 5 disk + 6 uptime + 1 substrate); all status=done after Phase 2 poller no-op handler claimed+completed each

---

## 7. Asks of Paco

1. **Confirm Phase 3 1/1 acceptance gate PASS** against verified-live evidence (sections 0 + 4) -- 22 atlas.tasks rows with all 5 expected payload kinds.
2. **Confirm Standing Gates 6/6 preserved** (section 5).
3. **Acknowledge spec/directive divergence** (atlas.events spec → atlas.tasks Sloan directive). PD surfaced divergence pre-execution + got explicit CEO confirmation. Spec amendment to ratify atlas.tasks routing for Domain 1 should fold into cycle close-out (canon hygiene per Phase 2 amendment pattern).
4. **Acknowledge mid-phase bug catch + fix** (dict-spread kind-shadowing in `_create_monitoring_task`). Caught at PD pre-acceptance via data-flow inspection. Self-corrected before paco_review. Banked as PD-internal coding convention; not a new P6 (it's a generic Python anti-pattern, not a directive-author hedge family case).
5. **Authorize Phase 4 GO** -- Domain 2: Talent operations per build spec lines 314-340 (job_search_log_check + weekly_digest_compile).

---

## 8. Cross-references

**Doc trail:**
- `tasks/atlas_v0_1_agent_loop.md` lines 272-313 (Phase 3 spec, commit `7f50db8`)
- `docs/paco_response_atlas_v0_1_phase2_confirm_phase3_go.md` (Phase 3 GO, HEAD `7f50db8`)
- Sloan CEO directive Day 78 morning (chat-delivered; explicit atlas.tasks override + 5 kind names + 5min uptime cadence)

**Atlas commits:**
- Phase 2: `473763f` (agent loop skeleton)
- Phase 3: `54e3a26` (Domain 1 Infrastructure monitoring) -- THIS PHASE

**Discipline metrics this cycle so far:**
- Phase 0 close: 7/7 PASS post-retry; Standing Gates 6/6
- Phase 1 close: 3/3 PASS first-try; Standing Gates 6/6
- Phase 2 close: 1/1 PASS post-spec-amendment; Standing Gates 6/6
- Phase 3 close: 1/1 PASS post-bug-fix; Standing Gates 6/6
- 4 paco_requests filed at PD pre-execution review (handler count / pretest flake / Phase 0 SSH+dep / Phase 2 DB API). All caught under 5-guardrail rule + SR #6.
- 4th-instance directive-author hedge propagation pattern (P6 #32) mitigation actively applied at Phases 2 + 3 (canonical reference impl copy).
- 1 PD-side coding bug (dict spread shadow) caught at pre-acceptance via data-flow inspection; not a P6 family case.

**File-level changes this phase:**
- atlas package: `src/atlas/agent/domains/__init__.py` (NEW), `src/atlas/agent/domains/infrastructure.py` (NEW), `src/atlas/agent/scheduler.py` (modified)
- Atlas commit: `54e3a26`
- control-plane-lab: this paco_review (untracked, transient until cycle close-out fold)

---

## 9. Status

**AWAITING PACO CLOSE-CONFIRM + PHASE 4 GO.**

PD paused. Domain 1 Infrastructure monitoring live in agent skeleton; 22 atlas.tasks rows per cycle (5 cpu + 5 ram + 5 disk + 6 service_uptime + 1 substrate_check); Standing Gates 6/6 + spec/directive divergence flagged + mid-phase bug fixed pre-acceptance. Phase 4 (Domain 2: Talent operations; src/atlas/agent/domains/talent.py + job_search_log_check + weekly_digest_compile) is the next deliverable per build spec lines 314-340.

-- PD
