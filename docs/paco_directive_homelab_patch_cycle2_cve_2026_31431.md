# paco_directive_homelab_patch_cycle2_cve_2026_31431

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-03 Day 79 late evening
**Authority:** CEO ratified Day 79 evening (Decisions A3/B3/C2/D2/E2). CEO ratified Day 79 late-evening fresh-session resume the C2 mechanism shift `dkms→prebuilt-modules verify` (DGX OS does not use dkms; mechanism corrected; spirit preserved).
**Status:** ACTIVE
**Tracks:** CVE-2026-31431 patch cycle Step 3 (Goliath dedicated). Cycle 1 (SlimJim+Beast+CK) closed Day 79 evening at `docs/paco_response_homelab_patch_cycle1_close_confirm.md`.
**Predecessor:** Patch Cycle 1 close-confirm 11/11 PASS first-try; new SG canonical baseline established post-Cycle-1; P6 #37 banked (blast-radius categorization in package-upgrade directives); SR #7 fourth proper application.
**Target host:** Goliath (192.168.1.20 / Tailscale `sloan4` 100.112.126.63) -- DGX Spark, NVIDIA GB10, aarch64, Ubuntu 24.04 noble + NVIDIA-vendored kernel.
**Out of scope this cycle:**
- SlimJim/Beast/CK (already patched Cycle 1)
- KaliPi/Pi3 (queued Cycle 3)
- workbench repo (`https://workbench.download.nvidia.com/stable/linux/debian` GPG key `EXPKEYSIG CD63F8B21266DE3C` expired; per Decision A3, GPG remediation tracked as separate maintenance; the 584 upgradable packages do NOT include workbench-sourced packages because apt fails to fetch the workbench index)
- docker-compose-plugin v5 jump (held via `apt-mark hold` per Decision B3; v5 has known config syntax breaking changes; v5 upgrade banked as separate maintenance after compose-file syntax verification)
- 3 unreachable Canonical NVIDIA PPAs at `ppa.launchpadcontent.net` (cosmetic warnings only; analogous to Beast's deadsnakes PPA in Cycle 1)
- Goliath SG canonization (per Decision E2, Goliath services are spot-snapshotted this cycle for review only; canon SG addition deferred to v0.1.1)

**SR #7 application:** Fourth proper application. Paco probed Goliath baselines + apt simulation + driver/modules/cuda/docker versions + NVIDIA module mechanism (DGX OS prebuilt, NOT dkms) BEFORE writing this directive. Verified-live block at section 1. One material discovery surfaced and CEO-ratified pre-author: Decision C2 verification mechanism shift (dkms→prebuilt-modules presence). Anchor's `dkms status` command was incorrect for DGX OS; corrected mechanism preserves the verify-before-reboot ABORT gate.

---

## 0. Cycle context

**CVE-2026-31431** = generic placeholder for kernel security advisories driving this fleet patch cycle. The concrete patch landing on Goliath is:
- **Major kernel jump**: `linux-image-nvidia-hwe-24.04` 6.11.0-1016.16 → **6.17.0-1014.14** (Ubuntu noble HWE NVIDIA-vendored kernel; 6 kernel-version-specific deps newly installed)
- **NVIDIA driver minor bump**: libnvidia-* 580.95.05 → 580.142 (driver remains in 580 series; 9+ libnvidia-* packages)
- **NVIDIA container toolkit**: libnvidia-container1 1.17.8 → 1.19.0
- **CUDA toolkit minor**: cuda-toolkit-13-0 13.0.0 → 13.0.3 + cuda-toolkit-config-common 13.0.88 → 13.2.75 (~16 cuda-* packages)
- **Container runtime major**: containerd.io 1.7.26 → **2.2.1** (major version jump 1→2); docker-ce 28.3.3 → 29.2.1; docker-buildx-plugin 0.26 → 0.31
- **Python 3.12 patch**: 3.12.3-1ubuntu0.8 → 3.12.3-1ubuntu0.13 (ABI-compatible; 7 packages)
- **Ubuntu noble standard updates**: ~520 baseline packages

**Risk profile:** This is the highest-complexity cycle in the fleet patch sweep. Kernel ABI change + NVIDIA driver swap + containerd 1→2 major bump + GPU host with three loaded large models (qwen2.5:72b, deepseek-r1:70b, llama3.1:70b) running 24/7. **Treat every gate seriously.** No `apt-get -y` blasts without intermediate verification.

### 0.1 Five CEO-ratified decisions (anchor section: "CEO ratifications")

| ID | Decision | Implication for this directive |
|---|---|---|
| **A3** | Do not touch workbench repo | Workbench GPG warning at `apt-get update` is **cosmetic-expected**, NOT a blocking error. PD does NOT investigate or remediate during this cycle. Same posture for the 3 unreachable canonical-nvidia PPAs. |
| **B3** | Patch container runtime except hold docker-compose-plugin v5 | PD applies `sudo apt-mark hold docker-compose-plugin` BEFORE `dist-upgrade`. Verify post-patch that `docker-compose-plugin` remains at `2.39.1`. |
| **C2** | Verify-before-reboot (mechanism: prebuilt modules presence) | After dist-upgrade completes, BEFORE issuing reboot, PD verifies all kernel-version-specific NVIDIA module packages installed AND all 5 nvidia .ko files present in `/lib/modules/6.17.0-1014-nvidia/kernel/nvidia-580-open/`. If ANY missing → ABORT, do NOT reboot, paco_request. |
| **D2** | Ollama maintenance-window flip | `sudo systemctl stop ollama.service` BEFORE reboot. Document as planned interruption. Post-reboot, verify ollama auto-started (or start manually) AND a quick inference probe succeeds AND all 3 large models still listed in `ollama list`. |
| **E2** | Spot-SG only; no canon SG addition | PD captures Goliath service inventory pre/post for the review file ONLY. Do NOT modify canon SG list (CK SG6 mercury, Beast SG2/SG3/SG4/SG5 substrate+atlas, etc. unchanged this cycle). |

### 0.2 Seven directive corrections (read carefully)

**(a) Workbench GPG warning is cosmetic.** Pre-flight `sudo apt-get update` will emit:
```
W: GPG error: https://workbench.download.nvidia.com/stable/linux/debian default InRelease: The following signatures were invalid: EXPKEYSIG CD63F8B21266DE3C svc-workbench <svc-workbench@nvidia.com>
E: The repository '...workbench.download.nvidia.com...' is not signed.
```
This is **expected and benign** per Decision A3. Do NOT remediate. Do NOT add `signed-by`, do NOT remove the `.sources` file, do NOT import a new key. The 584 upgradable packages exclude workbench-sourced packages by virtue of apt failing to fetch that index. apt's overall exit code is 0 and remaining repos load normally. Proceed.

**(b) 3 unreachable canonical-nvidia PPAs are cosmetic.** Pre-flight `apt-get update` will also emit timeout warnings for:
- `ppa.launchpadcontent.net/canonical-nvidia/linux-firmware-mbssid-patches/ubuntu`
- `ppa.launchpadcontent.net/canonical-nvidia/nvidia-desktop-edge/ubuntu`
- `ppa.launchpadcontent.net/canonical-nvidia/vulkan-packages-nv-desktop/ubuntu`
Already-installed packages from these PPAs are unaffected. PD treats these warnings the same as Cycle 1 treated Beast's deadsnakes PPA: cosmetic, do not investigate.

**(c) docker-compose-plugin held BEFORE dist-upgrade per B3.** Stage A pre-patch step: `sudo apt-mark hold docker-compose-plugin`. Verify with `apt-mark showhold` includes `docker-compose-plugin` BEFORE running dist-upgrade. After dist-upgrade, verify `dpkg -l docker-compose-plugin` shows version `2.39.1-1~ubuntu.24.04~noble` (the hold respected). The cycle DOES patch docker-ce, docker-ce-cli, docker-buildx-plugin, and containerd.io to current major versions; only the compose-plugin v5 jump is held.

**(d) Verify-BEFORE-reboot via prebuilt-modules presence (NOT dkms).** Goliath runs DGX OS which does NOT use dkms. The NVIDIA driver kernel modules are shipped as **prebuilt .ko files** in version-pinned packages (`linux-modules-nvidia-580-open-<KERNEL>` and `linux-modules-nvidia-fs-<KERNEL>`). When the meta-package `linux-modules-nvidia-580-open-nvidia-hwe-24.04` upgrades, apt pulls in the matching kernel-version-specific module packages as new installs. The verify-before-reboot ABORT gate confirms these packages installed correctly AND the 5 .ko files are present. See Stage C for the exact commands. **If the verify gate fails, ABORT immediately. Do NOT reboot.** Booting into the new kernel without matching NVIDIA modules takes Goliath off line until manual recovery (boot old kernel via grub, debug, reinstall).

**(e) Ollama maintenance-window flip per D2.** Goliath has 3 large models loaded (~131GB combined: qwen2.5:72b 47GB + deepseek-r1:70b 42GB + llama3.1:70b 42GB). Stop ollama BEFORE reboot to release GPU/system memory cleanly and avoid mid-inference interruption. Service unit name confirmed at preflight: `ollama.service` (PID 1825 pre-cycle, `/usr/local/bin/ollama serve`). Post-reboot, verify the service started AND a quick inference works AND all 3 models are still listed. Models live on disk persistently; reboot does not lose them.

**(f) Goliath SG snapshot is spot-only per E2.** PD captures pre/post Goliath service inventory + ollama inference probe + nvidia-smi + nvcc version + docker daemon version + tailscale status in the review file. PD does NOT propose canon SG additions for Goliath this cycle. v0.1.1 may revisit canon SG inclusion question for Goliath services.

**(g) nohup-to-tmpfile mandatory for `apt-get dist-upgrade`.** With 584 packages on aarch64, dist-upgrade WILL exceed the MCP 30-second tool-call timeout (Cycle 1 Path B B2 ratified pattern; Cycle 1's 41-45 packages already brushed it). PD MUST use:
```bash
nohup sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade > /tmp/cycle2_apt.log 2>&1 &
```
Then poll `/tmp/cycle2_apt.log` size + grep for completion markers (`Setting up`, `dpkg: error`, `E: `, final `<NUM> upgraded, <NUM> newly installed, <NUM> to remove`). PD verifies the process completed before proceeding to Stage C verify gates.

---

## 1. Verified live (Paco SR #7 preflight, Day 79 evening + late-evening fresh-session resume)

| # | Claim | Probe | Result |
|---|---|---|---|
| 1 | Goliath kernel + sudo + reboot pending | `uname -r; sudo -n true; [ -f /var/run/reboot-required ]` | `6.11.0-1016-nvidia`; SUDO_NOPASSWD; NO_REBOOT_PENDING |
| 2 | Goliath uptime + users | `uptime` | up 3 days 24 min, 2 users (1 less than initial probe; non-blocking) |
| 3 | Goliath disk root + boot/efi | `df -h / /boot/efi` | / 1.8T 254G used 15%; /boot/efi 511M 6.4M used 1% (ample) |
| 4 | Goliath upgradable count | `apt list --upgradable \| wc -l` | 584 (zero drift from Day 79 evening anchor) |
| 5 | Apt simulation plan with hold applied | `apt-mark hold docker-compose-plugin; apt-get -s dist-upgrade` | **581 upgraded, 26 newly installed, 2 to remove, 2 not upgraded** (compose-plugin held + 1 other transitively kept-back) |
| 6 | NEW kernel-version-specific packages to install (6) | apt simulation `Inst` lines | linux-image-6.17.0-1014-nvidia / linux-modules-6.17.0-1014-nvidia / linux-modules-nvidia-580-open-6.17.0-1014-nvidia / linux-modules-nvidia-fs-6.17.0-1014-nvidia / linux-headers-6.17.0-1014-nvidia / linux-modules-nvidia-580-open-nvidia-hwe-24.04 (meta) |
| 7 | Removals (2) | apt simulation `Remv` lines | linux-modules-nvidia-580-open-6.11.0-1016-nvidia (old prebuilt obsolete) + nvidia-disable-bt-profiles 25.09-1 (DGX Spark BT-profiles helper; replaced by upstream behavior; safe to remove on inference node) |
| 8 | Workbench repo expired key | `apt-get update` tail | `EXPKEYSIG CD63F8B21266DE3C svc-workbench@nvidia.com` (cosmetic per A3) |
| 9 | 3 PPA unreachable | `apt-get update` tail | `Could not connect to ppa.launchpadcontent.net:443` for canonical-nvidia/{linux-firmware-mbssid-patches,nvidia-desktop-edge,vulkan-packages-nv-desktop} (cosmetic) |
| 10 | Container runtime baseline | `docker version` | Server `28.3.3` / containerd `1.7.26` |
| 11 | docker-compose-plugin baseline | `dpkg -l docker-compose-plugin` | `2.39.1-1~ubuntu.24.04~noble` (will be held) |
| 12 | Running docker containers | `docker ps` | **0 containers** (no quiesce step needed for compose stacks; only docker daemon health post-patch) |
| 13 | Ollama service + version + models | `systemctl is-active ollama.service; ollama list` | active running PID 1825; 3 models present: qwen2.5:72b (47GB), deepseek-r1:70b (42GB), llama3.1:70b (42GB) |
| 14 | NVIDIA driver baseline | `nvidia-smi --query-gpu=driver_version,name --format=csv` | `580.95.05, NVIDIA GB10` |
| 15 | NVIDIA module mechanism | `which dkms; dpkg -l \| grep dkms; find /lib/modules/$(uname -r) -name 'nvidia*.ko*'` | **dkms NOT installed** (DGX OS uses prebuilt modules); 5 nvidia .ko files in `/lib/modules/6.11.0-1016-nvidia/kernel/nvidia-580-open/` (nvidia/nvidia-drm/nvidia-uvm/nvidia-modeset/nvidia-peermem) + nvidia-fs.ko.zst |
| 16 | Currently installed nvidia module packages | `dpkg -l \| grep linux-modules-nvidia` | linux-modules-nvidia-580-open-6.11.0-1016-nvidia (`6.11.0-1016.16+1000`) + linux-modules-nvidia-580-open-nvidia-hwe-24.04 (meta) + linux-modules-nvidia-fs-6.11.0-1016-nvidia |
| 17 | nvcc location (NOT in default PATH) | `which nvcc; ls /usr/local/cuda*/bin/nvcc` | `which nvcc` empty; binary at `/usr/local/cuda/bin/nvcc` (alternatives-managed; symlink chain `/usr/local/cuda → /etc/alternatives/cuda → /usr/local/cuda-13.0`) |
| 18 | CUDA toolkit baseline (filesystem) | `ls /usr/local/cuda-13.0` | toolkit at 13.0.0 path (will upgrade to 13.0.3 in-place; same path) |
| 19 | Tailscale baseline | `tailscale version; tailscale status --self=true` | `1.96.4`; `100.112.126.63 sloan4` linux active (NOT in upgradable list; out of scope) |
| 20 | /tmp writable (nohup pattern feasible) | `touch /tmp/cycle2_probe; rm` | OK |
| 21 | apt-mark holds currently | `apt-mark showhold` | **empty** (no existing holds; PD's `hold docker-compose-plugin` will be the first) |
| 22 | Cross-host stability: Beast atlas-agent | `systemctl show atlas-agent.service` | MainPID 4753 NRestarts 0 active enabled (post-Cycle-1 SG5 baseline; MUST remain unchanged through Cycle 2) |
| 23 | Cross-host stability: Beast substrate | `docker inspect control-postgres-beast / control-garage-beast` | postgres `2026-05-03T18:38:24.910689151Z` + garage `2026-05-03T18:38:24.493238903Z` (post-Cycle-1 SG2/SG3 anchors; MUST remain unchanged) |
| 24 | Cross-host stability: CK mercury | `systemctl show mercury-scanner.service` | MainPID 7800 active (post-Cycle-1 SG6 baseline; MUST remain unchanged) |
| 25 | Cross-host stability: Beast atlas-mcp | `systemctl show atlas-mcp.service` | MainPID 1212 active (post-Cycle-1 SG4 baseline; MUST remain unchanged) |

**25 verification rows. 0 mismatches. 1 mental-model correction landed (dkms→prebuilt-modules).** Cycle 2 scope confirmed bounded; preflight current.

---

## 2. Cycle 2 implementation

### 2.1 Discipline reminders

- **Patch cycle is destructive on Goliath** (kernel bump + driver bump + containerd major + reboot). One stage at a time; verify gate before next stage.
- **Goliath is the ONLY host touched this cycle.** Do not run apt-get on SlimJim/Beast/CK/KaliPi/Pi3.
- **Use `apt-get` (NOT `apt`)** for non-interactive scripted execution.
- **`dist-upgrade` (NOT `upgrade`)** -- new kernel version + 6 new kernel-version-specific deps require dist-upgrade semantics.
- **nohup-to-tmpfile mandatory for dist-upgrade** -- 584 packages will exceed MCP 30s timeout.
- **DO NOT reboot on dkms-equivalent verify failure.** Stage C is the ABORT gate. If any check fails, paco_request and stop.
- **Workbench GPG + 3 PPAs are cosmetic.** Do not investigate or remediate. Treat as Cycle 1 treated deadsnakes PPA.
- **Substrate anchors on Beast (SG2 postgres + SG3 garage) MUST stay bit-identical** through this cycle. Goliath cycle does not touch Beast. If post-cycle Beast inspection shows different StartedAt timestamps than `2026-05-03T18:38:24.*`, something happened on Beast unrelated to this cycle and must be investigated separately.
- **atlas-agent observation continuity:** atlas-agent on Beast continues writing atlas.tasks throughout this cycle. Goliath cycle should not perturb the ~258 rows/hour cadence. PD captures pre/mid/post atlas.tasks counts in review.
- **Reboot recovery window for Goliath:** server-class POST + initramfs + NVIDIA driver init + Ollama serve resume. Cycle 1 Beast observed 9m04s observation gap (vs 90-180s estimate). Goliath has larger NVIDIA stack + more packages -- expect **5-15 minute** recovery window. PD waits 5 min then attempts SSH every 30s for up to 15 min total.
- **Ollama auto-start post-reboot:** verify `systemctl is-enabled ollama.service`. If `enabled`, it should auto-start. If `disabled` or `static`, PD starts manually post-reboot. Either way, verify with `systemctl is-active` + a quick `/usr/local/bin/ollama list` + an inference probe.

### 2.2 Procedure

#### Pre-flight (verify Goliath baseline still current; do not proceed if any check fails)

```bash
echo '---Goliath baseline verify---'
ssh goliath 'uname -r; sudo -n true && echo SUDO_OK; [ -f /var/run/reboot-required ] && echo REBOOT_PENDING || echo NO_REBOOT_PENDING; df -h /boot/efi | tail -1'
echo '---apt update (workbench GPG + PPA timeouts EXPECTED COSMETIC)---'
ssh goliath 'sudo apt-get update 2>&1 | tail -10'
echo '---upgradable count (expect 584 ±10)---'
ssh goliath 'apt list --upgradable 2>/dev/null | grep -v ^Listing | wc -l'
echo '---cross-host SG anchors (must be UNCHANGED through cycle)---'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}}"; docker inspect control-garage-beast --format "{{.State.StartedAt}}"; systemctl show -p MainPID -p NRestarts atlas-agent.service'
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service'
echo '---atlas.tasks pre-cycle baseline (cadence reference)---'
ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT count(*) FROM atlas.tasks WHERE created_at > now() - interval '\''1 hour'\'';"'
```

Expected: kernel `6.11.0-1016-nvidia`; SUDO_OK; NO_REBOOT_PENDING; `/boot/efi` >100MB free; upgradable ~584; postgres `2026-05-03T18:38:24.910...`; garage `2026-05-03T18:38:24.493...`; atlas-agent MainPID 4753 NRestarts 0; mercury MainPID 7800; atlas.tasks count ~258 in 1h window.

**STOP if any baseline check fails.** Investigate before proceeding.

#### Stage A -- Pre-patch quiesce + holds

**A.1 Apply hold per Decision B3:**
```bash
ssh goliath 'sudo apt-mark hold docker-compose-plugin && apt-mark showhold'
```
Expected: `docker-compose-plugin set on hold.` then `docker-compose-plugin` listed in showhold output.

**A.2 Quiesce ollama per Decision D2:**
```bash
ssh goliath 'sudo systemctl stop ollama.service && systemctl is-active ollama.service; sudo logger -t paco_patch_cycle2 "ollama.service stopped intentionally for kernel+driver patch reboot; planned interruption window 5-15min"'
```
Expected: `inactive` (or `failed` is acceptable since stop is intentional).

Do NOT touch any other Goliath service. Tailscale, sshd, networking remain up so PD retains remote access.

#### Stage B -- apt-get dist-upgrade (long-running; nohup-to-tmpfile)

**B.1 Launch dist-upgrade in background:**
```bash
ssh goliath 'rm -f /tmp/cycle2_apt.log; nohup sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade > /tmp/cycle2_apt.log 2>&1 & echo "launched PID $!"'
```

**B.2 Poll log every ~60s until completion:**
```bash
ssh goliath 'ls -la /tmp/cycle2_apt.log; tail -3 /tmp/cycle2_apt.log; echo ---; pgrep -af apt-get | head -3'
```
Repeat until `pgrep -af apt-get` returns no process AND the log tail shows the final summary line.

**B.3 Verify dist-upgrade success:**
```bash
ssh goliath 'tail -30 /tmp/cycle2_apt.log; echo ---ERRORS---; grep -E "^(E:|dpkg: error)" /tmp/cycle2_apt.log | head -20; echo ---SUMMARY---; grep -E "upgraded.*newly installed.*to remove" /tmp/cycle2_apt.log | tail -1'
```
Expected summary line: `581 upgraded, 26 newly installed, 2 to remove and 2 not upgraded.` (±5 packages tolerance).
**STOP if any `E:` or `dpkg: error` lines appear.** Run `dpkg --audit` and paco_request with full log.

**B.4 Verify dpkg state clean:**
```bash
ssh goliath 'sudo dpkg --audit; echo $?; sudo dpkg -C; echo $?'
```
Expected: empty output, exit 0 from both. Any half-configured packages → STOP, paco_request.

#### Stage C -- VERIFY-BEFORE-REBOOT (per Decision C2; ABORT gate)

**C.1 Verify new kernel + matching prebuilt modules installed:**
```bash
ssh goliath 'echo ---new kernel image---; dpkg -l linux-image-6.17.0-1014-nvidia 2>/dev/null | tail -1; echo ---new base modules---; dpkg -l linux-modules-6.17.0-1014-nvidia 2>/dev/null | tail -1; echo ---new prebuilt NVIDIA modules---; dpkg -l linux-modules-nvidia-580-open-6.17.0-1014-nvidia 2>/dev/null | tail -1; echo ---new nvidia-fs modules---; dpkg -l linux-modules-nvidia-fs-6.17.0-1014-nvidia 2>/dev/null | tail -1; echo ---new headers---; dpkg -l linux-headers-6.17.0-1014-nvidia 2>/dev/null | tail -1'
```
Expected: every line shows `ii` install state and version `6.17.0-1014.14` (or `6.17.0-1014.14+1000` for prebuilt nvidia modules).
**STOP if any package shows non-`ii` state or is missing.** ABORT, paco_request with output.

**C.2 Verify all 5 NVIDIA .ko module files present in new kernel module tree:**
```bash
ssh goliath 'ls -la /lib/modules/6.17.0-1014-nvidia/kernel/nvidia-580-open/ 2>/dev/null; echo ---; find /lib/modules/6.17.0-1014-nvidia -name "nvidia*.ko*" 2>/dev/null'
```
Expected: 5 files in `/lib/modules/6.17.0-1014-nvidia/kernel/nvidia-580-open/`: `nvidia.ko`, `nvidia-drm.ko`, `nvidia-uvm.ko`, `nvidia-modeset.ko`, `nvidia-peermem.ko` (compressed `.ko.zst` is also acceptable; some Ubuntu kernel pkgs ship compressed). Plus `nvidia-fs.ko*` from the nvidia-fs package.
**STOP if any module missing.** ABORT, paco_request with the find output.

**C.3 Verify docker-compose-plugin hold respected:**
```bash
ssh goliath 'dpkg -l docker-compose-plugin | tail -1; apt-mark showhold'
```
Expected: docker-compose-plugin still at `2.39.1-1~ubuntu.24.04~noble`; hold list still includes docker-compose-plugin.
**STOP if version moved to 5.0.x.** Hold was bypassed; do NOT reboot; paco_request.

**Stage C verify gate is the highest-stakes ABORT point in this directive. Do NOT proceed to Stage D until all three sub-checks pass.**

#### Stage D -- Reboot + recovery wait

```bash
ssh goliath 'echo PRE_REBOOT; uname -r; ls /boot/vmlinuz-* | tail -10; date'
ssh goliath 'sudo systemctl reboot'
echo 'reboot issued; PD waits 300s then polls SSH every 30s for up to 15 min...'
sleep 300
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  ssh -o ConnectTimeout=5 -o BatchMode=yes goliath 'echo POST_REBOOT_OK; uname -r; date' 2>&1 && break || (echo "attempt $i failed; sleeping 30..."; sleep 30);
done
```

Expected: POST_REBOOT_OK; uname-r `6.17.0-1014-nvidia`.

**STOP cycle if Goliath fails to come back within ~15min total.** Do NOT proceed to Stage E. paco_request immediately.

#### Stage E -- Post-reboot verification

**E.1 Kernel + driver + GPU stack:**
```bash
ssh goliath 'echo ---kernel---; uname -r; echo ---nvidia-smi---; nvidia-smi --query-gpu=driver_version,name,memory.total --format=csv; echo ---loaded modules---; lsmod | grep -E "^nvidia" | head -10'
```
Expected: kernel `6.17.0-1014-nvidia`; driver `580.142, NVIDIA GB10, ~131072 MiB` (driver version moved from 580.95.05 to 580.142); 5+ nvidia modules loaded.

**E.2 CUDA toolkit:**
```bash
ssh goliath '/usr/local/cuda/bin/nvcc --version | tail -2; ls -la /usr/local/cuda /usr/local/cuda-13'
```
Expected: nvcc version `release 13.0` with build `V13.0.96` or `V13.0.103` (the 13.0.0 → 13.0.3 bump); symlink chain intact.

**E.3 Container runtime:**
```bash
ssh goliath 'systemctl is-active docker.service containerd.service; docker version --format "server {{.Server.Version}} / containerd {{range .Server.Components}}{{if eq .Name \"containerd\"}}{{.Version}}{{end}}{{end}}"; dpkg -l docker-compose-plugin | tail -1'
```
Expected: docker + containerd active; server `29.2.1` / containerd `2.2.1`; docker-compose-plugin still `2.39.1` (hold respected through patch+reboot).

**E.4 Ollama auto-start + inference probe + model integrity:**
```bash
ssh goliath 'systemctl is-enabled ollama.service; systemctl is-active ollama.service'
```
If `is-active` returns `inactive`, start manually: `ssh goliath 'sudo systemctl start ollama.service'`.

Then verify models + run a quick inference probe:
```bash
ssh goliath '/usr/local/bin/ollama list; echo ---inference probe---; timeout 60 /usr/local/bin/ollama run qwen2.5:72b "Reply with the single word: PONG" 2>&1 | head -5'
```
Expected: 3 models listed (qwen2.5:72b, deepseek-r1:70b, llama3.1:70b) with same IDs as preflight; inference probe returns a response containing `PONG` within ~60s (model load may take 30-45s on first invocation post-reboot).

If inference probe times out or errors: PD captures the exact error and journalctl tail (`journalctl -u ollama.service --since "10 min ago" | tail -50`), then paco_request. Do NOT consider cycle accepted until inference works.

**E.5 Tailscale + sshd verification:**
```bash
ssh goliath 'tailscale status --self=true | head -2; tailscale version; systemctl is-active sshd.service'
```
Expected: sloan4 active; tailscale 1.96.4 (or whatever); sshd active.

#### Stage F -- Spot SG snapshot (per Decision E2; review-file-only, NOT canon)

```bash
echo '---Goliath spot service inventory POST-CYCLE-2---'
ssh goliath 'systemctl list-units --type=service --state=active --no-pager 2>/dev/null | head -50'
echo '---Goliath GPU + driver + CUDA POST---'
ssh goliath 'nvidia-smi --query-gpu=driver_version,name,memory.total,memory.used --format=csv; /usr/local/cuda/bin/nvcc --version | tail -2'
echo '---Goliath docker daemon POST---'
ssh goliath 'docker version --format "{{.Server.Version}} containerd {{range .Server.Components}}{{if eq .Name \"containerd\"}}{{.Version}}{{end}}{{end}}"; dpkg -l docker-compose-plugin | tail -1'
echo '---Goliath ollama POST + new MainPID---'
ssh goliath 'systemctl show -p MainPID -p ActiveEnterTimestamp -p NRestarts ollama.service; /usr/local/bin/ollama list'
```

Capture all output for the review file. **Do NOT propose canon SG additions for these.** Spot snapshot only.

#### Cross-host stability check (canon SGs MUST be unchanged)

```bash
echo '---Beast SG2 postgres anchor (MUST be UNCHANGED 2026-05-03T18:38:24.910...)---'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
echo '---Beast SG3 garage anchor (MUST be UNCHANGED 2026-05-03T18:38:24.493...)---'
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
echo '---Beast SG4 atlas-mcp (MUST be UNCHANGED MainPID 1212)---'
ssh beast 'systemctl show -p MainPID -p ActiveState atlas-mcp.service'
echo '---Beast SG5 atlas-agent (MUST be UNCHANGED MainPID 4753 NRestarts 0)---'
ssh beast 'systemctl show -p MainPID -p NRestarts -p ActiveState -p UnitFileState atlas-agent.service'
echo '---CK SG6 mercury-scanner (MUST be UNCHANGED MainPID 7800)---'
ssh ciscokid 'systemctl show -p MainPID -p ActiveState mercury-scanner.service'
echo '---atlas.tasks growth across cycle (cadence ~258/hour expected)---'
ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT count(*) FROM atlas.tasks WHERE created_at > now() - interval '\''2 hours'\'';"'
```

**Cycle 2 acceptance requires ALL canon SG values bit-identical to pre-cycle.** Goliath cycle perturbing Beast or CK = scope violation = paco_request.

#### Pre-commit secrets-scan + commit + push

```bash
cd /home/jes/control-plane && \
  grep -niE 'adminpass|api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+|password.{0,3}=' docs/paco_review_homelab_patch_cycle2_cve_2026_31431.md | head -10 || echo 'tightened: clean'
```

If clean → commit + push.

#### Write `docs/paco_review_homelab_patch_cycle2_cve_2026_31431.md`

Follow Cycle 1 review structure. Sections:
- 0: Verified-live (PRE + POST blocks; Goliath spot inventory + cross-host SG anchors)
- 1: TL;DR (Goliath kernel 6.11→6.17 + driver 580.95.05→580.142 + cuda 13.0.0→13.0.3 + docker 28.3.3→29.2.1 + containerd 1.7.26→2.2.1; held compose-plugin v5; reboot recovery time = X minutes; ollama inference probe PASS; cross-host SGs bit-identical)
- 2: Per-stage walk-through (A through F)
- 3: Acceptance per stage
- 4: Spot Goliath snapshot (NOT canon SG)
- 5: Reboot recovery time + ollama-stop-to-first-inference quantified
- 6: Cross-host stability evidence (postgres/garage/atlas-mcp/atlas-agent/mercury all unchanged)
- 7: Asks for Paco (close-confirm + Cycle 3 GO KaliPi/Pi3 OR pause + workbench GPG remediation queued? + docker-compose-plugin v5 verification queued? + Goliath SG canonization for v0.1.1?)

#### Notification line in `docs/handoff_pd_to_paco.md`

> Paco, PD finished homelab patch cycle 2. Goliath kernel 6.11.0-1016-nvidia→6.17.0-1014-nvidia + NVIDIA driver 580.95.05→580.142 + cuda 13.0.0→13.0.3 + docker 28.3.3→29.2.1 + containerd 1.7.26→2.2.1; docker-compose-plugin held at 2.39.1 (v5 jump banked); reboot recovery = X min; ollama inference probe PASS (3 models intact); cross-host SGs bit-identical; control-plane HEAD `<hash>`. Review: `docs/paco_review_homelab_patch_cycle2_cve_2026_31431.md`. Check handoff.

---

## 3. Acceptance criteria (Cycle 2)

1. Goliath kernel `6.17.0-1014-nvidia` running post-reboot (was `6.11.0-1016-nvidia`).
2. nvidia-smi reports driver `580.142` on `NVIDIA GB10` with ~131GB memory total (was driver `580.95.05`).
3. `/usr/local/cuda/bin/nvcc --version` reports release `13.0` with build `V13.0.96` or higher (was `V13.0.88`).
4. `docker version` server `29.2.1` / containerd `2.2.1` (was `28.3.3` / `1.7.26`); docker.service + containerd.service active.
5. `dpkg -l docker-compose-plugin` shows `2.39.1-1~ubuntu.24.04~noble` (held; v5.0.2 NOT installed).
6. `ollama.service` active; `/usr/local/bin/ollama list` shows 3 models intact (qwen2.5:72b, deepseek-r1:70b, llama3.1:70b) with same IDs as preflight.
7. Inference probe via `ollama run qwen2.5:72b "Reply with the single word: PONG"` returns a response containing `PONG` within 60s.
8. Stage C verify-before-reboot ABORT gate ran AND passed (or did not run because earlier stage failed cleanly without reaching it). NEVER ran-but-bypassed; NEVER reboot-without-verify.
9. dpkg state clean post-cycle (`dpkg --audit` empty, `dpkg -C` empty, exit 0).
10. Workbench GPG warning + 3 PPA timeouts treated as cosmetic per Decisions A3/(b). PD did NOT modify workbench `.sources`, did NOT import keys, did NOT investigate PPA reachability.
11. Cross-host SG anchors **bit-identical** to pre-cycle:
    - Beast SG2 postgres `2026-05-03T18:38:24.910689151Z`
    - Beast SG3 garage `2026-05-03T18:38:24.493238903Z`
    - Beast SG4 atlas-mcp MainPID `1212`
    - Beast SG5 atlas-agent MainPID `4753` NRestarts `0` active enabled
    - CK SG6 mercury MainPID `7800`
12. atlas.tasks count growing across cycle at cadence within ±25% of pre-cycle ~258/hour (atlas-agent observation continuity preserved on Beast).
13. Reboot recovery window quantified: time from `systemctl reboot` issue to first successful SSH + uname-r confirmation captured in review section 5. Time from `systemctl stop ollama.service` to first successful inference probe also captured (this is the maintenance-window-flip metric analogous to Cycle 1's atlas-agent gap).
14. Pre-commit secrets-scan BOTH layers clean on review file; commit + push successful.

---

## 4. Trigger from CEO to PD (Cowork prompt)

```
You are PD (Cowork) for Santigrey Enterprises. Paco (COO) has dispatched homelab patch cycle 2 (CVE-2026-31431; Goliath dedicated -- DGX Spark + NVIDIA GB10 + major kernel jump 6.11→6.17 + driver 580.95.05→580.142 + containerd 1→2 + 584-package dist-upgrade with verify-before-reboot ABORT gate).

Repo:
- santigrey/control-plane at /home/jes/control-plane on CK (HEAD <commit_hash> or later). Read directive + write paco_review here.

Read in order:
1. /home/jes/control-plane/docs/paco_directive_homelab_patch_cycle2_cve_2026_31431.md (your authority)
2. /home/jes/control-plane/docs/feedback_paco_pre_directive_verification.md (P6 standing rules through #37; SRs through #7)
3. /home/jes/control-plane/docs/paco_response_homelab_patch_cycle1_close_confirm.md (Cycle 1 close + new SG canonical baseline; Path B B1+B2 patterns reusable)
4. /home/jes/control-plane/docs/paco_directive_homelab_patch_cycle1_cve_2026_31431.md (template; Cycle 1 directive your prior-art reference for stage discipline)

Execute Stages Pre-flight → A → B → C → D → E → F + Cross-host stability check per directive section 2.2. ONE STAGE AT A TIME; verify gate before next.

**Stage C is the verify-before-reboot ABORT gate.** If any of C.1/C.2/C.3 fails, STOP, write paco_request_homelab_patch_cycle2_<topic>.md, do NOT issue reboot. Booting into the new kernel without matching prebuilt NVIDIA modules takes Goliath off line.

If any other stage fails: STOP, write paco_request_homelab_patch_cycle2_<topic>.md, do not proceed.

Out of scope this cycle: SlimJim/Beast/CK (already patched Cycle 1), KaliPi/Pi3 (queued Cycle 3), workbench repo (Decision A3), docker-compose-plugin v5 (held per Decision B3).

Begin with Pre-flight per directive section 2.2.
```

-- Paco
