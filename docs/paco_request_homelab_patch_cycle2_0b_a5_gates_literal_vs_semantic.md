# Paco Request -- Cycle 2.0b Halt at Stage A.5/B.X.4 retry: Three gates trip on literal interpretation; semantic intent met

**Authored:** 2026-05-04 ~21:25 MT (~03:25Z UTC)
**By:** PD (Engineering, Cowork)
**For:** Paco (COO ruling)
**In response to:** Path Q resume per `docs/paco_response_homelab_patch_cycle2_0b_path_q_ratified.md` (HEAD c8c4af2). B.X.8 PASS (30 holds released, post-count = 1). A.5 simulation now BUILDS clean plan but trips literal gates.
**Cycle:** 2.0b PPA Suppression (CVE-2026-31431 close on Goliath)
**Halt point:** A.5 simulation exit 0 with semantically-correct plan; A.7 + A.8 + B.X.5 trip on literal gate definitions that don't account for B.X.8 unhold-30 scope
**Status:** Cycle frozen at A.5; B.X.1-B.X.3 + B.X.8 PASS; B.X.4 retry produced clean plan but fails 3 of 4 literal gates

---

## 0. WHAT JUST HAPPENED

Path Q resume per Paco c8c4af2:
- B.X.8 PASS (CEO-direct authorization) -- 30 packages unheld; pre-count 31 / post-count 1 (only docker-compose-plugin remains held); pre 03:18:10Z / post 03:19:15Z = 65s wall
- A.5 simulation retry: exit 0, plan builds clean (no broken-deps cascade)
- Gate A.6 (lpc-refs): 0 -- PASS
- Gate A.7 (+1000 modules): 2 matches -- AMBIGUOUS (literal H1 trigger; semantic PASS)
- Gate A.8 (Inst+Conf+Remv count): 61 -- AMBIGUOUS (literal FAIL on 5-25 bound; semantic PASS at exactly 30-unhold scope)
- Gate B.X.5 (libvulkan1 candidate): not in plan -- AMBIGUOUS (semantic PASS achievable via explicit version-pin install at Stage B)

---

## 1. FORENSIC FINDINGS

### 1.1 A.7 +1000 module gate

Two matches in regenerated /home/jes/cycle2_0b/apt_simulate.log:

```
Inst linux-modules-nvidia-580-open-nvidia-hwe-24.04 [6.11.0-1016.16+1000] (6.17.0-1014.14+1 Ubuntu:24.04/noble-updates [arm64]) []
Remv linux-modules-nvidia-580-open-6.11.0-1016-nvidia [6.11.0-1016.16+1000] []
```

Both lines contain `+1000` ONLY in the OLD/REMOVED version annotation (`[6.11.0-1016.16+1000]`):
- Line 1 Inst: target version is `(6.17.0-1014.14+1)` -- **+1**, NOT +1000. Package upgrades from +1000 to +1.
- Line 2 Remv: removing the orphaned 6.11-pinned module (kernel 6.17 replaces 6.11; 6.11 module no longer needed).

**Zero NEW +1000 module installs in plan.** The H1 trigger ("+1000 PPA module appears in apt-get install simulation") is functionally not met -- no PPA-suffixed modules are being installed. Literal grep fires because `+1000` appears as a substring in the OLD-version annotation that gets logged for human-readable diff context.

Directive sec 4 verified-live block expressly anticipates this exact pattern: "`6.17.0-1014.14+1` in `noble-updates/restricted`; `6.17.0-1014.14` (no suffix) in `noble-security/restricted`; `+1000` only on lpc". The plan delivers exactly that intent.

### 1.2 A.8 Inst+Conf+Remv count

Gate count: 61 (30 Inst + 30 Conf + 1 Remv).

Directive A.8: "Inst count between 5 and 25 (kernel + 6 explicit + dependencies; sanity bound). If Inst count > 25, escalate (unexpected dependency drag); if < 5, escalate (incomplete plan)."

Reality: 20 packages upgraded + 10 newly installed + 1 removed = 31 distinct packages. The 30 upgraded/new is a precise match for B.X.8 unhold scope (30 packages released) plus 1 transitive new dep (libopencsd1) plus 1 Remv (orphaned 6.11 kernel module).

Breakdown:
- 20 upgrades: 10 libnvidia-* (580.95.05 -> 580.142) + driver-580-open + nvidia-kernel-common-580 + nvidia-kernel-source-580-open + nvidia-utils-580 + nvidia-compute-utils-580 + xserver-xorg-video-nvidia-580 + linux-image-nvidia-hwe-24.04 (6.11.16 -> 6.17.14) + linux-headers-nvidia-hwe-24.04 + linux-modules-nvidia-580-open-nvidia-hwe-24.04 + linux-tools-nvidia-hwe-24.04 + linux-nvidia-hwe-24.04 + wpasupplicant
- 10 newly installed: libopencsd1 (transitive) + linux-image-6.17.0-1014-nvidia + linux-modules-6.17.0-1014-nvidia + linux-modules-nvidia-580-open-6.17.0-1014-nvidia + linux-modules-nvidia-fs-6.17.0-1014-nvidia + linux-headers-6.17.0-1014-nvidia + linux-tools-6.17.0-1014-nvidia + linux-nvidia-6.17-headers-6.17.0-1014 + linux-nvidia-6.17-tools-6.17.0-1014 + nvidia-firmware-580-580.142
- 1 Remv: linux-modules-nvidia-580-open-6.11.0-1016-nvidia (orphaned by 6.11 -> 6.17 kernel transition)

This is exactly what the directive intends: kernel + driver + modules upgrade from noble-updates/security/main with no PPA leakage. The 5-25 sanity bound was authored when the directive author didn't know B.X.8 unhold-30 was the actual scope (P6 #61 banked-pending: prior cycle's protective state must enumerate in next cycle's PF; P6 #60 banked-pending: directive PF should include `apt-mark showhold` enumeration).

A.8 directive note: "escalate if > 25 (unexpected dependency drag)". Strict reading triggers escalation. Semantic reading: this isn't unexpected -- it's the EXPECTED consequence of B.X.8 (CEO-direct authorized). Hold release is the cause; expanded scope is the effect.

### 1.3 B.X.5 libvulkan1 plan absence

libvulkan1 absent from Inst lines because apt sees:
- Installed: `1.4.321.0-1~1` (priority 100, /var/lib/dpkg/status -- snapshot.ppa source pre-cycle)
- Candidate: `1.4.321.0-1~1` (apt picks installed because no source serves anything newer)
- Available alternates: `1.3.275.0-1build1` from `noble/main` (priority 500)

Apt's logic: "already newest version" because installed is lexically newer than the only fetchable alternate. `apt-get install libvulkan1` is a no-op in this state -- apt won't auto-downgrade.

B.X.5 strict reading: candidate fetchable from noble/main is `1.3.275.0-1build1` (PASS in policy); but plan does not include libvulkan1 install (FAIL on "libvulkan1 candidate must be 1.3.275.0-1build1 from noble/main" if interpreted as "candidate present in install plan").

Directive intent (libvulkan1 from noble/main, Path X-aligned) IS achievable but requires Stage B explicit version-pin: `apt-get install libvulkan1=1.3.275.0-1build1` with `--allow-downgrades`. Or accept currently-installed 1.4.321.0-1~1 (snapshot.ppa origin) stays in place since it's effectively orphaned (snapshot CDN suppressed; future updates would route via noble/main once installed-version drops below noble/main version).

---

## 2. ARCHITECTURAL ANALYSIS

No new structural blocker exists. The cycle is in a directive-gate-definition lag state:

1. **A.7 grep is too loose.** Substring `+1000` matches OLD-version annotations, not just NEW installs. Refinement: grep for `+1000` only in target-version position (right side of parens for Inst lines), or grep `^Inst.*\+1000\)` format-aware.
2. **A.8 sanity bound (5-25) was authored pre-B.X.8.** Cycle 2.0b directive sec 4 verified-live was written before Cycle 2.0a's hold scope was confirmed at 30 packages; A.8 author predicted ~7 explicit + ~10 deps. Reality with B.X.8 scope is 30 + 1 transitive + 1 Remv = 31 distinct. Sanity bound needs adjustment to "30 +/- 5" given B.X.8 release scope is now known.
3. **B.X.5 needs Stage B explicit version-pin for libvulkan1 swap.** Directive intent (libvulkan1 from noble/main) requires `--allow-downgrades` because installed `1.4.321.0-1~1` is sticky from prior snapshot.ppa install.

All three are precisely the pattern Path X solved at A.4: literal grep gate fires due to substring match while semantic intent is preserved. Path X resolution under SR #9 / B0 was "refine the gate" (extend disable to third file). Same shape of problem here.

This is the **third** literal-vs-semantic gate trip in Cycle 2.0b execution (A.4 snapshot.ppa was first; A.7/A.8/B.X.5 are this halt). Pattern strongly suggests P6 #63 (verified-live block must include apt-subsystem internal state probes) is correctly diagnosing the upstream authoring discipline gap.

---

## 3. THREE PATHS

### Path R3 (PD RECOMMENDED) -- Refine gates, proceed

Apply gate-refinement under SR #9 / B0 standing-meta-authority:
- **B.X.10** -- A.7 grep refinement: `grep -E '^Inst .*\+1000\)' /home/jes/cycle2_0b/apt_simulate.log || echo 'clean: no +1000 in install targets'`. This catches +1000 only in target-version position, not OLD-version annotation. Fully aligned with directive intent.
- **B.X.11** -- A.8 sanity bound adjustment: 30 +/- 5 Inst (between 25 and 35) given B.X.8 unhold scope is now known. Document as scope-was-authored-pre-unhold-30. Ratify count 30 as expected.
- **B.X.12** -- B.X.5 Stage B addition: `apt-get install libvulkan1=1.3.275.0-1build1 --allow-downgrades` runs as a separate command after the main install. Or skip entirely (Path R3-skip variant) if Paco prefers leaving currently-installed snapshot.ppa version sticky (it's orphaned now anyway).

Authority: SR #9 / B0 (consistent with Path X B.X.1-B.X.7 precedent). NOT CEO-direct (these are gate-definition refinements that preserve directive intent verbatim, not architectural reversals like B.X.8).

**Why R3 is the right call:**
- Pattern-identical to Path X (literal grep gate vs semantic intent). Same SR #9 / B0 authority.
- Plan IS what the directive intends (kernel + driver + modules from noble-updates).
- 30-package scope is consequence of CEO-direct B.X.8, not directive scope creep.
- Stage B can run cleanly with the actual plan. ~10 min wall to install.
- Rollback Path 2 still valid if Stage B fails post-install.

### Path S3 -- Halt, re-author Cycle 2.0c with corrected gates

Rollback Path 1 (re-enable 3 .sources files via .disabled rename, re-apply 30 holds via apt-mark hold, restart ollama). Cycle 2.0b suspended. Probe loop kept alive. Paco re-authors Cycle 2.0c with:
- A.7 grep refined to target-version-only
- A.8 sanity bound 25-35 (or scope-aware: "matches B.X.8 unhold count + 1")
- B.X.5 explicit Stage B version-pin install for libvulkan1
- All P6 #54-#64 lessons folded into PF.SOURCE_INVENTORY + PF.HOLD_INVENTORY + PF.APT_POLICY_INVENTORY primitives

Delay: ~2-4 hours. Cleaner canon. Returns to held state during recovery (security implications minimal -- 30 packages were held protectively; rehold restores baseline).

### Path R3-strict -- Halt cycle for CEO-direct re-ratification of A.7/A.8 reading

Keep cycle frozen. CEO/Paco issues explicit ruling on whether to interpret A.7 + A.8 literally (halt + 2.0c) or semantically (R3 proceed). No PD self-authorization on gate refinement. Same as R3 outcome if CEO chooses semantic reading; same as S3 if CEO chooses literal.

---

## 4. PD RECOMMENDATION: PATH R3

Reasoning:
- Literal-vs-semantic gate failures are pattern-identical to Path X A.4 snapshot.ppa case; SR #9 / B0 authority cleanly applies
- Plan content is exactly directive intent: kernel + driver + modules from noble-updates/security/main; zero +1000 NEW installs; no PPA leakage; sources fully suppressed
- B.X.10 + B.X.11 are gate refinements (not directive intent changes); B.X.12 is a Stage B explicit version-pin add (consistent with directive's stated libvulkan1-from-noble-main intent)
- Cycle 2.0b directive sec 4 verified-live block expressly listed `+1` and unsuffixed as the noble-updates/security candidate suffixes; the plan delivers exactly that
- ~10 min Stage B wall vs. ~2-4h re-authoring

BUT -- given the third literal-vs-semantic halt in this cycle, plus B.X.8 already invoked CEO-direct (P6 #62 boundary), PD wants explicit CEO/Paco ratification that R3 is acceptable under SR #9 / B0 OR ratify under CEO-direct (cleanest signal would be CEO-direct given the volume of in-place adaptations this cycle).

3 P6 candidates banked-pending at close-confirm (additional to #54-#64; cumulative #54-#67):
- **P6 #65** -- Directive A.7-class gates (substring-matched against simulation log) must specify position (target-version only, not OLD-version annotation) to avoid false-positive matches on packages being upgraded FROM the suspect version
- **P6 #66** -- Directive A.8-class sanity bounds must be authored AFTER cycle scope is known; if B-extensions can change scope (e.g. B.X.8 unhold-30), bounds should be defined relative to scope ("matches unhold count +/- 2") not absolute
- **P6 #67** -- Path X / Path Q / Path R3 cycle-internal-iteration pattern: when literal directive gates trip but semantic intent is met, the in-place B-extension fix is canonical SR #9 / B0 territory IF the gate trip is consequence of either (a) authoring-time substring-too-loose grep, or (b) authoring-time scope-mispredict relative to actual cycle execution. Directive authors should expect iterative gate refinement on cycles touching apt-mark / pin / source state as standard, not exception.

---

## 5. STATE AT HALT

| Item | Value |
|---|---|
| Cycle stage | Between B.X.8 PASS and Stage B; A.5 retry plan built clean (exit 0); literal gates A.7/A.8/B.X.5 trip |
| ollama on Goliath | STOPPED |
| canonical-nvidia .sources files | 3 of 3 .disabled |
| apt-mark holds | 1 (docker-compose-plugin only; 30 released by B.X.8) |
| /home/jes/cycle2_0b/apt_update.log | 0 lpc-refs |
| /home/jes/cycle2_0b/apt_simulate.log | exit 0; 30 Inst + 30 Conf + 1 Remv; semantically clean plan |
| /root/cycle2_0b_backups/ | 3 .sources files |
| Goliath kernel/driver/modules | UNCHANGED (6.11.0-1016-nvidia / 580.95.05 / 6.11.0-1016.16+1000) |
| Standing gates 6/6 | bit-identical to PF.3 |
| HEAD on origin/main | c8c4af2 (Path Q ruling) |
| Probe loop PID 59800 | alive on Goliath; lpc=FAIL lp=PASS |
| Rollback availability | Rollback Path 1 valid (rename 3 .disabled back, reapply 30 holds via single apt-mark hold call, restart ollama, ~75s wall) |

---

## 6. RULING REQUESTED

Paco directs PD to (select one):
- **(R3)** Apply B.X.10 (A.7 grep refinement to target-version only) + B.X.11 (A.8 scope-aware bound 25-35 or +/- 5 of unhold count) + B.X.12 (Stage B explicit libvulkan1 version-pin install OR skip) under SR #9 / B0; document in close-confirm; proceed Stage B per directive
- **(R3-CEO-direct)** Same as R3 but ratified under CEO-direct (parallels B.X.8) given this is the 3rd in-place adaptation in cycle and pattern is establishing
- **(R3-skip-libvulkan)** Apply R3 but explicitly skip B.X.12 -- accept libvulkan1 1.4.321.0-1~1 stays installed (orphaned snapshot.ppa origin; no future updates will land via noble/main since installed > noble/main version, but source is suppressed so no security risk from snapshot CDN)
- **(S3)** Suspend Cycle 2.0b; rollback B.X.1-B.X.3 + B.X.8; re-author Cycle 2.0c with corrected gates + proper PF.HOLD_INVENTORY + libvulkan1 explicit version-pin Stage B step
- **(Other)** Specify amendment

PD halt position: standing by; ollama stopped; cycle reversible in <90s (unhold release + 3 file renames + ollama restart).

---

**End of paco_request.**
