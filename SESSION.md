# Project Ascension — Day 63
**Date:** Mon Apr 20 2026

## Completed this session
- **Repo hygiene sweep on control-plane-lab** (3 commits pushed to origin/main)
  - 8100c0e feat: standing drift committed — anti-hallucination prompt + send_email tool + 16K max_tokens + truncation continuation (pre-NM work from Apr 4-7)
  - da74a7a chore: gitignored generated reports, runtime state, deliverables/, piper/
  - eda75b6 feat: /chat/private endpoint shipped
- **Alexandra three-tier brain architecture live:**
  - Public /chat -> Anthropic Sonnet (tool use, vision, fast)
  - Private /chat/private -> Goliath qwen2.5:72b (local 70B, zero cloud egress)
  - Small tasks -> TheBeast llama3.1:8b + mxbai-embed-large
- **/chat/private implementation:**
  - Full Alexandra persona via get_system_prompt() + private-mode preamble
  - Persona lock verified — she identifies as Alexandra, not qwen
  - Session namespace isolation: private:{session_id}
  - Non-blocking startup via asyncio.create_task (boot 1.28s, was 48s blocking)
  - Warmup num_ctx=8192, keep_alive=60m — eliminates cold reload
  - Sonnet fallback path if Goliath unreachable
  - ChatResponse extended with brain field for observability
  - PRIVATE_MODEL env var enables Phase B LoRA adapter swap
- **Latency:** Boot 1.28s | First call 9.6s (3.8x better than 36.7s pre-fix) | Warm 1.5s

## Pending
- Phase B: 70B QLoRA run on same pipeline
- Dashboard Private toggle that routes to /chat/private
- Memory distillation (nightly Goliath summarization of pgvector)
- Semantic router for automatic brain selection
- Tier 3 MQTT approval gate wiring
- Schlage lock integration
- Demo video for portfolio

## Known issues / design decisions
- /chat/private first-call floor ~9.6s — bounded by ~2463-token system prompt ingest on 72B Q4 at ~300 tok/s. Accepted. Revisit after Phase B.
- P2 caught service name (orchestrator not ai-operator) and venv path in recon — reconnaissance-first workflow reinforced.
- Paco set <3s criterion without prompt token math; P2 corrected via analysis. Lesson: calculate theoretical floor before setting targets.

## Next session (Day 64)
- LinkedIn post: three-tier brain + iterative optimization story (36.7s -> 9.6s via warmup+context alignment)
- Phase B 70B QLoRA OR dashboard Private toggle (pick one)
