# Phase II-E Autonomous Patch Loop -- Post-mortem

**Retired:** 2026-04-24 (Day 68)
**Decided by:** Sloan (Paco recommendation concurred)
**Executed by:** P2 (Cowork)
**Decision thread:**
- `docs/paco_request_autonomous_loop_retire.md` (P2)
- `docs/paco_response_autonomous_loop_retire.md` (Paco; Q4 = LEGACY confirmed)
- `docs/paco_request_aiop_worker_triage.md` (P2; Section 1 triage findings)
- `docs/paco_response_aiop_worker_triage.md` (Paco; GO, no deviations)

---

## Architecture summary

Phase II-E was the first autonomous-execution lane of the AI Operator platform. The loop was:

```
Cowork (Mac mini)
    |  launchd: com.ascension.cc-poller
    v
cc_poller.sh  ->  SSH tunnel (localhost:15432 -> ciscokid:5432)
    v
cc_poller.py  polls agent_tasks for status='approved'
    v  (dispatch)
aiop-worker.service (CiscoKid) claims via ai_operator.worker.runner
    v  dispatches by task_type:
        tool.call    -> run_tool_call()
        repo.change  -> run_repo_change_task()
        doc.build    -> run_doc_build_task()
        patch.apply  -> run_patch_apply_task() -> writes patch_applies
    v
Task lifecycle written to worker_heartbeats (pre-Feb 22)
then migrated to memory table as EVENT rows (post-Feb 22)
    v
complete_task_success / complete_task_failure
```

## Why it existed

Phase II-E was the pre-Cowork autonomous-patching contract. Claude-in-Browser at the time lacked direct filesystem / SSH / git access. The loop gave Claude a queueing interface to request changes that a remote worker would execute. The worker was trusted to apply approved patches, build docs, and execute generic tool calls on behalf of Claude, heartbeating to `worker_heartbeats` to prove liveness to the control plane.

## What replaced it

Cowork + MCP + orchestrator. Starting ~Feb 22 2026, Sloan's workflow shifted to: Paco specs in claude.ai -> Sloan pastes into Cowork -> P2 executes directly via `homelab_ssh_run`, `homelab_file_read`, git ops over SSH, direct psql via `docker exec`. Faster, observable, single-lane. Phase II-E queue was bypassed for two months because the bypass is strictly better for the current workflow shape.

## Feb 22 migration (schema drift worth naming)

**Lesson tag:** `schema-drift-on-migration`

On or around 2026-02-22, the worker binary was rewritten. The new version moved heartbeat + status writes into the unified `memory` table as EVENT-type rows (`source='worker'`, JSON content). The legacy tables `worker_heartbeats` and `patch_applies` were never dropped but also never updated to reflect their orphaned status. This is why the Day 68 post-move audit initially misread the situation as "autonomous loop dormant" -- the loop had migrated its output channel, but the schema docs didn't reflect the change.

**Lesson:** when migrating table usage, update schema docs in the same commit. Table name alone is not self-documenting.

## What was retired

**Mac mini (2026-04-24 16:14 UTC):**
- `com.ascension.cc-poller` LaunchAgent -- bootout + disable
- `~/Library/LaunchAgents/com.ascension.cc-poller.plist` -> `~/retired/cc-poller/`
- `~/bin/cc_poller.sh` -> `~/retired/cc-poller/`
- `~/bin/cc_poller.py` -> `~/retired/cc-poller/`
- `/tmp/cc_poller.log` truncated (was 5.3 MB of connection-refused spam post-tunnel-death)
- Pre-retire state captured: `launchctl_print_pre_retire.txt` + `log_tail_pre_retire.txt`

**CiscoKid (2026-04-24 16:24 UTC):**
- `aiop-worker.service` -- stop + disable
- `/etc/systemd/system/aiop-worker.service` -> `/etc/systemd/retired/aiop-worker.service`
- `/etc/systemd/system/aiop-worker.service.d/` -> `/etc/systemd/retired/aiop-worker.service.d/`
- `daemon-reload` + `reset-failed` clean

**PostgreSQL (2026-04-24 16:25 UTC):**
- `worker_heartbeats` -> `_retired_worker_heartbeats_2026_04_24`
- `patch_applies` -> `_retired_patch_applies_2026_04_24`
- **Drop scheduled:** 2026-05-24 (30 days from retire). Calendar reminder pending.

## Source code preserved in git

Retired but NOT deleted. Git history is the archive. Resurrection paths:

| Path | Role | Post-retire status |
|---|---|---|
| `orchestrator/ai_operator/worker/runner.py` | Main worker loop | dead (no unit to invoke) |
| `orchestrator/ai_operator/repo/patch_apply.py` | `patch.apply` dispatcher + `patch_applies` writer | dead (no caller + table renamed) |
| `orchestrator/ai_operator/worker/artifacts.py` | `repo.change` / `doc.build` dispatchers | dead (no caller) |
| `orchestrator/ai_operator/memory/tasks.py` | `claim_task` / `complete_task_*` helpers | **still used** by orchestrator |
| `orchestrator/ai_operator/tools/registry.py:run_tool_call` | Tool-call dispatcher | **still used** by orchestrator |
| `orchestrator/ai_operator/dev/gate6_verify.sql` | Legacy dev-verify script; reads renamed table | will SELECT-fail if ever re-run; note as legacy-dev artifact |

**Dead-code summary:** with the worker retired, the `patch.apply` / `repo.change` / `doc.build` dispatcher branches in runner.py have no caller. Git archive; no `rm -rf` in this session.

## Resurrection cost (if Phase II-E ever needed)

- Rebuild cc-poller on Tailscale-direct (no SSH tunnel, with watchdog): 1-2 hours
- Re-enable aiop-worker from `/etc/systemd/retired/`: 10 min
- Restore tables: `ALTER TABLE _retired_... RENAME TO ...`: 1 min each
- End-to-end verify with test task: 30 min

Total: half a day. Redeploy, not rebuild.

## Calendar reminder

**2026-05-24: drop `_retired_*` tables** (30 days from retire, confirm no failures surfaced):

```sql
DROP TABLE _retired_worker_heartbeats_2026_04_24;
DROP TABLE _retired_patch_applies_2026_04_24;
```

---

**End of post-mortem. Phase II-E formally retired. Post-move audit YELLOW #2 closed.**
