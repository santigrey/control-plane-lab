# Paco Request -- Cycle 2.0b Halt at Stage A.5/B.X.4: Cycle 2.0a apt-mark holds block 6.17 upgrade plan

**Authored:** 2026-05-04 ~14:50 MT (~20:50Z UTC)
**By:** PD (Engineering, Cowork)
**For:** Paco (COO ruling)
**In response to:** Path X resume per `docs/paco_response_homelab_patch_cycle2_0b_path_x_ratified.md` (HEAD c9cf915) succeeded at B.X.1-B.X.3 then revealed second architectural blocker at A.5
**Cycle:** 2.0b PPA Suppression (CVE-2026-31431 close on Goliath)
**Halt point:** A.5 simulation exit 100 with broken-deps cascade; A.8 Inst count = 0 (expected 5-25)
**Status:** Cycle frozen at A.5; B.X.1-B.X.3 PASS (Path X source-suppression sound); B.X.4 FAIL on dependency-resolver due to held packages

---

## 0. WHAT JUST HAPPENED

Path X resume per Paco c9cf915:
- B.X.1 PASS -- 3rd source backed up to /root/cycle2_0b_backups/ (3 files: 1866 + 1857 + 1863 bytes)
- B.X.2 PASS -- nv-vulkan-desktop-ppa.sources renamed .disabled; content-grep across all active sources for snapshot.ppa/canonical-nvidia/launchpad returns ZERO matches
- B.X.3 PASS -- A.4 retry: apt-get update exit 0; lpc-ref count = 0; broader launchpad ref count = 0; 15 sources hit (was 23 pre-disable)
- B.X.4 FAIL -- A.5 simulation exit 100. A.6 PASS (0 lpc refs in plan). A.7 PASS (clean: no +1000 modules). A.8 FAIL (0 Inst lines, expected 5-25). B.X.5 cannot evaluate (libvulkan1 absent from plan because plan never built).

Key error chain (verbatim):

    The following packages have unmet dependencies:
     linux-modules-nvidia-580-open-6.17.0-1014-nvidia : Depends: nvidia-kernel-common-580 (>= 580.142) but 580.95.05-0ubuntu0.24.04.2 is to be installed
     linux-modules-nvidia-580-open-nvidia-hwe-24.04   : Depends: nvidia-kernel-common-580 (>= 580.142) but 580.95.05-0ubuntu0.24.04.2 is to be installed
     linux-nvidia-hwe-24.04 : Depends: linux-image-nvidia-hwe-24.04 (= 6.17.0-1014.14) but 6.11.0-1016.16 is to be installed
     nvidia-driver-580-open : Depends: nvidia-dkms-580-open (<= 580.95.05-1)
    E: Error, pkgProblemResolver::Resolve generated breaks, this may be caused by held packages.

Apt's own diagnostic: "this may be caused by held packages."

---

## 1. FORENSIC FINDINGS

### 1.1 31 packages held (Cycle 2.0a B2 expanded scope)

6 of 7 directive-explicit Stage A.5 packages are in the held set: linux-image-6.17.0-1014-nvidia, linux-headers-6.17.0-1014-nvidia, linux-modules-nvidia-580-open-6.17.0-1014-nvidia, linux-modules-nvidia-580-open-nvidia-hwe-24.04, linux-nvidia-hwe-24.04, libvulkan1, wpasupplicant. The 7th (linux-image-6.17.0-1014-nvidia) is also held. **All 7 explicit Cycle 2.0b install targets are held.** Plus dependencies: nvidia-kernel-common-580, nvidia-driver-580-open, all libnvidia-*-580, nvidia-dkms-580-open via transitive resolution etc.

Full held set (31): docker-compose-plugin (predates 2.0a, unrelated), libnvidia-cfg1-580, libnvidia-common-580, libnvidia-compute-580, libnvidia-decode-580, libnvidia-encode-580, libnvidia-extra-580, libnvidia-fbc1-580, libnvidia-gl-580, libvulkan1, linux-headers-6.17.0-1014-nvidia, linux-headers-nvidia-hwe-24.04, linux-image-6.17.0-1014-nvidia, linux-image-nvidia-hwe-24.04, linux-modules-6.17.0-1014-nvidia, linux-modules-nvidia-580-open-6.17.0-1014-nvidia, linux-modules-nvidia-580-open-nvidia-hwe-24.04, linux-modules-nvidia-fs-6.17.0-1014-nvidia, linux-nvidia-6.17-headers-6.17.0-1014, linux-nvidia-6.17-tools-6.17.0-1014, linux-nvidia-hwe-24.04, linux-tools-6.17.0-1014-nvidia, linux-tools-nvidia-hwe-24.04, nvidia-compute-utils-580, nvidia-driver-580-open, nvidia-firmware-580-580.142, nvidia-kernel-common-580 (THE specific blocker), nvidia-kernel-source-580-open, nvidia-utils-580, wpasupplicant, xserver-xorg-video-nvidia-580.

### 1.2 noble-updates/security serves all required versions

apt-cache policy confirms upgrade path is fully reachable post-PPA-suppression:

- nvidia-kernel-common-580: installed 580.95.05-0ubuntu0.24.04.2; candidate 580.142-0ubuntu0.24.04.1 from noble-updates/restricted
- nvidia-dkms-580-open: not installed; candidate 580.142-0ubuntu0.24.04.1 from noble-updates/restricted (would be added)
- nvidia-driver-580-open: installed 580.95.05; candidate 580.142 from noble-updates/restricted
- linux-image-nvidia-hwe-24.04: installed 6.11.0-1016.16; candidate 6.17.0-1014.14 from noble-updates/main + noble-security/main
- linux-headers-nvidia-hwe-24.04: installed 6.11.0-1016.16; candidate 6.17.0-1014.14 from noble-updates/main + noble-security/main

Snapshot CDN no longer in any policy version table. Path X / B.X.1-B.X.3 worked as designed for source visibility. Apt is willing to upgrade -- the holds prevent it.

### 1.3 Cycle 2.0b directive sec 9 B5 expressly authorizes the bump

Verbatim from directive (HEAD 8ac14eb): "B5 -- Driver micro-version may bump 580.95.05 -> 580.142 via the upgrade path; this is acceptable and expected (noble-updates ships 580.142-0ubuntu0.24.04.1)".

This is Paco-pre-authorized. The directive expected this bump. The 2.0a holds prevent the directive's stated intent.

---

## 2. ARCHITECTURAL REFRAME

Cycle 2.0a Path A close-confirm (HEAD aecb6ee at 01:35Z UTC) ratified holding 30 packages "to prevent silent 580.95.05 -> 580.142 D-drift via noble-updates fallback". Correct and protective FOR THAT CYCLE -- 2.0a was a non-PPA descope; driver bump was an unwanted side effect to be suppressed.

Cycle 2.0b directive (HEAD 8ac14eb at 01:55Z UTC, ~20 min after 2.0a close) was authored with sec 4 verified-live block but did NOT capture apt-mark hold state, did NOT include unhold steps in Stage A, and at sec 9 B5 expressly authorized the very 580.95.05 -> 580.142 bump that 2.0a's holds were preventing. Directive's stated intent and system's apt-mark state are mutually exclusive.

Source-suppression Path X (B.X.1-B.X.3) is sound -- snapshot CDN no longer in policy candidates. Hold conflict is orthogonal to Path X and would have happened regardless.

This is the **second** structural blocker discovered at run time in Cycle 2.0b (first was snapshot CDN; this is apt-mark hold). Both correlate with directive authoring not enumerating actual ground-truth state of apt subsystem at PF time.

---

## 3. TWO PATHS

### Path Q (PD RECOMMENDED) -- Release Cycle 2.0a holds, retry A.5

Apply `apt-mark unhold` to the 30 nvidia/kernel/libvulkan1/wpasupplicant packages from Cycle 2.0a B2 scope (preserve docker-compose-plugin which predates 2.0a and is unrelated). Re-run A.5 simulation. Expect Inst count between 5-25; libvulkan1 in plan downgrade-or-reinstall from snapshot-sourced 1.4.321.0-1~1 to noble/main 1.3.275.0-1build1; driver bump 580.95.05 -> 580.142; kernel meta bump 6.11 -> 6.17.

Document under SR #9 / B0 standing-meta-authority as B-extension B.X.8.

Why Q is the right call:
- Honors directive intent (Cycle 2.0b == kernel + driver bump per B5)
- B5 already pre-authorizes the driver bump from 580.95.05 to 580.142
- Source-suppression Path X work preserved (no rewind)
- ~30s wall to apply (single apt-mark unhold command), then ~10s for A.5 retry
- A.6 / A.7 H1 gates remain canonical safeguards
- Rollback Path 1 (re-enable .sources files + restart ollama) still trivially valid
- Re-applying holds at D.5 or close-confirm is a clean post-cycle return to held state IF persistent posture is desired (PD willing to add as B.X.9 if Paco directs)

The full unhold command will be a single apt-mark unhold call enumerating the 30 packages explicitly. PD authors verbatim on Paco ratify.

### Path S -- Abort Cycle 2.0b, re-author Cycle 2.0c with hold-state in PF

Rollback Path 1. Cycle 2.0b suspended. Probe loop kept alive. Paco re-authors Cycle 2.0c that:
- Captures apt-mark hold state in sec 0 verified-live
- Adds explicit unhold step at Stage A.0 or extends A.3 to include hold management
- Optionally reinstates holds at D.x post-success
- Adds new PF.SOURCE_INVENTORY primitive (P6 #58 candidate) and PF.HOLD_INVENTORY primitive (new P6 candidate)

Delay: ~2-4 hours for re-authoring + re-execution. High-quality canon for future cycles.

Why S may be preferable to Q: the apt-mark hold release reverses a recently CEO-ratified architectural decision (Cycle 2.0a Path A). Even though Cycle 2.0b's directive intent makes the release necessary, doing it under SR #9 / B0 in-place fix may be too broad an interpretation of "structural-clerical adaptation preserving intent." The release affects 30 packages and changes the system's protective posture for the duration. A re-authored 2.0c with explicit Stage A unhold + Stage D rehold is more transparent.

---

## 4. PD RECOMMENDATION: PATH Q

Reasoning:
- B5 path-B in the directive expressly anticipates the driver bump; the holds were the only thing in the way; releasing them honors directive intent
- ~30s incremental wall vs. ~2-4h for re-authoring
- A.6/A.7 H1 gates remain canonical safeguards
- Source-suppression work preserved
- Holds were a protective mechanism for 2.0a; with 2.0b explicitly authorizing the very bump they protected against, holds are now obstructive to current directive

However: Sloan/Paco explicit ratification of release is the cleanest signal. PD halts and waits for Q vs S directive.

3 P6 candidates banked-pending at close-confirm:
- P6 #60 -- Directive PF should include `apt-mark showhold` enumeration when cycle scope touches kernel/driver upgrades; hold state is invisible to filename-glob source inventory and to apt-cache policy version tables
- P6 #61 -- When two consecutive cycles touch overlapping package scopes, the prior cycle's protective state (holds, pins, masked services, disabled units) MUST be enumerated in the next cycle's PF; otherwise apt's behavior diverges from directive expectation in ways the simulation only catches at A.5 (after PPA suppression has been applied -- significant work to roll back)
- P6 #62 -- The B0 / SR #9 in-place fix authority has a soft boundary at "reverses a prior CEO-ratified architectural decision". When the in-place fix would unwind a prior Path A / Path B / etc. CEO ratification (even if the unwinding is consistent with current directive intent), PD should escalate rather than self-authorize. This Cycle 2.0b A.5 halt is the canonical example.

---

## 5. STATE AT HALT

| Item | Value |
|---|---|
| Cycle stage | Between B.X.3 PASS (A.4 retry) and B.X.4 FAIL (A.5 retry); A.5 simulation exit 100 |
| ollama on Goliath | STOPPED (intentional from A.2; through Path X resume) |
| canonical-nvidia .sources files | 3 of 3 .disabled (B.X.1 + B.X.2 PASS) |
| /home/jes/cycle2_0b/apt_update.log | 0 lpc-refs (B.X.3 fresh log) |
| /home/jes/cycle2_0b/apt_simulate.log | exit 100, broken deps logged |
| /root/cycle2_0b_backups/ | 3 files (1866 + 1857 + 1863 bytes) |
| Goliath kernel/driver/modules | UNCHANGED (6.11.0-1016-nvidia / 580.95.05 / 6.11.0-1016.16+1000) |
| apt-mark holds | 31 active (30 from 2.0a B2 + docker-compose-plugin) |
| Standing gates 6/6 | bit-identical to PF.3 (no drift) |
| HEAD on origin/main | c9cf915 (Path X ruling) |
| Probe loop PID 59800 | alive on Goliath; lpc=FAIL lp=PASS |
| Rollback availability | Rollback Path 1 valid (rename 3 .disabled back, restart ollama, ~30s wall) |

---

## 6. RULING REQUESTED

Paco directs PD to (select one):
- **(Q)** Apply `apt-mark unhold` to 30 packages (preserve docker-compose-plugin); document as B.X.8 under SR #9 / B0; retry A.5; proceed cycle. Optional B.X.9 to re-apply holds at D.5 (specify if desired).
- **(S)** Suspend Cycle 2.0b; rollback B.X.1-B.X.3 via Rollback Path 1; re-author Cycle 2.0c with hold-state in sec 0 verified-live + explicit Stage A unhold + Stage D rehold.
- **(Other)** Specify amendment.

PD halt position: standing by; ollama stopped; cycle reversible in <60s.

---

**End of paco_request.**
