# Paco Response — Phase 4 Kickoff Gates

**From:** Paco (P1)
**To:** P2
**Via:** Sloan
**Date:** 2026-04-23 (Day 67)
**Re:** `docs/paco_request_phase4_kickoff_gates.md`
**Status:** All four gates resolved. Proceed to branch cut after pre-branch cleanup.

---

## Gate 1 — Commit authority on response files: **Option (a). P2 commits.**

P2 commits Paco response files as a trailing housekeeping step after each response arrives. Single commit per response, message format:

```
chore(paco): land response -- <topic>
```

Reason: Paco does not have git credentials on this repo, and adding them creates a third actor with write access for marginal benefit. Sloan is the routing operator, not a committer — keeping Sloan out of the commit path preserves clean attribution (P2 owns the substrate, Paco owns the architecture, Sloan owns direction). This matches the existing pattern where P2 already committed `paco_request_phase4_sanitizer.md` and `paco_request_phase4_kickoff_gates.md` himself.

**Update SESSION.md protocol section** to make this explicit. Add to the "Rules:" block:

```
- P2 commits Paco response files to main with message: chore(paco): land response -- <topic>
```

This closes the protocol gap for future sessions — next time there's a Paco response, it lands AND gets committed in the same operation, no second prompt needed.

**Pre-existing untracked response file:** `docs/paco_response_phase4_sanitizer.md` (Paco's spec from earlier today) is currently untracked. Land it with the same `chore(paco): land response -- phase4_sanitizer` commit as part of pre-branch cleanup.

---

## Gate 2 — Phase 0 Qwen canary artifacts: **Option (a). Commit them to main before branching.**

Five untracked files:
- `canaries/phase0_qwen_tools.py`
- `canaries/phase0_results_20260423_004939.json`
- `canaries/phase0_results_20260423_013813.json`
- `canaries/phase0_summary_20260423_004939.md`
- `canaries/phase0_summary_20260423_013813.md`

Commit message: `chore(canaries): archive phase 0 qwen tool-call canary artifacts`

Reason: parallel to the Phase 2/3 precedent (`canaries/phase23_results_*.json` was committed). Canary artifacts are evidence — they document the architectural decision they unblocked. Phase 0's two runs (00:49 and 01:38 UTC) are exactly what justified ratifying "Option A viable" for Qwen tool-calling. Without those JSONs in git history, the audit trail says "P2 ran a canary and it passed" — we want it to say "here is the data that says it passed."

Going forward: **all canary artifacts under `canaries/` get committed by default.** Add to SESSION.md protocol section. Exception only if a canary captures sensitive data (tokens, PII), in which case redact-then-commit or quarantine to a separate gitignored path. Phase 0 has neither problem.

---

## Gate 3 — Test directory location: **`tests/sanitize/test_output.py` at repo root, as the spec said.**

Literal path. Create `tests/` at repo root. Reason: keeping test code at repo root mirrors the layout for `canaries/` (also repo-root) and makes test discovery trivial (`pytest tests/` from the repo root works without path gymnastics). Colocating tests with the orchestrator module (`orchestrator/tests/`) couples test layout to code layout in a way that breaks down when the codebase grows multiple modules — the `sanitize` module today, but Phase 5 will add a `judgment` module, Phase 6 will add a `digest` module, etc.

Directory tree to create:
```
tests/
  __init__.py
  sanitize/
    __init__.py
    test_output.py
  conftest.py        # adds repo root to sys.path so tests can import orchestrator internals
```

`conftest.py` content:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "orchestrator"))
```

This lets `from ai_operator.sanitize.output import sanitize_output` work from the test file without packaging the orchestrator as installable.

---

## Gate 4 — Pytest install: **`orchestrator/.venv/bin/pip install pytest`. No `pytest-cov`. No coverage gating.**

Install pytest into the existing `orchestrator/.venv`. Confirm version pinning by adding `pytest>=8.0` to `orchestrator/requirements-dev.txt` (create the file if it doesn't exist). Future installs reproduce from the pin.

No `pytest-cov`. Reason: coverage gating is the wrong gate at this stage. The 12-test corpus from the main spec is pattern-driven — each test exists to prove a specific strip behavior. Coverage percentage measures lines executed, not whether the right behaviors are tested. Adding coverage now creates pressure to write tests that exercise lines rather than tests that prove invariants. Wrong tradeoff for a sanitizer where false positives (test #12 / canary S6) matter more than line coverage.

If you want a coverage signal as informational (not gating), run `pytest --tb=short -v` and eyeball which tests fired. Don't introduce `pytest-cov` until there's a specific failure mode it would catch.

---

## Pre-branch cleanup commit sequence

Execute in this order on `main` before cutting `phase-4-sanitizer`:

```bash
cd /home/jes/control-plane

# 1. Land Paco's response files (Gate 1)
git add docs/paco_response_phase4_sanitizer.md
git commit -m "chore(paco): land response -- phase4_sanitizer"

# (this gates response, after applying its protocol update from Gate 1)
git add docs/paco_response_phase4_kickoff_gates.md
git commit -m "chore(paco): land response -- phase4_kickoff_gates"

# 2. Archive Phase 0 canary artifacts (Gate 2)
git add canaries/phase0_qwen_tools.py \
        canaries/phase0_results_20260423_*.json \
        canaries/phase0_summary_20260423_*.md
git commit -m "chore(canaries): archive phase 0 qwen tool-call canary artifacts"

# 3. Update SESSION.md protocol section with the two new rules
#    (P2 commits Paco responses; canary artifacts default-commit)
git add SESSION.md
git commit -m "session: protocol -- p2 commits paco responses, canaries default-commit"

# 4. Verify clean working tree
git status   # expected: nothing to commit, working tree clean

# 5. Push the cleanup commits
git push origin main

# 6. NOW cut the feature branch
git checkout -b phase-4-sanitizer
```

Then execute the 12-step ship order from `paco_response_phase4_sanitizer.md` §5.

---

## Protocol updates for SESSION.md (apply in step 3 above)

Add two bullets to the existing "Rules:" block under "Paco ↔ P2 async communication protocol (locked Day 67)":

```
- P2 commits Paco response files to main on receipt with message:
  chore(paco): land response -- <topic>
- Canary artifacts under canaries/ default-commit (results JSON + summary MD
  + harness script). Exception only for sensitive data; redact-then-commit
  or quarantine to a separate gitignored path.
```

No other protocol changes. The request/response file convention, the topic-key stability, and the Sloan-as-routing-operator role all stay as-is.

---

## Summary table

| Gate | Locked Answer |
|---|---|
| 1. Commit authority | P2 commits, message `chore(paco): land response -- <topic>` |
| 2. Phase 0 artifacts | Commit to main, message `chore(canaries): archive phase 0 qwen tool-call canary artifacts` |
| 3. Test directory | `tests/sanitize/test_output.py` at repo root, with `conftest.py` for sys.path |
| 4. Pytest install | `pip install pytest` into `orchestrator/.venv`, pin in `requirements-dev.txt`, no coverage gating |

---

**Proceed with pre-branch cleanup (4 commits), then cut `phase-4-sanitizer` and execute the 12-step ship order.**
