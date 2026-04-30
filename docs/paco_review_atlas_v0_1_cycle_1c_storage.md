# paco_review_atlas_v0_1_cycle_1c_storage

**Spec:** Atlas v0.1 -- Cycle 1C Garage S3 client + bucket adoption (`tasks/atlas_v0_1.md` v3 section 8.1C)
**Status:** Cycle 1C **CLOSED 5/5 PASS**.
**Date:** 2026-04-30 (Day 75)
**Author:** PD
**Predecessor docs:**
- `paco_review_atlas_v0_1_cycle_1b_db_layer.md` (commit `a460dfa`)
- `paco_response_atlas_v0_1_cycle_1b_confirm_1c_go.md` (Cycle 1C directive under 5th standing rule)

---

## 0. Verified live (2026-04-30 Day 75)

**Per 5th standing rule** (`feedback_paco_pre_directive_verification.md`). All deployed-state names referenced in this review trace back to a row in this table. Verifications run live this turn from `beast` SSH alias.

| Category | Command | Output |
|----------|---------|--------|
| Beast anchors PRE/POST | `docker inspect ...` | bit-identical: B2b `2026-04-27T00:13:57.800746541Z` healthy 0; Garage `2026-04-27T05:39:58.168067641Z` healthy 0 |
| Garage cluster status | `docker exec control-garage-beast /garage status` | 1 HEALTHY NODE `b90a0fe8e46f883c` at 127.0.0.1:3901, 4.0 TB capacity, 4.4 TB avail (91.7%), v2.1.0 |
| atlas-state bucket pre-test | `/garage bucket info atlas-state` | 0 B / 0 objects, RWO `GK21a7963c241ac918bd68c595` (root key, public ID OK to log) |
| atlas-state bucket post-test | `/garage bucket info atlas-state` (after roundtrip) | 0 B / 0 objects (cleanup verified) |
| .s3-creds file | `ls -la /home/jes/garage-beast/.s3-creds` | mode 600 owner jes:jes 229 bytes |
| .s3-creds AWS_ACCESS_KEY_ID prefix | `grep ... | sed 's/=\(.\{4\}\).*/...'/` | `GK21...` (Garage convention) |
| .s3-creds AWS_ENDPOINT_URL | `grep ...` | `http://192.168.1.152:3900` (S3 LAN, path-style) |
| .s3-creds AWS_DEFAULT_REGION | `grep ...` | `garage` |
| .s3-creds AWS_SECRET_ACCESS_KEY | `awk -F= '{print length}'` | 64 chars (REDACTED -- value never displayed) |
| pytest result | `pytest tests/ -v` | 8 passed in 0.54s (3 from 1A+1B + 4 new + 1 existing test_smoke) |
| Atlas commit on santigrey/atlas | `git log --oneline -1` | `81de0b2 feat: Cycle 1C Garage S3 client + bucket adoption` |
| Push verified | `git push` output | `42e41b7..81de0b2 main -> main` |
| Garage admin endpoint NOT used | n/a | boto3 client only uses `:3900` (S3 LAN); `:3903` admin port untouched |
| B2b subscription | n/a | untouched (Cycle 1C does not interact with Postgres replication) |

---

## 1. TL;DR

`atlas.storage` module landed on Beast: boto3 wrapper (`client.py`) + credential resolution helper with env > file precedence (`creds.py`) + public API (`__init__.py` exposing 3 bucket constants, `S3Storage`, `get_storage`, `S3Creds`, `get_s3_creds`). Module connects to Garage S3 LAN endpoint `http://192.168.1.152:3900` with path-style addressing per Garage compat requirement. Adopts 3 pre-allocated buckets (`atlas-state`, `backups`, `artifacts`) -- does NOT create. Key prefix conventions documented. 4 new pytest tests pass; total 8/8 (Cycles 1A+1B+1C combined). atlas-state bucket post-test: 0 B / 0 objects (cleanup verified).

Atlas commit on `santigrey/atlas`: **`81de0b2`** (`feat: Cycle 1C Garage S3 client + bucket adoption`). 7 files added (3 module + 4 tests).

B2b + Garage anchors bit-identical pre/post Cycle 1C. Garage cluster status unchanged (`b90a0fe8e46f883c` healthy, 4.0 TB capacity, 4.4 TB avail). pgvector + Postgres untouched.

Second clean PD-side application of 5th standing rule -- Verified live block at section 0 traces all 14 deployed-state references against running infrastructure. No spec-vs-live mismatches.

0 PD-side adaptations from Paco's sketches this cycle -- the sketches landed verbatim apart from minor docstring polish.

---

## 2. Cycle 1C 5-gate scorecard

| Gate | Description | Status | Evidence |
|------|-------------|--------|----------|
| 1 | atlas.storage module imports cleanly | PASS | `from atlas.storage import S3Storage, BUCKET_ATLAS_STATE, ...` returns no errors; pip install -e ".[dev]" no-op (deps already in venv) |
| 2 | list_buckets returns set including all 3 expected | PASS | `test_list_buckets_includes_expected` PASSED -- atlas-state, backups, artifacts all in returned set |
| 3 | Round-trip on atlas-state: put + head + get + delete + list-cleanup all succeed; atlas-state ends empty | PASS | `test_put_head_get_delete_roundtrip` PASSED -- ContentLength match / body match / list returns [] / `/garage bucket info` post-test confirms 0 B 0 objects |
| 4 | Cred resolution: env > file precedence verified | PASS | `test_file_resolution_default_path` PASSED (canonical file reachable, key starts with GK) + `test_env_override_takes_precedence` PASSED (env GKenvvalue overrides file GKfilevalue while other vars fall through to file) |
| 5 | B2b + Garage anchors bit-identical pre/post | PASS | `diff /tmp/atlas_1c_anchors_pre.txt /tmp/atlas_1c_anchors_post.txt` -> ANCHORS-BIT-IDENTICAL |

**5/5 PASS.**

Plus standing gates:
- 8 pytest tests passing total (4 prior + 4 new): PASS
- secret-grep on staged diff: clean (no AKIA / sk- / real GK keys in source or tests; test fakes `GKenvvalue` + `GKfilevalue` correctly excluded)
- B2b subscription `controlplane_sub` untouched (Cycle 1C doesn't touch Postgres at all): PASS
- atlas-state bucket post-test: 0 objects (no leftover test artifacts): PASS
- Garage admin endpoint `:3903` untouched (boto3 only uses S3 LAN `:3900`): PASS
- No new Garage access keys created (using existing root key `GK21...` per spec; per-Atlas key is v0.2 P5 #9): PASS

---

## 3. Implementation notes

**0 deviations from Paco's sketches.** The creds.py + client.py + __init__.py landed verbatim apart from minor docstring polish. No DSN/URL mismatches surfaced (unlike Cycle 1B where the sketch's DSN needed user= explicit).

**Path-style addressing** confirmed in client.py via `BotoConfig(s3={"addressing_style": "path"})`. Garage requires this; virtual-hosted-style would require DNS bucket-host setup we haven't done.

**No new Garage access key created.** v0.1 adopts the existing root key `GK21a7963c241ac918bd68c595` (RWO on all 3 buckets) per spec. Per-Atlas limited-scope key creation is v0.2 P5 #9.

**Secret hygiene:** `AWS_SECRET_ACCESS_KEY` value never appears in committed code, test files, paco_review, commit messages, or any artifact. The 64-char value lives only in `/home/jes/garage-beast/.s3-creds` mode 600 on Beast filesystem. AWS_ACCESS_KEY_ID is treated as a public ID (Garage convention) and OK to log. Test fakes (`GKenvvalue`, `GKfilevalue`) are clearly synthetic and not real keys.

---

## 4. Test results

```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/jes/atlas
configfile: pyproject.toml
plugins: asyncio-1.3.0, anyio-4.13.0
collecting ... collected 8 items

tests/db/test_cross_schema_read.py::test_read_public_agent_tasks PASSED
tests/db/test_db_smoke.py::test_connect_and_select_one PASSED
tests/db/test_migration_smoke.py::test_migrations_idempotent PASSED
tests/storage/test_creds_resolution.py::test_file_resolution_default_path PASSED
tests/storage/test_creds_resolution.py::test_env_override_takes_precedence PASSED
tests/storage/test_storage_roundtrip.py::test_put_head_get_delete_roundtrip PASSED
tests/storage/test_storage_smoke.py::test_list_buckets_includes_expected PASSED
tests/test_smoke.py::test_version_string PASSED

============================== 8 passed in 0.54s ===============================
```

8/8 pass. 0 failures. 0.54s execution.

---

## 5. Atlas package state on Beast (post-Cycle-1C)

```
/home/jes/atlas/
├── .git/                                          (commit 81de0b2)
├── .gitignore
├── .venv/                                         (Python 3.11.15)
├── README.md
├── pyproject.toml
├── src/atlas/
│   ├── __init__.py
│   ├── __main__.py
│   ├── db/                                         (Cycle 1B)
│   │   ├── __init__.py
│   │   ├── pool.py
│   │   ├── migrate.py
│   │   └── migrations/ (5 SQL files)
│   └── storage/                                    <-- NEW Cycle 1C
│       ├── __init__.py    (996 bytes, public API + key prefix docs)
│       ├── creds.py       (2196 bytes, env > file resolution)
│       └── client.py      (3123 bytes, boto3 path-style wrapper)
└── tests/
    ├── __init__.py
    ├── test_smoke.py
    ├── db/                                         (Cycle 1B)
    │   ├── __init__.py
    │   ├── test_db_smoke.py
    │   ├── test_migration_smoke.py
    │   └── test_cross_schema_read.py
    └── storage/                                    <-- NEW Cycle 1C
        ├── __init__.py                            (empty)
        ├── test_storage_smoke.py                  (414 bytes)
        ├── test_storage_roundtrip.py              (782 bytes)
        └── test_creds_resolution.py               (1263 bytes)
```

7 new files (3 module + 4 test). 0 modified files.

---

## 6. Atlas commit on santigrey/atlas

**Hash:** `81de0b2`
**Subject:** `feat: Cycle 1C Garage S3 client + bucket adoption`
**Push:** `42e41b7..81de0b2 main -> main`

Commit body cites: atlas.storage module purpose / boto3 path-style addressing for Garage / env > file cred precedence / 3-bucket adoption / key prefix conventions / 4 new test results / atlas-state cleanup verified / Postgres + Garage cluster untouched / Beast anchors bit-identical.

Secret-grep on staged diff: clean. No `AKIA`, no `sk-`, no real `GK[a-zA-Z0-9]{16,}` keys (test fakes `GKenvvalue` + `GKfilevalue` correctly excluded by literal match).

---

## 7. Beast anchor preservation

```
PRE  /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
PRE  /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
POST /control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
POST /control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

`diff` output: **ANCHORS-BIT-IDENTICAL**.

boto3 calls (put/head/get/delete/list) are S3 protocol traffic against the Garage container; the container itself is not restarted. Container `StartedAt` unchanged. ~73+ hours since establishment Day 71, holding through H1 ship + Cycle 1A + 1B + 1C.

---

## 8. Garage cluster state

Unchanged pre/post Cycle 1C:
- 1 HEALTHY NODE `b90a0fe8e46f883c` at 127.0.0.1:3901
- Capacity 4.0 TB, 4.4 TB available (91.7%)
- Garage v2.1.0
- Bucket `atlas-state`: 0 B / 0 objects (test cleaned up after itself)
- Bucket `backups`: not modified this cycle
- Bucket `artifacts`: not modified this cycle

---

## 9. B2b subscription untouched

Cycle 1C did not interact with Postgres at all (atlas.storage is S3-only). `controlplane_sub` subscription continues replicating CK -> Beast unchanged. No `pg_subscription` / `pg_publication` operations performed by Atlas this cycle.

---

## 10. Cross-references

**Predecessor doc chain:**
- `paco_review_atlas_v0_1_cycle_1b_db_layer.md` (Cycle 1B close, commit `a460dfa`)
- `paco_response_atlas_v0_1_cycle_1b_confirm_1c_go.md` (Cycle 1C directive)
- (this) `paco_review_atlas_v0_1_cycle_1c_storage.md`

**Standing rules invoked:**
- 5th standing rule (`feedback_paco_pre_directive_verification.md`) -- this review's section 0 Verified live block satisfies the rule (14 verifications)
- 5-guardrail rule -- not invoked this cycle (Paco's sketches landed verbatim, no DSN/URL adaptations needed)
- B2b + Garage anchor preservation invariant: holding
- Bidirectional one-liner format spec: this cycle's paired handoff follows it

---

## 11. Status

**CYCLE 1C CLOSED 5/5 PASS.** atlas.storage module shipped; 3 buckets adopted; 4 new tests passing (8 total); first commit on `santigrey/atlas` advanced to `81de0b2`. Substrate untouched.

This Cycle 1C close-out commit on `santigrey/control-plane-lab` folds: this paco_review + SESSION.md Day 75 Cycle 1C close section append + paco_session_anchor.md update (Cycle 1C CLOSED, Cycle 1D NEXT, P6=20, standing rules=5) + CHECKLIST.md audit entry.

Ready for Cycle 1D (Goliath inference RPC) per spec v3.

-- PD
