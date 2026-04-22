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
