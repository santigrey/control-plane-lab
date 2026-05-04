# paco_directive_v2_3_handoff_mechanism_amendment

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-04 Day 80 ~15:25 MT (~21:25 UTC)
**Cycle:** v2.2 -> v2.3 amendment of PROJECT_ASCENSION_INSTRUCTIONS.md -- handoff-mechanism deprecation + Status-token codification
**Authority:** CEO Sloan ratified scope 2026-05-04 ~15:20 MT after Paco-side discovery that `docs/handoff_*.md` is in `.gitignore` and never reached git, while PD's Cowork instruction set already directs anchor + SESSION.md as the handoff carrier. Paco-side v2.2 boot Step 2.3 has been reading a stale local-only file the whole time.
**Repo HEAD at directive author:** `79db9e6`
**Cumulative state at author:** P6=46, SR=8 (B0 standing-meta-authority used cleanly once; HOLD on SR #9 promotion)
**Type:** Standalone directive. NOT bundled with any other cycle. Single logical unit: Paco-side instruction set amendment + companion doc version bumps + file deprecation + iCloud cross-device sync.

---

## 0. TL;DR

Paco's v2.2 SESSION-START BOOT PROTOCOL Step 2 reads `docs/handoff_pd_to_paco.md` as a canon source. That file is in `.gitignore` (line: `docs/handoff_*.md`); has never been committed to git; exists only on CK filesystem; goes stale because it doesn't sync across PD's machines. Meanwhile, PD's Cowork instruction set already directs PD to update `paco_session_anchor.md` + `SESSION.md` at every session end as the handoff carrier. **PD has been doing it right; Paco has been reading the wrong file.**

This amendment fixes Paco's instruction set:

1. **Drop** `docs/handoff_pd_to_paco.md` from Step 2 reading order
2. **Add** explicit "anchor's last `[x]` cycle line is the handoff carrier" framing
3. **Codify** PD's existing four-value Status-token taxonomy (`DONE` | `AWAITING APPROVAL` | `BLOCKED: <reason>` | `NEEDS PACO: <reason>`) as a SESSION KEY PHRASES sub-section with Paco-response mapping
4. **Add NO EXCEPTIONS clause** to lock the convention against drift
5. **Delete** the two stale handoff files from disk (they were never in git)
6. **Remove** `docs/handoff_*.md` line from `.gitignore` (no longer needed once files are gone; keeps the prefix free for future legitimate use)
7. **Bump** companion doc version references from v2.2 to v2.3 (3 files)
8. **SCP** v2.3 + 3 companions to iCloud Santigrey via Mac mini for cross-device sync (matches v2.2 ratification pattern)
9. **Out-of-band CEO action** (post-cycle): paste new v2.3 PROJECT_ASCENSION_INSTRUCTIONS.md into claude.ai Project Instructions field replacing v2.2

PD-side: ZERO instruction changes. PD's Cowork spec is already aligned (see PD spec §SESSION HYGIENE + §OUTPUT FORMAT). This amendment is Paco-instruction-set-only.

---

## 1. Verified-live block (Paco source-surface preflight per SR #7)

All probes run by Paco at directive-author time via homelab MCP read-only. P6 #44-compliant (no `/proc/<pid>/environ`).

| Surface | Probe | Verified value at author |
|---|---|---|
| v2.2 file path | `stat PROJECT_ASCENSION_INSTRUCTIONS.md` | `/home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md`, 12140 bytes, mtime 2026-05-04 17:09:51 UTC |
| v2.2 header version line | `head -3 PROJECT_ASCENSION_INSTRUCTIONS.md` | `**Version:** 2.2 (ratified 2026-05-04 Day 80 by CEO; supersedes v1.0)` |
| Step 2 line 86 (canonical) | `grep -n handoff_pd_to_paco PROJECT_ASCENSION_INSTRUCTIONS.md` | `86:3. ` + backtick + `docs/handoff_pd_to_paco.md` + backtick + ` -- full read if mtime newer than anchor` (only `handoff_*` reference in file) |
| Step 2 block boundaries | `awk '/^\*\*Step 2/,/^\*\*Step 3/'` | confirmed 6-item ordered list lines 80-86, terminated by Step 3 header line 88 |
| SESSION KEY PHRASES section | `grep -n SESSION KEY PHRASES` | line 24 (`## SESSION KEY PHRASES (CEO↔Paco protocol)`) |
| SESSION KEY PHRASES section close | `awk '/^## SESSION KEY PHRASES/,/^---$/'` | section runs lines 24-43, terminator `---` at line 43, blank line at 42 |
| Closing line of SESSION KEY PHRASES section (insertion anchor) | `sed -n '41p'` | `These are the canonical bookends. Every session starts with "boot Paco," every session ends with "update canon." No exceptions.` |
| Section dividers | `grep -nE '^---$'` | line 9 + line 43 (after SESSION KEY PHRASES); other section dividers below |
| Companion v2.2 refs | `head -5 SANTIGREY_ORG_CHART.md HARDWARE_STACK.md ALEXANDRA_PRODUCT_BRIEF.md` | all three contain `**Version:** 1.0 (companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.2)` exactly |
| `.gitignore` handoff line | `grep -n handoff .gitignore` | line containing `docs/handoff_*.md` (exact line number to be confirmed at PD preflight) |
| Handoff files on disk | `ls -la docs/handoff_*.md` | `docs/handoff_pd_to_paco.md` (1593 bytes, mtime 2026-05-04 01:24:49 UTC); `docs/handoff_paco_to_pd.md` (3211 bytes, mtime 2026-05-02 15:46:18 UTC) |
| Handoff files in git history | `git log --all --oneline -- docs/handoff_pd_to_paco.md docs/handoff_paco_to_pd.md` | empty (NEVER committed; pure-disk artifacts) |
| iCloud Santigrey Mac mini path | per HARDWARE_STACK.md companion + anchor reference to v2.2 SCP cycle | `/Users/jes/Library/Mobile Documents/com~apple~CloudDocs/AI/Santigrey/` (PD verifies at preflight) |
| Mac mini reachability | per HARDWARE_STACK.md `192.168.1.13` (Day 78 cycle noted .194 IP drift; canonical /etc/hosts has `macmini`) | PD verifies at preflight |
| Standing gates baseline (pre-cycle) | atlas-mcp PID 1212 active; atlas-agent PID 4753 NRestarts=0 active; mercury PID 7800 active; postgres-beast `2026-05-03T18:38:24.910689151Z` r=0; garage-beast `2026-05-03T18:38:24.493238903Z` r=0 | bit-identical to anchor + Bug 1+2 close-confirm |
| Repo HEAD pre-cycle | `git log --oneline -1` | `79db9e6` (canon-hygiene triage commit; supersedes `945c36c` Bug 1+2 close-confirm) |

---

## 2. Pre-flight verification (PD MUST PASS before execution)

DPF.1 — v2.2 file at canonical path:
```
stat -c '%s %y' /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md
```
Expected: ~12140 bytes (± small drift acceptable), mtime older than this directive. If size drifted >5%, halt + paco_request.

DPF.2 — v2.2 header version line:
```
head -3 /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md | tail -1
```
Expected: `**Version:** 2.2 (ratified 2026-05-04 Day 80 by CEO; supersedes v1.0)` (verbatim).

DPF.3 — Step 2 anchor block content match:
```
sed -n '80,87p' /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md
```
Expected exactly:
```
**Step 2 -- Read canon, in order:**
1. `paco_session_anchor.md` -- current state + active queues
2. `docs/feedback_paco_pre_directive_verification.md` -- first 80 lines (cumulative state, standing rules, P6 lessons)
3. `docs/handoff_pd_to_paco.md` -- full read if mtime newer than anchor
4. `DATA_MAP.md` -- DB topology, especially primary-replica naming-convention warning
5. `docs/alexandra_product_vision.md` -- full read
6. `CHARTERS_v0.1.md` -- at minimum org chart + relevant charter for this session's scope
```
If line numbers drifted but content matches at different lines, B1 authorized (apply by content match).

DPF.4 — SESSION KEY PHRASES insertion anchor present + unique:
```
grep -c 'These are the canonical bookends. Every session starts with "boot Paco," every session ends with "update canon." No exceptions.' /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md
```
Expected: `1`. If `>1` or `0`, halt + paco_request.

DPF.5 — companion docs v2.2 references (3 files):
```
for f in SANTIGREY_ORG_CHART.md HARDWARE_STACK.md ALEXANDRA_PRODUCT_BRIEF.md; do
  echo "--- $f ---"
  grep -c 'companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.2' /home/jes/control-plane/$f
done
```
Expected: each file returns `1`. If any returns `0`, halt + paco_request.

DPF.6 — handoff files on disk + NOT in git:
```
ls -la /home/jes/control-plane/docs/handoff_pd_to_paco.md /home/jes/control-plane/docs/handoff_paco_to_pd.md
cd /home/jes/control-plane && git log --all --oneline -- docs/handoff_pd_to_paco.md docs/handoff_paco_to_pd.md
```
Expected: both files exist on disk; `git log` returns empty (no commits ever touched them). If either file is tracked by git, halt + paco_request (rollback strategy must change).

DPF.7 — `.gitignore` handoff line presence:
```
grep -n 'docs/handoff_\*\.md' /home/jes/control-plane/.gitignore
```
Expected: exactly 1 line match. Capture line number for surgical removal.

DPF.8 — Mac mini reachable + iCloud Santigrey path writable:
```
ssh macmini 'ls -la "/Users/jes/Library/Mobile Documents/com~apple~CloudDocs/AI/Santigrey/" | head -10'
ssh macmini 'test -w "/Users/jes/Library/Mobile Documents/com~apple~CloudDocs/AI/Santigrey/" && echo writable || echo READONLY'
```
Expected: directory listing shows v2.2 instruction set + 3 companions; `writable`. If unreachable, B5 authorizes Mac-mini-skip with paco_request to Sloan to manually copy from CK.

DPF.9 — standing gates baseline capture:
```
ssh beast 'systemctl show -p MainPID -p NRestarts atlas-mcp.service atlas-agent.service'
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} r={{.RestartCount}}"'
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} r={{.RestartCount}}"'
```
Expected: matches Verified-live block table.

---

## 3. Execution

One-step-at-a-time per SR #3. Each step gates the next. Standing gates re-checked at end of cycle.

### Step 1 — Backups

```
cp /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md \
   /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md.bak.day80-pre-v2.3
cp /home/jes/control-plane/SANTIGREY_ORG_CHART.md \
   /home/jes/control-plane/SANTIGREY_ORG_CHART.md.bak.day80-pre-v2.3
cp /home/jes/control-plane/HARDWARE_STACK.md \
   /home/jes/control-plane/HARDWARE_STACK.md.bak.day80-pre-v2.3
cp /home/jes/control-plane/ALEXANDRA_PRODUCT_BRIEF.md \
   /home/jes/control-plane/ALEXANDRA_PRODUCT_BRIEF.md.bak.day80-pre-v2.3
cp /home/jes/control-plane/.gitignore /home/jes/control-plane/.gitignore.bak.day80-pre-v2.3
ls -la /home/jes/control-plane/*.bak.day80-pre-v2.3 /home/jes/control-plane/.gitignore.bak.day80-pre-v2.3
```

Stop condition: 5 backup files present.

### Step 2 — v2.2 -> v2.3 surgical edits to `PROJECT_ASCENSION_INSTRUCTIONS.md`

PD's discretion on tooling (write a python script to `/tmp/v2_3_patch.py` per the established pattern; sed is too brittle for multi-line replacements). Three edits, each anchored on unique content.

**Edit 2a: Header version bump**

Replace anchor (verified DPF.2 -- exact 1 hit):
```
**Version:** 2.2 (ratified 2026-05-04 Day 80 by CEO; supersedes v1.0)
```
With:
```
**Version:** 2.3 (ratified 2026-05-04 Day 80 by CEO; supersedes v2.2 — Status-token codification + handoff-mechanism deprecation)
```

**Edit 2b: Step 2 reading-order block**

Replace anchor (verified DPF.3 -- exact 1 hit):
```
**Step 2 -- Read canon, in order:**
1. `paco_session_anchor.md` -- current state + active queues
2. `docs/feedback_paco_pre_directive_verification.md` -- first 80 lines (cumulative state, standing rules, P6 lessons)
3. `docs/handoff_pd_to_paco.md` -- full read if mtime newer than anchor
4. `DATA_MAP.md` -- DB topology, especially primary-replica naming-convention warning
5. `docs/alexandra_product_vision.md` -- full read
6. `CHARTERS_v0.1.md` -- at minimum org chart + relevant charter for this session's scope
```
With:
```
**Step 2 -- Read canon, in order:**
1. `paco_session_anchor.md` -- current state + active queues. **Last `[x]` cycle line is the canonical handoff carrier from PD's most recent session.** Read it fully; that line conveys cycle outcome, awaiting-Paco items (B0 ratifications, P6 candidates), and HEAD trace.
2. `docs/feedback_paco_pre_directive_verification.md` -- first 80 lines (cumulative state, standing rules, P6 lessons)
3. `DATA_MAP.md` -- DB topology, especially primary-replica naming-convention warning
4. `docs/alexandra_product_vision.md` -- full read
5. `CHARTERS_v0.1.md` -- at minimum org chart + relevant charter for this session's scope
```

**Edit 2c: Insert new sub-section in SESSION KEY PHRASES**

Insertion anchor (verified DPF.4 -- exact 1 hit):
```
These are the canonical bookends. Every session starts with "boot Paco," every session ends with "update canon." No exceptions.
```

Replace with that anchor PLUS the inserted block following it:
```
These are the canonical bookends. Every session starts with "boot Paco," every session ends with "update canon." No exceptions.

### Cross-turn `Status:` tokens (PD↔Paco protocol)

Every PD turn ends with one of four status tokens, defined in PD's Cowork instruction set (`AWAITING APPROVAL` | `DONE` | `BLOCKED: <reason>` | `NEEDS PACO: <reason>`). Paco interprets each as the cross-turn handoff signal and acts accordingly:

| PD `Status:` | Meaning | Paco response |
|---|---|---|
| `DONE` | Cycle closed; anchor is current. Read anchor's last `[x]` cycle line for handoff state. | Process awaiting-Paco items: B0 ratifications, P6 banking, anchor status flips, close-confirm doc authoring. |
| `AWAITING APPROVAL` | PD is waiting on Sloan, not Paco. | Hold or proceed on parallel item; do not act on PD's pending work. |
| `BLOCKED: <reason>` | PD cannot proceed; reason given. | Author unblock directive if scope-appropriate; else escalate to CEO. |
| `NEEDS PACO: <reason>` | Explicit escalation TO Paco. | Respond with ruling, directive amendment, or paco_response. |

Paco mirrors the same tokens at end of Paco turns when applicable (e.g. `Status: DONE` after a close-confirm cycle ratification; `Status: AWAITING APPROVAL` after a directive draft pending CEO sign-off; `Status: BLOCKED` if Paco cannot proceed without CEO input).

### Canonical handoff carrier

The anchor's last `[x]` cycle line is the cross-session handoff state. Both sides update or read it as canonical. There is **NO file-based handoff** (`docs/handoff_pd_to_paco.md` and `docs/handoff_paco_to_pd.md` are deprecated and removed from canon as of v2.3 ratification — they were never in git, only stale local-disk artifacts that drifted across machines). PD's Cowork session-hygiene step (anchor + SESSION.md update at session end) is already the carrier per PD's own instructions; this amendment aligns Paco's reading order with what PD has been doing all along.

**NO EXCEPTIONS.** This convention is load-bearing across sessions, machines, and instances. Drift is failure.
```

Verification post-edit:
```
head -3 /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md
grep -c 'handoff_pd_to_paco' /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md
grep -c 'Cross-turn .Status: tokens' /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md
grep -c 'NO EXCEPTIONS' /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md
wc -l /home/jes/control-plane/PROJECT_ASCENSION_INSTRUCTIONS.md
```
Expected:
- header line 3 starts with `**Version:** 2.3`
- `handoff_pd_to_paco` count: 0 (cleaned)
- `Cross-turn .Status: tokens` count: 1 (new sub-section header present)
- `NO EXCEPTIONS` count: 1
- file LOC: ~+30 lines (was ~234, expect ~264 ±5)

Stop condition: any verification mismatch. Halt + paco_request.

### Step 3 — Companion doc version bumps (3 files)

```
for f in SANTIGREY_ORG_CHART.md HARDWARE_STACK.md ALEXANDRA_PRODUCT_BRIEF.md; do
  python3 -c "
from pathlib import Path
p = Path('/home/jes/control-plane/$f')
s = p.read_text()
old = '**Version:** 1.0 (companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.2)'
new = '**Version:** 1.0 (companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.3)'
assert s.count(old) == 1, f'expected 1 hit in $f, got {s.count(old)}'
p.write_text(s.replace(old, new))
print('$f bumped to v2.3 reference')
"
done
```

Verification:
```
for f in SANTIGREY_ORG_CHART.md HARDWARE_STACK.md ALEXANDRA_PRODUCT_BRIEF.md; do
  echo "--- $f ---"
  grep 'companion to PROJECT_ASCENSION_INSTRUCTIONS' /home/jes/control-plane/$f
done
```
Expected: each file shows `companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.3`.

Stop condition: any file still shows v2.2. Halt.

### Step 4 — Delete stale handoff files from disk

```
rm -v /home/jes/control-plane/docs/handoff_pd_to_paco.md
rm -v /home/jes/control-plane/docs/handoff_paco_to_pd.md
ls -la /home/jes/control-plane/docs/handoff_*.md 2>&1 | head
```
Expected: both `removed` confirmations; ls returns no matches (or `No such file or directory`).

Stop condition: either file still present. Halt.

### Step 5 — Remove `docs/handoff_*.md` line from `.gitignore`

```
python3 -c "
from pathlib import Path
p = Path('/home/jes/control-plane/.gitignore')
lines = p.read_text().splitlines()
before = len(lines)
lines = [l for l in lines if l.strip() != 'docs/handoff_*.md']
after = len(lines)
assert before - after == 1, f'expected exactly 1 line removed; removed {before - after}'
p.write_text('\n'.join(lines) + '\n')
print(f'.gitignore: {before} -> {after} lines')
"
grep -n 'handoff' /home/jes/control-plane/.gitignore || echo 'no handoff references in .gitignore (correct)'
```
Expected: line count decreases by 1; no handoff references remain.

Stop condition: line not removed or other content changed. Halt.

### Step 6 — Secrets scan + git status sanity check

```
cd /home/jes/control-plane
for f in PROJECT_ASCENSION_INSTRUCTIONS.md SANTIGREY_ORG_CHART.md HARDWARE_STACK.md ALEXANDRA_PRODUCT_BRIEF.md .gitignore; do
  echo "--- $f ---"
  grep -nE '(adminpass|sk-ant-api|sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|JSEARCH_KEY=|ADZUNA_KEY=|ANTHROPIC_API_KEY=)' "$f" 2>/dev/null && echo HIT || echo CLEAN
done
git status --short
```
Expected:
- 5 files all CLEAN
- git status: 5 modified files (4 `*.md` + `.gitignore`); 2 deleted (handoff files); .bak files untracked + ignored by `*.bak` rule already in `.gitignore`

Stop condition: any HIT or unexpected file in status. Halt.

### Step 7 — Commit + push

```
cd /home/jes/control-plane
git add PROJECT_ASCENSION_INSTRUCTIONS.md SANTIGREY_ORG_CHART.md HARDWARE_STACK.md ALEXANDRA_PRODUCT_BRIEF.md .gitignore
git add -u docs/  # picks up the two `rm` deletions
git status --short
git commit -m 'paco_directive v2.3: Status-token codification + handoff-mechanism deprecation -- v2.2->v2.3 amendment to PROJECT_ASCENSION_INSTRUCTIONS.md (Step 2 reading order drops handoff_pd_to_paco.md ref; new SESSION KEY PHRASES sub-section codifies PD four-value Status-token taxonomy with Paco-response mapping; canonical handoff carrier explicitly = anchor last [x] cycle line; NO EXCEPTIONS clause); 3 companion docs bumped v2.2->v2.3 reference; both stale handoff files deleted from disk (never in git; pure local artifacts that rotted across PD machines); .gitignore docs/handoff_*.md line removed (no longer needed); secrets scan CLEAN'
git push origin main
git log --oneline -3
```
Expected:
- commit succeeds (note: `git rm` not needed; `git add -u` picks up deletions on already-untracked-but-deleted-files)
- push succeeds; HEAD advances

Stop condition: push fails or pre-commit secrets-scan hook trips. Halt.

### Step 8 — SCP to iCloud Santigrey via Mac mini

```
for f in PROJECT_ASCENSION_INSTRUCTIONS.md SANTIGREY_ORG_CHART.md HARDWARE_STACK.md ALEXANDRA_PRODUCT_BRIEF.md; do
  scp /home/jes/control-plane/$f macmini:'"/Users/jes/Library/Mobile Documents/com~apple~CloudDocs/AI/Santigrey/"'
done
ssh macmini 'ls -la "/Users/jes/Library/Mobile Documents/com~apple~CloudDocs/AI/Santigrey/" | grep -E "PROJECT_ASCENSION|SANTIGREY_ORG|HARDWARE_STACK|ALEXANDRA_PRODUCT"'
ssh macmini 'head -3 "/Users/jes/Library/Mobile Documents/com~apple~CloudDocs/AI/Santigrey/PROJECT_ASCENSION_INSTRUCTIONS.md" | tail -1'
```
Expected:
- 4 SCP transfers succeed
- ls shows 4 fresh mtime timestamps
- head -3 of v2.3 file on iCloud shows `**Version:** 2.3` line

Stop condition: any SCP fails OR iCloud copy not at v2.3. Halt + paco_request (or B5 if iCloud unreachable).

### Step 9 — Standing gates re-check (end of cycle)

```
ssh beast 'systemctl show -p MainPID -p NRestarts atlas-mcp.service atlas-agent.service'
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} r={{.RestartCount}}"'
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} r={{.RestartCount}}"'
```
Expected: bit-identical to DPF.9 baseline (this is a doc-only cycle; gates MUST NOT move).

Stop condition: any gate moved. Halt + paco_request (substrate drift unrelated to this cycle but worth flagging).

---

## 4. Acceptance Criteria

### MUST-PASS

- **AC.1** `PROJECT_ASCENSION_INSTRUCTIONS.md` line 3 contains `**Version:** 2.3 (ratified 2026-05-04 Day 80 by CEO; supersedes v2.2 — Status-token codification + handoff-mechanism deprecation)`.
- **AC.2** Step 2 reading order in v2.3 is 5 items (was 6); item 3 is no longer `docs/handoff_pd_to_paco.md`; item 1 prose explicitly names "last `[x]` cycle line is the canonical handoff carrier."
- **AC.3** New sub-section `### Cross-turn \`Status:\` tokens (PD↔Paco protocol)` present in SESSION KEY PHRASES section, containing the 4-row table and Paco-mirroring sentence.
- **AC.4** New sub-section `### Canonical handoff carrier` present, containing the explicit deprecation language for `handoff_*.md` files and the literal **`NO EXCEPTIONS.`** sentence.
- **AC.5** `grep -c 'handoff_pd_to_paco' PROJECT_ASCENSION_INSTRUCTIONS.md` returns `0`.
- **AC.6** All 3 companion docs (SANTIGREY_ORG_CHART.md, HARDWARE_STACK.md, ALEXANDRA_PRODUCT_BRIEF.md) header line shows `companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.3`.
- **AC.7** `docs/handoff_pd_to_paco.md` and `docs/handoff_paco_to_pd.md` no longer exist on CK filesystem.
- **AC.8** `.gitignore` no longer contains `docs/handoff_*.md` line; `grep handoff .gitignore` returns no matches.
- **AC.9** Single git commit on `main` covering all 4 doc edits + .gitignore + 2 file deletions; HEAD advances cleanly; push succeeds.
- **AC.10** All 4 doc files copied to iCloud Santigrey path on Mac mini; iCloud `PROJECT_ASCENSION_INSTRUCTIONS.md` `head -3` shows v2.3 ratification line.
- **AC.11** Standing gates 6/6 bit-identical pre/post (this is doc-only; gates MUST NOT move).
- **AC.12** Both secrets-scan layers CLEAN on all 5 modified files.

### SHOULD-PASS

- **AS.1** v2.3 file LOC delta within +25 to +40 lines vs v2.2 (sanity check on the new sub-section size).
- **AS.2** All 5 backup files (`.bak.day80-pre-v2.3`) preserved at execution end for one cycle of caution.
- **AS.3** Git commit message references the cycle outcomes from this directive.

---

## 5. Path B authorizations (SR #4 + B0 standing-meta-authority)

- **B0 (CEO standing meta-authority -- second invocation):** PD authorized to verify Paco's source-surface claims (line numbers, file paths, anchor text exactness, command syntax) at execution time and adapt to ground truth WITHOUT halting, when error is structural/clerical AND adaptation preserves directive intent UNCHANGED AND adaptation is documented in review (Paco-stated -> PD-observed -> PD-applied -> rationale). **Second clean-usage of B0 in this cycle would qualify B0 for SR #9 promotion at close-confirm**; PD's review should explicitly call out whether B0 was invoked and whether adaptations were structural-only.
- **B1 (line-number drift):** if `sed -n` line ranges don't match exact content but `grep -c` of anchor strings returns expected count, PD applies edit by content match. Document line drift in review.
- **B2 (sed vs python tooling):** PD discretion. Recommended pattern: write script to `/tmp/v2_3_patch.py`, execute via `python3`, verify with grep counts. sed for multi-line replacements is too brittle (P6 #5 lesson).
- **B3 (`.gitignore` line-number variance):** if `grep -n 'docs/handoff_\*\.md'` returns different line number than implied, edit by exact-string match (Step 5 python script does this correctly already).
- **B4 (companion-doc version reference variants):** if any companion doc has alternate phrasing like `companion-to-v2.2` or `paco v2.2`, PD applies the closest content-equivalent edit and documents in review. Halt only if NO companion-version reference exists at all.
- **B5 (iCloud Mac mini unreachable):** if Step 8 SCP fails on Mac mini reachability (not on transfer), PD halts SCP step ONLY (not the whole cycle), commits canon work (Steps 1-7 + 9), writes paco_request flagging iCloud sync-pending, dispatches to CEO for manual Sloan-side iCloud copy from CK. Cycle CLOSES PARTIAL with iCloud sync deferred.

### NOT authorized (halt + paco_request)

- Modifying any section of PROJECT_ASCENSION_INSTRUCTIONS.md outside of header line 3, Step 2 block, and SESSION KEY PHRASES section.
- Modifying companion docs beyond the single `companion to PROJECT_ASCENSION_INSTRUCTIONS.md vX.Y` line.
- Modifying any file other than the 5 named (PROJECT_ASCENSION_INSTRUCTIONS.md + 3 companions + .gitignore) plus the 2 deletions.
- Bumping companion-doc Version field from `1.0` (only the `companion to ... v2.2` reference changes; the companion's own version stays 1.0).
- Adding any content to v2.3 not listed in Edit 2a/2b/2c.
- Skipping secrets scan.
- Force-pushing or rewriting git history.

---

## 6. Rollback

### v2.3 rollback (full revert to v2.2)
```
cd /home/jes/control-plane
cp PROJECT_ASCENSION_INSTRUCTIONS.md.bak.day80-pre-v2.3 PROJECT_ASCENSION_INSTRUCTIONS.md
cp SANTIGREY_ORG_CHART.md.bak.day80-pre-v2.3 SANTIGREY_ORG_CHART.md
cp HARDWARE_STACK.md.bak.day80-pre-v2.3 HARDWARE_STACK.md
cp ALEXANDRA_PRODUCT_BRIEF.md.bak.day80-pre-v2.3 ALEXANDRA_PRODUCT_BRIEF.md
cp .gitignore.bak.day80-pre-v2.3 .gitignore
# Restore handoff files from backup ONLY if they existed on disk pre-cycle:
# (they were never in git, so git history won't restore them; they were stale)
# PD writes new empty handoff files only if rollback explicitly requires:
# touch docs/handoff_pd_to_paco.md docs/handoff_paco_to_pd.md  # NO -- leave deleted in rollback; they were stale
```

### iCloud rollback
- Manual: SCP v2.2 backups from CK to Mac mini iCloud Santigrey path. Or have Sloan revert iCloud-side via Apple's file history.

### Git rollback (if commit + push went out)
- `git revert <commit-sha> -m 'revert v2.3 amendment'` + push. Preserves audit trail.

### Rollback acceptance
- v2.3 doc files byte-identical to backups (`cmp -s`).
- Standing gates 6/6 bit-identical.
- iCloud Santigrey shows v2.2.
- claude.ai Project Instructions field still shows v2.2 (CEO action: paste back the v2.2 text from `*.bak.day80-pre-v2.3`).

---

## 7. Close-confirm artifacts (PD writes)

- `docs/paco_review_v2_3_handoff_mechanism_amendment.md` covering:
  - DPF.1–DPF.9 outputs verbatim
  - Step 1–9 commands run + outputs
  - AC.1–AC.12 PASS/FAIL/DEFERRED with evidence quotes (especially AC.10 iCloud sync verification head -3 output; if B5 invoked, AC.10 marked DEFERRED with paco_request reference)
  - AS.1–AS.3 PASS/FAIL
  - Standing gates pre/post comparison table
  - B0 invocation status: explicitly state YES (with adaptations table) or NO (clean first-try). **This is the data point that promotes B0 to SR #9 at Paco close-confirm.**
  - Path B applied (B1–B5) + rationale
  - Secrets scan results (broad + literal sweep)
  - Rollback NOT executed (or, if executed, full trace)
- Both secrets-scan layers + literal-sweep CLEAN before commit (P6 #34 forward-redaction)
- Single git commit on `control-plane` for the v2.3 amendment
- No anchor / SESSION.md update by PD; Paco handles at close-confirm-ratification (or this directive's close-confirm could combine with `update canon` if Sloan triggers session-end at the same time)

---

## 8. Pre-flight-checked code surface (Paco verification per P6 #42)

- **Indent convention:** Python scripts in `/tmp/` use 4-space indent (matches v2.2 internal Python conventions in orchestrator/).
- **HTTP method:** N/A this cycle (no service health checks needed; this is doc + git + scp).
- **Restart requirement:** NONE. Doc-only cycle. No service restart required. Standing gates MUST NOT move.
- **DB target:** N/A this cycle.
- **Env handling:** N/A; no secrets touched. Secrets scan applied as defense-in-depth.
- **Python script tooling pattern:** per established convention from Bug 1+2 cycle Step 2 (write to `/tmp/<name>.py`, execute via `python3`, verify via `grep -c`). Avoids sed multi-line brittleness (P6 #5).
- **iCloud SCP path quoting:** path contains spaces (`Mobile Documents`); quote double-wrapped for SCP (`'"..."'`) to survive both ssh and shell parse.
- **Backup naming:** `.bak.day80-pre-v2.3` follows the `.bak.day80-pre-*` convention from Alexandra hygiene + Bug 1+2 cycles (rollback discoverability via consistent prefix).
- **`git add -u`:** correctly picks up file deletions for files that were tracked. Handoff files were NEVER tracked, so `git add -u docs/` is a no-op for them (no error). The `rm` in Step 4 is the actual deletion mechanism.

---

## 9. Out-of-band CEO action (post-cycle)

After PD close-confirm + Paco ratification land, **CEO Sloan must paste new v2.3 PROJECT_ASCENSION_INSTRUCTIONS.md into the claude.ai Project Instructions field** to activate v2.3 governance for next session. Companion docs (3) replace the v2.2 versions in the Project files attachment area. Paco close-confirm doc will include explicit reminder + iCloud path + claude.ai navigation hint.

This CEO action is OUT OF SCOPE for PD execution. PD's cycle closes with Step 8 iCloud sync; CEO action lands the activation.

---

— Paco
