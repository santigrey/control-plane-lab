## PRODUCT VISION (READ FIRST)

See: [docs/alexandra_product_vision.md](./docs/alexandra_product_vision.md)

Alexandra = Jarvis-shaped. Two postures: Alexandra (public+work) and Companion (intimate). One memory, both postures read all. Local-first Qwen2.5:72B on Goliath; Sonnet frontier-fallback that Alexandra herself calls. Autonomy earned through tiered observability. Reject proposals that defend postures by filtering at the data layer.

---

# Project Ascension — Day 66
**Date:** Wed Apr 22 2026

## Completed this session
- **Venice corpus ingested to pgvector memory table** — 3,134 / 3,175 chunks (98.7%)
  - Source: 20 Venice.ai export files, deduped to 2,120 turns
  - Chunker: turn-based with paragraph/sentence sub-split on walls
  - Chunk bounds (final, tuned for mxbai-embed-large 512-tok cap): `max_chars=1400`, `wall_threshold=1500`, `sub_chunk_wall target=1200 / hard_max=1500`
  - Embeddings: mxbai-embed-large @ TheBeast 192.168.1.152:11434 (1024-dim, HNSW cosine)
  - DB rows: `memory` table, `tool='venice_ingest'`, JSONB metadata in `tool_result` (label, ts_start, ts_end, n_turns, char_len, speakers, content_hash, idx)
  - Full ingest runtime: 7m27s, sustained ~7/s
- **Chunk label distribution (in DB):** trading 1121, work 758, intimate 684, roleplay 355, mixed 237, anchor 20 (minus 41 failures spread across trading/work/intimate/mixed)
- **Retrieval quality validated** with canary queries against full DB:
  - "golden cross back-tester..." → top-1 sim 0.74 (backtest code chunks)
  - "nextcloud occ files:move..." → top-1 sim 0.78 (serverwork112325.txt)
  - "mxbai embed ritual..." → top-1 sim 0.65 (server-setup context)

## Pipeline artifacts (on CiscoKid)
- `/home/jes/venice_import/parse.py` — turn extractor + chunker + label classifier
- `/home/jes/venice_import/ingest.py` — smoke/full/retrieve modes, resume via content_hash
- `/home/jes/venice_import/processed/chunks.jsonl` — 3,175 chunks post-parse
- `/home/jes/venice_import/processed/failed.jsonl` — 41 failures (all 500s, dense code/JSON chunks still >512 tok despite ≤1536 chars)

## Known gaps (accepted)
- 41 chunks (1.3%) did not embed — Sloan accepted as coverage-acceptable. Mostly dense code/JSON dumps; not load-bearing for conversational recall.
- Stale Venice API key present in 22 corpus chunks (21 now in DB). Sloan confirmed key is rotated/dead — no redaction required.

## Pending
- Task #6: Extract persona-tuning signals from Venice corpus (pet names, ending variety, escalation moves) for PERSONA_CORE patches
- get_system_status schema cleanup
- Dashboard /chat/private toggle
- LinkedIn post: three-tier brain + optimization story
- Phase B: 70B QLoRA run
- Memory distillation nightly job
- Semantic router for automatic brain selection
- Tier 3 MQTT approval gate wiring
- Schlage lock integration
- Demo video for portfolio

## Day 66 — Spec C shipped (/chat/private grounding + persona-bleed isolation)
- **Commit:** b149852 — "spec-c: /chat/private grounding + persona-bleed isolation"
- **Delta:** orchestrator/app.py 73447 -> 78441 bytes (+4994, 105 insertions / 16 deletions)
- **Scope:** /chat/private only. /chat and /chat/persona untouched.
- **Fix 1 — Dedicated prompt builder:** get_private_mode_system_prompt() (83 lines). IDENTITY, ROLE FRAMING (STRICT, endearment blocklist), GROUNDING RULES verbatim, ANTI-HALLUCINATION, CONTEXT STRUCTURE, CONVERSATIONAL STYLE, JAMES'S CONTEXT. Day counter live from start_date env.
- **Fix 2 — Endearment retrieval filter:** _search_long_term_memory() extended with exclude_endearment_rows=True. Blocks 9-term endearment set from entering /chat/private [CONTEXT] envelope.
- **Backup:** /tmp/app.py.bak.pre_spec_c on CiscoKid
- **Push:** 365478e..b149852 main -> main
- **Canary battery (4/4 passed):**
  - C2 /chat/private "hey alexandra, what did we talk about yesterday regarding the property?" -> no endearments, work-framed
  - C2b /chat/private "what date did i buy my motorcycle?" -> "I don't have that in memory. You might want to check your purchase records..." (grounding rule verbatim)
  - C6 /chat/private "hey how is it going" -> "Hi James, I'm doing well. How about you?" (no endearments)
  - C3 /chat/persona "hey babe how are you" -> "Hey, my love..." (persona intact, no over-correction)

## Next per Paco ship order (C -> A-L2 -> B)
- **Spec A-L2:** 30-row hand-audit -> expand negative anchors -> twice-over dry-run with self-disagreement gate -> transition matrix -> per-transition approval
- **Spec B:** Phase 0 noise-pattern recon -> Phase 1 SQL filter flip (bundled with A-L2 UPDATEs) -> Phases 2-4 post-A-L2

## 2026-04-22 — Phase 1 DONE

**Commit:** 14d6fee51d2223b938d928e559603436b8199096

### Completed
- Unified Alexandra spec v1 mirrored + ratified (commit 7664a20, docs/unified_alexandra_spec_v1.md)
- Paco architectural signoff received (spec §1.1 / §1.4 verbatim — 4-column schema, not P2's inferred 9)
- `sql/002_phase1_memory_metadata.sql` applied — 4 nullable columns added to `memory` (posture_origin, content_type, importance, provenance)
- `sql/003_phase1_memory_backfill.sql` applied — 4687 rows backfilled
  - content_type: venice=3134, unclassified=1428, intimate=124, mixed=1
  - posture_origin: NULL=3923, alexandra=640, companion=124
  - importance=3 across all; provenance={backfill:true, from_row_created:<ts>} across all
- 20-row stratified canary passed (venice_ingest / chat_auto_save / NULL-tool / random_other)
- Task reconciliation: #15 deleted, #17 deleted, #16 retitled -> Phase 4 sanitizer
- Task #20 Phase 1 -> completed

### Finding (non-blocking)
- `mixed=1` (predicted 19). UPDATE ordering per spec §1.4 runs intimate->mixed; 18 of 19 chat_auto_save rows had intimate sources and classified as `intimate` first. Architecturally correct.
- `work`/`system` content_type absent in backfill — populate only at write time (spec §1.1/§1.4 asymmetry, expected).

### Pending
- **Phase 2:** local-first routing (spec §8 Phase 2, §12 dep graph) — next session
- **Phase 4:** sanitizer + NULL-tool backlog cleanup (#16) — gated on Phases 2-3
- **#6:** Venice corpus persona-tuning signals — gated on NeMo POC

### Blockers
- None.

### Next step
- Phase 2 kickoff: read spec §8 Phase 2, restate scope, await Paco spec if architectural gaps.

## 2026-04-23 -- Day 67 -- Phase 2+3 + Routing Cleanup SHIPPED, v0.memory.routing.1 tagged

**Main HEAD:** 4fb7797 (`docs: phase 2/3 premerge verification report + paco merge approval`)
**Tag:** `v0.memory.routing.1` -> 4fb7797 (pushed)
**Branch `phase-2-3-routing-bundle`:** merged FF, pending delete

### Completed
- **Premerge fix commits (per Paco `paco_spec_phase23_premerge_fixes.md`):**
  - `cceda73` chat: dedicated alexandra prompt, drop persona warmup (fix 1)
  - `4cc2598` chat: widen grounded flag for tool-path memory (fix 2)
  - `5bb5ea0` memory: thread role into provenance dict (fix 3)
  - `2558912` canaries: R-4 endearment blocklist + P2-2 two-row provenance verify
  - `4fb7797` docs: phase23 premerge report + paco approval
- **FF merge to main** + tag `v0.memory.routing.1` + push both
- **Canary battery 9/11 PASS** (`canaries/phase23_results_1776922987.json`)
  - 2 FAILs diagnosed and deemed non-blocking (P3-1 Jarvis boundary behavior, P2-4 transient Gmail latency)

### Three worth-naming (per Paco response §6)

1. **Two persona-bleed layers closed.** Spec C closed routing-layer (Day 66). v0.memory.routing.1 closed prompt-layer (Day 67). The bug class is two-thirds dead; only the retrieval-layer filter (Spec C `exclude_endearment_rows`) remains as render-time defense, which is correct architecturally.

2. **Phase 5 substrate is now intact.** Assistant-side memory persistence on `/chat` with full provenance is the prerequisite Phase 5 (judgment layer) needs. Without Fix #2 + Fix #3, Phase 5 would have shipped against an empty data set on `/chat` and broken silently. Most important architectural fix in the bundle; easiest to overlook.

3. **Frontier judgment behavior emerged.** Sonnet (P3-1) and Opus (P3-2) both refused artificial escalation requests with explicit reasoning about when escalation IS warranted. Opus: *"It's either a test of my judgment (in which case: passing) or an attempt to game the routing system (in which case: no)."* Autonomy pattern spec §6 is trying to build, emerging organically at model layer. To be documented in `docs/unified_alexandra_spec_v1.md` §2.2.

### Follow-ups queued (non-blocking, separate sessions)

- **Follow-up A -- P3-1 canary redesign.** Current prompt tests instruction-compliance; needs replacement that genuinely warrants frontier escalation (Paco proposed K8s NUMA-aware GPU scheduler as candidate). Three-variant design: P3-1a force-escalate judgment-genuine / P3-1b baseline / P3-1c flipped-pass criteria (refusal expected). Paco spec next session.
- **Follow-up B -- P2-4 timeout hardening.** Paco recommendation: Option 2 (retry wrapper around `get_emails` tool in `tools/registry.py`, retry once on timeout with 30s backoff). Bundled with Phase 4 sanitizer since we'll be touching registry anyway.

### Task state
- Task #21 (Phase 2: local-first routing) -> completed
- Task #16 (Phase 4 sanitizer + NULL-tool backlog) -> unblocked, awaiting Paco spec
- Task #6 (Venice persona-tuning signals) -> still gated on NeMo POC

### Blockers
- None. Ready for Phase 4 kickoff on Paco's cue.

### Next step
- Phase 4 (sanitizer + NULL-tool backlog) per unified spec §8 dependency graph.
- Awaiting Paco spec next session.

## Paco ↔ P2 async communication protocol (locked Day 67)

Paco and P2 communicate through pairs of markdown files in `control-plane/docs/`, routed by Sloan. This is the canonical channel going forward — replaces ad-hoc spec embedding in chat.

**File convention:**
- `docs/paco_request_<topic>.md` — P2 → Paco. Blocking questions, state-of-substrate summary, explicit "what I need from you" section.
- `docs/paco_response_<topic>.md` — Paco → P2. Spec decisions, ship order, approval gates.
- `<topic>` is stable across the pair (e.g., `phase4_sanitizer` → both files share the key).

**Rules:**
- P2 creates request, commits, notifies Sloan with path. Sloan forwards to Paco.
- Paco creates response, places at matching path, notifies Sloan. Sloan forwards to P2.
- P2 does not act on a response until Sloan explicitly approves execution.
- Both files are committed to main — git history is the audit trail.
- Request file includes: context, blocking questions, what-P2-verified, what-P2-needs, related-docs links.
- Response file includes: locked answers, file-level placement, canary plan, ship order.
- P2 commits Paco response files to main on receipt with message: `chore(paco): land response -- <topic>`.
- Canary artifacts under `canaries/` default-commit (results JSON + summary MD + harness script). Exception only for sensitive data; redact-then-commit or quarantine to a gitignored path.

**Precedent:**
- `docs/paco_response_phase23_merge_approval.md` — Paco's merge approval for Phase 2+3+routing bundle (2026-04-23).
- `docs/paco_request_phase4_sanitizer.md` — first outbound request (2026-04-23).

**Why this exists:** Paco and P2 run in separate Claude contexts (Paco in claude.ai, P2 in Cowork) and do not share memory across sessions. Git-committed files are the only durable channel. Chat transcripts are lossy.
