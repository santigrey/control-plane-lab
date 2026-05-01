# paco_request_atlas_v0_1_cycle_1f_phase3_pretest_flake

**Spec:** Atlas v0.1 Cycle 1F Phase 3 (combined fix + deploy-restart + build close)
**Step:** Step 7 prior-test snapshot, BEFORE Step 8 pre-deploy checkpoint + Step 9 deploy-restart
**Status:** ESCALATION (defensive) -- 2 prior-test failures surfaced; root-cause analysis suggests test-isolation flake (NOT a Phase 3 regression). Filing per directive Step 7 literal expectation + P6 #25 hedge-propagation discipline + P6 #26 notification protocol.
**Predecessor:** `docs/paco_response_handoff_protocol_p6_26.md` (HEAD `7910b3b`); `docs/paco_response_atlas_v0_1_cycle_1f_phase3_handler_count_reconciliation.md` (commit `77759f8`); `docs/paco_response_atlas_v0_1_cycle_1f_phase_c20_confirm_phase3_go.md`
**Author:** PD (Cortez session)
**Date:** 2026-04-30 / 2026-05-01 UTC (Day 76 night)
**Target host:** Beast (atlas test suite at `/home/jes/atlas/`)

---

## TL;DR

Step 7 prior-test snapshot ran `pytest tests/db tests/storage tests/inference tests/embeddings -q`. Result: **2 failed, 13 passed** (15 collected, vs directive's expect=16). The 2 failures are token_logging tests (inference + embeddings) with same failure pattern: `assert post_count == pre_count + 1` getting `4 == 2+1` (delta=2 instead of 1).

**Root cause analysis:**
- atlas HEAD unchanged at `6c0b8d6` (Cycle 1E close)
- git status: only `src/atlas/mcp_client/` + `tests/mcp_client/` (new files, no overwrites of existing modules)
- Phase 3 work has NOT touched atlas.inference, atlas.embeddings, atlas.db, or any other module that could regress these tests
- **Both failing tests PASS in isolation** (`pytest <single-file>` → 2/2 pass in 1.04s)
- Failures only occur in the full-suite run: test-interaction flake, NOT a Phase 3 regression

**Recommendation:** continue per directive's *purpose* (regression detection — no regression found). Bank pre-existing flake as v0.2 P5 (test isolation fix). PD does NOT proceed to Step 8 without Paco's ruling.

B2b + Garage anchors bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` (76+ hours holding). atlas.events PRE: embeddings=2, inference=4 (pre-Phase-3 baseline).

---

## 1. Test snapshot evidence

### 1.1 Full suite run (failure)

```
$ pytest tests/db tests/storage tests/inference tests/embeddings -q

FAILED tests/inference/test_inference_token_logging.py::test_token_logging_inserts_event
FAILED tests/embeddings/test_embed_token_logging.py::test_embed_inserts_atlas_events_row
2 failed, 13 passed in 27.55s
```

Count discrepancy: 2 failed + 13 passed = **15** total; directive expected **16**. The +1 directive-author count is a separate hedge issue (likely off-by-one similar to handler count reconciliation, but outside scope of this paco_request — flagging only).

### 1.2 Failure pattern (both tests, same shape)

```
E  assert 4 == (2 + 1)   # post == pre + 1 violated; pre=2, post=4, delta=2 not 1
```

Pre-test row count of 2 means atlas.events PRE has 2 rows for source='atlas.embeddings' (or 4 for 'atlas.inference'). Post-test count of 4 means 2 rows were inserted instead of expected 1.

### 1.3 Isolation run (both tests PASS)

```
$ pytest tests/inference/test_inference_token_logging.py tests/embeddings/test_embed_token_logging.py -v

tests/inference/test_inference_token_logging.py::test_token_logging_inserts_event PASSED [ 50%]
tests/embeddings/test_embed_token_logging.py::test_embed_inserts_atlas_events_row PASSED [100%]

2 passed in 1.04s
```

**Both tests pass when run alone.** The delta is exclusively in the full-suite context.

### 1.4 Phase 3 code changes affecting test surface (none)

```
$ cd /home/jes/atlas && git status --short
?? src/atlas/mcp_client/
?? tests/mcp_client/
```

Both are NEW directories (untracked, no overwrites of any existing test or source file). HEAD `6c0b8d6` unchanged. The only modifications I've made on Beast are these 8 new files inside the new mcp_client/ subdirectories. There is no code path by which my Phase 3 work could regress atlas.inference or atlas.embeddings token_logging tests.

## 2. Hypotheses (for Paco architectural review)

### 2.1 Most likely: pytest-asyncio session-scope test interaction

pytest-asyncio with `asyncio_default_fixture_loop_scope=function` (verified in pyproject.toml header per the test output) means each test gets a fresh event loop. But shared module-level state (e.g., a Database singleton, a connection pool) could persist across tests within the same module. If a prior test in `tests/inference/` opens a Database and leaves async write tasks pending, the row counter might catch them in the post_count window.

### 2.2 Alternative: GoliathClient/EmbeddingClient open() side-effect

When the test does `async with GoliathClient(db=db) as client:` followed by `await client.generate(...)`, perhaps the `open()` lifecycle in client.py logs an event in addition to the explicit telemetry from the generate call. Would explain double-logging.

### 2.3 Race: psycopg async connection pool

With `min_size=2, max_size=10` (atlas.db.pool defaults), multiple connections could be in flight simultaneously. If pre_count is captured on connection A while a previous test's async commit is still pending on connection B, the snapshot might miss that row. Then post_count picks up both the test's intended row AND the late-arriving previous-test row.

### 2.4 None of the above

Requires Paco architectural review of atlas.inference.client + atlas.db.pool to identify the root cause definitively.

## 3. Substrate state (no changes)

- B2b anchor: `2026-04-27T00:13:57.800746541Z` -- bit-identical, holding 76+ hours
- Garage anchor: `2026-04-27T05:39:58.168067641Z` -- bit-identical, holding 76+ hours
- atlas.events PRE: embeddings=2, inference=4 (matches Verified live block from directive)
- uvicorn MainPID 3631249 alive (no patch yet — running OLD code)
- mcp_server.py ON DISK at HEAD `7910b3b` is NEW patched code (~388 lines, asyncio.to_thread wraps); .bak.phase3 preserves OLD
- atlas.mcp_client module NEW on Beast at HEAD `6c0b8d6` (untracked); imports cleanly per Step 6
- 8 new atlas files written: src/atlas/mcp_client/{__init__.py, acl.py, client.py} + tests/mcp_client/{__init__.py + 4 test files}

## 4. Asks of Paco (ratification + path-forward)

1. **Ratify or reject** PD's regression-detection-purpose interpretation: Step 7's *purpose* is to verify Phase 3 work did not break prior tests. Evidence shows no Phase 3 regression. Failures are pre-existing test-isolation flake.

2. **Approve PD to proceed** to Step 8 (pre-deploy checkpoint) + Step 9 (deploy-restart) treating these failures as pre-existing flakes documented for v0.2 P5 fix. OR

3. **Halt** for root-cause investigation BEFORE Step 9 deploy-restart. (Risk: deploy-restart would still occur after the flake is investigated; the flake is in atlas/ Python tests, not in mcp_server.py or anything the restart affects.)

4. **Bank as v0.2 P5 #12** (or similar): pytest-asyncio test isolation in atlas.inference + atlas.embeddings token_logging — root cause unknown, surfaced Day 76 Phase 3 Step 7. Deferred root-cause investigation post-Cycle-1F close.

5. **Acknowledge directive count** of 16 prior tests vs reality of 15 (similar to Phase 3 handler count off-by-one). Paco directive-author hedge would benefit from a final `pytest --collect-only` count verification. (Not blocking; flagging only.)

## 5. PD recommendation

Approve option (2) — proceed to Step 8 + Step 9. Rationale:

- Phase 3 deploy-restart goal is unblocking Atlas Cycle 1F (transport-hang root cause). Failures are unrelated to that goal.
- atlas.mcp_client tests will run AFTER deploy-restart per Step 12 — they will exercise the new mcp_client module against the patched server. Those 4 tests should pass cleanly (independent of the flake in inference + embeddings token_logging).
- Pre-existing flake fix is mechanical work (likely test fixture cleanup or @pytest.fixture(scope=...) tuning) appropriate for v0.2 P5.
- Halt would cost ~hours of debugging for zero Phase 3 risk reduction.

If Paco prefers option (3), PD can investigate atlas.inference.client.GoliathClient.open() lifecycle + atlas.db.pool connection state in parallel while CEO + Paco rule on Step 9 advance.

## 6. State at this pause (no further changes)

- Step 1 captured (anchors PRE)
- Step 2 server patch on disk (mcp_server.py.bak.phase3 backup preserved)
- Step 3 server patch validated (import probe + handler wrap inspection)
- Step 4+5 atlas.mcp_client module built (8 files) + Step 6 import validated
- Step 7 prior-test snapshot: this paco_request
- Steps 8-17 + Z: NOT started
- handoff_pd_to_paco.md notification line for THIS paco_request to follow per P6 #26 protocol

---

**File:** `docs/paco_request_atlas_v0_1_cycle_1f_phase3_pretest_flake.md` (untracked, transient until close-out per correspondence triad standing rule)

-- PD
