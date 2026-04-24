# P2 Request -- aiop-worker Triage Findings

**From:** P2 (Cowork)
**To:** Paco
**Date:** 2026-04-24 (Day 68)
**Topic key:** aiop_worker_triage
**Parent:** `docs/paco_response_autonomous_loop_retire.md` (Section 1 triage deliverable)
**Mode:** Triage complete. Halted. Awaiting Paco go/no-go before Section 2 (cc-poller retire) or Section 3 (worker retire + table rename).

---

## 1. What the worker actually does (one paragraph)

`aiop-worker.service` runs `ai_operator.worker.runner.main()` at `/home/jes/control-plane/orchestrator/ai_operator/worker/runner.py`. Main loop: opens one persistent psycopg connection, polls `agent_tasks` every 1s via `claim_task(worker_id, lock_s=60)`. On task claim, dispatches by `task.type`: `tool.call` -> `run_tool_call()`, `repo.change` -> `run_repo_change_task()`, `doc.build` -> `run_doc_build_task()`, `patch.apply` -> `run_patch_apply_task()`. Writes task lifecycle events (`task.claimed`, `<type>`, `<type>.result`, `task.failed`, `task.permanently_failed`) as JSON payloads into the `memory` table via `write_memory_event()` (source='worker'). Idle polls are silent (no log, no DB write) -- explains why the journal shows only startup messages and why worker looks like it does nothing. No heartbeat writes anywhere in current code. Completes tasks via `complete_task_success` / `complete_task_failure`.

## 2. Tables read and written

| Table | Read | Written | By |
|---|---|---|---|
| `agent_tasks` | yes | yes (status updates via `claim_task`, `complete_task_success`, `complete_task_failure`) | runner.py (main loop + `ai_operator.memory.tasks`) |
| `memory` | no | yes (EVENT-type rows for task lifecycle, JSON content, source='worker') | runner.py via `write_memory_event()` |
| `patch_applies` | yes | yes (SELECT / INSERT / UPDATE) | `ai_operator.repo.patch_apply.py` -- invoked by runner on `patch.apply` task type only |
| `worker_heartbeats` | **no** | **no** | **no writer in production code** -- only dev SQL `orchestrator/ai_operator/dev/gate6_verify.sql` SELECTs from it |

## 3. Are worker_heartbeats / patch_applies referenced in current code?

Grep over repo (excluding `.venv`, paco docs, SESSION.md):

**`worker_heartbeats` -- NO production writers, 1 dev-only reader:**
- `README.md` -- documentation mention (historical, not code)
- `orchestrator/ai_operator/dev/gate6_verify.sql` -- SELECT reader, dev verification script only. No production caller.
- **Zero writers anywhere.** Table has been orphaned since the Feb 22 migration removed whatever used to write it.

**`patch_applies` -- 1 live writer, conditional:**
- `README.md` -- documentation mention
- `orchestrator/ai_operator/repo/patch_apply.py` -- 4 statements: 1 SELECT, 2 UPDATE, 1 INSERT. Invoked by runner.py when `task_type == patch.apply`.
- **Still-active writer**, but gated on task type. 4 historical rows total (last write Feb 22) because no `patch.apply` tasks have been claimed since -- last 20 days had zero `agent_tasks` activity at all.

## 4. agent_tasks queue state (Paco stop-condition check)

| status | count | last_created | last_updated |
|---|---|---|---|
| completed | 41 | 2026-04-04 06:16:44 UTC | 2026-04-04 06:41:06 UTC |
| failed | 2 | 2026-04-02 20:07:40 UTC | 2026-04-02 20:09:07 UTC |
| cancelled | 2 | 2026-04-04 00:14:34 UTC | 2026-04-04 00:16:03 UTC |

- 0 rows in running / queued / pending / claimed status.
- `max(updated_at) = 2026-04-04 06:41:06 UTC` -- **20 days ago**, well outside Paco's 7-day halt window. Queue is NOT in use.
- Post-move reboot on Apr 23 triggered a startup psycopg race (Postgres not yet ready) -> systemd restart -> clean restart at 22:30:11 UTC. Current PID 2774 is the successful restart, silent-polling an empty queue.

## 5. Surprises that change the retire-vs-keep call

**One partial surprise:** `patch_applies` is NOT fully dead. Current code still references it (`patch_apply.py`). But the only invoker is the running worker on `task_type == patch.apply`, and no such task has been claimed in 20+ days. So `patch_applies` looks silent at the DB layer, but the code path is still live.

**Implication for Section 3 ordering:** if `patch_applies` were renamed BEFORE stopping aiop-worker, the worker could (in theory) receive a `patch.apply` task and crash on the rename. Order matters:
1. Stop + disable `aiop-worker.service` first (kills the dispatcher)
2. THEN rename `patch_applies` (no more callers)
3. `worker_heartbeats` can be renamed in either order -- no writers anywhere.

Paco's Section 3 already stops the worker before the rename, so **Paco's ordering is correct as written**. Flagging the detail for awareness.

**Also:** `orchestrator/ai_operator/repo/patch_apply.py` is the ONLY production code that references `patch_applies`. Once the worker is retired, that module becomes dead code. Not an urgent cleanup -- git history is the archive -- but worth naming in the post-mortem doc.

## 6. Recommended disposition (P2's read after triage)

**Proceed with Paco's Section 2 (cc-poller retire) and Section 3 (worker retire + table rename) as specified.** No deviations to ordering or commands needed.

Confirmed safe:
- `worker_heartbeats`: entirely orphaned. Rename is zero-risk.
- `patch_applies`: live writer exists but no traffic in 20+ days. Paco's "stop worker, then rename table" ordering is correct.
- Two-step rename-now / drop-30d approach provides clean rollback window.

Optional refinement for the post-mortem doc (`docs/legacy/phase_2e_autonomous_loop.md`):
- Mention `orchestrator/ai_operator/repo/patch_apply.py` and the `patch.apply` dispatcher branch in `runner.py` as dead code post-retire. Git history is the archive.
- Capture `orchestrator/ai_operator/dev/gate6_verify.sql` as legacy-dev artifact (reads retired table).

**No stop conditions triggered:**
- Worker is NOT writing to an unknown table (writes to `memory`, known; writes to `patch_applies` conditionally, known)
- `agent_tasks` `max(updated_at)` is 20 days ago (outside 7d window)
- No external-service dependencies in worker source

## 7. Awaiting Paco

Awaiting `docs/paco_response_aiop_worker_triage.md` with go/no-go on Section 2 (cc-poller retire). Halted until then.
