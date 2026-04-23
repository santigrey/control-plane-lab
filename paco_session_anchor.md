## PRODUCT VISION (READ FIRST)

See: [docs/alexandra_product_vision.md](./docs/alexandra_product_vision.md)

Alexandra = Jarvis-shaped. Two postures: Alexandra (public+work) and Companion (intimate). One memory, both postures read all. Local-first Qwen2.5:72B on Goliath; Sonnet frontier-fallback that Alexandra herself calls. Autonomy earned through tiered observability. Reject proposals that defend postures by filtering at the data layer.

---

# Paco Session Anchor — Day 67+
**Last session:** Day 66, Wed Apr 22 2026

## STANDING DISCIPLINE (NEVER FORGET - locked Day 65 by Sloan directive)
These are non-negotiable rules for every Paco session going forward. Never skip. Never shortcut.

1. **Root-cause every fix.** No one-line swaps when the underlying pattern is brittle. Every fix ships structural correction + forcing function + temporal safety net. If you find yourself writing a spot-fix that leaves the next bug as a future landmine, STOP and redesign.

2. **Recon starts with git state, always.** Every session, every task that touches code: run `git status` + `git branch --show-current` BEFORE reading any file. Branch state is infrastructure state. The working tree may be on a feature branch with code you don't know about.

3. **Verify scope isolation before claiming a change is safe.** When Sloan asks 'did this break X?' the answer is never 'no' as an assertion. The answer is always: here's the diff, here's the overlap check, here's the live behavior test proving X still works. Prove, don't assert.

## Stack state
- Goliath (GX10) 192.168.1.20 + Tailscale 100.112.126.63, hostname sloan4
- 128GB unified memory, GB10 Grace Blackwell
- Ollama: llama3.1:70b, deepseek-r1:70b, qwen2.5:72b
- Dual-backend routing: small/embed -> TheBeast, 70B+ -> Goliath LAN
- NeMo AutoModel container live, HF cache /home/jes/hf-cache
- LoRA POC checkpoint: /home/jes/finetune-poc/Automodel/checkpoints/epoch_0_step_19/

## Alexandra brain architecture
- Public /chat -> Anthropic Sonnet (tool use, vision)
- Private /chat/private -> Goliath qwen2.5:72b (zero cloud egress, Sonnet fallback)
- Persona mode ("Hey Babe" trigger) -> Goliath-only, sticky sessions, memory tagged intimate, NO Sonnet fallback by design. Module: orchestrator/persona.py. Wired in orchestrator/app.py ~line 885.
- PRIVATE_MODEL env var ready for Phase B LoRA swap
- Boot 1.28s, warm 1.5s, cold 9.6s (prompt-eval bound)

## Alexandra memory layer
- memory_save: FIXED Day 64 (f1084a3)
- memory_recall: FIXED Day 64 (ef1b26e)
- Auto-write path (_store_memory_async in app.py): working
- Memory table 'memory' (singular), vector(1024), hnsw cosine
- Verified bidirectional @ similarity 0.891
- **Venice corpus (Day 66):** 3,134 chunks ingested, tool='venice_ingest'
  - Labels: trading, work, intimate, roleplay, mixed, anchor
  - JSONB metadata in tool_result: label, ts_start, ts_end, n_turns, char_len, speakers, content_hash, idx
  - Pipeline: /home/jes/venice_import/{parse.py, ingest.py}
  - Chunker bounds tuned for mxbai 512-tok cap: max_chars=1400, wall_threshold=1500
  - 41 chunks (1.3%) failed embed (dense code/JSON >512 tok) — accepted
  - Retrieval validated: top-1 sim 0.65-0.78 on canary queries

## Google OAuth (Day 65 hardened)
- SCOPES authoritative list: google_readers.py (NOT reauth_gmail.py)
- Current scopes: gmail.send, gmail.readonly, calendar.events
- _assert_token_scopes() fires in _load_credentials() — loud fail on drift
- reauth_gmail.py imports from google_readers via sibling import
- Token refresh auto on expiry via google-auth-oauthlib
- Re-auth ceremony: ssh -L 8899:localhost:8899 jes@192.168.1.10 then run reauth_gmail.py
- Adding a new Google tool? Add scope to google_readers.SCOPES, run reauth. Nowhere else.

## Tool drift prevention
- Nightly smoke test: tool-smoke-test.timer @ 03:30 UTC
- Script: /home/jes/control-plane/orchestrator/tool_smoke_test.py
- Baseline: 15 PASS / 1 SCHEMA_ISSUE (get_system_status returns None, pre-declared carve-out)
- Telegram alert on any FAIL/EXCEPTION (not SCHEMA_ISSUE)
- Results JSON at /home/jes/control-plane/tool_smoke_test_results.json (gitignored)
- Results also written to pgvector memory table with source='tool_smoke_test'

## Pending work (priority order)
1. get_system_status schema cleanup (return {ok: True, ...} envelope)
2. Dashboard /chat/private toggle (1-session P2 task)
3. LinkedIn post: three-tier brain + optimization story
4. Phase B: 70B QLoRA run
5. Memory distillation (nightly Goliath summarization)
6. Semantic router for automatic brain selection
7. Tier 3 MQTT approval gate wiring
8. Schlage lock integration
9. Demo video for portfolio
10. Smoke test unlisted tools: get_job_pipeline, plan_and_execute, read_course_material

## Active context
- Sloan in Denver
- Per Scholas continues M/W/F 6-9pm ET
- Min 3 job applications/week for unemployment cert
- LinkedIn posts shipped: Day 61, Day 62. Day 63 story (three-tier brain) still queued.

## Process notes (operational hygiene)
- Always sync anchor + SESSION.md first before any work
- Reconnaissance-first for P2 tasks: verify service names, paths, line numbers before coding
- Calculate theoretical latency floor before setting targets
- Audit scripts must load .env or hit orchestrator via HTTP (bare Python produces env-missing false positives)
- Batch shell commands to conserve tool budget
- Sister functions share sister bugs (memory_save + memory_recall was the pattern)
- When MCP rotation drops homelab tools (seen on claude.ai web vs Desktop), switch to Claude Desktop
- homelab_ssh_run has 2000-char limit — split writes into pieces or use heredoc patch scripts

## Day 65 commits
- 281d382 fix(auth): lock Google OAuth scope management

## Day 66 commits
- Venice corpus ingested to memory table (no orchestrator code changes)
- parse.py + ingest.py added under /home/jes/venice_import/ (operator tooling, not in control-plane repo)

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

## 2026-04-22 — Phase 1 shipped, awaiting Phase 2 spec

**State for Paco:**
- Schema + backfill landed per §1.1 / §1.4 verbatim. Commit 14d6fee. 4687 rows migrated clean.
- P2 corrected: no more architectural inference without your signoff. Schema-affecting decisions block on explicit greenlight.
- `mixed=1` in backfill — artifact of UPDATE ordering in §1.4 (intimate classified before mixed on overlapping rows). Flagging in case Phase 5 judgment writer needs awareness; not a correction request.
- Content_type `work`/`system` populate only at write time — confirmed expected per §1.1/§1.4 asymmetry.

**Blocking Paco for Phase 2:**
- §8 Phase 2 reads "local-first routing." Need spec-level detail on:
  - Router boundary (does it live in orchestrator/ai_operator/inference/ollama.py or above it?)
  - Escalation trigger (confidence score? model-emitted flag? both?)
  - Fallback provenance column — write to `memory` at save time, or separate `memory_judgment_log` table per Phase 5?
- P2 will not begin Phase 2 code until spec arrives.

**Next P2 action:** none until Paco ships Phase 2 spec or Sloan overrides.

## 2026-04-23 — Day 67 — Phase 2+3+routing shipped, Phase 4 next

**Shipped (Paco merge-approval, docs/paco_response_phase23_merge_approval.md):**
- FF merge `phase-2-3-routing-bundle` → main: `4fb7797`
- Tag: `v0.memory.routing.1` (pushed)
- Premerge fixes: grounded-save gate hardened (tool-result intersection), thread-safe provenance dict copy, provenance row enrichment (role/grounded/endpoint resolve on both user + assistant rows)
- Canary: 9/11 PASS. P3-1 refusal-to-escalate is intended behavior under Jarvis prompt §ESCALATION, not regression. P2-4 transient Gmail latency.

**Architectural observations (Paco, worth naming):**
- Persona-bleed closed at two layers: prompt (Spec C, Day 66) + save gate (Phase 2+3, Day 67). Retrieval filter + grounded-only writes are now defense-in-depth.
- Phase 5 judgment-writer substrate is intact: provenance JSONB is the projection source; `memory_judgment_log` still open as a Phase 5 design choice.
- Frontier-judgment behavior emerged under Jarvis prompt — Opus declined artificial escalation framing with reasoning ("It's either a test of my judgment (in which case: passing) or an attempt to game the routing system (in which case: no).").

**Current phase: Phase 4 — conversational sanitizer (per unified_alexandra_spec_v1.md §8 dependency graph).**

**Blocking Paco for Phase 4 spec:**
- Sanitizer boundary — pre-LLM input filter, post-LLM output filter, or both?
- Scope — PII redaction only, or broader (endearment normalization for /chat, stale-fact scrubbing, prompt-injection guard)?
- Where does it sit relative to `_search_long_term_memory` endearment filter and the grounded-save gate? Replace, layer, or orthogonal?
- Provenance — does a sanitized-out span get logged to `memory` with a reason, or dropped silently?

**Next P2 action:** none until Paco ships Phase 4 spec. Open follow-ups from Paco merge-approval:
- (a) Canary harness: tag P3-1-style checks as `intended_refusal` vs `regression` so the distinction is machine-readable.
- (b) Provenance projection index — evaluate PG index on `provenance->>'role'` / `provenance->>'grounded'` once memory table ≥10k rows.
