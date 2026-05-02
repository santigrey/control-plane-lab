# feedback_paco_pre_directive_verification

**Banked:** 2026-04-30 / Day 75
**Originated:** Atlas v0.1 Cycle 1A preflight ESC + CEO discipline RFC after 3 consecutive Paco-side spec errors in 24-72 hours
**Companion to:** feedback_directive_command_syntax_correction_pd_authority.md, feedback_paco_review_doc_per_step.md, feedback_paco_pd_handoff_protocol.md, feedback_phase_closure_literal_vs_spirit.md
**Memory file count after this banking:** 5

## Purpose

Define the discipline gate that prevents Paco from authoring spec/directive content from a mental model rather than from verified runtime state. Three consecutive Paco-side spec errors (P6 #17, P6 #19, P6 #20) within 72 hours surfaced this as the dominant Paco-side failure class. Going forward, this rule is mechanical: it is impossible for Paco to author a compliant directive without the verification step landing in the directive itself.

## Root cause this rule addresses

Across P6 #17 (Grafana env var single vs double underscore), P6 #19 (compose long-syntax swarm-only), and P6 #20 (Atlas spec named fictional database `alexandra_replica` + role `replicator_role` + wrong Garage URL `:3900`), the underlying mechanism is identical: **directive content authored from a mental model of "what the system probably looks like" rather than from verified runtime state, when the verification was one tool call away.**

Each error was caught at runtime by PD's discipline cycle. That works but is wasteful: every error costs one paco_request roundtrip + one paco_response + one corrected handoff, plus PD's preflight time and Paco's ruling time. At scale across Atlas v0.1's ~25 phases, this pattern would compound into days of avoidable escalation.

This is not an adaptive thinking failure. Adaptive thinking is what produced the rulings, the ESC framings, and the spec architecture. The failure is at the *discipline* layer: noticing that "I'm about to write a deployed-state name" should trigger a mechanical verification before authoring.

## Three-layer rule

### Layer 1 -- Mandatory pre-spec verification block (mechanical gate)

Every spec or directive Paco authors that references deployed state must include a **"Verified live"** section before any directive text. This section captures the actual commands run + their outputs + the date.

If the section is empty, missing, or stale (older than the current session), the directive is non-compliant and PD's first read-check rejects it.

Required content categories that trigger the verification gate:
- Database names, role names, schemas, table names
- URLs, ports, hostnames, listener bindings
- File paths, compose service names, container names
- Environment variable names (especially upstream-product conventions)
- Compose feature usage (especially long-syntax fields, deploy.* blocks, mode-gated features)
- Bucket names, object key conventions, storage paths
- Tailscale node names, IP allocations
- systemd unit names, service dependencies
- Secrets file locations, credential conventions

Required verification commands per category include but are not limited to:
- DB names + roles: `docker exec <pg-container> psql -U <admin> -c '\du'` and `'\l'` and `SELECT * FROM pg_subscription`
- URLs/ports: `ss -tlnp | grep <port>` on the actual host AND verify against compose.yaml on disk
- Bucket names: query the actual S3/Garage backend
- Tailscale state: `tailscale status` on the host
- File paths: `ls -la <path>` on the host
- Env var names: read upstream documentation OR existing config that's known-working

Required format of the "Verified live" section:

```markdown
## Verified live (YYYY-MM-DD Day N)

| Category | Command | Output |
|----------|---------|--------|
| <name> | `<command>` | <output summary> |
| ... | ... | ... |

Verification host: <host>
Verification timestamp: <ISO 8601>
```

This format makes the verification auditable. PD can re-run any command to confirm the named state.

### Layer 2 -- System prompt enhancement (reminder layer)

Paco's system prompt receives the discipline language as an operating rule. CEO action -- Paco cannot self-modify the system prompt. The exact text is drafted by Paco for CEO to paste into Claude project preferences (Action 2 of CEO discipline RFC Day 75).

The prompt language is intentionally concrete (not aspirational) and has no carve-outs. The pattern of error is precisely Paco being "sure" of the state, so the rule applies even to "trivial" cases.

### Layer 3 -- Adversarial self-check (cognitive layer)

Before dispatching any directive (writing to handoff_paco_to_pd.md), Paco runs an internal pre-mortem:

1. What deployed-state names did I just write? (DB / role / URL / port / path / env var / compose feature)
2. Did I verify each one live this turn or read it from a recently-verified source within the same session?
3. What upstream-product mechanisms am I assuming work the way I remember?
4. What's the worst case if any of those assumptions are wrong? (Usually: PD escalates, ~30 minutes lost.)
5. Is the verification cost lower than the worst case? (Almost always yes -- verification is seconds; escalation is minutes-to-hours.)

If question 5 yields "yes, verify before dispatch," verify before dispatch. The rule is "verify when cheaper than the worst case." It's almost always cheaper.

## When this rule does NOT apply

- Casual conversation with CEO that is not a directive
- Architectural discussion that doesn't reference specific deployed state
- Reasoning about hypothetical future state (e.g., "if we added X")
- Reading existing canonical docs (the docs themselves are presumed verified at write time)
- Quoting from prior verifications within the same session (e.g., "per pg_subscription query at 14:30 today")

## When this rule DOES apply (default assumption)

Every spec, every cycle, every phase, every directive text that names actual deployed-state values. If unsure, verify. The cost is seconds.

## Required documentation in directives that pass the gate

The "Verified live" section is structural. PD reads it first. Any subsequent directive text that names deployed state must be traceable back to a row in the Verified live table.

If a directive amends prior spec text and the amendment changes deployed-state names, the Verified live section must be re-run for the new names.

## Why this rule has teeth

- Layer 1 is mechanical: a missing or stale Verified live section is a structural failure of the directive that PD catches at first read, not after preflight execution.
- Layer 2 is persistent: every time Paco picks up the conversation, the system prompt re-enforces the rule.
- Layer 3 is adversarial: the pre-dispatch self-check is a forced friction point that interrupts memory-shaped output.
- All three together cover the failure modes: mechanical gate catches forgotten verification; reminder layer prevents drift; adversarial check catches "I'm sure of this" overconfidence.

## Why this rule does NOT slow Paco down meaningfully

Per category verification cost:
- DB/role names: ~5 seconds per `psql -c` query
- URL/port verification: ~5 seconds per `ss -tlnp` query
- File path verification: ~3 seconds per `ls -la`
- Env var convention: ~30 seconds per upstream doc fetch (rare, only when introducing new upstream product)

Per directive: ~30-60 seconds of verification overhead. Per Atlas v0.1 build: ~25 phases * 60s = ~25 minutes total. Compared to ~30-60 minutes per escalation roundtrip and we've already seen 4 ESCs in Atlas Cycle 1A alone, this is a massive net positive.

## Self-acknowledgment of the pattern

Three errors in 24-72 hours:
- 2026-04-29 Phase E: Grafana env var `_FILE` vs `__FILE` (single vs double underscore) -- transcribed from memory, no upstream verification
- 2026-04-29 Phase G: compose long-syntax `uid/gid/mode` swarm-only -- assumed mode-compatibility without verification
- 2026-04-30 Atlas Cycle 1A: fictional `replicator_role` + `alexandra_replica` + Garage `:3900/health` -- mental-model names, no live verification

Underlying cause across all three: directive authored before verification, not after. PD's runtime discipline caught all three. The system worked. The cost was measurable: ~3 paco_request roundtrips, ~3 hours of Paco-PD-CEO time across the three. Without this rule, the Atlas v0.1 build would generate ~10-15 more such errors over the next ~5 weeks. With this rule, that count drops to near zero.

## Cross-references

- Companion rules: 4 prior memory files in `/home/jes/control-plane/docs/`
- Banked from: CEO discipline RFC Day 75 + Atlas Cycle 1A preflight ESC ruling
- Originating P6 lessons: #17 (env var conventions), #19 (compose mode-compat), #20 (deployed-state-name verification)
- Related: 5-guardrail rule (PD's runtime discipline that has been catching Paco's errors)

## Standing rule status

ACTIVE from 2026-04-30 Day 75 forward. Applies to all Paco-authored directives across all charters and build cycles. No carve-outs.

Periodic CEO evaluation per Day 75 ratification: "approved on all three then we evaluate as needed." If the rule produces excessive friction without proportional error-prevention, CEO can revise. Default measurement window: end of Atlas v0.1 Cycle 1 close (one full cycle). If P6 #17/#19/#20-class errors continue at the same rate, the rule isn't working and needs revision. If they drop to zero, the rule is working and stays.

---

## P6 Lessons banked from Cycle 1F transport saga (Day 76)

### P6 #21 -- tcpdump-on-lo for client-server impedance

When client-server impedance hangs initialize, capture both sides headers via tcpdump on lo (loopback interface between nginx and the local backend). 5-minute root-cause vs hours of speculation. Demonstrated value in Phase C.1 P1.c.

### P6 #22 -- PD diagnostic verdicts must validate end-to-end against runtime path

Diagnostic verdicts on transport/protocol issues MUST be validated end-to-end against the actual runtime path before issuing a build directive. Curl-loopback probes are not sufficient evidence for SDK+HTTPS+nginx claims. Phase C.1 verdict declared header is the fix based only on curl loopback HTTP; Pacos CP1-CP5 counter-probes caught the gap. The end-to-end question did we test the actual code path Atlas will use must be answered yes.

### P6 #23 -- Verify launch mechanism before authoring restart commands

Verify launch mechanism (systemd vs nohup vs screen vs supervisord) BEFORE authoring restart commands. PPID=1 + systemd unit existence is a 10-second probe (`ps -o ppid -p PID`; `find /etc/systemd -name *service*`). Phase C.2.0 recommendation said relaunch via nohup -- would have orphaned the process while systemd auto-restarted its own copy, creating chaos. Pacos Phase 3 directive Verified live caught it at directive-author time.

### P6 #24 -- Recursive observer effect during long-running diagnostics

When attaching diagnostic tools (py-spy, strace, tcpdump) to a long-running production server, account for the recursive observer effect. Pacos homelab_ssh_run calls during Phase C.1 diagnostic were themselves the in-flight blockers that made Phase C.1s probes hang. py-spys catching the same handler in 3 sequential dumps was partially because Paco was actively driving probe traffic. PDs Step 7 pretest flake reproduced under heavy Paco MCP traffic; in 3 controlled reruns it disappeared. Diagnostic methodology should isolate active observer load (e.g., pause tool calls for the diagnostic window OR attribute observed blocking to the observers own calls).

### P6 #25 -- Hedge propagation discipline

When directive-author hedges with placeholder language (any Nth item I missed during grep -- verify count via final grep), the hedge MUST propagate into all downstream gate text and acceptance criteria, not just the enumeration section. If the hedge is in section 2.3 but the gate text in section 11 is hardcoded, the contingency clause is incomplete. Better practice: re-count cleanly at directive-author time, OR make the gate text reference the live count. Two instances banked Day 76: handler count 14 vs 13 actual; Step 7 prior-test count 16 vs 15 actual. Both same root cause (memory-assertion vs ground-truth grep).

### P6 #26 -- All Paco<->PD events write notification line in handoff_pd_to_paco.md

ALL Paco<->PD events (paco_request escalation, paco_review phase close, mid-cycle checkpoint, anything requiring Paco/CEO attention) MUST write a notification line in handoff_pd_to_paco.md so the CEO trigger remains a single canonical phrase Paco check handoff regardless of event type. CEO should never have to compose triggers with filenames or event hints; PDs notification carries that context. Notification line minimum content: event type, filename, one-line summary of Paco action expected, spec context (Cycle/Phase/Step).

All six are direct applications of 5th standing rules principles. Cumulative count: P6 lessons banked = 26.

## P6 #27 -- Telemetry intelligibility invariant (Cycle 1F belated bank)

**Banked:** 2026-05-01 UTC (Day 77) -- carried forward from Cycle 1F close-confirm `paco_response_atlas_v0_1_cycle_1f_close_confirm.md` Section 5 (commit `3baa455`); appended to this file in Cycle 1G close-out fold per Paco directive.

**Statement:** When a client introspects schema and applies caller-transparent transformations (auto-wrap, format conversion, default-injection), telemetry MUST capture the **caller-provided** form of inputs BEFORE transformation. This preserves intelligibility for downstream consumers (audit logs, debug traces, anomaly detection) while letting the wire-format stay schema-compliant. Capture happens at the function boundary, before any internal transformation.

**Originating context:** Refinement 3 of Option B for Cycle 1F atlas.mcp_client (caller_arg_keys captured before auto-wrap). Verified live at Cycle 1F close: `arg_keys=["command", "host"]` in atlas.events for tool_call rows, NOT `["params"]` (which would be the post-wrap form). Pattern works as designed and generalizes to any future schema-aware wrapper across Atlas (e.g., Atlas inbound MCP server, future RAG retrieval gateway, future inference-side schema adapters).

**Application pattern:** Every function that does caller-transparent transformation should:
1. Capture caller-provided form FIRST (`caller_arg_keys = sorted(args.keys())` or equivalent)
2. Apply the transformation
3. Write to wire / send / call upstream with the transformed form
4. Emit telemetry with the captured caller-provided form (NOT the transformed form)

This composes cleanly with the secrets-discipline invariant (capture KEYS not VALUES; both invariants are upheld at the same capture point).

## P6 #28 -- Reference-pattern verification before propagation (Cycle 1G this turn)

**Banked:** 2026-05-01 UTC (Day 77) per Paco's response `paco_response_atlas_v0_1_cycle_1g_uvicorn_host_validation.md` Section 3 Ask 5 (commit `4f045e4`).

**Statement:** When a directive references an existing pattern ("matches X", "mirrors X", "uses Y's approach"), the existing pattern's ACTUAL state MUST be Verified live BEFORE the directive is dispatched -- not asserted from memory of how the pattern was originally designed or how the author remembers it working.

**Distinction from P6 #20:** P6 #20 covers deployed-state NAMES (database names, role names, URLs, paths). P6 #28 covers BEHAVIORAL PATTERNS (binding modes, header propagation, middleware presence, security postures). Both fail the same way -- assertion from memory when verification is cheap -- but they involve different probe types:
- P6 #20 probe: `psql -c '\\du'`, `ss -tlnp`, `ls -la`
- P6 #28 probe: `cat <config-file>`, behavioral test (curl with specific Host header), `systemctl show <unit>` for ExecStart, etc.

**Originating context (Cycle 1G):** handoff Section 7 said: "Note: bind to 127.0.0.1 (loopback ONLY), not 0.0.0.0. nginx is the only external access path. **This matches CK's pattern (homelab-mcp also loopback-bound and nginx-fronted).**" Verified live at PD Step 11 escalation: CK's `mcp_http.py` actually contains `uvicorn.run(mcp.streamable_http_app(), host='0.0.0.0', port=8001)`. CK is **0.0.0.0-bound**, not loopback. Verifying-live would have been `cat /home/jes/control-plane/mcp_http.py | grep host=` or `ss -tlnp | grep :8001` on CK -- 3 seconds. Cost of skipping: one full Cycle 1G build-execution cycle to surface the conflict at Step 11 smoke time (HTTP 421 Misdirected Request from uvicorn h11 layer rejecting Host header).

**Mitigation pattern:** when authoring "matches X" claims in directives, the directive author runs a quick reference-state probe and pastes the actual config snippet/output into the Verified live block. Future directives that reference patterns get a Verified-live row that pins what the pattern actually IS at directive-author time.

**Resolution at Cycle 1G:** Option A (nginx Host rewrite to `127.0.0.1:8001` + X-Forwarded-Host enhancement) ratified. Atlas's strict-loopback bind is the BETTER security posture; CK's 0.0.0.0 was likely a historical accident, and CK migrates in v0.2 P5 #20.

## Cumulative

All seven (#21 through #28) are direct applications of 5th standing rule's principles. Cumulative count: **P6 lessons banked = 28** (was 26 at end of Cycle 1F; +1 #27 telemetry intelligibility, +1 #28 reference-pattern verification).


## Standing Rule #6 -- Paco self-state verification before conclusion-drawing

**Banked:** 2026-05-01 UTC (Day 77) per CEO discipline RFC after Paco self-state-blindness incident at Cycle 2A close.

**Statement:** Before declaring "X didn't happen," "X is broken," "no work occurred," "PD didn't act," or any conclusion that PD/another actor failed to advance state, Paco MUST run a 1-tool-call self-state probe FIRST:

```bash
cd /home/jes/control-plane && git log --oneline -5 && stat -c '%y %s %n' docs/handoff_*.md
```

This tells Paco:
- HEAD position (has it advanced past the last Paco commit?)
- Last write time on `handoff_paco_to_pd.md` (does it have substantial content from a recent turn?)
- Last write time on `handoff_pd_to_paco.md` (placeholder = post-Paco-reset; substantial content = unread PD notification)

**Decision tree after the probe:**

1. If HEAD has advanced past Paco's last known commit AND the new commit is by Paco -> "I shipped this; the trigger is asking me to look at my own work." Read what I just shipped, confirm coherence, respond to CEO with status.
2. If HEAD has advanced past Paco's last known commit AND the new commit is by PD -> PD acted. Read `handoff_pd_to_paco.md` for notification, then read the new file PD created.
3. If HEAD hasn't advanced AND `handoff_paco_to_pd.md` has substantial recent content -> Paco wrote a directive but no actor consumed it yet. Likely a trigger misfire on CEO's end; ask before assuming inaction.
4. If HEAD hasn't advanced AND `handoff_paco_to_pd.md` is empty -> trigger misfire OR PD blocked silently. Tell CEO; do not invent activity.
5. If HEAD hasn't advanced AND `handoff_pd_to_paco.md` has unread PD notification -> read it; this is the case the trigger was for.

**Originating context:** At Cycle 2A close, Paco shipped a 16,400-byte ruling + 27,473-byte build directive + reset placeholder + commit `c3ede72` + push. Then a follow-up trigger arrived (CEO repeating the same escalation trigger). Paco read `handoff_pd_to_paco.md` (the placeholder Paco had just reset), saw it was placeholder content, and concluded "PD didn't do anything" -- treating Paco's own completed work as evidence of inaction. Cost: erosion of CEO trust + 1 unnecessary diagnostic turn + Paco self-criticism cascade. The probe Paco needed was `git log --oneline -3` -- 1 tool call, would have shown HEAD `c3ede72` was Paco's own commit and the question was "look at your own work," not "diagnose missing work."

**Why this rule has teeth:**
- **Mechanical**: probe runs first, before any narrative interpretation
- **One tool call**: cost is seconds; the alternative is wasting CEO time and eroding protocol trust
- **Distinct from P6 lessons**: P6 covers Paco's authoring patterns; SR #6 covers Paco's conclusion-drawing patterns
- **Symmetric to PD's Verified-live discipline**: PD verifies live before authoring; Paco verifies state before concluding. Same family.

**When this rule applies:** every trigger arrival from CEO that frames PD's state ("PD finished", "PD escalated", "PD blocked"). Run the probe. THEN respond.

**When this rule does NOT apply:** casual conversation, architectural discussion, novel-state-establishment turns where there's no PD activity to evaluate.

**Cumulative standing rules: 6** (was 5; +1 SR #6 self-state verification before conclusion-drawing).

---

## P6 #29 -- API symbol verification before reference (Cycle 1H this turn)

**Banked:** 2026-05-01 UTC (Day 77) per Paco's response `paco_response_atlas_v0_1_cycle_1h_close_confirm.md` Section 2 Ask 3.

**Statement:** When a directive sketches code that imports/calls/references a function, class, or module symbol from an existing codebase (`from atlas.embeddings import embed_single`, `await self._log_event(...)`, etc.), the symbol's existence + signature must be Verified live BEFORE the directive is dispatched -- not asserted from memory of how the API was originally designed or how the author remembers it.

**Distinction from P6 #20 + P6 #28:**
- P6 #20 covers deployed-state NAMES (database names, role names, URLs, paths). Probe: `psql \\du`, `ss -tlnp`, `ls -la`.
- P6 #28 covers BEHAVIORAL PATTERNS (binding modes, header propagation, middleware presence, security postures). Probe: `cat <config-file>`, behavioral test, `systemctl show <unit>`.
- P6 #29 (NEW) covers API SYMBOL EXPORTS (function/class names from modules, method signatures, return types). Probe: `grep -nE '^(def|class|async def) <name>' <module.py>`, `python -c 'import X; print(dir(X))'`, IDE quick-reference.

All three fail the same way -- assertion from memory when verification is cheap -- but require different probe types. Naming them distinctly helps catch each pattern at its specific surface.

**Originating context (Cycle 1H build directive):** Paco's Step 4 sketch said `from atlas.embeddings import embed_single`. PD's Verified live during build authoring found the actual API is `get_embedder().embed(text)` returning `list[float]`. Cost of skipping: would have been an ImportError at first import attempt during Step 5 wiring. PD caught at directive-author time via 5-guardrail rule.

**Mitigation pattern:** when authoring code skeletons in build directives, the directive author runs `grep` on the actual module file or `python -c "from X import *; print(...)"` for any symbol referenced + paste the actual signature into the directive's Verified live block.

## Cumulative

All P6 #21 through #29 are direct applications of 5th standing rule's principles. Cumulative count: **P6 lessons banked = 29** (was 28 at end of Cycle 1G; +1 #29 API symbol verification before reference).

Standing rules: **6** (was 5; +1 SR #6 self-state verification before conclusion-drawing).


---

## P6 #31 -- Recurring third-instance confirmation of P6 #25 (directive-author hedge propagation): count/name claims from memory persist into specs (Day 78 morning bank)

**Banked:** 2026-05-02 UTC (Day 78 morning) per Paco's response `docs/paco_response_atlas_v0_1_phase0_unblock.md` Ruling 4.

**Statement:** When the directive author writes counts ("14 handlers", "16 tests") or names ("asyncpg", "the foo helper") from memory rather than verifying against the actual repo state, those claims propagate into the canonical spec and become PD's pre-execution verification load. Three confirmed instances Day 76-78 establishes this is a recurring pattern, not an isolated error.

**Three confirmed instances:**
1. Cycle 1F Phase 3 -- handler count claimed 14, actual 13 (paco_response `77759f8`)
2. Cycle 1F Phase 3 Step 7 -- prior-test count claimed 16, actual 15 (paco_response part of `eadc2e7`)
3. Atlas v0.1 Phase 0 spec -- dependency name claimed `asyncpg`, actual `psycopg[binary,pool]` (paco_response `docs/paco_response_atlas_v0_1_phase0_unblock.md`)

**Distinction from P6 #25:** P6 #25 named the pattern at first instance. P6 #31 confirms the pattern is recurring -- not a one-off Cycle 1F anomaly. The distinction matters because recurring patterns warrant standing-rule reinforcement, not just a flagged note.

**Mitigation pattern (becomes standing practice for spec authors):** Before claiming any count or name in a build spec, run the actual probe:
- Counts: `grep -c '^def ' <module>` for handler counts; `find <dir> -name 'test_*.py' | wc -l` for test counts
- Names: `cat pyproject.toml | grep -A 20 dependencies` for dep names; `psql \du` for role names; `\dn` for schema names; `systemctl list-units` for unit names
- File-existence claims: `ls -la <path>` BEFORE writing "the file at <path> contains..."

The probe takes 5 seconds. The error costs PD a paco_request escalation and one round-trip.

**Standing rule reinforcement:** PD's pre-execution verification under 5-guardrail rule + SR #6 catches every instance. The rule is the safety net; PD performing the safety net's job is correct discipline. Spec authors should not lean on PD as the verification layer -- spec authors should pre-verify so PD's verification is a confirmation, not a correction.

**Cross-reference:** P6 #25 (original instance), P6 #20 (deployed-state names), P6 #28 (behavioral patterns), P6 #29 (API symbols). All four are surface-specific applications of the same root rule: do not assert from memory when verification is one tool call away.

---

## P6 #32 -- Directive-author entire-API-mental-model from memory: spec code blocks need canonical-reference impl as source, not memory (Day 78 morning bank, 4th-instance escalation)

**Banked:** 2026-05-02 UTC (Day 78 morning) per Paco's response `docs/paco_response_atlas_v0_1_phase2_db_api_amendment.md` Ruling 3.

**Statement:** P6 #25/#31 named the count/name-from-memory pattern (single-symbol, mechanical fix). P6 #29 named the API-symbol-from-memory pattern (one symbol, one verification). P6 #32 names a deeper surface: when a directive author writes a complete code block in a build spec from a remembered API mental model, the result contains MULTIPLE distinct errors (API style + column names + type model + return shape) that compound. The mitigation cannot be "verify each symbol" (that scales linearly with the block); the mitigation must be "copy from canonical reference impl and adapt."

**Originating context (Atlas v0.1 Phase 2 spec):** Paco authored `tasks/atlas_v0_1_agent_loop.md` lines 195-230 (poller.py skeleton) using an asyncpg-style API mental model. Reality: atlas.db is psycopg-based per P6 #29 + Cycle 1I canonical at `atlas.mcp_server.tasks.claim_task` (commit `d383fe0`). PD pre-execution review caught FIVE distinct errors:
1. `from atlas.db import get_pool` -- atlas.db has no `get_pool`; canonical export is `Database`
2. `pool.acquire() + conn.fetchrow()` -- canonical is `db.connection() + cursor() + cur.execute() + cur.fetchone()`
3. `started_at=now()` -- column does not exist; canonical is `updated_at`
4. `completed_at=now()` -- column does not exist; canonical is `updated_at`
5. `RETURNING id, kind, payload, assigned_to` -- columns `kind` and `assigned_to` do not exist; `kind` lives inside payload jsonb (`payload->>'kind'`)

Cost of skipping verification: would have been 5 errors compounding into a stack trace at first `python -m atlas.agent` smoke test, requiring sequential debug + multiple retry cycles.

**Distinction from P6 #29 + #31:**
- P6 #29: single API symbol from memory (e.g. `embed_single` vs `get_embedder().embed`). Mitigation: grep one symbol.
- P6 #31: count or single name from memory (e.g. `14 handlers` vs 13; `asyncpg` vs `psycopg[pool]`). Mitigation: run the count/grep.
- P6 #32 (NEW): entire code-block API mental model from memory (multi-symbol + multi-column + multi-pattern compound). Mitigation: copy from canonical reference impl. The P6 #29 grep does not scale; the canonical-copy approach does.

**Originating context detail:** The Cycle 1I canonical pattern was already documented in `atlas.mcp_server.tasks` module docstring with exact P6 #29 reference: "DB API: uses atlas.db.Database psycopg-style API verified live per P6 #29: async with db.connection() as conn: async with conn.cursor() as cur: await cur.execute(sql, args) with %s placeholders, await cur.fetchall() / await cur.fetchone() returns tuples". The Phase 2 spec was authored without consulting this canonical pattern. The canonical reference EXISTED; the spec author simply did not reach for it.

**Mitigation pattern (becomes standing practice for spec authors writing code blocks):** Before authoring a code block in a build spec that interacts with an internal subsystem (atlas.db, atlas.embeddings, atlas.events, etc.), the spec author:
1. Identifies the canonical reference impl (the most recent, most-tested, P6-documented usage of that subsystem in atlas.* source)
2. Copies that impl verbatim into a scratch buffer
3. Adapts the SQL / business logic for the new context, keeping the API surface bit-identical to the canonical
4. Pastes the adapted result into the build spec

The probe takes 30 seconds (find the canonical impl + copy/adapt). The error costs PD a paco_request escalation + Paco a spec amendment + 5-error compound debug if not caught.

**Standing rule reinforcement:** PD's pre-execution verification under 5-guardrail rule + SR #6 catches every instance, INCLUDING this 4th instance. The rule is the safety net; PD performing the safety net's job is correct discipline. P6 #32 specifically applies to spec authors and asks them to pre-emptively close the gap before PD has to escalate.

**Cross-reference:** P6 #25 (original count/name memory pattern), P6 #20 (deployed-state names), P6 #28 (behavioral patterns), P6 #29 (API symbols), P6 #31 (recurring confirmation of P6 #25). All five are surface-specific applications of the same root rule: do not assert from memory when verification is one tool call away. P6 #32 is the most expensive surface (5-error compound) and warrants the most rigorous mitigation (canonical-copy, not symbol-grep).

## Cumulative (Day 78 morning, post-P6 #32)

All P6 #21 through #32 are direct applications of 5th standing rule's principles. Cumulative count: **P6 lessons banked = 32** (was 31 at start of Day 78 morning; +1 #32 here Day 78 morning Phase 2 escalation).

Standing rules: **6** (unchanged; SR #6 self-state verification before conclusion-drawing held through Day 78 morning).

Distribution by surface:
- Counts/names from memory: P6 #25 + #31 (4 instances total)
- Single API symbols from memory: P6 #29 (1 instance Cycle 1H)
- Deployed-state names from memory: P6 #20 (1 instance)
- Behavioral patterns from memory: P6 #28 (1 instance)
- **Entire API mental model from memory: P6 #32 (1 instance Day 78 morning Phase 2)** -- newest surface, highest cost-per-instance, requires canonical-copy mitigation
