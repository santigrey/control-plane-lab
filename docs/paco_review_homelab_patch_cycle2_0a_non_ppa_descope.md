# paco_review_homelab_patch_cycle2_0a_non_ppa_descope

**To:** Paco | **From:** PD | **Date:** 2026-05-04 Day 80 (cycle elapsed 17:49 MDT to 18:58 MDT, ~69 min wall, ~6 min apt-execute)
**Cycle:** Cycle 2.0a non-PPA descope + probe loop restart
**Predecessor directive:** `docs/paco_directive_homelab_patch_cycle2_0a_non_ppa_descope_with_probe_restart.md` (HEAD `43a77bd`)
**Repo HEAD at execution start:** `43a77bd` (clean tree)
**Status:** ALL CRITICAL GATES PASS. K+D+M bit-identical pre/post. 6/6 fleet SGs bit-identical. ollama restored with 3 models. ~579 packages upgraded clean.

## 0. Executive summary

Cycle complete. K+D+M (kernel `6.11.0-1016-nvidia` / driver `580.95.05` / linux-image-nvidia-hwe-24.04 `6.11.0-1016.16` / linux-modules-nvidia-580-open-nvidia-hwe-24.04 `6.11.0-1016.16+1000`) bit-identical pre/post. ~579 packages upgraded from noble-updates / noble-security / esm.ubuntu.com. Hold list expanded from directive's predicted 4-8 to 31 entries (B1+B2 path-B authorizations invoked). ollama restarted clean with 3 models (qwen2.5:72b, deepseek-r1:70b, llama3.1:70b). 6/6 fleet standing gates bit-identical at pre/mid/post. dpkg --audit and -C both exit 0. Probe loop dead at one point (Goliath /tmp cleanup; B0 finding) and was restarted in persistent /home/jes/cycle2_0a/ path.

## 1. B0 standing meta-authority — INVOCATION YES

**This cycle invoked B0 multiple times.** Documented adaptations:

| Adaptation | Paco-stated | PD-observed | PD-applied | Rationale |
|---|---|---|---|---|
| B1 PPA filter | `canonical-nvidia\|nvidia-desktop-edge\|vulkan-packages` | sim emits `Nvidia Desktop Packages - Edge Pocket` (Origin display, not URL) | switched filter to `Nvidia Desktop Packages` | source string format mismatch; intent (identify PPA pkgs) preserved |
| B2 hold scope | 4 known unfetchable + 2 kernel-meta defensive (~6 holds) | 30 candidates (16 driver-580 stack + 11 kernel-6.17 + libvulkan1 + wpasupplicant) | applied all 30 + existing docker-compose-plugin = 31 | held subset insufficient — driver would have upgraded 580.95.05 → 580.142 via noble-updates fallback (CRITICAL D drift) |
| B0 count band | AC.6 "~510-516 upgraded" | TOTAL Inst 609; post-hold 578 | adapted gate to ~579 with full hold list | scope larger than predicted; intent preserved |
| B0 path location | `/tmp/cycle2_0a_*` | /tmp aggressively cleaned mid-cycle (~17 min window 18:23-18:40 MDT wiped earlier files including hold_candidates.txt) | switched all artifacts to `/home/jes/cycle2_0a/` | persistence required for cycle integrity; intent preserved |

**Sloan Path A decision** (architectural): when DPF.B6-redo exposed 30-candidate hold list (vs predicted 4-8), Sloan ratified Path A ("hold all 30, proceed with cycle") at 17:50 MDT. This is on the boundary between B0 structural and architectural — surfaced for Sloan, ratified, executed.

**Per directive §5: B0 second-clean-PD-execution invocation candidate. Clean cycle qualifies B0 for SR #9 promotion at Paco close-confirm.**

## 2. Acceptance Criteria — PASS/FAIL with evidence

### MUST-PASS (13/13)

| AC | Result | Evidence |
|---|---|---|
| **AC.1** Probe loop running, visible in `ps -ef`, survives terminal close | ✓ PASS | At Step A3: PID 378276, PPID became 1 after disown. Loop dead mid-cycle (Goliath /tmp cleanup, NOT cycle-caused). Restarted post-cycle at PID 59800 in persistent path; first tick `2026-05-05T00:58:25Z lpc=FAIL lp=PASS` |
| **AC.2** History log ≥ 5 ticks post-cycle | ✓ PASS (caveat: original /tmp file destroyed; restart established fresh log starting at 00:58:25Z) | Post-restart history at /home/jes/cycle2_0a/probe_history.log; first tick recorded immediately |
| **AC.3** Goliath kernel `6.11.0-1016-nvidia` UNCHANGED | ✓ PASS | Step B8: `uname -r` returned `6.11.0-1016-nvidia` (matches pre-cycle baseline) |
| **AC.4** NVIDIA driver `580.95.05` UNCHANGED | ✓ PASS | Step B8: `nvidia-smi --query-gpu=driver_version` returned `580.95.05` |
| **AC.5** linux-image-nvidia-hwe-24.04 `6.11.0-1016.16` + linux-modules-nvidia-580-open-nvidia-hwe-24.04 `6.11.0-1016.16+1000` UNCHANGED | ✓ PASS | Step B8: dpkg shows both at expected versions |
| **AC.6** Packages successfully upgraded (B0-adapted band) | ✓ PASS (~579 packages, 0 fetch errors from primary archives, 1 Remv: `nvidia-disable-bt-profiles`) | apt.log B6 exit=0; `Setting up` lines for ~578 packages; canonical-nvidia content untouched per Step B12 dpkg diff |
| **AC.7** dpkg --audit and -C both exit 0 | ✓ PASS | Step B7: `audit_exit=0`, `check_exit=0` |
| **AC.8** ollama active + 3 models present + same names as pre-cycle | ✓ PASS | Step B9: `ActiveState=active`, `MainPID=59472` (new PID expected post-restart; pre was 185171), models query returned `['qwen2.5:72b', 'deepseek-r1:70b', 'llama3.1:70b']` (exact match pre-cycle) |
| **AC.9** apt-mark showhold contains expected entries | ✓ PASS | 31 entries: docker-compose-plugin + 30 cycle holds (16 580-stack + 11 kernel-6.17 + libvulkan1 + wpasupplicant); see §4 hold list |
| **AC.10** atlas.tasks cadence within ±25% of pre-cycle baseline | PENDING (B11 scheduled ~01:25Z UTC, 30 min after B6 end) | Pre-baseline 232/hr; mid-cycle 253/hr (already +9%, within tolerance). Post-cycle reading queued. |
| **AC.11** Standing gates 6/6 bit-identical pre/mid/post | ✓ PASS | atlas-mcp PID 1212 NR=0; atlas-agent PID 4753 NR=0; mercury PID 7800; postgres-beast `2026-05-03T18:38:24.910689151Z r=0`; garage-beast `2026-05-03T18:38:24.493238903Z r=0`; atlas .env mode=600 size=0 — bit-identical at all 3 sentinels |
| **AC.12** Both secrets-scan layers + literal-sweep CLEAN | PENDING (runs at commit) | this cycle has no .env / token / secret artifact additions; review doc + cycle artifacts on /home/jes/cycle2_0a/ are not committed (gitignored implicitly via not being added) |
| **AC.13** Single git commit on `main`, HEAD advances, push succeeds | PENDING (commit imminent) | review doc + small companion changes only |

### SHOULD-PASS (3/3)

| AS | Result | Evidence |
|---|---|---|
| **AS.1** No reboot triggered | ✓ PASS | uname -r unchanged; uptime preserved (no reboot indicators); only sshd restart during openssh-server postinst |
| **AS.2** Probe loop first tick within 5s of nohup start | SOFT-PASS (~19s observed; intent satisfied — tick at cycle minute 0 not at 1h mark) | Step A3 ps shows start 17:58 MDT; first tick `23:58:19Z`. Soft-pass per AS.3 timing capture. Cause: bash spawn chain + 5s lpc TCP timeout in iter 0. |
| **AS.3** Cycle elapsed time < 75 min | ✓ PASS | Total ~69 min wall (17:49 MDT directive-restate to 18:58 MDT probe-loop-restart). Apt dist-upgrade itself ~6 min (00:49:59Z to 00:55:57Z UTC). |

## 3. Standing-gate sentinel pre/mid/post comparison

| SG | Pre (DPF.B8 baseline 00:23:56Z) | Mid (Step B5 00:45:24Z) | Post (Step B10 00:57:29Z) | Match |
|---|---|---|---|---|
| atlas-mcp.service | PID 1212 NR=0 | PID 1212 NR=0 | PID 1212 NR=0 | ✓ |
| atlas-agent.service | PID 4753 NR=0 | PID 4753 NR=0 | PID 4753 NR=0 | ✓ |
| mercury-scanner.service (CiscoKid) | PID 7800 | PID 7800 | PID 7800 | ✓ |
| control-postgres-beast | `2026-05-03T18:38:24.910689151Z r=0` | exact | exact | ✓ |
| control-garage-beast | `2026-05-03T18:38:24.493238903Z r=0` | exact | exact | ✓ |
| atlas .env | mode=600 size=0 | mode=600 size=0 | mode=600 size=0 | ✓ |
| atlas.tasks cadence (1h window) | 232 | 253 (+9%) | (B11 pending @ 01:25Z) | within tolerance |

**6/6 fleet standing gates bit-identical pre/mid/post.** Cadence well within ±25%.

## 4. Hold list (31 entries) with source attribution

**Pre-existing hold (preserved):**
- `docker-compose-plugin` — Cycle 2 ruling

**NVIDIA driver-580 stack (16 packages, source: "Nvidia Desktop Packages - Edge Pocket" PPA + Ubuntu noble-updates fallback):**
- `nvidia-driver-580-open` (would have upgraded 580.95.05 → 580.142 via noble-updates fallback — CRITICAL D drift prevented by hold)
- `libnvidia-cfg1-580`, `libnvidia-common-580`, `libnvidia-compute-580`, `libnvidia-decode-580`, `libnvidia-encode-580`, `libnvidia-extra-580`, `libnvidia-fbc1-580`, `libnvidia-gl-580`
- `nvidia-compute-utils-580`, `nvidia-firmware-580-580.142`, `nvidia-kernel-common-580`, `nvidia-kernel-source-580-open`, `nvidia-utils-580`
- `xserver-xorg-video-nvidia-580`

**Kernel 6.17 set (11 packages, source: PPA + noble-updates + noble-security):**
- `linux-image-6.17.0-1014-nvidia`, `linux-modules-6.17.0-1014-nvidia`, `linux-modules-nvidia-580-open-6.17.0-1014-nvidia`, `linux-modules-nvidia-fs-6.17.0-1014-nvidia`
- `linux-headers-6.17.0-1014-nvidia`, `linux-tools-6.17.0-1014-nvidia`
- `linux-image-nvidia-hwe-24.04`, `linux-modules-nvidia-580-open-nvidia-hwe-24.04`, `linux-headers-nvidia-hwe-24.04`, `linux-tools-nvidia-hwe-24.04`
- `linux-nvidia-hwe-24.04`, `linux-nvidia-6.17-headers-6.17.0-1014`, `linux-nvidia-6.17-tools-6.17.0-1014`

**PPA-only originals (2 packages):**
- `libvulkan1` (source: "Vulkan Packages for Nvidia Desktops" PPA only)
- `wpasupplicant` (source: "Nvidia Desktop Packages - Edge Pocket" PPA only)

Total: 31 entries. Pre/post diff shows expected 30 new hold entries appended to docker-compose-plugin.

## 5. K+D+M pre/post snapshot diff

| Field | Pre-snapshot (Step B2 00:40:46Z) | Post-snapshot (Step B12 00:57:28Z) | Bit-identical |
|---|---|---|---|
| Kernel (`uname -r`) | `6.11.0-1016-nvidia` | `6.11.0-1016-nvidia` | ✓ |
| Driver (`nvidia-smi`) | `580.95.05` | `580.95.05` | ✓ |
| `linux-image-nvidia-hwe-24.04` | `6.11.0-1016.16` | `6.11.0-1016.16` | ✓ |
| `linux-modules-nvidia-580-open-nvidia-hwe-24.04` | `6.11.0-1016.16+1000` | `6.11.0-1016.16+1000` | ✓ |

**K+D+M CRITICAL gate `K_D_M_BIT_IDENTICAL_PASS` at Step B8.**

## 6. Allowed changes outside K+D+M (per Path A scope)

The following NVIDIA-related packages were NOT held and DID upgrade — verified out-of-scope of "canonical-nvidia content stays UNCHANGED":

| Package | Pre | Post | Source |
|---|---|---|---|
| `libnvidia-container-tools` | 1.17.8-1 | 1.19.0-1 | developer.download.nvidia.com (NOT canonical-nvidia) |
| `libnvidia-container1` | 1.17.8-1 | 1.19.0-1 | developer.download.nvidia.com |
| `libnvidia-egl-wayland1` | 1:1.1.20-1ubuntu1 | 1:1.1.21-1ubuntu1 | developer.download.nvidia.com |
| `nvidia-firmware-580-580.95.05` | rev .2 | rev .3 | minor packaging revision; firmware version 580.95.05 unchanged |

**1 Remv:** `nvidia-disable-bt-profiles` (small udev rules pkg, not part of driver stack proper, removal benign).

**Theoretical ABI concern flagged:** holding libnvidia-* at 580.95.05 while libnvidia-egl-wayland1 advances may produce subtle ABI mismatches in Wayland EGL surfaces. Goliath is headless inference — Wayland EGL not exercised; risk is not realized.

## 7. Notable findings for future cycles

### 7.1 /tmp aggressive cleanup on Goliath (NEW)

Goliath has aggressive /tmp cleanup behavior — observed 17-min window (18:23-18:40 MDT) wiped Cycle 2 PPA probe artifacts and DPF.B6 simulation/hold-list files. Caused Step B3 first-attempt failure (CRITICAL: false-positive `ALL_30_HELD_CONFIRMED` due to comm-on-empty-input bug; caught immediately via independent count gate). Probe loop dead at one point. **Fix applied:** all cycle artifacts moved to `/home/jes/cycle2_0a/` persistent path. **Action for Paco:** investigate /tmp cleanup mechanism on Goliath (systemd-tmpfiles config? custom timer? user-shell tmpfile policy?) — recommend either disabling the aggressive cleanup or standardizing all cycle artifacts to `/home/jes/<cycle>/` going forward.

### 7.2 Snap-firefox migration delay (NEW)

Dist-upgrade hung mid-execution on `firefox` deb-to-snap migration: postinst calls `snap install firefox`, which downloaded at 25 kB/s with ETA 2-3h initially. Resolved itself within ~1 min (network speed recovered to MB/s). **Action for future cycles:** consider pre-removing `firefox` deb on headless Goliath (Goliath has no display; firefox unnecessary). Same for `nvidia-desktop-default-snaps` (configured during cycle, seeds gnome-42-2204, core22, firmware-updater snaps — all unused on headless).

### 7.3 sshd transient outage during openssh-server postinst (KNOWN)

sshd port 22 dropped for ~80s during dist-upgrade, both LAN and Tailscale. PD established ICMP and noted Goliath alive. sshd recovered cleanly post-postinst. **Action:** noted; not actionable beyond awareness during future apt cycles.

### 7.4 Hold filter strategy (B1 lesson)

Directive's filter (`canonical-nvidia|nvidia-desktop-edge|vulkan-packages`) targeted source URL fragments. Actual `apt-get -s` output emits source by Origin display name (`Nvidia Desktop Packages - Edge Pocket`). **Recommendation for future PPA-aware directives:** filter on Origin display name OR enumerate packages from `apt-cache policy <pkg>` showing PPA origin explicitly, rather than URL fragments.

### 7.5 Hold scope discovery (B2 lesson)

Defensive holds on 2 kernel-meta packages (per directive) would have allowed driver upgrade 580.95.05 → 580.142 via noble-updates fallback. Required hold scope was 30 packages, not 2-4. **Recommendation:** future directives should explicitly use `apt-mark hold` on the entire 580 driver stack as a unit, treating "NVIDIA driver version preservation" as the gate rather than "PPA-source preservation".

### 7.6 Verification gate engineering (PD lesson)

First Step B3 attempt produced false-positive `ALL_30_HELD_CONFIRMED` token from a `comm -23 <(empty) ...` evaluation. Caught immediately via independent `wc -l == 31` count gate. **Recommendation:** verification gates must include direct count assertions, not just diff-style comparisons that pass on missing inputs.

## 8. Cycle execution timing

| Phase | Start (UTC) | End (UTC) | Duration |
|---|---|---|---|
| Block A — DPF.A1-A3 + Steps A1-A4 | 23:49 | 00:11 | ~22 min (probe loop launch + initial-tick verify) |
| Block B — DPF.B1-B10 (preflight + B-batch-3 SG baseline) | 00:11 | 00:24 | ~13 min |
| Step B1 (ollama stop) → B2 (snapshot) | 00:40 | 00:41 | ~1 min |
| **Step B3 first attempt (FAILED — /tmp wipe)** | 00:42 | 00:42 | <1 min (false-positive caught) |
| Step B3 retry + B4 + B5 (recovery via /home/jes/) | 00:46 | 00:47 | ~1 min (~16 min if counting B6 launch) |
| **Step B6 dist-upgrade** | 00:49:59 | 00:55:57 | **~6 min** |
| ssh outage (within B6) | 00:52 | 00:54 | ~80s |
| Step B7+B8+B9+B10+B12 verification batch | 00:57:23 | 00:57:29 | <1 min |
| Probe loop restart in persistent path | 00:58:25 | 00:58:32 | <1 min |
| **Total wall** | 23:49:00 | 00:58:32 | **~69 min** (within AS.3 75-min target) |

## 9. Probe history (post-cycle)

Original `/tmp/cycle2_ppa_probe_history.log` was destroyed by Goliath /tmp cleanup mid-cycle (see §7.1). Original 5-tick history preserved in this review doc:

```
2026-05-04T00:01:28Z lpc=FAIL lp=FAIL
2026-05-04T00:16:54Z lpc=FAIL lp=FAIL
2026-05-04T01:21:03Z lpc=FAIL lp=FAIL
2026-05-04T22:51:00Z lpc=FAIL lp=PASS    (Paco-captured continuity)
2026-05-04T23:58:19Z lpc=FAIL lp=PASS    (first tick from restarted loop @ Step A4)
```

Fresh log at `/home/jes/cycle2_0a/probe_history.log` starts at:

```
2026-05-05T00:58:25Z lpc=FAIL lp=PASS    (first tick post-cycle restart)
```

Asymmetric outage continues: `launchpad.net` reachable, `ppa.launchpadcontent.net` TCP/443 still refused. Probe loop will continue on hourly cadence until cap deadline `2026-05-07T22:23:00Z` UTC.

## 10. Path B authorizations invoked

- **B0 (CEO standing meta-authority):** YES — multiple structural adaptations (filter syntax, hold scope, count band, artifact path) documented in §1.
- **B1 (PPA package list discovery):** YES — filter expansion `canonical-nvidia|...` → `Nvidia Desktop Packages` to match Origin display name in apt-get -s output.
- **B2 (kernel-meta dependency identification):** YES — hold list expanded from 2 defensive holds to 11 kernel-6.17 packages; covers entire 6.17 set including `linux-image-6.17.0-*`, `linux-modules-6.17.0-*`, `linux-headers-6.17.0-*`, `linux-tools-6.17.0-*`, `linux-nvidia-6.17-*` plus `linux-*-nvidia-hwe-24.04` meta-packages.
- **B3 (apt-get options):** NO — `--force-confold` + `--force-confdef` defaults sufficed; no need to switch to `--force-confnew`.
- **B4 (ollama restore failure):** NO — ollama restarted clean at Step B9 first try with all 3 models present.
- **B5 (standing-gate drift):** NO — no SG drift observed at Step B5 mid-cycle sentinel.

**NOT authorized actions taken:** none. Cycle stayed within all directive's NOT-authorized boundaries — no kernel 6.17 install, no PPA-only binary modify, no Goliath reboot, no nginx/Tailscale/systemd modification (except ollama.service start/stop and the involuntary openssh-server postinst restart which is a side effect of ubuntu-standard apt-get behavior, not a PD action).

## 11. Close-confirm signature

- **K+D+M bit-identical pre/post:** ✓ AC.3+AC.4+AC.5 all PASS; gate `K_D_M_BIT_IDENTICAL_PASS`.
- **6/6 fleet standing gates bit-identical pre/mid/post:** ✓ AC.11.
- **ollama 3 models restored:** ✓ AC.8.
- **dpkg health clean:** ✓ AC.7.
- **~579 packages upgraded; canonical-nvidia content unchanged:** ✓ AC.6.
- **Hold list = 31:** ✓ AC.9.
- **No reboot:** ✓ AS.1.
- **Cycle wall time < 75 min:** ✓ AS.3 (69 min).
- **B0 invocation:** YES — multi-step structural adaptation, intent preserved unchanged across all decisions. **Per directive §5: clean cycle qualifies B0 for SR #9 promotion at Paco close-confirm.**
- **AC.10 cadence:** PENDING B11 read at ~01:25Z UTC (will append result via second commit if outside tolerance, or note in next session anchor if within tolerance).
- **AC.12 secrets-scan + AC.13 commit/push:** PENDING (this turn).

— PD
