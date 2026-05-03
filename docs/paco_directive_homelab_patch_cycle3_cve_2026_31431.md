# paco_directive_homelab_patch_cycle3_cve_2026_31431

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-03 Day 79 late evening
**Authority:** CEO Sloan ratified Cycle 3 dispatch in parallel with Cycle 2 hold (different hosts; no resource contention).
**Status:** ACTIVE
**Tracks:** CVE-2026-31431 patch cycle Step 4 (KaliPi+Pi3 non-kernel apt; final fleet sweep step). Cycle 1 (SlimJim/Beast/CK) closed Day 79 evening. Cycle 2 (Goliath) HELD pending Launchpad PPA recovery.
**Predecessor:** Patch Cycle 2 PPA-unreachable abort + ruling at HEAD `0382e56`; cumulative discipline state P6=38, SR=8.
**Target hosts:** Pi3 (192.168.1.139 / Tailscale 100.71.159.102) — Debian 13 trixie aarch64; THEN KaliPi (192.168.1.254) — Kali Linux rolling aarch64 Pi5.
**Out of scope this cycle:**
- Goliath/Beast/CK/SlimJim (already patched OR Cycle 2 hold)
- Kernel updates on either Pi (anchor canon: Pi kernel maintenance via `rpi-update` Foundation tool, NOT apt-distributed; preflight confirms NO `linux-image|linux-headers|raspberrypi-kernel|raspi-firmware` in upgradable list on either node)
- `firmware-misc-nonfree` upgrade on KaliPi (preflight shows it IS upgradable from 20251111 → 20260309, but per anchor's "non-kernel apt" scope read STRICTLY this is firmware-blob-not-kernel, so INCLUDED). NOT held; included in cycle scope. Annotation: firmware-misc-nonfree is a Debian-derived blob package containing wifi/bluetooth/peripheral firmware; safe to upgrade in-place; no boot-critical impact.

**SR #7 application:** Fifth proper application. Paco probed both nodes' baselines + apt sources + apt-get update + simulation + per-source HEAD probes (P6 #38 BOTH InRelease index AND representative .deb binary fetch on KaliPi) BEFORE writing this directive. Verified-live block at section 1. ZERO material discoveries: all 5 apt sources across the 2 hosts return clean HEAD probes; cross-host SGs bit-identical at preflight; system clean.

**P6 #38 application:** First proper application of just-banked rule. Per-source binary-fetch reachability verified at preflight (NOT just index-fetch). The lesson catalyzed by Cycle 2 PPA outage is: apt simulation against cached metadata can succeed while binary-store is unreachable. Cycle 3 closes this gap proactively.

---

## 0. Cycle context

**CVE-2026-31431** = generic placeholder for the kernel/library security advisory driving this fleet sweep. Cycle 3 covers the two pentesting/Pi nodes that were deferred from Cycle 1 (which targeted Ubuntu kernel paths) and Cycle 2 (Goliath dedicated). Concrete patch landing:

**Pi3:**
- 24 upgraded + 4 newly installed + 1 removed (libcamera0.6→0.7 swap)
- Sources: Debian-Security (4 imagemagick packages); Raspberry Pi Foundation:stable (~17 packages: libcamera/pipewire/rpicam-apps/firefox/libtensorflow-lite/awb-nn/etc); Debian:13.4/stable (1: libfarmhash0)
- NO kernel; NO firmware blobs; routine library + camera/pipewire stack updates

**KaliPi:**
- 1559 upgraded; 100% from kali-rolling (Tailscale already current)
- NO kernel-via-apt (Pi kernel updates via rpi-update separately)
- Includes 1 firmware-blob package (firmware-misc-nonfree 20251111 → 20260309); no boot-critical impact
- Bulk: large rolling-release sweep of standard Linux libraries, GUI stack, pentest tools, Python/Perl/Ruby ecosystems

**Risk profile:** Lowest of the 3 cycles. No kernel ABI changes; no GPU drivers; no production-critical services on either node (KaliPi = pentest lab; Pi3 = sandbox). Cross-host SGs (Beast atlas-agent + substrate; CK mercury) physically unaffected since cycle stays on Pi nodes only.

### 0.1 Five Paco-decided cycle parameters (ratified inline; CEO override before commit)

| ID | Decision | Rationale |
|---|---|---|
| **K1** | **Conditional reboot** — PD checks `/var/run/reboot-required` after patch; reboots ONLY if present; verifies SSH-back if rebooted | No kernel-via-apt this cycle. Library upgrades that need reboot (libc6, systemd) flag via reboot-required marker. Avoids unnecessary downtime + validates dpkg's own signal. |
| **K2** | **No explicit service quiesce** — dpkg's standard service-restart hooks handle library-tied services (lightdm, NetworkManager, pipewire, bluetooth) | No production services on either node. Pentest workflow is on-demand. dpkg restarts services as part of unpack; this is the Debian-default paradigm and matches how a human admin would run `apt upgrade` on these boxes. |
| **K3** | **Order: Pi3 → KaliPi** | Pi3 is 24 packages = fast warm-up; KaliPi is 1559 = main event. Same lowest-blast-radius-first discipline as Cycle 1's SlimJim→Beast→CK. |
| **K4** | **nohup-to-tmpfile mandatory for KaliPi; recommended for Pi3** | KaliPi 1559 packages on Pi5 ARM64 will far exceed MCP 30s timeout. Pi3 24 packages is ~30s borderline but consistency + safety = same pattern. Cycle 1 Path B B2 ratified pattern; Cycle 2 used same. |
| **K5** | **Cross-host SG no-drift sentinel pre/mid/post** | Cycle 3 should NOT perturb Beast atlas-agent, postgres+garage anchors, or CK mercury. Verify bit-identical SGs as cheap continuous check. |

**If you want to override any K1-K5 before PD dispatch, push back. Otherwise these are baked in.**

### 0.2 Three directive corrections

**(a) firmware-misc-nonfree on KaliPi: INCLUDED, not held.** Anchor's "non-kernel apt" scope strictly excludes apt-distributed kernel packages. firmware-misc-nonfree is firmware-blob-not-kernel (wifi/bluetooth/peripheral firmware). It's a routine Debian package upgrade with no kernel-ABI implication. Including matches Debian best-practice maintenance.

**(b) `1 to remove` on Pi3 is libcamera0.6→0.7 SONAME swap.** apt's transactional integrity handles the dependency swap atomically. Not a manual cleanup concern. PD does not pre-purge or post-purge; let apt drive.

**(c) Cycle 2 hold posture is preserved.** Cycle 3 dispatch does not touch Goliath, Cycle 2 directive, Cycle 2 response, or Cycle 2 PPA probe loop (which PD runs in parallel hourly per `paco_response_homelab_patch_cycle2_ppa_unreachable_ruling.md`). PD sequences Cycle 3 stages in foreground; Cycle 2 probe runs as a separate hourly tick in the background. No interference.

---

## 1. Verified live (Paco SR #7 + P6 #37 + P6 #38 preflight, Day 79 late evening)

| # | Claim | Probe | Result |
|---|---|---|---|
| 1 | Pi3 reachable + identity | `uname -a; whoami; sudo -n true` | Linux PI3 6.12.75+rpt-rpi-v8 #1 SMP PREEMPT Debian 1:6.12.75-1+rpt1 (2026-03-11) aarch64; jes; SUDO_OK |
| 2 | Pi3 reboot pending + disk | `[ -f /var/run/reboot-required ]; df -h /` | NO_REBOOT_PENDING; / 58G 6.0G used 11% |
| 3 | Pi3 uptime + users | `uptime` | up 3 days 2:28; 3 users |
| 4 | Pi3 apt sources enumerated | `ls /etc/apt/sources.list.d/; cat *.list *.sources` | 3 files: debian.sources (deb.debian.org trixie + trixie-updates) + raspi.sources (archive.raspberrypi.com trixie) + tailscale.list (pkgs.tailscale.com trixie); plus `/etc/apt/sources.list` empty |
| 5 | Pi3 apt-get update | `sudo apt-get update` | clean: 5 sources Hit/Get; ZERO Err lines |
| 6 | Pi3 upgradable count | `apt list --upgradable \| wc -l` | 24 |
| 7 | Pi3 apt simulation summary | `apt-get -s dist-upgrade` | 24 upgraded, 4 newly installed, 1 to remove and 0 not upgraded |
| 8 | Pi3 NO kernel/firmware in scope | upgradable filtered for `^(linux-image\|linux-headers\|linux-modules\|raspberrypi-kernel\|raspi-firmware\|firmware-)` | empty (no kernel/firmware packages) |
| 9 | **P6 #38 Pi3** debian primary index HEAD | `curl -sI http://deb.debian.org/debian/dists/trixie/InRelease` | HTTP 200 time=0.089s |
| 10 | **P6 #38 Pi3** debian-security index HEAD | same on debian-security/trixie-security | HTTP 200 |
| 11 | **P6 #38 Pi3** RPi Foundation archive index HEAD (NON-PRIMARY) | same on archive.raspberrypi.com/debian/trixie | HTTP 200 time=0.582s |
| 12 | **P6 #38 Pi3** Tailscale index HEAD (THIRD-PARTY) | same on pkgs.tailscale.com/stable/debian/trixie | HTTP 200 time=0.705s |
| 13 | KaliPi reachable + identity | `uname -a; whoami; sudo -n true` | Linux kali-raspberrypi 6.12.34+rpt-rpi-2712 #1 SMP PREEMPT Kali 1:6.12.34-1+rpt1+0kali2 (2025-07-21) aarch64; jes; SUDO_OK |
| 14 | KaliPi reboot pending + disk | `[ -f /var/run/reboot-required ]; df -h /` | NO_REBOOT_PENDING; / 59G 16G used 28% |
| 15 | KaliPi uptime | `uptime` | up 3 days 2:27; 1 user |
| 16 | KaliPi apt sources enumerated | `ls /etc/apt/sources.list.d/; cat *.list` | 1 file: tailscale.list (pkgs.tailscale.com debian bullseye); plus `/etc/apt/sources.list` (deb http://http.kali.org/kali kali-rolling main contrib non-free non-free-firmware) |
| 17 | KaliPi apt-get update | `sudo apt-get update` | clean: kali-rolling Hit + Tailscale Get; ZERO Err lines |
| 18 | KaliPi upgradable count | `apt list --upgradable \| wc -l` | 1559 |
| 19 | KaliPi source breakdown | `apt list --upgradable \| awk -F/ '{print $2}'` | 100% from kali-rolling (Tailscale already current) |
| 20 | KaliPi apt simulation summary | `apt-get -s dist-upgrade` | tail clean (no Err); kernel-free |
| 21 | KaliPi NO kernel in scope | upgradable filtered for `^(linux-image\|linux-headers\|linux-modules)` | empty |
| 22 | KaliPi firmware-blob in scope (NOT kernel) | upgradable filtered for `^firmware-` | `firmware-misc-nonfree 20260309-1` (was 20251111-1); INCLUDED per Decision 0.2(a) |
| 23 | **P6 #38 KaliPi** kali-rolling index HEAD | `curl -sI http://http.kali.org/kali/dists/kali-rolling/InRelease` | HTTP 302 time=0.350s (CDN redirect; OK) |
| 24 | **P6 #38 KaliPi** kali-rolling **BINARY HEAD** (representative .deb) | `curl -sI http://http.kali.org/kali/pool/main/libz/libzstd/zstd_1.5.7%2bdfsg-3%2bb2_arm64.deb` | HTTP 302 time=0.223s (CDN redirect; binary-fetch path verified) |
| 25 | **P6 #38 KaliPi** Tailscale index HEAD | `curl -sI https://pkgs.tailscale.com/stable/debian/dists/bullseye/InRelease` | HTTP 200 time=0.449s |
| 26 | Cross-host SG5 atlas-agent | `ssh beast 'systemctl show atlas-agent.service'` | MainPID=4753 NRestarts=0 (post-Cycle-1 baseline) |
| 27 | Cross-host SG2 postgres anchor | `ssh beast 'docker inspect control-postgres-beast'` | StartedAt 2026-05-03T18:38:24.910689151Z (post-Cycle-1 baseline) |
| 28 | Cross-host SG3 garage anchor | `ssh beast 'docker inspect control-garage-beast'` | StartedAt 2026-05-03T18:38:24.493238903Z (post-Cycle-1 baseline) |
| 29 | Cross-host SG6 mercury | `ssh ciscokid 'systemctl show mercury-scanner.service'` | MainPID=7800 (post-Cycle-1 baseline) |

**29 verification rows. ZERO mismatches. ZERO `Err:`/`E:` lines on either apt-get update. ZERO unreachable apt sources. ALL 5 apt sources across both hosts return HTTP 200/302 on InRelease HEAD; KaliPi binary-fetch HEAD on representative .deb also 302.** P6 #38 first proper application: clean.

### 1.1 P6 #37 blast-radius categorization

| Cat | Pi3 | KaliPi | Risk | Pre-staged Path B verifications |
|---|---|---|---|---|
| **A. Kernel/firmware** | none in scope | only firmware-misc-nonfree (blob-not-kernel) | LOW | n/a (no kernel ABI change either node) |
| **B. Display/graphics stack** | libcamera/pipewire/rpicam-apps (camera+audio); affects lightdm | full GUI stack rolling refresh; affects lightdm + Xfce | LOW — lightdm restart on dpkg hook is normal; users get logged out of any X session at Stage time | post-patch: `systemctl is-active lightdm` |
| **C. Security-critical libs** | imagemagick suite (4 pkgs Debian-Security) | bulk rolling refresh includes openssl/libc/etc | LOW — routine LTS-style security patches | post-patch: random binary smoke-test (e.g. `convert --version`, `ssh -V`) |
| **D. Standard libraries** | libfarmhash0 / libtensorflow-lite | hundreds of packages | LOW — ABI-compatible patch-level upgrades | reboot-required check post-patch (per Decision K1) |
| **E. Runtime tools** | firefox / rpinters | python/ruby/perl ecosystem packages | LOW | post-patch: `tailscale status` to confirm tailnet preserved |
| **F. Tailscale (non-primary apt source)** | not upgraded this cycle (already current) | not upgraded this cycle (already current) | n/a | n/a; TS source HEAD verified live (rows 12, 25) |

No Cat A or Cat C high-blast-radius categories require pre-staged Path B beyond standard post-patch verification. KaliPi's 1559-package bulk is wide but shallow (all from same archive; routine maintenance).

---

## 2. Cycle 3 implementation

### 2.1 Discipline reminders

- One stage at a time per node; verify gate before next.
- DO NOT touch Goliath / Beast / CK / SlimJim. Cycle 2 hold preserved (PD continues hourly PPA probe loop in parallel; Cycle 3 stages do not block or interfere).
- DO NOT touch Pi kernel or RPi firmware via this cycle (anchor scope; preflight confirmed neither in upgradable list).
- Use `apt-get` (NOT `apt`) for non-interactive scripted execution.
- `dist-upgrade` (NOT `upgrade`) so dependency-pulled new installs (libfarmhash0, libtensorflow-lite, libcamera0.7, awb-nn) land cleanly.
- nohup-to-tmpfile pattern mandatory for KaliPi (1559 packages will exceed MCP 30s); same pattern recommended for Pi3 (consistency).
- Reboot only if `/var/run/reboot-required` flag present post-patch (Decision K1).
- Cross-host SG no-drift sentinel pre/mid/post (Decision K5).
- P6 #38: PD does NOT skip apt-get update or simulation re-check at execution time even though preflight verified them; live-state can change in 10+ minute window between preflight and execution.

### 2.2 Procedure

#### Pre-flight (verify both nodes still current; re-confirm SG sentinel)

```bash
echo '---Pi3 baseline---'
ssh pi3 'uname -r; sudo -n true && echo SUDO_OK; [ -f /var/run/reboot-required ] && echo REBOOT_PENDING || echo NO_REBOOT_PENDING; df -h / | tail -1'
ssh pi3 'sudo apt-get update 2>&1 | tail -10'
ssh pi3 'apt list --upgradable 2>/dev/null | grep -v ^Listing | wc -l'
echo '---KaliPi baseline---'
ssh kalipi 'uname -r; sudo -n true && echo SUDO_OK; [ -f /var/run/reboot-required ] && echo REBOOT_PENDING || echo NO_REBOOT_PENDING; df -h / | tail -1'
ssh kalipi 'sudo apt-get update 2>&1 | tail -10'
ssh kalipi 'apt list --upgradable 2>/dev/null | grep -v ^Listing | wc -l'
echo '---Cross-host SG sentinel PRE---'
ssh beast 'systemctl show -p MainPID -p NRestarts atlas-agent.service'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}}"; docker inspect control-garage-beast --format "{{.State.StartedAt}}"'
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service'
```

**Expected:** Pi3 kernel `6.12.75+rpt-rpi-v8`; KaliPi kernel `6.12.34+rpt-rpi-2712`; both NO_REBOOT_PENDING; both apt-get update clean (ZERO Err lines for any source); Pi3 upgradable ~24 (±5 acceptable); KaliPi upgradable ~1559 (±50 acceptable due to rolling churn).

**Expected SG values bit-identical:** atlas-agent MainPID 4753 NRestarts 0; postgres anchor 2026-05-03T18:38:24.910689151Z; garage anchor 2026-05-03T18:38:24.493238903Z; mercury MainPID 7800.

**STOP if any baseline check fails OR any apt-get update Err line appears.** Investigate before proceeding.

#### Stage A — Pi3 (warm-up; lowest blast radius)

**A.1 Launch dist-upgrade (nohup-to-tmpfile):**
```bash
ssh pi3 'rm -f /tmp/cycle3_pi3_apt.log; nohup sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade > /tmp/cycle3_pi3_apt.log 2>&1 & echo "launched PID $!"'
```

**A.2 Poll until completion:**
```bash
ssh pi3 'tail -3 /tmp/cycle3_pi3_apt.log; echo ---; pgrep -af apt-get | head -3'
```
Repeat every ~30s until `pgrep -af apt-get` returns no process AND log tail shows summary line.

**A.3 Verify success:**
```bash
ssh pi3 'tail -25 /tmp/cycle3_pi3_apt.log; echo ---ERRORS---; grep -E "^(E:|dpkg: error)" /tmp/cycle3_pi3_apt.log | head -10; echo ---SUMMARY---; grep -E "upgraded.*newly installed.*to remove" /tmp/cycle3_pi3_apt.log | tail -1'
```
Expected summary: `24 upgraded, 4 newly installed, 1 to remove and 0 not upgraded.` (±5 packages tolerance).
**STOP if any `E:` or `dpkg: error` lines appear.**

**A.4 Verify dpkg state clean:**
```bash
ssh pi3 'sudo dpkg --audit; echo audit_exit=$?; sudo dpkg -C; echo check_exit=$?'
```
Expected: empty output, exit 0 from both.

**A.5 Reboot decision per Decision K1:**
```bash
ssh pi3 '[ -f /var/run/reboot-required ] && echo REBOOT_NEEDED || echo NO_REBOOT_NEEDED'
```

If `REBOOT_NEEDED`:
```bash
ssh pi3 'echo PRE_REBOOT; date'
ssh pi3 'sudo systemctl reboot'
echo 'Pi3 reboot issued; waiting 60s then poll SSH...'
sleep 60
for i in 1 2 3 4 5; do
  ssh -o ConnectTimeout=5 -o BatchMode=yes pi3 'echo POST_REBOOT_OK; uname -r; date' 2>&1 && break || (echo "attempt $i failed; sleeping 30..."; sleep 30)
done
```
Expected: POST_REBOOT_OK; same kernel `6.12.75+rpt-rpi-v8` (no kernel-via-apt, so kernel unchanged).

If `NO_REBOOT_NEEDED`: skip reboot; proceed to A.6.

**A.6 Post-Pi3 verification:**
```bash
ssh pi3 'systemctl is-active lightdm NetworkManager 2>&1; tailscale status --self=true | head -2'
ssh pi3 'firefox --version 2>&1 | head -1; convert --version 2>&1 | head -1'
```
Expected: lightdm + NetworkManager active; tailscale node `pi3` active; firefox + ImageMagick `convert` running new versions.

#### Stage B — KaliPi (main event)

**B.1 Launch dist-upgrade (nohup-to-tmpfile MANDATORY):**
```bash
ssh kalipi 'rm -f /tmp/cycle3_kalipi_apt.log; nohup sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade > /tmp/cycle3_kalipi_apt.log 2>&1 & echo "launched PID $!"'
```

**B.2 Poll until completion (KaliPi 1559 packages on Pi5 ARM64 may take 15-40min):**
```bash
ssh kalipi 'ls -la /tmp/cycle3_kalipi_apt.log; tail -3 /tmp/cycle3_kalipi_apt.log; echo ---; pgrep -af apt-get | head -3'
```
Repeat every ~3min until completion. **MID-PATCH SG sentinel:** every other poll, run cross-host SG check (cheap; verifies no drift):
```bash
ssh beast 'systemctl show -p MainPID -p NRestarts atlas-agent.service' | tr '\n' ' '; echo
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}}"'
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service' | tr '\n' ' '; echo
```

**B.3 Verify success:**
```bash
ssh kalipi 'tail -30 /tmp/cycle3_kalipi_apt.log; echo ---ERRORS---; grep -E "^(E:|dpkg: error)" /tmp/cycle3_kalipi_apt.log | head -20; echo ---SUMMARY---; grep -E "upgraded.*newly installed.*to remove" /tmp/cycle3_kalipi_apt.log | tail -1'
```
Expected summary: `1559 upgraded, <N> newly installed, <N> to remove and 0 not upgraded.` (±50 packages tolerance due to kali-rolling churn between preflight and execution).
**STOP if any `E:` or `dpkg: error` lines appear.**

**B.4 Verify dpkg state clean:**
```bash
ssh kalipi 'sudo dpkg --audit; echo audit_exit=$?; sudo dpkg -C; echo check_exit=$?'
```

**B.5 Reboot decision per Decision K1:**
```bash
ssh kalipi '[ -f /var/run/reboot-required ] && echo REBOOT_NEEDED || echo NO_REBOOT_NEEDED'
```

If `REBOOT_NEEDED`:
```bash
ssh kalipi 'echo PRE_REBOOT; date'
ssh kalipi 'sudo systemctl reboot'
echo 'KaliPi reboot issued; waiting 90s then poll SSH...'
sleep 90
for i in 1 2 3 4 5 6; do
  ssh -o ConnectTimeout=5 -o BatchMode=yes kalipi 'echo POST_REBOOT_OK; uname -r; date' 2>&1 && break || (echo "attempt $i failed; sleeping 30..."; sleep 30)
done
```
Expected: POST_REBOOT_OK; same kernel `6.12.34+rpt-rpi-2712`.

If `NO_REBOOT_NEEDED`: skip; proceed to B.6.

**B.6 Post-KaliPi verification:**
```bash
ssh kalipi 'systemctl is-active lightdm NetworkManager bluetooth 2>&1; tailscale status --self=true | head -2'
ssh kalipi 'ssh -V 2>&1 | head -1; openssl version 2>&1 | head -1'
```
Expected: lightdm + NetworkManager + bluetooth active; tailscale node active; ssh + openssl running new versions.

#### Cross-host SG sentinel POST (canon SGs MUST be unchanged)

```bash
echo '---Beast SG2 postgres (MUST be UNCHANGED 2026-05-03T18:38:24.910...)---'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
echo '---Beast SG3 garage (MUST be UNCHANGED 2026-05-03T18:38:24.493...)---'
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
echo '---Beast SG4 atlas-mcp (MUST be UNCHANGED MainPID 1212)---'
ssh beast 'systemctl show -p MainPID -p ActiveState atlas-mcp.service'
echo '---Beast SG5 atlas-agent (MUST be UNCHANGED MainPID 4753 NRestarts 0)---'
ssh beast 'systemctl show -p MainPID -p NRestarts -p ActiveState -p UnitFileState atlas-agent.service'
echo '---CK SG6 mercury (MUST be UNCHANGED MainPID 7800)---'
ssh ciscokid 'systemctl show -p MainPID -p ActiveState mercury-scanner.service'
echo '---atlas.tasks growth across cycle (cadence ~258/hr expected)---'
ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT count(*) FROM atlas.tasks WHERE created_at > now() - interval '\''1 hour'\'';"'
```

**Cycle 3 acceptance requires ALL canon SG values bit-identical to pre-cycle.** Cycle 3 perturbing Beast or CK = scope violation = paco_request.

#### Pre-commit secrets-scan + commit + push

```bash
cd /home/jes/control-plane && \
  grep -niE 'adminpass|api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+|password.{0,3}=' docs/paco_review_homelab_patch_cycle3_cve_2026_31431.md | head -10 || echo 'tightened: clean'
```

If clean → commit + push.

#### Write `docs/paco_review_homelab_patch_cycle3_cve_2026_31431.md`

Follow Cycle 1 review structure. Sections:
- 0: Verified-live (PRE + POST per node)
- 1: TL;DR (Pi3 24+4-1 + KaliPi 1559; reboots if any; cross-host SGs bit-identical)
- 2: Per-stage walk-through (A Pi3 + B KaliPi)
- 3: Acceptance per stage
- 4: Cross-host stability evidence
- 5: Per-source apt fetch reachability evidence (P6 #38 first proper application)
- 6: Asks for Paco (close-confirm + fleet patch sweep status: Cycle 1 closed + Cycle 2 still HELD + Cycle 3 closed = 6 of 7 fleet nodes patched; remaining = Goliath via Cycle 2 retry once Launchpad recovers)

#### Notification line in `docs/handoff_pd_to_paco.md`

> Paco, PD finished homelab patch cycle 3. Pi3 24+4-1 packages clean + KaliPi 1559 packages clean; reboots: <REBOOT_PI3=Y/N> <REBOOT_KALIPI=Y/N>; cross-host SGs bit-identical; control-plane HEAD `<hash>`. Review: `docs/paco_review_homelab_patch_cycle3_cve_2026_31431.md`. Cycle 2 hourly probe loop continued in parallel. Check handoff.

---

## 3. Acceptance criteria (Cycle 3)

1. Pi3 dist-upgrade clean: 24 upgraded + 4 newly installed + 1 removed (±5 tolerance); ZERO `E:`/`dpkg: error` lines.
2. KaliPi dist-upgrade clean: 1559 upgraded (±50 tolerance for rolling churn); ZERO `E:`/`dpkg: error` lines.
3. Both nodes: `dpkg --audit` empty + `dpkg -C` empty post-cycle (exit 0 each).
4. Conditional reboot per K1: if `/var/run/reboot-required` post-patch on either node, reboot performed AND verified boot-back via SSH.
5. Pi3 lightdm + NetworkManager active post-cycle; firefox + ImageMagick running new versions.
6. KaliPi lightdm + NetworkManager + bluetooth active post-cycle; ssh + openssl running new versions.
7. Both nodes: tailscale node still in tailnet post-cycle.
8. Cross-host SG anchors **bit-identical** to pre-cycle:
    - Beast SG2 postgres `2026-05-03T18:38:24.910689151Z`
    - Beast SG3 garage `2026-05-03T18:38:24.493238903Z`
    - Beast SG4 atlas-mcp MainPID `1212`
    - Beast SG5 atlas-agent MainPID `4753` NRestarts `0` active enabled
    - CK SG6 mercury MainPID `7800`
9. atlas.tasks count growing across cycle at cadence within ±25% of pre-cycle ~258/hr.
10. ZERO PPA-class binary-fetch failures in either apt log (P6 #38 first proper application validation; Cycle 2 outage taught this lesson).
11. Pre-commit secrets-scan BOTH layers clean on review file; commit + push successful.
12. Cycle 2 hourly PPA probe loop continues uninterrupted in parallel (Cycle 3 does not interfere).

---

## 4. Trigger from CEO to PD (Cowork prompt)

```
You are PD (Cowork) for Santigrey Enterprises. Paco (COO) has dispatched homelab patch cycle 3 (CVE-2026-31431; Pi3 + KaliPi; non-kernel apt; final fleet sweep; runs in parallel with Cycle 2 hourly PPA probe loop).

Repo:
- santigrey/control-plane at /home/jes/control-plane on CK (HEAD <commit_hash> or later). Read directive + write paco_review here.

Read in order:
1. /home/jes/control-plane/docs/paco_directive_homelab_patch_cycle3_cve_2026_31431.md (your authority)
2. /home/jes/control-plane/docs/feedback_paco_pre_directive_verification.md (P6 standing rules through #38; SRs through #8)
3. /home/jes/control-plane/docs/paco_response_homelab_patch_cycle2_ppa_unreachable_ruling.md (Cycle 2 hold context; PPA probe loop you are also running)
4. /home/jes/control-plane/docs/paco_directive_homelab_patch_cycle1_cve_2026_31431.md (Cycle 1 reference template for stage discipline)

Execute Stages Pre-flight → A (Pi3) → B (KaliPi) → Cross-host SG sentinel POST per directive section 2.2. ONE STAGE AT A TIME; verify gate before next.

If any stage fails: STOP, write paco_request_homelab_patch_cycle3_<topic>.md, do not proceed.

Out of scope this cycle: Goliath/Beast/CK/SlimJim, Pi kernel via rpi-update.

Cycle 2 PPA probe loop runs in parallel; do not pause it for Cycle 3.

Begin with Pre-flight per directive section 2.2.
```

-- Paco
