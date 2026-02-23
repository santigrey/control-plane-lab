# Architecture Overview

## Design Principles

- One runtime engine powers multiple playbooks, reducing operational sprawl and keeping behavior consistent.
- LLM outputs are wrapped in deterministic control paths (classification, validation, and bounded tool execution).
- Structured responses are treated as contracts so downstream systems can validate and automate reliably.
- Durability comes before intelligence: events, task state, and outcomes are persisted as the source of truth.
- Observability is first-class through run-level correlation, health/readiness gates, and replayable traces.
- Control-plane orchestration and inference services are explicitly separated to isolate scaling and failure domains.

## High-Level Architecture (ASCII)

```text
                         +----------------------+
Client / API Consumer -->|  FastAPI Runtime     |
   POST /ask, /trace     |  (orchestrator)      |
                         +----------+-----------+
                                    |
                                    | embeds/chat
                                    v
                            +-------+--------+
                            |  Model Service |
                            |    (Ollama)    |
                            +-------+--------+
                                    ^
                                    |
                                    | tool JSON / final answer
                                    |
+----------------------+    +-------+--------+    +----------------------+
| Worker Process       |<-->| PostgreSQL +   |<-->| Tool Registry        |
| (task queue runner)  |    | pgvector (DB)  |    | (ping, sleep, etc.)  |
| claim/execute/retry  |    | memory + tasks |    | validated execution  |
+----------------------+    +----------------+    +----------------------+
```

## System Components

- Runtime (`orchestrator/app.py`): FastAPI control-plane entrypoint. Handles `/ask`, `/healthz`, `/readyz`, and `/trace/{run_id}`.
- Database (`PostgreSQL + pgvector`): Durable system of record for memory events and task queue state (`memory`, `tasks`).
- Model service (Ollama): Embedding generation for retrieval and chat generation for response/tool-call decisions.
- Worker (`orchestrator/ai_operator/worker/runner.py`): Background loop that claims queued tasks, executes handlers, emits result/failure events, and retries within limits.
- Tools (`orchestrator/ai_operator/tools/registry.py`): Registry-based, schema-validated tool execution surface (`ping`, `sleep`, extensible for additional tools).

## Request Lifecycle

1. Client sends `POST /ask` with a prompt.
2. Runtime assigns/propagates `run_id` for correlation across logs, traces, and persisted events.
3. Runtime classifies mode (`remember`, `recall`, or `chat`).
4. For `remember`/`recall`, runtime executes deterministic DB-backed paths and returns directly.
5. For `chat`, runtime calls embedding model, runs vector retrieval from memory, and injects retrieved context.
6. Runtime calls chat model for first response.
7. If model returns strict tool JSON, runtime validates and executes tool, persists `tool_call`/`tool_result`, then performs a second model call for final synthesis.
8. Runtime persists canonical `response` event and returns structured API response (`answer`, `tool_calls`, `retrieved_topk`, `run_id`).
9. Observability path remains available via `/trace/{run_id}` for chronological replay.

## Memory Flow

1. Runtime/worker creates normalized event envelopes (`type`, `source`, `run_id`, `ts`, `data`).
2. Writer persists events to `memory` with `content` as `EVENT:{...}` envelope string, `tool_result` as structured JSONB payload, and optional embedding metadata for retrieval.
3. Retrieval path computes query embedding and searches vector similarity (`top_k`, `min_similarity`) from persisted memory.
4. Retrieved items are injected into generation context and tracked as `retrieved_ids`.
5. Trace endpoint reconstructs run history by parsing persisted `EVENT:` records ordered by `created_at`.

## Tool Execution Flow

1. Model emits strict JSON tool call (`{"tool":"...","args":{...}}`).
2. Runtime parses JSON, verifies tool name exists, and validates args against tool schema.
3. Runtime executes tool handler through registry.
4. Runtime persists both `tool_call` and `tool_result` as first-class memory events.
5. Runtime performs follow-up generation using tool output to produce final answer.
6. API response includes explicit `tool_calls` for client-visible auditability.

## Durability + Failure Handling

- Memory/events are committed to Postgres before completion of request/worker paths.
- Task queue state (`queued`, `running`, `succeeded`, `failed`) is persisted in `tasks`.
- Worker uses atomic `FOR UPDATE SKIP LOCKED` claim semantics for safe concurrent claiming.
- Locks include expiry (`lock_expires_at`) to prevent indefinite ownership.
- Failed tasks re-queue with backoff until `max_attempts`; then transition to terminal `failed`.
- `/healthz` exposes dependency status (API, Postgres, Ollama, worker signal).
- `/readyz` fails closed when core dependencies are unavailable.
- Worker writes `task.failed` / `task.permanently_failed` events with timing and error context.

## Deployment Topology

- Current baseline (Phase I): single-node control-plane deployment.
- In baseline mode, FastAPI runtime, worker process, and Postgres run on the control-plane host.
- In baseline mode, Ollama model endpoint is consumed by runtime via network/API.
- Documented lab target topology maps `sloan3` to control plane + memory DB + orchestration services.
- Documented lab target topology maps `sloan2` to dedicated model/GPU inference.
- Documented lab target topology maps `sloan1` to edge/device integration.
- Design intent is to isolate stateful control services from high-variance GPU workloads.
- Design intent is to preserve clear failure domains between control, inference, and edge concerns.

## Tradeoffs and Known Failure Modes

- Model calls can time out; the runtime returns explicit failure responses and retains deterministic paths (`remember`/`recall`) for core functionality.
- Embedding and generation are coupled to model-service availability, so inference outages degrade both retrieval and response quality.
- Synchronous tool execution keeps control simple and auditable but increases end-to-end request latency for tool-heavy prompts.
- Database latency is on the critical request path for retrieval and event writes, so DB slowdown directly impacts API tail latency.
- Vector similarity retrieval can produce false positives/negatives, requiring threshold tuning and deterministic overrides for critical recall cases.
- Worker retries are intentionally bounded (`max_attempts`) to prevent infinite failure loops, which can leave some tasks terminally failed for operator triage.
- A deterministic recall path exists to guarantee exact phrase retrieval independent of non-deterministic model generation behavior.
