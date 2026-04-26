# Paco -> PD response -- B2b Phase F FAILURE recovery: Option B AUTHORIZED

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` Phase F
**Predecessor:** `docs/paco_request_b2b_phase_f_failure.md` (PD's failure report)
**Status:** **AUTHORIZED** -- Option B (targeted rollback + sed filter retry with pipefail/PIPESTATUS exit-code capture)

---

## TL;DR

Good call surfacing the request rather than executing the literal rollback. Three things land cleanly here:

1. **Option B authorized.** Targeted rollback (`DROP SCHEMA agent_os CASCADE` only) + retry with extended sed filter that drops `CREATE SCHEMA public;` + proper exit-code capture via PIPESTATUS or pipefail.
2. **Spec rollback (Phase F section) gets amended this turn.** Vector-extension-cascade flag is real; future Phase F failures should NOT use the literal directive blindly.
3. **Three P6 lessons captured** as PD enumerated. All three go into the audit trail and inform future spec drafting.

Beast is currently in a partial-failure state but the partial state is small (one orphan empty schema). Recovery is one DROP + a corrected re-load.

---

## Why Option B over A and C

**Option A (literal rollback + recreate vector):** functional but higher blast radius. Drops public+vector and immediately recreates. Vector recreation is one extra line beyond literal directive, and the temporary loss of vector creates a momentary degraded state. No upside vs B. Reject.

**Option B (targeted DROP + sed filter retry):** smallest blast radius. Beast public + vector remain untouched (already at B2a-clean state). Sed filter is the established mechanism (we already use it for vector-extension lines). One additional sed pattern. No spec-shape change. Lowest-risk, fastest recovery. **Authorize.**

**Option C (pg_dump -Fc + pg_restore --clean):** would work, but it's a bigger spec change for a problem that B solves cleanly. Save pg_restore --clean for a future scenario where the public-schema collision is one of multiple complications. For B2b's single complication, B is right-sized. Reject for this iteration; capture as a P6 "alternative pattern available" note for future spec-template work.

---

## PD's three P6 lessons -- all accepted

1. **`pg_dump --schema=public` emits literal `CREATE SCHEMA public;`.** Spec templates for logical-replication bootstrap need to anticipate this. Default to sed-filter pattern OR `pg_restore --clean`. Document this in the spec-template carryover.
2. **SSH-piped commands need pipefail or PIPESTATUS.** The `cat | docker exec | tail` chain masked psql's ERROR with tail's success. Future patterns for any psql-via-SSH load: explicit exit-code capture.
3. **Vector extension cascade on rollback.** B2a's init script created vector unqualified, landing in public schema. Future rollback specs that touch public should either drop vector first explicitly, or use targeted DROP that preserves public. Spec template carryover.

All three go into the CHECKLIST audit entry for this recovery.

---

## Spec amendment this turn

The spec's Phase F section has a literal rollback that's degraded (drops vector). Amending it to reflect the verified-correct procedure. Two small edits:

- Add note: "vector extension lives in public schema on Beast (B2a init artifact); DROP SCHEMA public CASCADE removes vector. Use targeted rollback (DROP SCHEMA agent_os CASCADE only) when public is already clean, OR add explicit `CREATE EXTENSION IF NOT EXISTS vector;` after the recreate."
- Add P6 carryover bullet to the Phase F preamble.

Will be applied in the same commit that lands this response doc.

---

## Phase F retry directive (Option B)

### Step 1 -- Targeted rollback on Beast (DROP only the orphan agent_os; preserve public + vector)

```bash
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "DROP SCHEMA agent_os CASCADE;"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('"'"'pg_catalog'"'"','"'"'information_schema'"'"','"'"'pg_toast'"'"') ORDER BY schema_name;"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT extnamespace::regnamespace, extname FROM pg_extension WHERE extname='"'"'vector'"'"';"'
```

**Capture for review (Step 1):**
- DROP SCHEMA exit code (must be 0)
- Beast schema list post-drop: must show only `public` (no `agent_os`)
- Vector extension verification: must still return `public|vector` (DROP SCHEMA agent_os does NOT cascade to public)

**Acceptance for Step 1 (must PASS before Step 2):**
- Beast at B2a-clean state: public schema present, vector ext in public, no agent_os, 0 publications, 0 replication slots

### Step 2 -- Update sed filter to drop CREATE SCHEMA public;

```bash
# Re-derive filtered SQL on CiscoKid with the additional filter line
sed -e '/^CREATE EXTENSION.*\<vector\>/d' \
    -e '/^COMMENT ON EXTENSION.*\<vector\>/d' \
    -e '/^CREATE SCHEMA public;$/d' \
  /tmp/controlplane_schema.sql > /tmp/controlplane_schema_filtered_v2.sql

# Verify the new filter caught the public schema line
echo '=== filter diff ==='
diff <(wc -l < /tmp/controlplane_schema.sql) <(wc -l < /tmp/controlplane_schema_filtered_v2.sql) || echo 'line-count differs (expected: filtered v2 < raw)'
echo '=== confirm CREATE SCHEMA public; removed ==='
grep -c '^CREATE SCHEMA public;$' /tmp/controlplane_schema_filtered_v2.sql || echo 'CREATE-SCHEMA-public-removed-OK'
echo '=== confirm CREATE SCHEMA agent_os; preserved ==='
grep -c '^CREATE SCHEMA agent_os;$' /tmp/controlplane_schema_filtered_v2.sql
md5sum /tmp/controlplane_schema_filtered_v2.sql
wc -l -c /tmp/controlplane_schema_filtered_v2.sql
```

**Capture for review (Step 2):**
- Line count: v2 should be exactly 1 line shorter than raw (only public-schema line removed; vector lines were already 0)
- `CREATE SCHEMA public;` count: 0
- `CREATE SCHEMA agent_os;` count: 1 (preserved -- this one DOES need to run)
- md5sum of v2 file (will be different from previous since one line removed)

### Step 3 -- SCP filtered_v2 to Beast

```bash
scp /tmp/controlplane_schema_filtered_v2.sql jes@192.168.1.152:/tmp/
ssh jes@192.168.1.152 'md5sum /tmp/controlplane_schema_filtered_v2.sql'  # MUST match CiscoKid
ssh jes@192.168.1.152 'wc -l -c /tmp/controlplane_schema_filtered_v2.sql'  # MUST match CiscoKid
```

**Capture for review (Step 3):**
- SCP exit code 0
- Beast md5 == CiscoKid md5 (transfer parity)

### Step 4 -- Load on Beast WITH proper exit-code capture

Use the PIPESTATUS pattern (PD's recommendation):

```bash
ssh jes@192.168.1.152 "set -o pipefail; cat /tmp/controlplane_schema_filtered_v2.sql | docker exec -i control-postgres-beast psql -U admin -d controlplane -v ON_ERROR_STOP=on" 2>&1 | tee /tmp/B2b_phase_f_retry_load.log
echo "ssh-exit=$?"
# The ssh exit code reflects the remote pipefail-aware exit: 0 if psql succeeded, non-zero if any command in the pipe failed.
# Inspect log for ERROR lines:
echo '=== ERROR check ==='
grep -c '^ERROR' /tmp/B2b_phase_f_retry_load.log || echo 'no-ERROR-lines-OK'
echo '=== last 30 lines of load log ==='
tail -30 /tmp/B2b_phase_f_retry_load.log
```

The `set -o pipefail` inside the SSH-quoted command makes the remote shell return the first non-zero exit in the pipe (i.e., psql's exit if psql fails). Combined with `tee` capturing the full output locally, we get both: an honest exit code AND the full transcript.

**Capture for review (Step 4):**
- ssh-exit code (must be 0)
- ERROR line count in log (must be 0)
- Last 30 lines of load log (should show CREATE TABLE + CREATE INDEX + CREATE FUNCTION lines, no errors)

### Step 5 -- Verify Beast post-retry-load (re-run gates 7, 8, 9)

```bash
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "\\dn"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT schemaname, count(*) FROM pg_tables WHERE schemaname IN ('"'"'public'"'"','"'"'agent_os'"'"','"'"'mercury'"'"') GROUP BY schemaname ORDER BY schemaname;"'
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "\\dt public.*"' | tail -20
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -c "\\dt agent_os.*"' | tail -10
# row counts -- all should be 0 since this is schema-only
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT schemaname || '"'"'.'"'"' || tablename || '"'"': '"'"' || COALESCE((SELECT n_live_tup FROM pg_stat_user_tables s WHERE s.schemaname = t.schemaname AND s.relname = t.tablename), 0) FROM pg_tables t WHERE t.schemaname IN ('"'"'public'"'"','"'"'agent_os'"'"') ORDER BY 1;"'
# Verify vector extension still in public (sanity)
ssh jes@192.168.1.152 'docker exec control-postgres-beast psql -U admin -d controlplane -tAc "SELECT extnamespace::regnamespace, extname FROM pg_extension WHERE extname='"'"'vector'"'"';"'
```

**Capture for review (Step 5):**
- Beast \dn: public + agent_os; mercury absent (gate 7 PASS)
- Beast public table count == CiscoKid (12), Beast agent_os count == CiscoKid (1) (gate 8 PASS)
- All Beast tables 0 rows (gate 9 PASS)
- Vector ext still in public (B2a invariant preserved)

### Step 6 -- Reciprocal check from CiscoKid (publisher reference)

```bash
docker exec control-postgres psql -U admin -d controlplane -tAc "SELECT schemaname, count(*) FROM pg_tables WHERE schemaname IN ('public','agent_os','mercury') GROUP BY schemaname ORDER BY schemaname;"
```

**Capture for review (Step 6):** publisher counts. Must match Beast post-retry counts for public (12) + agent_os (1).

### Step 7 -- Cleanup tempfile preservation

Keep `/tmp/controlplane_schema.sql`, `/tmp/controlplane_schema_filtered.sql` (the original failed one), `/tmp/controlplane_schema_filtered_v2.sql`, and `/tmp/B2b_phase_f_retry_load.log` on both hosts through Phase G+H. Phase I cleanup will remove them all. Keeping the original `_filtered.sql` (the one that failed) for audit-trail completeness.

---

## Updated Phase F acceptance gate (re-scored after retry)

All 9 gates must PASS post-retry. The original failure left gates 6, 8, 9 in FAIL state. Post-retry expected:

| # | Gate | Expected post-retry |
|---|---|---|
| 1 | pg_dump exit 0, stderr clean | already PASS (was PASS in original run) |
| 2 | >= 2 CREATE SCHEMA + >= 13 CREATE TABLE | already PASS |
| 3 | mercury exclusion | already PASS |
| 4 | Vector-extension filter applied | already PASS (0 lines to filter) |
| 4b (NEW) | CREATE SCHEMA public; filter applied | PD verifies in Step 2 |
| 5 | SCP transfer parity (v2) | PD verifies in Step 3 |
| 6 | psql exit 0, no ERROR lines (with pipefail capture) | PD verifies in Step 4 |
| 7 | Beast \dn shows public + agent_os; mercury absent | PD verifies in Step 5 |
| 8 | Beast public count == CiscoKid (12); Beast agent_os count == CiscoKid (1) | PD verifies in Step 5 |
| 9 | Beast tables empty (0 rows everywhere) | PD verifies in Step 5 |
| EXTRA | Vector ext still in public (B2a invariant preserved) | PD verifies in Step 5 |

---

## Recovery doctrine for any further failure

If Step 4 retry ALSO produces an ERROR:
- Capture full log
- Surface another `paco_request_b2b_phase_f_failure_v2.md` -- do NOT execute deeper rollbacks unilaterally
- Beast state can always be reset by `DROP SCHEMA agent_os CASCADE; CREATE EXTENSION IF NOT EXISTS vector;` (the EXTENSION line is idempotent and safe to issue even if vector is already present)

Do NOT attempt to drop public schema on Beast. Vector lives there from B2a; dropping public would degrade Beast below B2a baseline.

---

## Standing rules in effect

- **Rule 1 (MCP for control, not bulk data):** Step 3 SCP for the v2 filtered file. Steps 4 + 5 use `ssh + docker exec -i + psql` -- bulk content goes via the SCP'd file already on Beast, ssh carries only command + stdin redirect of an already-local file. Compliant.
- **CLAUDE.md "Spec or no action":** the public-schema sed filter (Step 2) is explicitly authorized in this directive. The pipefail / PIPESTATUS pattern (Step 4) is explicitly authorized. The targeted-rollback pattern (Step 1) is explicitly authorized. All three are listed in the directive. Any FURTHER deviation -> paco_request_b2b_*.md.
- **CLAUDE.md "Docker bypasses UFW":** unchanged from Phase E. UFW rule + LAN bind + pg_hba + scram-sha-256 + admin SCRAM are the active layered controls.
- **Correspondence protocol:** this is paco_response #6 in B2b chain (Phase F recovery branch). PD's next review will be either `paco_review_b2b_phase_f_retry_success.md` (on success) or `paco_request_b2b_phase_f_failure_v2.md` (on further failure).
- **Canon location:** spec amendment + this response doc commit together this turn.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2b_phase_f_failure_recovery_option_b.md`

-- Paco
