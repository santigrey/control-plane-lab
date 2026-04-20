# Paco Session Anchor — Day 64+
**Last session:** Day 63, Mon Apr 20 2026

## Stack state
- Goliath (GX10) at 192.168.1.20 (wired, static) + 100.112.126.63 (Tailscale), hostname sloan4
- 128GB unified memory, GB10 Grace Blackwell
- Ollama serving: llama3.1:70b, deepseek-r1:70b, qwen2.5:72b
- Dual-backend routing: small/embed -> TheBeast, 70B+ -> Goliath over LAN
- NeMo AutoModel env live: container nemo-finetune, HF cache /home/jes/hf-cache
- LoRA POC checkpoint: /home/jes/finetune-poc/Automodel/checkpoints/epoch_0_step_19/

## Alexandra brain architecture (NEW Day 63)
- Public /chat -> Anthropic Sonnet (tool use, vision)
- Private /chat/private -> Goliath qwen2.5:72b (zero cloud egress, persona-locked, Sonnet fallback)
- PRIVATE_MODEL env var ready for Phase B LoRA swap
- Boot 1.28s, warm call 1.5s, cold call 9.6s (prompt-eval bound)

## Pending work
1. LinkedIn post: three-tier brain + optimization story (36.7s -> 9.6s)
2. Phase B: 70B QLoRA on same pipeline
3. Dashboard Private toggle
4. Memory distillation (nightly Goliath summarization)
5. Semantic router for automatic brain selection
6. Tier 3 MQTT approval gate wiring
7. Schlage lock integration
8. Demo video for portfolio

## Active context
- Sloan in Denver
- Per Scholas continues M/W/F 6-9pm ET
- Min 3 job applications/week for unemployment cert
- LinkedIn posts shipped: Day 61 (GX10 integration), Day 62 (LoRA methodology)
- Next LinkedIn target: Day 63 private reasoning + optimization narrative

## Process notes (reinforce next session)
- ALWAYS sync anchor + SESSION.md first before any work
- Reconnaissance-first for P2 tasks: verify service names, paths, line numbers before coding
- Calculate theoretical latency floor before setting targets
