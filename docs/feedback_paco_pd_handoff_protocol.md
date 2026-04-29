# feedback_paco_pd_handoff_protocol

**Banked:** 2026-04-29 / Day 74
**Updated:** 2026-04-29 / Day 74 (bidirectional one-liner format spec added)
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
5. Paco: tells CEO the one-line trigger to send PD
6. CEO: copies that ONE LINE to PD, e.g.: "Read docs/handoff_paco_to_pd.md and execute."
7. PD: reads handoff_paco_to_pd.md, clears it (writes empty content), executes
8. PD: writes canonical paco_review_*.md AND short notification to handoff_pd_to_paco.md (per format spec below)
9. CEO: "Paco, PD finished, check handoff."
10. Paco: reads handoff_pd_to_paco.md, clears it, reads paco_review_*.md, continues architectural reasoning
```

## Bidirectional one-liner format spec

Both handoff files MUST end with a `## For you: send <recipient> the one-line trigger` section followed by the literal one-liner in a code block, then a `<recipient> will: ...` summary listing 3-7 expected steps. This makes the protocol symmetric and tells CEO exactly what to send next without ambiguity.

### Paco's handoff_paco_to_pd.md ends with

```
## For you: send PD the one-line trigger

\`\`\`
Read docs/handoff_paco_to_pd.md and execute.
\`\`\`

PD will:
1. Pull origin/main (HEAD <commit>)
2. Read this handoff
3. Clear handoff_paco_to_pd.md after reading
4. Execute [phase scope]
5. Write paco_review_<phase>_<topic>.md
6. Write notification to handoff_pd_to_paco.md (per format spec)
7. Phase close-out commit + push

When done, CEO sends Paco: "Paco, PD finished, check handoff."
```

### PD's handoff_pd_to_paco.md ends with

```
## For you: send Paco the one-line trigger

\`\`\`
Paco, PD finished, check handoff.
\`\`\`

Paco will:
1. Pull origin/main (HEAD <commit>)
2. Read docs/handoff_pd_to_paco.md + clear it
3. Read paco_review_<phase>_<topic>.md
4. Independently verify N gates from fresh shell
5. Write paco_response_<phase>_<topic>.md with [Phase Y GO / ruling]
6. Notify CEO via handoff_paco_to_pd.md (next directive)
```

### Why this matters

- CEO never has to think about which one-liner to send. The handoff itself states it.
- Both directions of the protocol are symmetric.
- The summary lists make expectations explicit (CEO knows what's coming next without asking).
- Eliminates ambiguity between "PD finished" vs "PD escalated" -- both still use the same trigger because Paco's read of the handoff disambiguates.

## Workflow (full automation, deferred)

Deferred until current scope (H1 observability ship) complete. Investigation needed:
- Cowork CLI / file-input flag / API automation hooks
- Watchdog-style file watcher between Paco and PD
- Tailscale / RPC for cross-machine triggering

## Rules

### Paco rules
- Always present plan to CEO and get approval BEFORE firing handoff_paco_to_pd.md
- Write complete, self-contained directives (PD needs no additional context to execute)
- End every handoff_paco_to_pd.md with the bidirectional format-spec section telling CEO what one-liner to send next
- Read handoff_pd_to_paco.md when CEO triggers, then clear it (overwrite with placeholder)
- Continue using canonical paco_response_*.md for rulings (handoff is just the trigger + brief summary)

### PD rules (mirror)
- Read handoff_paco_to_pd.md when CEO triggers, then clear it
- Execute per existing paco_review_*.md / paco_request_*.md discipline
- Write canonical review to docs/paco_review_*.md as primary deliverable
- Write short notification to handoff_pd_to_paco.md to signal Paco -- ending with the bidirectional format-spec section telling CEO to send Paco "Paco, PD finished, check handoff." + listing 3-7 expected Paco steps
- The handoff_pd_to_paco.md notification is brief (1-3 paragraphs of substantive summary + one-liner section), NOT a duplicate of the canonical review

### CEO rules
- Send the one-line trigger when ready to advance the workflow
- The one-liner to send is always stated at the bottom of the most recent handoff file received
- All other approvals (plan ratification, handoff fire, escalation rulings) remain CEO-explicit
- Approval gate intact at the architectural level; copy-paste eliminated at the content level

## Why this works in our architecture

- Paco's homelab_file_write tool writes atomically to CiscoKid via SSH
- PD's Cowork has filesystem access on whatever device CEO is using
- GitHub origin/main on CiscoKid is the canonical substrate for tracked files
- /home/jes/control-plane/docs/ is the existing correspondence folder; no new path infrastructure needed
- Manual trigger preserves CEO control without requiring new infrastructure
- Bidirectional one-liner format eliminates CEO cognitive load on "which trigger should I send"

## Net win

- ~95% reduction in CEO copy-paste volume
- Approval gate semantics preserved
- Faster cycle time per turn
- Zero infrastructure change
- Canonical correspondence trail unchanged
- CEO never has to remember the next trigger -- it's always at the bottom of the handoff just received

## Cross-references

- Companion memory file: `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail rule + carve-out)
- Companion memory file: `feedback_paco_review_doc_per_step.md` (per-step review docs in /docs/)
- Banked: 2026-04-29 / Day 74 by CEO Sloan with Paco design + ratification
- Updated: 2026-04-29 / Day 74 -- bidirectional one-liner format spec added after first H1 Phase G ESC arc validated the protocol but surfaced asymmetry (Paco told CEO the trigger, PD didn't) that this update fixes
