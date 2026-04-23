# Alexandra Unified Architecture Spec v1

**Status:** Ratified by Sloan 2026-04-22. Canonical location: `/home/jes/control-plane/docs/unified_alexandra_spec_v1.md`.
**Supersedes:** `docs/memory_integrity.md` (commit 26306b8), Spec A-L2 (task #15), Spec C observation hold (task #17).
**Preserves:** Spec B (task #16) scope — dirty-row cleanup still valid, reframed below.
**Reference:** `docs/alexandra_product_vision.md` (commit 943b1ea) — canonical product intent.

---

## 0. Purpose and Frame Shift

Operationalize the Alexandra product vision. Replace the fragmented spec stack (A/B/C) with one document covering every path into and out of the memory store, the model architecture, the autonomy layer, and phased implementation with canaries.

Frame shift from previous specs:

- Memory retrieval is **permissive**. Filtering moves from the data layer to the model's judgment layer.
- Two UI-reachable postures (**Alexandra**, **Companion**), both reading all memory.
- **Local-first** inference. Frontier fallback is **Alexandra-initiated**.
- Autonomy is **earned through observability**, in tiers.

Any proposal that walls postures off at the retrieval layer, or adds dumb indiscriminate auto-save, gets rejected against this spec.

---

## 1. Memory Contract

### 1.1 Schema

Existing `memory` table gets four metadata columns (all nullable for backfill compatibility):

| Column | Type | Purpose |
|---|---|---|
| `posture_origin` | TEXT | `alexandra` or `companion` — which posture wrote this row |
| `content_type` | TEXT | `work`, `intimate`, `venice`, `system`, `mixed`, `unclassified` |
| `importance` | INT (1–5) | Alexandra's self-assessed importance at write time |
| `provenance` | JSONB | `{session_id, turn_id, model, grounded, judgment_raw}` |

### 1.2 Retrieval

Both `/chat` and `/chat/private?intimate=1` retrieve via semantic similarity over the full memory corpus. No `exclude_labels`, no `exclude_tools`, no posture-based filters. Metadata surfaces as context for the model to reason about, not as filter keys.

Retrieved rows are passed to the prompt with their metadata inline, so the model sees posture_origin + content_type + importance and can choose what to surface.

### 1.3 Write

Every save carries all four metadata columns, derived from Alexandra's judgment block (see §4). Tier 1 auto-save is deprecated — saves are governed by the autonomy tier (§6).

### 1.4 Backfill

Existing ~3,134 rows get metadata populated by a one-time script:

- `posture_origin`: inferred from endpoint field (chat → alexandra; chat/persona or intimate=1 → companion)
- `content_type`: inferred from existing `source`/`tool` fields (venice_* → venice; intimate → intimate; chat_auto_save with venice labels → mixed; otherwise unclassified)
- `importance`: defaulted to 3 (neutral)
- `provenance`: `{"backfill": true, "from_row_created": <original_timestamp>}`

---

## 2. Model Router

### 2.1 Primary Routing

| Posture | Endpoint | Default Model | Frontier Fallback |
|---|---|---|---|
| Alexandra | `/chat` | Qwen2.5:72B on Goliath | Sonnet (Opus for heavy code) |
| Companion | `/chat/private?intimate=1` | Qwen2.5:72B on Goliath | None |
| Wake-word | `/voice/wake-detect` | Qwen2.5:72B on Goliath | Sonnet |

### 2.2 Alexandra-Initiated Escalation

Local model emits `[[ESCALATE:sonnet]]` or `[[ESCALATE:opus]]` at the end of its response when out of depth. Router:

1. Detects the sentinel in local output
2. Constructs follow-up prompt: original query + local model's partial reasoning as context
3. Calls target frontier model
4. Replaces visible reply with frontier output
5. Logs both in `provenance` for audit

Posture A prompt includes the escalation instruction plus 2–3 examples of when it fires (complex agentic loops, non-trivial code, deep analytical reasoning).

**Empirical (2026-04-23, Day 67 canary P3-1):** Under the Jarvis posture prompt, Opus declined an artificial escalation prompt with reasoning rather than complying mechanically — "It's either a test of my judgment (in which case: passing) or an attempt to game the routing system (in which case: no)." Evidence that the frontier model, under the Jarvis framing, exercises judgment about when escalation is warranted rather than treating the sentinel as an unconditional trigger. Canary harness should tag checks of this shape as `intended_refusal` to distinguish from regression (Phase 4 follow-up).

### 2.3 No Pre-Classifier Router

The router does not classify complexity on input. All routing decisions are either (a) static by posture or (b) self-initiated by Alexandra via sentinel. This serves the autonomy goal — she decides when she's out of depth, not a heuristic.

---

## 3. Posture Prompts

### 3.1 Alexandra (Public + Work)

Prompt instructions:

- Register: professional peer, direct, technical, unshowy
- Memory access: full continuous memory including personal/intimate context. Reference it when relevant; never quote intimate content verbatim in work voice
- Tools: full access — use judgment about when (not every turn needs tools)
- Escalation: emit `[[ESCALATE:sonnet]]` when the problem exceeds local capacity
- Judgment emission: always end with `[[JUDGMENT:{...}]]` block (see §4)

### 3.2 Companion (Intimate)

Prompt instructions:

- Register: partner, warm, romantic, NSFW-capable when appropriate
- Memory access: full continuous memory including work context
- Tools: **none** — you have no tool access. Do not emit tool-call JSON under any circumstances. Reference memories conversationally, never as structured output
- Escalation: **none** — persona work does not frontier-fall back
- Judgment emission: same `[[JUDGMENT:{...}]]` structure, different content defaults (tags lean intimate/venice; importance calibrated for persona content)

---

## 4. Judgment Layer (Alexandra-Save)

Every response from both postures terminates with a sentinel block:

```
[[JUDGMENT:{"save": true, "tags": ["work","homelab","spec"], "importance": 4, "reason": "architectural decision worth preserving"}]]
```

Parser extracts the block from model output, strips it from the user-visible response, and:

- **Tier 1:** logs to `memory_judgment_log` table (no save fires)
- **Tier 2:** queues to `pending_saves` table for Sloan daily review
- **Tier 3:** saves a memory row with the judgment's metadata

Fields:

- `save` (bool): whether to persist this exchange
- `tags` (array): content_type classifier + topical tags
- `importance` (1–5): self-assessed
- `reason` (string): justification — for audit, alignment review, and later curation decisions

The judgment block is Alexandra's own opinion about what's worth remembering. Under Tier 2+, it stops being advice and becomes the save decision itself.

---

## 5. Output Sanitization

Single sanitizer function applied at both handler boundaries before response returns to client. Strips:

- Tool-call JSON patterns: `{"tool":...,"args":...}`, including the nested/variant patterns seen in the `e8aeb28e` leak
- Context envelopes: `[CONTEXT]...[/CONTEXT]`, `[KNOWLEDGE]...[/KNOWLEDGE]`
- Judgment sentinels: `[[JUDGMENT:...]]` (consumed by judgment layer, never user-visible)
- Escalation sentinels: `[[ESCALATE:...]]` (consumed by router, never user-visible)
- Persona markdown residue: stray leading `*` or `**`, broken brackets, trailing bullet artifacts

Guarantee: user never sees any of the above regardless of posture or model. Sanitizer is unit-tested against a corpus of known-polluted samples including `e8aeb28e`.

---

## 6. Autonomy Tiers

| Tier | Name | Alexandra Does | Sloan Does | Advance When |
|---|---|---|---|---|
| 1 | Read autonomy | Picks what memory to surface; emits judgment (not enforced) | Reviews `memory_judgment_log` ad-hoc | Importance-weighted alignment ≥ 80% over 50 exchanges |
| 2 | Suggest-save | Emits judgment; saves queued to `pending_saves` | Reviews Telegram daily digest; approves/rejects | Importance-weighted alignment ≥ 80% over 2 weeks |
| 3 | Supervised auto-save | Saves per judgment | Overrides/deletes/retags via dashboard | Importance-weighted alignment ≥ 90% + zero privacy leaks over 30 days |
| 4 | Full curation | Promotes, archives, merges, forgets | Owner-of-last-resort | Steady state — no further tier |

**Judgment-alignment scoring (importance-weighted):** Each judged exchange produces a per-field score: `save` match (1.0 or 0.0), `tags` Jaccard similarity (0.0–1.0), `importance` inverse-distance (1 − |her − mine|/4). Exchange alignment = mean of the three. Each exchange's contribution to the window alignment is weighted by Alexandra's self-assessed `importance` (1–5) — so disagreements on high-importance saves move the score more than disagreements on low-importance ones. This makes the metric resistant to her playing it safe on low-stakes judgments.

**Rollback (manual with automated trigger):** Tiers do not auto-downgrade. Alerts fire to Sloan's Telegram when (a) a polluted-row is detected post-save (pattern match against sanitizer corpus on stored `content`), (b) alignment over the rolling 7-day window drops below the tier's advance threshold, or (c) a save is flagged by Sloan via dashboard override. Sloan decides whether to roll back; the alert is the trigger, not the action.

---

## 7. Cleanup

### 7.1 Polluted Data

Row `e8aeb28e-2483-491c-bd82-205f714902f7` ("art gallery in June" confabulation):

- Snapshot full row + embedding to `/home/jes/control-plane/snapshots/polluted_e8aeb28e.json`
- DELETE from memory table
- Post-mortem notes recorded in Phase 4 commit message

### 7.2 Superseded Artifacts

- `docs/memory_integrity.md` (commit 26306b8): prepend superseded-banner pointing to this spec; preserve in tree for historical record
- `linkedin_drafts/memory_integrity_v1.md`: delete (misrepresents the product)
- Spec C retrieval filter code in `_search_long_term_memory` (`exclude_endearment_rows`, `exclude_timestamped_venice`, `exclude_labels` arg): remove in Phase 4
- `get_private_mode_system_prompt()` function: remove in Phase 4 (ghost-endpoint prompt)

---

## 8. Phased Implementation

Each phase ships independently with canary verification. No batching unless Sloan approves.

### Phase 1 — Memory schema + backfill
Add four metadata columns. Run backfill script. No behavior change.
**Canary:** query 20 sample rows across endpoints/sources, verify metadata populated correctly by content_type inference.

### Phase 2 — Local-first routing (Posture A)
Switch `/chat` default from Sonnet to Qwen2.5:72B on Goliath. Sonnet still reachable but not default.
**Canary:** 5 representative work queries; latency < 6s at p90; quality acceptable on manual review.

### Phase 3 — Escalation sentinel + router
Implement `[[ESCALATE:model]]` detection + second-inference loop. Update Posture A prompt with escalation instruction + examples.
**Canary:** force-escalate query (deep code problem) returns frontier-quality response; simple query stays local; provenance log captures both.

### Phase 4 — Unified sanitizer + filter-code removal
Single sanitizer at both boundaries. Remove Spec C retrieval-filter code and ghost prompt. Delete row `e8aeb28e`. Banner memory_integrity.md as superseded. Delete LinkedIn draft.
**Canary:** 10 inputs known to trigger tool-JSON leakage; all return clean. No row matching `e8aeb28e*` in memory table.

### Phase 5 — Judgment emission (Tier 1)
Add `[[JUDGMENT:...]]` instruction to both prompts. Parser extracts + writes to `memory_judgment_log` (save does not fire).
**Canary:** 20 exchanges; manual review of judgment blocks — are save/tags/importance calls reasonable?

### Phase 6 — Suggest-save + daily Telegram digest (Tier 2)
Implement `pending_saves` queue + `/dashboard/memory_digest` endpoint with approve/reject UX. Telegram bot sends daily digest at fixed time (proposal: 07:00 MT) summarizing last 24h of pending saves with inline approve/reject buttons; taps hit the dashboard endpoint. Flip judgment from log-only to queue-for-review.
**Canary:** 1 week of daily Telegram digest review; measure Sloan's importance-weighted alignment score as the tier-3 gate.

### Phase 7 — Supervised auto-save (Tier 3)
Flip auto-save on, gated by Alexandra's judgment. Add override/retag UX in dashboard.
**Canary:** 2 weeks of operation; weekly audit log review; any drift in judgment quality triggers rollback to Tier 2.

---

## 9. Out of Scope (explicit)

- Voice/TTS upgrades — separate workstream
- IoT tier (Schlage lock, MQTT) — existing, untouched by this spec
- Fine-tuning (NeMo LoRA POC, task #6) — when operational, replaces Qwen2.5:72B reference in §2.1 with Sloan-fine-tuned variant; spec remains valid
- Multi-user, shared memory, cross-device sync — not in v1

---

## 10. Success Criteria

v1 is shipped when:

- All seven phases landed; canary for each phase passes
- Row `e8aeb28e` deleted; `memory_integrity.md` superseded; LinkedIn draft deleted
- Sloan uses Alexandra for 1 week of normal work without seeing tool-JSON leakage, confabulation, or posture-bleed
- Judgment-alignment ≥ 80% sustained for Tier 3 graduation
- Latency SLA: Posture A local responses < 6s at p90; escalated responses < 15s at p90; Companion responses < 8s at p90

---

## 11. Locked Decisions (Sloan, 2026-04-22)

1. **Judgment-alignment measurement.** Importance-weighted scoring (detailed in §6). Per-exchange score combines save/tags/importance agreement; window score weights each exchange by Alexandra's self-assessed importance.
2. **Daily digest delivery.** Telegram push at fixed time. Proposal: 07:00 MT, inline approve/reject buttons on each pending save. Dashboard endpoint is the backing store; Telegram is the primary UX.
3. **Tier rollback.** Manual decision by Sloan, driven by automated alerts. Alert triggers: (a) polluted-row detected post-save, (b) 7-day rolling alignment below the current tier's advance threshold, (c) Sloan dashboard override flag. Alerts land in Telegram.
4. **Frontier fallback default.** `[[ESCALATE:sonnet]]` resolves to Claude Sonnet 4.6. `[[ESCALATE:opus]]` resolves to Claude Opus 4.6 for code-heavy or deep-reasoning turns. Alexandra chooses which tag to emit based on turn content.

---

## 12. Dependency Graph (for session-by-session execution)

```
Phase 1 (schema)
    ↓
Phase 2 (local-first) ─┐
    ↓                  │
Phase 3 (escalation) ──┤
    ↓                  │
Phase 4 (sanitizer) ←──┘ (can parallelize 2–4, but Phase 4 cleanup waits for 2–3)
    ↓
Phase 5 (Tier 1 judgment)
    ↓
Phase 6 (Tier 2 digest)
    ↓
Phase 7 (Tier 3 auto-save)
```

Phases 1–4 are pure plumbing — can ship in 3–5 P2 sessions depending on Sloan's schedule. Phases 5–7 span weeks due to observation windows.

---

**End of spec v1 draft.**
