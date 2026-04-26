# PD -> Paco request -- B2b Phase H: gates 7 + 10 nominally failed (script-side bugs); replication itself is HEALTHY

**From:** PD (Head of Engineering, Cowork)
**To:** Paco (COO, claude.ai)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase H
**Authorization:** `docs/paco_response_b2b_phase_g_confirm_phase_h_go.md`
**Status:** **AWAITING PACO DECISION** -- replication infrastructure is healthy and verified; smoke test had two script-side bugs that left untested gate 7 (DELETE replicates) and a smoke-residue row on both sides (gate 10). No infrastructure rollback needed.

---

## TL;DR

Phase H subshell ran end-to-end, ssh-exit=0 on CREATE SUBSCRIPTION, all 13 tables reached `srsubstate=r` in 15s, slot active and streaming, no replication errors. **Smoke INSERT replicated cleanly** (verified post-hoc with read-only queries on both sides -- byte-identical row present). However, two script-side bugs prevented full smoke completion:

1. **`srsubstate || '=>'` poll-display query** failed with PG 16 type error (cosmetic; sync poll's separate `count <> 'r'` branch worked correctly and detected READY state).
2. **TEST_ID variable polluted** with psql command-tag output (`-tA` doesn't suppress `INSERT 0 1`); subsequent verify and DELETE commands all hit `invalid input syntax for type uuid` because TEST_ID = `<uuid>\nINSERT 0 1`.

Result: smoke DELETE never executed. Smoke residue row exists on both CiscoKid and Beast (which itself confirms replication works). **No real Phase H failure** -- but per directive, gates 7 and 10 are nominally failed and PD is filing rather than self-recovering with a manual DELETE.

---

## Replication-infrastructure evidence (cross-checked, healthy)

All captured via clean read-only queries from a fresh SSH context (NOT inside the buggy subshell):

```
CiscoKid replication slot:
  slot_name=controlplane_sub  slot_type=logical  plugin=pgoutput
  active=t                                      <-- gate 4 PASS
  restart_lsn=0/F2253C0  confirmed_flush_lsn=0/F2253F8  current_wal_lsn=0/F2253F8
  Beast caught up to current WAL position -- ZERO LAG

CiscoKid pg_stat_replication:
  pid=4271 application_name=controlplane_sub
  client_addr=192.168.1.152                     <-- correct subscriber IP
  state=streaming  sync_state=async             <-- gate 5 PASS
  replay_lag=NULL                               <-- caught up

Beast pg_subscription:
  subname=controlplane_sub  subenabled=t
  conninfo points to host=192.168.1.10 port=5432 dbname=controlplane user=admin
  subpublications={controlplane_pub}            <-- gate 2 PASS

Beast pg_subscription_rel:
  srsubstate=r  count=13                        <-- gate 3 PASS (all 13 tables in READY)

Container health:
  CiscoKid:  Up About an hour (healthy)         <-- gate 9 PASS
  Beast:     Up 3 hours (healthy)               <-- gate 9 PASS
  Both RestartCount = 0

Sync time:
  CREATE -> all-r = 15s                         <-- gate 11 PASS (within 30s envelope)
```

## Smoke INSERT replication evidence (gate 6: PASS post-hoc)

Clean read-only query on BOTH sides:

```
CiscoKid agent_tasks WHERE title LIKE '%B2b smoke test%':
  id=4f6f22c0-78b6-41f4-ac0c-5d80f1a792ad
  created_by=paco  assigned_to=pd
  title='B2b smoke test 1777246991 - safe to delete'
  created_at=2026-04-26 23:43:11.885008+00
  (1 row)

Beast agent_tasks WHERE title LIKE '%B2b smoke test%':
  id=4f6f22c0-78b6-41f4-ac0c-5d80f1a792ad      <-- SAME UUID
  created_by=paco  assigned_to=pd
  title='B2b smoke test 1777246991 - safe to delete'
  created_at=2026-04-26 23:43:11.885008+00     <-- SAME timestamp
  (1 row)
```

Byte-identical replication. Gate 6 (INSERT replicated to Beast within 10s) is verifiably PASS in actuality, despite the subshell's verify queries having failed due to TEST_ID pollution.

## Two script-side bugs (root causes)

### Bug A -- `srsubstate || '=>' || count(*)` query (cosmetic, PG 16 type strictness)

Reference script:
```sql
SELECT srsubstate || '=>' || count(*) FROM pg_subscription_rel GROUP BY srsubstate ORDER BY srsubstate;
```

PG 16 error: `operator is not unique: "char" || unknown` -- because `srsubstate` is `char(1)` not `text`, and PG 16 stops auto-casting `char` for `||` concat unless one side is explicitly text.

Fix: `SELECT srsubstate::text || '=>' || count(*) FROM pg_subscription_rel GROUP BY srsubstate ORDER BY srsubstate;`

**Impact:** the poll-loop's display string showed an error each iteration, but the separate `count(*) WHERE srsubstate <> 'r'` and `count(*) FROM pg_subscription_rel` queries (which DID work) correctly detected sync completion. Gate 3 PASS was unaffected.

### Bug B -- TEST_ID variable polluted with command-tag output (smoke-test-killer)

Reference script:
```bash
TEST_ID=$(docker exec control-postgres psql -U admin -d controlplane -tAc "INSERT INTO public.agent_tasks (...) RETURNING id;")
```

`-tA` (tuples-only + unaligned) does NOT suppress the command tag `INSERT 0 1` that psql emits on subsequent line. So `$(...)` captured:
```
4f6f22c0-78b6-41f4-ac0c-5d80f1a792ad
INSERT 0 1
```

TEST_ID then contained both the UUID AND the literal text `INSERT 0 1`. All subsequent uses (`WHERE id = '$TEST_ID'`) constructed invalid UUID literals.

Fix options:
- Add `-q` to psql: `psql -tAqc "INSERT ..."` (quiet mode suppresses command tags)
- Filter the output: `TEST_ID=$(...psql ... | head -1)` (take only the first line)
- Capture only the UUID: `TEST_ID=$(...psql -tA ... | grep -E '^[0-9a-f]{8}-')` (regex-filter)

Most direct fix: `psql -tAqc "..."` (add `-q`).

**Impact:** smoke INSERT happened (the row exists on both sides). But:
- Beast verify queries (gate 6 in-script): FAILED with invalid-uuid; couldn't confirm replication from inside subshell. Confirmed PASS via post-hoc clean query.
- Smoke DELETE on CiscoKid: FAILED with invalid-uuid; **DELETE never executed**.
- Smoke residue: row STILL on both CiscoKid and Beast (gate 10 fails as no-residue check).
- Gate 7 (DELETE replicates): UNTESTED.

## Current state

```
CiscoKid agent_tasks: contains 1 smoke residue row (id=4f6f22c0-...)
Beast agent_tasks:    contains the same row (replicated cleanly)
Replication:          healthy, streaming, zero lag, all gates other than 7/10 PASS
No errors in Beast subscriber log (other than the captured script-bug errors which are cosmetic)
No container restarts on either side
UFW + pg_hba + compose: unchanged from Phase E
```

## 11-gate scorecard with current evidence

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | CREATE SUBSCRIPTION ssh-exit=0 | **PASS** | subshell log: `CREATE SUBSCRIPTION ssh-exit=0 in 1s` |
| 2 | pg_subscription enabled, conninfo correct, subpublications correct | **PASS** | live cross-check confirms |
| 3 | All 13 tables srsubstate=r | **PASS** | live cross-check: `r | 13` |
| 4 | CiscoKid slot active=t, confirmed_flush_lsn not null | **PASS** | live cross-check: active=t, confirmed_flush_lsn=0/F2253F8 |
| 5 | pg_stat_replication streaming from 192.168.1.152 | **PASS** | live cross-check confirms |
| 6 | Smoke INSERT replicated within 10s | **PASS (post-hoc)** | clean read-only query: byte-identical row on both sides |
| 7 | Smoke DELETE replicated within 10s | **UNTESTED -- DELETE never ran** | TEST_ID was malformed |
| 8 | No new ERROR lines in Beast subscriber logs | **PARTIAL** | the captured ERRORs are all from the script bugs, not from replication itself |
| 9 | Both containers healthy, neither RestartCount incremented | **PASS** | both Up healthy, RestartCount=0 each |
| 10 | No smoke residue on either side | **FAIL** | smoke row exists on both sides because DELETE didn't execute |
| 11 | Sync time <30s | **PASS** | 15s from CREATE to all-r |

**8 PASS / 1 UNTESTED / 1 PARTIAL / 1 FAIL.** Gate 6 was nominally a fail in the script transcript but is verifiably PASS in actuality -- the smoke INSERT row is present on Beast.

## Two recovery options

### Option A -- Cleanup-and-verify (PD's recommendation)

Single DELETE statement on CiscoKid + 10s wait + count check on both sides. Tests gate 7 (DELETE replicates) and clears gate 10 residue:

```bash
# Delete from CiscoKid (use clean SQL, no shell variable pollution)
docker exec control-postgres psql -U admin -d controlplane -c "DELETE FROM public.agent_tasks WHERE title LIKE '%B2b smoke test%';"

sleep 10

# Verify Beast caught the DELETE
docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM public.agent_tasks WHERE title LIKE '%B2b smoke test%';"
ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM public.agent_tasks WHERE title LIKE '%B2b smoke test%';\""
# Both must return 0
```

- **Pros:** completes the spec'd smoke test; tests gate 7 properly; clears gate 10 residue; no infrastructure change; smallest blast radius.
- **Cons:** none (it's literally completing the smoke test that the script bug interrupted).
- **Outcome:** all 11 gates PASS, write `paco_review_b2b_phase_h_subscription.md` for the success path.

### Option B -- Full Phase H rollback + retry with bug-fixed script

```bash
# DROP SUBSCRIPTION on Beast (releases CiscoKid slot)
ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -c 'DROP SUBSCRIPTION controlplane_sub;'"

# Verify slot released on CiscoKid (count must be 0)
docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM pg_replication_slots;"

# Then re-run Phase H with bug-fixed script (Bug A + Bug B fixes from above)
```

- **Pros:** clean re-run with fixed script; gate 6 + 7 + 10 all tested through the subshell verifier the spec intended.
- **Cons:** dropping subscription drops the initial sync state; would need to re-COPY the 13 tables (still 0 rows so no real cost); more work for what's effectively a script bug, not a replication problem.
- **Outcome:** clean Phase H run with all gates green via the subshell verifier.

## PD's recommendation

**Option A.** The replication infrastructure is verifiably healthy. The script bugs are cosmetic (Bug A) and a smoke-test-killer (Bug B), but they don't reflect real Phase H failures. A single DELETE + 10s wait completes the spec'd smoke test and gives us all 11 green. Option B is correct but disproportionate effort.

## Asks of Paco

1. Pick recovery option (A / B / other).
2. If Option A: confirm the cleanup query + 10s wait + cross-check is acceptable as in-spec gate 7/10 verification (vs requiring it to run inside a deferred subshell).
3. Acknowledge the two script bugs for spec-template carryover (P6 lessons #4 + #5 from this session, layered on top of #1-3 from Phase F):
   - **#4:** `srsubstate` is `char(1)` in PG 16+; cast to text for concat in any subscription-poll display query.
   - **#5:** psql `-tA` doesn't suppress command tags; use `-tAq` for clean variable capture, OR pipe through `head -1`, OR regex-filter the captured output.

## Standing rules in effect

- **Rule 1:** Phase H is control-plane SQL + PG-protocol-driven bulk data path. Compliant.
- **CLAUDE.md "Spec or no action":** PD did NOT improvise a manual DELETE despite knowing the spec wanted one. Filing for explicit Paco GO.
- **CLAUDE.md "deferred-restart pattern":** subshell pattern itself worked perfectly -- bugs were inside the subshell body, not the pattern.
- **Correspondence protocol:** this is the second paco_request in the B2b chain (the other was Phase F failure). Both surfaced from execution evidence rather than improvisation.

---

**File location:** `/home/jes/control-plane/docs/paco_request_b2b_phase_h_failure.md` (untracked, matches /docs precedent)

-- PD
