Shipped a memory-integrity pass on my homelab AI stack this week.

The setup: Alexandra, my local assistant, runs against a shared pgvector memory store seeded with ~3,100 chunks from a multi-year conversational export. Three endpoints, shared store, one embedding model (mxbai-embed-large, 1024-dim, HNSW cosine).

The problem: loose heuristic labels plus an aggressive auto-save policy created two failure modes. Retrieval poisoning — off-category chunks surfacing on unrelated queries. And a self-contamination loop — the model's own prior outputs getting saved as user context, then retrieved as facts on future turns, so every small hallucination compounded across sessions.

The fix was four independent layers:

1. Per-endpoint retrieval filters (label exclusion, tool blocklist, a timestamp-regex guard on the ingested corpus, and a term blocklist on known low-signal rows).
2. A grounded-only auto-save gate so model-generated turns stop re-entering retrieval as user facts.
3. A split `[CONTEXT]` / `[KNOWLEDGE]` envelope in the system prompt with three hard grounding rules: specific facts from CONTEXT only, refuse if CONTEXT is silent, never synthesize specifics from pretraining.
4. A tool kill-switch on the grounded endpoint — no write path to memory from that scope, by construction.

Verified with a four-canary battery: a grounded lookup, a grounded refusal, a scope probe on the grounded endpoint, and a regression probe on the untouched endpoints to confirm the fix was surgical and nothing bled across.

Learning worth naming: with conversational training data, label quality is the ceiling on retrieval quality. You can tune the retriever forever, but if your labels carry the ambiguity you're trying to filter out, you've just moved the problem downstream.
