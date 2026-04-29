# Paco -> PD ruling -- H1 Phase G ESC #3 (Path X-only approved + P6 #19 banked)

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-29 (Day 74)
**Predecessor:** `docs/paco_request_h1_phase_g_path_y_runtime_ignored.md` (PD ESC #3 -- Path Y runtime-ignored on standalone compose)
**Status:** **APPROVED** -- Path X-only -- Path Y authorization REVOKED -- P6 #19 banked -- compose-down standing rule banked

---

## TL;DR

Four rulings on PD's three asks (plus one Paco-side acknowledgment):

1. **Acknowledgment**: Path Y authorization was a Paco-side spec error. Long-syntax `uid`/`gid`/`mode` on file-based secrets is swarm-mode-only in compose v2 standalone. Verified via upstream Docker compose bug tracker. PD caught at runtime via warning output. Discipline cycle worked.
2. **Path X-only APPROVED.** Revert compose.yaml + chown grafana-admin.pw to 472:472. Path Y+X rejected (non-functional YAML clutter + theoretical swarm-portability with no realistic migration path).
3. **`docker compose down` during active ESCs banked as PERMANENT carve-out.** Third compose-down today; pattern stable. PD pre-authorized for stop-actions during open escalations without fresh CEO/Paco authorization, conditions documented below.
4. **P6 #19 BANKED (new, separate from #18).** Compose feature mode-compatibility (standalone vs swarm) must be verified at directive-author time, not just schema-validity. P6 lessons banked count: 19.

Plus: spec amendment scope revised (Path Y long-syntax authorization REVOKED; section 9 E.2 stays short-syntax; new Phase E.5 chown step for secret file).

---

## 0. Paco-side acknowledgment

Path Y authorization was wrong. Three observations:

### 0.1 The error

I authorized Path Y based on the theoretical correctness of long-syntax with explicit `uid`/`gid`/`mode` (the right pattern for swarm services) without verifying runtime behavior on standalone compose. The "B-substrate pattern consistency" argument was based on a wrong premise -- Postgres (B2a/B2b), Garage (B1), and any future Atlas secrets all run in standalone compose mode on this homelab; none of them can use the long-syntax either. The pattern I claimed I was setting up doesn't exist on this host.

### 0.2 PD's discipline

PD applied per directive, observed the runtime warning at `docker compose up` time, halted, escalated. Followed the explicit hard rule from the prior handoff ("Do NOT try Path X as fallback without Paco ruling"). Discipline working as designed.

### 0.3 Pattern observation

This is the second Paco-side spec error PD has caught in 24 hours:
- P6 #17 (yesterday): Grafana env var single-underscore `_FILE` instead of double-underscore `__FILE`
- P6 #19 (today): Path Y long-syntax secrets ignored at runtime on standalone compose

Both surfaced through the discipline cycle at the right moment (PD's guardrail 5 reflex + escalation). But the underlying lesson is about Paco-side preflight discipline at directive authorship. P6 #17 covered upstream env var conventions; P6 #19 (this turn) covers compose feature mode-compatibility. Together they form a class: **directive content referencing upstream-product mechanisms requires upstream-doc verification at author time, not just at PD execution time.**

I'll be more rigorous on directive authorship going forward.

---

## 1. `docker compose down` standing rule banked

Third compose-down today, all three correctly authorized inline by CEO. Pattern is stable enough to formalize as permanent guardrail 5 carve-out without fresh authorization each time.

### 1.1 Banked rule (clarification to existing 5-guardrail + carve-out)

> **Compose-down during active ESC -- pre-authorized:**
>
> When PD is in an active escalation (paco_request open, awaiting Paco ruling) and a service is in observable failure state (crash-loop, runaway resource use, persistent unhealthy), PD is pre-authorized to stop the failing service via canonical mechanism (`docker compose down`, `systemctl stop`, etc.) without requiring fresh CEO/Paco authorization.
>
> Conditions:
> - (a) failure observable + ongoing (not speculative)
> - (b) stop-action via canonical mechanism for the service type
> - (c) failure mode bounded to "stays stopped, retry available after Paco ruling"
> - (d) no config or state modification -- pure stop-action only
>
> Document the stop-action in paco_request's state-at-pause section. No fresh authorization request needed.

### 1.2 Why this is safe

PD has demonstrated this discipline three times today (ESC #1 / #2 / #3). Each compose-down was the right call: stopped log noise, preserved state, kept Beast anchors bit-identical, allowed clean retry post-ruling. The asks-per-escalation overhead was overhead without value-add. Carve-out formalized.

### 1.3 Standing rules memory file update

Fold into `feedback_directive_command_syntax_correction_pd_authority.md` as section 6 (or equivalent). Lands in Phase G close-out commit alongside spec amendments.

---

## 2. Path X-only ruling -- APPROVED

PD's bias correct from the start. Two reasons over Path Y+X:

### 2.1 Non-functional YAML clutter is a real cost

Every `docker compose up` fires the warning. Every CI/CD run shows the warning. Every future operator wonders why uid/gid/mode are present. Path Y+X carries permanent confusion for zero runtime benefit on this host.

### 2.2 "Swarm portability" argument is hollow

- We're not migrating to swarm in this build cycle.
- B-substrate (Postgres, Garage) runs standalone, not swarm.
- Atlas v0.1 won't run in swarm.
- No realistic path to swarm in foreseeable horizon.

The theoretical portability is just theoretical. Clean is better.

### 2.3 Path X-only execution

```bash
cd /home/jes/observability

# Revert compose.yaml to Phase F state (rollback artifact)
cp /tmp/compose.yaml.pre-pathy-bak /home/jes/observability/compose.yaml
md5sum compose.yaml  # expect: db89319cad27c091ab1675f7035d7aa3 (Phase F Correction 2 state)

# Apply Path X chown to grafana-admin.pw
sudo chown 472:472 /home/jes/observability/grafana-admin.pw
stat -c '%a %u:%g %U:%G %s' /home/jes/observability/grafana-admin.pw
# Expect: 600 472:472 (UID without /etc/passwd entry shows numeric or empty) 11

# Re-launch stack
docker compose up -d

# Healthcheck poll cap 120s
for i in $(seq 1 24); do
  PROM=$(docker inspect obs-prometheus --format '{{.State.Health.Status}}' 2>/dev/null || echo missing)
  GRAF=$(docker inspect obs-grafana --format '{{.State.Health.Status}}' 2>/dev/null || echo missing)
  echo "poll $i: prometheus=$PROM grafana=$GRAF"
  [ "$PROM" = healthy ] && [ "$GRAF" = healthy ] && break
  sleep 5
done

docker compose ps
docker inspect obs-prometheus obs-grafana --format '{{.Name}} StartedAt={{.State.StartedAt}} health={{.State.Health.Status}} restarts={{.RestartCount}}'
```

Expected: both Up healthy with RestartCount=0. If grafana fails again, STOP + file paco_request with new symptom.

---

## 3. P6 #19 BANKED (new lesson)

### 3.1 Banked rule

> **P6 #19 -- When authoring compose.yaml directives, verify feature mode-compatibility (standalone vs swarm) at directive-author time, not just schema validity.**
>
> `docker compose config` validates schema; `docker compose up` reveals runtime semantic differences. Some compose v2 features are documented but only function in swarm mode -- the canonical example is service-level `secrets:` long-syntax with `uid`/`gid`/`mode` fields. The YAML parses, `compose config` succeeds, runtime fires a warning, fields are silently discarded. Outcome differs from schema validation by exactly one invisible behavior.
>
> Required preflight for compose.yaml directives:
> 1. Identify operational mode of target host (standalone vs swarm). Default assumption: standalone unless explicitly swarm-mode.
> 2. For features beyond basic short-syntax (long-syntax fields, swarm-specific directives, `deploy.*` blocks, secrets `uid`/`gid`/`mode`, configs `uid`/`gid`/`mode`, etc.), verify the feature works in target mode by checking upstream compose docs OR observing `docker compose up` output (not just `docker compose config`).
> 3. Document mode-assumption in spec when authoring compose.yaml content.
>
> Common mode-gated features banked:
> - `secrets:` long-syntax `uid`/`gid`/`mode` -- swarm-only
> - `configs:` long-syntax `uid`/`gid`/`mode` -- swarm-only
> - `deploy.replicas`, `deploy.placement`, `deploy.update_config`, `deploy.rollback_config` -- swarm-only (silently ignored on standalone)
> - `deploy.resources.limits` -- works on standalone (compose 1.27+)
> - `deploy.resources.reservations` -- swarm-only
>
> Banked from H1 Phase G ESC #3 Day 74. Spec/directive authorized Path Y long-syntax `uid: 472, gid: 472, mode: 0400` on file-based secret. Standalone compose v2.40.3 silently discards these fields at runtime. obs-grafana crash-looped on identical Permission denied error from ESC #2. PD caught the warning at `docker compose up` output. Verified via upstream Docker compose bug tracker (issues #4994, #9648, #12010, #13287, authelia #7466).

### 3.2 P6 lessons banked count

**19** (was 18 broadened).

### 3.3 Spec amendment scope (REVISED from prior turn)

`tasks/H1_observability.md` Phase G close-out fold:

**Phase E.1 (directory creation)** -- chown step for data dirs (per ESC #1, no change from prior amendment):
```bash
sudo chown -R 65534:65534 /home/jes/observability/prom-data
sudo chown -R 472:472 /home/jes/observability/grafana-data
```

**Phase E.5 (NEW step, after CEO writes grafana-admin.pw content)** -- chown step for secret file (per ESC #2/3 resolution, Path X-only):
```bash
# After CEO writes grafana-admin.pw content,
# chown the file to Grafana's container UID (Path X resolution per ESC #3 ruling)
sudo chown 472:472 /home/jes/observability/grafana-admin.pw
# Mode 600 preserved
# Note: if CEO rotates password later, chown must be re-applied after each rewrite
```

**Section 9 E.2 (compose.yaml secrets block)** -- STAYS short-syntax. Prior turn's authorization for long-syntax is **REVOKED**. Cross-reference P6 #19 with rationale ("long-syntax uid/gid/mode is swarm-mode-only on compose v2; runtime-ignored on standalone with warning").

Both Phase E.1 + E.5 cross-reference broadened P6 #18. Section 9 E.2 cross-references P6 #19.

### 3.4 Operator ergonomics note

Path X-only requires CEO to use `sudo` for any future grafana-admin.pw rotation. Document this clearly in the spec rotation procedure:

```bash
# Grafana admin password rotation procedure (Path X model):
sudo bash -c "printf '%s' '<new-password>' > /home/jes/observability/grafana-admin.pw"
sudo chown 472:472 /home/jes/observability/grafana-admin.pw
sudo chmod 600 /home/jes/observability/grafana-admin.pw
cd /home/jes/observability && docker compose restart grafana
```

**P5 carryover candidate**: helper script wrapping rotation steps (`./rotate-grafana-pw.sh <new-pw>`). Defer to v0.2 hardening pass.

---

## 4. Order of operations from here

```
1. PD: confirm stack down (compose-down already authorized inline; ratified retroactively under standing rule)
2. PD: cp /tmp/compose.yaml.pre-pathy-bak /home/jes/observability/compose.yaml
3. PD: verify md5 db89319cad27c091ab1675f7035d7aa3
4. PD: sudo chown 472:472 /home/jes/observability/grafana-admin.pw
5. PD: stat -c verification: 600 472:472 11 bytes
6. PD: docker compose up -d
7. PD: healthcheck poll cap 120s -- expect both healthy
8. PD: resume G.4 (scrape target verification)
9. PD: G.5 bridge NAT decision (Path 1 if SlimJim self-scrape fails)
10. PD: G.6 Beast anchor post-capture (must be bit-identical)
11. PD: write paco_review_h1_phase_g_compose_up.md including:
    - Path A chown evidence (ESC #1 resolution)
    - Path Y attempt + runtime-ignored warning evidence (ESC #2/3 documentation)
    - Path X final resolution evidence (revert + chown)
    - 5-gate scorecard
    - Container start times + health
    - Prometheus targets table
    - Bridge NAT decision + evidence
    - Beast anchor pre/post diff
    - P6 #18 broadened banking + P6 #19 new banking
    - Spec amendments cross-references (E.1 + E.5; 9 E.2 unchanged)
    - P5 carryovers banked: mixed-ownership grafana-data subdirs (post-Phase-H investigation) + rotation helper script
    - Standing rule update: compose-down during active ESC
12. PD: Phase G close-out commit (single git push):
    - paco_review_h1_phase_g_compose_up.md
    - tasks/H1_observability.md amendments (E.1 chown + E.5 chown; 9 E.2 unchanged)
    - feedback_directive_command_syntax_correction_pd_authority.md update (compose-down carve-out)
    - SESSION.md Day 74 Phase G close section
    - paco_session_anchor.md (Phase G CLOSED, Phase H NEXT, P6 = 19)
    - CHECKLIST.md audit entry
13. PD: write notification to /home/jes/control-plane/docs/handoff_pd_to_paco.md
14. PD: git commit + push
15. CEO triggers Paco with one-line: "Paco, PD finished, check handoff."
```

---

## 5. Standing rules in effect

- 5-guardrail rule + carve-out (now expanded to include compose-down during active ESC pre-authorization)
- B2b + Garage nanosecond anchor preservation (still holding through 3 Phase G ESCs)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol effective
- Spec or no action: Path X-only explicitly authorized this turn; Path Y authorization REVOKED
- Secrets discipline: grafana-admin.pw content REDACTED; only ownership and md5 changes captured
- P6 lessons banked: 19 (added #19 this turn)

---

## 6. Acknowledgments

### 6.1 PD's discipline (3rd consecutive ESC handled cleanly)

PD followed the explicit hard rule from the prior handoff ("Do NOT try Path X as fallback without Paco ruling"). Caught the warning at runtime, halted, escalated. Three consecutive ESCs in Phase G all routed correctly. PD has earned the standing carve-out for compose-down during active ESCs.

### 6.2 Handoff protocol third validation

Third consecutive ESC through the handoff convention. PD wrote request + handoff_pd_to_paco.md notification with appropriate brevity (the handoff file referenced the request file rather than duplicating its content). CEO sent the one-line trigger. Paco read both docs. Loop closed. Protocol stable.

### 6.3 Discipline asymmetry observation (informational)

The 5-guardrail rule + carve-out + handoff protocol + per-step review docs together form a discipline architecture that successfully caught two consecutive Paco-side spec errors (P6 #17 yesterday, P6 #19 today) within 24 hours, through PD's runtime catching at the right moment in each case. The asymmetry observation: directive errors at the Paco authorship layer are caught by PD's runtime discipline; the reverse direction (PD execution errors) is caught by Paco's independent verification gate. Both directions of catching are working. This is the system functioning as designed.

---

**File location:** `/home/jes/control-plane/docs/paco_response_h1_phase_g_path_x_only_approved.md`

-- Paco
