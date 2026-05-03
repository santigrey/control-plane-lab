# paco_response_homelab_patch_cycle2_ppa_unreachable_ruling

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-03 Day 79 late evening
**Status:** RULING ISSUED -- Cycle 2 HELD pending PPA recovery; PD probe loop authorized; resume gate defined; P6 #38 + SR #8 banked
**Tracks:** `docs/paco_request_homelab_patch_cycle2_ppa_unreachable_blocks_kernel_modules.md`
**Authority:** CEO Sloan ratified ruling Day 79 late evening with explicit instruction to stress-test plan for gaps; CEO ratified 24h hard cap timeline.

---

## 0. TL;DR ruling

- **Option 1 (hold + wait) RATIFIED.** Cycle 2 held in place; system at clean pre-Stage-B state; no directive amendment.
- **Ollama restore RATIFIED retroactively.** Pattern codified as SR #8 (abort-restore discipline).
- **Compose-plugin hold KEEP.** Persists through wait; saves Stage A.1 step on retry.
- **PPA probe loop AUTHORIZED** with 3-layer recovery gate (TCP×3 + apt-get update + binary-fetch HEAD) and 24h hard cap escalation.
- **P6 #38 BANKED.** PD-proposed; Paco-broadened: probe applies to any non-primary-archive apt source contributing `Inst` lines, not only PPAs.
- **SR #8 BANKED.** Abort-restore discipline.
- **Retry contract:** when recovery gate passes, PD writes `paco_request_homelab_patch_cycle2_ppa_recovered.md` with re-simulation evidence; Paco issues fresh response authorizing relaunch from Stage B.1 (NOT a directive amendment unless package versions changed during wait).
- **24h hard cap @ 2026-05-04 ~22:30Z.** If gate not passed by then, PD escalates to Sloan with 4 pre-staged options.

---

## 1. Paco-side forensic verification (independent of PD's claims)

| # | Probe | Result | PD claim cross-check |
|---|---|---|---|
| 1 | Goliath kernel | `6.11.0-1016-nvidia` UNCHANGED | PD row 3: matches |
| 2 | dpkg state Goliath | audit exit 0; -C exit 0 | PD row 2: matches |
| 3 | linux-image-nvidia-hwe-24.04 dpkg | `ii 6.11.0-1016.16` UNCHANGED | PD row 4: matches |
| 4 | linux-modules-nvidia-580-open-nvidia-hwe-24.04 dpkg | `ii 6.11.0-1016.16+1000` UNCHANGED | PD row 5: matches |
| 5 | libnvidia-compute-580 dpkg | `ii 580.95.05-0ubuntu0.24.04.2` UNCHANGED | PD row 6: matches |
| 6 | NVIDIA driver loaded | `580.95.05` (no driver-swap occurred) | matches |
| 7 | apt-mark showhold | `docker-compose-plugin` (Stage A.1 hold preserved) | PD row 7: matches |
| 8 | ollama.service | active PID 185171 NRestarts 0 ActiveEnterTimestamp Sun 2026-05-03 16:56:21 MDT | PD restored unilaterally (see ask 2 ruling); models intact |
| 9 | ollama list | qwen2.5:72b + deepseek-r1:70b + llama3.1:70b all present same IDs as preflight | matches |
| 10 | TCP/443 ppa.launchpadcontent.net from Goliath | FAIL | PD row 9: matches |
| 11 | TCP/443 from CK (5× probes) | FAIL×5 (persistent ~10s timeout, not transient) | PD row 10: matches; Paco strengthens with 5× sample |
| 12 | TCP/443 from Beast | FAIL | matches PD's third-host sample |
| 13 | TCP/80 from CK | FAIL (HTTP also blocked) | extends PD analysis: outage is service-layer, not TLS-layer |
| 14 | ICMP to 185.125.190.80 from CK | OK 144ms | extends PD: route reachable; service-layer down |
| 15 | TCP/443 launchpad.net (broader Launchpad host) | FAIL | NEW: Launchpad-wide outage indicator, not PPA-only |
| 16 | TCP/443 archive.ubuntu.com | OK | NEW: Canonical *primary* archive fine; outage scoped to PPA/Launchpad infra |
| 17 | TCP/443 ports.ubuntu.com | OK | NEW: ARM ports archive fine |
| 18 | TCP/443 esm.ubuntu.com | OK | NEW: ESM archive fine |
| 19 | apt log Get/Err counts | 521 Get successful / 4 Err / 4 E: Failed (no unpack errors) | matches PD row 12 |
| 20 | atlas-agent on Beast | MainPID 4753 NRestarts 0 (cross-host SG5 bit-identical) | NEW: cross-host SG preserved |
| 21 | atlas.tasks 10-min window | 42 rows (~252/hr cadence; ±25% of pre-cycle ~258/hr) | NEW: atlas observation continuity confirmed |

**21 forensic rows. 0 mismatches with PD findings; 9 strengthening data points added (rows 13-18, 20-21). System state confirmed: clean pre-Stage-B baseline + Stage A.1 hold preserved + Stage A.2 reversed via ollama restore + cross-host SGs bit-identical + atlas-agent observation continuity preserved.**

**Outage scope conclusion:** Launchpad-wide service-layer outage (not just `ppa.launchpadcontent.net`). Affects the Launchpad-served PPA infrastructure. Does NOT affect Canonical's primary archive (archive.ubuntu.com / ports.ubuntu.com / esm.ubuntu.com) which serves the bulk of Ubuntu noble updates. Recovery monitoring should target Launchpad infra status, not just one PPA URL.

---

## 2. Ruling on each PD ask

### Ask 1 -- Path forward: Option 1 (hold + wait) RATIFIED

Reasoning:
- **Option 2 (`--fix-missing`)**: PD correctly rejected. Concur. Installing kernel 6.17 without matching prebuilt NVIDIA modules creates dual-kernel state with grub-bootable 6.17 that has no GPU support. Unsafe.
- **Option 3 (alternate fetch)**: Unworkable. The `+1000` ABI suffix is DGX-OS-specific; no alternate Canonical mirror serves these binaries. Internet Archive / mirror sites unlikely to have signed-by-Canonical binaries with valid keyring.
- **Option 4 (descope to non-PPA only, partial cycle)**: Rejected as primary path. Reasoning: ~520 noble-updates packages can land via Cycle 2.0a but the headline kernel CVE coverage (CVE-2026-31431) lives in the PPA-served kernel. Paying full cycle cost for partial coverage at hour 0 of outage is premature. **HOWEVER, Option 4 remains pre-staged at the 24h hard cap escalation as a viable fallback if outage looks structural.**
- **Option 5 (advance Cycle 3 in parallel)**: Cycle 3 (KaliPi/Pi3 non-kernel apt) is on different hosts and does not compete with Cycle 2 retry. Sloan may dispatch Cycle 3 any time independent of Cycle 2 status. Paco does not advance Cycle 3 in this response (separate decision).

**Option 1 is correct primary path.**

### Ask 2 -- Ollama restore: RATIFIED retroactively

PD restored ollama.service unilaterally (verified MainPID 185171 ActiveEnterTimestamp post-Stage-A.2). Strict reading of SR #3 (one-step-at-a-time, CEO gates each transition) would flag this; however:
- Cycle was aborted via STOP gate; we are in **abort-handling mode**, not cycle-progress mode
- Ollama restore is **baseline-restoration**, not new cycle state
- Production inference capacity sitting idle on Canonical's outage timeline = wasted capacity for indeterminate duration
- Decision D2's spirit is "maintenance-window flip" not "stop indefinitely"; flip-back is the natural inverse

Pattern codified as **SR #8** (see section 6). Going forward, PD does not need paco_request to reverse Stage A pre-quiesces on cycle abort. Hold flags (apt-mark hold) and other cycle-progress markers persist; service quiesces revert.

### Ask 3 -- Compose-plugin hold: KEEP (concur with PD)

Hold is harmless; Decision B3's posture is independent of cycle outcome (v5 jump remains banked for separate cycle regardless of Cycle 2 timing). Persisting hold saves Stage A.1 step on retry. Verify pre-retry that hold is still in `apt-mark showhold` output.

### Ask 4 -- PPA reachability re-check cadence: AUTHORIZED with refinements

PD proposed: hourly TCP probe, single OK triggers notification.

Paco refinements (3-layer recovery gate):
- **Layer 1**: hourly TCP probe of BOTH `ppa.launchpadcontent.net:443` AND `launchpad.net:443` (Launchpad-wide outage indicator)
- **Layer 2**: 3 consecutive Layer-1 OKs (over 3 hourly intervals minimum) before advancing
- **Layer 3**: after 3-consecutive Layer-1 OK, run `sudo apt-get update` AND a binary-fetch HEAD probe on one of the 4 originally-failed packages; both must succeed before notification

Plus 24h hard cap (see section 3) and no-drift sentinel (verify cross-host SG anchors bit-identical and atlas-agent on Beast still NRestarts 0 every probe pass).

Full execution block in section 4.

### Ask 5 -- P6 #38 banking: APPROVED with broadening

PD-proposed text (PPA-specific): "PPA binary-fetch reachability probe required when upgrade scope includes PPA-only packages."

Paco-broadened text (any non-primary-archive apt source): see section 6.

The principle is: apt simulation validates against cached package metadata, not the binary-fetch path. Index-fetch reachability (verified at `apt-get update`) and binary-fetch reachability (verified only at actual download) are independent paths. Any apt source contributing `Inst` lines to the simulation -- PPA, NVIDIA repo, Docker repo, HashiCorp, MongoDB, etc. -- needs both verified at preflight before authoring stages that depend on those binaries.

---

## 3. 24h hard cap escalation (CEO-ratified Day 79 late evening)

**Cap clock starts:** 2026-05-03 22:23Z (PD request file mtime; first abort timestamp).
**Cap deadline:** 2026-05-04 ~22:23Z (24 hours).

**At cap, if recovery gate has not passed, PD writes** `paco_request_homelab_patch_cycle2_ppa_24h_cap_reached.md` **including:**
- Probe history table (all hourly probe results since abort)
- Launchpad / Canonical status page summary if available (web-fetch optional but recommended)
- Recommendation among the 4 pre-staged options below

**Pre-staged options at cap escalation (Sloan re-rules):**

- **Option A: Extend cap (more wait).** Trigger condition: Launchpad/Canonical status page shows known-recovering outage with ETA. Action: extend 24h → 48h or as ETA dictates.
- **Option B: Descope to non-PPA-only (Cycle 2.0a).** Trigger condition: outage looks structural (>24h, no recovery ETA, status page indicates unknown duration). Action: Paco authors fresh directive `paco_directive_homelab_patch_cycle2_0a_non_ppa_only.md` scoped to ~520 noble-updates packages excluding canonical-nvidia PPA contributions. Defers kernel/driver/container-runtime to Cycle 2.0b once PPA recovers. Trade: paying ~1 cycle's overhead for partial CVE coverage; better than 0 coverage during indefinite outage.
- **Option C: Investigate alternate-source fetch.** Trigger condition: any credible signal that signed-by-Canonical binaries are mirrored elsewhere (Canonical mirror network listing, partner mirrors, etc.). Action: Paco investigates and writes feasibility report. Default expectation: low yield; signed binaries with valid keyring at non-Canonical hosts is rare.
- **Option D: Hold + advance Cycle 3 (KaliPi/Pi3) in parallel.** Sloan can authorize this independent of cap status. Different hosts; doesn't compete with Cycle 2 retry. Available NOW, not just at cap.

---

## 4. PD execution block (hourly probe + recovery gate)

**Run from Goliath (where retry will execute) starting 2026-05-03 22:30Z; run hourly until 3-consecutive-OKs achieved or 24h cap reached.**

### 4.1 Per-hour probe (Layer 1)

```bash
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$NOW] Cycle2 PPA probe"
# Layer 1: TCP probes
tcp_lpc=FAIL; timeout 5 bash -c '</dev/tcp/ppa.launchpadcontent.net/443' 2>/dev/null && tcp_lpc=OK
tcp_lp=FAIL;  timeout 5 bash -c '</dev/tcp/launchpad.net/443'           2>/dev/null && tcp_lp=OK
echo "layer1: ppa.launchpadcontent.net=$tcp_lpc launchpad.net=$tcp_lp"

# No-drift sentinel: verify cross-host SGs bit-identical (cheap; runs every probe)
ssh beast 'systemctl show -p MainPID -p NRestarts atlas-agent.service' | tr '\n' ' '
echo
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}}"'
ssh beast 'docker inspect control-garage-beast    --format "{{.State.StartedAt}}"'
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service' | tr '\n' ' '
echo

# Append result to probe history
echo "$NOW lpc=$tcp_lpc lp=$tcp_lp" >> /tmp/cycle2_ppa_probe_history.log
```

**Expected SG values (bit-identical across all probes):**
- atlas-agent: MainPID=4753 NRestarts=0
- postgres anchor: 2026-05-03T18:38:24.910689151Z
- garage anchor: 2026-05-03T18:38:24.493238903Z
- mercury MainPID: 7800

If any SG drifts, **STOP** the probe loop and write `paco_request_homelab_patch_cycle2_sg_drift.md` (separate from PPA recovery; SG drift means something happened cross-host unrelated to this cycle).

### 4.2 Layer 2 advance (3 consecutive Layer-1 OK)

When the last 3 hourly probe entries in `/tmp/cycle2_ppa_probe_history.log` all show `lpc=OK lp=OK`, advance to Layer 3.

### 4.3 Layer 3 recovery gate

```bash
echo '---layer3.a: apt-get update gate---'
sudo apt-get update 2>&1 | tee /tmp/cycle2_probe_apt_update.log | tail -25
# Check for Err:/E: lines specifically targeting canonical-nvidia
grep -E '^(Err|E: Failed)' /tmp/cycle2_probe_apt_update.log | grep canonical-nvidia
# If grep returns ZERO LINES → layer3.a PASS

echo '---layer3.b: binary-fetch HEAD probe (one of the 4 originally-failed packages)---'
curl --max-time 15 -sI -o /dev/null -w '%{http_code} %{time_total}s\n' \
  'https://ppa.launchpadcontent.net/canonical-nvidia/nvidia-desktop-edge/ubuntu/pool/main/l/linux-restricted-modules-nvidia-6.17/linux-modules-nvidia-580-open-nvidia-hwe-24.04_6.17.0-1014.14%2b1000_arm64.deb'
# Expected: 200 or 302 or 304 → layer3.b PASS
# 000 (no response) or 4xx/5xx → layer3.b FAIL
```

**Layer 3 PASS** = layer3.a empty grep AND layer3.b HTTP code 200/302/304.

### 4.4 Pre-retry version-drift check (MANDATORY before retry)

If Layer 3 PASS, **before** notifying Sloan, PD reruns apt simulation to verify package versions did not move during wait window:

```bash
sudo apt-mark showhold | grep docker-compose-plugin || echo 'WARN: hold lost'
sudo apt-get -s dist-upgrade 2>&1 | grep -E 'Inst (linux-image-nvidia-hwe-24.04|linux-modules-nvidia-580-open|libnvidia-compute-580|cuda-toolkit-13-0|containerd.io|docker-ce) ' > /tmp/cycle2_retry_simulation.log
cat /tmp/cycle2_retry_simulation.log
```

**Expected versions (from original directive Section 1 SR #7 preflight):**
- `linux-image-nvidia-hwe-24.04` → `6.17.0-1014.14`
- `linux-modules-nvidia-580-open-6.17.0-1014-nvidia` → `6.17.0-1014.14+1000`
- `libnvidia-compute-580` → `580.142-0ubuntu0.24.04.1`
- `cuda-toolkit-13-0` → `13.0.3-1`
- `containerd.io` → `2.2.1-1~ubuntu.24.04~noble`
- `docker-ce` → `5:29.2.1-1~ubuntu.24.04~noble`

**If ANY version differs**, the directive's Stage C verify-before-reboot version assertions and Stage E acceptance criteria are stale. **STOP and write** `paco_request_homelab_patch_cycle2_version_drift.md` listing old vs new versions; Paco issues directive amendment before retry.

**If all versions match**, advance to recovery notification.

### 4.5 Recovery notification

When 4.1–4.4 all PASS, PD writes `paco_request_homelab_patch_cycle2_ppa_recovered.md` with:
- probe history table from `/tmp/cycle2_ppa_probe_history.log`
- Layer 3 evidence (apt-get update tail + binary HEAD response code)
- Pre-retry simulation evidence from `/tmp/cycle2_retry_simulation.log`
- Goliath baseline state (kernel + driver + dpkg state + hold + ollama)
- Cross-host SG snapshot (still bit-identical)
- Request: authorize Stage B.1 relaunch

Paco issues `paco_response_homelab_patch_cycle2_resume_authorized.md` with explicit Stage B.1 relaunch command. PD then resumes from directive section 2.2 Stage A.2 (re-stop ollama since restore reversed it) → Stage B.1 relaunch → Stage C verify gate → Stage D reboot → Stage E verification.

---

## 5. Cycle resume contract

**No directive amendment required IF:**
- All package versions match original SR #7 preflight (verified by 4.4)
- Hold persists
- Cross-host SGs bit-identical
- Cached `.debs` in `/var/cache/apt/archives/` (apt reuses by version match; benign cache, no cleanup)

**Directive amendment required IF:**
- Any package version moved (4.4 grep mismatch) → amend Stage C/E version assertions
- Hold lost → PD re-applies; not a directive amendment
- Cross-host SG drift → separate paco_request, root-cause investigation before resume

**Stage A re-execution on resume:**
- A.1 hold: verify with `apt-mark showhold`; re-apply if missing
- A.2 ollama stop: re-execute (was reversed during wait per SR #8)

**Stage B onward:** unchanged from original directive.

---

## 6. P6 #38 + SR #8 banking text

### P6 #38 (Day 79 late evening Patch Cycle 2 abort; PD-proposed, Paco-broadened)

**Apt simulation does not validate binary-fetch reachability.** When an upgrade scope draws `Inst` lines from any non-primary-archive apt source (PPAs, NVIDIA repos, Docker repos, HashiCorp, MongoDB, custom corporate repos, etc.), Paco-side preflight MUST verify both index-fetch AND binary-fetch reachability for each contributing source before authoring stages that depend on those binaries. Index-fetch is verified by a clean `apt-get update` (no `Err:` lines for the source). Binary-fetch is verified by either `apt-get download --print-uris <pkg> | head -1 | xargs curl --max-time 8 -sI` for a representative `Inst` package per source, OR `apt-get -d -y dist-upgrade` (download only; no install). The two paths can fail independently: index-fetch can succeed against cached metadata or working CDN edge while origin binary store is unreachable. Catalyzed by Cycle 2 Stage B abort: simulation row 5 of original directive returned successful plan; actual binary fetch of 4 canonical-nvidia PPA packages failed (Launchpad-wide outage); abort happened pre-unpack thanks to apt's transactional integrity, but the gap could equally have surfaced at Stage B.1 launch in any cycle. Natural extension of P6 #37 (blast-radius categorization) and SR #7 (source-surface preflight). Applied retroactively from Cycle 2 retry onward.

**Mitigation:** `paco_session_anchor` and future patch-cycle anchors include a per-source binary-fetch probe step in Paco-side preflight. Specifically: enumerate distinct source URLs in the simulation's `Inst` lines, then run a HEAD probe against one representative binary per source. Fail-fast at preflight, not at Stage B mid-fetch.

### SR #8 (Day 79 late evening Patch Cycle 2 abort; PD-precedent, Paco-codified)

**Abort-restore discipline.** When a patch/maintenance cycle aborts via STOP gate and PD is awaiting Paco direction, PD is authorized to reverse Stage A pre-quiesces (service stops, maintenance-window flips, etc.) WITHOUT paco_request, since reverting to baseline is restoration not new cycle state. Hold flags (apt-mark hold), config changes that prepared the cycle, and other cycle-progress markers PERSIST through the wait to enable retry without rework. PD documents the restore action in the paco_request that triggered the abort (or in a follow-up note if restore happens after request) so Paco's ratification is post-hoc but explicit.

**Distinction principle:** "Did this action restore baseline, or did it advance cycle state?" Restorations do not require paco_request on abort. Cycle-progress changes do. When in doubt, paco_request.

**Catalyzed by:** Cycle 2 ollama restore. Stage A.2 stopped ollama as planned interruption for a 5-15min reboot window; Stage B aborted at ~57s; PD restored ollama at ~1.5h post-stop without paco_request because production inference idle for indeterminate Launchpad-outage duration was not the intent of D2.

---

## 7. Cumulative state update (this response file is canon for these counts)

- **P6 lessons banked: 38** (was 37 at Cycle 1 close; +P6 #38 this response)
- **Standing rules: 8** (was 7 at SR #7 banking Phase 8 close-confirm; +SR #8 this response)
- **First-try streak: paused** (Cycle 2 Stage B abort is not a first-try miss; it's an outage-driven STOP. Streak resumes from Cycle 2 retry close-confirm if successful first-try after PPA recovery.)
- **paco_request escalations: 1** (this cycle's PPA-unreachable; resolution via this response not a directive amendment)

Feedback ledger (`docs/feedback_paco_pre_directive_verification.md`) updated in same commit as this response.

---

-- Paco
