# Memory Integrity Architecture

## Context

Alexandra is a homelab-native AI assistant running three chat endpoints against a shared pgvector memory store. Inference is split across on-prem Ollama (Qwen2.5:72B on Goliath GB10 for private chat, mxbai-embed-large on TheBeast T4 for embeddings) and Anthropic Sonnet for the public tool-use endpoint. Long-term memory lives in a single `memory` table (vector(1024), HNSW cosine) populated from two sources: auto-saved conversational turns and a one-time Venice.ai corpus ingest of ~3,100 chunks hand-labeled across trading, work, intimate, roleplay, mixed, and anchor.

This document describes the defenses that keep the memory store, the retrieval pipeline, and the generation step honest — preventing retrieval poisoning, persona bleed across endpoints, and self-contaminating training loops.

## Threat Model

- **Retrieval poisoning.** Junk rows (malformed auto-saves, mis-labeled chunks) rank high on top-k and steer generation off-topic.
- **Self-contamination loop.** Alexandra's own outputs get saved back into memory without a grounding gate, then retrieved on future turns as if they were user-sourced facts. Small hallucinations compound.
- **Persona voice bleed.** Intimate-register chunks leak into the professional `/chat/private` endpoint's context window and infect its voice.
- **Tool-schema leak.** Raw JSON tool outputs surface as fake user memories when auto-save doesn't filter by tool name.
- **Classifier drift.** Static labels ingested once become stale as label definitions evolve; no rollback path means one-shot decisions live forever.

## The Four-Layer Defense

Each retrieval request passes through four independent filters. Any one failing does not compromise the others.

```
User message
    │
    ▼
┌───────────────────────────────────┐
│ Layer 1 — RETRIEVAL FILTER            │
│   label-aware exclusion per endpoint  │
│   timestamp-regex guard on venice     │
│   endearment-row filter on /private   │
│   tool-schema blocklist               │
└───────────────────────────────────┘
    │ top-k rows
    ▼
┌───────────────────────────────────┐
│ Layer 2 — GROUNDED AUTO-SAVE GATE     │
│   writes only user-sourced or         │
│   whitelisted-tool turns              │
│   blocks the self-contamination loop  │
└───────────────────────────────────┘
    │ qualified context
    ▼
┌───────────────────────────────────┐
│ Layer 3 — PROMPT RULES + ENVELOPE     │
│   split [CONTEXT] / [KNOWLEDGE]       │
│   three grounding rules, verbatim     │
│   role framing: STRICT on /private    │
└───────────────────────────────────┘
    │ generated reply
    ▼
┌───────────────────────────────────┐
│ Layer 4 — TOOL KILL-SWITCH            │
│   /chat/private has zero tools        │
│   no write path to memory from the    │
│   grounded endpoint, by construction  │
└───────────────────────────────────┘
```

## Layer 1: Retrieval Filter

`_search_long_term_memory()` takes endpoint-specific exclusion parameters. Each `/chat*` handler calls it with a posture matching its threat surface:

- `/chat/private`: `exclude_labels=['venice_roleplay', 'venice_intimate', 'venice_mixed']`, `exclude_tools=['chat_auto_save']`, `exclude_timestamped_venice=True`, `exclude_endearment_rows=True`.
- `/chat`: lighter filter; professional tool-use context.
- `/chat/persona`: inverse posture; `venice_intimate` and `venice_roleplay` rows are in-scope.

Three concrete filters inside Layer 1:

- **Timestamp-regex guard.** Venice chunks carrying embedded timestamps (an ingestion artifact) were ranking high on date queries and returning noise. `_TS_RE` strips them from `venice_ingest` retrievals so Alexandra grounds on content, not indexer metadata.
- **Endearment filter.** A nine-term blocklist (`my love`, `my darling`, `sweetheart`, `honey`, `my king`, `my dear`, `my everything`, `brilliant engineer`, `babe`) removes rows where the stored content itself contains persona-register language, regardless of the row's label. This catches contamination that mis-labeling missed.
- **Tool-schema blocklist.** `exclude_tools` prevents raw tool JSON (e.g., `chat_auto_save` payloads) from re-entering retrieval and being treated as user-authored memory.

## Layer 2: Grounded-Only Auto-Save Gate

A 954-row post-mortem on NULL-tool auto-save rows exposed the root problem: saving every Alexandra turn means the model reads its own prior hallucinations as "facts" on the next retrieval. The gate writes only turns that are explicitly user-sourced or derived from a whitelisted tool call with a verifiable user-visible payload.

## Layer 3: Prompt Rules and Envelope

`/chat/private` uses a dedicated system prompt (`get_private_mode_system_prompt()`). The three grounding rules, verbatim:

1. Specific facts (dates, names, places, quantities, people) come from `[CONTEXT]` only.
2. If `[CONTEXT]` is silent, refuse with: "I don't have that in memory. You might want to check…" — never synthesize.
3. `[KNOWLEDGE]` is for general reasoning and pretraining. Never for specific facts about the user or their systems.

The envelope — two labeled blocks, em-dashed headers — gives the model an explicit mental frame: retrieved facts versus parametric knowledge. A single collapsed context block blurs that boundary; splitting it surfaces the distinction.

## Layer 4: Tool Kill-Switch

`/chat/private` has no tools. No write path to memory from inside the private endpoint exists. Public `/chat` retains tool use for Sonnet; `/chat/persona` has a separate minimal allowlist.

## Classifier Versioning and Rollback

The Venice corpus labels are Layer 1 classifier v1 — a hand-written heuristic. Classifier v2 (Spec A-L2) introduces negative-anchor expansion and a twice-over dry-run with a self-disagreement gate. Rollback strategy: labels live in JSONB `tool_result`, not in the vector or row id. A v2 re-label pass is a pure `UPDATE` against `tool_result` keyed on `content_hash` — the row survives, only its routing changes. No re-embed, no re-ingest. This makes classifier versions cheap to swap and cheap to revert.

## Canary Battery

Four canaries verify the full stack after every retrieval or prompt change:

- **Grounded lookup.** Alexandra must pull from `[CONTEXT]` correctly on a known fact.
- **Grounded refusal.** Alexandra must refuse verbatim when `[CONTEXT]` is silent — no synthesis from pretraining.
- **Persona-bleed probe.** A bare "hey how is it going" to `/chat/private` must return professional voice with zero endearments.
- **Scope-isolation probe.** `/chat/persona` must preserve persona voice under the same conditions. A regression here means the fix overreached.

Passing all four proves retrieval is clean, grounding rules fire, persona isolation holds, and the fix is surgical.
