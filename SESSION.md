# Project Ascension — Day 62
**Date:** Mon Apr 20 2026

## Completed this session
- Goliath wired ethernet recovered (192.168.1.20 static, WiFi off)
- Pulled qwen2.5:72b — Goliath now serves 3 large models (llama3.1:70b, deepseek-r1:70b, qwen2.5:72b)
- Fixed CiscoKid LAN connectivity (Nighthawk satellite recovery)
- Orchestrator routing updated to Goliath LAN IP (192.168.1.20) for OLLAMA_URL_LARGE
- Cleaned stale runbook reference (:8000/healthz vs :8001 — both by design, correct)
- HuggingFace token provisioned and persisted in ~/.profile (deduped)
- NeMo AutoModel installed on Goliath: NGC container nvcr.io/nvidia/pytorch:25.11-py3, host-mounted HF cache at /home/jes/hf-cache, all dependencies verified
- Pre-flight sanity: torch 2.11.0+cu130 + bf16 forward/backward on GB10 Blackwell verified
- **LoRA fine-tune complete: base Llama 3.1 8B + SQuAD + 20 steps, train loss 0.66→0.20, 1,250 tok/s, 24m wall**
- Checkpoint: /home/jes/finetune-poc/Automodel/checkpoints/epoch_0_step_19/ (43MB adapter)
- Before/after eval generated — LoRA shows terser, faster extractive answers on SQuAD; no catastrophic forgetting on open prompts
- Eval artifacts committed to repo (finetune-poc/)
- LinkedIn post published: methodology-focused on "why base not Instruct"

## Pending
- Phase B: 70B QLoRA run (memory math: ~50-80GB peak, fits on 128GB)
- Tier 3 MQTT approval gate wiring
- Schlage lock integration
- Demo video for portfolio

## Known issues tracked
- NeMo AutoModel saves wrong base model name in checkpoint config.yaml (CLI override not persisted) — resume requires explicit --model.pretrained_model_name_or_path
- pad_token_id warning on Llama 3.1 (non-issue, set explicit pad_token for production)
- ~/.bashrc non-interactive guard blocks env via SSH bash -lc — HF_TOKEN moved to ~/.profile

## Next session
- Phase B 70B QLoRA run on same pipeline
- Demo video
