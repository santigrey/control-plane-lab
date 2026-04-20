# Project Ascension — Day 62
**Date:** Mon Apr 20 2026

## Completed this session
- Goliath wired ethernet recovered (192.168.1.20, /home/jes static, WiFi off)
- Pulled qwen2.5:72b → Goliath now serving 3 large models (llama3.1:70b, deepseek-r1:70b, qwen2.5:72b)
- Fixed CiscoKid LAN connectivity (Nighthawk satellite recovery)
- Orchestrator routing updated to use Goliath LAN IP (192.168.1.20) for OLLAMA_URL_LARGE
- Cleaned stale runbook reference (:8000/healthz vs :8001 — by design, both correct)
- HuggingFace token provisioned and persisted (HF_TOKEN in ~/.profile, deduped)
- NeMo AutoModel install on Goliath: NGC container nvcr.io/nvidia/pytorch:25.11-py3, host-mounted HF cache, all dependencies verified
- Pre-flight sanity check: torch 2.11.0+cu130 + bf16 forward/backward on GB10 Blackwell verified
- **LoRA fine-tune complete: base Llama 3.1 8B + SQuAD + 20 steps, train loss 0.66→0.20, 1,250 tok/s, 24m wall, checkpoint at /home/jes/finetune-poc/Automodel/checkpoints/epoch_0_step_19/**

## Pending
- Generate before/after inference samples (LoRA portfolio shot)
- LinkedIn post for fine-tuning milestone
- Phase B: 70B QLoRA run (next session, ~50-80GB peak mem expected)
- Tier 3 MQTT approval gate wiring
- Schlage lock integration
- Demo video for portfolio

## Known issues to track
- NeMo AutoModel checkpoint config.yaml saves base model name from recipe default, not CLI override (resume requires explicit --model.pretrained_model_name_or_path)
- pad_token_id warning on Llama 3.1 (non-issue for non-MoE, set explicit pad_token for production)
- ~/.bashrc non-interactive guard blocks env loading via SSH `bash -lc` — moved HF_TOKEN to ~/.profile

## Next session
- Before/after inference generation + LinkedIn post
- Phase B 70B QLoRA
