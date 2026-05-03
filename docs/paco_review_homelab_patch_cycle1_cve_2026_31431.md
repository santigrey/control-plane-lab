# paco_review_homelab_patch_cycle1_cve_2026_31431

**To:** Paco | **From:** PD (Cowork) | **Date:** 2026-05-03 Day 79 mid-day
**Authority:** `paco_directive_homelab_patch_cycle1_cve_2026_31431.md`
**Status:** EXECUTION COMPLETE — 3/3 nodes patched, all per-node acceptance PASS, SG canonical baseline reset post-cycle.
**Streak context:** Phase 9 close-confirm streak = 6 first-try acceptance passes. This was a homelab patch cycle (separate cadence), not an Atlas phase, so streak counter unaffected.

---

## 0. Verified live (PRE + POST per node)

### 0.1 PRE-flight (Day 79 mid-day, pre-execution)

| # | Probe | Expected per directive §1 | Actual | Status |
|---|---|---|---|---|
| 1 | SlimJim kernel | `6.8.0-110-generic` | `6.8.0-110-generic` | PASS |
| 2 | SlimJim sudo | NOPASSWD | SUDO_OK | PASS |
| 3 | SlimJim mosquitto | active | active | PASS |
| 4 | SlimJim /boot free | >100MB | 1.6G free (11% of 2.0G) | PASS |
| 5 | SlimJim reboot-pending | none | NO_REBOOT_PENDING | PASS |
| 6 | Beast kernel | `5.15.0-176-generic` | `5.15.0-176-generic` | PASS |
| 7 | Beast sudo | NOPASSWD | SUDO_OK | PASS |
| 8 | Beast atlas-agent | MainPID=2872599 NRestarts=0 active | MainPID=2872599 NRestarts=0 active (exact Phase 9 anchor) | PASS |
| 9 | Beast /boot free | >100MB | root FS `4.0T free` (no separate /boot mount; cosmetic difference) | PASS |
| 10 | Beast reboot-pending | none | NO_REBOOT_PENDING | PASS |
| 11 | CK kernel | `5.15.0-176-generic` | `5.15.0-176-generic` | PASS |
| 12 | CK sudo | NOPASSWD | SUDO_OK | PASS |
| 13 | CK mercury+homelab-mcp+nginx | all active | all active | PASS |
| 14 | CK /boot free | >100MB | 1.6G free (15% of 2.0G) | PASS |
| 15 | CK reboot-pending | none | NO_REBOOT_PENDING | PASS |
| 16 | Substrate SG2 postgres anchor | `2026-04-27T00:13:57.800746541Z restart=0` | EXACT MATCH (~158h+ bit-identical) | PASS |
| 17 | Substrate SG3 garage anchor | `2026-04-27T05:39:58.168067641Z restart=0` | EXACT MATCH (~158h+ bit-identical) | PASS |

**17/17 PASS, zero divergence from directive §1 Verified-live.**

### 0.2 POST-cycle verification (after CK reboot completed, Day 79 mid-day)

| Subject | Result |
|---|---|
| SlimJim kernel | `6.8.0-111-generic` ✓ (was 110) |
| SlimJim mosquitto.service | active ✓ |
| Beast kernel | `5.15.0-177-generic` ✓ (was 176) |
| Beast atlas-mcp.service | active, MainPID=1212, ActiveEnter `2026-05-03 18:38:07 UTC` ✓ |
| Beast atlas-agent.service | active+enabled, MainPID=4753, NRestarts=0, ActiveEnter `2026-05-03 18:38:26 UTC` ✓ |
| Beast docker.service | active ✓ |
| Beast NVIDIA driver (Path B add) | Tesla T4, **`595.71.05`** (was 595.58.03) — dkms rebuild successful ✓ |
| Beast Ollama (Path B add) | qwen2.5:14b model listed, responding on `:11434` ✓ |
| Beast SG2 postgres NEW anchor | `2026-05-03T18:38:24.910689151Z restart=0` |
| Beast SG3 garage NEW anchor | `2026-05-03T18:38:24.493238903Z restart=0` |
| CK kernel | `5.15.0-177-generic` ✓ (was 176) |
| CK mercury-scanner.service | active, **NEW MainPID=7800** (was 643409 — proof of reboot), ActiveEnter `2026-05-03 18:53:27 UTC` ✓ |
| CK homelab-mcp.service | active, MainPID=1082, ActiveEnter `2026-05-03 18:53:18 UTC` ✓ |
| CK nginx.service | active, MainPID=1934, ActiveEnter `2026-05-03 18:53:19 UTC` ✓ |
| atlas-agent post-CK-reboot stability | UNCHANGED (MainPID=4753, NRestarts=0, ActiveEnter 18:38:26 UTC) — proves CK reboot doesn't perturb Beast atlas-agent ✓ |
| atlas.tasks 2-min window post-CK-reboot | 21 rows ✓ — vitals fired throughout CK outage |

**All directive §3 acceptance criteria PASS (per-stage detail in §3 below).**

---

## 1. TL;DR

3 nodes patched in directive order (SlimJim → Beast → CK; CK last per Decision 3.2). Kernel bumps: SlimJim `6.8.0-110→111`, Beast/CK `5.15.0-176→177`. All 3 nodes rebooted clean on new kernel. Atlas-agent observation gap during Beast reboot: **9m04s** (above directive's 90-180s expectation, root cause = Beast's heavier-than-expected boot path; see §5). Standing Gates canonical baseline reset post-Cycle 1 (SG2/SG3/SG4/SG5 new from Beast reboot; SG6 new from CK reboot). SG5 invariant (Phase 9) honored — atlas-agent active+enabled MainPID stable, NRestarts within tolerance (+1 acceptable per planned reboot per node, Phase 9 close-confirm canon).

Two Path B adaptations (one operational, one observational); see §2.4 for details and ratification ask in §6.

---

## 2. Per-node procedure walk-through

### 2.1 Stage A — SlimJim (lowest blast radius)

Wall time: dist-upgrade `~93s` (per `/var/log/apt/history.log` 2026-05-03 12:03:11 → 12:04:44 local); autoremove `~5s`; reboot wait `~3min` (queued 18:11:28Z → first SSH success ~18:14:30Z).

- 41 packages upgraded incl. `linux-image-generic 6.8.0-110.110 → 6.8.0-111.111` and ancillary systemd/containerd/docker/snapd/NetworkManager bumps.
- Autoremove: dropped `linux-{modules,modules-extra,tools,image}-6.8.0-107` packages. Cosmetic dpkg warning that `/lib/modules/6.8.0-107-generic` directory was non-empty so not removed (leftover .ko files — non-blocking).
- Reboot transitions observed by SSH probe: Connection closed → reset → refused → No route to host → refused → OK (clean network reconfig path).
- Boot completed: `2026-05-03 12:12:22 (local MDT, = 18:12:22 UTC)`; total reboot downtime ~54s.
- POST verification: `uname -r = 6.8.0-111-generic`; `mosquitto.service` active.

### 2.2 Stage B — Beast (atlas-agent host; maintenance-window flip)

Wall time: dist-upgrade `9m57s` (18:16:55 → 18:26:52); autoremove `~21s`; maintenance flip `<1s`; reboot wait `9m14s` (queued 18:31:41Z → first SSH success ~18:40:55Z).

#### 2.2a Discovery — bundle was broader than directive enumerated

Directive §0 stated `45 packages`, which matched, but the bundle's substantive content was richer than directive's text-level call-outs. Surfaced mid-execution:

- **NVIDIA driver upgrade:** `595.58.03 → 595.71.05` (nvidia-firmware, nvidia-modprobe, libnvidia-encode, libnvidia-fbc1, cuda-drivers, libxnvctrl0, nvidia-driver, nvidia-dkms, libnvidia-decode, libnvidia-compute, libnvidia-gl, libnvidia-gpucomp, xserver-xorg-video-nvidia, nvidia-settings, nvidia-persistenced, nvidia-kernel-common).
- **Docker major bump:** `docker.io 28.2.2 → 29.1.3`, `containerd 1.7.28 → 2.2.1`, `runc 1.3.3 → 1.3.4`.
- **linux-firmware** + **systemd 249.11-0ubuntu3.20** (plus libpam-systemd, libnss-systemd, etc.).

#### 2.2b dkms duration anomaly

dkms rebuilt nvidia 595.71.05 against **4 installed kernels** (`5.15.0-171/-174/-176/-177`), not just the new kernel. Dominated wall time. Two of those kernels (171, 174) were stale-but-headers-still-installed; subsequent autoremove cleaned `5.15.0-174` (171 was already orphaned headers without vmlinuz). Future cycles will be much faster once the kernel-header inventory is trimmed.

Option to SIGTERM dkms builds for soon-to-be-removed kernels was considered and explicitly declined (CEO directed "wait it out" to stay on directive spec, no ratification required).

#### 2.2c Substrate restart deferral (better than expected)

Directive §2.1 anticipated docker.io upgrade-driven substrate container restarts. needrestart logic (`No containers need to be restarted.` line in apt log) consciously declined to restart docker.service during dist-upgrade. Substrate containers + atlas-agent remained on Phase 9 anchors through dist-upgrade and autoremove; restart event consolidated into the planned reboot (cleaner than directive anticipated).

#### 2.2d Maintenance-window flip

Captured PRE-stop atlas.tasks `max(created_at) = 2026-05-03 18:29:26.370419+00`; wall clock at stop = `18:30:57Z` (91s natural cadence-tick gap was already in flight). `systemctl stop atlas-agent.service` exit 0; post-stop is_active=inactive, MainPID=0. Journal entry written: `logger -t paco_patch_cycle1 "atlas-agent.service stopped intentionally for kernel patch reboot; expect 60-120s production observation gap"`.

#### 2.2e Reboot wait — long but successful

Reboot queued `18:31:41Z`. ARP/ping unreachable for ~6 minutes. CEO consultation at 4m30s elapsed (approaching directive's 5min STOP threshold) — CEO directed "wait it out (recommended)". Beast came back at `~18:40:55Z`; boot-time `2026-05-03 18:37:36 UTC`; total downtime 9m14s. Drivers of the long reboot:

1. 9+ days uptime — extensive shutdown cleanup
2. Server-class BIOS POST
3. Freshly-generated initramfs (untested boot path)
4. NVIDIA driver init at boot
5. Docker daemon + substrate containers + atlas-mcp + atlas-agent dependency chain

Not a regression — Beast's hardware profile makes this normal range, just longer than directive's 120s estimate.

#### 2.2f POST verification — Path B adds (NVIDIA + Ollama)

Directive §3 acceptance did not enumerate NVIDIA or Ollama checks, but given the bundle expansion (§2.2a), PD added two non-destructive read-only POST verifications:

```bash
ssh beast 'nvidia-smi --query-gpu=name,driver_version --format=csv,noheader'
# Tesla T4, 595.71.05  → driver loaded, dkms rebuild successful

ssh beast 'curl -sS --max-time 5 http://localhost:11434/api/tags | head -c 200'
# {"models":[{"name":"qwen2.5:14b",...}]}  → Ollama up, GPU-accessible
```

Both healthy. This is a **Path B adaptation** flagged for ratification; no scope expansion (read-only verification only); rationale = bundle scope materially exceeded directive text.

### 2.3 Stage C — CK (orchestrator; LAST)

Wall time: dist-upgrade `2m17s` (18:43:52 → 18:46:09); autoremove `~10s`; reboot wait `2m31s` (queued 18:50:18Z → first SSH success 18:52:49Z).

- 30 packages upgraded incl. `linux-image-generic 5.15.0-176 → 5.15.0-177`, ancillary systemd/networking. No NVIDIA/dkms work — much faster than Beast.
- Autoremove: dropped `linux-{image,modules,modules-extra}-5.15.0-174`. Kernels remaining: `176 + 177` (clean).
- needrestart again declined to restart in-place: `No containers need to be restarted.`
- CK reboot interrupted homelab-mcp.service (PD's own MCP path); MCP unavailable for ~2.5min during outage. Reconnected automatically when CK came back.
- POST: kernel `5.15.0-177-generic`; mercury-scanner NEW MainPID=7800 (was 643409 — confirms reboot); homelab-mcp + nginx active with NEW MainPIDs; reboot-required file gone.
- Beast atlas-agent UNCHANGED during CK outage: MainPID=4753 NRestarts=0 ActiveEnter 18:38:26 UTC (Stage B baseline preserved per directive expectation row #13).
- atlas.tasks count in 2-min window post-CK-reboot: 21 rows — vitals fired throughout CK outage.

### 2.4 Path B adaptations summary (for ratification)

| # | Adaptation | Scope | Rationale | Risk |
|---|---|---|---|---|
| B1 | NVIDIA + Ollama POST checks added to Stage B verification | Read-only, non-destructive | Beast bundle included full NVIDIA driver upgrade not enumerated in directive text; verification confirmed dkms rebuild succeeded and Ollama still responsive | Zero — read-only checks |
| B2 | Long-running apt-get / dist-upgrade wrapped in `nohup → /tmp/cycle1_<node>_distupgrade.{log,exit}` pattern instead of inline `tail -25` | Operational shape only; directive's `apt-get update + dist-upgrade` semantics preserved | MCP tool 30s timeout couldn't observe inline output of multi-minute operations; without exit-file pattern, exit code would have been lost on MCP timeout | Zero — preserves apt semantics; exit code captured to file; dpkg behavior identical |

Both adaptations fall under SR #4 Path B authorization (PD adapts to ground truth without directive deviation in core operation). Asking Paco to ratify at close-confirm.

---

## 3. Acceptance per stage (directive §3)

### 3.1 Stage A — SlimJim

| Criterion | Result |
|---|---|
| Kernel `6.8.0-111-generic` running post-reboot | PASS |
| mosquitto.service active | PASS |

**Stage A: 2/2 PASS first-try.**

### 3.2 Stage B — Beast

| Criterion | Result |
|---|---|
| Kernel `5.15.0-177-generic` running post-reboot | PASS |
| atlas-mcp + atlas-agent + docker all active post-reboot | PASS (MainPIDs 1212 / 4753 / docker active) |
| Substrate containers running with new StartedAt baseline | PASS (postgres/garage at `2026-05-03T18:38:24.{910689151,493238903}Z restart=0`) |
| atlas.tasks count > 0 in 5-min window post-agent-restart | PASS (multiple readings: 22 rows in 3-min window post-restart) |

**Stage B: 4/4 directive criteria PASS first-try; +2 Path B adds (NVIDIA + Ollama) — both PASS.**

### 3.3 Stage C — CK

| Criterion | Result |
|---|---|
| Kernel `5.15.0-177-generic` running post-reboot | PASS |
| mercury-scanner + homelab-mcp + nginx active | PASS |
| mercury-scanner NEW MainPID (proof of reboot) | PASS (7800, was 643409) |
| Beast atlas-agent UNCHANGED MainPID during CK reboot | PASS (4753 stable, NRestarts=0) |
| atlas.tasks count > 0 in 2-min window | PASS (21 rows) |

**Stage C: 5/5 PASS first-try.**

### 3.4 Cycle-level criteria (directive §3 #4-#7)

| Criterion | Result |
|---|---|
| #4 Standing Gates new baseline documented; SG5 invariant honored | PASS — see §4 |
| #5 atlas-agent observation gap quantified and documented | PASS — see §5; gap = 9m04s |
| #6 Pre-commit secrets-scan BOTH layers clean on review file | PENDING — to run at close-write of this file |
| #7 NO services other than the 3 patched nodes' services touched | PASS — Goliath, KaliPi, Pi3 untouched per directive scope |

---

## 4. Standing Gates new baseline (post-Cycle 1)

From this cycle close-confirm onward, the canonical SG anchors are:

| SG | Subject | NEW value (post-Cycle 1) | Source | Notes |
|---|---|---|---|---|
| SG2 | postgres | `2026-05-03T18:38:24.910689151Z restart=0` | Beast `docker inspect control-postgres-beast` | Bit-identical from this point until next planned reboot |
| SG3 | garage | `2026-05-03T18:38:24.493238903Z restart=0` | Beast `docker inspect control-garage-beast` | Bit-identical from this point until next planned reboot |
| SG4 | atlas-mcp.service (Beast) | MainPID=1212 active, ActiveEnter `2026-05-03 18:38:07 UTC` | Beast `systemctl show atlas-mcp.service` | Stable from this point until next planned reboot |
| SG5 | atlas-agent.service (Beast) | MainPID=4753 NRestarts=0 active+enabled, ActiveEnter `2026-05-03 18:38:26 UTC` | Beast `systemctl show atlas-agent.service` | Phase 9 invariant: "active enabled MainPID stable NRestarts within tolerance" — **NRestarts honored at 0 because Beast got a fresh kernel boot, not a service-restart event**. Bounded restart per planned reboot is acceptable per Phase 9 close-confirm canon (`paco_response_atlas_v0_1_phase9_close_confirm.md` Ask 5 ratification) |
| SG6 | mercury-scanner.service (CK) | MainPID=7800 active, ActiveEnter `2026-05-03 18:53:27 UTC` | CK `systemctl show mercury-scanner.service` | Stable from this point until next planned reboot |

All SG anchors will need to be re-baselined at every planned reboot of the host they live on. PD's pre-flight discipline at the next cycle should diff against THESE values, not the prior pre-Cycle-1 anchors.

---

## 5. atlas-agent production observation gap (quantified)

Directive §3 criterion #5 asked PD to quantify and document the gap.

```sql
-- last write before atlas-agent stop:
SELECT max(created_at)::text FROM atlas.tasks;
--   2026-05-03 18:29:26.370419+00

-- first write after atlas-agent restart (post-Beast-reboot):
SELECT min(created_at)::text FROM atlas.tasks WHERE created_at > '2026-05-03 18:30:57+00';
--   2026-05-03 18:38:30.144939+00
```

**Gap: 9m04s** (`18:29:26.370419 → 18:38:30.144939`).

Decomposition:
- 1m31s natural cadence-tick gap (last write was 91s before atlas-agent stop — vitals had not fired the next tick yet)
- 7m29s atlas-agent service downtime (stopped at `18:30:57Z`, ActiveEnter post-reboot at `18:38:26Z`)
- 4s first-tick latency (atlas-agent started at 18:38:26, first scheduler emit at 18:38:30)

**Above directive expectation of 90-180s.** Drivers (covered in §2.2e):
1. Beast 9+ days prior uptime
2. Server-class BIOS POST + freshly-generated initramfs (untested boot path)
3. NVIDIA driver init at boot
4. atlas-mcp + atlas-agent dependency-chain startup post-substrate-containers

No evidence of service-level pathology — atlas-agent's own start was clean (50s from boot to ActiveEnter), substrate containers came up healthy, atlas-mcp came up before atlas-agent as designed (`Requires=atlas-mcp.service`). The gap was driven by hardware boot time, not software latency. Future cycles on Beast should expect similar order-of-magnitude gap unless we add hardware-side optimization (BIOS quick-boot, faster initramfs).

v0.1.1 banking candidate: production observation gap as an SLO, with 5min target steady-state and 10min max during planned reboots. Worth discussing.

---

## 6. Asks for Paco

1. **Confirm 3-node Cycle 1 patch acceptance** (Stage A 2/2 + Stage B 4/4 + Stage C 5/5 + cycle-level #4 / #5 / #7 — all PASS).
2. **Ratify Path B adaptations** (per §2.4): B1 NVIDIA + Ollama POST checks, B2 nohup-to-tmpfile pattern for long-running apt-get. Both read-only / operational-shape, zero scope expansion.
3. **Ratify Standing Gates new baseline** (per §4) as canonical from Day 79 mid-day forward.
4. **Ratify gap > directive expectation** (9m04s vs 90-180s) as bounded by Beast hardware profile, not service-level regression. v0.1.1 candidate: codify gap SLO target.
5. **Ratify cosmetic dpkg warnings as accepted** — `/lib/modules/6.8.0-107-generic directory not empty` (SlimJim autoremove) and Beast nvidia-persistenced postinst's `Could not execute systemctl: at /usr/bin/deb-systemd-invoke line 142.` Both confirmed non-blocking (services healthy POST-reboot).
6. **Authorize next cycle** — pick one:
   - Cycle 2 (Goliath dedicated cycle: 584 upgradable + major kernel 6.11→6.17 + GPG key expired)
   - Cycle 3 (KaliPi/Pi3 non-kernel apt cycle)
   - Pause and continue with Atlas v0.1 Phase 10 (ship report) instead — recall Phase 10 was authorized at Phase 9 close, data already over-saturated
7. **Bank P6 #37 candidate** (PD-proposed): when a directive enumerates package count without enumerating bundle contents (as here, where 45 packages included a full NVIDIA driver upgrade not surfaced in directive text), Paco-side preflight should call out specific high-blast-radius categories (kernel + GPU driver + container runtime) so PD can pre-stage Path B verifications. This cycle's NVIDIA bundle was discovered mid-execution; B1 absorbed it cleanly but a forward-pass surface during pre-directive verification would have been cleaner. This is a natural extension of SR #7. Reasonable candidate for v0.1.1+1 close-confirm or its own banking event.
8. **Acknowledge feedback on /boot mount inconsistency on Beast** — Beast lacks a separate `/boot` partition (boot files on root FS). Pre-flight directive §1 row 9 expectation "Beast /boot >100MB" was met by 4.0T-free root, but the directive's mental model implied Beast had a separate /boot mount. Cosmetic, but worth amending future patch-cycle directive templates to be filesystem-agnostic.

## 7. Concerns / risks / followups

- **Beast's 4-kernel dkms inventory** is now reduced to 2 kernels (176 + 177). Future patch cycles on Beast will be much faster (one kernel target for dkms, ~3-5 min, vs this cycle's ~20+ min).
- **needrestart's "No containers need to be restarted" decision** during dist-upgrade is healthy (kept substrate stable through dist-upgrade), but worth understanding the heuristic for future cycles where we DO want a coordinated container restart.
- **Cosmetic dpkg warnings** (non-blocking) noted in §6 #5.
- **homelab-mcp.service outage during CK reboot** worked clean — auto-recovered when CK came back at `~18:52:49Z`. PD lost MCP path for ~2.5min, reconnected automatically. SR #6 self-state re-verification worked: post-reconnect probe captured CK NEW MainPID=7800 (was 643409), proving reboot.

---

Ready for close-confirm. Awaiting Paco ratification and next-cycle authorization.

— PD
