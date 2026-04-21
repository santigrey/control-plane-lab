# Paco Session Anchor — Day 65+
**Last session:** Day 64, Mon Apr 20 2026 (overnight)

## Stack state
- Goliath (GX10) at 192.168.1.20 + Tailscale 100.112.126.63, hostname sloan4
- 128GB unified memory, GB10 Grace Blackwell
- Ollama: llama3.1:70b, deepseek-r1:70b, qwen2.5:72b
- Dual-backend routing: small/embed -> TheBeast, 70B+ -> Goliath LAN
- NeMo AutoModel container live, HF cache /home/jes/hf-cache
- LoRA POC checkpoint: /home/jes/finetune-poc/Automodel/checkpoints/epoch_0_step_19/

## Alexandra brain architecture (Day 63)
- Public /chat -> Anthropic Sonnet (tool use, vision)
- Private /chat/private -> Goliath qwen2.5:72b (zero cloud egress, persona-locked, Sonnet fallback)
- PRIVATE_MODEL env var ready for Phase B LoRA swap
- Boot 1.28s, warm 1.5s, cold 9.6s (prompt-eval bound)

## Alexandra memory layer (Day 63-64 fixes)
- memory_save: FIXED Day 64 (f1084a3) - mxbai-embed-large + memory table + vec_str cast
- memory_recall: FIXED Day 64 (ef1b26e) - sister bug to save, same fix pattern
- Auto-write path (_store_memory_async in app.py): working, untouched
- Memory table is 'memory' (singular), vector(1024), hnsw cosine index
- Verified bidirectional: save -> recall @ similarity 0.891 on exact match

## Pending work (priority order)
1. MANUAL: Re-run Google OAuth flow (get_emails/get_calendar/get_upcoming_calendar returning invalid_grant)
2. Dashboard /chat/private toggle (1-session P2 task)
3. LinkedIn post: three-tier brain + optimization story
4. Phase B: 70B QLoRA on same pipeline
5. Memory distillation (nightly Goliath summarization)
6. Semantic router for automatic brain selection
7. Tier 3 MQTT approval gate wiring
8. Schlage lock integration
9. Demo video for portfolio

## Day 64 commits
- f1084a3 memory_save handler fix
- 85f4ae1 TOOL FAILURE HONESTY prompt clause
- ef1b26e memory_recall handler fix

## Process notes (reinforce)
- Sync anchor + SESSION.md first, always
- Reconnaissance-first for P2 tasks
- Audit scripts must load .env or hit orchestrator via HTTP
- Batch shell commands to conserve tool budget
- Sister functions share sister bugs

## Day 64 late-session final updates
- Google OAuth re-auth COMPLETE: get_emails/get_calendar/get_upcoming_calendar all live. Refresh token persisted.
- reauth_gmail.py rebuilt (commit 1f79971) for modern google-auth-oauthlib. Uses run_local_server on port 8899. Docstring has the SSH tunnel command.
- P2 handoff drafted: nightly tool_smoke_test.py + systemd timer to detect tool drift before Alexandra encounters it. Spec ready for next session.

## Day 64 commits total
- f1084a3 memory_save fix
- 85f4ae1 TOOL FAILURE HONESTY prompt clause
- ef1b26e memory_recall fix
- cb96a50 session close (earlier)
- 1f79971 reauth_gmail.py rebuild
