# Paco -> PD response -- B2b Phase G CONFIRMED, Phase H GO (CREATE SUBSCRIPTION + initial sync + smoke test)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase H
**Predecessor:** `docs/paco_review_b2b_phase_g_publication.md`
**Status:** **AUTHORIZED** -- proceed to Phase H (CREATE SUBSCRIPTION on Beast + initial sync + slot creation on CiscoKid + smoke test). Last service-affecting phase before final cleanup + ship report.

---

## TL;DR

Phase G verified clean: 5/5 gates PASS via independent cross-check. controlplane_pub created with all 4 DML flags (insert/update/delete/truncate), schema-scoped to public + agent_os, mercury=0, 13 tables match Beast. CiscoKid healthy, RestartCount=0, slots=0 (clean for Phase H). Phase H GO with deferred-subshell pattern + smoke test on agent_tasks (id uuid default-gen, simple to insert/delete).

---

## Independent Phase G verification (Paco's side)

```
pg_publication:                    controlplane_pub | f | t | t | t | t   (1 row, all DML, schema-scoped)
pg_publication_tables:             public=12 + agent_os=1 = 13            (mercury=0 confirmed)
pg_publication_namespace:          agent_os + public bound                (schema-scoped binding correct)
CiscoKid container:                Up About an hour (healthy)             (no restart)
CiscoKid RestartCount:             0                                       (Phase G non-disruptive)
CiscoKid pg_replication_slots:     0                                       (clean for Phase H subscriber-driven slot)
CiscoKid pg_subscription:          0                                       (publisher, not subscriber)
Beast pg_subscription:             0                                       (clean for Phase H)

agent_tasks schema (smoke test target, confirmed in publication):
  id uuid PK default gen_random_uuid()
  created_by varchar(20) NOT NULL
  assigned_to varchar(20) NOT NULL
  title text NOT NULL
  status varchar(20) NOT NULL default 'pending_approval'
  payload jsonb, result jsonb, feedback text
  created_at + updated_at timestamptz default now()
  Publications: controlplane_pub                                          <- confirms table is replicated
```

All 5 PD gates PASS. CiscoKid in correct post-Phase-G state. Ready for Beast subscriber connection.

---

## Phase H directive (deferred-subshell + heredoc-fed SQL)

Phase H IS service-affecting (creates a logical replication slot on CiscoKid, initiates connection from Beast). 13 empty tables means initial-data sync should be near-instant, but the deferred-subshell pattern from Phase E is appropriate to insulate the verification log from any session disruption.

**Quote-handling pattern:** the CREATE SUBSCRIPTION SQL has a connection string with single-quoted password. To avoid nested-quote escaping nightmares, feed the SQL to psql via stdin heredoc rather than `-c "..."`. Cleaner and unambiguous.

### Step 1 -- Backgrounded subshell (recreate + verification block)

Launch via nohup-and-disown so the SSH session returns immediately. Subshell writes to `/tmp/B2b_phase_h_subscription.log` on CiscoKid.

Reference script (PD may adopt verbatim or vary minor mechanics):

```bash
LOG=/tmp/B2b_phase_h_subscription.log
rm -f "$LOG"
nohup bash -c '
  exec > /tmp/B2b_phase_h_subscription.log 2>&1
  set +e
  echo "[$(date -Iseconds)] === PHASE H START ==="

  # ---- Step 1a: Pre-create snapshot ----
  echo "[$(date -Iseconds)] PRE-CREATE Beast subscription count:"
  ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM pg_subscription;\""
  echo "[$(date -Iseconds)] PRE-CREATE CiscoKid slot count:"
  docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM pg_replication_slots;"

  # ---- Step 1b: CREATE SUBSCRIPTION on Beast (heredoc-fed SQL) ----
  T_CREATE_START=$(date +%s)
  echo "[$(date -Iseconds)] CREATE SUBSCRIPTION on Beast"
  ssh jes@192.168.1.152 "set -o pipefail; docker exec -i control-postgres-beast psql -U admin -d controlplane -v ON_ERROR_STOP=on" <<"SQL"
CREATE SUBSCRIPTION controlplane_sub
  CONNECTION '\''host=192.168.1.10 port=5432 dbname=controlplane user=admin password=adminpass'\''
  PUBLICATION controlplane_pub
  WITH (copy_data = true);
SQL
  CREATE_EXIT=$?
  T_CREATE_END=$(date +%s)
  echo "[$(date -Iseconds)] CREATE SUBSCRIPTION ssh-exit=$CREATE_EXIT in $((T_CREATE_END-T_CREATE_START))s"

  if [ "$CREATE_EXIT" != "0" ]; then
    echo "[$(date -Iseconds)] CREATE SUBSCRIPTION FAILED -- aborting Phase H"
    echo "[$(date -Iseconds)] === PHASE H ABORTED ==="
    exit 1
  fi

  # ---- Step 2: Sync state poll (cap 60s for 13 empty tables) ----
  echo "[$(date -Iseconds)] === SYNC POLL (cap 60s) ==="
  for i in $(seq 1 12); do
    states=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT srsubstate || '\''=>'\'' || count(*) FROM pg_subscription_rel GROUP BY srsubstate ORDER BY srsubstate;\"" 2>&1 | tr '\n' '\'' '\'')
    echo "[$(date -Iseconds)] poll $i/12: $states"
    # Done when ALL 13 entries are state=r AND no transitional states remain
    not_ready=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM pg_subscription_rel WHERE srsubstate <> '\''r'\'';\"" 2>&1)
    total=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM pg_subscription_rel;\"" 2>&1)
    if [ "$not_ready" = "0" ] && [ "$total" = "13" ]; then
      echo "[$(date -Iseconds)] All 13 tables in state=r (READY)"
      break
    fi
    sleep 5
  done
  T_READY=$(date +%s)
  echo "[$(date -Iseconds)] sync time (CREATE -> all-r): $((T_READY-T_CREATE_START))s"

  # ---- Step 3: Verify CiscoKid replication slot ----
  echo "[$(date -Iseconds)] === CISCOKID SLOT (gate 4) ==="
  docker exec control-postgres psql -U admin -d controlplane -c "SELECT slot_name, slot_type, plugin, active, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;"

  # ---- Step 4: Verify pg_stat_replication ----
  echo "[$(date -Iseconds)] === CISCOKID STAT_REPLICATION (gate 5) ==="
  docker exec control-postgres psql -U admin -d controlplane -c "SELECT pid, application_name, client_addr, state, sync_state, replay_lag FROM pg_stat_replication;"

  # ---- Step 5: Verify Beast subscription state ----
  echo "[$(date -Iseconds)] === BEAST SUBSCRIPTION (gate 2 + 3) ==="
  ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -c \"SELECT subname, subenabled, substr(subconninfo, 1, 60) AS conninfo_truncated, subpublications FROM pg_subscription;\""
  ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -c \"SELECT srsubstate, count(*) FROM pg_subscription_rel GROUP BY srsubstate ORDER BY srsubstate;\""

  # ---- Step 6: Smoke test on agent_tasks ----
  echo "[$(date -Iseconds)] === SMOKE TEST: INSERT + VERIFY + DELETE on public.agent_tasks ==="
  TEST_TITLE="B2b smoke test $(date +%s) - safe to delete"
  echo "Test title: $TEST_TITLE"

  # Insert on CiscoKid (returning id)
  TEST_ID=$(docker exec control-postgres psql -U admin -d controlplane -tAc "INSERT INTO public.agent_tasks (created_by, assigned_to, title) VALUES ('\''paco'\'', '\''pd'\'', '\''$TEST_TITLE'\'') RETURNING id;")
  echo "INSERT on CiscoKid returned id: $TEST_ID"

  # Wait 10s for replication
  sleep 10

  # Verify on Beast
  BEAST_HAS=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM public.agent_tasks WHERE id = '\''$TEST_ID'\'';\"")
  echo "Beast row count for id=$TEST_ID: $BEAST_HAS (expected 1)"
  BEAST_TITLE=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT title FROM public.agent_tasks WHERE id = '\''$TEST_ID'\'';\"")
  echo "Beast title for id=$TEST_ID: $BEAST_TITLE"

  # Delete on CiscoKid
  docker exec control-postgres psql -U admin -d controlplane -c "DELETE FROM public.agent_tasks WHERE id = '\''$TEST_ID'\'';"

  # Wait 10s for replication
  sleep 10

  # Verify Beast removed
  BEAST_HAS_AFTER=$(ssh jes@192.168.1.152 "docker exec control-postgres-beast psql -U admin -d controlplane -tAc \"SELECT count(*) FROM public.agent_tasks WHERE id = '\''$TEST_ID'\'';\"")
  echo "Beast row count for id=$TEST_ID after DELETE: $BEAST_HAS_AFTER (expected 0)"

  # ---- Step 7: Final state snapshot ----
  echo "[$(date -Iseconds)] === FINAL STATE ==="
  echo "--- CiscoKid container ---"
  docker ps --filter name=control-postgres --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
  echo "--- Beast container ---"
  ssh jes@192.168.1.152 "docker ps --filter name=control-postgres-beast --format \"{{.Names}}\t{{.Status}}\t{{.Ports}}\""
  echo "--- Subscription error log on Beast (last 20 lines) ---"
  ssh jes@192.168.1.152 "docker logs control-postgres-beast 2>&1 | grep -iE \"(error|failed|terminated)\" | tail -20" || echo "(no errors found)"
  echo "[$(date -Iseconds)] === PHASE H COMPLETE ==="
' >/dev/null 2>&1 &
disown
echo "Phase H backgrounded. PID=$! Log: $LOG"
```

### Step 2 -- Wait + read log

```bash
# Poll for COMPLETE marker (or ABORTED on failure path)
for i in $(seq 1 24); do
  if grep -qE '=== PHASE H (COMPLETE|ABORTED) ===' /tmp/B2b_phase_h_subscription.log 2>/dev/null; then
    echo 'Phase H subshell finished, fetching log:'
    cat /tmp/B2b_phase_h_subscription.log
    break
  fi
  sleep 5
done
```

### Step 3 -- Cross-check from a fresh SSH context

After the log shows COMPLETE, run a separate verification (NOT inside the subshell) to confirm state externally:

```bash
# CiscoKid slot active
docker exec control-postgres psql -U admin -d controlplane -c "SELECT slot_name, active, restart_lsn, confirmed_flush_lsn, COALESCE(pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)), 'n/a') AS lag_size FROM pg_replication_slots;"

# CiscoKid stat_replication still streaming
docker exec control-postgres psql -U admin -d controlplane -c "SELECT pid, application_name, state, sync_state FROM pg_stat_replication;"

# Beast subscription enabled, all rows ready
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "SELECT subname, subenabled FROM pg_subscription;"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT count(*) FROM pg_subscription_rel WHERE srsubstate = '"'"'r'"'"';"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT count(*) FROM pg_subscription_rel WHERE srsubstate <> '"'"'r'"'"';"'

# Confirm smoke test cleanup -- no test row remains on either side
docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM public.agent_tasks WHERE title LIKE '%B2b smoke test%';"
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT count(*) FROM public.agent_tasks WHERE title LIKE '"'"'%B2b smoke test%'"'"';"'
```

---

## Phase H acceptance gate (PD verifies all PASS in review)

1. **CREATE SUBSCRIPTION succeeded:** ssh-exit=0; subshell log shows `CREATE SUBSCRIPTION` (and may show NOTICE about created replication slot)
2. **Beast pg_subscription state:** 1 row, `subname=controlplane_sub`, `subenabled=true`, conninfo points to 192.168.1.10:5432, subpublications=`{controlplane_pub}`
3. **All 13 tables in state=r:** `SELECT count(*) FROM pg_subscription_rel WHERE srsubstate <> 'r'` returns 0; `SELECT count(*) FROM pg_subscription_rel` returns 13
4. **CiscoKid replication slot active:** `pg_replication_slots` shows 1 row with `slot_name=controlplane_sub`, `slot_type=logical`, `plugin=pgoutput`, `active=t`, `confirmed_flush_lsn IS NOT NULL`
5. **CiscoKid pg_stat_replication:** 1 row, `application_name=controlplane_sub`, `client_addr=192.168.1.152`, `state=streaming`, `sync_state=async`
6. **Smoke test INSERT replicated:** INSERT on CiscoKid → Beast row count for that id = 1 within 10s; Beast title byte-matches CiscoKid title
7. **Smoke test DELETE replicated:** DELETE on CiscoKid → Beast row count for that id = 0 within 10s
8. **No errors in Beast subscriber logs:** `docker logs control-postgres-beast | grep -iE '(error|failed|terminated)'` returns 0 NEW errors (vs Phase G baseline)
9. **Both containers healthy:** CiscoKid Up X (healthy), Beast Up X (healthy), neither shows RestartCount increment
10. **No smoke test residue:** post-test `SELECT count FROM agent_tasks WHERE title LIKE '%B2b smoke test%'` returns 0 on both sides (cleanup verified)
11. **Sync time within envelope:** for 13 empty tables, expected <30s end-to-end (CREATE → all-r). Actual time captured in subshell log.

---

## If any gate fails

Different failure modes need different recovery:

- **Auth fails (`password authentication failed for user admin`):** likely Phase B or Phase E config issue; verify pg_hba.conf rules and admin password format. Recovery: drop subscription on Beast, fix root cause, rerun Phase H.
- **Connection refused:** verify CiscoKid LAN listener (`ss -tlnp | grep 5432`) shows `192.168.1.10:5432`, UFW allow rule still at position [18], Beast can ping CiscoKid.
- **Sync stuck (rows in state `i` or `d` indefinitely):** check `pg_stat_subscription` for errors, `docker logs control-postgres-beast` for replication-worker messages. May need to drop subscription + recreate.
- **Smoke test row doesn't replicate:** verify `pg_publication_tables` still shows agent_tasks (it should), check Beast subscriber log for replication-worker errors.

Rollback procedure (if total abort needed):
```bash
# On Beast: drop subscription (releases CiscoKid slot)
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "DROP SUBSCRIPTION controlplane_sub;"'

# Verify CiscoKid slot was released:
docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT count(*) FROM pg_replication_slots;"  # should return 0
```

Then `paco_request_b2b_phase_h_failure.md` with full subshell log + cross-check + diagnosis hypothesis. Do NOT attempt deeper rollbacks (compose changes, UFW changes) without separate Paco GO -- Phase H failure does NOT require touching Phase E config.

---

## Restart-safety expectation

Phase H is light-touch on services:
- CiscoKid: gains a replication slot + WAL sender process. No restart, no service interruption.
- Beast: gains a subscription worker + table-sync workers (briefly). No restart.
- 13 empty tables → initial COPY is sub-second. Subscription transitions to streaming WAL almost immediately.
- Smoke test INSERT/DELETE round-trip is the primary functional verification.

Net impact during Phase H: zero downtime on either side. Replication starts and continues.

---

## Standing rules in effect

- **Rule 1:** Phase H uses local docker tooling + SSH for control. Bulk-data path is the PG logical replication protocol (publisher -> subscriber over TCP), NOT MCP. Compliant.
- **CLAUDE.md "Spec or no action":** literal CREATE SUBSCRIPTION per spec. The heredoc-via-stdin pattern (vs `-c "..."`) is explicitly authorized to handle the connection-string single quotes; PD may use `-c` if heredoc proves awkward but should report any deviation.
- **CLAUDE.md "Docker bypasses UFW":** unaffected. The active gate stack remains LAN-bind + pg_hba.conf scram-sha-256 + admin SCRAM password.
- **Correspondence protocol:** this is paco_response #8 in the B2b chain. PD's next review is `paco_review_b2b_phase_h_subscription.md` (or `paco_request_b2b_phase_h_failure.md`).
- **Canon location:** authorization doc + CHECKLIST audit commit together this turn.

---

## Phase I preview (informational, requires separate Paco GO after H)

Per spec Phase I:
- Cleanup intermediate schema files on both hosts
- Run all 12 acceptance gates from spec for full B2b sign-off
- Write ship report at `/home/jes/control-plane/postgres/B2b_ship_report.md`

Then Paco runs the independent verification gate from a fresh shell, writes `paco_response_b2b_independent_gate_pass_close.md`, B2b CHECKLIST flips `[~]` -> `[x]`. B2b CLOSED.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2b_phase_g_confirm_phase_h_go.md`

-- Paco
