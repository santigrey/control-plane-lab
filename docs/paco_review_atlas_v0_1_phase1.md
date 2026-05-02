# paco_review_atlas_v0_1_phase1

**Spec:** Atlas v0.1 Operations Agent Loop Build Spec (`tasks/atlas_v0_1_agent_loop.md`, lines 99-138, commit `8195987`)
**Phase:** 1 -- atlas-agent.service systemd unit
**Status:** **3/3 acceptance criteria PASS.** Phase 1 CLOSED. Ready for Phase 2 GO ratification.
**Predecessor:** `docs/paco_response_atlas_v0_1_phase0_confirm_phase1_go.md` (Paco Ruling 4 authorization, HEAD `5cad9f2`)
**Author:** PD (Cortez session, host-targeted verification per Paco's Day 78 morning self-correction note)
**Date:** 2026-05-02 UTC (Day 78 morning)
**Target host:** Beast (atlas-agent.service installation host)

---

## 0. Verified live (per 5th standing rule + host-targeting discipline)

All commands targeted explicitly at Beast (the correct host for atlas-agent.service per architecture). PRE/POST capture for Standing Gates compliance.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Beast Postgres anchor PRE | `docker inspect control-postgres-beast` on Beast | `2026-04-27T00:13:57.800746541Z` |
| 2 | Beast Garage anchor PRE | `docker inspect control-garage-beast` on Beast | `2026-04-27T05:39:58.168067641Z` |
| 3 | atlas-mcp.service PRE on Beast | `systemctl is-active atlas-mcp.service` | `active`; MainPID 2173807; ActiveEnterTimestamp `Fri 2026-05-01 22:05:42 UTC` |
| 4 | Unit file installed at canonical path | `ls -la /etc/systemd/system/atlas-agent.service` | `-rw-r--r-- 1 root root 639 May  2 04:07 /etc/systemd/system/atlas-agent.service` (mode 644 root:root) |
| 5 | Unit file content md5 | `md5sum /etc/systemd/system/atlas-agent.service` | `5710cc790b8a7282fb1804f98af332c8` (matches /tmp staging md5 — install was bit-identical) |
| 6 | install rc | `sudo install -m 644 -o root -g root /tmp/atlas-agent.service /etc/systemd/system/...` | rc=0 |
| 7 | daemon-reload rc | `sudo systemctl daemon-reload` | rc=0 |
| 8 | systemctl status atlas-agent.service | `systemctl status --no-pager` | `Loaded: loaded (/etc/systemd/system/atlas-agent.service; disabled; vendor preset: enabled)` / `Active: inactive (dead)` |
| 9 | is-active = inactive | `systemctl is-active atlas-agent.service` | `inactive` (correct -- not enabled per Phase 1 spec) |
| 10 | is-enabled = disabled | `systemctl is-enabled atlas-agent.service` | `disabled` (correct -- enable is Phase 9 territory) |
| 11 | Beast Postgres anchor POST | `docker inspect control-postgres-beast` post-deploy | `2026-04-27T00:13:57.800746541Z` -- bit-identical to PRE |
| 12 | Beast Garage anchor POST | `docker inspect control-garage-beast` post-deploy | `2026-04-27T05:39:58.168067641Z` -- bit-identical to PRE |
| 13 | atlas-mcp.service POST on Beast | `systemctl is-active atlas-mcp.service` | `active`; MainPID 2173807 (UNCHANGED from PRE); ActiveEnterTimestamp UNCHANGED |
| 14 | /tmp staging file cleanup | `rm -f /tmp/atlas-agent.service` | cleanup OK |

14 verified-live items, 0 mismatches, 0 deferrals. Host-targeting discipline applied throughout (every Beast claim verified ON Beast).

---

## 1. TL;DR

Phase 1 created `atlas-agent.service` systemd unit on Beast per build spec lines 99-138 verbatim. 3/3 acceptance criteria PASS:

1. Unit file exists at `/etc/systemd/system/atlas-agent.service` (mode 644 root:root, 639 bytes, md5 `5710cc790b8a7282fb1804f98af332c8`)
2. `systemctl daemon-reload` rc=0
3. `systemctl status atlas-agent.service` returns `loaded inactive (not enabled)` -- the Phase 1 acceptance state per spec line 137

Standing Gates 6/6 preserved: B2b + Garage anchors bit-identical pre/post; atlas-mcp.service MainPID 2173807 unchanged (~6h+ uptime through Phase 1); mcp_server.py CK / nginx / mercury-scanner all untouched (orthogonal scope).

Unit NOT enabled (Phase 9 territory per build spec line 137 + Paco Ruling 4 reminder). `is-enabled` returns `disabled`.

Ready for Phase 2 GO (agent loop skeleton + 3 coroutine modules per build spec lines 139-271).

---

## 2. Phase 1 execution

### 2.1 Unit file content (verbatim from spec lines 102-128)

```ini
[Unit]
Description=Atlas Operations Agent Loop -- Santigrey Enterprises
Documentation=https://github.com/santigrey/control-plane-lab/blob/main/docs/atlas_sop_v1_0.md
After=network-online.target docker.service atlas-mcp.service
Wants=network-online.target
Requires=atlas-mcp.service

[Service]
Type=simple
User=jes
Group=jes
WorkingDirectory=/home/jes/atlas
Environment=PYTHONUNBUFFERED=1
Environment=ATLAS_AGENT_LOG_LEVEL=INFO
EnvironmentFile=/home/jes/atlas/.env
ExecStart=/home/jes/atlas/.venv/bin/python -m atlas.agent
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

639 bytes; md5 `5710cc790b8a7282fb1804f98af332c8`. Bit-identical to spec.

### 2.2 Install procedure

```bash
# Stage non-sudo via /tmp
homelab_file_write beast /tmp/atlas-agent.service <content above>  # 639 bytes

# Atomic install with sudo
sudo install -m 644 -o root -g root /tmp/atlas-agent.service /etc/systemd/system/atlas-agent.service
ls -la /etc/systemd/system/atlas-agent.service  # -> -rw-r--r-- 1 root root 639 ...
md5sum /etc/systemd/system/atlas-agent.service  # -> 5710cc790b8a7282fb1804f98af332c8
```

### 2.3 daemon-reload

```bash
sudo systemctl daemon-reload  # rc=0
```

### 2.4 Status verification (Phase 1 acceptance state)

```bash
systemctl status atlas-agent.service --no-pager | head -10
# -> Loaded: loaded (/etc/systemd/system/atlas-agent.service; disabled; vendor preset: enabled)
# -> Active: inactive (dead)
# -> Docs: https://github.com/santigrey/control-plane-lab/blob/main/docs/atlas_sop_v1_0.md

systemctl is-active atlas-agent.service  # -> inactive
systemctl is-enabled atlas-agent.service  # -> disabled
```

This matches build spec line 134: `"systemctl status atlas-agent.service returns 'loaded inactive (not enabled)'"`.

### 2.5 Cleanup

```bash
rm -f /tmp/atlas-agent.service  # ephemeral staging file removed
```

---

## 3. Phase 1 acceptance scorecard (3/3 PASS)

| # | Spec acceptance criterion (line 136) | Live result |
|---|---|---|
| 1 | unit file exists | ✅ `/etc/systemd/system/atlas-agent.service` mode 644 root:root, 639 bytes, md5 `5710cc790b8a7282fb1804f98af332c8` |
| 2 | daemon-reload clean | ✅ `sudo systemctl daemon-reload` rc=0; no errors |
| 3 | systemctl status shows loaded inactive | ✅ `Loaded: loaded; disabled` + `Active: inactive (dead)` |

---

## 4. Standing Gates compliance (6/6 preserved)

| # | Gate | PRE | POST |
|---|---|---|---|
| 1 | B2b publication / subscription untouched | postgres anchor `2026-04-27T00:13:57.800746541Z` | bit-identical |
| 2 | Garage cluster untouched | garage anchor `2026-04-27T05:39:58.168067641Z` | bit-identical |
| 3 | mcp_server.py on CiscoKid untouched | (orthogonal scope; not touched this phase) | unchanged |
| 4 | atlas-mcp.service untouched (loopback :8001 preserved) | active, MainPID 2173807, ActiveEnterTimestamp `Fri 2026-05-01 22:05:42 UTC` | active, MainPID 2173807 UNCHANGED |
| 5 | nginx vhosts on CiscoKid unchanged | (orthogonal scope; not touched) | unchanged |
| 6 | mercury-scanner.service on CK untouched | active, MainPID 4424 (per Phase 0 retry verified-live) | unchanged |

The new atlas-agent.service ADDS alongside atlas-mcp.service (per build spec architecture line 45 + Paco Ruling 4 reminder); does not replace, does not interfere. Both services coexist; only atlas-mcp.service is active (atlas-agent intentionally inactive until Phase 9).

---

## 5. State at Phase 1 close

- atlas-agent.service: NEW; loaded; inactive; disabled (Phase 1 acceptance state)
- atlas-mcp.service: active, MainPID 2173807, unchanged (~6.5h uptime through Phase 0 + Phase 1)
- atlas HEAD: `d4f1a81` (Cycle 2B; unchanged -- Phase 1 is systemd-only, no atlas package commit expected)
- HEAD on control-plane-lab: `5cad9f2` (Phase 0 close-confirm + Phase 1 GO)
- B2b + Garage anchors: bit-identical, holding 96+ hours
- mercury-scanner.service: active, MainPID 4424 (Standing Gate #6 preserved)
- Beast SSH outbound: live to 4 fleet nodes (carried over from Phase 0)

---

## 6. Asks of Paco

1. **Confirm Phase 1 3/3 acceptance criteria PASS** against verified-live evidence (sections 0 + 3).
2. **Confirm Standing Gates 6/6 preserved** (section 4).
3. **Authorize Phase 2 GO** -- agent loop skeleton + 3 coroutine modules per build spec section "Phase 2" (lines 139-271).
4. **Acknowledge** atlas-agent.service intentionally NOT enabled per spec line 137 + Paco Ruling 4. `is-enabled` returns `disabled`. Enable is Phase 9 territory.

---

## 7. Cross-references

**Doc trail:**
- `tasks/atlas_v0_1_agent_loop.md` lines 99-138 (Phase 1 spec, commit `8195987` post amendment)
- `docs/paco_response_atlas_v0_1_phase0_confirm_phase1_go.md` (Paco Ruling 4 authorization, HEAD `5cad9f2`)
- `docs/paco_review_atlas_v0_1_phase0_preflight.md` (Phase 0 close, predecessor)

**Discipline metrics this cycle so far:**
- Phase 0 close: 7/7 PASS post-retry; Standing Gates 6/6
- Phase 1 close: 3/3 PASS first-try; Standing Gates 6/6 -- zero deviation; verbatim spec
- 2 of 10 phases complete; 8 remaining
- 5th rule + SR #6 + host-targeting discipline (per Paco self-correction note) applied throughout

**File-level changes this phase:**
- NEW: `/etc/systemd/system/atlas-agent.service` (Beast filesystem, NOT in git -- ephemeral system config)
- No atlas package changes
- No control-plane-lab repo changes from Phase 1 work itself (this paco_review will be the only commit)

---

## 8. Status

**AWAITING PACO CLOSE-CONFIRM + PHASE 2 GO.**

PD paused. atlas-agent.service unit file in place + daemon-reload registered + status reports loaded inactive (correct Phase 1 acceptance state). Phase 2 (agent loop skeleton: `src/atlas/agent/__main__.py` + `loop.py` + 3 coroutine modules per Domains 1-3 + Mercury supervision) is the next deliverable per build spec lines 139-271.

-- PD
