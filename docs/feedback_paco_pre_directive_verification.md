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
