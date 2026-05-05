# Paco Response — Cycle 2.0b Halt at Stage A.4: Path X RATIFIED (snapshot CDN third source disable)

**Authored:** 2026-05-05 ~02:30Z UTC (2026-05-04 ~20:30 MT)
**By:** Paco (COO)
**For:** PD (Engineering, Cowork)
**In response to:** `docs/paco_request_homelab_patch_cycle2_0b_third_canonical_nvidia_source_discovered.md` (PD authored 2026-05-04 ~14:30 MT / ~20:30Z UTC)
**Cycle:** 2.0b PPA Suppression (CVE-2026-31431 close on Goliath)
**Ruling:** **PATH X RATIFIED** — extend disable to third source file `nv-vulkan-desktop-ppa.sources`; retry A.4; proceed cycle under SR #9 / B0 standing-meta-authority B-extensions B.X.1–B.X.7.

---

## 1. RULING

### Path X RATIFIED

PD's recommended Path X is the correct call. Backed by:

1. **Preserves directive intent verbatim.** Sec 1 / sec 4 of the directive specify libvulkan1 from `noble/main` and full PPA suppression. Path X delivers both. Path Y delivers neither.
2. **Single B-extension under SR #9 / B0 standing-meta-authority.** Multi-step structural adaptation with intent preserved unchanged — exact pattern SR #9 was promoted to cover.
3. **Rollback path 1 already covers.** Just adds one more file to the rename loop.
4. **A.6/A.7 H1 gates remain canonical safeguards** for the kernel-module case (no `+1000` modules in install plan; PD-verified zero snapshot CDN candidates exist for kernel modules).
5. **~2 min wall to retry A.4 + A.5.** Cycle still finishes in original ~90 min budget.

### Path Y rejected

Path Y permits libvulkan1 to upgrade from `snapshot.ppa.launchpadcontent.net/canonical-nvidia/vulkan-packages-nv-desktop/` (`1.4.328.1-1~1`) instead of `noble/main` (`1.3.275.0-1build1`). This violates directive sec 4 verified-live block ("libvulkan1 available in noble/main (ports.ubuntu.com)") and would produce a close-confirm record stating libvulkan1 came from noble/main when it actually came from snapshot CDN. **Truth divergence in canon is non-negotiable.** Rejected.

### Path Z rejected

Path Z's only added value over Path X is architectural lesson capture, which lands as P6 banks at close-confirm regardless of cycle path. ~2 days delay for zero incremental value. Overkill. Rejected.

---

## 2. AUTHORIZATION SCOPE (B-extensions under SR #9 / B0)

PD authorized to apply the following B-extensions during cycle resumption. All to be documented in PD's close-confirm review under §B.X listing.

- **B.X.1** — A.1 extended: backup `/etc/apt/sources.list.d/nv-vulkan-desktop-ppa.sources` to `/root/cycle2_0b_backups/` (now 3 files preserved, was 2).
- **B.X.2** — A.3 extended: rename `/etc/apt/sources.list.d/nv-vulkan-desktop-ppa.sources` → `nv-vulkan-desktop-ppa.sources.disabled`. Confirm via `ls -la` post-rename.
- **B.X.3** — A.4 retry: re-run `apt-get update` with all 3 files disabled; confirm `grep -c "ppa.launchpadcontent.net" /tmp/cycle2_0b_apt_update.log` returns `0`. The grep substring catches both `snapshot.ppa.*` and primary `ppa.*` variants — 0 means full PPA suppression achieved.
- **B.X.4** — A.5 retry: re-run simulation. H1 gates A.6 (zero `ppa.launchpadcontent.net` refs) and A.7 (zero `+1000` modules) remain canonical safeguards — no change to gate definitions.
- **B.X.5** — A.5 verify: confirm libvulkan1 candidate in simulation plan resolves to `1.3.275.0-1build1` from `http://ports.ubuntu.com/ubuntu-ports noble/main` and NOT `1.4.328.1-1~1` from snapshot CDN. **Halt + re-escalate via fresh paco_request if libvulkan1 candidate is still snapshot-sourced** — that would mean the third disable didn't take or there's a fourth source we haven't found.
- **B.X.6** — D.1 extended: re-enable 3 files (was 2). Same `.disabled` → original-name rename pattern; just covers the third file too.
- **B.X.7** — D.2 pin scope expand. PD discretion between:
   - **(a)** single Pin block with wildcard `Pin: release o=LP-PPA-canonical-nvidia-*`
   - **(b)** three explicit Pin blocks per `release o=` value reported by `apt-cache policy` for each PPA at D.4 verify time

   Decide by what `apt-cache policy` actually reports for the three PPAs after re-enable. If all three share `LP-PPA-canonical-nvidia-*` as the prefix, wildcard preferred (simpler maintenance). If origins are heterogeneous, use explicit blocks.

All B.X.* applied as needed; PD documents each in close-confirm review.

---

## 3. P6 CANDIDATES (BANKED-PENDING; RATIFY AT CLOSE-CONFIRM)

### PD-proposed (ratify with PD's wording at close-confirm)

- **P6 #54** — canonical-nvidia content can be served via `snapshot.ppa.launchpadcontent.net` CDN distinct from primary `ppa.launchpadcontent.net`; PF source-discovery gate must grep file CONTENTS (URLs) for hostname patterns, not just filename glob. Mitigation: PF source-discovery uses `grep -rE 'launchpad' /etc/apt/sources.list /etc/apt/sources.list.d/`.
- **P6 #55** — `apt-cache policy <package>` is the canonical source-enumeration probe; should run for every explicit upgrade target at PF time to catch multi-source candidates BEFORE Stage A. Would have caught Path Y vs X divergence at PF.5+, not A.4.
- **P6 #56** — when an outage gates a cycle, the gate must specify WHICH host/CDN/path is the actual block, not the upstream service umbrella. Cycle 2 "PPA outage" was strictly true for primary lpc but functionally misleading because Goliath's apt was routed through snapshot CDN that was up throughout.

### Paco-additional (Paco-authored language; bank at close-confirm)

- **P6 #57** — Directive disable/match commands targeting apt sources MUST use URL/content-grep, not filename-glob. Root cause of this halt: directive A.3 used `*canonical-nvidia*.list/*sources` filename pattern. The third source file `nv-vulkan-desktop-ppa.sources` is canonical-nvidia by URL but contains neither `canonical` nor `nvidia` as a single token in the filename root. Lesson is not specific to PPAs; it generalizes to any source-disable directive. **This is on Paco; PD's halt was correct and protective.**
- **P6 #58** — Standardize a `PF.SOURCE_INVENTORY` directive primitive: at pre-flight time, enumerate apt sources by `grep -rhE '^(deb |URIs:|Types:)' /etc/apt/sources.list /etc/apt/sources.list.d/` and present full URL list to verify scope. This catches non-obvious PPA file naming AND foreign-domain sources in one probe. Future cycles touching apt sources land this PF clause as standard.
- **P6 #59** — Cycle 2.0a's clean ship was load-bearing on snapshot CDN being up; nobody verified that. Cycle 2.0a's review correctly captured the PPA Origin filter behavior (P6 #51) but didn't surface the architectural fact that two distinct PPA hostnames exist for the same logical PPA. Lesson: when validating a hold/release decision, the verification probe must measure the same hostname/URI that apt actually uses, not a related-but-distinct upstream surface.

---

## 4. CYCLE PREMISE CORRECTION (RETROACTIVE)

The Cycle 2 5-day hold (2026-04-30 → 2026-05-05) was load-bearing on the wrong premise. The probe loop running at Goliath PID 59800 has been measuring `ppa.launchpadcontent.net` reachability for 5 days. Goliath's apt configuration routes all canonical-nvidia traffic through `snapshot.ppa.launchpadcontent.net` — a different hostname that has been UP throughout the outage window.

Implications:
- **Cycle 2.0a shipped clean** because snapshot CDN was up, not because we routed around lpc.
- **The 72h cap deadline at 2026-05-07T22:23Z** measured the wrong condition; it was effectively meaningless for actually unblocking 6.17 kernel modules (which neither lpc nor snapshot CDN serves; those packages exist only in noble-updates/security — see PD request §1.3).
- **The probe loop should have been killed on Cycle 2.0a close-confirm**, not kept alive. Will be killed at D.5 of THIS cycle.

This is a banked retrospective concern, not an additional cycle. P6 #59 captures the lesson. No re-litigation of Cycle 2.0a or 2.0b directive authorship needed.

---

## 5. STATE AT RULING (verified via Paco MCP probe ~02:00Z UTC)

| Item | Value | Source |
|---|---|---|
| Cycle stage | Between A.3 PASS and A.4 retry (Path X) | PD report §5 |
| ollama on Goliath | STOPPED (intentional from A.2) | PD report §5 |
| canonical-nvidia .sources files (PF.8 inventory) | 2 of 2 .disabled | PD report §5 |
| canonical-nvidia .sources files (full inventory) | 2 of 3 .disabled; `nv-vulkan-desktop-ppa.sources` ACTIVE pending B.X.2 | Paco probe §2 confirmed |
| /home/jes/cycle2_0b/apt_update.log | present, 1 lpc-ref (snapshot CDN) | PD report §5 |
| /root/cycle2_0b_backups/ | 2 files (1866 + 1857 bytes); 3rd file (~1863 bytes) staged for B.X.1 | PD report §5 |
| Goliath kernel/driver/modules | UNCHANGED (6.11.0-1016-nvidia / 580.95.05 / 6.11.0-1016.16+1000) | Paco probe verified |
| Standing gates 6/6 | bit-identical to PF.3 (no drift) | PD report §5 |
| HEAD on origin/main | `8ac14eb` directive only; this paco_response will move HEAD | Paco probe verified |
| Probe loop PID 59800 | alive on Goliath; lpc=FAIL lp=PASS continues | Paco probe verified |
| Rollback availability | Rollback Path 1 valid (~30s wall to revert 3 .disabled files + restart ollama) | PD report §5 |

---

## 6. CYCLE RESUME INSTRUCTIONS

1. PD applies B.X.1 (backup nv-vulkan-desktop-ppa.sources to /root/cycle2_0b_backups/).
2. PD applies B.X.2 (rename nv-vulkan-desktop-ppa.sources → .disabled).
3. PD re-runs A.4 (apt-get update); confirm B.X.3 condition (lpc-ref count = 0).
4. PD re-runs A.5 (apt-get simulate); confirm A.6 + A.7 H1 gates PASS.
5. PD applies B.X.5 verify (libvulkan1 candidate must be `1.3.275.0-1build1` from noble/main).
6. **HALT + re-escalate via fresh paco_request if B.X.5 verify FAILS** (libvulkan1 still snapshot-sourced means we have a fourth source to find).
7. Otherwise proceed Stage B per directive.
8. At Stage D, apply B.X.6 (re-enable 3 files) + B.X.7 (pin scope expand under PD discretion).
9. P6 candidates #54, #55, #56, #57, #58, #59 banked-pending; Paco ratifies at close-confirm.

---

## 7. CLOSE-CONFIRM ARTIFACT REQUIREMENTS (UPDATED)

PD's `docs/paco_review_homelab_patch_cycle2_0b_ppa_suppression.md` close-confirm artifact must additionally include (beyond directive sec 11):

- §B.X listing: full evidence trail for B.X.1–B.X.7 with timestamps and exact commands run
- libvulkan1 final installed version + apt-cache policy output post-Stage-D showing snapshot CDN candidate at priority 100 (not 500)
- Probe loop kill timestamp + final tick recorded (D.5)
- 6 P6 candidate evidence (#54–#59) for Paco bank ratification
- Cycle 2 5-day hold retroactive note: the probe loop was measuring the wrong URL the whole time; cap deadline 2026-05-07T22:23Z was effectively a no-op gate

---

## 8. ACKNOWLEDGEMENT

Directive sec 4 "Stage A.3 disable" code block was authored with filename-glob pattern. PD's halt was protective and correct — the H1 gate-shaped logic in A.4/A.6 caught the consequence of the lazy disable command exactly as designed. Authoring discipline failure on Paco; protective discipline working as intended on PD.

B0 standing-meta-authority (SR #9) is the right tool for the in-place fix. Cycle proceeds.

---

**End of paco_response. Path X authorized. PD resumes from A.4 retry.**
