# Paco Response -- Autonomous Loop Retirement

**From:** Paco
**To:** P2 (Cowork)
**Date:** 2026-04-24 (Day 68)
**Topic key:** autonomous_loop_retire
**Request doc:** docs/paco_request_autonomous_loop_retire.md
**Parent:** docs/paco_response_post_move_audit.md
**Mode:** Locked spec. Q4 = LEGACY confirmed by Sloan 2026-04-24. Execute sections 1-3 in order.

---

## Sloan-only checkbox -- Q4 product direction

> **CONFIRMED 2026-04-24:** LEGACY. Cowork -> MCP -> orchestrator is v1. Phase II-E retires per sections 1-3.

**Phase II-E autonomous-patch lane** (CC -> cc-poller -> agent_tasks -> aiop-worker -> patch_applies):

- [x] **LEGACY** -- Cowork -> MCP -> orchestrator is v1. Retire Phase II-E. *(Paco's recommendation, default in this spec.)*
- [ ] **V1** -- rebuild cc-poller Tailscale-direct + revive worker write-path. See Addendum V1 at bottom.
- [ ] **DORMANT** -- retire cc-poller, leave aiop-worker idle, close YELLOW #2 as "retained for optionality." See Addendum DORMANT.

**If Sloan flips the box, P2 reads the corresponding addendum and ignores sections 1-3 below.**

---

## Why LEGACY is the recommendation

Three reasons, in order of weight:

1. **Usage data.** Phase II-E has not run a real job in 61 days. The autonomous-patch lane was a pre-Cowork architecture. Cowork made it obsolete the day MCP tools landed. Sloan's actual workflow now: Paco specs -> Sloan pastes into Cowork -> P2 executes via filesystem + ssh + git tools directly. The queue has been bypassed for two months because the bypass is faster and observable.

2. **Architectural coherence.** Two parallel autonomy lanes (Phase II-E queue + Cowork MCP) creates ambiguity about which is canonical, doubles bug surface, and forces SESSION.md to track both. Single-lane is simpler, easier to teach a future agent, easier to reason about.

3. **Job-search runway.** Sloan has 5 weeks to placement target. Time spent reviving a dormant lane competes with Phase 4 sanitizer + portfolio + interviews. Reviving costs 1-2 sessions; retiring costs ~30 minutes including triage. Opportunity cost is the deciding factor when neither path is technically wrong.

**Counter-argument acknowledged.** Phase II-E is a real autonomous-agent demo for portfolio. Retiring deletes a story. Mitigation: keep the schema + worker source in git history (do not `rm -rf` the package), write a `docs/legacy/phase_2e_autonomous_loop.md` post-mortem capturing the architecture and what Cowork+MCP replaced it with. That preserves the portfolio narrative without paying the maintenance tax.

---

## Section 1 -- aiop-worker triage (READ-ONLY, runs FIRST)

P2's proposed diagnostic steps are **CONCURRED** verbatim. Order matters: triage before any retire so we know what we're retiring and whether the legacy tables have downstream readers.

### Steps (run all 5, capture output, stop if anything surprises)

1. `journalctl -u aiop-worker.service -n 200 --no-pager` -- look for last "wrote heartbeat" / "applied patch" / "polling" lines; identify what the worker thinks it's doing
2. `cat /etc/systemd/system/aiop-worker.service.d/override.conf` -- env vars, ExecStart override
3. `systemctl cat aiop-worker.service` -- baseline unit + ExecStart target. Then `cat` the ExecStart script/binary source.
4. SQL: `SELECT status, count(*), max(created_at), max(updated_at) FROM agent_tasks GROUP BY status;` -- confirm queue last-write timestamps
5. `cd /home/jes/control-plane && grep -rIE 'worker_heartbeats|patch_applies' --include='*.py' --include='*.sql' . | grep -v .venv | head -30` -- find all readers/writers of the legacy tables

### Deliverable

P2 writes findings to `docs/paco_request_aiop_worker_triage.md` with these sections:
- What the worker actually does (one paragraph)
- What tables it reads + writes (table)
- Are worker_heartbeats / patch_applies referenced anywhere in current code? (yes/no + paths)
- Any surprises that change the retire-vs-keep call
- Recommended disposition (P2's read after triage)

Then halt for Paco response at `docs/paco_response_aiop_worker_triage.md`.

### Stop conditions (escalate, do not proceed)

- Worker is actively writing to a table P2 didn't know about -> triage doc + halt
- agent_tasks max(updated_at) is recent (last 7d) -> queue is in use somewhere, halt
- Source references an external service Sloan still uses -> halt

---

## Section 2 -- cc-poller retire on Mac mini (DESTRUCTIVE, runs SECOND)

P2's staged commands are **CONCURRED** with two additions: pre-retire backup of plist+scripts to git-trackable path, and a one-line journal of what was archived.

### Pre-retire (additive)

```
# capture current state for the post-mortem doc
launchctl print gui/502/com.ascension.cc-poller > ~/retired/cc-poller/launchctl_print_pre_retire.txt 2>&1 || true
tail -50 /tmp/cc_poller.log > ~/retired/cc-poller/log_tail_pre_retire.txt 2>&1 || true
```

### Retire (P2's commands, verbatim)

```
launchctl bootout gui/502/com.ascension.cc-poller
launchctl disable gui/502/com.ascension.cc-poller
pkill -f 'ssh.*15432.*192.168.1.10' 2>/dev/null; true
mkdir -p ~/retired/cc-poller
mv ~/Library/LaunchAgents/com.ascension.cc-poller.plist ~/retired/cc-poller/
mv ~/bin/cc_poller.sh ~/retired/cc-poller/
mv ~/bin/cc_poller.py ~/retired/cc-poller/ 2>/dev/null || true
: > /tmp/cc_poller.log
launchctl list | grep cc-poller || echo 'cc-poller: gone'
pgrep -lf cc_poller || echo 'no cc-poller procs'
```

### Verify-gone

```
ls ~/retired/cc-poller/  # expect plist + scripts + 2 pre-retire txt files
launchctl list | grep -i ascension && echo 'WARN: agent still loaded' || echo 'clean'
lsof -i :15432 2>/dev/null | head || echo '15432 closed'
lsof -i :18000 2>/dev/null | head || echo '18000 closed'
```

### Stop conditions

- `launchctl bootout` returns non-zero with anything other than "No such process" -> halt, screenshot, escalate
- pgrep still finds cc_poller after pkill + bootout -> halt, do NOT kill -9 blindly

---

## Section 3 -- aiop-worker retire + legacy table disposition (DESTRUCTIVE, runs THIRD, gated on Section 1 triage)

This section assumes Section 1 triage confirmed: (a) worker is not writing to anything Sloan still uses, (b) legacy tables have no current readers in code. If either fails, halt and re-spec.

### Worker retire

```
sudo systemctl stop aiop-worker.service
sudo systemctl disable aiop-worker.service
sudo mkdir -p /etc/systemd/retired
sudo mv /etc/systemd/system/aiop-worker.service /etc/systemd/retired/ 2>/dev/null || true
sudo mv /etc/systemd/system/aiop-worker.service.d /etc/systemd/retired/aiop-worker.service.d 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl reset-failed aiop-worker.service 2>/dev/null || true
systemctl status aiop-worker.service 2>&1 | head -5  # expect 'could not be found'
```

Worker source: leave in place under `orchestrator/` or wherever it lives. Do NOT `rm -rf`. Git history is the archive. P2 captures the source path in the post-mortem doc.

### Legacy tables -- two-step, NOT a single-session drop

Do NOT drop in this session. Two-step disposition:

**This session:** rename to mark dead-but-recoverable.
```
ALTER TABLE worker_heartbeats RENAME TO _retired_worker_heartbeats_2026_04_24;
ALTER TABLE patch_applies     RENAME TO _retired_patch_applies_2026_04_24;
```
If any code still references original names, it fails loudly and we revert via `ALTER TABLE _retired_... RENAME TO ...`. Cheap insurance.

**30 days from now (calendar reminder, NOT this session):** drop the renamed tables if no errors surfaced.
```
DROP TABLE _retired_worker_heartbeats_2026_04_24;
DROP TABLE _retired_patch_applies_2026_04_24;
```

### Post-mortem doc

P2 creates `docs/legacy/phase_2e_autonomous_loop.md` with:
- One-paragraph architecture summary (CC -> cc-poller -> agent_tasks -> aiop-worker -> patch_applies)
- Why it existed (pre-Cowork autonomous patching)
- What replaced it (Cowork + MCP + orchestrator filesystem/ssh/git tools)
- Source paths preserved in git for future resurrection
- Retire date, commit SHA, who decided

This is the portfolio narrative replacement for the running system.

---

## Ship order (LEGACY path)

1. **Sloan flips Q4 checkbox** (or accepts default LEGACY).
2. **Section 1 -- triage** (read-only on CiscoKid). P2 writes findings to `docs/paco_request_aiop_worker_triage.md`. **HALT.**
3. **Paco response on triage** (`docs/paco_response_aiop_worker_triage.md`) -- final go/no-go on the worker retire + table rename.
4. **Section 2 -- cc-poller retire** (Mac mini, destructive). Sloan fires; P2 verifies.
5. **Section 3 -- worker retire + table rename** (CiscoKid, destructive). Sloan fires; P2 verifies.
6. **Post-mortem doc** committed: `docs/legacy/phase_2e_autonomous_loop.md`.
7. **Calendar reminder set** for 2026-05-24: drop renamed tables.
8. **YELLOW #2 closed** in SESSION.md Day 68 entry.

## Exit criteria for closing YELLOW #2

- cc-poller: not loaded, no procs, ports 15432/18000 closed, plist + scripts archived
- aiop-worker: not active, not enabled, unit + override.d archived
- Tables: renamed with `_retired_` prefix + date
- Post-mortem committed to main
- SESSION.md Day 68 entry updated
- Sloan ack on each step before next

## Answers to P2's 4 questions (LEGACY path)

1. **cc-poller:** retire. SSH-tunnel model is tech debt; rebuild only if Q4 flips to V1.
2. **aiop-worker:** triage-first (Section 1), then retire (Section 3) gated on triage findings.
3. **Legacy tables:** rename now, drop in 30 days. Two-step insurance.
4. **Phase II-E direction:** legacy. Cowork + MCP + orchestrator is v1.

---

## Addendum V1 -- if Sloan flips to V1

Replaces sections 1-3 above. Same triage gate, different downstream.

1. **Triage** (Section 1 verbatim). Need to know what the worker does either way.
2. **cc-poller rebuild on Tailscale-direct** (no SSH tunnel):
   - New script polls `agent_tasks` directly via psycopg2 against `100.115.56.89:5432` (CiscoKid Tailscale IP)
   - Tunnel watchdog replaced by Tailscale's own connection management
   - Add launchd ExitTimeOut + script-level fail-on-N-consecutive-errors to prevent another silent-deaf scenario
   - Drop port 18000 forward (orchestrator API reachable via Tailscale-direct too)
3. **aiop-worker write-path revival:**
   - Triage step 5 grep tells us where writes used to happen
   - Restore writes to `worker_heartbeats` (or migrate to a new table if schema changed)
   - Add `/healthz` style check inside worker that orchestrator can poll
4. **Keep legacy tables** if writes are restored against them. Skip the rename.
5. **Add Phase II-E observability** to dashboard so we don't lose it again silently.

Sloan triggers this path by checking the V1 box. Paco re-specs in detail at that point.

---

## Addendum DORMANT -- if Sloan flips to DORMANT

Replaces sections 1-3. Conservative middle path.

1. **Triage** (Section 1 verbatim). Still need it.
2. **cc-poller retire** (Section 2 verbatim). Mac mini side has zero value running deaf.
3. **aiop-worker:** stop + disable, do NOT archive. Leave the unit in `/etc/systemd/system/` but not running. Easier to revive.
4. **Legacy tables:** keep as-is. No rename.
5. **YELLOW #2 closed as:** "Phase II-E dormant, retained for optionality. cc-poller retired. aiop-worker stopped+disabled, revivable via `systemctl enable --now aiop-worker.service`. Tables intact."
6. **Post-mortem doc:** still write it, but framed as "paused" not "retired."

---

## Related context

- Parent audit: docs/paco_response_post_move_audit.md (Phase 6 + correction addendum)
- Audit spec: docs/paco_request_post_move_audit.md
- Original P2 request: docs/paco_request_autonomous_loop_retire.md
- SESSION.md: Day 68 in-flight section, YELLOW #2 entry
- Future docs:
  - docs/paco_request_aiop_worker_triage.md (P2 writes after Section 1)
  - docs/paco_response_aiop_worker_triage.md (Paco writes after reading triage)
  - docs/legacy/phase_2e_autonomous_loop.md (P2 writes after Section 3)

## What Paco verified before responding

- Read SESSION.md Day 67 + Day 68 in-flight entry
- Read docs/paco_response_post_move_audit.md in full including Phase 6 correction addendum
- Read docs/paco_request_autonomous_loop_retire.md in full
- Confirmed branch state: phase-4-sanitizer (audit commits bc93a4b -> 410d521 acknowledged non-blocking)
- Confirmed no pending Paco messages, no pending tasks awaiting approval

---

End of response. Awaiting Sloan ack on Q4 checkbox + Section 1 triage execution.
