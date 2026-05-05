# Paco Request -- Cycle 2.0b Halt at Stage A.4: Third canonical-nvidia source discovered (snapshot.ppa CDN active)

**Authored:** 2026-05-04 ~14:30 MT (~20:30Z UTC)
**By:** PD (Engineering, Cowork)
**For:** Paco (COO ruling)
**Cycle:** 2.0b PPA Suppression (CVE-2026-31431 close on Goliath)
**Halt point:** Stage A.4 lpc-ref count gate FAILED (got 1, expected 0)
**Status:** Cycle frozen at A.4; A.1-A.3 executed and reversible via Rollback Path 1

---

## 0. WHAT JUST HAPPENED (PD execution log)

Pre-flight PF.1-PF.10 all PASS first-try. Stage A.1 PASS (2 .sources files backed up to /root/cycle2_0b_backups/). Stage A.2 PASS (ollama stopped, MainPID 59472 -> inactive). Stage A.3 PASS (the 2 PF.8 files renamed to .disabled). Stage A.4 apt-get update exit 0 BUT lpc-ref count = 1, not 0 per directive sec 4 expectation.

The 1 ref is to a hostname the directive treated as identical to the down primary:
- Down primary: `ppa.launchpadcontent.net` (PF.6 = FAIL; lpc=FAIL since 2026-04-30)
- The matched line: `Hit:10 https://snapshot.ppa.launchpadcontent.net/canonical-nvidia/vulkan-packages-nv-desktop/ubuntu noble InRelease`

These are different hosts. Snapshot CDN is UP and was serving canonical-nvidia content the entire 6-day primary outage.

---

## 1. FORENSIC FINDINGS (read-only investigation post-A.4 deviation)

### 1.1 Third source file located

**File:** `/etc/apt/sources.list.d/nv-vulkan-desktop-ppa.sources` (1863 bytes, mtime Oct 14 2025)
**URI:** `https://snapshot.ppa.launchpadcontent.net/canonical-nvidia/vulkan-packages-nv-desktop/ubuntu/`
**Why PF.8 missed it:** filename begins `nv-vulkan-` (no "nvidia" string). PF.8 grep was `grep -iE "nvidia|canonical-nvidia"` against `ls -la` output; this filename has neither token. Pattern was filename-based, not file-content-based.

### 1.2 The 2 disabled files also point to snapshot.ppa CDN

```
canonical-nvidia-ubuntu-nvidia-desktop-edge-noble.sources.disabled
  -> https://snapshot.ppa.launchpadcontent.net/canonical-nvidia/nvidia-desktop-edge/ubuntu/

canonical-nvidia-ubuntu-linux-firmware-mbssid-patches-noble.sources.disabled
  -> https://snapshot.ppa.launchpadcontent.net/canonical-nvidia/linux-firmware-mbssid-patches/ubuntu/
```

All THREE canonical-nvidia files use the snapshot CDN, not primary lpc.

### 1.3 apt-cache policy proves snapshot CDN does NOT serve +1000 modules for 6.17

```
linux-modules-nvidia-580-open-6.17.0-1014-nvidia:
  Installed: (none)
  Candidate: 6.17.0-1014.14+1
  Version table:
     6.17.0-1014.14+1 500
        500 http://ports.ubuntu.com/ubuntu-ports noble-updates/restricted arm64 Packages
     6.17.0-1014.14 500
        500 http://ports.ubuntu.com/ubuntu-ports noble-security/restricted arm64 Packages

linux-modules-nvidia-580-open-nvidia-hwe-24.04:
  Installed: 6.11.0-1016.16+1000
  Candidate: 6.17.0-1014.14+1
  Version table:
     6.17.0-1014.14+1 500
        500 http://ports.ubuntu.com/ubuntu-ports noble-updates/restricted arm64 Packages
     6.17.0-1014.14 500
        500 http://ports.ubuntu.com/ubuntu-ports noble-security/restricted arm64 Packages
 *** 6.11.0-1016.16+1000 100
        100 /var/lib/dpkg/status
```

Zero snapshot.ppa candidates for either kernel-module package. The `+1000` ABI version persists only as the locally-installed 6.11 module (dpkg-status priority 100).

### 1.4 libvulkan1 has TWO candidates competing

```
libvulkan1:
  Installed: 1.4.321.0-1~1
  Candidate: 1.4.328.1-1~1
  Version table:
     1.4.328.1-1~1 500
        500 https://snapshot.ppa.launchpadcontent.net/canonical-nvidia/vulkan-packages-nv-desktop/ubuntu noble/main arm64 Packages
 *** 1.4.321.0-1~1 100
        100 /var/lib/dpkg/status
     1.3.275.0-1build1 500
        500 http://ports.ubuntu.com/ubuntu-ports noble/main arm64 Packages
```

- Directive sec 4 verified-live: "libvulkan1 available in noble/main (ports.ubuntu.com)" -- **TRUE but incomplete** -- snapshot CDN also serves it at higher version.
- With snapshot CDN active, apt will pick `1.4.328.1-1~1` from snapshot.ppa (lexical sort prefers higher version at equal priority 500), NOT `1.3.275.0-1build1` from noble/main as directive intent specified.
- Directive sec 4 simulation expectation A.6/A.7: "zero `+1000` modules in plan" -- snapshot.ppa libvulkan1 doesn't carry `+1000` suffix, so A.7 grep wouldn't catch it. A.7 gate is module-specific, not source-comprehensive.

### 1.5 wpasupplicant + 6.17 kernel are clean

- `wpasupplicant` candidate `2:2.10-21ubuntu0.4` from noble-updates/main; no snapshot.ppa candidate. Clean.
- 6.17 kernel image candidates: from noble-updates/main, noble-security/main only. Clean.

---

## 2. ARCHITECTURAL REFRAME

**Directive premise (sec 1, sec 4):** lpc still FAIL therefore canonical-nvidia unreachable therefore suppress PPA and route through noble-updates/security. Implicit equivalence: canonical-nvidia == primary lpc.

**Actual ground truth:**
- `ppa.launchpadcontent.net` (primary) DOWN since 2026-04-30 (verified PF.6).
- `snapshot.ppa.launchpadcontent.net` (CDN) UP throughout (verified A.4 apt-get update Hit:10).
- All 3 canonical-nvidia source files configured to use snapshot CDN (verified 1.1, 1.2).
- Snapshot CDN serves SOME canonical-nvidia content (vulkan packages) but NOT 6.17 `+1000` modules (verified 1.3).
- The Cycle 2 "PPA hold" was correct for **kernel modules** (no snapshot CDN candidates exist for those), but broader "canonical-nvidia unreachable" assumption was incomplete -- vulkan packages reachable throughout.

**Implication for Cycle 2.0b directive intent:**

Directive's stated outcome (sec 1): "Switch the apt-resolution path from `canonical-nvidia` PPA (`+1000` suffix builds) to Canonical's `noble-updates`/`noble-security` archives (`+1` suffix or unsuffixed builds)."

- For kernel + 6.17 modules: intent already met by A.3 (no snapshot CDN candidates for those packages).
- For libvulkan1: intent NOT met if `nv-vulkan-desktop-ppa.sources` stays active (apt prefers snapshot CDN's `1.4.328.1-1~1` over noble/main's `1.3.275.0-1build1`).
- For wpasupplicant: intent met (no snapshot CDN candidate exists).

Additional finding: The Cycle 2 hold at "5+ days" was load-bearing on the original misclassification. **Cycle 2.0a non-PPA descope shipped clean from snapshot CDN** without the team noticing the CDN was up (P6 #51 "PPA Origin filter" caught the symptom but didn't surface the upstream architectural fact).

---

## 3. THREE PATHS

### Path X (PD RECOMMENDED) -- Extend suppression to third file, proceed cleanly

- Backup `nv-vulkan-desktop-ppa.sources` to `/root/cycle2_0b_backups/` (extend A.1)
- Rename `nv-vulkan-desktop-ppa.sources` -> `.disabled` (extend A.3)
- Re-run apt-get update; verify lpc-ref count = 0 across all snapshot.ppa variants
- Re-run A.5 simulation; confirm A.6/A.7 PASS (no +1000 in plan, no snapshot.ppa in plan)
- Confirm libvulkan1 candidate becomes `1.3.275.0-1build1` from noble/main
- Proceed Stage B
- Document under SR #9 / B0 standing-meta-authority as B-extension at A.1 + A.3 + D.1
- D.1 re-enable: 3 files renamed back from .disabled (was 2)
- Pin priority D.2 already covers "Pin: release o=LP-PPA-canonical-nvidia-*" pattern -- may need adaptation if snapshot CDN reports different `release o=` value (test at D.4 verify)

**Why X is the right call:** preserves directive intent (full PPA suppression, source migration to noble-updates/security/main); single new structural adaptation; forces libvulkan1 from noble/main as directive specifies; rollback path 1 already works (just adds one more file to the rename loop); A.6/A.7 H1 gates remain canonical safeguards; ~2 min wall to retry A.4 + A.5.

### Path Y -- Refine A.4 grep gate, proceed without disabling third file

- Refine A.4 grep to `ppa\.launchpadcontent\.net` excluding `snapshot\.ppa\.`
- Proceed to A.5 simulation; H1 catches +1000 modules if they leak from any source
- If A.6/A.7 PASS, run Stage B (libvulkan1 will upgrade to snapshot CDN's `1.4.328.1-1~1`, NOT noble/main's `1.3.275.0-1build1`)

**Why Y is wrong:** directive's stated intent (sec 4 verified-live: "libvulkan1 available in noble/main") is NOT met. Goliath ships with snapshot.ppa-sourced libvulkan1 going forward, and the canon record would say "upgraded from noble/main" when it actually came from snapshot CDN. Truth divergence in close-confirm.

### Path Z -- Suspend Cycle 2.0b, re-author 2.0c with architectural reframe

- Cycle 2.0b frozen; rollback A.1-A.3 via Rollback Path 1
- Probe loop PID 59800 kept alive
- Paco re-authors Cycle 2.0c that explicitly addresses the snapshot CDN architecture (PF source-discovery via apt-cache policy not file-glob; A.3 disable scope = all 3 files; D.1/D.2 pin scope updated)
- Adds ~2 days delay; high-quality canon for future cycles

**Why Z is overkill:** Path X resolves the immediate gap with single structural adaptation. Z's value is the architectural lessons, which can be captured as P6 banks at close-confirm without re-authoring.

---

## 4. PD RECOMMENDATION: PATH X

Backed by:
- A.6/A.7 H1 gates handle the only architectural risk (a +1000 module leaking into install plan)
- Snapshot CDN apt-cache policy already verified clean for kernel modules (sec 1.3)
- Single B-extension; SR #9 B0 authority covers it
- Preserves directive's stated outcome verbatim
- Probe loop, ollama-stopped state, backups, .disabled files all intact -- minimal additional state
- ~2 min wall to retry; full Cycle 2.0b finishes in original ~90 min budget

Two P6 candidates banked-pending at close-confirm regardless of path:
- **P6 #54** -- canonical-nvidia content is served via snapshot.ppa CDN, not primary lpc; PF source inventory should grep file CONTENTS for hostname patterns, not just filename patterns. Mitigation: PF source-discovery gate uses `grep -rE 'launchpad' /etc/apt/sources.list /etc/apt/sources.list.d/` to find PPA refs by URL not filename.
- **P6 #55** -- `apt-cache policy <package>` is the canonical source-enumeration probe; should run for every explicit upgrade target at PF time to catch multi-source candidates BEFORE Stage A. Would have caught Path Y vs Path X divergence at PF.5+, not A.4.

Additionally, the Cycle 2 5-day hold (2026-04-30 -> 2026-05-05) was load-bearing on the wrong premise: Cycle 2.0a shipped successfully via snapshot CDN content that nobody had verified was reaching apt. The canon record "PPA outage continues" was strictly true for primary lpc but functionally misleading. **P6 #56** candidate -- when an outage gates a cycle, the gate must specify which CDN/host/path is the actual block, not just the upstream service umbrella.

---

## 5. STATE AT HALT

| Item | Value |
|---|---|
| Cycle stage | Between A.3 PASS and A.4 retry |
| ollama | STOPPED on Goliath (A.2 left it that way; MainPID was 59472) |
| canonical-nvidia .sources files (PF.8 inventory) | 2 of 2 .disabled |
| canonical-nvidia .sources files (full inventory) | 2 of 3 disabled; `nv-vulkan-desktop-ppa.sources` still ACTIVE |
| /home/jes/cycle2_0b/apt_update.log | present, 23 source hits, 1 lpc-ref (snapshot CDN) |
| /root/cycle2_0b_backups/ | 2 files preserved (sizes 1866 + 1857) |
| Goliath kernel/driver/modules | UNCHANGED (6.11.0-1016-nvidia / 580.95.05 / 6.11.0-1016.16+1000) |
| Standing gates 6/6 | bit-identical to PF.3 (no drift) |
| HEAD on origin/main | 8ac14eb (directive itself; no canon updates this cycle) |
| Probe loop PID 59800 | alive; lpc=FAIL lp=PASS continues |
| Rollback availability | Rollback Path 1 valid (rename `.disabled` back, restart ollama, ~30s wall) |

---

## 6. RULING REQUESTED

Paco directs PD to (select one):
- **(X)** Extend A.1 + A.3 to disable third file `nv-vulkan-desktop-ppa.sources`; retry A.4; proceed cycle. Document as B-extension under SR #9.
- **(Y)** Refine A.4 grep to exclude `snapshot\.ppa\.` substring; accept libvulkan1 from snapshot CDN; proceed cycle. Truth divergence noted in close-confirm.
- **(Z)** Suspend Cycle 2.0b; rollback A.1-A.3; re-author Cycle 2.0c with architectural reframe. Probe loop kept alive.
- **(Other)** Specify amendment.

PD halt position: standing by; ollama stopped; cycle reversible in <60s.

---

**End of paco_request.**
