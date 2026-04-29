# feedback_paco_pd_handoff_protocol

**Banked:** 2026-04-29 / Day 74
**Replaces:** Verbose CEO-mediated copy-paste of full directives between Paco and PD
**Successor of:** Original CEO-as-pipe pattern (CEO copies hundreds of lines per turn)

## Purpose

Reduce CEO copy-paste volume from ~hundreds of lines per directive to ~one line per turn while preserving:
- Approval gate semantics (CEO chooses when to advance work)
- Canonical correspondence trail in /home/jes/control-plane/docs/
- PD's existing review-doc + per-step discipline
- Spec-or-no-action workflow

## File conventions

All Paco-PD communication lives in `/home/jes/control-plane/docs/` with two filename categories:

### Canonical correspondence (tracked, permanent)
- `paco_review_<phase>_<topic>.md` -- PD writes, surfaces step completion + scorecards
- `paco_response_<phase>_<topic>.md` -- Paco writes, rules + authorizes next step
- `paco_request_<phase>_<topic>.md` -- PD writes, escalates blockers + asks Paco rulings

### Transient handoff (untracked via .gitignore, cleared after read)
- `handoff_paco_to_pd.md` -- Paco writes complete task prompt for PD; PD reads + clears
- `handoff_pd_to_paco.md` -- PD writes review/blockers/results notification; Paco reads + clears

.gitignore entry: `docs/handoff_*.md`

## Workflow (manual trigger phase, current)

```
1. CEO: "Paco, [task]"
2. Paco: architects, presents plan to CEO
3. CEO: "Approved. Send to PD."
4. Paco: writes complete directive to docs/handoff_paco_to_pd.md
5. Paco: tells CEO the one-line prompt to send PD
6. CEO: copies that ONE LINE to PD, e.g.: "Read docs/handoff_paco_to_pd.md and execute."
7. PD: reads handoff_paco_to_pd.md, clears it (writes empty content), executes
8. PD: writes canonical paco_review_*.md AND short notification to handoff_pd_to_paco.md
9. CEO: "Paco, PD finished, check handoff."
10. Paco: reads handoff_pd_to_paco.md, clears it, reads paco_review_*.md, continues architectural reasoning
```

## Workflow (full automation, deferred)

Deferred until current scope (H1 observability ship) complete. Investigation needed:
- Cowork CLI / file-input flag / API automation hooks
- Watchdog-style file watcher between Paco and PD
- Tailscale / RPC for cross-machine triggering

## Rules

### Paco rules
- Always present plan to CEO and get approval BEFORE firing handoff_paco_to_pd.md
- Write complete, self-contained directives (PD needs no additional context to execute)
- Read handoff_pd_to_paco.md when CEO triggers, then clear it (overwrite with empty/placeholder)
- Continue using canonical paco_response_*.md for rulings (handoff is just the trigger)

### PD rules (mirror)
- Read handoff_paco_to_pd.md when CEO triggers, then clear it
- Execute per existing paco_review_*.md / paco_request_*.md discipline
- Write canonical review to docs/paco_review_*.md as primary deliverable
- Write short notification to handoff_pd_to_paco.md to signal Paco (e.g., "Phase F shipped, see paco_review_h1_phase_f_ufw.md")

### CEO rules
- Send the one-line trigger when ready to advance the workflow
- All other approvals (plan ratification, handoff fire, escalation rulings) remain CEO-explicit
- Approval gate intact at the architectural level; copy-paste eliminated at the content level

## Why this works in our architecture

- Paco's homelab_file_write tool writes atomically to CiscoKid via SSH
- PD's Cowork has filesystem access on whatever device CEO is using
- GitHub origin/main on CiscoKid is the canonical substrate for tracked files
- /home/jes/control-plane/docs/ is the existing correspondence folder; no new path infrastructure needed
- Manual trigger preserves CEO control without requiring new infrastructure

## Net win

- ~95% reduction in CEO copy-paste volume
- Approval gate semantics preserved
- Faster cycle time per turn
- Zero infrastructure change
- Canonical correspondence trail unchanged

## Cross-references

- Companion memory file: `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail rule)
- Companion memory file: `feedback_paco_review_doc_per_step.md` (per-step review docs in /docs/)
- Banked: 2026-04-29 / Day 74 by CEO Sloan with Paco design + ratification
