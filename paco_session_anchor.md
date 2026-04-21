# Paco Session Anchor — Day 66+
**Last session:** Day 65, Tue Apr 21 2026

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
