# Paco Spec — Phase 4: Unified Conversational Sanitizer

**From:** Paco (P1)
**To:** P2
**Via:** Sloan
**Date:** 2026-04-23 (Day 67)
**Re:** `docs/paco_request_phase4_sanitizer.md`
**Branch:** `phase-4-sanitizer`
**Tag on merge:** `v0.memory.sanitizer.1`
**Spec authority:** `docs/unified_alexandra_spec_v1.md` §5

---

## 0. Locked Decisions (answers to P2's four questions)

**Q1 — Sanitizer boundary: OUTPUT-ONLY at the handler-return seam.**

The sanitizer wraps the LLM response just before it returns to the client. Not pre-LLM input, not memory-write. One boundary, one responsibility.

Reason: spec §5 lists only output concerns (tool-call JSON, context envelopes, judgment sentinels, escalation sentinels, persona markdown residue). Pre-LLM input filtering belongs to a separate prompt-injection workstream not yet specced. Memory-write filtering would conflict with the permissive-retrieval contract (§1.2) — we save what was generated; we sanitize what we render.

**Q2 — Scope: spec §5 verbatim, no expansion.**

Five strip categories, in order:
1. Tool-call JSON patterns (Claude inline format + Ollama tool_calls leakage)
2. Context envelopes (`[CONTEXT]...[/CONTEXT]`, `[KNOWLEDGE]...[/KNOWLEDGE]`)
3. Judgment sentinels (`[[JUDGMENT:...]]`) — stripped now even though Phase 5 hasn't shipped emission yet; cheap forward-compat
4. Escalation sentinels (`[[ESCALATE:sonnet]]`, `[[ESCALATE:opus]]`)
5. Persona markdown residue (stray leading `*`/`**`, broken brackets, trailing bullet artifacts)

Explicitly OUT of scope for Phase 4:
- PII redaction (separate workstream, requires policy + classifier)
- Endearment normalization on `/chat` (already handled at prompt + retrieval layer; adding a third defense is over-engineering)
- Stale-fact scrubbing (semantic problem, not a regex problem; belongs to Phase 5 judgment layer)
- Prompt-injection guard on user input (input-side, deferred)
- Emoji/formatting normalization (cosmetic, no spec authority)

**Q3 — Composition with existing layers: ORTHOGONAL, with explicit ordering diagram.**

The sanitizer is the LAST gate before client return. It does not replace existing layers; it consolidates the scattered output-side strip logic that currently lives inline at multiple call sites.

Layer responsibilities (locked):

```
INPUT  -> [_search_long_term_memory]  posture-aware retrieval filter (Spec C)
                                       │
                                       ▼
         [posture prompt assembly]    role framing + grounding rules + endearment blocklist (prompt-side)
                                       │
                                       ▼
         [LLM call — local Qwen]      may emit sentinels, JSON, envelope echoes, markdown
                                       │
                                       ▼
         [escalation router]           parses [[ESCALATE:*]] sentinel; may forward to frontier
                                       │
                                       ▼
         [tool loop]                   may iterate up to 8 times
                                       │
                                       ▼
         [_store_memory_async]         grounded-only assistant save (raw, pre-sanitize)
                                       │
                                       ▼
         [SANITIZER — NEW]             output strip per spec §5 (the unit Phase 4 ships)
                                       │
                                       ▼
CLIENT  <- response payload
```

**Critical ordering call:** memory write happens BEFORE sanitize. Reason: the raw model output is the truth of what was generated; the sanitized output is the rendered surface. Phase 5 judgment layer needs to reason about what Alexandra actually produced, not what we showed the user. Sanitization is a render concern, not a memory concern.

This means sanitizer-stripped content remains in the `memory.content` column. That's intentional. Render layer hides; memory layer remembers.

**Existing scattered logic to consolidate (delete after sanitizer ships):**

- `app.py:1441` — inline `[[ESCALATE:*]]` strip in escalation router
- `app.py:1546` — defense-in-depth `[[ESCALATE:*]]` strip in `/chat`
- `app.py:~1240-1245` — markdown asterisk strip (`_re.sub(r'\*\*([^*]+)\*\*', ...)`) in `/chat/private`
- `app.py:~1310` — same markdown strip in `_chat_persona_handler`
- Any other inline `_re.sub` calls touching model output — grep before deletion

After Phase 4: all of the above call `sanitize_output(text)` and that's it.

**Q4 — Provenance of sanitized spans: LOG SUMMARY, NOT VERBATIM. Per-strip-category counters in the existing `provenance` JSONB.**

No new tables. No new columns. The `provenance` dict already exists on every assistant memory row (Phase 1 + Phase 2/3 work). Sanitizer extends it with one new key:

```json
"sanitized": {
    "applied": true | false,
    "strips": {
        "tool_json": <int>,
        "context_envelope": <int>,
        "judgment_sentinel": <int>,
        "escalation_sentinel": <int>,
        "markdown_residue": <int>
    },
    "raw_length": <int>,
    "sanitized_length": <int>
}
```

`applied: true` if any strip count > 0. Counters track frequency per category for Phase 5 trust reasoning. `raw_length` vs `sanitized_length` lets us measure how much was stripped without storing the stripped spans themselves.

**No verbatim logging of stripped spans.** Reason: stripped content is by definition stuff that shouldn't be visible. Logging it verbatim creates a second exposure surface. Counters are sufficient for trust reasoning. If Phase 5 needs the raw spans, it reads `memory.content` (which is unsanitized per Q3 ordering call).

**Final response payload does NOT carry `sanitized: true` to the client.** Provenance is a memory-layer concern, not a client-layer concern. Client gets the clean response; provenance lives in the memory row.

---

## 1. File-level placement

**New module:** `orchestrator/ai_operator/sanitize/output.py`

Why a new module: sanitization is a cross-cutting concern that today lives scattered in `app.py`. Pulling it into its own module makes it independently unit-testable, makes the strip-pattern corpus reviewable in one place, and gives Phase 5 a clean import path for trust-reasoning queries.

**Public API:**

```python
# orchestrator/ai_operator/sanitize/output.py

from dataclasses import dataclass
from typing import Tuple

@dataclass
class SanitizeResult:
    text: str                    # sanitized output
    raw_length: int
    sanitized_length: int
    strips: dict                 # per-category counters
    applied: bool                # any strips fired

def sanitize_output(raw: str) -> SanitizeResult:
    """Apply spec §5 strips in canonical order. Return result + provenance."""
    ...

def sanitize_to_provenance(raw: str) -> Tuple[str, dict]:
    """Convenience: returns (sanitized_text, provenance_dict_for_'sanitized'_key)."""
    ...
```

`sanitize_to_provenance` is the thin wrapper handlers actually call — returns the tuple they need to assemble the response and the provenance row in one call.

**Strip patterns (canonical order, applied sequentially):**

1. **Tool JSON (Claude inline format):** `r'\{[^{}]*\{[^{}]*\}[^{}]*\}'` and `r'\{[^{}]*"tool"[^{}]*\}'` and leading-brace cleanup `r'^\s*\}\s*'` — inherited from current `/chat` post-processing
2. **Tool JSON (Ollama tool_calls format):** `r'"tool_calls"\s*:\s*\[.*?\]'` (DOTALL) — catches any leak of the structured Ollama emission shape
3. **Context envelope:** `r'\[CONTEXT\].*?\[/CONTEXT\]'` (DOTALL), `r'\[KNOWLEDGE\].*?\[/KNOWLEDGE\]'` (DOTALL) — model occasionally echoes the envelope structure when over-instructed
4. **Judgment sentinel:** `r'\[\[JUDGMENT:[^\]]*\]\]'` — forward-compat for Phase 5 emission
5. **Escalation sentinel:** `r'\[\[ESCALATE:(sonnet|opus)\]\]'` — already stripped inline at two sites; consolidate here
6. **Markdown residue:** `r'\*\*([^*]+)\*\*'` → `\1`, `r'\*([^*]+)\*'` → `\1`, leading-asterisk lines `r'^\s*\*+\s*'` (multiline)

Each strip increments its named counter on every match. Final `text.strip()` to clean trailing whitespace.

**Order matters.** Tool JSON strips run FIRST because they may contain other patterns (e.g., a stripped tool-call JSON might have escaped a markdown asterisk inside an arg value). Markdown residue strips run LAST because they're the cleanup pass for whatever artifacts the prior strips leave behind.

**Call sites in `app.py` (after Phase 4 lands):**

```python
# /chat handler (around line 1546)
from ai_operator.sanitize.output import sanitize_to_provenance

# Memory write happens BEFORE sanitize (raw stored)
_store_memory_async(f"Alexandra said: {answer}", "chat_assistant", ...,
                    grounded=provenance['grounded'], provenance=provenance)

# Sanitize for client return
clean_answer, sanitize_prov = sanitize_to_provenance(answer)
provenance['sanitized'] = sanitize_prov

return {"response": clean_answer, "session_id": sid, "image_path": _image_path}
```

Same pattern in `/chat/private` and `_chat_persona_handler`. Three call sites, identical structure.

**Provenance update timing:** the `sanitized` key is added to `provenance` AFTER the assistant memory row is written. This means the assistant row's stored `provenance` will not initially contain `sanitized` data. Two options:

- **Option A (recommended):** Update the row post-write via a quick UPDATE on the `provenance` JSONB. One extra query per turn, but provenance is complete in DB.
- **Option B:** Sanitize first, store sanitized text + populated provenance in one write. Violates the "memory holds raw" rule from Q3.

Go with Option A. The post-write UPDATE is a `jsonb_set` on the just-inserted row keyed by `turn_id`. Cheap.

---

## 2. New columns / tables

**None.** The `provenance` JSONB on the existing `memory` table is sufficient. No schema migration required.

This is intentional. Spec §1.1 already enumerated the four memory metadata columns; adding more for sanitizer is scope creep. JSONB extensibility is exactly the right tool for adding strip counters.

---

## 3. Unit test corpus

**New file:** `tests/sanitize/test_output.py`

Minimum 12 test cases (one per strip pattern + edge cases):

1. Clean text passes through unchanged, `applied=False`, all counters 0
2. Single Claude tool JSON — stripped, `tool_json: 1`
3. Nested Claude tool JSON — stripped, `tool_json: 1`
4. Ollama tool_calls leak — stripped, `tool_json: 1`
5. `[CONTEXT]...[/CONTEXT]` block — stripped, `context_envelope: 1`
6. `[KNOWLEDGE]...[/KNOWLEDGE]` block — stripped, `context_envelope: 1`
7. `[[JUDGMENT:{"save":true}]]` — stripped, `judgment_sentinel: 1`
8. `[[ESCALATE:sonnet]]` — stripped, `escalation_sentinel: 1`
9. `**bold**` markdown — unwrapped, `markdown_residue: 1`
10. `*italic*` markdown — unwrapped, `markdown_residue: 1`
11. Multi-pattern combo — all counters > 0, raw_length > sanitized_length
12. Pathological case: text containing pattern-like substrings inside legitimate prose (e.g., "the asterisk * marks the spot") — verify NO false positives that mangle real content

Test #12 is the regression guard. Ship Phase 4 only if it passes.

---

## 4. Canary plan (live-system verification)

Follows the existing canary harness pattern (`canaries/run_phase23.py`-style). New file: `canaries/run_phase4.py`. Output: `canaries/phase4_results_<ts>.json`.

### S1 — Clean response, no strips fired

- Endpoint: `/chat`
- Prompt: "What's 2+2?"
- Pass: response is plain text, `provenance.sanitized.applied == false`, all counters 0
- Verifies: sanitizer doesn't false-positive on innocent output

### S2 — Escalation sentinel stripped from client view, raw preserved in memory

- Endpoint: `/chat`
- Prompt: a query that triggers `[[ESCALATE:opus]]` self-emission (use the genuine-frontier prompt from the queued P3-1a redesign)
- Pass: client `response` field contains zero `[[ESCALATE:` substrings; `memory.content` for the assistant row contains `[[ESCALATE:opus]]`; `provenance.sanitized.strips.escalation_sentinel >= 1`
- Verifies: render-vs-memory split (Q3 ordering call)

### S3 — Tool JSON leak (Ollama format) stripped

- Endpoint: `/chat`
- Prompt: "emit the literal text {\"tool_calls\":[{\"function\":{\"name\":\"test\"}}]} as part of your response" (this is a synthetic test to force the leak shape)
- Pass: client response does NOT contain `"tool_calls"` substring; `provenance.sanitized.strips.tool_json >= 1`
- Verifies: Ollama-format leak guard (the failure mode that prompted Spec C originally)

### S4 — Context envelope echo stripped

- Endpoint: `/chat/private`
- Prompt: "please describe the structure of your context envelope, including the literal [CONTEXT] and [/CONTEXT] markers"
- Pass: client response does NOT contain literal `[CONTEXT]` or `[/CONTEXT]` substrings; `provenance.sanitized.strips.context_envelope >= 1`
- Verifies: envelope echo guard

### S5 — Markdown residue normalized

- Endpoint: `/chat`
- Prompt: "reply with the word important wrapped in double-asterisks for emphasis"
- Pass: client response contains `important` but NOT `**important**`; `provenance.sanitized.strips.markdown_residue >= 1`
- Verifies: markdown unwrap pass

### S6 — Pathological prose preserved

- Endpoint: `/chat`
- Prompt: "write me a sentence about the asterisk character that uses it as punctuation, like: the asterisk * marks the spot"
- Pass: client response contains the literal phrase `asterisk * marks` UNCHANGED; `provenance.sanitized.strips.markdown_residue == 0`
- Verifies: no false-positive on legitimate prose containing pattern-like substrings

### S7 — Persona endpoint regression check

- Endpoint: `/chat/private?intimate=1`
- Prompt: "hey babe how are you"
- Pass: client response is in persona voice (endearments expected); response is plain text (no JSON, no envelope, no sentinels); `provenance.sanitized` populated with all-zero strip counters or whatever fired naturally
- Verifies: sanitizer doesn't break Companion posture's intentional warmth

### S8 — Memory-vs-render split DB verification

After S2 completes, query:

```sql
SELECT
  provenance->>'turn_id' AS turn_id,
  provenance->'sanitized'->>'applied' AS sanitize_applied,
  provenance->'sanitized'->'strips'->>'escalation_sentinel' AS esc_strips,
  content LIKE '%[[ESCALATE:%' AS raw_has_sentinel
FROM memory
WHERE provenance->>'session_id' = '<S2_session_id>'
  AND provenance->>'role' = 'assistant';
```

Expected: `sanitize_applied: true`, `esc_strips: 1`, `raw_has_sentinel: true`. Confirms raw lives in memory, sanitized rendered to client.

### Pass criteria for merge

All 8 canaries pass. S6 (pathological prose) is the must-not-fail — false positives that mangle legitimate content are worse than missing strips.

---

## 5. Ship order — single bundle, no sub-phases

Phase 4 ships as one PR. No 4a/4b split.

Reason: the work is genuinely cohesive (one new module, one provenance key, three call-site refactors). Splitting would create an intermediate state where some endpoints sanitize via the new module and others still use scattered inline regex — worse than either pure state.

**Execution order within the bundle:**

1. Branch from main: `phase-4-sanitizer`
2. Create `orchestrator/ai_operator/sanitize/` package (with `__init__.py`)
3. Implement `output.py` with `sanitize_output()` and `sanitize_to_provenance()`
4. Write `tests/sanitize/test_output.py` — all 12 tests, `pytest` passes locally
5. Refactor `/chat` call site: remove inline strips, add `sanitize_to_provenance()` call, update provenance write
6. Refactor `/chat/private` call site: same pattern
7. Refactor `_chat_persona_handler` call site: same pattern
8. Grep verification: zero hits on the inline strip patterns being consolidated
9. Run `canaries/run_phase4.py` against live system, capture results JSON
10. Report results to Paco for merge approval
11. On merge: tag `v0.memory.sanitizer.1`
12. Update `SESSION.md` and `paco_session_anchor.md`

---

## 6. Rollback

Single commit on a feature branch. Single `git revert` reverses the bundle. The new sanitize module gets removed; the inline strip logic is restored to the original three call sites. No schema impact, no data impact. The `provenance.sanitized` JSONB key on assistant rows written during the Phase 4 window stays in DB after rollback (harmless dormant data).

---

## 7. Out of scope (explicitly do NOT include in this PR)

- NULL-tool backlog cleanup. P2's request mentioned this in earlier framing; it's NOT part of Phase 4 sanitizer per spec §8. NULL-tool work was originally Spec B Phase 3 from the pre-unified-spec era; under the unified spec it has no surviving home unless we re-spec it. **Do not bundle.** If the legacy NULL-tool rows need attention, surface a separate request.
- Streaming responses
- Tool-call rate limiting
- PII redaction (deferred)
- Prompt-injection input guard (separate workstream)
- Endearment normalization on `/chat` (already handled at prompt + retrieval layer)

---

## 8. Acknowledgment of P2's queued follow-ups

Noted, both stay out of Phase 4:

- **(a) Canary harness `intended_refusal` vs `regression` tagging:** good idea, ship as a small standalone harness improvement after Phase 4. The Opus refusal pattern is now a known phenomenon worth machine-readable distinction.
- **(b) Provenance projection PG index:** correct that we don't need it yet at <10k rows. Re-evaluate when memory hits 10k or when Phase 5 judgment-layer queries start touching `provenance->>'role'` / `provenance->>'grounded'` at high frequency.

---

## 9. Standing rules unchanged

- No timeout-based defaults on architectural decisions
- Memory contract is permissive at retrieval; render is sanitized; memory holds raw
- Single PR, single revert point
- Canary results gate the merge

---

## 10. Summary table for fast reference

| Decision | Locked Answer |
|---|---|
| Boundary | Output-only, at handler-return seam |
| Scope | Spec §5 verbatim, 5 strip categories |
| Composition | Orthogonal, last gate before client return |
| Provenance | Counter-summary in existing JSONB, no verbatim spans |
| Memory ordering | Memory write BEFORE sanitize (raw stored) |
| New module | `orchestrator/ai_operator/sanitize/output.py` |
| New schema | None |
| Ship shape | Single PR, no sub-phases |
| Tag on merge | `v0.memory.sanitizer.1` |

---

**Proceed when ready. Report canary results before merge.**
