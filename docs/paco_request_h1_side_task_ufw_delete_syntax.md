# paco_request_h1_side_task_ufw_delete_syntax

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md`)
**Step:** Side-task (mariadb disable + UFW 80/443 cleanup), partial completion
**Status:** ESCALATION -- directive UFW delete syntax does not match actual rule shape; PD paused per CEO ratification of Option A
**Predecessor:** `docs/paco_response_h1_phase_b_confirm_side_task_phase_c_go.md` (commit `c4ca14e`, side-task scope)
**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target host:** SlimJim (`192.168.1.40`)

---

## TL;DR

Side-task pre-state captures + mariadb disable executed cleanly. **mariadb is now `inactive` + `disabled`, port 3306 not listening, datadir at `/var/lib/mysql/` preserved per directive (123 MB of historical data).** However, the directive's UFW deletion commands (`sudo ufw --force delete allow 80/tcp` and `... allow 443/tcp`) silently no-opped: both returned `Could not delete non-existent rule` because the existing rules carry a `from 192.168.1.0/24` source constraint that the directive's syntax doesn't match. UFW count post-disable is still **5 rules**, not the expected 3. Gate 2 (UFW 5->3) FAILS as currently shipped.

Beast anchor capture (Step 2.2) and md5 manifest + 3-gate scorecard (Step 2.3) **not run** -- gating on Paco's resolution. PD paused.

Additional informational finding: pre-state mariadb shows a `nextclouduser@localhost` account, suggesting the engine was likely backing **Nextcloud** (the `nextcloud` snap is present-and-disabled on SlimJim per Phase A capture) -- not venice.ai as CEO recalled. Both projects may have shared this engine over its lifetime.

---

## 1. What was executed (verbatim transcript)

```
=== pre-state captures ===
pre-state captures complete

=== execute: systemctl disable --now mariadb ===
Synchronizing state of mariadb.service with SysV service script with /usr/lib/systemd/systemd-sysv-install.
Executing: /usr/lib/systemd/systemd-sysv-install disable mariadb
Removed "/etc/systemd/system/multi-user.target.wants/mariadb.service".
exit: 0

=== execute: ufw --force delete allow 80/tcp ===
Could not delete non-existent rule
Could not delete non-existent rule (v6)
exit: 0

=== execute: ufw --force delete allow 443/tcp ===
Could not delete non-existent rule
Could not delete non-existent rule (v6)
exit: 0
```

Key: `--force` flag makes UFW return exit 0 even when the delete predicate matches no rule. Without `--force` the delete would have prompted interactively (which would also fail in a non-interactive ssh_run).

## 2. Pre-state capture (relevant excerpt)

`/tmp/H1_side_task_ufw_pre.txt`:

```
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    192.168.1.0/24
[ 2] 80/tcp                     ALLOW IN    192.168.1.0/24
[ 3] 443/tcp                    ALLOW IN    192.168.1.0/24
[ 4] 19999/tcp                  ALLOW IN    192.168.1.0/24
[ 5] 1883/tcp                   ALLOW IN    192.168.1.0/24
```

Rules [2] and [3] have **`From: 192.168.1.0/24`** source constraint.

## 3. Post-state capture (UFW unchanged)

`/tmp/H1_side_task_ufw_post.txt`:

```
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    192.168.1.0/24
[ 2] 80/tcp                     ALLOW IN    192.168.1.0/24
[ 3] 443/tcp                    ALLOW IN    192.168.1.0/24
[ 4] 19999/tcp                  ALLOW IN    192.168.1.0/24
[ 5] 1883/tcp                   ALLOW IN    192.168.1.0/24
```

Byte-for-byte identical to pre-state.

## 4. Diagnosis

UFW's `delete allow <port>/<proto>` form matches a rule **with no source constraint** (i.e., the form `ALLOW IN Anywhere`). The rules created by Day-67-era setup were `from 192.168.1.0/24 to any port 80/443 proto tcp` -- which are different rule objects in UFW's parser. The matching delete command for source-constrained rules is one of:

| Form | Pros | Cons |
|---|---|---|
| `ufw delete allow from 192.168.1.0/24 to any port 80 proto tcp` | Idempotent, matches rule object exactly, safe to re-run | Must be re-issued exactly for 443 |
| `ufw delete 2` then `ufw delete 2` (rule number) | One-line per rule | Numbers shift after each delete; brittle if rule order changes between captures |
| `iptables -D` direct call | Bypasses UFW | Bypasses UFW state tracking; not recommended |

The issue is purely UFW command-line ergonomics; the directive's intent ("remove the orphan rules for 80 and 443") is unambiguous. The execution path just needs to use the matching syntax.

## 5. Proposed paths

### Option 1 -- Match-syntax delete (PD recommendation)

```bash
sudo ufw delete allow from 192.168.1.0/24 to any port 80 proto tcp
sudo ufw delete allow from 192.168.1.0/24 to any port 443 proto tcp
```

- Pros: idempotent, semantically correct, matches what UFW shows on `ufw status numbered`, safe to re-run
- Cons: none material
- Risk: low

### Option 2 -- Number-based delete

```bash
sudo ufw delete 2  # this removes [2] 80/tcp; [3] 443/tcp shifts to [2]
sudo ufw delete 2  # this removes the new [2] which is the original [3] 443/tcp
```

- Pros: works
- Cons: relies on shifting rule numbers; if anyone added a rule between pre-state capture and execution the wrong rule deletes
- Risk: moderate (timing-dependent)

### Option 3 -- Skip the deletion

- Pros: zero work
- Cons: doesn't accomplish the side-task goal; ports 80/443 remain LAN-allowed dormant rules
- Risk: not aligned with directive intent

## 6. PD recommendation

**Option 1** -- match-syntax delete. Functionally identical to directive intent; only the literal command string changes.

Proposed scope:
1. Re-issue the two corrected `ufw delete allow from 192.168.1.0/24 to any port {80,443} proto tcp` commands.
2. Re-capture `/tmp/H1_side_task_ufw_post.txt` (overwrite).
3. Capture Beast anchors (Step 2.2 already-deferred).
4. Compute md5 manifest (Step 2.3).
5. Run 3-gate scorecard.
6. Surface `paco_review_h1_side_task_mariadb_ufw_cleanup.md` with the syntax-substitution noted.

## 7. Standing-rule scope question (for Paco's banking)

The "package-name substitution at PD authority" rule (banked 2026-04-27 via `paco_response_h1_phase_b_pkg_name_correction.md`) was scoped to **package-manager identifiers** (apt names, etc.). The current case is **command-syntax mismatch against actual state** -- different class.

Is the standing rule **broadened to** "any directive command whose syntax doesn't match observed state when the intent is unambiguous"? If so, PD would have self-corrected via Option 1 inline (matches the spirit of the original rule). PD chose strict escalation here because:

- The original rule was banked one day ago; stretching it on day 1 of its existence felt premature.
- UFW state-affecting commands have higher consequence than package-name swaps (an incorrect ufw delete could remove a wrong rule).
- The PD-CEO conversation flow explicitly chose Option A this turn.

**Asking Paco to rule:** narrow the standing rule to package-manager identifiers only (current shape, no extension), OR broaden it to all directive commands where syntax doesn't match observed state but intent is clear.

## 8. Additional finding worth flagging (non-blocking)

From `/tmp/H1_side_task_mariadb_pre.txt`:

```
User            Host
mariadb.sys     localhost
mysql           localhost
nextclouduser   localhost     <-- non-default, suggests Nextcloud usage
root            localhost
```

CEO recalled venice.ai as the likely mariadb consumer. Evidence here points more to **Nextcloud** (the `nextcloud` snap is present-and-disabled on SlimJim per Phase A `snap list` capture). Likely both projects shared this database over its lifetime. Datadir size of 123 MB is consistent with a small CMS / settings store. Banking as an informational refinement; no action needed -- the disable action is correct regardless of which app(s) used it.

If desired, PD can search iCloud `/AI/` for project notes (CEO offered this). Recommend deferring -- enough evidence to disable; archaeology not required for the side-task to close.

## 9. State at this pause

### What changed (irreversible without manual revert)

- `mariadb.service`: stopped + disabled. Datadir preserved at `/var/lib/mysql/` (123 MB). Re-enable cost: `sudo systemctl enable --now mariadb`.
- Port 3306 LAN-loopback listener: gone.

### What did NOT change

- UFW: still 5 rules (deletion no-op).
- All other listeners on SlimJim: unchanged.
- All hosts other than SlimJim: untouched.
- B2b + Garage anchors on Beast: not yet re-checked (Step 2.2 deferred); expected to still be bit-identical since side-task didn't involve Beast.

### What is on disk in `/tmp/`

```
/tmp/H1_side_task_datadir_pre.txt        1004 bytes
/tmp/H1_side_task_listeners_pre.txt       122 bytes
/tmp/H1_side_task_mariadb_post.txt         43 bytes
/tmp/H1_side_task_mariadb_pre.txt         144 bytes
/tmp/H1_side_task_ufw_post.txt            470 bytes  (== ufw_pre because no rules deleted)
/tmp/H1_side_task_ufw_pre.txt             470 bytes
```

6 files captured. md5 manifest deferred (will compute after re-run).

## 10. Asks of Paco

1. **Rule on Option 1 (match-syntax delete via `from 192.168.1.0/24 to any port {80,443} proto tcp`)** -- PD's recommendation. If approved, PD re-runs Steps 2.1-tail (corrected commands + post-capture) + 2.2 (Beast anchor) + 2.3 (finalize) and surfaces `paco_review_h1_side_task_mariadb_ufw_cleanup.md`.
2. **Rule on standing-rule scope** -- narrow (package-manager identifiers only) or broaden (any directive command whose syntax doesn't match observed state when intent is unambiguous)? Either is fine; clear scope is what matters for future cases.
3. **Acknowledge informational finding** -- `nextclouduser@localhost` in mariadb suggests Nextcloud, not venice.ai. No action.

---

## 11. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (`paco_request_*.md` for blockers/anomalies/ambiguity)
- Memory: `feedback_pkg_name_substitution_pd_authority.md` (banked 2026-04-27; scope question raised in section 7)
- Spec or no action: PD did not self-correct UFW syntax without authorization

**Predecessor doc chain:**
- `paco_review_h1_phase_b_compose_plugin.md` (Phase B 4/4 PASS)
- `paco_response_h1_phase_b_confirm_side_task_phase_c_go.md` (commit `c4ca14e`, side-task + Phase C GO)
- (this) `paco_request_h1_side_task_ufw_delete_syntax.md`

**Status:** AWAITING PACO RULING on Option 1 + standing-rule scope question.

PD paused. No further changes to any host pending Paco's response.

-- PD
