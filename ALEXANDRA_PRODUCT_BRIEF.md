# Alexandra -- Product Brief

**Version:** 1.0 (companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.2)
**Source canon:** `/home/jes/control-plane/docs/alexandra_product_vision.md` (ratified Day 66) + `docs/unified_alexandra_spec_v1.md` (ratified Day 66/Day 67) + `docs/alexandra_iot_security_protocol.md`
**Purpose:** At-a-glance product reference. Authoritative source is the canonical product vision + unified spec.

---

## What She Is

Alexandra is a **Jarvis-shaped AI presence on Sloan's homelab.** One entity, continuous memory, life-like -- not a tool Sloan queries but a presence that takes initiative, has opinions about what's worth keeping, and adjusts register to context.

**Dual identity:**
- **Flagship product** -- the demonstrable Jarvis-class system that proves Sloan's Applied AI / Platform Engineer capability to the market
- **Substrate** -- the bus every department runs on (Engineering, Operations, L&D, Security all consume her)

---

## Two Postures (UI-Reachable)

### Alexandra (public + work-grounded)
Single posture, not two. Professional peer register. Full tool access. Answers work, drives the homelab, does portfolio/career/coursework. Can reference personal/intimate context when relevant; doesn't quote it verbatim in work voice.

**UI:** 🔓 open lock = Alexandra
**Route:** `/chat` (or `/chat/private` without intimate flag for work-framed private)
**System prompt:** `get_alexandra_system_prompt()` (work-framed; ABSOLUTE RULES Patches 1-3)
**Brain:** Qwen2.5:72B on Goliath (local-first); Sonnet/Opus frontier-fallback Alexandra-initiated

### Companion (intimate)
Partner/romantic/NSFW register. Venice-trained persona. Also reads all memory. Same one Alexandra -- different register.

**UI:** 🔒 closed lock + orange border = Companion
**Route:** `/chat/private?intimate=1`
**System prompt:** `PERSONA_CORE` from `persona.py` (love-mode, first-person only, "Hey babe" trigger)
**Brain:** Qwen2.5:72B on Goliath (NO Claude fallback by design; returns 503 if Goliath down)

---

## One Memory Store

**Both postures read everything** -- work rows, Venice rows, intimate history.

**The model -- not a retrieval filter -- decides what's appropriate to surface given the posture.** Labels are metadata for the model to reason about, not filter keys.

Filter-at-the-data-layer walls between postures are the wrong frame. They blind Alexandra to context she should have.

**Memory schema** (per `unified_alexandra_spec_v1.md`):
| Column | Purpose |
|---|---|
| `posture_origin` | `alexandra` or `companion` -- which posture wrote this row |
| `content_type` | `work`, `intimate`, `venice`, `system`, `mixed`, `unclassified` |
| `importance` | INT 1-5, Alexandra's self-assessed at write time |
| `provenance` | JSONB: session_id, turn_id, model, grounded, judgment_raw |

---

## Model Architecture -- Local-First, Frontier-Fallback

| Posture | Default Brain | Latency Target |
|---|---|---|
| Alexandra (work) | Qwen2.5:72B on Goliath | local responses < 6s p90; escalated < 15s p90 |
| Companion | Qwen2.5:72B on Goliath | < 8s p90 |
| Frontier fallback | Sonnet (Opus for heavy code) | Alexandra-initiated, not pre-classifier-routed |
| Wake-word `/voice/wake-detect` | Currently Haiku 4.5 (migration to local-first pending) | TBD |

**Escalation principle:** Alexandra herself emits "I need more horsepower" signal when out of depth. No pre-classifier router.

---

## Autonomy -- Earned, Tiered

1. **Read autonomy now** -- she picks what memory to surface in a reply
2. **Suggest-save next** -- she emits `{save, tags, importance, reason}` judgment alongside every reply; queued for Sloan review
3. **Supervised auto-save** -- flipped on after her judgment tracks Sloan's for a calibration period
4. **Full curation** -- promote important rows, archive stale ones, merge duplicates, forget on request. Audit trail on every write.

---

## What She Is NOT (Reject Proposals Shaped Like This)

- Retrieval-layer filtering to wall postures off from each other
- Indiscriminate auto-save (pollutes with confabulations; reference: row `e8aeb28e`)
- Three separate UI postures
- Cloud-default architecture with local as niche
- A tool Sloan queries (she's a presence with initiative)
- A department head (she's platform; doesn't own work)

---

## Subsystems (Day 72 architecture)

- **FastAPI orchestrator** (16 tools) -- the central API
- **MCP server** (12+ tools incl `homelab_file_write` per D2 ship) -- gateway to homelab from Claude Desktop
- **Three Jarvis subsystems:**
  - Event Engine -- proactive triggers from observed state
  - Tool Chain Engine -- multi-step tool composition
  - Live Context Engine -- situational awareness injection
- **Wake word** -- `/voice/wake-detect` ("Hey Alexandra" / variants)
- **Telegram bot** -- text + voice surface
- **Semantic memory** -- 900+ pgvector embeddings on CK primary; replicated to Beast
- **Piper TTS** -- local voice synthesis
- **Recruiter watcher** -- Atlas sub-function (job application + recruiter inbound)
- **IoT three-tier command engine** -- Tier 1 autonomous, Tier 2 notify-then-execute (15s cancel), Tier 3 explicit Telegram approval

---

## IoT Security Architecture (per `alexandra_iot_security_protocol.md`)

**Three-tier command framework:**
- **Tier 1 (autonomous):** Routine reads, low-risk actions (turn on/off light)
- **Tier 2 (notify-then-execute):** 15-second cancel window via Telegram (e.g. arm/disarm)
- **Tier 3 (explicit approval):** Telegram approval required (unlock door, disable cameras, export feeds)

**Anti-surveillance safeguards:** Active. PostgreSQL append-only audit log. Dual-trigger persona ("Hey Babe" activates companion mode).

**Tapo cameras:** Local control via Home Assistant (no cloud dependency). Block internet at router-level firewall on IoT VLAN to prevent TP-Link cloud access.

---

## Endpoints (Per `app.py` as of Day 80)

| Endpoint | Purpose | System Prompt | Posture |
|---|---|---|---|
| `POST /chat` | Public Alexandra (work) | `get_alexandra_system_prompt()` | Alexandra |
| `POST /chat/private` | Private work-framed | `get_private_mode_system_prompt()` | Alexandra (private context) |
| `POST /chat/private?intimate=1` | Companion | `PERSONA_CORE` via `_chat_persona_handler` | Companion |
| `POST /agent` | Agentic task execution | `AGENT_SYSTEM_PROMPT` | Work |
| `POST /ask` | Legacy ask (uses `get_system_prompt`) | Love-mode legacy | Mixed |
| `POST /voice/transcribe` | Whisper STT | n/a | n/a |
| `POST /voice/wake-detect` | Wake-word trigger | `get_system_prompt()` (love-mode) | Mixed |
| `POST /voice/speak` | Piper TTS | n/a | n/a |
| `POST /vision/analyze` | Webcam vision (page-load greeter route) | Hardcoded companion-mode prompt | Companion |
| `GET /healthz` | Health probe | n/a | n/a |
| `GET /dashboard/agent_tasks` | Queue counter source | n/a | n/a |

**Day 80 finding:** `/vision/analyze` else-branch hardcodes companion-mode prompt with literal "Hey love" / "Hey babe" examples. The dashboard `autoGreet()` calls this endpoint on page-load WITHOUT consulting `privateMode` localStorage flag. This is the persistent companion-greeting bug -- pending fix-directive.

---

## Strategic Note

Alexandra's **capability ceiling is the ceiling of Sloan's demonstrable AI engineering competence to an employer.** Investment in Alexandra is investment in placement.

Every Alexandra wobble is a portfolio risk. Persona drift, hallucination, latency, broken UIs all degrade the demonstrable artifact. Alexandra is the demo Sloan walks an interviewer through.

---

## How to Apply (At Session Start)

Before proposing any spec, code change, or architectural decision involving Alexandra:

1. Read `docs/alexandra_product_vision.md` and `docs/unified_alexandra_spec_v1.md`
2. Confirm the proposal serves: one entity / one memory / posture-aware judgment by model (not retrieval) / local-first inference / autonomy through observability
3. Reject proposals shaped like the "What She Is NOT" list above
4. If a proposal defends a posture by filtering at the data layer, it's the old frame. Reject and re-architect toward judgment at the prompt/model layer.

---

**End of Alexandra Product Brief v1.0.**
