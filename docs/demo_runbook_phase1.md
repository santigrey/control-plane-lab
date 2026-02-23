# Phase I Demo Runbook (15 Minutes)

## 1. 60-Second Intro
AI Operator is a control-plane service that converts prompts into auditable execution with memory, tool calls, and traceability.

Phase I proves:
- Health/readiness gates are working (`/healthz`, `/readyz`).
- Memory retrieval is functioning (`retrieved_topk > 0`) and deterministic recall works.
- Tool orchestration works (`tool_calls[0].tool == "ping"`).
- End-to-end correlation is visible via `run_id` and `/trace/{run_id}`.
- Structured operational outputs can be produced and schema-validated.

## 2. Architecture Overview
- Runtime loop: `POST /ask` accepts prompt, routes logic, retrieves memory, optionally executes a tool, returns structured response.
- Memory: events/responses persist in Postgres for retrieval, recall, and audit history.
- Tools: strict JSON tool-call pattern allows controlled execution (example: `ping`).
- Durability: state and trace artifacts are persisted for repeatability and post-run inspection.
- Observability: each request has a `run_id`; traces and logs expose request-to-result lineage.

## 3. Live Demo Steps (In Order)
### Step 1: Core Phase I Assertions
Run the deterministic Phase I path (health, recall, tool call, trace, readiness).

```bash
./scripts/demo_phase1.sh
```

### Step 2: Structured Research Playbook
Generate and validate a JSON research plan.

```bash
./scripts/playbook_research.sh "AI incident response for a small SaaS company"
```

### Step 3: Infrastructure Deployment Playbook
Generate and validate a JSON infrastructure automation runbook.

```bash
./scripts/playbook_infra.sh "single-node Ubuntu server" "deploy aiop-worker + api with systemd"
```

## 4. What To Call Out During Output Review
- `run_id`: unique correlation ID per ask/tool execution.
- `retrieved_topk`: proof retrieval returned relevant memory.
- `tool_calls`: explicit tool invocation and result payload.
- `/trace/{run_id}`: chronological evidence of `tool_call -> tool_result -> response`.
- Pass gates: `DEMO PASS` and `PLAYBOOK PASS` lines are objective success criteria.

## 5. Fast Failure Triage (Two Commands)
If any step fails, run these first:

```bash
curl http://127.0.0.1:8000/healthz
tail -n 50 /tmp/orchestrator.log
```
