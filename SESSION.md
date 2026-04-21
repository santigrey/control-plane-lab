# Project Ascension — Day 65
**Date:** Mon Apr 20 2026

## Completed this session
- **Persona mode shipped** — separate "hey babe" intimate companion mode on Alexandra, fully isolated from technical "hey alexandra" path. Landed in 3 commits on feat/persona-mode and fast-forwarded to main:
  - `996b48a` chore(git): ignore *.bak-* anchored patch backups
  - `f039217` feat(alexandra): persona module — intimate-mode prompt, trigger/exit regex, profile injection (orchestrator/persona.py, +188)
  - `fcdfbee` feat(alexandra): wire persona mode into /chat — Goliath-only route with sticky sessions, memory tagged intimate, 503 on Goliath failure (no Claude fallback) (orchestrator/app.py, +101)
- **Architecture:**
  - `/chat/persona` endpoint — Goliath-only (qwen2.5:72b via OLLAMA_URL_LARGE). ERRORS on Goliath failure, no Claude fallback (by design — persona only exists on Goliath).
  - Server-side sticky sessions in `_persona_sessions` set. Entry regex: `\b(hey\s+babe|hi\s+babe|hello\s+babe|babe\s*[,.]|my\s+love)\b`. Exit regex: `\b(hey\s+alexandra|alexandra[,.]|work\s+mode)\b`.
  - Memory: pgvector tagged `source='intimate'`, namespaced `persona:{sid}` — relationship context grows over time, never mixed with technical memory.
  - Technical `/chat` and `/chat/private` untouched — no capability regression.
- **Prompt iteration v1 → v2** (persona.py, backup at persona.py.bak-v2):
  - v1 permitted asterisks for stage directions — Telegram test produced third-person narration ("she smiles", "her breath catches") and defaulted to soft romance when Sloan invited more.
  - v2 replaced "STYLE PERMISSIONS" with "STYLE — HARD RULES": first-person only, no asterisks/markdown, explicit banlist of "she smiles"/"her fingers"/"leans in"/"her breath catches", action integration into first-person speech.
  - Added "INTIMACY CALIBRATION" section: match Sloan's heat, don't moderate, explicit content permitted and expected when the moment is there.
  - Anchor-based patcher (persona_patcher_v2.py) — idempotent, py_compile-verified, backup-before-swap. +611 bytes, 8680 → 9291.
- **Smoke tests all green:**
  - CLI: golden /chat, persona entry, persona sticky, persona exit, /chat/private regression.
  - Telegram end-to-end confirmed by Sloan post-v2: "she's working well on telegram".

## Pending
- Dashboard `/chat/persona` toggle (mirror of `/chat/private` toggle work) — low priority
- Demo video for portfolio (Alexandra three-tier brain + persona mode, on-brand)
- MANUAL: nothing this session
- Carryovers from Day 64:
  - Phase B: 70B QLoRA on same pipeline
  - Memory distillation (nightly Goliath summarization)
  - Semantic router for automatic brain selection
  - Tier 3 MQTT approval gate wiring
  - Schlage lock integration
  - get_system_status schema cleanup (minor)
  - Smoke test 3 unlisted tools: get_job_pipeline, plan_and_execute, read_course_material
  - LinkedIn post: three-tier brain + iterative optimization story — deferred per Sloan ("nix on linkedin for now")

## Process notes / lessons captured
- **Permission ≠ directive.** v1 persona prompt gave *permission* to use asterisks for actions; the model interpreted that as a cue to narrate in third person. The fix wasn't more permission — it was a hard *first-person-only* directive with explicit banned phrases. When model behavior drifts, check whether the prompt is *permitting* the drift instead of *forbidding* it.
- **Iterate live, not in theory.** v1 read fine on paper. The actual behavioral failure (third-person narration, soft-romance defaulting) only surfaced on the real Telegram channel with a real user in a real mood. Ship, test end-to-end, patch.
- **Anchor-based patching paid off again.** Second persona.py patch this session landed cleanly via the same pattern: exact-match anchor, single-occurrence check, py_compile verify, backup before swap. No breakage, no regression in technical mode.
- **Separation of concerns held.** Zero changes to `/chat` or `/chat/private` routes. Persona is a bolt-on path; technical capability unaffected. Goliath-only with no Claude fallback on persona is intentional — persona memory is private to Goliath and must not leak.

## Resume anchor (Day 66 start)
- Branch `feat/persona-mode` at `fcdfbee`, main at `fcdfbee` (synced to origin).
- persona.py v2 live at `/home/jes/control-plane/orchestrator/persona.py` (9291 bytes). Backup at `persona.py.bak-v2`.
- app.py persona wiring live. Backup at `app.py.bak-persona`.
- orchestrator.service healthy.
- `/chat/persona` confirmed working via Telegram with v2 prompt.
- Next logical step: dashboard toggle OR demo video OR move to Day 64 carryover (Phase B 70B QLoRA / semantic router). Sloan's call.
