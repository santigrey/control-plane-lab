# paco_directive_homelab_patch_cycle_cve_2026_31431

**To:** PD | **From:** Paco | **Date:** 2026-05-02 Day 78 mid-day
**Authority:** CEO directive (Path 1 chosen Day 78 mid-day; patch now, before Phase 7 resumes)
**Status:** ACTIVE -- supersedes Phase 7 GO until cycle closes
**Tracks:** Mr Robot backlog Job #1 (`docs/mr_robot_backlog_v1_0.md`)

---

## Background

CVE-2026-31431 (Copy Fail) Linux kernel LPE; public PoC; fleet exposure verified live Day 78 morning (5 vulnerable Linux nodes; 2 unprobed). CEO authorized operational patch cycle BEFORE Mr Robot is built.

Full context: `docs/mr_robot_backlog_v1_0.md` Job #1.

## Phase 7 status

Phase 7 GO at HEAD `07e0e26` (corrected scope: 7.1 emit_event + 7.2 mercury cancel-window) is **PAUSED**. PD does NOT execute Phase 7 until this patch cycle reaches completion + Phase 7 resumption trigger fires from Paco.

## Pre-patch standing gates baseline (current values; will reset on Beast + CK reboot per Steps 4 + 5)

| Gate | Pre-patch value |
|---|---|
| 1. B2b anchor (control-postgres-beast StartedAt) | `2026-04-27T00:13:57.800746541Z` |
| 2. Garage anchor (control-garage-beast StartedAt) | `2026-04-27T05:39:58.168067641Z` |
| 4. atlas-mcp.service MainPID | 2173807 |
| 5. atlas-agent.service | loaded inactive disabled |
| 6. mercury-scanner.service MainPID | 643409 |

Gates 1, 2, 4, 6 will cycle on reboot. Gate 5 is preserved (unit stays disabled). New post-patch values become the new canonical baseline; document at Step 6.

## Procedure -- 6 steps

One step at a time. Each step ends with PD writing `docs/paco_review_patch_step<N>_<node>.md` + commit + push + handoff trigger. CEO authorizes each next step explicitly.

---

### Step 1 -- CEO probe: KaliPi + Pi3 kernel + sudo capability

**Owner:** CEO (PD cannot reach KaliPi as jes user; Pi3 access path TBD).

**CEO actions:**
1. SSH to KaliPi (sloan user): `uname -r && lsb_release -ds && sudo -n true 2>&1`
2. SSH or console to Pi3 (sloanzj user via TS or LAN): `uname -r && cat /etc/os-release | grep PRETTY_NAME && sudo -n true 2>&1`
3. Report values + sudo status back to Paco (chat message OR commit notes file `docs/ceo_kalipi_pi3_kernel_probe.md`).

**Acceptance:** Both kernel versions known; both sudo capability known. If sudo requires password, PD will need CEO at terminal during patch step.

**Standing gates impact:** None. Read-only probe.

---

### Step 2 -- SlimJim (192.168.1.40)

**Owner:** PD via homelab_ssh_run.

**Pre-patch state capture:**
```
uname -r                      # current: 6.8.0-110-generic
systemctl is-active mosquitto # MQTT broker
uptime                        # baseline
```

**Patch:**
```
sudo apt-get update
sudo apt-get dist-upgrade -y
# verify kernel package was upgraded
dpkg -l | grep linux-image- | head -5
sudo reboot
```

**Wait ~90s for reboot. SSH back in.**

**Post-patch verification:**
```
uname -r                      # NEW kernel; document new value
systemctl is-active mosquitto # back up
systemctl --failed            # zero failed units
```

**Acceptance:** New kernel running; mosquitto active; zero failed units.

**Standing gates impact:** None directly. SlimJim is edge-only; not part of standing gates.

---

### Step 3 -- KaliPi (192.168.1.254) + Pi3 (192.168.1.139 / TS 100.71.159.102)

**Owner:** Joint -- PD executes via homelab_ssh_run if sudo permits; CEO at terminal if password required.

**Per-node pattern (same as SlimJim):**
- Pre-patch: `uname -r`; list services running (`systemctl list-units --state=running --type=service | head -10`)
- Patch: `sudo apt-get update && sudo apt-get dist-upgrade -y && sudo reboot`
- Post-patch (~90s): `uname -r` + `systemctl --failed` + service-specific verification

**KaliPi services:** Pentesting workloads. Likely no critical persistent services.

**Pi3 services:** DNS Gateway TBD per memory. CEO confirms before patching whether DNS service is live and which name to verify post-reboot.

**Acceptance:** Both nodes new kernel; zero failed units; CEO-verified service health.

**Standing gates impact:** None.

---

### Step 4 -- Goliath (192.168.1.20; sloan4)

**Owner:** PD via homelab_ssh_run.

**Pre-patch state capture:**
```
uname -r                      # 6.11.0-1016-nvidia
systemctl is-active ollama    # GPU inference service
ollama list                   # confirm model inventory: llama3.1:70b, deepseek-r1:70b, qwen2.5:72b
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
```

**Special consideration:** Goliath uses `linux-image-*-nvidia` kernel meta-package (GB10 Blackwell). `dist-upgrade` should pull the matching nvidia-kernel and the userspace nvidia-driver in lockstep. After reboot, verify nvidia-smi works AND ollama can load a model before declaring success.

**Patch:**
```
sudo apt-get update
sudo apt-get dist-upgrade -y
dpkg -l | grep -E 'linux-image-.*-nvidia|nvidia-driver' | head -5
sudo reboot
```

**Wait ~120s for reboot (GPU init takes longer).**

**Post-patch verification (CRITICAL because GPU stack):**
```
uname -r                      # NEW kernel
nvidia-smi                    # GPU detected; driver loaded
systemctl is-active ollama    # service active
ollama list                   # model inventory unchanged
# Test inference (light):
curl -s http://localhost:11434/api/generate -d '{"model":"llama3.1:70b","prompt":"hi","stream":false}' | head -5
```

**If nvidia-smi fails or ollama can't serve:** STOP. Do not proceed to Step 5. File paco_request. GPU/driver mismatch is rollback-territory; CEO ratifies recovery path.

**Acceptance:** New kernel + nvidia-smi works + ollama loads model + 1 inference round-trip succeeds.

**Standing gates impact:** Atlas Domain 1 monitoring will note Goliath service uptime reset. Expected. Not a failure.

---

### Step 5 -- TheBeast (192.168.1.152) + ANCHOR RESET

**Owner:** PD via homelab_ssh_run.

**Capacity context:** Beast hosts atlas-mcp.service + atlas Postgres replica (control-postgres-beast Docker container = B2b anchor) + Garage cluster (control-garage-beast Docker container = Garage anchor) + atlas-agent.service (disabled inactive).

**Pre-patch state capture:**
```
uname -r                      # 5.15.0-176-generic
systemctl is-active atlas-mcp.service  # active
systemctl is-active atlas-agent.service # inactive (Phase 1 acceptance state)
docker ps --format 'table {{.Names}}\t{{.Status}}'
docker inspect control-postgres-beast --format '{{.State.StartedAt}}'  # OLD B2b anchor
docker inspect control-garage-beast --format '{{.State.StartedAt}}'    # OLD Garage anchor
```

**Document OLD anchor values in Step 5 paco_review.** They become the historical baseline.

**Patch:**
```
sudo apt-get update
sudo apt-get dist-upgrade -y
sudo reboot
```

**Wait ~90s for reboot.**

**Post-patch verification:**
```
uname -r                      # NEW kernel
docker ps --format 'table {{.Names}}\t{{.Status}}'
# atlas-mcp.service auto-starts after Docker; wait if needed
systemctl is-active atlas-mcp.service
systemctl is-active atlas-agent.service  # MUST stay inactive (Phase 1 acceptance)
docker inspect control-postgres-beast --format '{{.State.StartedAt}}'  # NEW B2b anchor
docker inspect control-garage-beast --format '{{.State.StartedAt}}'    # NEW Garage anchor
```

**B2b subscription verification:**
```
docker exec control-postgres-beast psql -U admin -d controlplane -c 'SELECT subname, subenabled, last_msg_send_time FROM pg_stat_subscription'
# B2b subscription should be active and replicating from CK
```

**Garage cluster verification:**
```
docker exec control-garage-beast /garage status
# Cluster healthy; node alive
```

**Acceptance:** New kernel + atlas-mcp.service active + atlas-agent.service still disabled inactive + B2b subscription replicating + Garage cluster healthy + new anchor values documented.

**Standing gates impact:** Gates 1+2 RESET. New values become canonical post-patch baseline. PD documents both new timestamps in Step 5 paco_review. Paco will update paco_session_anchor.md + propagate new values to all canon at cycle close (Step 6).

---

### Step 6 -- CiscoKid (192.168.1.10) + Mercury restart + canon anchor update

**Owner:** PD via homelab_ssh_run; CEO at terminal recommended for Mercury restart confirmation.

**Capacity context:** CK hosts orchestrator.service (Alexandra) + mercury-scanner.service (paper-trader) + nginx (TLS reverse proxy) + control-postgres Docker container (canonical Postgres + B2b publisher).

**Pre-patch state capture:**
```
uname -r                      # 5.15.0-176-generic
systemctl is-active orchestrator.service
systemctl is-active mercury-scanner.service  # MainPID 643409 (Day 78 morning fix preserved)
systemctl is-active nginx
docker ps --format 'table {{.Names}}\t{{.Status}}'
docker inspect control-postgres --format '{{.State.StartedAt}}'  # canonical Postgres anchor
# Mercury state
docker exec control-postgres psql -U admin -d controlplane -c \
  "SELECT count(*) AS total, max(opened_at) AS latest_opened, count(*) FILTER (WHERE status='open') AS still_open FROM mercury.trades"
```

**Mercury preparation:** Mercury is paper-trade only and stateless between scan cycles. Reboot does not lose trade history (persisted in Postgres). After reboot, mercury-scanner.service auto-starts; new MainPID; resumes Strategy B AI Mispricing scan loop.

**Patch:**
```
sudo apt-get update
sudo apt-get dist-upgrade -y
sudo reboot
```

**Wait ~90s for reboot.**

**Post-patch verification (CRITICAL because biggest blast radius):**
```
uname -r                      # NEW kernel
docker ps --format 'table {{.Names}}\t{{.Status}}'
systemctl is-active orchestrator.service
systemctl is-active mercury-scanner.service
systemctl is-active nginx
docker inspect control-postgres --format '{{.State.StartedAt}}'  # NEW canonical Postgres anchor

# Mercury health
systemctl show -p MainPID -p ActiveEnterTimestamp mercury-scanner.service
journalctl -u mercury-scanner.service -n 10 --no-pager
# trade count unchanged from pre-patch (paper-trade persistence)
docker exec control-postgres psql -U admin -d controlplane -c \
  "SELECT count(*) AS total FROM mercury.trades"

# Alexandra dashboard health
curl -sk https://sloan3.tail1216a3.ts.net/dashboard | head -5
curl -sk https://sloan3.tail1216a3.ts.net:8443/mcp -X POST -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' 2>&1 | head -5

# B2b publisher verification
docker exec control-postgres psql -U admin -d controlplane -c \
  "SELECT pubname, puballtables FROM pg_publication"
```

**Atlas-side verification (from Beast):** Atlas-mcp.service should still be active (untouched at Step 5 reboot per current). atlas-agent.service still disabled inactive. Substrate anchors documented in Step 5 paco_review remain valid; CK Postgres restart will trigger B2b subscription resume on Beast side; atlas Domain 1 substrate_check will resume normal cadence.

**Canon update at Step 6 close:**
- Update `paco_session_anchor.md` with new B2b anchor + new Garage anchor + new canonical Postgres anchor (from Step 5 + Step 6)
- Update `CHECKLIST.md` audit entry for full patch cycle
- Update `docs/mr_robot_backlog_v1_0.md` Job #1: status PENDING -> COMPLETE; per-node patch table updated with new kernel versions
- Optionally update `docs/feedback_paco_pre_directive_verification.md` if any new P6 lesson surfaces during patch cycle

**Acceptance:** All CK services back up + Mercury trade count unchanged + Alexandra dashboard + MCP server live + B2b publisher present + atlas-mcp on Beast still healthy + new anchor values documented + canon updated.

**Standing gates impact:** Gate 4 cycles (atlas-mcp.service didn't reboot if CK reboots first; if CK rebooted before Beast, the B2b subscription on Beast may have surfaced a brief disconnect -- harmless). Expected. Mercury Gate 6 cycles to new MainPID (post-Day-78 MainPID 643409 retires; new MainPID is fine).

---

## Phase 7 resumption trigger

After Step 6 paco_review lands + CEO ratifies, Paco issues `paco_response_homelab_patch_cycle_close.md` confirming canon update + closing Mr Robot backlog Job #1. Phase 7 resumes via fresh handoff trigger:

```
PD, patch cycle complete. Read docs/paco_response_homelab_patch_cycle_close.md and resume Phase 7 against amended spec lines 427-451.
```

## Discipline reminders

- One step at a time. PD does not chain steps. CEO authorizes each next step explicitly.
- Pre-commit secrets-scan BOTH broad + tightened on every paco_review (P6 #34 standing practice; literal credentials remain prohibited even in patch-cycle docs).
- If any step fails acceptance: STOP + paco_request + CEO ratifies recovery path.
- Atlas Domain 1 monitoring service uptime + substrate anchor checks WILL fire during patch window. These are expected events; do not interpret as failure signals.
- Goliath GPU stack is the highest-risk node for kernel regression. Treat Step 4 nvidia-smi + ollama acceptance as load-bearing.
- Beast reboot will reset B2b + Garage anchors. New values are the new baseline; old values move to historical canon.

## Trigger from CEO to PD (Step 1 not yet executed; CEO probes KaliPi + Pi3 first)

```
Paco directive: docs/paco_directive_homelab_patch_cycle_cve_2026_31431.md committed. Phase 7 paused. Step 1 is CEO action: probe KaliPi (sloan@192.168.1.254) and Pi3 kernel + sudo capability. Report values; PD then executes Step 2 SlimJim on CEO go.
```

-- Paco
