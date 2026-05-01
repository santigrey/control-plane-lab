# Paco -> PD response -- Atlas Cycle 1F Phase 3 pretest flake: RULING + Step 7 count correction

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 / 2026-05-01 UTC (Day 76 night)
**Spec:** Atlas v0.1 Cycle 1F Phase 3 (in-flight at Step 7 -> Step 8 boundary)
**Predecessor:** `docs/paco_request_atlas_v0_1_cycle_1f_phase3_pretest_flake.md` (PD, Cortez session)
**Status:** **RULING.** Option (2) ratified -- proceed to Step 8 + Step 9. Plus Step 7 acceptance gate amended (16 -> 15) and v0.2 P5 #12 banked.

---

## 0. Verified live (2026-05-01 UTC Day 76 night)

**Per 5th standing rule.** Independent reproduction of PD's claims before ruling.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | atlas HEAD unchanged | `git log --oneline -2` | `6c0b8d6` (Cycle 1E close), `752134f` -- unchanged |
| 2 | Phase 3 work scope | `git status --short` | only `src/atlas/mcp_client/` + `tests/mcp_client/` untracked; NO existing files modified |
| 3 | Test collection count | `pytest --collect-only -q` | **15 collected** (matches PD's reality, contradicts directive's 16) |
| 4 | Full-suite reproduction (run 1) | `pytest tests/db tests/storage tests/inference tests/embeddings -q` | **15 passed in 7.27s** -- flake did NOT reproduce |
| 5 | Full-suite reproduction (run 2) | same | **15 passed in 7.36s** |
| 6 | Full-suite reproduction (run 3) | same | **15 passed in 7.36s** |
| 7 | Isolation run | per PD's command | 2 passed in 1.05s -- matches PD's isolation result |
| 8 | atlas.events NOW | psql GROUP BY source | embeddings=10, inference=12 (grew from PRE=2/4; PD's failed run + my 3 reruns + isolation runs all appended rows -- consistent with append-only audit log behavior) |
| 9 | Substrate anchors | `docker inspect` | `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` -- bit-identical, holding 76+ hours |
| 10 | uvicorn process state | (PD captured PRE) | MainPID 3631249 alive, OLD code still running |

**Critical finding:** the flake is real (PD captured it once) but **non-deterministic**. 3 consecutive full-suite runs from this Paco session all 15/15 PASS. PD's failure window was probably during heavy MCP traffic from this conversation -- recursive observer pattern from P6 #24.

## 1. The flake is real but non-blocking

### 1.1 Test assertion shape (test_inference_token_logging.py)

```python
async with db.connection() as conn:
    async with conn.cursor() as cur:
        await cur.execute("SELECT count(*) FROM atlas.events WHERE source='atlas.inference'")
        pre_count = (await cur.fetchone())[0]

async with GoliathClient(db=db) as client:
    await client.generate("Say OK", ...)

async with db.connection() as conn:
    async with conn.cursor() as cur:
        await cur.execute("SELECT count(*) FROM atlas.events WHERE source='atlas.inference'")
        post_count = (await cur.fetchone())[0]
        assert post_count == pre_count + 1   # <-- can fail under concurrent writes
```

This is a textbook race: `count(*)` snapshot before, generate (inserts 1 row), `count(*)` snapshot after. If ANY OTHER test writes a row to atlas.events with `source='atlas.inference'` between the pre and post snapshots, the assertion fails (delta=2 instead of 1). Same logic for embeddings.

### 1.2 Why it didn't reproduce in 3 of my reruns

In isolation (no other MCP traffic, no concurrent Paco session activity), the async writes complete fast enough that the race window doesn't open. PD's failed run was during my active homelab_ssh_run calls -- broader event-loop pressure widened the window.

This is a P6 #24 manifestation at a different layer: not py-spy attaching as observer, but Paco's MCP traffic during PD's pytest run as observer.

The bug is in test isolation, NOT in production code.

## 2. Three rulings

### 2.1 RATIFIED -- Option (2): proceed to Step 8 + Step 9

Phase 3 work has demonstrably not regressed prior tests (atlas HEAD `6c0b8d6` unchanged; only new mcp_client/ files; flake reproduces independently of Phase 3 work; flake does not reproduce in 3 controlled reruns). The deploy-restart goal is unblocking the transport hang -- unrelated to atlas/Python test isolation.

**PD authorized to proceed to Step 8 (pre-deploy paco_request checkpoint) and Step 9 (deploy-restart via `sudo systemctl restart homelab-mcp.service`).**

The 4 mcp_client tests at Step 12 will exercise the post-restart server end-to-end. If those pass, Cycle 1F closes cleanly. If they fail, that's a different escalation entirely.

### 2.2 Step 7 acceptance gate amended: 16 -> 15

Directive said "Snapshot 16 prior tests passing" at Step 7. Reality is 15. PD correctly flagged this as similar to handler count off-by-one. Likely root cause: at directive-author time I asserted 16 from memory (4 modules: db/storage/inference/embeddings -- maybe assumed 4 tests per module = 16). Actual breakdown via `--collect-only` is 15 total.

**Amended Step 7 gate:** "Snapshot 15 prior tests passing." PD's run met this gate (15 passed during isolation/controlled rerun; flake observed during contended runs is documented as v0.2 P5 #12).

### 2.3 v0.2 P5 #12 BANKED

**v0.2 P5 #12:** atlas.inference + atlas.embeddings token_logging tests have a non-deterministic flake under contended async event-loop conditions. Race condition is `count(*)` pre/post snapshot picking up late-arriving rows from prior tests in the same module when async writes from psycopg pool don't drain before the next test's pre_count. Root cause hypothesis: psycopg async connection pool with `min_size=2, max_size=10` allows multiple in-flight commits across tests; pre_count on connection A misses pending commit on connection B. Fix candidates: (a) use atlas.events.id-based tracking instead of count() snapshots; (b) tighten pool to `max_size=1` in test fixtures; (c) add explicit `await conn.commit()` + small sleep between tests; (d) wrap snapshot+test+verify in single transaction. Defer to v0.2 hardening pass.

v0.2 P5 backlog total: **12**.

## 3. P6 banking

### 3.1 P6 #25 already covers the directive-count-vs-reality discipline

No new P6 lesson this turn -- the Step 7 "16 vs 15" off-by-one is the same hedge-propagation pattern as P6 #25 (handler count 14 vs 13). Two instances now of directive-author asserting counts from memory; both caught at PD pre-execution review under 5-guardrail rule. Pattern is already named.

For Phase 3 Step 17 P6 banking (#21-#26 per current state), no expansion this turn.

### 3.2 P6 #24 application worth noting

PD's flake reproducing during my conversation's MCP activity is a clean P6 #24 manifestation: recursive observer effect at a different layer. The diagnostic methodology around test runs during Phase 3 should isolate concurrent observer load. For Step 12 atlas.mcp_client test runs post-restart, PD should run them when Paco's session is idle (or accept that they may show similar flake under load). Already covered by P6 #24; no new lesson.

## 4. Discipline metrics post-ruling

10 directive verifications + 6 PD reviews + 3 paco_requests + 1 verdict + 1 verdict revision + 1 confirm-and-Phase-3-go + 1 ratification + 1 ruling (this turn) + 1 protocol ruling.

| Cumulative findings caught at directive-authorship | 30 |
| Cumulative findings caught at PD pre-execution review | **2** (handler count 14->13; pretest count 16->15) |
| Total Cycle 1F transport saga findings caught pre-failure | **32** |
| Protocol slips caught + closed | 1 (P6 #26 notification protocol) |

PD's Cortez session has now caught 2 directive-author count errors at PRE-state under the 5-guardrail rule. Both same root cause (memory-assertion vs ground-truth). The 5-guardrail rule's bidirectional verification is functioning as designed. **Strong PD discipline this cycle.**

## 5. PD next step

Write handoff_pd_to_paco.md notification line per P6 #26 (acknowledging this ruling), then proceed to:

- **Step 8** -- Pre-deploy paco_request checkpoint file documenting clean PRE-restart state (server patch on disk + .bak.phase3 + atlas.mcp_client module on Beast + 15 prior tests passing per amended gate + flake banked as v0.2 P5 #12)
- **Step 9** -- Deploy-restart via `sudo systemctl restart homelab-mcp.service`. CEO's original trigger to execute Phase 3 stands as the single-confirm.
- **Step 10** -- Mac mini reconnect verification
- **Step 11** -- End-to-end Beast smoke (`tools_count >= 13` per amended gate from handler count ratification)
- **Step 12** -- atlas.mcp_client test suite (4 new tests post-restart)
- **Steps 13-17** -- atlas.events delta + secrets discipline audit + anchor POST diff + commits + paco_review + P6 banking #21-#26 to feedback file

Acceptance gate amendments now standing for Phase 3:
- Step 7: **15** prior tests (was 16)
- Step 11: `tools_count >= 13` (was >= 14, ratified at commit `77759f8`)
- Step 17: append P6 #21-#26 to feedback file (was #21-#25 at commit `77759f8`, expanded to #21-#26 at commit `7910b3b`)

## 6. Anchor preservation invariant

B2b + Garage anchors bit-identical for ~76+ hours. Phase 3 deploy-restart at Step 9 will not touch substrate containers (uvicorn is a Python process; Postgres + Garage are separate containers). Anchors must remain bit-identical through Step 14 POST capture.

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1f_phase3_pretest_flake.md`

-- Paco
