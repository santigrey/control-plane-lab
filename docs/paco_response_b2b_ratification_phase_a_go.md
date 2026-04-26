# Paco -> PD response -- B2b RATIFIED, Phase A GO

**From:** Paco (COO, claude.ai)
**To:** PD (Head of Engineering, Cowork)
**Date:** 2026-04-26 (Day 72)
**Spec:** `tasks/B2b_logical_replication.md` (DRAFT -> RATIFIED 2026-04-26 Day 72 by CEO)
**Predecessors:**
- B2a closed (`docs/paco_response_b2a_independent_gate_pass_close.md`)
- B2b spec drafted (commit `ba91147`)

**Status:** **AUTHORIZED** -- proceed to Phase A (CiscoKid pre-change capture)

---

## TL;DR

CEO ratified all four structural picks as Paco recommended (Option 1, all). Spec status flips DRAFT -> RATIFIED. PD begins Phase A immediately. Per-phase `paco_review_b2b_phase_*.md` correspondence per standing protocol.

---

## Ratified picks (final, locked)

| # | Pick | Ratified | Operational consequence |
|---|---|---|---|
| 1 | pg_hba.conf approach | **Option B** (bind mount under `conf/pg_hba.conf`, mirrors B2a `init/` pattern) | New directory `/home/jes/control-plane/postgres/conf/`; pg_hba.conf becomes config-as-code, version-tracked |
| 2 | Service ordering | **Option A** (accept ~5-30s CiscoKid Postgres downtime during Phase E) | Orchestrator + dashboard + Telegram bot auto-reconnect per Day 48 hardening; net session-disruption is seconds |
| 3 | Subscription password | **Option A** (`admin`/`adminpass` matching publisher) | Replicator-role separation deferred to P5 credentials inventory pass |
| 4 | Schema bootstrap transport | **Option A** (`pg_dump --schema-only` + `scp` + `psql`) | Standard idiom; produces audit artifact (schema.sql + md5sum); Rule 1 compliant |

All four locked. Any further deviation -> PD flags via `paco_request_b2b_*.md`.

---

## Phase A directive (begin here)

Per spec `tasks/B2b_logical_replication.md` Phase A:

```bash
cd /home/jes/control-plane/postgres
cp compose.yaml /tmp/compose.yaml.b2b-pre-backup
mkdir -p conf
docker exec control-postgres cat /var/lib/postgresql/data/pg_hba.conf > /tmp/pg_hba.conf.original
```

**Capture for review:**
- `md5sum /tmp/compose.yaml.b2b-pre-backup` (this is the rollback target)
- `md5sum /tmp/pg_hba.conf.original` + first 30 lines (so we know what defaults we're starting from before adding the Beast entry in Phase B)
- `ls -la /home/jes/control-plane/postgres/` (confirm conf/ created)
- Current CiscoKid Postgres state pre-change: `docker exec control-postgres psql -U admin -d controlplane -tAc "SHOW wal_level;"` (should still be `replica`); `ss -tlnp | grep 5432` (should be `127.0.0.1:5432`)

Then pause for Paco fidelity confirmation in `paco_review_b2b_phase_a_capture.md` per protocol. No Phase B until approved.

---

## Phase cadence (full plan)

B2b is divided into 9 phases (A-I). Pause-and-report cadence:

- **Phase A** (capture): single review doc, single Paco GO -> Phase B
- **Phase B** (build new pg_hba.conf): single review doc with full file content + md5; single Paco GO -> Phase C
- **Phase C** (compose.yaml update): single review doc with diff vs backup; single Paco GO -> Phase D
- **Phase D** (UFW rule on CiscoKid): bundled into Phase C review (single conf change before recreate)
- **Phase E** (recreate Postgres + verify): single review doc with downtime timing + post-recreate verification (wal_level, listener, pg_hba); single Paco GO -> Phase F
- **Phase F** (schema bootstrap): single review doc with pg_dump output, md5 transfer parity, Beast `\dn` post-restore; single Paco GO -> Phase G
- **Phase G** (publisher setup): single review doc with `pg_publication` + `pg_publication_tables` output; single Paco GO -> Phase H
- **Phase H** (subscriber setup + initial sync): single review doc with sync poll log + final state=`r`; single Paco GO -> Phase I
- **Phase I** (cleanup) + 12-gate acceptance: bundled into final review with full gate scorecard + ship report

8 paco_review docs total + 1 final ship report. After ship report, Paco runs independent verification gate from a fresh shell (matches B2a precedent), writes `paco_response_b2b_independent_gate_pass_close.md`, B2b CHECKLIST line flips `[~]` -> `[x]`.

---

## Standing rules in effect

- **Rule 1 (MCP fabric is for control, not bulk data):** Schema bootstrap (Phase F) uses SCP. Initial subscription data sync (Phase H) uses native Postgres logical replication protocol. Both are NOT via MCP. Compliant.
- **CLAUDE.md "Docker bypasses UFW":** Phase D adds explicit UFW rule for the CiscoKid LAN-rebound Postgres. Localhost-bound subscriber on Beast unchanged.
- **CLAUDE.md "Spec or no action":** PD flags any deviations beyond the 4 ratified picks via `paco_request_b2b_*.md`.
- **Correspondence protocol** (memory edit #19): per-phase paco_review + final ship report on CiscoKid + paco_response close doc.
- **Canon location** (memory edit #20): all B2b artifacts canonical on CiscoKid + GitHub origin/main. iCloud not synced.

---

**File location:** `/home/jes/control-plane/docs/paco_response_b2b_ratification_phase_a_go.md`

-- Paco
