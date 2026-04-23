# Paco Request: Phase 4 Spec (Conversational Sanitizer)

**From:** P2 (executor)
**To:** Paco (architect)
**Via:** Sloan
**Date:** 2026-04-23 (Day 67)
**Status:** AWAITING PACO SPEC
**Related:** docs/unified_alexandra_spec_v1.md §5, §8; docs/paco_response_phase23_merge_approval.md

## Context

Phase 2+3+routing bundle shipped and tagged `v0.memory.routing.1` at commit `4fb7797`. Per unified_alexandra_spec_v1.md §8 dependency graph, Phase 4 (conversational sanitizer) is the next architectural unit. P2 will not begin Phase 4 code until Paco ships spec.

## What P2 has verified on the current substrate

- Grounded-only save gate live at `_store_memory_async` entry — only tool-grounded assistant turns persist (tool-result intersection logic).
- Retrieval-side endearment filter live at `_search_long_term_memory` (Day 66 Spec C).
- Provenance JSONB carries `role`, `grounded`, `endpoint`, `model` — verified on both user and assistant rows via Fix #3.
- Jarvis posture prompt exhibits emergent judgment behavior on frontier (Opus declined artificial escalation, see §2.2 empirical note).

## Blocking questions for Phase 4 spec

1. **Sanitizer boundary.** Pre-LLM input filter, post-LLM output filter, or both? Does it wrap the retrieval envelope, the model response, or the memory write?

2. **Scope.** PII redaction only, or broader — endearment normalization for /chat, stale-fact scrubbing (e.g., superseded facts from unified_alexandra_spec_v1.md §7.1), prompt-injection guard on user input, emoji/formatting normalization?

3. **Composition with existing layers.** How does the sanitizer sit relative to (a) `_search_long_term_memory` endearment filter, (b) the grounded-save gate, (c) the posture prompt's endearment blocklist? Replace, layer, or orthogonal? Explicit ordering diagram preferred.

4. **Provenance of sanitized spans.** When a span is redacted/dropped, does it get logged to `memory` (or a sibling log table) with a reason code, or dropped silently? Does the final assistant response carry a `sanitized: true` provenance flag? Needed for Phase 5 judgment writer to reason about trust.

## What P2 needs from Paco

Spec in the same shape as the Phase 2+3 bundle:

- Decision-tree for the four questions above (each with a locked answer, not an option list).
- File-level placement: which module, which function boundary, which call order relative to existing gates.
- New columns / tables, if any (mirror §1.1 schema convention).
- Canary plan: specific prompts + expected behavior per sanitizer rule.
- Ship order if Phase 4 needs to split into sub-bundles (4a, 4b) like Phase 2+3 did.

## Follow-ups already queued (do not block Phase 4 spec)

- **(a)** Canary harness: tag P3-1-style checks as `intended_refusal` vs `regression` so machine-readable.
- **(b)** Provenance projection index: evaluate PG index on `provenance->>'role'` / `provenance->>'grounded'` once memory table ≥10k rows.

## Convention

Paco response lands at `docs/paco_response_phase4_sanitizer.md`. Sloan routes. P2 will not act until the response file exists and Sloan approves execution.
