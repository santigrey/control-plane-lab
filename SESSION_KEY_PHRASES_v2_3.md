# Project Ascension -- Session Key Phrases (v2.3 quick reference)

**Version:** 2.0 (rewritten 2026-05-04 Day 80 session-close per CEO feedback that PD<->Paco directions were implicit; companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.3 + PD_COWORK_INSTRUCTIONS_v2_3.md)
**Purpose:** One-page reference for the canonical phrases and channels driving Project Ascension's CEO/Paco/PD session protocol. If this card and v2.3 instructions disagree, v2.3 instructions win.

---

## All six communication directions

Project Ascension has three agents (CEO, Paco, PD) and three channels (claude.ai chat, Cowork app, git canon). Six directional flows total. ALL are explicit.

| # | Direction | Phrase / Mechanism | Channel | Trigger |
|---|---|---|---|---|
| 1 | **CEO -> Paco** | `boot Paco` | claude.ai chat | Session start |
| 2 | **CEO -> Paco** | `update canon` | claude.ai chat | Session end |
| 3 | **CEO -> Paco** | Free-form prompts | claude.ai chat | Mid-session ("approved", "go", "check X") |
| 4 | **Paco -> CEO** | `Status: <token>` at end of every Paco turn | claude.ai chat | Every turn |
| 5 | **CEO -> PD** | Cowork dispatch (paste paco_directive_*.md path or full text) | Cowork app | Per cycle |
| 6 | **PD -> CEO** | `Status: <token>` at end of every PD turn | Cowork app | Every turn |
| 7 | **Paco -> PD** | `paco_directive_*.md` committed to canon | git canon | Per cycle (via CEO dispatch) |
| 8 | **PD -> Paco** | Anchor's last `[x]` cycle line + `paco_review_*.md` committed to canon | git canon (read at next `boot Paco`) | Cycle close |

Directions 7 + 8 are the **asynchronous PD<->Paco loop**. They're not chat; they're file-based via git. Both agents read canon at session boot.

---

## Status token taxonomy (canonical, both directions)

Both Paco and PD end every turn with one of these four:

| Token | Meaning | What the receiver does |
|---|---|---|
| `Status: DONE` | Cycle/turn closed cleanly. Anchor reflects current state. | Receiver reads anchor's last `[x]` cycle line for handoff. Process awaiting items. |
| `Status: AWAITING APPROVAL` | Sender is waiting on Sloan, not the other agent. | Sloan responds. The other agent holds or proceeds on parallel work; does not act on the pending item. |
| `Status: BLOCKED: <reason>` | Sender halted on a blocker; reason given. | Receiver may author an unblock directive (Paco) or escalate to CEO. |
| `Status: NEEDS PACO: <reason>` | Explicit escalation TO Paco. | Paco responds with a ruling, directive amendment, or paco_response. |

*(`NEEDS CEO` is the Paco-side mirror of `NEEDS PACO`; informally valid; v2.4 candidate for formal codification.)*

---

## Canonical handoff carrier

The **anchor's last `[x]` cycle line** is the cross-session handoff state. Both Paco and PD update or read it as canonical.

**`docs/handoff_pd_to_paco.md` and `docs/handoff_paco_to_pd.md` are DEPRECATED as of v2.3** -- never write to them. They were never in git, only stale local-disk artifacts that drifted across machines.

**NO EXCEPTIONS.** This convention is load-bearing across sessions, machines, and instances. Drift is failure.

---

## What goes into the anchor's last `[x]` line

When PD closes a cycle and writes the anchor's last `[x]` line for Paco to read at next boot, that line should contain:

1. **Cycle name + status** (`CLOSE-CONFIRM-READY` / `CLOSED-CONFIRMED` / `BLOCKED` / etc.)
2. **Date/time stamp** in MT and UTC
3. **AC verdict** (e.g. `13/13 MUST + 3/3 SHOULD PASS`)
4. **Standing gates state** (typically `6/6 bit-identical pre/mid/post`)
5. **HEAD trace** (commit SHAs in chain)
6. **B0/SR #9 invocations** (if any; documented as Paco-stated -> PD-observed -> PD-applied -> rationale)
7. **P6 candidates** for Paco to bank at close-confirm
8. **Awaiting-Paco items** (B0 ratifications, P6 banks, anchor flips, close-confirm doc authoring)
9. **Cumulative state delta** (P6 count, SR count, B0 promotion status)

When Paco closes a cycle (close-confirm), the line records ratification + cumulative state landing.

---

## Session start / session end protocol

### Session start (CEO opens)

```
CEO: "boot Paco"
Paco: [Step 1: verify time + location]
Paco: [Step 2: read canon in order]
      1. paco_session_anchor.md (last [x] line is the handoff)
      2. docs/feedback_paco_pre_directive_verification.md (first 80 lines)
      3. DATA_MAP.md
      4. docs/alexandra_product_vision.md
      5. CHARTERS_v0.1.md
Paco: [Step 3: run boot probes; quote outputs]
Paco: [Step 4: state understanding back in 5-7 bullets]
Paco: "Status: DONE" (or "Status: AWAITING APPROVAL" if waiting for ask)
```

### Session end (CEO closes)

```
CEO: "update canon"
Paco: 1. Surgical update to paco_session_anchor.md (date stamp + cycle outcomes + cumulative state)
Paco: 2. Append section to SESSION.md (date + completed work + pending + HEAD trace)
Paco: 3. Append P6/SR entries to docs/feedback_paco_pre_directive_verification.md if applicable
Paco: 4. git add + commit + push
Paco: 5. Confirm HEAD moved + tail of each artifact
Paco: "Status: DONE"
```

---

## Cycle close protocol (PD-side -> Paco-side, async via canon)

### PD finishes a directive cleanly

```
PD: [executes 8-element directive from docs/paco_directive_*.md]
PD: [writes docs/paco_review_*.md with AC table + B0 adaptations + P6 candidates]
PD: [updates anchor's last [x] cycle line as CLOSE-CONFIRM-READY]
PD: [updates SESSION.md with cycle trace]
PD: [git add + commit + push]
PD: "For Paco at next session boot: read anchor -- last entry surfaces cycle outcome + B0 adaptations awaiting ratification + P6 candidates to bank."
PD: "Status: DONE"
```

### Paco picks up the handoff at next boot

```
CEO: "boot Paco"
Paco: [reads anchor's last [x] line FIRST per Step 2 reading order]
Paco: [identifies awaiting-Paco items: B0 ratifications, P6 banks, anchor flips]
Paco: [reads docs/paco_review_*.md for full evidence]
Paco: [authors docs/paco_response_*_close_confirm.md ratifying or amending]
Paco: [flips anchor entry from CLOSE-CONFIRM-READY to CLOSED-CONFIRMED]
Paco: [appends P6 entries to ledger if applicable]
Paco: [git add + commit + push]
Paco: "Status: DONE"
```

---

## Quick examples

### Paco dispatches a directive draft, awaiting CEO sign-off
```
Paco: [authors directive to /tmp/; presents scope summary]
Paco: "Status: AWAITING APPROVAL"
```

### Paco escalates to CEO mid-cycle
```
Paco: [catches scope mismatch between observed state and directive intent]
Paco: "Status: NEEDS CEO: Sloan-committed spec 3f30fed diverges from MCP-shipped edits; reconciliation path required."
```

### PD halts on a blocker
```
PD: "Cannot proceed: orchestrator returns 503 on /healthz; suspect nginx upstream timeout."
PD: "Status: BLOCKED: nginx upstream timeout on /healthz; need Paco unblock directive or CEO override."
```

### PD escalates to Paco mid-cycle
```
PD: [discovers directive AC.6 verbiage `linux-modules-nvidia-580` filter doesn't match apt-get -s output]
PD: "Status: NEEDS PACO: filter regex doesn't match Origin display; B1 Path B candidate but scope expansion may be required."
```

---

## What this protocol replaces

- File-based handoff (`docs/handoff_*.md`) -- DEPRECATED v2.3.
- Implicit / unstated turn closures -- replaced by explicit Status token.
- Paco's session-start file-reading order item 3 (the old handoff file) -- replaced by anchor last `[x]` line.
- v1.0 of this card had a single 5-row matrix that only made CEO<->Paco and Paco<->PD explicit but not the asynchronous canon-mediated PD<->Paco loop. v2.0 surfaces all six directions.

---

## Cross-references

- Paco-side spec: `PROJECT_ASCENSION_INSTRUCTIONS.md` v2.3 SESSION KEY PHRASES section
- PD-side spec: `PD_COWORK_INSTRUCTIONS_v2_3.md` CROSS-TURN HANDOFF (PD <-> PACO) section
- Source canon for handoff carrier: `paco_session_anchor.md` last `[x]` cycle line
- Ratified: 2026-05-04 Day 80 by CEO; v2.0 of this card written at session-close from Mac mini transitioning to Cortez

---

**End of session key phrases v2.0 quick reference (v2.3-aligned).**
