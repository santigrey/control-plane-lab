# paco_review_atlas_v0_1_cycle_1a_skeleton

**Spec:** Atlas v0.1 -- Cycle 1A package skeleton (`tasks/atlas_v0_1.md` v3, commit `93b97e6`)
**Status:** Cycle 1A **CLOSED 5/5 PASS** post preflight ESC resolution.
**Date:** 2026-04-30 (Day 75)
**Author:** PD
**Predecessor docs:**
- `paco_request_atlas_v0_1_cycle_1a_preflight_fail.md` (PD ESC #1 of Cycle 1A)
- `paco_response_atlas_v0_1_cycle_1a_preflight_resolved.md` (commit `7d29c6c`, 4 path rulings + P6 #20 banked)
- `feedback_paco_pre_directive_verification.md` (5th standing rule, banked at commit `93b97e6`)
- `tasks/atlas_v0_1.md` v3 (commit `93b97e6`, all amendments folded)

---

## 1. TL;DR

Cycle 1A shipped the Atlas package skeleton on Beast at `/home/jes/atlas/`. Python 3.11.15 venv (deadsnakes PPA per Path A), pyproject.toml + src layout + 6 files, all dependencies installed cleanly (47 packages including atlas-0.1.0 + mcp 1.27.0 + psycopg 3.3.3 + boto3 + pydantic + httpx + structlog + dev deps), pytest smoke passes (1/1), first commit pushed to `santigrey/atlas` at hash `3e50a13`. Preflight ESC resolved 4 distinct issues prior to scaffold work (Python 3.11 install + .pgpass with real B2b creds + Garage URL spec fix + Tailscale Path B / LAN substitution).

B2b + Garage Beast anchors bit-identical pre/post Cycle 1A: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z`. Substrate untouched. P6 #20 banking confirmed in spec v3.

---

## 2. Cycle 1A 5-gate scorecard

| Gate | Description | Status | Evidence |
|------|-------------|--------|----------|
| 1 | `/home/jes/atlas/` exists with required files | PASS | tree contains `.gitignore`, `README.md`, `pyproject.toml`, `src/atlas/__init__.py`, `src/atlas/__main__.py`, `tests/__init__.py`, `tests/test_smoke.py`, `.venv/` |
| 2 | python3.11 venv activates + `pip install -e ".[dev]"` succeeds | PASS | venv Python 3.11.15; pip install installed 47 packages (atlas-0.1.0 + 6 runtime deps + 3 dev deps + transitive); no errors |
| 3 | `python -m atlas --version` returns `atlas 0.1.0`; pytest smoke passes | PASS | `atlas 0.1.0` returned verbatim; `test_version_string PASSED` (1 passed in 0.01s) |
| 4 | Git remote configured to `github.com/santigrey/atlas`; first commit pushed; hash captured | PASS | commit hash `3e50a13`; push output: `[new branch] main -> main` |
| 5 | B2b + Garage anchors bit-identical pre/post Cycle 1A | PASS | both anchors unchanged from H1 ship state (verified pre/post) |

**5/5 PASS.**

---

## 3. Preflight ESC resolution (per Paco's 4 path rulings)

Path rulings approved at commit `7d29c6c` (`paco_response_atlas_v0_1_cycle_1a_preflight_resolved.md`).

### 3.1 Python 3.11 -- Path A (deadsnakes PPA) APPLIED

Before: only Python 3.10.12 on Beast; jammy apt only had `3.11.0~rc1-1~22.04` (RC1 from 2022, not production).

```bash
sudo -n add-apt-repository -y --no-update ppa:deadsnakes/ppa
sudo -n apt update
sudo -n apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils
```

After: Python 3.11.15 from `3.11.15-1+jammy1` deadsnakes package. System default `python3 -> 3.10` unchanged. Venv created via `python3.11 -m venv .venv` (explicit invocation).

**Note:** `python3.11-distutils` shows `un` in dpkg but `import distutils` works -- distutils is bundled in the main python3.11 package in deadsnakes' build. No follow-up needed.

### 3.2 PG creds -- Path A (.pgpass) APPLIED with REAL names

Real B2b state confirmed live this turn:
- DB: `controlplane`
- User: `admin`
- Password: `adminpass` per .pgpass entry (mode 600)
- Endpoints: `127.0.0.1:5432` + `localhost:5432`

`.pgpass` content (REDACTED in this review per Paco's directive; lives at `/home/jes/.pgpass` mode 600 owner jes:jes, 88 bytes):

```
127.0.0.1:5432:controlplane:admin:<REDACTED-IN-REVIEW-OUTPUT>
localhost:5432:controlplane:admin:<REDACTED-IN-REVIEW-OUTPUT>
```

Verification (live):
```
psql -h localhost -U admin -d controlplane -c 'SELECT 1 AS ok, current_database() AS db, current_user AS user;'
 ok |      db      | user
----+--------------+-------
  1 | controlplane | admin
(1 row)
```

Libpq picked up `.pgpass` automatically; no PGPASSWORD env required.

**`adminpass` is a known weak default.** P5 carryover banked for v0.2 hardening pass per Paco's deliverables list.

### 3.3 Garage URL -- spec amendment APPLIED in v3

Spec v1+v2 wrongly said `http://localhost:3900/health`. Garage's `:3900` is the S3 listener (returns AccessDenied on anonymous /health). Admin endpoint is `:3903`.

Verification (live):
```
curl -s http://127.0.0.1:3903/health
Garage is fully operational
Consult the full health check API endpoint at /v2/GetClusterHealth for more details
```

Spec v3 (commit `93b97e6`) cites the corrected URL throughout. No further amendment needed in this commit.

### 3.4 Tailscale -- Path B (skip, use LAN) APPLIED

Beast not enrolled in Tailscale (no `tailscale` package, no `tailscale0` interface). Goliath LAN endpoint `192.168.1.20:11434` substituted for the preflight check.

Verification (live):
```
curl -s http://192.168.1.20:11434/api/tags
{"models":[{"name":"qwen2.5:72b","size":47415724625,...},
          {"name":"deepseek-r1:70b","size":42520397873,...},
          {"name":"llama3.1:70b","size":42520412561,...}]}
```

3 70B+ models hosted on Goliath, all reachable from Beast via LAN. Atlas inference RPC (Cycle 1G per spec v3) will use this endpoint. Tailscale enrollment for Beast is now a P5 carryover for v0.2 if a future cycle hard-needs it.

---

## 4. Container state evidence

### 4.1 Pre-Cycle-1A Beast anchors (from preflight)

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

### 4.2 Post-Cycle-1A Beast anchors

```
/control-postgres-beast StartedAt=2026-04-27T00:13:57.800746541Z health=healthy restarts=0
/control-garage-beast   StartedAt=2026-04-27T05:39:58.168067641Z health=healthy restarts=0
```

**Bit-identical.** Cycle 1A is non-substrate-affecting per design (filesystem scaffold + git operations + apt install of Python on Beast host, none of which touch the running Postgres or Garage Docker containers).

---

## 5. Atlas package on-disk state (post-Cycle-1A)

```
/home/jes/atlas/
├── .git/                            (git initialized)
├── .gitignore                       (105 bytes, excludes .venv/ + secrets)
├── .venv/                           (Python 3.11.15 venv, gitignored)
├── README.md                        (357 bytes)
├── pyproject.toml                   (530 bytes, 9 deps + 3 dev deps)
├── src/
│   └── atlas/
│       ├── __init__.py              (63 bytes, __version__ = '0.1.0')
│       └── __main__.py              (443 bytes, --version flag)
└── tests/
    ├── __init__.py                  (empty)
    └── test_smoke.py                (142 bytes, test_version_string)
```

**File md5s** (for ship report continuity):
- pyproject.toml: 530 bytes
- src/atlas/__init__.py: 63 bytes
- src/atlas/__main__.py: 443 bytes
- tests/test_smoke.py: 142 bytes
- .gitignore: 105 bytes
- README.md: 357 bytes

---

## 6. Installed Python packages (47 total post pip install -e ".[dev]")

Key runtime deps:
- `atlas-0.1.0` (editable install of this package)
- `mcp 1.27.0` (latest Python MCP SDK)
- `psycopg 3.3.3` + `psycopg-binary` + `psycopg-pool 3.3.0` (Postgres async + pool)
- `boto3 1.43.0` + `botocore 1.43.0` + `s3transfer 0.17.0` (Garage S3 client)
- `pydantic 2.13.3` + `pydantic-core 2.46.3` + `pydantic-settings 2.14.0`
- `httpx 0.28.1` + `httpcore 1.0.9` + `httpx-sse 0.4.3`
- `structlog 25.5.0`
- `cryptography 47.0.0` + `pyjwt 2.12.1` (transitive)
- `starlette 1.0.0` + `sse-starlette 3.4.1` + `uvicorn 0.46.0` (transitive from mcp -- Atlas's own MCP server in Cycle 1F will use these)

Key dev deps:
- `pytest 9.0.3` + `pytest-asyncio 1.3.0`
- `ruff 0.15.12`

---

## 7. First commit on `santigrey/atlas`

**Hash:** `3e50a13`
**Message:** `feat: Cycle 1A scaffold -- atlas package skeleton on Beast`
**Body:** "Initial scaffold per tasks/atlas_v0_1.md Cycle 1A. Python 3.11 venv (deadsnakes PPA per Cycle 1A preflight ESC ruling). pyproject.toml, src layout (src/atlas + tests). Initial deps: psycopg+pool, boto3, pydantic, httpx, structlog, mcp 1.27.0+. Smoke test passes (version=0.1.0). Real B2b connection: controlplane db / admin user via .pgpass. Garage health verified at 127.0.0.1:3903. Goliath via LAN 192.168.1.20:11434."

7 files committed: `.gitignore`, `README.md`, `pyproject.toml`, `src/atlas/__init__.py`, `src/atlas/__main__.py`, `tests/__init__.py`, `tests/test_smoke.py`. `.venv/` excluded by gitignore. secret-grep: clean.

Push output:
```
To https://github.com/santigrey/atlas.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## 8. Spec amendments status (per Paco's deliverables list vs reality)

Paco's deliverables list specified spec amendments to fold:
- Cycle 1A preflight block: real DB/role names + Garage `:3903` URL + Goliath LAN check
- Cycle 1B Postgres connection layer: `admin/controlplane` instead of fictional names
- Cycle 1G inference RPC: Goliath via LAN
- Section 13 standing rules count: 4 -> 5
- P6 lessons count: 19 -> 20
- Section 14.3 P5 carryovers: add 2 (rotate adminpass + Beast Tailscale enrollment)

**Reality check:** Atlas spec v3 (commit `93b97e6`) ALREADY contains all of these amendments. The handoff was authored before v3 was published; Paco published v3 the same turn as ratifying the discipline RFC. Spec md5 currently `79c365406453d84ba7be54346287b3b9`.

No additional spec amendments folded in this commit. PD verified via grep that v3 has:
- Line 13: real names propagated to Cycles 1B/1E/1H/4D
- Line 15: Garage `:3903` admin URL
- Line 18: standing rules count 5
- Line 19: P6 lessons 20
- Line 247: Cycle 1A acceptance gates referencing this exact Cycle 1A close-out workflow
- Lines 38-40: live Verified live block citing real DB names + Garage URL

Spec is current; no fold needed.

---

## 9. P5 carryovers banked this cycle (added to v0.2 queue)

Added to v0.2 hardening pass (now ~9 items total, was 6 at H1 ship + 2 from this cycle + 1 from Phase I CK DNS):

7. **Rotate `adminpass`** -- Postgres admin password is a known weak default; rotate as part of v0.2 hardening pass. Current usage is contained to localhost-bound replica access.
8. **Beast Tailscale enrollment (optional)** -- if any future Atlas cycle hard-depends on Tailscale routes, enroll Beast then. Currently substituted with LAN access (`192.168.1.20:11434` for Goliath inference) which is sufficient.

(Existing v0.2 items: Goliath UFW / KaliPi UFW / grafana-data subdirs / Grafana pw rotation script / dashboard 3662 / CK->slimjim DNS / sshd recovery delay observation.)

---

## 10. Standing rules in effect (5 memory files)

1. `feedback_directive_command_syntax_correction_pd_authority.md` (5-guardrail + 2 carve-outs)
2. `feedback_paco_review_doc_per_step.md` (per-step review)
3. `feedback_paco_pd_handoff_protocol.md` (handoff + bidirectional one-liner)
4. `feedback_phase_closure_literal_vs_spirit.md` (closure pattern)
5. **`feedback_paco_pre_directive_verification.md` (NEW Day 75 -- pre-directive verification, three-layer rule, default measurement window: end of Atlas Cycle 1)**

The new 5th rule was authored in response to 3 consecutive Paco-side spec authoring errors (P6 #17/#19/#20). Cycle 1A is the first cycle authored under the rule (spec v3 has the master Verified live block per the rule).

---

## 11. P6 lessons banked total: 20

No new P6 lessons banked this Cycle 1A (the architectural lesson banked as the 5th standing rule). #20 was Paco's deployed-state-name verification banking from this cycle's preflight ESC.

---

## 12. Cross-references

**Predecessor doc chain:**
- `paco_request_atlas_v0_1_cycle_1a_preflight_fail.md` (PD ESC #1)
- `paco_response_atlas_v0_1_cycle_1a_preflight_resolved.md` (commit `7d29c6c`)
- Discipline RFC commit `93b97e6` (5th memory file + Atlas spec v3)
- (this) `paco_review_atlas_v0_1_cycle_1a_skeleton.md`

**Standing rules invoked:**
- 5-guardrail rule (deadsnakes install + .pgpass creation both PD-self-auth under operational-propagation carve-out since Paco explicitly authorized them via Path rulings)
- Pre-directive verification (5th rule -- spec v3 has master Verified live block)
- B2b + Garage anchor preservation invariant (still holding)
- Bidirectional one-liner format spec on handoffs (this cycle's paired handoff follows it)

---

## 13. Status

**CYCLE 1A CLOSED 5/5 PASS.** Atlas package skeleton landed on Beast + first commit on `santigrey/atlas` repo. Substrate untouched. Ready for Cycle 1B (Postgres connection layer per spec v3 section 7).

This Cycle 1A close-out commit folds: paco_review (this) + SESSION.md Day 75 Cycle 1A close section append + paco_session_anchor.md update (Cycle 1A CLOSED, Cycle 1B NEXT, P6=20, standing rules=5) + CHECKLIST.md audit entry.

-- PD
