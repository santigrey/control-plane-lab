# paco_review_atlas_v0_1_phase6

**Spec:** Atlas v0.1 Operations Agent Loop Build Spec (`tasks/atlas_v0_1_agent_loop.md` lines 395-447 = Phase 6)
**Phase:** 6 -- Domain 4: Mercury supervision (liveness + trade activity + real-money fail-closed + start/stop stubs)
**Status:** **1/1 acceptance criterion PASS first-try.** Phase 6 CLOSED. Ready for Phase 7 GO ratification.
**Predecessor:** `docs/paco_response_atlas_v0_1_phase5_confirm_phase6_go.md` (Phase 6 GO Ruling 5) + `docs/handoff_paco_to_pd.md` (Phase 6 GO directive with cross-host architecture surfacing)
**Atlas commit:** `10adf9f7e3a89aeb2cad86b65b14bfa11e925b9c` on santigrey/atlas main (parent `af8768d`)
**Author:** PD (Cowork session, Beast-targeted execution + Path B refined ratified by CEO mid-Step-1)
**Date:** 2026-05-02 UTC (Day 78 morning)
**Target host:** Beast (atlas package authoring + agent runtime host) + cross-host SSH+psycopg2 to CK

---

## 0. Verified live (per 5th standing rule + P6 #29 + #32 reuse-pattern)

P6 #32 reuse pattern carried forward: `_create_monitoring_task` + `_ssh_run` from `infrastructure.py`; `_alert_already_today` from `vendor.py`. P6 #29 verified at write time: every external dependency probed live BEFORE authoring (CK Python, psycopg2 version, mercury .env parseability, ratification doc baseline, end-to-end SSH+inline-Python+JSON-stdout prototype).

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Beast Postgres anchor PRE | `docker inspect control-postgres-beast` | `2026-04-27T00:13:57.800746541Z` |
| 2 | Beast Garage anchor PRE | `docker inspect control-garage-beast` | `2026-04-27T05:39:58.168067641Z` |
| 3 | atlas-mcp.service PRE | `systemctl show atlas-mcp.service` | `active running`; MainPID 2173807; since 2026-05-01 22:05:42 UTC |
| 4 | atlas-agent.service PRE | `systemctl show atlas-agent.service` | `inactive dead disabled`; MainPID 0 (Phase 1 acceptance preserved through 5 phases) |
| 5 | mercury-scanner.service PRE | `ssh ck systemctl show` | `active running` MainPID 643409 |
| 6 | atlas HEAD PRE | `git log` | `af8768d` (Phase 5 close) |
| 7 | Beast has /home/jes/control-plane/ clone | `[ -d .git ]` | `BEAST_HAS_CLONE` (but docs/ stale at Apr 30 21:26; missing Phase 0-5 docs) -- routed ratification check via SSH to CK for canonical source-of-truth |
| 8 | Ratification doc presence (canonical CK path) | `ssh ck test -f /home/jes/control-plane/docs/mercury_real_money_ratification.md` | `DOC_ABSENT_AS_EXPECTED` (correct baseline; never created) |
| 9 | Beast .pgpass for CK | `cat /home/jes/.pgpass` | localhost+127.0.0.1 only; no CK entry. Confirmed via `psql -h 192.168.1.10` -> `fe_sendauth: no password supplied`. Path B refined chosen over Path A. |
| 10 | CK has psql command | `which psql` on CK | `psql: command not found`. Confirmed Path B uses Python+psycopg2 inline, NOT shell psql. |
| 11 | CK Python + psycopg2 (P6 #29) | `which python3 + python3 -c 'import psycopg2'` on CK | `/usr/bin/python3 3.10` + `psycopg2 2.9.11` system-wide |
| 12 | Mercury .env DATABASE_URL parseable | `grep DATABASE_URL` on CK | `postgresql://admin:<weak>@192.168.1.10:5432/controlplane` (P5 candidate flagged for v0.1.1 hardening) |
| 13 | Beast->CK SSH BatchMode + key auth | `ssh -o BatchMode=yes jes@192.168.1.10 ...` | exit 0; Phase 4 carryover working |
| 14 | End-to-end SSH+inline-python+psycopg2+JSON prototype | live probe before authoring mercury.py | rc=0; parsed JSON `{total: '152', paper: '152', real: '0', latest: '2026-05-02 05:10:09'}` -- approach validated |
| 15 | atlas /home/jes/atlas/.env (Phase 9 latent blocker) | `ls -la .env` | DID NOT EXIST. Created empty at Step 1 close (`touch`); systemd EnvironmentFile reference now satisfies on Phase 9 enable. |
| 16 | mercury.trades baseline | cross-host query at Step 1 | `total=152 paper=152 real=0 latest=2026-05-02 05:10:09 earliest=2026-04-08 20:52:38` (Day 78 fix revived Mercury; spec `142 rows latest 2026-04-26` was stale -- Paco-acknowledged) |
| 17 | mercury.py py_compile + import | `python -m py_compile + python -c 'from atlas.agent.domains import mercury'` | `PY_COMPILE_OK`; `IMPORT_OK`; 5 public funcs (3 cadenced + 2 stubs) + 4 private helpers |
| 18 | scheduler.py wiring | `python -c 'inspect.getsource(scheduler.scheduler)'` | All 3 mercury dispatch blocks present; `last_run` dict has 11 keys total; `CADENCE_MERCURY_S=300` + `MERCURY_TRADE_HOUR_UTC=8` exposed |
| 19 | 9/9 smoke assertions PASS end-to-end | `/tmp/atlas_phase6_smoke.py` | A: real liveness (mercury active) -> 0 alerts; B: real trade_activity (recent_count > 0) -> 0 alerts; C: real real_money_failclosed (real_count=0) -> 0 alerts; D: synthetic mercury_is_active=False -> 1 critical liveness; D2: D rerun -> dedup held; E: synthetic 8d-gap -> 1 warn trade_activity; F: synthetic real_count=5 + doc absent -> 1 critical unauthorized; G: real_count=5 + doc PRESENT -> 0 new (gate satisfied); H: synthetic check error -> 1 critical check_error (fail-closed bias) |
| 20 | atlas commit + push | `git log + git push` | `10adf9f feat: Cycle Atlas v0.1 Phase 6 Domain 4 Mercury supervision`; pushed `af8768d..10adf9f` to santigrey/atlas main |
| 21 | Pre-commit secrets scan (broad) -- CAUGHT real credential exposure | `git diff --staged \| grep -iE 'key\|token\|secret\|password\|api'` | Initial scan caught literal Mercury credential (`'adminpass'`) embedded in mercury.py module docstring (P5 finding I had documented WITH the value). REDACTED via sed to generic phrasing ('a weak password embedded inline'). Re-scan: count=0. |
| 22 | Pre-commit secrets scan (tightened) | `grep -iE 'api[_-]?key\|secret[_-]?key\|access[_-]?token\|bearer\\s+\|authorization:'` | `TIGHTENED_GREP_CLEAN` -- would have missed the `adminpass` literal; broad scan was the catch layer |
| 23 | Beast Postgres anchor POST | `docker inspect` post-smoke + post-commit | `2026-04-27T00:13:57.800746541Z` -- bit-identical |
| 24 | Beast Garage anchor POST | `docker inspect` post-smoke + post-commit | `2026-04-27T05:39:58.168067641Z` -- bit-identical |
| 25 | atlas-mcp.service POST (Standing Gate #4) | `systemctl show` | `active running`; MainPID 2173807 -- UNCHANGED |
| 26 | atlas-agent.service POST (Phase 1 state preserved) | `systemctl show` | `inactive dead disabled` -- still NOT enabled (Phase 9 territory respected through 6 phases) |
| 27 | mercury-scanner.service POST (Standing Gate #6) | `ssh ck systemctl show` | `active running` MainPID 643409 -- UNCHANGED |
| 28 | mercury.trades zero atlas-side mutation | cross-host query post-smoke | `total=152 real=0` -- bit-identical to PRE; smoke used monkey-patches, not synthetic INSERTs |
| 29 | Ratification doc still ABSENT POST | `ssh ck test -f` post-smoke | `DOC_ABSENT` -- canonical baseline preserved (smoke used monkey-patch of `_check_ratification_doc`, not file create/delete on CK) |
| 30 | atlas.tasks mercury alerts POST cleanup | `psql count` | 0 -- no leak |

30 verified-live items, 0 mismatches, 0 deferrals (1 mid-step REDACTION caught by secrets scan + corrected before commit).

---

## 1. TL;DR

Phase 6 implemented Domain 4: Mercury supervision. 2 atlas package files (1 new module + 1 modified scheduler) totaling +402 lines. Atlas commit `10adf9f` shipped to santigrey/atlas main. Acceptance criterion PASSES first-try.

**Cross-host architecture (Path B refined; ratified by CEO mid-Step-1):** atlas runs on Beast; mercury.* lives on CK Postgres. Beast does NOT have CK PG credentials. atlas SSHes to CK + runs `/usr/bin/python3 -c <inline-source>` with system psycopg2; the inline source reads mercury's existing .env DATABASE_URL on CK; auths locally; prints JSON of first row to stdout. `shlex.quote()` handles shell-escaping of multi-line Python source. **Credential never propagates to Beast.** End-to-end prototype validated before authoring (returned correct mercury.trades summary).

**Fail-closed safety bias** for capital-protection gate: when cross-host query fails OR ratification check fails, `mercury_real_money_failclosed` raises critical with kind=`mercury_failclosed_check_error` (distinct from `mercury_real_money_unauthorized` for the actual-real-money case). Three failure modes mapped to two distinct alert kinds.

**3 cadenced + 2 stub functions:**
- `mercury_liveness_check`: every 5min; SSH CK + systemctl is-active; Tier 3 critical if NOT active
- `mercury_trade_activity_check`: daily 08:00 UTC; cross-host PG read; Tier 2 warn if scanner active but no trades in 7d
- `mercury_real_money_failclosed`: every 5min continuous gate; Tier 3 immediate unless ratification doc present
- `mercury_start` / `mercury_stop`: STUB at v0.1 (Paco-preferred option a); TODO Phase 7 cancel-window via communication.py

**Standing Gates 6/6 preserved** including mercury.trades bit-identical (zero atlas-side mutations -- smoke used monkey-patches) and ratification doc still ABSENT (canonical baseline).

---

## 2. Phase 6 implementation

### 2.1 File inventory

| File | Bytes | Purpose |
|---|---|---|
| `src/atlas/agent/domains/mercury.py` | 15,343 | Domain 4 module: 5 public funcs + 4 private helpers (NEW; post-redact) |
| `src/atlas/agent/scheduler.py` | 8,380 | UPDATED: 3 mercury imports; 2 constants (CADENCE_MERCURY_S=300; MERCURY_TRADE_HOUR_UTC=8); 3 dispatch blocks |

Total: +402 lines.

### 2.2 mercury.py architecture

**Cross-host helper `_ck_python_query(sql, timeout=15.0) -> Optional[dict]`:**
- Templates `_CK_PY_TEMPLATE` with the SQL via `repr()` (safe quoting of static module-level constants)
- Wraps full Python source in `shlex.quote()` for shell-escape safety
- Invokes via `_ssh_run(CK_HOST, CK_USER, f'/usr/bin/python3 -c {quoted}')`
- Parses JSON stdout into Python dict
- Returns None on rc != 0 OR JSON parse failure (with logging)
- The inline Python source on CK: parses mercury .env line-by-line, connects via psycopg2, executes the query, prints first row as JSON. **Reads mercury's existing credential; never propagates to Beast.**

**Helper `_check_ratification_doc() -> Optional[bool]`:**
- SSH to CK + `test -f <canonical-path>` + echo PRESENT/ABSENT
- Returns True/False/None (None on SSH error -- caller treats as ABSENT for fail-closed bias)

**Helper `_mercury_is_active() -> tuple[bool, str]`:**
- SSH to CK + `systemctl is-active mercury-scanner.service`
- Returns (True, 'active') if scanner active; (False, raw_state) otherwise

**`mercury_liveness_check(db)`** -- 5min cadence; Tier 3 critical if NOT active; per-day dedup

**`mercury_trade_activity_check(db)`** -- daily 08:00 UTC; only fires when scanner is active (composes with liveness); Tier 2 warn if recent_count == 0; per-day dedup

**`mercury_real_money_failclosed(db)`** -- 5min continuous gate:
- Real query result is None -> Tier 3 critical with kind=`mercury_failclosed_check_error` (fail-closed safety bias)
- real_count == 0 -> silent (gate naturally satisfied)
- real_count > 0 + doc PRESENT -> silent (CEO ratification suppresses)
- real_count > 0 + doc ABSENT or check failed -> Tier 3 critical with kind=`mercury_real_money_unauthorized`
- Per-day dedup with fail-open

**`mercury_start(db)` / `mercury_stop(db)`** -- v0.1 stubs; log-only no-op; TODO Phase 7 implements real start/stop with cancel-window via communication.py emit_event.

### 2.3 scheduler.py wiring (Phase 6 additions)

- `CADENCE_MERCURY_S = 300` -- 5 minutes for liveness + real-money
- `MERCURY_TRADE_HOUR_UTC = 8` -- daily for trade activity
- 2 interval dispatch blocks (liveness + real_money) -- same shape as vitals/uptime/anchor
- 1 daily wall-clock dispatch block (trade_activity) -- same shape as talent_log + vendor_*
- `last_run` dict now has 11 keys (was 8 after Phase 5)

### 2.4 Discipline applied

- **P6 #32 reuse:** `_create_monitoring_task` + `_ssh_run` from infrastructure; `_alert_already_today` from vendor. Zero re-implementation.
- **P6 #29 verified at write:** CK Python version + psycopg2 availability (mercury venv search came up empty -- mercury runs system Python; system has psycopg2 not psycopg v3); ratification doc absence baseline; mercury .env parseability; end-to-end prototype validated.
- **P6 #20 deployed-state names:** CK_HOST=192.168.1.10; MERCURY_SERVICE=mercury-scanner.service; MERCURY_ENV_PATH=/home/jes/polymarket-ai-trader/.env; RATIFICATION_DOC_PATH=/home/jes/control-plane/docs/mercury_real_money_ratification.md -- all verified live.
- **No new dependencies:** stdlib `shlex` for cross-host shell-escape; `json`+`datetime`+`logging`+`typing` already in use. No paramiko/asyncssh; no psycopg-on-Beast.
- **All probes READ-ONLY:** SSH systemctl status read; SQL SELECTs only; `test -f` for ratification doc; never mutate mercury data, mercury config, or ratification doc state.
- **Fail-closed safety bias** for capital-protection gate -- explicitly tested in smoke H (cross-host query=None still raises critical).
- **Tier 3 distinct kinds** -- `mercury_real_money_unauthorized` (Mercury actually went rogue) vs `mercury_failclosed_check_error` (atlas can't reach CK to verify). Sloan can distinguish failure modes.

---

## 3. Smoke test transcript

```
=== Phase 6 smoke test (start=2026-05-02T08:40:58.784311+00:00) ===
PRE: mercury_alerts_in_window=0

[A] PASS: 0 alerts (Mercury active)
[B] PASS: 0 alerts (recent trades present)
[C] PASS: 0 alerts (gate naturally satisfied; real_count=0)
[D] PASS: 1 critical alert with systemctl_state=inactive
[D2] PASS: dedup held (1 alerts; no new)
[E] PASS: 1 warn alert (recent_7d=0, total=152, latest=2026-04-24 12:00:00+00)
[F] PASS: 1 critical unauthorized (real_count=5, doc=absent)
[G] PASS: 0 new alerts (CEO ratification suppresses gate; still 1 from F)
[H] PASS: 1 critical check_error (fail-closed safety bias)

[CLEANUP] deleted 4 smoke-test alert rows
POST: mercury_alerts=0 (zero leak)

=== ALL TESTS PASS ===
```

9/9 assertions PASS:
- Real baseline (3): liveness/trade_activity/real_money_failclosed all silent on healthy production state
- Synthetic alerts via monkey-patch (5): liveness inactive (critical), 8d trade gap (warn), real_money unauthorized (critical), gate-satisfied path (silent), check_error fail-closed (critical)
- Idempotency (1): liveness dedup held on rerun

**Zero CK mutations throughout:** smoke used monkey-patch of `_mercury_is_active`, `_ck_python_query`, `_check_ratification_doc` rather than INSERT/DELETE on mercury.trades or touch/rm on ratification doc. Both CK postgres state and CK filesystem state untouched.

---

## 4. Standing Gates 6/6 PRESERVED

| Gate | Description | PRE | POST | Status |
|---|---|---|---|---|
| SG1 | Standing-rule discipline applied (P6 #29 + #32 reuse + Path B refined ratified mid-phase + secrets-scan catch + redact discipline) | -- | applied throughout | ✓ PASS |
| SG2 | B2b publication untouched | postgres anchor `2026-04-27T00:13:57.800746541Z` | identical | ✓ PASS |
| SG3 | Garage cluster untouched | garage anchor `2026-04-27T05:39:58.168067641Z` | identical | ✓ PASS |
| SG4 | atlas-mcp.service untouched | active MainPID 2173807 enabled since 2026-05-01 22:05:42 UTC | identical | ✓ PASS |
| SG5 | atlas-agent.service disabled inactive (Phase 9 territory) | inactive disabled MainPID 0 | identical | ✓ PASS |
| SG6 | nginx vhosts on CK + mercury-scanner.service + ratification doc | mercury active MainPID 643409; mercury.trades total=152 real=0; doc ABSENT | identical (zero atlas-side mutations) | ✓ PASS |

Substrate anchors held bit-identical for ~96+ hours through 9 Atlas cycles + Phases 0-6 work.

---

## 5. Pre-commit security catch (notable mid-phase event)

**What happened:** While authoring mercury.py, I included a docstring "P5 candidate weak credential note" that quoted the literal Mercury password (`'adminpass'`) as part of the security observation. This embedded the credential in the about-to-be-committed source.

**How caught:** Pre-commit broad-grep secrets scan (`grep -iE 'key|token|secret|password|api'`) flagged the line. The tightened scan (`api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+|authorization:`) **would have missed** the `adminpass` literal -- it doesn't match any of those patterns. The broad scan was the catch layer.

**Resolution:** STOPPED before commit. `sed -i` redacted to generic phrasing ('a weak password embedded inline'). Verified `grep -c 'adminpass' = 0`. Re-staged. Both broad + tightened scans clean. Proceeded with commit at SHA `10adf9f`.

**Commit message includes a transparency line:** "Pre-commit security note: broad secrets-scan caught a literal credential in docstring (P5 finding documentation cited the actual password value); redacted to generic language before commit."

---

## 6. Notable

- **First-try acceptance PASS** (third consecutive after Phase 4 + 5).
- **Most architecturally complex phase yet:** new cross-host pattern (SSH+inline-Python+JSON-stdout); credential-free read; fail-closed multi-mode safety bias.
- **Path B refined ratified by CEO mid-Step-1:** Step 1 surfaced 3 architectural decisions (cross-host PG, atlas .env latent blocker, ratification doc path); CEO chose Path B + proceed + Path B; PD then proceeded to Step 2 (originally wrote mercury.py at Step 3 in re-numbered plan).
- **Pre-commit secrets-scan caught real credential exposure** -- documented in Section 5; commit line in message; P6 #34 candidate proposal in Section 7.
- **Zero CK mutations during smoke** -- monkey-patch pattern replaces INSERT/DELETE on mercury.trades (which would have been a Mercury production data touch, even temporarily). Cleanest possible test methodology for mercury domain.

---

## 7. P6 #34 candidate proposal

**Statement:** Documentation about credentials must describe the issue without including the credential value. When authoring a docstring or commit message that flags a weak/leaked/expiring credential, the safe form is generic phrasing ('a weak password embedded inline', 'short PAT length', 'expires within N days'), NOT the literal value. The literal lives only in incident-response private channels (encrypted DM, secrets manager, ratification audit log), never in committed source.

**Distinction from P6 #20-32:** prior P6 entries cover authoring errors where the author was wrong about state (deployed-state names, API symbols, behavioral patterns, entire mental models). P6 #34 covers a different failure mode: the author is RIGHT about state (the credential really is weak) but documents it WITH the credential value, propagating exposure to a new location even though the original exposure already exists elsewhere.

**Originating context (Phase 6 mercury.py docstring):** Authored "Weak credential note (P5 candidate): Mercury .env on CK contains DATABASE_URL with literal 'adminpass' password" -- the literal value 'adminpass' is the actual production credential. Pre-commit broad-grep secrets-scan caught it. Tightened scan would have missed it. Redacted to 'a weak password embedded inline' before commit.

**Mitigation pattern:**
1. When flagging a credential issue in code: describe what's wrong (length, weakness, exposure path, expiry) without the value
2. Reference the canonical incident location (e.g. "per Atlas v0.1 Phase 6 Step 1 verification") rather than embedding the value
3. Pre-commit broad-grep secrets-scan stays in the discipline as defense-in-depth (tightened scan alone misses this class)

**Cumulative count if accepted:** P6 lessons banked = 34 (was 33 at Phase 3 close; +1 #34 here Phase 6 close).

---

## 8. Asks for Paco

1. Confirm Phase 6 1/1 acceptance criterion PASS post-smoke (9/9 sub-assertions including 3 real baseline + 5 synthetic + 1 idempotency).
2. Confirm Standing Gates 6/6 preserved (including mercury.trades bit-identical across 6 phases now).
3. Ratify Path B refined cross-host architecture as standing pattern (atlas SSHes to CK + runs inline Python+psycopg2; credential never propagates to Beast). This is the canonical cross-host PG read pattern for any future cross-host atlas reads (e.g. if Mr Robot under Charter 7 needs cross-host data on SlimJim).
4. Ratify P6 #34 candidate (documentation-about-credentials-without-credential-value).
5. Authorize Phase 7 GO (Communication helper -- atlas.events writes + Telegram dispatch). Open spec questions: (a) does Phase 7 also implement the canonical create_event helper that v0.1.1 will need (per atlas.tasks-as-proxy substrate-gap from Phase 3), or stays deferred? (b) Tier 2 cancel-window mechanism for mercury_start/stop -- Phase 7 wires this OR Phase 7+ follow-up.
6. P5 candidate (Atlas v0.1.1): Mercury weak credential rotation + read-only mercury_reader role.

---

## 9. State at close

- atlas HEAD: `10adf9f7e3a89aeb2cad86b65b14bfa11e925b9c` (Phase 6 commit; advanced from `af8768d`)
- atlas-mcp.service: active, MainPID 2173807, ~10h+ uptime (Standing Gate #4 holding through Phases 0-6)
- atlas-agent.service: loaded inactive disabled (Phase 1 acceptance state preserved through Phases 2-3-4-5-6)
- mercury-scanner.service: active, MainPID 643409 (Standing Gate #6; Mercury continues paper-trading)
- Substrate anchors: bit-identical 96+ hours
- mercury.trades: total=152 paper=152 real=0 (zero atlas-side mutations across full Phase 6 work)
- Ratification doc: ABSENT at canonical CK path (canonical baseline preserved)
- atlas.tasks state: 0 mercury alerts (smoke cleanup verified); Phase 3 monitoring rows continue to accrue per scheduler
- atlas /home/jes/atlas/.env: empty file created (Phase 9 latent EnvironmentFile blocker neutralized)

## 10. Cycle progress

7 of 10 phases complete. Pace clean. 3 phases remain (Communication helper + Tests + Production deployment + Ship report).

```
[x] Phase 0  Pre-flight verification (7/7 PASS post-retry)
[x] Phase 1  systemd unit (3/3 PASS first-try)
[x] Phase 2  Agent loop skeleton (1/1 PASS first-try post-amendment)
[x] Phase 3  Domain 1 Infrastructure monitoring (1/1 PASS post-bug-fix)
[x] Phase 4  Domain 2 Talent operations (1/1 PASS first-try)
[x] Phase 5  Domain 3 Vendor & admin (1/1 PASS first-try; 8/8 smoke; first migration)
[x] Phase 6  Domain 4 Mercury supervision (1/1 PASS first-try; 9/9 smoke; cross-host Path B refined; capital-protection fail-closed; secrets-scan catch P6 #34 candidate)
[~] Phase 7  Communication helper (NEXT -- atlas.events + Telegram + cancel-window for Phase 6 mercury_start/stop)
[ ] Phase 8  Tests
[ ] Phase 9  Production deployment (enable + start atlas-agent.service)
[ ] Phase 10 Ship report
```

-- PD (Cowork; Head of Engineering)
