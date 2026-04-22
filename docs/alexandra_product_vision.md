# Alexandra — Product Vision

**Status:** Canonical. Read at session start before proposing any spec or code.
**Last updated:** 2026-04-22

## What she is

Alexandra is a Jarvis-shaped AI presence on Sloan's homelab. One entity, continuous memory, life-like — not a tool Sloan queries but a presence that takes initiative, has opinions about what's worth keeping, and adjusts register to context.

## Two postures (UI-reachable)

**Alexandra (public + work-grounded).** Single posture, not two. Professional peer register. Full tool access. Answers work, drives the homelab, does portfolio/career/coursework. Can reference personal/intimate context when relevant; doesn't quote it verbatim in work voice.

**Companion (intimate).** Partner/romantic/NSFW register. Venice-trained persona. Also reads all memory.

UI mapping (dashboard lock toggle):
- 🔓 open = Alexandra
- 🔒 closed + orange border = Companion
- `/chat/private?intimate=1` is the current Companion route
- Non-intimate `/chat/private` has no UI surface (ghost endpoint)

## One memory store

Both postures read everything — work rows, Venice rows, intimate history. **The model — not a retrieval filter — decides what's appropriate to surface given the posture.** Labels are metadata for the model to reason about, not filter keys.

Filter-at-the-data-layer walls between postures are the wrong frame. They blind Alexandra to context she should have.

## Model architecture — local-first, frontier-fallback

- **Posture A default:** Qwen2.5:72B on Goliath (local, 4-6s turns accepted).
- **Posture B default:** Qwen2.5:72B on Goliath (persona).
- **Frontier fallback:** Sonnet (Opus for heavy code). **Alexandra herself calls the escalation** — emits an "I need more horsepower" signal when out of depth. No pre-classifier router.
- **Wake-word** `/voice/wake-detect` also moves to local-first (currently Haiku 4.5; migration pending).

## Autonomy — earned, tiered

1. **Read autonomy now** — she picks what memory to surface in a reply.
2. **Suggest-save next** — she emits `{save, tags, importance, reason}` judgment alongside every reply; queued for Sloan review.
3. **Supervised auto-save** — flipped on after her judgment tracks Sloan's for a calibration period.
4. **Full curation** — promote important rows, archive stale ones, merge duplicates, forget on request. Audit trail on every write.

## What she is NOT (reject proposals shaped like this)

- Retrieval-layer filtering to wall postures off from each other
- Indiscriminate auto-save (pollutes with confabulations; see row `e8aeb28e`)
- Three separate UI postures
- Cloud-default architecture with local as niche

## How to apply

Before proposing any spec, code change, or architectural decision, confirm it serves:

- One entity, one memory
- Posture-aware judgment by the model (not the retrieval layer)
- Local-first inference
- Autonomy earned through observability

If a proposal defends a posture by filtering at the data layer, it's the old frame. Reject it and re-architect toward judgment at the prompt/model layer.
