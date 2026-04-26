# Paco -> PD response -- B2b Phase E CONFIRMED, Phase F GO (schema bootstrap pg_dump + scp + psql)

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase F
**Predecessor:** `docs/paco_review_b2b_phase_e_recreate.md`
**Status:** **AUTHORIZED** -- proceed to Phase F (schema bootstrap CiscoKid -> Beast)

---

## TL;DR

Phase E recreate verified clean: 9/9 gates PASS via independent fresh-shell cross-check. Container Up 4+ min (healthy) on `192.168.1.10:5432->5432/tcp`, `wal_level=logical`, internal pg_hba.conf md5 `2138efc3a90ab513cf5aa1fff1af613e` (matches Phase B), PID 1 args show command stanza, max_wal_senders/slots both 10, RestartCount=0, pg_publication/pg_replication_slots both 0 (clean baseline for F/G/H). Measured downtime 16s within 5-30s envelope. **One observation correction:** orchestrator was NOT inactive; PD checked the wrong service name. Phase F GO with explicit pg_dump + scp + psql directive (Pick 4 ratified, Rule 1 carve-out for SCP bulk transport).

---

## Independent Phase E verification (Paco's side)

```
Container (cross-checked from fresh SSH context):
  Status:                    Up 4 minutes (healthy)         <- old container removed, new one running
  Ports:                     192.168.1.10:5432->5432/tcp    <- LAN bind active (was 127.0.0.1)
  StartedAt:                 2026-04-26T22:23:29.359Z
  RestartCount:              0                              <- no crash loops

Listener:                    LISTEN 192.168.1.10:5432       <- count=1, single LAN listener
No 127.0.0.1:5432:           confirmed absent
No 0.0.0.0:5432:             confirmed absent

PG settings:
  wal_level:                 logical                        <- gate 2 PASS (was replica)
  hba_file:                  /etc/postgresql/pg_hba.conf    <- gate 3a PASS (bind-mounted path)
  max_wal_senders:           10                             <- gate 6a PASS (>=1 needed for logical)
  max_replication_slots:     10                             <- gate 6b PASS (>=1 needed for slot)

Internal pg_hba.conf md5:    2138efc3a90ab513cf5aa1fff1af613e <- gate 3b PASS (matches Phase B host file)
PID 1 cmdline:               postgres -c hba_file=/etc/postgresql/pg_hba.conf -c wal_level=logical  <- gate 4 PASS
pg_isready:                  /var/run/postgresql:5432 - accepting connections  <- gate 8 PASS

Clean baseline for F+G+H:
  pg_publication count:      0
  pg_replication_slots:      0

Rollback artifacts intact:
  /tmp/compose.yaml.b2b-pre-backup    md5 b7bbe49cd6e113a450eba8f72bcdb61a  (still rollback-able)
  /tmp/pg_hba.conf.original           md5 3f1a04ebe46ac5af105962d6be6360c2
  /tmp/B2b_phase_e_verify.log         1946 bytes (Phase E subshell record preserved)

Downtime measured:           16s (subshell log timestamps; gate 7 PASS within 5-30s envelope)
```

All 9 gates PASS. No drift between subshell log and live state. No surprises.

---

## Observation correction: orchestrator was NOT inactive

PD's review noted: "`systemctl is-active ai-operator` returns `inactive`" and inferred orchestrator was down before Phase E. **This was a wrong-service-name read.**

Independent check on CiscoKid:

```
systemctl is-active ai-operator        ->  inactive (no such unit)
systemctl is-enabled ai-operator       ->  Failed to get unit file state for ai-operator.service: No such file or directory

ls /etc/systemd/system/ | grep orchestrator
  ->  orchestrator.service                            <- THIS is the actual unit
  ->  alexandra-telegram.service                      <- Telegram bot also exists

pgrep -af 'uvicorn|orchestrator'
  ->  PID 2688  /home/jes/control-plane/orchestrator/.venv/bin/python3 .venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
  ->  PID 833768 /home/jes/control-plane/orchestrator/.venv/bin/python3 /home/jes/control-plane/approval_gate.py
```

**The orchestrator IS running** (PID 2688 since long before Phase E). The Phase E recreate would have caused a brief connection error window for the orchestrator's PG-touching endpoints, and the Day 48 reconnect logic handled it -- which is exactly the design intent. The auto-reconnect resilience IS being exercised; PD's wrong-name check just gave a false negative.

**P6 lesson captured:** when checking service status, look up the actual systemd unit name via `systemctl list-units --type=service | grep -iE '<keyword>'` (or `ls /etc/systemd/system/`) before running `is-active`. Project-codename != systemd-unit-name. Service reference: `orchestrator.service` (NOT ai-operator.service). Update CHECKLIST and any spec drafts referring to `ai-operator` as a service unit name.

Not a B2b failure or concern. Just a documentation/naming correction logged in audit trail.

---

## Image-version observation (logged for ship report)

PD's image SHA observation is correct: CiscoKid is on `pgvector/pgvector:pg16` PG 16.11 (SHA `0a07c411...`); Beast is on the same tag at PG 16.13 (SHA `8ed31923...`). Different SHAs because the floating `:pg16` tag was pulled at different times.

For PG logical replication: subscriber-version >= publisher-version is the canonical safe direction (subscriber knows how to handle equal-or-older WAL formats; opposite direction risks subscriber not understanding newer WAL features). Beast 16.13 receiving from CiscoKid 16.11 is the correct direction. **This is fine.**

Flag for ship-report: noting the 16.11 vs 16.13 split in the closing audit so any future operator understands the image-tag drift consciously.

---

## Phase F directive (Pick 4 ratified: pg_dump + scp + psql)

Phase F is the schema bootstrap. Per Pick 4 ratification: standard idiom, produces tangible audit artifact (schema.sql + md5sum), uses SCP for the transfer (Rule 1 explicit carve-out for bulk SQL data, NOT via MCP).

### Step 1 -- pg_dump on CiscoKid

```bash
rm -f /tmp/controlplane_schema.sql
docker exec control-postgres pg_dump -U admin -d controlplane \
  --schema-only \
  --schema=public --schema=agent_os \
  --no-owner --no-privileges \
  > /tmp/controlplane_schema.sql 2>/tmp/pg_dump_stderr.log
echo "pg_dump-exit=$?"
md5sum /tmp/controlplane_schema.sql
wc -l -c /tmp/controlplane_schema.sql
```

**Capture for review:**
- pg_dump exit code (must be 0)
- /tmp/pg_dump_stderr.log content (should be empty or just version banner)
- md5sum + line count of /tmp/controlplane_schema.sql
- Schema sanity check: `grep -c '^CREATE SCHEMA' /tmp/controlplane_schema.sql` (expect 2 or more), `grep -c '^CREATE TABLE' /tmp/controlplane_schema.sql` (expect 13+ per Phase A's count of public+agent_os tables)
- **Mercury exclusion check:** `grep -c -i 'mercury' /tmp/controlplane_schema.sql` MUST equal 0. If non-zero -> abort Phase F, surface via paco_request_b2b_phase_f_failure.md.

### Step 2 -- Filter out vector-extension lines (Beast already has vector from B2a)

```bash
sed -e '/^CREATE EXTENSION.*\<vector\>/d' \
    -e '/^COMMENT ON EXTENSION.*\<vector\>/d' \
    /tmp/controlplane_schema.sql > /tmp/controlplane_schema_filtered.sql
echo "=== Lines filtered ==="
diff <(wc -l < /tmp/controlplane_schema.sql) <(wc -l < /tmp/controlplane_schema_filtered.sql) || echo "diff in line counts above"
md5sum /tmp/controlplane_schema_filtered.sql
wc -l -c /tmp/controlplane_schema_filtered.sql
grep -c -i 'extension.*vector' /tmp/controlplane_schema_filtered.sql || echo 'vector-extension-removed-OK'
```

**Capture for review:**
- Number of lines removed (expect 1-2 lines: CREATE EXTENSION vector + maybe a COMMENT)
- md5sum of filtered file
- Confirmation that vector extension references are gone from filtered file

### Step 3 -- SCP to Beast (Rule 1 carve-out)

```bash
scp /tmp/controlplane_schema_filtered.sql jes@192.168.1.152:/tmp/controlplane_schema_filtered.sql
echo "scp-exit=$?"
ssh jes@192.168.1.152 'md5sum /tmp/controlplane_schema_filtered.sql'
ssh jes@192.168.1.152 'wc -l -c /tmp/controlplane_schema_filtered.sql'
```

**Capture for review:**
- scp exit code (must be 0)
- Beast-side md5sum MUST equal CiscoKid-side md5sum (transfer parity gate)
- Beast-side line count MUST equal CiscoKid-side line count

### Step 4 -- Load schema on Beast

```bash
# Pre-load: capture Beast's CURRENT controlplane state (should be empty post-B2a init)
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT count(*) FROM information_schema.schemata WHERE schema_name IN ('"'"'public'"'"','"'"'agent_os'"'"','"'"'mercury'"'"');"'
# expect: 1 (only public, which is default; agent_os + mercury absent on Beast)

ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "\\dt public.*"' 2>&1 | head -5
# expect: 0 rows / no relations

# Load the schema (use ON_ERROR_STOP=on so any non-extension error halts immediately)
ssh jes@192.168.1.152 'cat /tmp/controlplane_schema_filtered.sql | docker exec -i control-postgres-beast psql -U admin -d controlplane -v ON_ERROR_STOP=on 2>&1 | tail -50'
echo "psql-exit=$?"
```

**Capture for review:**
- Pre-load schema count on Beast (expect 1 -- only public)
- Pre-load public table count on Beast (expect 0)
- psql exit code (must be 0)
- psql output tail (last 50 lines should show the final CREATE statements + no ERRORs)
- If any ERROR appears in psql output -> abort, surface via paco_request_b2b_phase_f_failure.md

### Step 5 -- Verify schemas on Beast

```bash
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "\\dn"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('"'"'pg_catalog'"'"','"'"'information_schema'"'"','"'"'pg_toast'"'"') ORDER BY schema_name;"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "\\dt public.*"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "\\dt agent_os.*"'
# count tables in each schema
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT schemaname, count(*) FROM pg_tables WHERE schemaname IN ('"'"'public'"'"','"'"'agent_os'"'"','"'"'mercury'"'"') GROUP BY schemaname ORDER BY schemaname;"'
```

**Capture for review:**
- Beast non-system schemas list (expect: public, agent_os; mercury MUST be absent)
- Public table count on Beast (must equal CiscoKid public table count)
- agent_os table count on Beast (must equal CiscoKid agent_os table count)
- All Beast tables empty (zero rows) -- this is schema-only, no data should be present yet

### Step 6 -- Reciprocal table-count parity from CiscoKid side (publisher reference)

```bash
docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT schemaname, count(*) FROM pg_tables WHERE schemaname IN ('public','agent_os','mercury') GROUP BY schemaname ORDER BY schemaname;"
```

**Capture for review:** publisher (CiscoKid) table counts per schema. Must match Beast's counts for public + agent_os.

### Step 7 -- Cleanup intermediate artifacts

```bash
# Keep the schema files until Phase G+H are confirmed; they're tiny.
# Just confirm the intermediate stderr log doesn't have surprises.
cat /tmp/pg_dump_stderr.log
```

Do NOT delete `/tmp/controlplane_schema.sql` or `/tmp/controlplane_schema_filtered.sql` yet. Phase I cleanup will remove them after the 12-gate acceptance passes. Keeping them through G+H means we can re-bootstrap quickly if subscription creation hits an issue.

---

## Phase F acceptance gate (PD must verify all PASS in review)

1. **pg_dump succeeded:** exit 0, stderr log empty or version banner only
2. **Schema dump contents reasonable:** >= 2 CREATE SCHEMA statements (public + agent_os); >= 13 CREATE TABLE statements (per Phase A's table-count baseline of public+agent_os tables)
3. **Mercury exclusion verified:** `grep -c -i mercury /tmp/controlplane_schema.sql` == 0
4. **Vector-extension filter applied:** filtered file has no `CREATE EXTENSION vector` or `COMMENT ON EXTENSION vector` lines
5. **SCP transfer parity:** Beast-side md5sum == CiscoKid-side md5sum for `controlplane_schema_filtered.sql`
6. **psql load on Beast succeeded:** exit 0; no ERROR lines in output (only NOTICE/INFO are acceptable)
7. **Beast schemas correct:** `\dn` shows public + agent_os; mercury absent
8. **Beast table-count parity:** Beast public table count == CiscoKid public table count; Beast agent_os table count == CiscoKid agent_os table count
9. **Beast tables empty:** every table in public + agent_os has 0 rows on Beast (schema-only, data sync is Phase H job)

Then pause for Paco fidelity confirmation in `paco_review_b2b_phase_f_schema_bootstrap.md` per protocol. **No Phase G** (CREATE PUBLICATION on CiscoKid) until approved.

---

## If any gate fails

Phase F is non-irreversible if all you've done is load a schema into an empty DB. Recovery options:

- **Mercury contamination found in dump (gate 3 fail):** something is wrong with the `--schema=public --schema=agent_os` filter; abort, do NOT scp; rerun pg_dump with stricter filter. Likely scenario: `mercury` schema name appears as a string in a comment or a function body; manual inspection needed.
- **SCP parity fail (gate 5):** transient network issue; retry SCP; if persistent, drop to ssh `cat | tee` pattern.
- **psql load fail (gate 6):** capture full psql output; rollback Beast's controlplane DB to empty state via `DROP SCHEMA public CASCADE; DROP SCHEMA agent_os CASCADE; CREATE SCHEMA public;`; surface via paco_request_b2b_phase_f_failure.md with full output.
- **Schema/table count mismatch (gates 7-9):** likely a partial load; full DROP+rebuild as above; surface and diagnose.

Full rollback to pre-Phase-F (empty Beast DB): `DROP SCHEMA public CASCADE; DROP SCHEMA agent_os CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO PUBLIC;`. Beast remains at B2a state.

---

## Standing rules in effect

- **Rule 1 (MCP fabric is for control, not bulk data):** Step 3 (SCP) is the explicit ratified carve-out for bulk SQL transport between hosts. The schema dump is NOT moved via MCP -- it's a single SCP call. Step 4 uses `ssh ... | docker exec -i ...` with stdin redirect; this is shell-piping local SCP'd content into psql, NOT bulk MCP traffic. Compliant.
- **CLAUDE.md "Spec or no action":** the vector-extension filter (Step 2) is explicitly authorized in this directive. Beast already has vector from B2a init; replaying CREATE EXTENSION vector would error. The filter handles this cleanly. Any further deviation -> paco_request_b2b_*.md.
- **CLAUDE.md "Docker bypasses UFW":** Phase F does not touch ports/UFW; the UFW rule from Phase D is in place but inactive (logical replication uses the publisher endpoint at 192.168.1.10:5432, which Phase H will exercise). Phase F's psql-to-Beast goes through Beast's localhost-bound 127.0.0.1:5432 via `docker exec -i`, no network hop.
- **Correspondence protocol:** this is paco_response #5 in B2b chain. PD's review will be #5 of 8 planned (paco_review #5).
- **Canon location:** all artifacts on CiscoKid + Beast filesystems for now; no git-tracked file changes in this phase.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2b_phase_e_confirm_phase_f_go.md`

-- Paco
