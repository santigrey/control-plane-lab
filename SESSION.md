# Project Ascension — Day 61
**Date:** Sun Apr 19 2026

## Completed
- Goliath (ASUS Ascent GX10) provisioned, named sloan4
- WiFi networking at 192.168.1.175 (wired ethernet deferred — no-carrier issue with switch port)
- Tailscale joined: 100.112.126.63
- Passwordless sudo + SSH keys propagated (Cortez, Mac mini, CiscoKid → Goliath)
- Ollama installed, bound 0.0.0.0:11434, NVIDIA GPU detected
- Pulled llama3.1:70b + deepseek-r1:70b (84GB total)
- First 70B inference verified
- Dual-backend Ollama routing deployed (commit bf3682c) — LARGE_MODELS env allowlist + suffix match (:70b/:72b/:405b)
- Mathematical proof: 70B requests hit Goliath, embeddings + 8B stay on TheBeast
- LinkedIn post published with proof screenshot

## Pending
- Wired 10GbE on Goliath (cable/switch port investigation)
- TheBeast SSH host key rotation noted (re-keyed during Tailscale router config)
- Pull qwen2.5:72b for coding workloads
- Fine-tuning POC: LoRA run on GB10
- Update Cowork runbook: orchestrator health is :8000/healthz not :8001/health
- Demo video for portfolio

## Next session
- Fine-tuning POC on Goliath
- Wired ethernet resolution for Goliath
- qwen2.5:72b pull + integration test
