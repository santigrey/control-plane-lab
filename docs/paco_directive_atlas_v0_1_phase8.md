# paco_directive_atlas_v0_1_phase8

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-02 Day 78 evening
**Authority:** CEO ratified Day 78 evening (Atlas Phase 8 GO; A1=strict-spec-scope / B=include-pyproject-pytest-config / C1=GitHub-Actions-with-skip-mark / D=integration-test-marked / E1=fix-stale-migration-test / F=PD-executable).
**Status:** ACTIVE
**Tracks:** `tasks/atlas_v0_1_agent_loop.md` Phase 8 (lines 470-498).
**Predecessor:** Phase 7 close-confirm (atlas commit `085b8fb`; control-plane HEAD `bf05f80`).
**Target host:** Beast (atlas package + test authoring + smoke runs); GitHub.com (CI workflow lands as `.github/workflows/test.yml`).

---

## 0. Directive supersedes spec for these corrections

Live verification (Paco-side, 6 probes Day 78 evening) caught spec divergences:

| # | Spec assumption (line ref) | Live finding | Directive correction |
|---|---|---|---|
| 1 | Spec line 472 says `src/atlas/agent/test_*.py` (alongside source) | Phase 7 PD landed tests in `tests/agent/test_*.py` (separate test tree). Convention established. | Phase 8 tests land in `tests/agent/test_*.py` (loop, poller, infrastructure, talent, vendor) and `tests/integration/test_integration.py`. NOT alongside source. |
| 2 | Spec line 487 says `test_communication.py` should be authored Phase 8 | Already exists from Phase 7 (12 cases; full coverage). | Phase 8 does NOT re-author test_communication.py. Existing coverage stands. |
| 3 | Spec line 486 says `test_mercury.py` | Phase 7 landed `test_mercury_phase7.py` (3 cases; cancel-window only). Phase 6 mercury supervision lacks tests. | Phase 8 authors NEW `tests/agent/test_mercury.py` covering Phase 6 surface (liveness check + trade activity check + fail-closed Tier 3). Keeps `test_mercury_phase7.py` as-is. |
| 4 | (NEW finding) `pyproject.toml` lacks `[tool.pytest.ini_options]` | 27-line pyproject; pytest infers asyncio_mode from per-test fixtures; no testpaths/markers config | Phase 8 adds `[tool.pytest.ini_options]` block: asyncio_mode=auto, testpaths=tests, custom markers (slow, integration, homelab). |
| 5 | (NEW finding) `tests/db/test_migration_smoke.py` is broken | Hardcoded `tables == ["events", "memory", "schema_version", "tasks"]` but Phase 5 migration `0006_atlas_vendors.sql` added vendors table. Test fails on full-suite run. | Phase 8 fixes: update expected list to `["events", "memory", "schema_version", "tasks", "vendors"]`. Single-line change. |
| 6 | Spec mentions "CI hooks" without specifying CI host | No CI infra in atlas repo currently | Phase 8 adds `.github/workflows/test.yml` for GitHub Actions. Tests requiring homelab connectivity (DB, MCP, embeddings, inference) marked `@pytest.mark.homelab` and skipped in CI via `-m 'not homelab'`. CI runs unit + light tests only; homelab-marked tests run locally on Beast. |

---

## 1. Verified live (Paco pre-directive, Day 78 evening)

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | atlas HEAD PRE | `git log --oneline -1` on beast | `085b8fb feat: Cycle Atlas v0.1 Phase 7` |
| 2 | atlas working tree PRE | `git status -s` on beast | clean |
| 3 | Existing test inventory | `find tests -name 'test_*.py' \| sort` | 21 files / 35 collected tests; spans agent/db/embeddings/inference/mcp_client/storage |
| 4 | Full-suite pass-rate baseline | `pytest --tb=no -q` | 34 passed, 1 FAILED (`test_migration_smoke::test_migrations_idempotent`); 72.46s runtime |
| 5 | Migration test failure root cause | `pytest tests/db/test_migration_smoke.py -v` | hardcoded expected `["events","memory","schema_version","tasks"]`, actual schema `["events","memory","schema_version","tasks","vendors"]`. Stale test; migrations work. |
| 6 | Migration files inventory | `ls src/atlas/db/migrations/` | 6 SQL files: 0001 schema, 0002 schema_version, 0003 tasks, 0004 events, 0005 memory, 0006 vendors |
| 7 | pyproject.toml pytest config | `cat pyproject.toml` | NO `[tool.pytest.ini_options]` section; only `[project]`, `[project.optional-dependencies]`, `[build-system]`, `[tool.hatch.build.targets.wheel]` |
| 8 | atlas/.venv presence | `ls /home/jes/atlas/.venv/bin/python3` | exists; pytest 9.0.3, pytest-asyncio 1.3.0 installed |
| 9 | Existing test dirs structure | `find tests -type d` | tests/, tests/agent/, tests/db/, tests/embeddings/, tests/inference/, tests/mcp_client/, tests/storage/. NO tests/integration/ yet |
| 10 | Standing Gates 6/6 PRE | per Phase 7 close-confirm | All bit-identical at 120h+ |

All 10 verification rows match expectations. Zero discrepancies beyond the 6 spec corrections in section 0.

---

## 2. Phase 8 implementation

### 2.1 File inventory

| File | Action | Approx size |
|---|---|---|
| `tests/agent/test_loop.py` | NEW | ~80 lines |
| `tests/agent/test_poller.py` | NEW | ~120 lines |
| `tests/agent/test_infrastructure.py` | NEW | ~150 lines |
| `tests/agent/test_talent.py` | NEW | ~120 lines |
| `tests/agent/test_vendor.py` | NEW | ~140 lines |
| `tests/agent/test_mercury.py` | NEW (covers Phase 6 surface; complements Phase 7's test_mercury_phase7.py) | ~120 lines |
| `tests/integration/__init__.py` | NEW | empty |
| `tests/integration/test_integration.py` | NEW | ~150 lines |
| `tests/db/test_migration_smoke.py` | MODIFY (1 line; add 'vendors' to expected list) | -1/+1 |
| `pyproject.toml` | MODIFY (add `[tool.pytest.ini_options]` block) | +12 lines |
| `.github/workflows/test.yml` | NEW | ~50 lines |

Net: 7 NEW test files + 1 NEW init + 2 MODIFY (1-line + ~12-line) + 1 NEW CI workflow.

### 2.2 pyproject.toml additions

Append after existing `[tool.hatch.build.targets.wheel]` block:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "slow: tests that take more than 5 seconds",
    "integration: end-to-end integration tests requiring DB + agent loop",
    "homelab: tests requiring live homelab connectivity (DB / MCP / inference / embeddings); skipped in CI via -m 'not homelab'",
]
filterwarnings = [
    "ignore::DeprecationWarning:mcp.client.streamable_http",
]
```

### 2.3 tests/db/test_migration_smoke.py fix

Locate the assertion line:
```python
assert tables == ["events", "memory", "schema_version", "tasks"]
```
Replace with:
```python
assert tables == ["events", "memory", "schema_version", "tasks", "vendors"]
```

Single-line change. Keep all other test code intact.

### 2.4 tests/agent/test_loop.py architecture

**Coverage (per spec line 473):** loop crash-isolation works (one coroutine raising does not stop others).

Test cases:
- `test_loop_runs_three_coroutines`: monkey-patch loop's spawned coroutines with sentinels; verify all 3 spawn + run.
- `test_loop_crash_isolation`: monkey-patch one coroutine to raise immediately; verify other 2 continue running for >=2 cycles.
- `test_loop_logs_crashes`: verify caplog captures "coroutine X crashed" log line on synthetic crash.

Use `asyncio.create_task` + `asyncio.wait` with timeout for crash-isolation verification. Mark tests `@pytest.mark.asyncio`.

### 2.5 tests/agent/test_poller.py architecture

**Coverage (per spec line 474):** claim semantics correct; SKIP LOCKED prevents double-claim.

Test cases:
- `test_poller_claims_pending_task`: INSERT a pending task; run one poller iteration; verify status='running', updated_at incremented.
- `test_poller_skip_locked_no_double_claim`: INSERT 1 pending task; spawn 2 concurrent pollers; verify exactly 1 claims it (the other returns None).
- `test_poller_marks_done_after_handler`: full lifecycle: pending -> running -> done.
- `test_poller_idle_when_no_pending`: empty pending queue; poller returns None within sleep cadence.

Mark `@pytest.mark.homelab` (requires real psycopg connection to controlplane DB).

Cleanup discipline: tests INSERT atlas.tasks rows; finally-block DELETE all created rows.

### 2.6 tests/agent/test_infrastructure.py architecture

**Coverage (per spec line 475):** Prometheus query parsing; SSH fallback path; threshold detection.

Test cases:
- `test_prometheus_query_parses_cpu_value`: feed mocked Prometheus JSON response; verify CPU% extracted correctly.
- `test_prometheus_query_parses_ram_value`: same for RAM.
- `test_ssh_fallback_invoked_when_prometheus_unreachable`: monkey-patch httpx to raise; verify _ssh_run called for the same metric.
- `test_threshold_detection_cpu_high`: feed value above threshold; verify _create_monitoring_task called with kind='monitoring_cpu'.
- `test_threshold_detection_cpu_normal`: feed value below threshold; verify NO task created.
- `test_substrate_anchor_unchanged`: monkey-patch docker inspect to return baseline timestamp; verify check passes (no Tier 3 emit).
- `test_substrate_anchor_changed_raises_tier3`: monkey-patch docker inspect to return DIFFERENT timestamp; verify Tier 3 emit_event called.

Monkey-patch httpx, `_ssh_run`, `_create_monitoring_task`, `emit_event`. NO real network/DB calls. Mark `@pytest.mark.asyncio`.

### 2.7 tests/agent/test_talent.py architecture

**Coverage (per spec line 476):** job_search_log parsing; new-entry detection; digest aggregation.

Test cases:
- `test_parse_job_search_log_csv_or_md`: feed sample log; verify entries extracted correctly (title, company, applied_date).
- `test_new_entry_detection_since_last_check`: feed log with timestamp; verify only entries after `last_check_ts` returned.
- `test_digest_aggregation_groups_by_company`: feed multi-company log; verify aggregation produces per-company summary.
- `test_empty_log_returns_no_entries`: edge case.

Monkey-patch file reads (Path.read_text); NO real disk reads.

### 2.8 tests/agent/test_vendor.py architecture

**Coverage (per spec line 477):** renewal warning thresholds (14d / 3d); Tailscale parsing; GitHub PAT note reading.

Test cases:
- `test_renewal_warning_14d_threshold`: feed expiry 13 days out; verify warning emit; 15d out verify NO warning.
- `test_renewal_warning_3d_threshold_critical`: feed expiry 2 days out; verify CRITICAL emit (Tier 3); 4d out verify warn (Tier 2).
- `test_tailscale_status_parses_devices`: feed mocked tailscale status JSON; verify devices extracted.
- `test_github_pat_note_parses_expiry`: feed mocked PAT note text; verify expiry date extracted.
- `test_alert_already_today_dedup`: verify _alert_already_today helper returns True when same alert posted today, False when not.

### 2.9 tests/agent/test_mercury.py architecture (Phase 6 surface)

**Coverage (per spec line 478, complements existing test_mercury_phase7.py):** liveness check; trade activity check; fail-closed raises Tier 3.

Test cases:
- `test_mercury_liveness_active_no_emit`: monkey-patch _mercury_is_active=True; verify no Tier 3 emit.
- `test_mercury_liveness_inactive_raises_tier3`: monkey-patch _mercury_is_active=False; verify Tier 3 emit_event with kind='mercury_liveness_failed'.
- `test_trade_activity_recent_no_emit`: monkey-patch trade query to return rows within TRADE_ACTIVITY_GAP_DAYS; verify no emit.
- `test_trade_activity_stale_emits_warn`: monkey-patch trade query to return rows older than TRADE_ACTIVITY_GAP_DAYS; verify warn emit.
- `test_fail_closed_on_db_error_raises_tier3`: monkey-patch DB to raise; verify Tier 3 emit before re-raise (defensive).
- `test_ratification_doc_check_passes`: monkey-patch _check_ratification_doc=True; verify proceed.
- `test_ratification_doc_check_fails_raises_tier3`: monkey-patch _check_ratification_doc=False; verify Tier 3 emit.

### 2.10 tests/integration/test_integration.py architecture

**Coverage (per spec lines 482-485):** spin up agent loop for 30s with mocked atlas.tasks rows; verify all coroutines run; verify atlas.events rows written.

Test cases:
- `test_full_agent_loop_30s`: 
  1. INSERT 3 pending atlas.tasks rows (one per domain).
  2. Start agent loop in background (asyncio.create_task).
  3. Wait 30 seconds.
  4. Cancel loop.
  5. Verify atlas.events received >=1 row from each Domain (1-4) via SQL count.
  6. Verify atlas.tasks rows transitioned pending -> running -> done.
  7. Cleanup: DELETE all test rows from atlas.events + atlas.tasks.

Mark `@pytest.mark.integration @pytest.mark.slow @pytest.mark.homelab`. Triple-marked: skipped in fast CI; runs on Beast manually or via tagged CI run.

### 2.11 .github/workflows/test.yml

```yaml
name: atlas tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
      - name: Run unit tests (skip homelab + slow + integration)
        run: pytest -m 'not homelab and not slow and not integration' -v
      - name: Lint
        run: ruff check src tests
```

CI runs `pytest -m 'not homelab and not slow and not integration'` -- excludes all 3 marks. Result: only tests that work without homelab connectivity run. The 4 mcp_client + 4 inference + 4 embeddings + 3 db + 3 storage + integration tests all skip in CI.

Locally on Beast: `pytest` runs everything (no -m filter); `pytest -m homelab` runs only homelab-dependent; `pytest -m 'not slow'` runs fast tests only.

### 2.12 Mark application across existing 21 tests

PD adds `@pytest.mark.homelab` decorator to existing tests requiring homelab connectivity:

- `tests/db/test_*.py` (3 files: cross_schema_read, db_smoke, migration_smoke) -- ALL three need DB.
- `tests/embeddings/test_*.py` (4 files) -- all need DB + embeddings service.
- `tests/inference/test_*.py` (4 files) -- all need inference service.
- `tests/mcp_client/test_*.py` (4 files) -- all need MCP server.
- `tests/storage/test_*.py` (3 files) -- all need Garage S3.
- `tests/test_smoke.py` -- pure version string check; NO mark needed.
- `tests/agent/test_communication.py` -- mostly mocked; ONE test (test_emit_event_inserts_atlas_events) hits DB; mark THAT ONE only.
- `tests/agent/test_mercury_phase7.py` -- mostly mocked; cancel-mid-window test hits atlas.tasks via DB; mark THAT ONE only.

18 of 21 existing test files get module-level `pytestmark = pytest.mark.homelab`; 3 (test_smoke.py, test_communication.py per-test, test_mercury_phase7.py per-test) get selective marking.

---

## 3. Acceptance criteria (Phase 8)

1. All 6 NEW unit test files exist with documented test cases per sections 2.4-2.9.
2. Integration test file exists per section 2.10; runs to completion in <60s when invoked manually.
3. `tests/db/test_migration_smoke.py` passes (vendors fix per section 2.3).
4. `pyproject.toml` `[tool.pytest.ini_options]` block lands per section 2.2; `pytest --version` shows configfile.
5. `pytest -m 'not homelab and not slow and not integration'` (CI mode) passes 0 fail.
6. `pytest` (full local mode) passes >=49/50 tests (35 existing + 15 NEW Phase 8 minimum); 1 known-fail tolerance ONLY if it's not net-new from Phase 8 (e.g. a pre-existing inference flakiness).
7. `.github/workflows/test.yml` exists; YAML lint clean (PD verifies via `python -c 'import yaml; yaml.safe_load(open(".github/workflows/test.yml"))'`).
8. Standing Gates 6/6 preserved (Phase 8 should be entirely test-side; no source code changes; substrate anchors bit-identical).
9. Pre-commit BOTH broad-grep AND tightened-regex secrets-scan clean (P6 #34).

---

## 4. Procedure

**Step 0 -- Pre-flight:**
```bash
cd /home/jes/atlas && git log --oneline -1 && git status -s && \
  source .venv/bin/activate && pytest --collect-only -q 2>&1 | tail -3 && \
  pytest --tb=no -q 2>&1 | tail -3
```
Expected: HEAD `085b8fb`; clean tree; 35 tests collected; baseline 34 passed 1 failed (migration_smoke).

**Step 1 -- pyproject.toml + migration test fix:**
- Append `[tool.pytest.ini_options]` block per section 2.2.
- Edit `tests/db/test_migration_smoke.py` line per section 2.3.
- Run: `pytest tests/db/test_migration_smoke.py -v` -- expect PASS.

**Step 2 -- Apply @pytest.mark.homelab decorators per section 2.12:**
- Module-level `pytestmark = pytest.mark.homelab` for 18 files.
- Per-test marks for selective cases.
- Verify: `pytest -m 'not homelab' --collect-only -q` shows only the small no-homelab subset.

**Step 3 -- Author tests/agent/test_loop.py (section 2.4)** + run + verify pass.

**Step 4 -- Author tests/agent/test_poller.py (section 2.5)** + run + verify pass.

**Step 5 -- Author tests/agent/test_infrastructure.py (section 2.6)** + run + verify pass.

**Step 6 -- Author tests/agent/test_talent.py (section 2.7)** + run + verify pass.

**Step 7 -- Author tests/agent/test_vendor.py (section 2.8)** + run + verify pass.

**Step 8 -- Author tests/agent/test_mercury.py (section 2.9)** + run + verify pass. (NEW file; complementary to existing test_mercury_phase7.py.)

**Step 9 -- Author tests/integration/__init__.py + tests/integration/test_integration.py (section 2.10)** + run + verify pass.

**Step 10 -- Author .github/workflows/test.yml (section 2.11)** + YAML lint check.

**Step 11 -- Full-suite cross-cutting smoke:**
```bash
source .venv/bin/activate
echo '---CI mode (no homelab/slow/integration)---'
pytest -m 'not homelab and not slow and not integration' --tb=short 2>&1 | tail -10
echo '---FULL local mode---'
pytest --tb=short 2>&1 | tail -10
```
Capture both outputs in PD review section 4.

**Step 12 -- Pre-commit secrets-scan (BOTH broad + tightened, diff-only):**
```bash
cd /home/jes/atlas && git diff | grep -E '^[+-]' | grep -v '^---' | grep -v '^+++' | grep -niE 'key|token|secret|password|api|auth' | head -30
cd /home/jes/atlas && git diff | grep -E '^[+-]' | grep -v '^---' | grep -v '^+++' | grep -niE 'api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+|authorization:'
```

**Step 13 -- Standing gates POST-check** (4 + mercury liveness same as Phase 7 Step 7).

**Step 14 -- Commit + push:**
```bash
git add tests/agent/test_loop.py tests/agent/test_poller.py tests/agent/test_infrastructure.py \
  tests/agent/test_talent.py tests/agent/test_vendor.py tests/agent/test_mercury.py \
  tests/integration/__init__.py tests/integration/test_integration.py \
  tests/db/test_migration_smoke.py pyproject.toml .github/workflows/test.yml
git add tests/  # for the homelab-mark decorator updates
git commit -m 'feat: Cycle Atlas v0.1 Phase 8 consolidated test suite + CI hooks

Phase 8.1: 6 NEW unit test modules (loop crash-isolation, poller SKIP LOCKED claim,
infrastructure Prometheus+SSH fallback+threshold, talent job_search_log+digest,
vendor renewal thresholds+Tailscale+GitHub PAT, mercury Phase-6-surface liveness+trade-activity).

Phase 8.2: integration test (30s agent loop with mocked atlas.tasks rows; all 4 domains
emit atlas.events; full lifecycle pending->running->done) marked @pytest.mark.integration
@pytest.mark.slow @pytest.mark.homelab.

Infra: pyproject.toml [tool.pytest.ini_options] (asyncio_mode=auto; testpaths=tests;
custom markers slow/integration/homelab); .github/workflows/test.yml runs CI mode
(-m "not homelab and not slow and not integration") to skip homelab-dependent tests.

Pre-existing test fix: tests/db/test_migration_smoke.py expected list updated to include
vendors table (added in 0006_atlas_vendors.sql; test never updated).

6 spec corrections handled per paco_directive_atlas_v0_1_phase8.md section 0.

Tests: 6/6 acceptance criteria PASS; CI-mode 0 fail; full-mode <known-flaky-tolerance>.'
git push
```

**Step 15 -- Write `docs/paco_review_atlas_v0_1_phase8.md`** in control-plane following Phase 7 review template.

**Step 16 -- Notification line in `docs/handoff_pd_to_paco.md`:**
> Paco, PD finished Atlas v0.1 Phase 8. Consolidated test suite + CI hooks shipped; <N> tests pass; standing gates 6/6 preserved; atlas commit `<hash>`. Review: `docs/paco_review_atlas_v0_1_phase8.md`. Check handoff.

## 5. Discipline reminders

- One step at a time per Phase 7 cadence; 16 steps is bigger than Phase 7 (10) but each step is smaller.
- DO NOT touch source code under `src/atlas/` -- Phase 8 is test-side only. Standing gates auto-preserved.
- Test fixtures must DELETE rows in finally-blocks; zero leak (Phase 7 cleanup discipline).
- For tests/integration/test_integration.py: 30s real agent loop run is allowed but must use a unique payload marker (e.g. `payload.test_run_id=<uuid>`) so cleanup can target only test rows, never production rows.
- @pytest.mark.homelab is the LOAD-BEARING mark for CI; if any test silently depends on DB without that mark, CI breaks. PD audits by running `pytest -m 'not homelab' -v` and confirming all collected tests pass without DB reachability.
- ruff lint: PD runs `ruff check src tests` after authoring; fixes any new violations before commit.
- `.github/workflows/test.yml` should NOT include any secrets / tokens. CI runs ruff + pytest only.
- atlas-agent.service stays disabled+inactive (Phase 1 acceptance preserved through 8 phases; Phase 9 enables).

## 6. Trigger from CEO to PD (Cowork prompt)

```
You are PD (Cowork) for Santigrey Enterprises. Paco (COO) has dispatched Atlas v0.1 Phase 8.

Repos:
- santigrey/atlas at /home/jes/atlas on Beast (HEAD 085b8fb).
- santigrey/control-plane at /home/jes/control-plane on CK (HEAD bf05f80). Read directive + write paco_review here.

Read in order:
1. /home/jes/control-plane/docs/paco_directive_atlas_v0_1_phase8.md (your authority)
2. /home/jes/control-plane/docs/feedback_paco_pre_directive_verification.md (P6 standing rules)
3. /home/jes/control-plane/docs/paco_review_atlas_v0_1_phase7.md (predecessor)

Directive supersedes spec for the 6 corrections in section 0.

Execute Steps 0 -> 16 per directive section 4. One step at a time; verify before next.

Phase 8 is test-side ONLY. Do NOT modify src/atlas/ source. Standing gates auto-preserved.

If any step fails acceptance: STOP, write paco_request_atlas_v0_1_phase8_<topic>.md, do not proceed.

Begin with Step 0 pre-flight.
```

-- Paco
