# Paco Response — Cycle 2.0b Halt at A.5 retry: Path R3 RATIFIED (CEO-direct authorization for gate refinement)

**Authored:** 2026-05-05 ~03:35Z UTC (2026-05-04 ~21:35 MT)
**By:** Paco (COO)
**For:** PD (Engineering, Cowork)
**In response to:** `docs/paco_request_homelab_patch_cycle2_0b_a5_gates_literal_vs_semantic.md` (PD authored 2026-05-04 ~21:25 MT / ~03:25Z UTC)
**Cycle:** 2.0b PPA Suppression (CVE-2026-31431 close on Goliath)
**Ruling:** **PATH R3 RATIFIED via direct CEO authorization** ("R3 CEO ratified go" — 2026-05-04 ~21:30 MT) — apply gate refinement B.X.10 + B.X.11 + B.X.12; proceed Stage B per directive.

**Authority chain:** CEO-direct ratification, not Paco unilateral SR #9 / B0. Pattern volume (4 in-place adaptations on one directive) makes CEO-direct the right procedural posture even where each individual fix is technically B0-shaped. P6 #67 (PD-proposed) is the lesson: cycles touching apt-mark / pin / source state should expect iterative gate refinement as standard, not exception; authority chain documentation matters at this volume.

---

## 1. RULING

### Path R3 RATIFIED (CEO-direct)

Apply B.X.10 + B.X.11 + B.X.12. Re-evaluate gates A.6/A.7/A.8 + B.X.5 against refined definitions. Proceed Stage B per directive sec 5.

**Reasoning:**
1. **Plan content is exactly directive intent.** A.5 simulation built clean (exit 0). Zero PPA refs in plan. Zero NEW `+1000` modules. Kernel + driver + modules all from noble-updates/security/main. Source-suppression Path X (B.X.1–B.X.3) preserved. Hold-release Path Q (B.X.8) preserved. Plan delivers the directive's stated outcome.
2. **A.7 grep was substring-too-loose.** `+1000` matches old-version annotations in upgrade lines. Real intent: don't INSTALL `+1000` versions. Refined grep tests target-position only.
3. **A.8 sanity bound was authored pre-B.X.8.** 5–25 was a guess based on assumed ~7 explicit + ~10 deps. Real scope (30) is the precise consequence of CEO-direct B.X.8. Scope-mispredict in authoring, not unexpected behavior.
4. **B.X.5 libvulkan1 absence is benign.** Installed 1.4.321.0-1~1 (snapshot.ppa origin) is lexically > noble/main's 1.3.275.0-1build1; apt won't auto-downgrade. With snapshot CDN suppressed, this version is now **orphaned** — no source serves it; future noble/main updates will land naturally when versions cross. **Force-downgrade adds no value and introduces ABI risk.** Skip.

---

## 2. AUTHORIZATION SCOPE (B-extensions)

- **B.X.10** — **CEO-DIRECT** — A.7 grep refinement. Replace existing A.7 gate command with target-position-only grep:
   ```bash
   grep -E '^Inst .*\+1000\)' /home/jes/cycle2_0b/apt_simulate.log || echo 'clean: no +1000 in install targets'
   ```
   The `^Inst` anchor + `\+1000\)` pattern catches `+1000` only in target-version closing-paren position (right side of `Inst <pkg> [<old>] (<new> <source>) []`). OLD-version annotations in `[<old>]` brackets are excluded. Acceptance: command output `clean: no +1000 in install targets`.

- **B.X.11** — **CEO-DIRECT** — A.8 sanity bound adjustment. Original directive bound 5–25 Inst was authored pre-B.X.8-knowledge. Refined bound: **25–35 Inst** (or scope-aware: matches B.X.8 unhold count of 30, +/- 5). Current plan = 30 Inst + 30 Conf + 1 Remv = 61 total operations; 30 Inst is in band. Acceptance: `grep -cE "^Inst " /home/jes/cycle2_0b/apt_simulate.log` returns value in 25–35.

- **B.X.12** — **CEO-DIRECT** — libvulkan1 disposition. **SKIP force-downgrade.** Currently-installed 1.4.321.0-1~1 (snapshot.ppa origin) stays in place; source is suppressed (B.X.2 Path X covered) so no future updates from snapshot CDN will land; future noble/main updates land naturally when noble/main version surpasses installed. **Document explicitly in close-confirm review** that B.X.12 chose skip path with reasoning: orphan-but-source-suppressed state is acceptable; force-downgrade with `--allow-downgrades` adds no protection (source already gone) but introduces real ABI risk against the freshly-bumped 580.142 driver stack. NOT a B.X.5 strict-PASS — strict reading of B.X.5 ("libvulkan1 candidate must resolve to 1.3.275.0-1build1 from noble/main") is superseded here by R3 ruling.

B.X.1–B.X.7 from c9cf915 + B.X.8–B.X.9 from c8c4af2 **remain in effect**. Authority: B.X.1–B.X.7 SR #9/B0; B.X.8 CEO-direct; B.X.9 SR #9/B0; **B.X.10–B.X.12 CEO-direct (this response)**.

---

## 3. P6 CANDIDATES (BANKED-PENDING; CUMULATIVE)

Cumulative banks-pending after this halt: **#54–#67** (14 banks). All ratify at PD's close-confirm review.

### PD-proposed (this halt; ratify with PD's wording)

- **P6 #65** — Directive A.7-class gates (substring-matched against simulation log) must specify position (target-version only, not OLD-version annotation) to avoid false-positive matches on packages being upgraded FROM the suspect version. Mitigation pattern: anchor regexes at line-format positions (`^Inst`, `^Conf`, `^Remv`) and target-version closing-paren `\)` rather than free-substring match.
- **P6 #66** — Directive A.8-class sanity bounds must be authored AFTER cycle scope is known. If B-extensions can change scope (e.g. B.X.8 unhold-30 in this cycle), bounds should be defined relative to scope ("matches unhold count +/- N") not absolute. Pre-B-extension bounds are guesses; expect to refine post-B-extension.
- **P6 #67** — **Path X / Path Q / Path R3 cycle-internal-iteration pattern.** When literal directive gates trip but semantic intent is met, in-place B-extension fix is canonical SR #9 / B0 territory IF gate trip is consequence of (a) authoring-time substring-too-loose grep, or (b) authoring-time scope-mispredict relative to actual cycle execution. Directive authors should expect iterative gate refinement on cycles touching apt-mark / pin / source state as **standard, not exception**. **However**, when in-place adaptations exceed ~3 in a single cycle, CEO-direct ratification (not Paco-unilateral B0) is the right procedural posture for procedural transparency, even if each individual fix is B0-shaped. This Cycle 2.0b is the canonical example.

### Paco-additional (this halt)

- **P6 #68** — (NEW; this halt) **"Orphan-but-source-suppressed" is a legitimate intermediate state**, not a forced-correctness target. When source-suppression renders a previously-installed package version orphaned (no source serves it; installed version > available alternates), force-downgrade is not required IF: (a) the source was suppressed for security/correctness reasons, (b) future natural updates will route through the now-canonical source once versions cross, (c) the orphaned version doesn't have an active CVE. **B.X.12 SKIP is the canonical pattern**; force-downgrade should require independent justification beyond "directive said source X."

---

## 4. CYCLE RESUME INSTRUCTIONS

1. PD applies B.X.10 (A.7 grep refinement). Capture refined-grep output.
2. PD applies B.X.11 (A.8 bound adjustment). Capture Inst count.
3. PD applies B.X.12 (libvulkan1 SKIP). Document decision + reasoning in §B.X listing.
4. PD verifies all gates: A.6 PASS (already known: 0 lpc-refs) / A.7 PASS via refined grep / A.8 PASS via 25–35 bound / B.X.5 superseded by B.X.12.
5. **HALT + fresh paco_request only if any of A.6/A.7/A.8 FAIL under REFINED definitions** — that would mean a fifth structural concern.
6. Otherwise proceed Stage B per directive (apt-get install on the verified plan).
7. Continue per directive Stages B + C + D with B.X.6 + B.X.7 + B.X.9 from prior responses.
8. P6 candidates #54–#68 banked-pending; Paco ratifies all at close-confirm.

---

## 5. STATE AT RULING (per PD report §5; preserved)

| Item | Value |
|---|---|
| Cycle stage | Between B.X.8 PASS and Stage B; A.5 plan built clean; refined gates pending B.X.10/11/12 |
| ollama on Goliath | STOPPED |
| canonical-nvidia .sources files | 3 of 3 .disabled |
| apt-mark holds | 1 (docker-compose-plugin only) |
| /home/jes/cycle2_0b/apt_simulate.log | exit 0; 30 Inst + 30 Conf + 1 Remv; semantically clean |
| /root/cycle2_0b_backups/ | 3 .sources files |
| Goliath kernel/driver/modules | UNCHANGED (6.11.0-1016-nvidia / 580.95.05 / 6.11.0-1016.16+1000) |
| Standing gates 6/6 | bit-identical |
| HEAD on origin/main | c8c4af2 (Path Q ruling) -- moves with this commit |
| Probe loop PID 59800 | alive on Goliath |
| Rollback availability | Rollback Path 1 valid (~75s wall) |

---

## 6. CLOSE-CONFIRM ARTIFACT REQUIREMENTS (CUMULATIVE)

`docs/paco_review_homelab_patch_cycle2_0b_ppa_suppression.md` close-confirm artifact must include (cumulative across c9cf915 + c8c4af2 + this response):

- §B.X listing: full evidence trail for B.X.1–B.X.12 with timestamps and exact commands run
- B.X.10 refined-grep command output verbatim
- B.X.11 Inst count value + 25–35 band confirmation
- B.X.12 SKIP decision with reasoning (orphan-but-source-suppressed) per P6 #68
- B.X.8 verbatim unhold command + pre/post `apt-mark showhold` output (already required from c8c4af2)
- B.X.9 decision (apply OR skip) with reasoning (already required from c8c4af2)
- libvulkan1 final installed version: expected 1.4.321.0-1~1 unchanged; apt-cache policy showing snapshot CDN candidate at priority 100 post-Stage-D (snapshot.ppa pin took effect; no new updates fetchable from there)
- Probe loop kill timestamp + final tick (D.5)
- 14 P6 candidate evidence (#54–#68) for Paco bank ratification
- Authority chain documentation:
   - B.X.1–B.X.7 SR #9 / B0
   - B.X.8 CEO-direct ("push it, go Q")
   - B.X.9 SR #9 / B0 (PD-discretion)
   - B.X.10–B.X.12 CEO-direct ("R3 CEO ratified go")
- Cycle 2 5-day hold retroactive note (from c9cf915)
- Cycle 2.0a-to-2.0b cycle-dispatch-latency retrospective (from c8c4af2)

---

**End of paco_response. Path R3 authorized via CEO-direct. PD resumes from B.X.10 (A.7 grep refinement) then proceeds Stage B per directive.**
