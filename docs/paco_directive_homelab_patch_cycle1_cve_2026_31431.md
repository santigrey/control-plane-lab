# paco_directive_homelab_patch_cycle1_cve_2026_31431

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-03 Day 79 mid-day
**Authority:** CEO ratified Day 79 mid-day (Linux patch cycle GO; Decision 1.1=Cycle 1 only Beast/CK/SlimJim Ubuntu kernel; 2b=maintenance-window flip for atlas-agent; 3.2=SlimJim->Beast->CK order CK-last; 4.1=forced reboot; 5.2=one PD directive serial through 3 nodes).
**Status:** ACTIVE
**Tracks:** CVE-2026-31431 patch cycle Step 2+ (Step 1 banked at reachability cycle Step 3.5 close `cb8a109`).
**Predecessor:** Atlas v0.1 ship (control-plane HEAD `b8e66e8`; atlas-agent.service production-stable since Day 79 03:57:17 UTC; substrate ~158h+).
**Target hosts:** SlimJim (192.168.1.40), Beast (192.168.1.152), CK (192.168.1.10) -- in this order.
**Out of scope this cycle:** Goliath (584 upgradable + major kernel 6.11->6.17 + GPG key expired = dedicated future cycle); KaliPi/Pi3 (no kernel via apt; non-kernel apt cycle separately).
**SR #7 application:** Third proper application. Paco probed kernel inventory + sudo + reboot-pending + apt list --upgradable + special-concerns per node BEFORE writing this directive. SR #7 verified-live block at section 1.

---

## 0. Cycle context

**CVE-2026-31431** = generic placeholder for the kernel security advisory driving this cycle. The actual concrete patch landing is Ubuntu kernel `linux-image-generic` bump:
- Beast/CK (Ubuntu 22.04 jammy): `5.15.0-176-generic` -> `5.15.0-177-generic`
- SlimJim (Ubuntu 24.04 noble): `6.8.0-110-generic` -> `6.8.0-111-generic`

Both bumps are routine LTS kernel maintenance per Ubuntu's HWE/security update stream. No exotic patch path; standard `apt-get dist-upgrade` + reboot.

## 1. Verified live (Paco SR #7 preflight, Day 79 mid-day)

| # | Claim | Probe | Result |
|---|---|---|---|
| 1 | SlimJim kernel + sudo | `uname -r; sudo -n true; [ -f /var/run/reboot-required ]` | `6.8.0-110-generic`; SUDO_NOPASSWD; NO_REBOOT_PENDING |
| 2 | SlimJim upgradable count + kernel pending | `apt list --upgradable` filtered | 41 total; `linux-image-generic 6.8.0-111.111` pending |
| 3 | SlimJim mosquitto active | `systemctl is-active mosquitto.service` | active |
| 4 | Beast kernel + sudo | same | `5.15.0-176-generic`; SUDO_NOPASSWD; NO_REBOOT_PENDING |
| 5 | Beast upgradable + kernel pending | `apt list --upgradable` filtered | 45 total; `linux-image-generic 5.15.0.177.162` pending |
| 6 | Beast atlas-agent runtime | `systemctl show atlas-agent.service` | MainPID=2872599 NRestarts=0 active enabled (production from Day 79 03:57) |
| 7 | Beast deadsnakes PPA scope | `apt-cache policy + dpkg -l python3.11` | python3.11 from deadsnakes provides atlas runtime venv; PPA index unreachable but installed packages OK; **dist-upgrade does NOT touch python3.11 packages** (verified via `apt-get -s dist-upgrade | grep linux`); deadsnakes broken-fetch is cosmetic warning only |
| 8 | CK kernel + sudo | same | `5.15.0-176-generic`; SUDO_NOPASSWD; NO_REBOOT_PENDING |
| 9 | CK upgradable + kernel pending | `apt list --upgradable` filtered | 30 total; `linux-image-generic 5.15.0.177.162` pending |
| 10 | CK mercury-scanner active | `systemctl is-active mercury-scanner.service` | active MainPID=643409 |
| 11 | CK atlas-mcp.service runtime | `systemctl show atlas-mcp.service` | active MainPID=2173807 (Beast atlas-agent depends on this for MCP calls; CK reboot will interrupt) |
| 12 | Substrate anchors PRE | `docker inspect control-postgres-beast / control-garage-beast` | postgres `2026-04-27T00:13:57.800746541Z` restart=0; garage `2026-04-27T05:39:58.168067641Z` restart=0; ~158h+ bit-identical |
| 13 | atlas-agent dependency chain on CK | `systemctl cat atlas-agent.service` (Phase 9 directive section 1) | `Requires=atlas-mcp.service` (atlas-mcp on Beast itself, not CK; CK reboot does NOT trigger atlas-agent restart unless homelab MCP server on CK is the dep -- which it is NOT for atlas-agent runtime) |
| 14 | Mercury-scanner depends on CK substrate | (mercury runs on CK) | CK reboot interrupts mercury-scanner; mercury auto-restarts on systemd boot |

14 verification rows. **0 mismatches.** Cycle 1 scope confirmed safe and bounded.

---

## 2. Cycle 1 implementation

### 2.1 Discipline reminders

- **Patch cycle is destructive on every node** (kernel bump + reboot). One step at a time per node; verify each completes before moving to next.
- **Order is load-bearing:** SlimJim (lowest blast radius; if reboot fails, no other service depends on it) -> Beast (atlas-agent host; maintenance-window flip required) -> CK LAST (orchestrator + MCP server + mercury-scanner host; reboot interrupts mercury but mercury auto-restarts on boot; reboot does NOT lose Paco's Cortez/JesAir SSH path because new kernel boots and SSHD comes back).
- **DO NOT touch Goliath, KaliPi, or Pi3 in this cycle.** Goliath needs separate dedicated cycle for major kernel + driver + expired-GPG remediation. KaliPi/Pi3 need separate non-kernel apt cycle.
- **DO NOT remove or downgrade any python3.11 packages** on Beast (Atlas runtime venv depends on them via deadsnakes PPA).
- **Use `apt-get` (NOT `apt`)** for non-interactive scripted execution.
- **`dist-upgrade` (NOT `upgrade`)** -- kernel packages need dist-upgrade to install new kernel image alongside existing.
- **Beast atlas-agent maintenance-window flip:** explicit `systemctl stop atlas-agent.service` BEFORE Beast reboot. Document as planned interruption (NRestarts will increment by 1 post-reboot when systemd auto-starts via `WantedBy=multi-user.target`; this is expected; SG5 invariant for Phase 9+ allows bounded restarts).
- **Substrate anchors WILL CHANGE on Beast reboot:** `control-postgres-beast` + `control-garage-beast` containers will restart when docker.service restarts after reboot. New StartedAt timestamps post-reboot are EXPECTED for Beast reboot, NOT a SG2/SG3 violation. Document new anchors post-reboot as the new baseline.
- **CK reboot impacts:** mercury-scanner.service (auto-restarts), homelab-mcp.service (auto-restarts; my own tool path; expect 60-120s outage post-reboot before MCP reconnects). Plan CK reboot last so SlimJim + Beast already verified before potentially losing my own remote-control path.

### 2.2 Procedure

#### Pre-flight (all 3 nodes; do not proceed if any check fails)

```bash
echo '---SlimJim---'
ssh slimjim 'uname -r; sudo -n true && echo SUDO_OK; systemctl is-active mosquitto.service; df -h /boot | tail -1'
echo '---Beast---'
ssh beast 'uname -r; sudo -n true && echo SUDO_OK; systemctl show -p MainPID -p ActiveState atlas-agent.service; df -h /boot | tail -1'
echo '---CK---'
ssh ciscokid 'uname -r; sudo -n true && echo SUDO_OK; systemctl is-active mercury-scanner.service homelab-mcp.service; df -h /boot | tail -1'
echo '---substrate anchors---'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}}"'
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}}"'
```

Expected: all kernels at 5.15.0-176 / 6.8.0-110; all sudo OK; all named services active; /boot has >100MB free per node (kernel images are ~50MB each).

**STOP if /boot is <100MB free anywhere** -- kernel install will fail. Run `apt-get autoremove --purge` first to free old kernels.

#### Stage A -- SlimJim (lowest risk; first)

```bash
ssh slimjim 'sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade 2>&1 | tail -20'
```
Expected: 41 packages upgraded; new kernel 6.8.0-111 installed alongside 110.

```bash
ssh slimjim 'sudo apt-get autoremove -y --purge 2>&1 | tail -5'
```
Remove obsolete kernel packages.

```bash
ssh slimjim 'echo PRE_REBOOT; uname -r; ls /boot/vmlinuz-*' && \
  ssh slimjim 'sudo systemctl reboot' && \
  echo 'reboot issued; waiting 90s for SlimJim to come back...' && \
  sleep 90 && \
  for i in 1 2 3 4 5; do \
    ssh -o ConnectTimeout=5 -o BatchMode=yes slimjim 'echo POST_REBOOT_OK; uname -r; systemctl is-active mosquitto.service' 2>&1 && break || (echo "attempt $i failed; sleeping 30..."; sleep 30); \
  done
```
Expected: POST_REBOOT_OK; uname-r `6.8.0-111-generic`; mosquitto active.

**STOP cycle if SlimJim fails to come back within ~5min total.** Do not proceed to Beast.

#### Stage B -- Beast (atlas-agent host; maintenance-window flip)

```bash
ssh beast 'sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade 2>&1 | tail -20'
```
Expected: 45 packages upgraded; new kernel 5.15.0-177 installed alongside 176; deadsnakes PPA fetch warning is COSMETIC (already verified PPA scope at preflight).

```bash
ssh beast 'sudo apt-get autoremove -y --purge 2>&1 | tail -5'
```

**Maintenance-window flip:**
```bash
ssh beast 'sudo systemctl stop atlas-agent.service && systemctl is-active atlas-agent.service'
```
Expected: `inactive` (or `failed` is acceptable since stop is intentional).

This is the planned interruption: atlas-agent observation pauses for the duration of the reboot. Document via journal:
```bash
ssh beast 'logger -t paco_patch_cycle1 "atlas-agent.service stopped intentionally for kernel patch reboot; expect 60-120s production observation gap"'
```

```bash
ssh beast 'echo PRE_REBOOT; uname -r; ls /boot/vmlinuz-*' && \
  ssh beast 'sudo systemctl reboot' && \
  echo 'reboot issued; waiting 120s for Beast to come back (substrate containers + atlas-mcp need to start)...' && \
  sleep 120 && \
  for i in 1 2 3 4 5; do \
    ssh -o ConnectTimeout=5 -o BatchMode=yes beast 'echo POST_REBOOT_OK; uname -r; systemctl is-active atlas-mcp.service atlas-agent.service docker.service' 2>&1 && break || (echo "attempt $i failed; sleeping 30..."; sleep 30); \
  done
```

Expected post-reboot: uname-r `5.15.0-177-generic`; docker active; atlas-mcp active; atlas-agent active (auto-started via WantedBy=multi-user.target after Requires=atlas-mcp.service satisfied).

**Verify substrate containers came up:**
```bash
ssh beast 'docker ps --format "{{.Names}} {{.Status}}" | grep -E "control-postgres-beast|control-garage-beast"'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
```
Expected: both containers running with NEW StartedAt (post-reboot); restart count may be 0 (fresh start) or non-zero (depends on docker restart policy).

**Verify atlas-agent producing observations again:**
```bash
ssh beast 'systemctl show -p MainPID -p NRestarts -p ActiveEnterTimestamp atlas-agent.service'
ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT count(*) FROM atlas.tasks WHERE created_at > now() - interval '\''3 minutes'\'';"'
```
Expected: atlas-agent active with new MainPID; new ActiveEnterTimestamp post-reboot; atlas.tasks count > 0 (5min cadence kicks in within ~60s of agent start; 3-min window catches at least vitals tick).

**STOP cycle if Beast atlas-agent fails to come back active OR fails to write atlas.tasks within 5 min post-reboot.** Do not proceed to CK; investigate.

#### Stage C -- CK (orchestrator; LAST)

```bash
ssh ciscokid 'sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade 2>&1 | tail -20'
```
Expected: 30 packages upgraded; new kernel 5.15.0-177 installed.

```bash
ssh ciscokid 'sudo apt-get autoremove -y --purge 2>&1 | tail -5'
```

**Pre-reboot warning:** CK runs homelab-mcp.service (Paco's tool path), nginx, mercury-scanner. CK reboot will interrupt all. Plan: issue reboot, wait ~120s, reconnect.

```bash
ssh ciscokid 'echo PRE_REBOOT; uname -r; ls /boot/vmlinuz-*' && \
  ssh ciscokid 'sudo systemctl reboot' && \
  echo 'CK reboot issued; PD waits 120s; my MCP path will reconnect on its own when CK comes back...' && \
  sleep 120 && \
  for i in 1 2 3 4 5; do \
    ssh -o ConnectTimeout=5 -o BatchMode=yes ciscokid 'echo POST_REBOOT_OK; uname -r; systemctl is-active mercury-scanner.service homelab-mcp.service nginx.service' 2>&1 && break || (echo "attempt $i failed; sleeping 30..."; sleep 30); \
  done
```

Expected post-reboot: uname-r `5.15.0-177-generic`; mercury-scanner + homelab-mcp + nginx all active.

**Verify mercury MainPID changed (proof of reboot)** + atlas observation continuing on Beast:
```bash
ssh ciscokid 'systemctl show -p MainPID -p ActiveEnterTimestamp mercury-scanner.service'
ssh beast 'systemctl show -p MainPID -p NRestarts -p ActiveEnterTimestamp atlas-agent.service'
ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT count(*) FROM atlas.tasks WHERE created_at > now() - interval '\''2 minutes'\'';"'
```
Expected: mercury new MainPID + new timestamp; atlas-agent UNCHANGED MainPID from Stage B post-reboot (CK reboot does NOT impact atlas-agent on Beast); atlas.tasks count > 0 in 2-min window (vitals fired since CK came back).

#### Standing Gates POST (canon SGs; document new baseline)

```bash
echo '---canon SG2 postgres NEW anchor (Beast rebooted)---'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
echo '---canon SG3 garage NEW anchor (Beast rebooted)---'
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
echo '---canon SG4 atlas-mcp NEW MainPID (Beast rebooted)---'
ssh beast 'systemctl show -p MainPID -p ActiveState atlas-mcp.service'
echo '---canon SG5 atlas-agent NEW MainPID (Beast rebooted; SG5 invariant: bounded restart acceptable)---'
ssh beast 'systemctl show -p MainPID -p NRestarts -p ActiveState -p UnitFileState atlas-agent.service'
echo '---canon SG6 mercury-scanner NEW MainPID (CK rebooted)---'
ssh ciscokid 'systemctl show -p MainPID -p ActiveState mercury-scanner.service'
```

New Standing Gates baseline established post-cycle. Phase 9-onward SG5 invariant ("MainPID stable NRestarts within tolerance") explicitly accepts +1 restart per planned reboot. Document the new MainPID values for next cycle's PRE checks.

#### Pre-commit secrets-scan + commit + push

```bash
cd /home/jes/control-plane && \
  grep -niE 'adminpass|api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+|password.{0,3}=' docs/paco_review_homelab_patch_cycle1_cve_2026_31431.md | head -10 || echo 'tightened: clean'
```

If clean -> commit + push.

#### Write `docs/paco_review_homelab_patch_cycle1_cve_2026_31431.md`

Follow Phase 9 review structure. Sections:
- 0: Verified-live (PRE + POST per node)
- 1: TL;DR (3 nodes patched; new kernel + reboots; atlas observation gap = X seconds; Standing Gates new baseline)
- 2: Per-node procedure walk-through (Stage A SlimJim + Stage B Beast + Stage C CK)
- 3: Acceptance per stage
- 4: Standing Gates new baseline (post-Cycle 1)
- 5: atlas-agent observation gap quantified (PD captures via `SELECT max(created_at) FROM atlas.tasks` before-and-after each reboot)
- 6: Asks for Paco (close-confirm + Cycle 2 GO Goliath OR Cycle 3 GO KaliPi/Pi3 OR pause)

#### Notification line in `docs/handoff_pd_to_paco.md`

> Paco, PD finished homelab patch cycle 1. SlimJim + Beast + CK all kernels patched (6.8.0-110->111; 5.15.0-176->177); all 3 nodes rebooted clean; atlas-agent observation gap = X seconds during Beast reboot; Standing Gates new baseline documented; control-plane HEAD `<hash>`. Review: `docs/paco_review_homelab_patch_cycle1_cve_2026_31431.md`. Check handoff.

## 3. Acceptance criteria (Cycle 1)

1. SlimJim: kernel `6.8.0-111-generic` running post-reboot; mosquitto active.
2. Beast: kernel `5.15.0-177-generic` running post-reboot; atlas-mcp + atlas-agent + docker all active; substrate containers running with new StartedAt baseline; atlas.tasks count > 0 in 5-min window post-agent-restart.
3. CK: kernel `5.15.0-177-generic` running post-reboot; mercury-scanner + homelab-mcp + nginx all active.
4. Standing Gates new baseline documented; SG5 invariant honored (NRestarts increment +1 acceptable per planned reboot per node).
5. atlas-agent observation gap during Beast reboot quantified and documented (expected: 90-180 seconds).
6. Pre-commit secrets-scan BOTH layers clean on review file.
7. NO services other than the 3 patched nodes' services touched.

## 4. Trigger from CEO to PD (Cowork prompt)

```
You are PD (Cowork) for Santigrey Enterprises. Paco (COO) has dispatched homelab patch cycle 1 (CVE-2026-31431; SlimJim + Beast + CK Ubuntu kernel patches).

Repos:
- santigrey/control-plane at /home/jes/control-plane on CK (HEAD b8e66e8 or later). Read directive + write paco_review here.

Read in order:
1. /home/jes/control-plane/docs/paco_directive_homelab_patch_cycle1_cve_2026_31431.md (your authority)
2. /home/jes/control-plane/docs/feedback_paco_pre_directive_verification.md (P6 standing rules through #36; SRs through #7)
3. /home/jes/control-plane/docs/paco_response_atlas_v0_1_phase9_close_confirm.md (atlas-agent SG5 invariant context)

Execute Stages A -> B -> C per directive section 2.2. One stage at a time; verify before next. CK is LAST (Paco's MCP path runs through CK).

If any stage fails: STOP, write paco_request_homelab_patch_cycle1_<topic>.md, do not proceed.

Out of scope this cycle: Goliath, KaliPi, Pi3.

Begin with Pre-flight per directive section 2.2.
```

-- Paco
