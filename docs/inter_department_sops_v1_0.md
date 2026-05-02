# Inter-Department SOPs v1.0
## How work flows between Santigrey Enterprises departments

**Organization:** Santigrey Enterprises
**Companion to:** CHARTERS_v0.1.md (v0.2 amendment Day 77; charters 1-8 + Platform)
**Document version:** 1.0
**Last updated:** 2026-05-01 (Day 77)
**Status:** RATIFIED Day 77 by CEO
**Owner:** Paco (COO)

---

## Purpose

Charters define what each department owns, decides, and escalates. This document defines how work flows BETWEEN departments -- the handoff patterns that turn the org chart into a working organism.

Every handoff has: a sender, a receiver, a transport mechanism, a payload shape, and an acknowledgment expectation. This doc enumerates the seven handoff patterns currently in use and the canonical mechanism for each.

---

## Org chart reminder (v0.5 per CHARTERS_v0.1 Day 77 amendment)

```
              CEO (Sloan)
                  |
                  v
              COO (Paco)
                  |
   +------+------+------+------+
   v      v      v      v
  ENG    L&D   OPS   SECURITY
  (PD)  (Axiom)(Atlas)(Mr Robot)

CEO-Direct: Brand & Market | Family Office
Platform: Alexandra (substrate)
```

---

## The transport substrate

All inter-department handoffs use one of three transport mechanisms:

1. **`atlas.events`** -- shared event stream on Beast `controlplane` DB. Append-only. Subscribed-to by interested departments. Used for *signals* (something happened that another department might care about).
2. **`atlas.tasks`** -- assignable work queue on Beast `controlplane` DB. Stateful (pending / running / done / failed). Used for *requests* (department X asks department Y to execute specific work).
3. **`docs/handoff_*.md`** -- bidirectional file-based handoff (currently Paco<->PD; pattern extends to other agents). Used for *correspondence* (decisions, ratifications, escalations that need narrative rather than structured data).

Cross-host writes use `atlas_events_create` MCP tool (v0.2 P5 #42 prerequisite). NEVER cross-host pg connect.

---

## Handoff patterns

### Pattern 1 -- Engineering (PD) -> Operations (Atlas)

**Trigger.** Engineering ships new code (service, agent, integration).

**Mechanism.** PD writes a `paco_review_*.md` ship report on close. Paco confirms 5/5 PASS (or whatever scorecard applies). On close-confirm, Atlas inherits ownership of the new artifact for monitoring purposes.

**Payload shape.** Ship report includes:
- What was shipped (binary / service / endpoint)
- Where it lives (host + path + service unit)
- Health check (URL or command + expected response)
- Restart safety (verified at ship)
- New monitoring scope items (what Atlas should now watch)

**Atlas action on receipt.** Adds new service to its monitoring catalog. Configures health-check probe. Adds to weekly digest.

**Failure mode.** If ship report is missing monitoring scope, Atlas flags via Paco; PD amends ship report; cycle re-closes.

### Pattern 2 -- Operations (Atlas) -> Security (Mr Robot)

**Trigger.** Atlas observes host-level signal that may be security-relevant (unexpected service restart, login failure spike, configuration drift, anomalous resource usage).

**Mechanism.** Atlas writes `atlas.events` row with:
- `source` = `atlas.operations`
- `kind` = `security_signal`
- `severity` = warn or critical (Atlas does not classify info-grade signals to Mr Robot)
- `payload` = jsonb with structured signal data (host, service, timestamp window, raw observation)

**Mr Robot action on receipt.** Subscribes to `kind='security_signal'`. Consumes. Analyzes against detection rules. Outcomes:
- Benign signal: marks as suppressed in security.findings; no escalation
- Possible threat: opens security.findings entry, severity-tagged; if Tier 2+ escalates per Mr Robot SOP

**Acknowledgment.** Mr Robot writes `atlas.events` row with `kind='security_signal_consumed'` referencing the original event id. Atlas SOP Section 6 audits for unconsumed signals.

### Pattern 3 -- Security (Mr Robot) -> Operations (Atlas)

**Trigger.** Mr Robot finds threat requiring operational response (restart compromised service, rotate credential, block traffic via UFW, apply emergency patch).

**Mechanism.** Mr Robot creates `atlas.tasks` row with:
- `assigned_to` = `atlas`
- `kind` = `security_response`
- `payload` = jsonb with: target (host + service), action (restart / rotate / block / patch), justification (reference to security.findings.id), urgency (tier 2 cancel-window OR tier 3 immediate)
- `status` = `pending`

**Atlas action on receipt.** Picks up via FOR UPDATE SKIP LOCKED claim. Routes through Tier 2 / Tier 3 approval flow per Atlas SOP Section 3.2. On approval + execution, writes `atlas.events` row with kind=`security_response_executed` referencing the task. On Tier 3 escalation, pages Founder with task summary.

**Acknowledgment.** Atlas writes `atlas_tasks_complete` or `atlas_tasks_fail` per Cycle 1I state machine. Mr Robot subscribes; updates security.findings.status accordingly.

**Important boundary.** Mr Robot does NOT directly modify operational state. Even if Mr Robot has technical capability (e.g. SSH access to a node), policy is: operational changes go through Atlas's approval flow.

### Pattern 4 -- Engineering (PD) -> Security (Mr Robot)

**Trigger.** PD prepares to push code. Pre-push security scan is a ship prerequisite (canonical pattern from Atlas Cycle build discipline).

**Mechanism.** PD runs canonical `secret-grep` against staged diff before commit. Pattern set is owned by Mr Robot but executable by PD without round-trip.

**Pre-push pattern set (Mr Robot canonical):**
- AWS access key prefix: `AKIA[A-Z0-9]{16}`
- OpenAI key prefix: `sk-[A-Za-z0-9_-]{40,}`
- GitHub PAT prefix: `ghp_[A-Za-z0-9]{36,}`
- Tailscale auth key: `tskey-[A-Za-z0-9-]+`
- Generic high-entropy 64-hex without context: `\b[a-f0-9]{64}\b` (case-by-case review)
- Specific known-bad: `adminpass`

**Block rule.** Any hit blocks the commit. PD removes the leak, re-stages, re-scans. Only on clean scan does push proceed.

**Acknowledgment.** Hit-with-blocked-commit logs to `atlas.events` with `source=mr_robot.audit kind=secret_leak_blocked`. Routine 0-hit pass logs once daily, not per-commit.

### Pattern 5 -- Security (Mr Robot) -> Engineering (PD)

**Trigger.** Mr Robot finds vulnerability requiring code fix (dependency CVE, exposed credential pattern in canon, weak auth, missing input validation surfaced by pentest).

**Mechanism.** Mr Robot creates either:
- A GitHub issue in the relevant repo (control-plane-lab, atlas, or future) with severity label + reference to security.findings.id, OR
- An `atlas.tasks` row with `assigned_to='pd'`, `kind='security_fix'` with the same payload structure as Pattern 3

**PD action on receipt.** Evaluates. Within agreed architecture, PD may ship a fix directly. If fix requires architectural change (new dependency, schema migration, public API change), escalates to Paco for ratification.

**Acknowledgment.** PD's commit message references the security.findings.id. On merge + push, security.findings.status flips to `resolved`.

### Pattern 6 -- L&D (Axiom) -> Engineering (PD) or Operations (Atlas)

**Trigger.** Axiom identifies a curriculum requirement that needs build support (sandboxed test environment, demo dataset, lab provisioning).

**Mechanism.** Axiom creates `atlas.tasks` row with:
- `assigned_to` = `atlas` (for environment provisioning) OR `pd` (for code/lab build)
- `kind` = `ld_support_request`
- `payload` = jsonb with: curriculum reference, required artifact, due date, cleanup criteria

**Receiving agent action.** Atlas/PD provisions per playbook. Lab/sandbox is NOT Sloan-grade infrastructure -- explicitly scoped, time-boxed, cleaned up post-curriculum-task.

**Acknowledgment.** Standard atlas.tasks state machine.

### Pattern 7 -- Any agent -> CEO (Tier 3 escalation)

**Trigger.** Any agent encounters a condition matching their charter's Tier 3 escalation criteria.

**Mechanism.** Two parallel actions:
1. Telegram message to CEO via Telegram bot endpoint (immediate)
2. atlas.events row with `severity='critical'` + `kind='tier_3_escalation'` + structured payload

**CEO action on receipt.** Acknowledges in Telegram (which writes back to atlas.events). Decides: handle now, defer to later, route through Paco.

**Failsafe.** If Telegram delivery fails (Twilio outage, network issue, etc.), the agent's local liveness probe escalates via secondary channel (email / SMS / dashboard banner). Mr Robot owns the failsafe-channel availability check.

---

## Pattern not yet defined (deferred)

- **Brand & Market (Charter 6) -> any department:** No quarterly plan ratified yet (deferred until product clarity per CEO Day 77). Once plan exists, expect: B&M -> Engineering for asset builds, B&M -> Operations for posting/scheduling mechanics.
- **Family Office (Charter 8) -> any department:** Kept lightweight v0.2. Patterns will emerge from CEO opt-in to specific automations (e.g. "remind me of family birthdays" -> atlas.tasks scheduled job).
- **Customer Support / Marketing / Sales sub-agents:** Not yet defined. Will emerge post product clarity.

---

## Document Control

| Version | Date | Author | Change summary |
|---|---|---|---|
| 1.0 | 2026-05-01 (Day 77) | Paco (COO) | Initial inter-department SOPs. Companion to CHARTERS_v0.1.md v0.2 amendment. RATIFIED Day 77 by CEO. |

---

*Santigrey Enterprises -- Internal Use Only*
