# Project Ascension -- Session Key Phrases (v2.3 quick reference)

**Version:** 1.0 (companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.3 + PD_COWORK_INSTRUCTIONS_v2_3.md)
**Purpose:** One-page reference for the canonical phrases that drive Project Ascension's CEO/Paco/PD session protocol. If this card and v2.3 instructions disagree, instructions win.

---

## At a glance

| When | Who says it | The phrase | What it triggers |
|---|---|---|---|
| Session start | CEO -> Paco | **`boot Paco`** | Paco runs full SESSION-START BOOT PROTOCOL before any other response |
| Session end | CEO -> Paco | **`update canon`** | Paco updates anchor + SESSION.md + ledger; commits + pushes |
| Every Paco turn end | Paco -> CEO/PD | **`Status: <token>`** | Signals turn outcome (see token table below) |
| Every PD turn end | PD -> CEO/Paco | **`Status: <token>`** | Same four-value taxonomy |
| PD session start | n/a | -- | PD receives a dispatched directive from CEO (no session-open phrase needed) |
| PD session end | PD -> CEO/Paco | SESSION.md + anchor update + commit/push + `Status: DONE` | PD's existing SESSION HYGIENE discipline; anchor's last `[x]` line is the handoff carrier |

---

## Status token taxonomy (canonical, both directions)

Both Paco and PD end every turn with one of these four:

| Token | Meaning | What the receiver does |
|---|---|---|
| **`Status: DONE`** | Cycle/turn closed cleanly. Anchor reflects current state. | Receiver reads anchor's last `[x]` cycle line for handoff. Process awaiting items. |
| **`Status: AWAITING APPROVAL`** | Sender is waiting on Sloan, not the other agent. | Sloan responds. The other agent holds or proceeds on parallel work; does not act on the pending item. |
| **`Status: BLOCKED: <reason>`** | Sender halted on a blocker; reason given. | Receiver may author an unblock directive (Paco) or escalate to CEO. |
| **`Status: NEEDS PACO: <reason>`** | Explicit escalation TO Paco. | Paco responds with a ruling, directive amendment, or paco_response. |

---

## Canonical handoff carrier

The anchor's last `[x]` cycle line is the cross-session handoff state. Both Paco and PD update or read it as canonical.

**`docs/handoff_pd_to_paco.md` and `docs/handoff_paco_to_pd.md` are DEPRECATED as of v2.3** -- never write to them. They were never in git, only stale local-disk artifacts that drifted across machines.

**NO EXCEPTIONS.** This convention is load-bearing across sessions, machines, and instances. Drift is failure.

---

## Examples

### CEO opens a Paco session

```
CEO: "boot Paco"
Paco: [executes full session-start boot protocol; states understanding back in 5-7 bullets; waits for actual ask]
```

### CEO closes a Paco session

```
CEO: "update canon"
Paco: [updates paco_session_anchor.md + SESSION.md + ledger if needed; git add + commit + push; confirms HEAD moved]
Paco: "Status: DONE"
```

### PD finishes a directive cleanly

```
PD: [executes directive end-to-end; writes paco_review_X.md; updates anchor + SESSION.md]
PD: "For Paco at next session boot: read anchor -- last entry surfaces cycle outcome + B0 adaptations awaiting ratification + P6 candidates to bank."
PD: "Status: DONE"
```

### PD halts on a blocker

```
PD: "Cannot proceed: orchestrator returns 503 on /healthz; suspect nginx upstream timeout."
PD: "Status: BLOCKED: nginx upstream timeout on /healthz; need Paco unblock directive or CEO override."
```

### Paco dispatches a directive draft, awaiting CEO sign-off

```
Paco: [authors directive to /tmp/; presents scope summary]
Paco: "Status: AWAITING APPROVAL"
```

### Paco escalates to CEO mid-cycle (rare but valid)

```
Paco: [catches scope mismatch between observed state and directive intent]
Paco: "Status: NEEDS CEO: Sloan-committed spec 3f30fed diverges from MCP-shipped edits; reconciliation path required."
```

*(`NEEDS CEO` is the Paco-side mirror of `NEEDS PACO`; Sloan call whether to formalize this in v2.4 or keep it ad-hoc.)*

---

## What this protocol replaces

- File-based handoff (`docs/handoff_*.md`) -- DEPRECATED v2.3.
- Implicit / unstated turn closures -- replaced by explicit Status token.
- Paco's session-start file-reading order item 3 (the old handoff file) -- replaced by anchor last `[x]` line.

---

## Cross-references

- Paco-side spec: `PROJECT_ASCENSION_INSTRUCTIONS.md` v2.3 SESSION KEY PHRASES section
- PD-side spec: `PD_COWORK_INSTRUCTIONS_v2_3.md` CROSS-TURN HANDOFF (PD <-> PACO) section
- Source canon for handoff carrier: `paco_session_anchor.md` last `[x]` cycle line
- Ratified: 2026-05-04 Day 80 by CEO; cycle close at HEAD `80e1327`

---

**End of session key phrases v2.3 quick reference.**
