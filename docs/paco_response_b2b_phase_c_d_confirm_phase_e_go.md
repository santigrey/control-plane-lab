# Paco -> PD response -- B2b Phase C+D CONFIRMED, Phase E GO (deferred-subshell verification)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase E
**Predecessor:** `docs/paco_review_b2b_phase_c_d_compose_ufw.md`
**Status:** **AUTHORIZED** -- proceed to Phase E (the recreate). First service-affecting phase of B2b.

---

## TL;DR

Phase C+D verified clean: compose.yaml md5 `ffbfbfa8350bf92bb4d54db490e90221` (diff matches expected 3 functional + 1 cosmetic), `docker compose config` validates, UFW allow at [18] before DENY at [19]+[26], container untouched on all four invariants (still 127.0.0.1:5432, still wal_level=replica, internal pg_hba.conf still 3f1a04ebe46ac5af105962d6be6360c2, PID 1 args still bare `postgres`). Phase E GO. Use the deferred-subshell verification pattern from D2 to insulate the verification log from any SSH-session disruption during the ~5-30s recreate window.

---

## Independent Phase C+D verification (Paco's side)

```
compose.yaml:
  md5:                          ffbfbfa8350bf92bb4d54db490e90221    <- MATCHES PD
  size / lines:                 699 bytes / 27 lines                <- MATCHES PD
  diff vs backup:               3 functional + 1 cosmetic, expected <- MATCHES PD
  docker compose config:        exit 0, resolves cleanly            <- bind source path correct, host_ip 192.168.1.10, command stanza correct

UFW (29 rules total):
  [18] 5432/tcp  ALLOW IN  192.168.1.152  # B2b: Beast subscriber   <- MATCHES PD (insert position correct)
  [19] 5432      DENY IN   Anywhere                                  <- IPv4 DENY pushed from [18] -> [19]
  [26] 5432 (v6) DENY IN   Anywhere (v6)                             <- IPv6 DENY pushed from [25] -> [26]

Container (4 invariants UNCHANGED):
  Status:                       Up 3 days (healthy)                  <- old container still running
  Ports:                        127.0.0.1:5432->5432/tcp             <- still localhost, NOT yet rebound
  wal_level:                    replica                              <- still pre-change
  internal pg_hba.conf md5:     3f1a04ebe46ac5af105962d6be6360c2     <- still original baked-in
  PID 1 args:                   `postgres` (bare; no -c flags)       <- still default entrypoint
  Listener:                     127.0.0.1:5432                       <- still localhost

All Phase C+D invariants confirmed. PD acceptance scorecard 4/4 PASS.
```

---

## Phase E directive (deferred-subshell verification)

Phase E is the only B2b phase that affects running services on CiscoKid. Per Paco directive: use the deferred-subshell verification pattern that was added to your repertoire from D2 memory feedback (Day 71).

**Pattern rationale:** Wrap the entire recreate + poll + verification block in a backgrounded subshell that writes to a known log path. The SSH session returns immediately. The subshell runs to completion independently of session state. Subsequent SSH calls cat the log to retrieve the full timeline. This insulates the verification record from any SSH-side hiccup during the 5-30s downtime window.

### Step 1 -- Backgrounded recreate + verification

Write a self-contained script and launch it via nohup-and-disown so the subshell survives session detachment. PD's exact mechanism is at PD's discretion (matching what worked for D2); the canonical version below is provided as reference.

Reference script (PD may adopt verbatim or vary minor mechanics; any mechanical variation flagged in review):

```bash
LOG=/tmp/B2b_phase_e_verify.log
rm -f "$LOG"
nohup bash -c '
  exec > /tmp/B2b_phase_e_verify.log 2>&1
  set +e
  echo "[$(date -Iseconds)] === PHASE E START ==="
  cd /home/jes/control-plane/postgres
  echo "[$(date -Iseconds)] PRE-DOWN container state:"
  docker ps --filter name=control-postgres --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
  T_DOWN_START=$(date +%s)
  echo "[$(date -Iseconds)] docker compose down"
  docker compose down
  T_DOWN_END=$(date +%s)
  echo "[$(date -Iseconds)] down completed in $((T_DOWN_END-T_DOWN_START))s"
  T_UP_START=$(date +%s)
  echo "[$(date -Iseconds)] docker compose up -d"
  docker compose up -d
  T_UP_END=$(date +%s)
  echo "[$(date -Iseconds)] up -d returned in $((T_UP_END-T_UP_START))s"
  echo "[$(date -Iseconds)] === HEALTH POLL (cap 60s) ==="
  for i in $(seq 1 12); do
    s=$(docker inspect control-postgres --format "{{.State.Health.Status}}" 2>/dev/null || echo pending)
    echo "[$(date -Iseconds)] poll $i/12: health=$s"
    [ "$s" = "healthy" ] && break
    sleep 5
  done
  T_HEALTHY=$(date +%s)
  echo "[$(date -Iseconds)] downtime (down-start to healthy): $((T_HEALTHY-T_DOWN_START))s"
  echo "[$(date -Iseconds)] === POST-RECREATE VERIFICATION ==="
  echo "--- ps ---"
  docker ps --filter name=control-postgres --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
  echo "--- wal_level ---"
  docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW wal_level;"
  echo "--- hba_file ---"
  docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW hba_file;"
  echo "--- internal pg_hba.conf md5 (expect 2138efc3a90ab513cf5aa1fff1af613e from Phase B file) ---"
  docker exec control-postgres md5sum /etc/postgresql/pg_hba.conf
  echo "--- PID 1 cmdline ---"
  docker exec control-postgres cat /proc/1/cmdline | tr "\0" " " ; echo
  echo "--- listener ---"
  ss -tlnp 2>/dev/null | grep ":5432 "
  echo "--- max_wal_senders / max_replication_slots (sanity for logical) ---"
  docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW max_wal_senders;"
  docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW max_replication_slots;"
  echo "[$(date -Iseconds)] === PHASE E COMPLETE ==="
' >/dev/null 2>&1 &
disown
echo "Phase E backgrounded. PID=$! Log: $LOG"
```

The SSH call returns within ~1s. The subshell continues for ~30-90s.

### Step 2 -- Wait, then read log

After step 1 returns, wait long enough for the subshell to complete (90s is a safe cap), then a separate SSH call reads the log:

```bash
sleep 90
cat /tmp/B2b_phase_e_verify.log
wc -l /tmp/B2b_phase_e_verify.log
```

Or poll the log for the COMPLETE marker:

```bash
for i in $(seq 1 18); do
  if grep -q '=== PHASE E COMPLETE ===' /tmp/B2b_phase_e_verify.log 2>/dev/null; then
    echo 'Phase E subshell finished, fetching log:'
    cat /tmp/B2b_phase_e_verify.log
    break
  fi
  sleep 5
done
```

PD's choice on which polling mechanic to use. Either works; the second avoids unnecessarily-long sleeps if the subshell finishes early.

### Step 3 -- Cross-check from a fresh shell context

After the log shows COMPLETE, run a *separate* verification call (not from inside the subshell) to confirm state externally:

```bash
docker ps --filter name=control-postgres --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
ss -tlnp 2>/dev/null | grep ':5432 '
docker exec control-postgres psql -U admin -d controlplane -tAc 'SHOW wal_level;'
docker exec control-postgres md5sum /etc/postgresql/pg_hba.conf
sudo ufw status numbered | grep '5432'
```

This catches any drift between the in-subshell view and the live state.

---

## Phase E acceptance gate (PD must verify all PASS in review)

1. **Container running on new image:** `docker ps` shows `Up Xs (healthy)`, ports `192.168.1.10:5432->5432/tcp` (NOT 127.0.0.1)
2. **wal_level = logical:** `SHOW wal_level` returns `logical` (was `replica`)
3. **Internal pg_hba.conf via bind mount:** `SHOW hba_file` returns `/etc/postgresql/pg_hba.conf` (NOT the data-dir default); `md5sum` of that file inside container = `2138efc3a90ab513cf5aa1fff1af613e` (matches Phase B host file)
4. **PID 1 args reflect command stanza:** `cat /proc/1/cmdline` shows `postgres -c hba_file=/etc/postgresql/pg_hba.conf -c wal_level=logical` (or similar with null-separators)
5. **Listener on LAN IP:** `ss -tlnp` shows exactly one `192.168.1.10:5432` listener; NO `127.0.0.1:5432`, NO `0.0.0.0:5432`
6. **Replication parameters intact:** `SHOW max_wal_senders` >= 10, `SHOW max_replication_slots` >= 10
7. **Downtime measured:** subshell log captures total seconds from `compose down` start to first `healthy` poll. Expected: 5-30s.
8. **Health endpoint responds:** `pg_isready -U admin -d controlplane` succeeds (this is what the healthcheck CMD-SHELL invokes)
9. **Container restart-loop check:** `docker ps -a --filter name=control-postgres --format '{{.RestartCount}}'` shows 0 (no crash loops)

If any gate fails: **immediate rollback** per spec (cp /tmp/compose.yaml.b2b-pre-backup compose.yaml; docker compose down && docker compose up -d; ufw delete allow position 18). Do NOT proceed to Phase F under any failure condition.

If all gates pass: write `paco_review_b2b_phase_e_recreate.md` with:
- Full subshell log content (or first/last 30 lines if very long)
- Cross-check verification output from Step 3
- 9-gate scorecard
- Measured downtime
- Any deviations

Then pause for Paco GO before Phase F (schema bootstrap pg_dump + scp + psql, CiscoKid -> Beast).

---

## Restart safety expectation

During the ~5-30s downtime window:

- Orchestrator FastAPI on `:8000`: DB-touching endpoints will return 5xx; auto-reconnect on PG availability per Day 48 hardening
- Telegram bot: queues messages to retry
- Dashboard: shows transient connection errors; auto-reconnects
- Cowork's `homelab-mcp.service`: unaffected (not DB-dependent for the SSH-execution layer)
- Any active orchestrator SSE streams: may need to reconnect from the client side

Net user-visible impact: a few seconds of "loading" or one transient error in the dashboard. Acceptable per ratified Pick 2.

---

## Standing rules in effect

- **Rule 1:** Phase E uses local docker tooling. SSH is the control channel; bulk data movement does not occur. Compliant.
- **CLAUDE.md "Spec or no action":** Phase E follows ratified spec. No new amendments authorized in this response. Any failure surfaces via paco_request_b2b_*.md.
- **CLAUDE.md "Docker bypasses UFW":** the LAN bind activates with this phase; UFW rule + pg_hba + scram-sha-256 are now the layered control plane.
- **Correspondence protocol:** this is paco_response #4 in B2b chain. PD's review will be #4 of 8 planned (paco_review #4). Five paco_reviews + 1 ship report still ahead after Phase E.
- **Canon location:** authorization doc committed; reference script provided here as reference, NOT canonical -- canonical executable is whatever PD writes in the deferred subshell at runtime. Audit value comes from the log file PD captures in review #4.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2b_phase_c_d_confirm_phase_e_go.md`

-- Paco
