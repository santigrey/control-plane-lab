# paco_review_h1_side_task_mariadb_ufw_cleanup

**Spec:** H1 -- SlimJim observability + MQTT broker close (`tasks/H1_observability.md`)
**Step:** Side-task -- mariadb disable + UFW orphan rule cleanup (Phase B-adjacent, pre-Phase-C)
**Status:** AWAITING PACO FIDELITY CONFIRMATION + PHASE C GO
**Predecessors (chain):**
- `docs/paco_response_h1_phase_b_confirm_side_task_phase_c_go.md` (commit `c4ca14e`, side-task scope)
- `docs/paco_request_h1_side_task_ufw_delete_syntax.md` (PD escalation after directive UFW syntax no-op'd)
- `docs/paco_response_h1_side_task_ufw_syntax_approved.md` (commit `d2da918`, Option 1 approved + standing rule broadened)

**Author:** PD
**Date:** 2026-04-28 (Day 73)
**Target host:** SlimJim (`192.168.1.40`)

---

## TL;DR

Side-task complete. **All 3 gates PASS.** mariadb stopped + disabled (datadir at `/var/lib/mysql/` preserved per directive `DO NOT purge`); UFW reduced from 5 -> 3 rules (only `22/tcp` + `19999/tcp` + `1883/tcp` remain); B2b + Garage anchors on Beast still bit-identical (`2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`). Execution required one Paco-authorized command-syntax substitution (UFW delete form) per the broadened standing rule. Documentation requirements per `paco_response_h1_side_task_ufw_syntax_approved.md` satisfied below in section 3.

---

## 1. Execution timeline

Three sub-steps, one mid-step escalation, then resume:

| Sub-step | Action | Result |
|---|---|---|
| Pre-state captures | mariadb `SHOW DATABASES` + `SELECT User, Host`; UFW; listeners; datadir | 5 capture files written, content as expected |
| Execute (initial attempt) | `systemctl disable --now mariadb` + 2x `ufw --force delete allow {80,443}/tcp` (directive verbatim) | mariadb disable PASS; both UFW deletes silently NO-OP (`Could not delete non-existent rule`) -- exit 0 because of `--force` |
| ESCALATION | PD filed `paco_request_h1_side_task_ufw_delete_syntax.md` with diagnosis + 3 options + recommendation | CEO ratified Option A (strict escalation) |
| Paco ruling | Option 1 (match-syntax) APPROVED; standing rule BROADENED; Nextcloud finding ACKNOWLEDGED -- `paco_response_h1_side_task_ufw_syntax_approved.md` (commit `d2da918`) | Resume authorized |
| Execute (corrected) | 2x `ufw delete allow from 192.168.1.0/24 to any port {80,443} proto tcp` | Both deletes succeeded (`Rule deleted`, exit 0) |
| Re-capture | Overwrite `/tmp/H1_side_task_ufw_post.txt` | UFW = 3 rules |
| Beast anchor | Capture both containers via MCP->Beast call, write to `/tmp/H1_side_task_anchors_post.txt` | bit-identical to invariant |
| md5 manifest | 7 captures + manifest | written |
| 3-gate scorecard | All 3 PASS | confirmed |

---

## 2. Per-capture summary

### 2.1 mariadb_pre.txt

Databases (4 default schemas + nothing else):
- `information_schema`
- `mysql`
- `performance_schema`
- `sys`

Users (`SELECT User, Host FROM mysql.user`):
```
mariadb.sys     localhost
mysql           localhost
nextclouduser   localhost      <-- non-default, see section 4
root            localhost
```

### 2.2 ufw_pre.txt -> ufw_post.txt

Pre (5 rules):
```
[ 1] 22/tcp                     ALLOW IN    192.168.1.0/24
[ 2] 80/tcp                     ALLOW IN    192.168.1.0/24
[ 3] 443/tcp                    ALLOW IN    192.168.1.0/24
[ 4] 19999/tcp                  ALLOW IN    192.168.1.0/24
[ 5] 1883/tcp                   ALLOW IN    192.168.1.0/24
```

Post (3 rules; original [4]+[5] renumbered to [2]+[3]):
```
[ 1] 22/tcp                     ALLOW IN    192.168.1.0/24
[ 2] 19999/tcp                  ALLOW IN    192.168.1.0/24
[ 3] 1883/tcp                   ALLOW IN    192.168.1.0/24
```

Orphan rules cleared as authorized.

### 2.3 listeners_pre.txt

Single line: `LISTEN 0  80  127.0.0.1:3306  0.0.0.0:*  users:(("mariadbd",pid=1738,fd=23))` -- mariadb on loopback only. Ports 80 and 443 had no listener (orphan UFW rules pointing to nothing -- which is why they were targeted for cleanup).

### 2.4 datadir_pre.txt

`/var/lib/mysql/` had ~123 MB content as of capture: `aria_log.00000001`, `ddl_recovery*.log`, `ib_buffer_pool`, `ibdata1`, `ib_logfile0`, `ibtmp1` and (likely from `ls -la` not shown in head) subdirectories for the configured databases. Files owned `mysql:mysql` mode 660. Directory mode 755. **Preserved on disk per directive's `DO NOT purge` instruction.** Re-enable cost: `sudo systemctl enable --now mariadb` (datadir intact, would resume in same state).

### 2.5 mariadb_post.txt

```
inactive
disabled
3306-listener-check-done
```

(The `3306-listener-check-done` marker is printed unconditionally; the `:3306` line above it would have been the listener entry if any -- absent confirms no listener.)

### 2.6 anchors_post.txt

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

Both bit-identical to the established invariants from B2b + B1 close. ~37 hours of continuous undisturbed operation.

---

## 3. Command-syntax substitution (per broadened standing rule's documentation requirement)

The broadened rule (per `paco_response_h1_side_task_ufw_syntax_approved.md` section 3) requires the review doc to capture: (a) original directive command verbatim, (b) corrected command verbatim, (c) why equivalent, (d) citation.

### 3.1 Original directive command (verbatim)

```bash
sudo ufw --force delete allow 80/tcp
sudo ufw --force delete allow 443/tcp
```

### 3.2 Corrected command (verbatim)

```bash
sudo ufw delete allow from 192.168.1.0/24 to any port 80 proto tcp
sudo ufw delete allow from 192.168.1.0/24 to any port 443 proto tcp
```

### 3.3 Why equivalent

UFW's rule store keys by the full rule object including the source constraint. The directive's `delete allow <port>/<proto>` form generates a rule object with NO source (i.e., `ALLOW IN Anywhere`); UFW found no matching rule and silently no-op'd with `--force`. The corrected `delete allow from 192.168.1.0/24 to any port <N> proto tcp` form generates the exact rule object that pre-state showed as numbered rules [2] and [3]. Both directive and corrected commands target the same intent ("remove the orphan rules for 80 and 443 from LAN"); the corrected form is the syntactic match for our actual rule shape. After execution, ufw's internal rule store is identical to what the directive intended.

### 3.4 Citation

`docs/paco_response_h1_side_task_ufw_syntax_approved.md` (commit `d2da918` on origin/main).

---

## 4. Informational refinement: the mariadb consumer

Pre-state capture surfaced a non-default mysql user: `nextclouduser@localhost`. Combined with the present-and-disabled `nextcloud` snap on SlimJim (per Phase A `services.txt` capture), the most-likely-historical-consumer of this mariadb engine is **Nextcloud**, not venice.ai as CEO recalled. Both projects may have shared the engine over its lifetime. Disable action is correct regardless of consumer. Banking as informational refinement to the Day-67-era scaffolding inventory.

Paco acknowledged this finding in `paco_response_h1_side_task_ufw_syntax_approved.md` section 2.3.

---

## 5. State integrity -- B2b + Garage nanosecond invariants

### 5.1 Pre-side-task (carried forward from Phase B post)

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

### 5.2 Post-side-task (captured this turn)

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

BIT-IDENTICAL nanosecond match across both containers. Side-task confined entirely to SlimJim (mariadb stop+disable, UFW rule deletions). No Beast service touched. B2b nanosecond invariant continues holding from B1 close (commit `1fce00e`, 2026-04-27) through Phase A + Phase B + side-task, ~37 hours of continuous undisturbed operation.

---

## 6. md5 manifest (`/tmp/H1_side_task_md5_manifest.txt`)

```
62541d66b69f10d7dbe080d982a2bab8  H1_side_task_anchors_post.txt
b64e8d5eec7ad5e8fb71908c9dc951cb  H1_side_task_datadir_pre.txt
53092680afff45b03ca821f65c438dda  H1_side_task_listeners_pre.txt
1e9859fca313ce0658f0ccc5eb7aff21  H1_side_task_mariadb_post.txt
17152b959c6e1d079eb4d361ed7b59b9  H1_side_task_mariadb_pre.txt
359c4b59b1c10d1676732272312acaf2  H1_side_task_ufw_post.txt
f3e22a2869484e1c20e67099391a7b70  H1_side_task_ufw_pre.txt
```

7 capture files. `ufw_pre.txt` md5 (`f3e22a28...`) is identical to the earlier Phase A capture md5 -- expected, since UFW state didn't change between Phase A and side-task pre. `ufw_post.txt` md5 differs (`359c4b59...`) -- expected, post-deletion state.

---

## 7. Side-task 3-gate acceptance scorecard

| Gate | Spec wording | Live observed | Result |
|---|---|---|---|
| 1 | mariadb is-active=inactive, is-enabled=disabled, port 3306 NOT listening | `is-active: inactive`, `is-enabled: disabled`, port 3306 listener count = 0 | **PASS** |
| 2 | UFW count drops 5 -> 3 (only 22 + 19999 + 1883 remain) | UFW count = 3; rules `[1] 22/tcp`, `[2] 19999/tcp`, `[3] 1883/tcp` from `192.168.1.0/24` | **PASS** |
| 3 | B2b + Garage anchors bit-identical pre/post | postgres `2026-04-27T00:13:57.800746541Z` + garage `2026-04-27T05:39:58.168067641Z` (both healthy, RestartCount=0) | **PASS** |

**Side-task internal scorecard: 3/3 PASS.**

### 7.1 Verifier-bug self-disclosure

PD's first scorecard run booked Gate 1 as FAIL due to a shell-idiom bug: `M_ACTIVE=$(systemctl is-active mariadb)` propagates the systemctl exit code (which is 3 for inactive, 1 for failed-states), and the `&&` chain bailed before printing values + reaching the boolean test. Re-ran with `set +e` and explicit `if`-block; values confirmed correct (inactive / disabled / 0 listeners). The state was always correct; only the verifier was wrong. Fix banked as a footnote: when checking exit-coded systemctl outputs in shell, use `; ` (statement separator) not `&&` (short-circuit AND), or `set +e` and an explicit conditional.

---

## 8. State at end of side-task

### SlimJim
- `mariadb.service`: inactive + disabled. Datadir preserved at `/var/lib/mysql/` (123 MB).
- Port 3306: no longer listening.
- UFW: 3 rules (`22/tcp`, `19999/tcp`, `1883/tcp` from `192.168.1.0/24`).
- Listeners (LAN-exposed): only `:22` + `:19999` (unchanged from Phase A baseline).
- Loopback-only services: containerd, systemd-resolve, otel-plugin, netdata-statsd remain. (mariadbd `127.0.0.1:3306` was the only listener change vs Phase A.)
- Docker compose v2 plugin still installed; jes still in `docker` group (no Phase B regression).

### Beast (read-only confirmation)
- `control-postgres-beast`: healthy, RestartCount=0, anchor preserved.
- `control-garage-beast`: healthy, RestartCount=0, anchor preserved.

### CiscoKid (read-only confirmation)
- HEAD `d2da918`. This review doc to be untracked-pending-Paco-confirmation per standing pattern.

---

## 9. Asks of Paco

1. **Confirm side-task 3/3 gates PASS** against the captured evidence (sections 2 + 7).
2. **Authorize Phase C GO** (mosquitto 2.x install + dual-listener config + smoke test) per spec section 7 lines 150-218, with the Q3 UFW idempotency guard (`grep -qE` for pre-existing 1883/tcp rule before any add) already authorized in `paco_response_h1_phase_a_confirm_phase_b_go.md`.
3. **Bank verifier-bug self-disclosure (section 7.1)** as a P6 lesson candidate, OR rule that it's too localized for a formal lesson. PD recommends localized footnote; not in same league as #11 (which had cross-spec applicability). If banking, suggested wording: *"Shell verifier scripts using `M=$(systemctl is-active <unit>)` must avoid `&&` chaining around the assignment because systemctl returns non-zero for non-running states. Use `;` separator (with `set +e`) and explicit `if`-block instead."*
4. **Acknowledge banking the broadened standing rule** to PD memory (`feedback_pkg_name_substitution_pd_authority.md` superseded by an updated version reflecting the broadened scope + 3 guardrails). PD will update memory after this review doc lands.

---

## 10. Cross-references

**Standing rules invoked:**
- Memory: `feedback_paco_review_doc_per_step.md` (per-step review docs in `/home/jes/control-plane/docs/`)
- Memory: `feedback_pkg_name_substitution_pd_authority.md` (banked 2026-04-27, narrow scope; superseded by broadened version per `paco_response_h1_side_task_ufw_syntax_approved.md`)
- Spec or no action: PD escalated the directive command-syntax issue rather than self-correcting under the original narrow rule
- Broadened standing rule (now in effect): all directive command-syntax corrections within agreed strategy at PD authority + 3 guardrails (per Paco's response section 3)

**Predecessor doc chain:**
- `paco_review_h1_phase_a_baseline.md` (Phase A)
- `paco_response_h1_phase_a_confirm_phase_b_go.md` (Phase A confirm + Phase B GO + Q3/Q4 rulings)
- `paco_review_h1_phase_b_compose_plugin.md` (Phase B)
- `paco_response_h1_phase_b_confirm_side_task_phase_c_go.md` (Phase B confirm + side-task scope + Phase C GO conditional on side-task close)
- `paco_request_h1_side_task_ufw_delete_syntax.md` (PD escalation, mid-side-task)
- `paco_response_h1_side_task_ufw_syntax_approved.md` (Option 1 approved + rule broadened)
- (this) `paco_review_h1_side_task_mariadb_ufw_cleanup.md`

**Capture files on disk (SlimJim):**
- `/tmp/H1_side_task_{anchors_post,datadir_pre,listeners_pre,mariadb_post,mariadb_pre,ufw_post,ufw_pre}.txt`
- `/tmp/H1_side_task_md5_manifest.txt`

---

## 11. Status

**AWAITING PACO FIDELITY CONFIRMATION + PHASE C GO.**

PD paused. SlimJim infra changed: mariadb stopped+disabled (datadir preserved), UFW reduced from 5 to 3 rules. No CiscoKid file touched beyond this review doc. No Beast service touched. B2b + Garage anchors preserved bit-identical.

Ready to begin Phase C (mosquitto 2.x + dual-listener config + smoke test) on Paco's authorization.

-- PD
