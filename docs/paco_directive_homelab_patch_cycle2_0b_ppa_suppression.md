# Paco Directive — Homelab Patch Cycle 2.0b: PPA Suppression + Goliath Kernel 6.17 Upgrade

**Authored:** 2026-05-05 ~01:55Z UTC (2026-05-04 ~19:55 MT)
**By:** Paco (COO)
**For:** PD (Engineering Head, Cowork)
**Scope:** Goliath only (single-node kernel + driver + selected userspace upgrade)
**Supersedes:** original Cycle 2.0b plan ("hold for lpc recovery") — that strategy is abandoned in favor of PPA suppression based on new ground truth that all four "PPA-only" packages are mirrored in `noble-updates/restricted` and `noble-security/restricted`.

---

## 0. VERIFIED-LIVE BLOCK (Paco; 2026-05-05 ~01:55Z UTC)

Ground truth confirmed via MCP probes against Goliath at session start:

- **Goliath kernel:** `6.11.0-1016-nvidia` (UNCHANGED from pre-Cycle-2 baseline; CVE-2026-31431 unpatched)
- **Goliath driver:** `nvidia-driver-580-open` `580.95.05-0ubuntu0.24.04.2` (noble-updates source)
- **Goliath modules installed:** `linux-modules-nvidia-580-open-6.11.0-1016-nvidia` `6.11.0-1016.16+1000` (PPA-suffixed; legacy)
- **Goliath modules meta:** `linux-modules-nvidia-580-open-nvidia-hwe-24.04` `6.11.0-1016.16+1000`
- **lpc state:** `ppa.launchpadcontent.net` TCP/443 FAIL (day 6 of outage; `lp=PASS` asymmetric continues)
- **noble-updates state:** `ports.ubuntu.com` reachable; primary Canonical archive UP throughout outage
- **Probe loop:** Goliath PID 59800 alive at /home/jes/cycle2_0a/probe_loop.sh (will be killed on Stage A success — outage no longer relevant once we route around it)
- **Standing gates 6/6 holding bit-identical:**
  - atlas-mcp.service MainPID=1212 NRestarts=0 active (Beast)
  - atlas-agent.service MainPID=4753 NRestarts=0 active (Beast)
  - mercury-scanner.service MainPID=7800 active (CK)
  - postgres-beast StartedAt=`2026-05-03T18:38:24.910689151Z` restart=0
  - garage-beast StartedAt=`2026-05-03T18:38:24.493238903Z` restart=0
  - atlas .env on Beast: empty mode 0600 jes:jes
- **HEADs:** control-plane `3137c90` / atlas `c28310b`
- **Package availability verified via apt-cache policy on Goliath:**
  - `linux-image-6.17.0-1014-nvidia` `6.17.0-1014.14` available in `noble-updates/main` AND `noble-security/main` (also lpc; lpc UNREACHABLE)
  - `linux-modules-nvidia-580-open-6.17.0-1014-nvidia` `6.17.0-1014.14+1` in `noble-updates/restricted`; `6.17.0-1014.14` (no suffix) in `noble-security/restricted`; `+1000` only on lpc
  - `linux-modules-nvidia-580-open-nvidia-hwe-24.04` same triplet of variants
  - `libvulkan1` available in `noble/main` (ports.ubuntu.com)
  - `wpasupplicant` available in `noble-updates/main` AND `noble-security/main` (ports.ubuntu.com)

---

## 1. MISSION

Patch Goliath kernel + NVIDIA modules to close CVE-2026-31431 by routing around the lpc outage entirely. Switch the apt-resolution path from `canonical-nvidia` PPA (`+1000` suffix builds) to Canonical's `noble-updates`/`noble-security` archives (`+1` suffix or unsuffixed builds). Reboot into kernel `6.17.0-1014-nvidia`. Verify GPU + ollama inference. Pin `canonical-nvidia` low priority post-success so the system doesn't auto-revert when lpc recovers.

Fleet patch state at success: 7/7 nodes patched on CVE-2026-31431.

---

## 2. SCOPE

**In-scope (single-node, Goliath only):**
- Disable `canonical-nvidia` apt sources temporarily
- `apt-get update` + `apt-get -y install` to upgrade kernel, NVIDIA modules, libvulkan1, wpasupplicant from noble-updates/security
- Reboot into kernel `6.17.0-1014-nvidia`
- Verify nvidia-smi + all 3 ollama models inferable
- Re-enable `canonical-nvidia` sources but pin Pin-Priority: 100 (low; non-default)

**Out-of-scope (deferred to follow-on cycles per anchor pending priorities):**
- P6 #48 /tmp cleanup mechanism investigation (deferred)
- P6 #49 headless snap pre-removal (deferred)
- apt-get autoremove sweep (deferred; usually run post-2.0b)
- Other fleet nodes (already patched in Cycle 1+3)

---

## 3. PRE-FLIGHT PROBES (PF.1–PF.10; ALL MUST PASS BEFORE STAGE A)

PD runs each probe and records output. If any FAIL, halt + escalate to Paco.

```bash
# PF.1 — control-plane HEAD unchanged from authoring time
ssh ciscokid 'cd /home/jes/control-plane && git log --oneline -1'
# expect: 3137c90 (or newer if anchor updates landed in interim — verify with Paco if drifted)

# PF.2 — atlas HEAD unchanged
ssh beast 'cd /home/jes/atlas && git log --oneline -1'
# expect: c28310b

# PF.3 — standing gates 6/6 bit-identical
ssh beast 'systemctl show -p MainPID -p NRestarts -p ActiveState atlas-mcp.service atlas-agent.service'
# expect: MainPID=1212 NRestarts=0 active (atlas-mcp) and MainPID=4753 NRestarts=0 active (atlas-agent)
ssh ciscokid 'systemctl show -p MainPID -p ActiveState mercury-scanner.service'
# expect: MainPID=7800 active
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
# expect: 2026-05-03T18:38:24.910689151Z restart=0
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} restart={{.RestartCount}}"'
# expect: 2026-05-03T18:38:24.493238903Z restart=0
ssh beast 'stat -c "%n %s %a %U:%G" /home/jes/atlas/.env'
# expect: /home/jes/atlas/.env 0 600 jes:jes

# PF.4 — Goliath reachable + current kernel/driver state
ssh goliath 'uname -r && nvidia-smi --query-gpu=driver_version --format=csv,noheader'
# expect: 6.11.0-1016-nvidia and 580.95.05

# PF.5 — ollama active + 3 models present
ssh goliath 'systemctl is-active ollama && ollama list | awk "NR>1 {print \$1}"'
# expect: active and qwen2.5:72b + deepseek-r1:70b + llama3.1:70b (in some order)

# PF.6 — lpc still down (sanity; expected FAIL means we're routing around correctly)
ssh goliath 'timeout 5 bash -c "</dev/tcp/ppa.launchpadcontent.net/443" && echo lpc=PASS || echo lpc=FAIL'
# expect: lpc=FAIL (if PASS, the outage has recovered and we can decide to proceed with PPA suppression anyway or revert to original PPA path — escalate to Paco for ratification)

# PF.7 — ports.ubuntu.com reachable from Goliath
ssh goliath 'timeout 5 bash -c "</dev/tcp/ports.ubuntu.com/443" && echo ports=PASS || echo ports=FAIL'
# expect: ports=PASS

# PF.8 — canonical-nvidia source files inventory (where they live + format)
ssh goliath 'ls -la /etc/apt/sources.list.d/ | grep -iE "nvidia|canonical-nvidia"'
# expect: at least one .list or .sources file matching canonical-nvidia
# (record exact filenames; needed for Stage A)

# PF.9 — dpkg state clean pre-cycle
ssh goliath 'sudo dpkg --audit; sudo dpkg -C; echo audit_exit=$?'
# expect: empty stdout, audit_exit=0

# PF.10 — disk space on Goliath / and /boot
ssh goliath 'df -h / /boot'
# expect: / has >5GB free, /boot has >500MB free
# (kernel + modules install ~300MB total; /boot needs ~100MB for vmlinuz+initramfs)
```

**GATE:** All PF.1–PF.10 PASS → proceed to Stage A. Any FAIL → halt + paco_request.

---

## 4. STAGE A — PREPARATION

### A.1 — Backup canonical-nvidia source files (rollback path preservation)

```bash
ssh goliath 'sudo bash -c "
  set -euo pipefail
  mkdir -p /root/cycle2_0b_backups
  for f in /etc/apt/sources.list.d/*canonical-nvidia*.list /etc/apt/sources.list.d/*canonical-nvidia*.sources; do
    [ -f \"\$f\" ] && cp -a \"\$f\" /root/cycle2_0b_backups/ || true
  done
  ls -la /root/cycle2_0b_backups/
"'
```

**Expected:** at least one file backed up; ls shows the files in `/root/cycle2_0b_backups/`.

### A.2 — Stop ollama service (graceful pre-upgrade)

```bash
ssh goliath 'sudo systemctl stop ollama && sleep 2 && systemctl is-active ollama'
```

**Expected:** `inactive` (intentional stop pre-cycle).

### A.3 — Disable canonical-nvidia source files (rename to .disabled)

```bash
ssh goliath 'sudo bash -c "
  set -euo pipefail
  for f in /etc/apt/sources.list.d/*canonical-nvidia*.list /etc/apt/sources.list.d/*canonical-nvidia*.sources; do
    if [ -f \"\$f\" ]; then
      mv \"\$f\" \"\${f}.disabled\"
      echo \"disabled: \$f\"
    fi
  done
  ls -la /etc/apt/sources.list.d/ | grep -iE \"canonical-nvidia\"
"'
```

**Expected:** at least one file renamed; `ls` post-rename shows only `*.disabled` variants of canonical-nvidia entries; no active `.list` or `.sources` for canonical-nvidia.

### A.4 — apt-get update with PPA disabled (must succeed; zero lpc references in fetch)

```bash
ssh goliath 'sudo apt-get update 2>&1 | tee /tmp/cycle2_0b_apt_update.log'
ssh goliath 'grep -c "ppa.launchpadcontent.net" /tmp/cycle2_0b_apt_update.log'
```

**Expected:** apt-get update exit 0; grep for `ppa.launchpadcontent.net` returns `0` (zero references).

### A.5 — apt-get install simulation (capture full plan)

```bash
ssh goliath 'sudo apt-get -y --simulate install \
  linux-image-6.17.0-1014-nvidia \
  linux-headers-6.17.0-1014-nvidia \
  linux-modules-nvidia-580-open-6.17.0-1014-nvidia \
  linux-modules-nvidia-580-open-nvidia-hwe-24.04 \
  linux-nvidia-hwe-24.04 \
  libvulkan1 \
  wpasupplicant \
  2>&1 | tee /tmp/cycle2_0b_apt_simulate.log'
```

**Expected:** simulation completes exit 0; log captured for gate-checks A.6–A.8.

### A.6 — GATE: zero lpc references in simulation plan

```bash
ssh goliath 'grep -c "ppa.launchpadcontent.net" /tmp/cycle2_0b_apt_simulate.log'
```

**Expected:** `0` (zero references). If non-zero → HALT (H1 trigger).

### A.7 — GATE: no `+1000` PPA module versions in simulation

```bash
ssh goliath 'grep -E "\+1000" /tmp/cycle2_0b_apt_simulate.log | grep -E "linux-modules-nvidia" || echo "clean: no +1000 modules"'
```

**Expected:** output `clean: no +1000 modules`. If `+1000` modules appear → HALT (H1 trigger).

### A.8 — GATE: simulation scope matches expected package set

```bash
ssh goliath 'grep -E "^(Inst|Conf|Remv) " /tmp/cycle2_0b_apt_simulate.log | wc -l'
ssh goliath 'grep -E "^Inst " /tmp/cycle2_0b_apt_simulate.log | head -30'
```

**Expected:** Inst count between 5 and 25 (kernel + 6 explicit + dependencies; sanity bound). Inst lines should show `linux-image-6.17.0-1014-nvidia`, `linux-modules-nvidia-580-open-6.17.0-1014-nvidia`, `linux-modules-nvidia-580-open-nvidia-hwe-24.04`, `linux-nvidia-hwe-24.04`, `libvulkan1`, `wpasupplicant`, `linux-headers-6.17.0-1014-nvidia`. If Inst count > 25, escalate (unexpected dependency drag); if < 5, escalate (incomplete plan).

**GATE:** A.6, A.7, A.8 all PASS → proceed to Stage B. Any FAIL → halt + paco_request.

---

## 5. STAGE B — EXECUTION

### B.1 — apt-get install (commit the simulated plan)

```bash
ssh goliath 'cd /home/jes/cycle2_0b && sudo bash -c "
  mkdir -p /home/jes/cycle2_0b
  cd /home/jes/cycle2_0b
  apt-get -y install \
    linux-image-6.17.0-1014-nvidia \
    linux-headers-6.17.0-1014-nvidia \
    linux-modules-nvidia-580-open-6.17.0-1014-nvidia \
    linux-modules-nvidia-580-open-nvidia-hwe-24.04 \
    linux-nvidia-hwe-24.04 \
    libvulkan1 \
    wpasupplicant \
    2>&1 | tee /home/jes/cycle2_0b/apt_install.log
"'
```

**Expected:** apt exit 0; log shows packages installed without lpc errors.

**Note:** sudo creates `/home/jes/cycle2_0b/` as root-owned if `mkdir -p` runs under sudo. Adapt under B0/SR #9 if needed (e.g. pre-create as `jes` then sudo apt-get inside).

### B.2 — dpkg state clean post-install

```bash
ssh goliath 'sudo dpkg --audit; sudo dpkg -C; echo audit_exit=$?'
```

**Expected:** empty stdout, audit_exit=0.

### B.3 — verify new kernel installed but not yet booted

```bash
ssh goliath 'dpkg -l linux-image-6.17.0-1014-nvidia linux-modules-nvidia-580-open-6.17.0-1014-nvidia | tail -5'
ssh goliath 'ls /boot/vmlinuz-6.17.0-1014-nvidia /boot/initrd.img-6.17.0-1014-nvidia 2>&1'
ssh goliath 'uname -r'  # still expect 6.11 (not booted yet)
```

**Expected:** dpkg shows `ii` for both packages; vmlinuz + initrd present in /boot; uname still `6.11.0-1016-nvidia`.

### B.4 — verify GRUB will default to 6.17 on next boot

```bash
ssh goliath 'sudo grub-mkconfig -o /tmp/grub.cfg.preview 2>&1 | tail -10'
ssh goliath 'grep -E "menuentry .*(6.17.0-1014-nvidia|6.11.0-1016-nvidia)" /tmp/grub.cfg.preview | head -5'
```

**Expected:** preview shows menuentries for both 6.17 and 6.11; first menuentry should be 6.17 (default).

**GATE:** B.1–B.4 all PASS → proceed to Stage C. Any FAIL → ROLLBACK (see §10).

---

## 6. STAGE C — REBOOT + VERIFY

### C.1 — Issue reboot (background; SSH will drop)

```bash
ssh goliath 'sudo systemctl reboot' &
# Connection will drop; that's expected. Capture timestamp.
T_REBOOT_ISSUED=$(date -u +%FT%TZ)
echo "reboot issued at: $T_REBOOT_ISSUED"
```

### C.2 — Wait for SSH return (5 min cap)

```bash
# Poll Goliath SSH every 15s up to 20 attempts (5 min wall)
for i in $(seq 1 20); do
  sleep 15
  if ssh -o ConnectTimeout=5 -o BatchMode=yes goliath 'echo back && date -u' 2>/dev/null; then
    echo "Goliath returned at attempt $i ($((i*15))s)"
    break
  fi
  echo "attempt $i ($((i*15))s): no response"
done
```

**Expected:** Goliath returns SSH within 5 min. If not → HALT (H5 trigger; CEO physical access likely needed).

### C.3 — verify booted kernel

```bash
ssh goliath 'uname -r'
```

**Expected:** `6.17.0-1014-nvidia`. If still `6.11.0-1016-nvidia` → HALT (kernel didn't boot; investigate GRUB default).

### C.4 — verify nvidia-smi works

```bash
ssh goliath 'nvidia-smi'
ssh goliath 'nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader'
```

**Expected:** nvidia-smi exit 0; reports GB10 GPU, driver `580.x` (likely `580.142` from noble-updates), 128GB unified memory. If exit non-zero or no GPU → HALT (H3).

### C.5 — verify modules loaded

```bash
ssh goliath 'lsmod | grep -E "^nvidia"'
```

**Expected:** nvidia, nvidia_uvm, nvidia_modeset modules listed.

### C.6 — restart ollama service

```bash
ssh goliath 'sudo systemctl start ollama && sleep 5 && systemctl is-active ollama'
```

**Expected:** `active`.

### C.7 — ollama smoke test (3 models)

```bash
ssh goliath 'ollama list'
ssh goliath 'curl -sS http://127.0.0.1:11434/api/generate -d "{\"model\": \"qwen2.5:72b\", \"prompt\": \"Say HELLO and stop.\", \"stream\": false}" | head -c 500'
ssh goliath 'curl -sS http://127.0.0.1:11434/api/generate -d "{\"model\": \"llama3.1:70b\", \"prompt\": \"Say HELLO and stop.\", \"stream\": false}" | head -c 500'
ssh goliath 'curl -sS http://127.0.0.1:11434/api/generate -d "{\"model\": \"deepseek-r1:70b\", \"prompt\": \"Say HELLO and stop.\", \"stream\": false}" | head -c 500'
```

**Expected:** each curl returns JSON with non-empty `response` field within 30s. If any model fails → HALT (H4).

**GATE:** C.1–C.7 all PASS → proceed to Stage D. Any FAIL → ROLLBACK (see §10).

---

## 7. STAGE D — PPA RE-ENABLE WITH LOW PRIORITY PIN

### D.1 — Re-enable canonical-nvidia source files

```bash
ssh goliath 'sudo bash -c "
  set -euo pipefail
  for f in /etc/apt/sources.list.d/*canonical-nvidia*.disabled; do
    [ -f \"\$f\" ] && mv \"\$f\" \"\${f%.disabled}\" || true
  done
  ls -la /etc/apt/sources.list.d/ | grep -iE \"canonical-nvidia\"
"'
```

**Expected:** files renamed back from `.disabled` to original; `ls` shows them active again.

### D.2 — Write apt preferences pin (canonical-nvidia priority 100)

```bash
ssh goliath 'sudo bash -c "cat > /etc/apt/preferences.d/canonical-nvidia-low-priority << \"EOF\"
Package: *
Pin: release o=LP-PPA-canonical-nvidia-nvidia-desktop-edge
Pin-Priority: 100
EOF
chmod 0644 /etc/apt/preferences.d/canonical-nvidia-low-priority
cat /etc/apt/preferences.d/canonical-nvidia-low-priority
"'
```

**Expected:** file exists, mode 0644, contents match input. (Note: if PPA name differs from `canonical-nvidia-nvidia-desktop-edge`, PD adapts the `Pin: release o=` value under B0/SR #9 based on actual `apt-cache policy` output — see B7 below.)

### D.3 — apt-get update with pin in place

```bash
ssh goliath 'sudo apt-get update 2>&1 | tail -20'
```

**Expected:** exit 0; lpc still FAIL since outage continues, but pin file in place for when it returns.

### D.4 — Verify pin took effect

```bash
ssh goliath 'apt-cache policy linux-modules-nvidia-580-open-nvidia-hwe-24.04 | head -10'
```

**Expected:** `+1` or unsuffixed at priority 500; `+1000` (when reachable) at priority 100.

### D.5 — Restart probe loop kill + cleanup

```bash
ssh goliath 'kill 59800 2>/dev/null && echo killed || echo "already gone"'
ssh goliath 'ls -la /home/jes/cycle2_0a/ /home/jes/cycle2_0b/ 2>/dev/null | tail -30'
```

**Expected:** PID 59800 killed (or already gone); directories list cleanly. `/home/jes/cycle2_0a/` may be archived or kept for reference.

---

## 8. ACCEPTANCE CRITERIA

### MUST-PASS (cycle FAILS if any fails)

- **AC.1** — Stage A.6 GATE PASS: simulation log shows zero `ppa.launchpadcontent.net` URLs
- **AC.2** — Stage A.7 GATE PASS: zero `+1000`-suffix module versions in simulation plan
- **AC.3** — Stage B.2 PASS: dpkg --audit + dpkg -C exit 0 post-install
- **AC.4** — Stage B.3 PASS: `linux-image-6.17.0-1014-nvidia` in `ii` state; vmlinuz + initrd present in /boot
- **AC.5** — Stage C.3 PASS: post-reboot `uname -r` returns `6.17.0-1014-nvidia`
- **AC.6** — Stage C.4 PASS: nvidia-smi exit 0, reports GB10, driver 580.x
- **AC.7** — Stage C.7 PASS: qwen2.5:72b returns non-empty JSON `response` field within 30s
- **AC.8** — Stage C.7 PASS: llama3.1:70b returns non-empty JSON `response` field within 30s
- **AC.9** — Stage C.7 PASS: deepseek-r1:70b returns non-empty JSON `response` field within 30s
- **AC.10** — Stage D.4 PASS: apt-cache policy shows `+1000` versions at priority 100, `+1`/unsuffixed at priority 500
- **AC.11** — Standing gates 6/6 bit-identical pre/mid/post (same five values from PF.3 unchanged across cycle)
- **AC.12** — control-plane HEAD `3137c90` no drift during cycle (verify pre + post identical)
- **AC.13** — atlas HEAD `c28310b` no drift during cycle

### SHOULD-PASS (informational; non-blocking)

- **AS.1** — Reboot wall (C.1 issued → C.3 SSH return) < 5 min
- **AS.2** — Total cycle wall (PF.1 → D.5) < 90 min
- **AS.3** — ollama restart-to-first-inference (C.6 active → C.7 first response) < 60s
- **AS.4** — atlas.tasks cadence post-cycle within ±25% of pre-cycle baseline (~250/hr expected)
- **AS.5** — Stage A.8 dependency chain Inst count between 7 and 20 (right-sized scope; outside this range is informational concern, not blocking)

---

## 9. PATH B ADAPTATIONS (PD discretion under SR #9 / B0 standing-meta-authority)

Pre-authorized adaptations (PD applies, documents in review):

- **B1** — `.list` vs `.sources` file format variation: handle both filename patterns in A.1, A.3, D.1
- **B2** — apt-get update may require `--allow-releaseinfo-change` after PPA suspend; auto-add if needed
- **B3** — Additional dependencies pulled by `linux-nvidia-hwe-24.04` meta upgrade are pre-authorized PROVIDED all resolve to noble-updates/security and zero `+1000` modules (Stage A.7 enforces)
- **B4** — `linux-headers-*-nvidia` and similar transitive dependencies are expected; proceed
- **B5** — Driver micro-version may bump `580.95.05` → `580.142` via the upgrade path; this is acceptable and expected (noble-updates ships `580.142-0ubuntu0.24.04.1`)
- **B6** — If `systemctl reboot` doesn't trigger cleanly, fall back to `shutdown -r now` or `reboot -f`
- **B7** — If `apt-cache policy` shows the canonical-nvidia PPA `release o=` field as something other than `LP-PPA-canonical-nvidia-nvidia-desktop-edge` (e.g. `LP-PPA-canonical-nvidia-nvidia-desktop`), PD adapts the Pin value in D.2 to match actual policy output
- **B8** — `/home/jes/cycle2_0b` directory creation: pre-create as `jes` user before sudo apt-get install runs, so log files have proper ownership; if PD prefers root ownership for parity with `/home/jes/cycle2_0a/`, that's also acceptable

Non-authorized halt conditions (PD escalates to Paco via paco_request):

- **H1** — `+1000` PPA module appears in apt-get install simulation (Stage A.6/A.7)
- **H2** — dpkg state non-clean after Stage B (broken install)
- **H3** — After reboot, kernel boots but `nvidia-smi` exits non-zero or no GPU detected
- **H4** — After reboot, ollama can't serve any of the 3 models within 60s
- **H5** — SSH doesn't return within 5 min of reboot (likely needs CEO physical access to Goliath)
- **H6** — Standing gate value changes during cycle (atlas-mcp/agent NRestarts moves, mercury PID changes, postgres/garage StartedAt changes, atlas .env mode changes)
- **H7** — Any /boot file checksum or size anomaly that suggests partial install
- **H8** — `apt-cache policy` for any of the 7 explicit packages shows ZERO non-PPA candidates available (ports.ubuntu.com unavailable; if ports.ubuntu.com is also down, the cycle premise collapses)

---

## 10. ROLLBACK PROCEDURE

### Rollback path 1: failure between Stage A.3 and Stage A.8 (PPA disabled but no install yet)

```bash
# Re-enable PPA
ssh goliath 'sudo bash -c "
  for f in /etc/apt/sources.list.d/*canonical-nvidia*.disabled; do
    [ -f \"\$f\" ] && mv \"\$f\" \"\${f%.disabled}\" || true
  done
"'
ssh goliath 'sudo apt-get update'
ssh goliath 'sudo systemctl start ollama'
# Goliath is back to pre-cycle state
```

### Rollback path 2: Stage B failed before reboot

```bash
# dpkg state may be inconsistent; try to repair first
ssh goliath 'sudo apt-get -y -f install'
ssh goliath 'sudo dpkg --configure -a'
ssh goliath 'sudo apt-get -y install \
  linux-image-6.11.0-1016-nvidia=6.11.0-1016.16+1000 \
  linux-modules-nvidia-580-open-6.11.0-1016-nvidia=6.11.0-1016.16+1000 \
  linux-modules-nvidia-580-open-nvidia-hwe-24.04=6.11.0-1016.16+1000 \
  --reinstall'
# Re-enable PPA per Path 1
```

**Note:** the `+1000` reinstall may fail if lpc is still down. Fallback: install matching versions from noble-updates without strict `=` pin.

### Rollback path 3: 6.17 boot fails or kernel/driver issues post-reboot (Stage C failed)

**Goliath ALREADY HAS 6.11 installed** — kernel `6.11.0-1016-nvidia` is still on disk in /boot; only the GRUB default changed. To rollback:

```bash
# Option A: select 6.11 from GRUB advanced options at boot (requires console access)
# At GRUB menu: Advanced options for Ubuntu → 6.11.0-1016-nvidia (recovery or normal)

# Option B: from running 6.17 (if SSH works but driver doesn't), set GRUB default and reboot:
ssh goliath 'sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.11.0-1016-nvidia"'
ssh goliath 'sudo update-grub'
ssh goliath 'sudo systemctl reboot'
# Wait for SSH return; verify uname -r = 6.11.0-1016-nvidia

# Option C: physical console access; select 6.11 from GRUB advanced options
```

**After rollback to 6.11:** investigate why 6.17 failed before retrying. Likely candidates: driver-kernel ABI mismatch, modules didn't get installed properly, GRUB config issue.

---

## 11. CLOSE-CONFIRM ARTIFACT REQUIREMENTS

PD produces `docs/paco_review_homelab_patch_cycle2_0b_ppa_suppression.md` containing:

1. Verified-live snapshot at start (PF.1–PF.10 outputs)
2. Stage-by-stage execution log with timestamps (UTC) for each step
3. All 13 MUST-PASS AC outcomes (PASS/FAIL with evidence)
4. All 5 SHOULD-PASS AS outcomes (PASS/FAIL with timing data)
5. Standing gates 6/6 pre/mid/post (3 sentinel probes; bit-identical confirmed)
6. HEADs pre/post for control-plane + atlas
7. Any B# adaptations applied (B1–B8) with justification + actual divergence captured
8. Any P6 candidate findings (numbered #54+ continuing from #53)
9. Secrets-scan layer 1 + 2 + literal-sweep CLEAN attestation
10. Final apt-cache policy output for the 4 originally-PPA-only packages (showing the priority pin took effect)
11. Final fleet patch state: 7/7 nodes patched on CVE-2026-31431
12. Any latent issues observed for follow-on cycles (e.g. autoremove sweep, /tmp cleanup, snap pre-removal)

---

## 12. CYCLE CLOSE → SR/P6 CANDIDATES

Candidate lessons for Paco bank consideration at close-confirm:

- **P6 candidate** — apt-cache policy gives full mirror inventory; a single pre-flight policy probe per critical package would have caught the original Cycle 2 "PPA-only" misclassification before scheduling a 5-day hold. Lesson: when an upgrade depends on PPA-mirrored packages, run `apt-cache policy <pkg>` and inventory ALL sources before declaring availability gating.
- **P6 candidate** — apt's behavior with multiple repos hosting the same package: lexical version-string sort makes apt prefer higher-suffixed versions (`+1000` > `+1`), and apt does NOT automatically fall back to lower-priority mirror on outage. Need explicit pin or source-disable to force mirror substitution. Lesson: PPA-and-main-archive co-hosting requires explicit pin-priority management.
- **SR candidate** — Pin-Priority pattern for downgrading non-default mirrors: standardize as a directive primitive when shipping packages from non-default sources to prevent silent revert on PPA recovery.

---

**End of Cycle 2.0b directive.**

**Authoring next steps:**
1. CEO reviews this draft at `/tmp/paco_directive_homelab_patch_cycle2_0b_ppa_suppression.md` on CK
2. CEO approves → directive moves to `/home/jes/control-plane/docs/` and is committed to canon (via Cowork or per-command MCP override)
3. CEO dispatches PD via Cowork with directive path
4. PD executes; produces close-confirm review at `docs/paco_review_homelab_patch_cycle2_0b_ppa_suppression.md`
5. Paco close-confirm + ratification + anchor update
