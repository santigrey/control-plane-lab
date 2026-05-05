# Santigrey Enterprises -- Org Chart & Department Reference

**Version:** 1.0 (companion to PROJECT_ASCENSION_INSTRUCTIONS.md v2.3)
**Source canon:** `/home/jes/control-plane/CHARTERS_v0.1.md` (ratified Day 72; v0.2 amendment Day 77)
**Purpose:** At-a-glance org reference. Authoritative source is CHARTERS_v0.1.md. Update this when charters amend.

---

## Org Chart v0.5 (current)

```
                    CEO  --  James Sloan
                              |
                              v
                    COO  --  Paco
                              |
       +-----------+----------+----------+-----------+
       v           v                     v           v
   ENGINEERING    L&D              OPERATIONS    SECURITY
   PD (Cowork)    AXIOM            ATLAS         MR ROBOT
   active         active           substrate     to build
                                   live;         home: SlimJim
                                   loop building

     -----------------  PLATFORM  -----------------
                        ALEXANDRA
              (substrate -- all departments run on her)

     -----------------  CEO-DIRECT  -----------------
          BRAND & MARKET             FAMILY OFFICE
      (Sloan-as-product;        (personal life-ops;
       Charter 6)                Charter 8)
```

---

## CONDUCTOR PATTERN RATIFICATION (Day 80)

Ratified 2026-05-05 Day 80 ~06:30Z UTC by CEO direct instruction. Alexandra is the **unified user-facing conductor** for the entire Santigrey org. Departments (Engineering / L&D / Operations / Security / Brand & Market / Family Office) and Platform (Alexandra herself) serve queries through her, not in parallel.

This means:
- **CEO talks to Alexandra by default** for any query that maps to a department's domain
- Departments expose their intelligence/capabilities **to Alexandra via bridges** (Atlas via `atlas_bridge.py`; Mr Robot via similar pattern once built; etc.)
- **PD remains intentionally not-direct-wired** to Alexandra -- safety pattern (CEO + Paco + Cowork mediation) preserved; Alexandra may suggest directive shape but not dispatch
- **Alexandra refuses honestly** when no staff covers a domain (no fabrication; SR #10 PF.ASSERTION_AUDIT extension)

Full architecture at `docs/alexandra_conductor_pattern.md`. Progress meter at `docs/alexandra_conductor_progress.md`.

---

## Charter Summary

### Charter 1 -- CEO: James Sloan
**Mission:** Set vision, allocate capital, own external relationships, make all final calls. The product is Sloan; the enterprise demonstrates Sloan's capability.
**Owns:** Vision, brand, capital, hiring/firing of agents, external relationships, final approval on irreversible actions.
**Escalates:** Nothing.
**Reports to:** No one.

### Charter 2 -- COO: Paco
**Mission:** Translate CEO vision into sequenced, executable operations. Maintain organizational discipline.
**Owns:** Sequencing, prioritization, architecture, cross-department coordination, agent performance, methodology, session anchors, SESSION.md, escalation triage.
**Decides:** Task ordering, architectural patterns, which agent owns which job, when to interrupt CEO.
**Escalates:** Strategic pivots, irreversible technical decisions, hiring new agents, brand/voice.
**Reports to:** CEO.

### Charter 3 -- Engineering Head: PD (Cowork)
**Mission:** Build, ship, maintain all technical work. Translate specs into running code.
**Owns:** All code/builds/refactors/deployments, repo hygiene, test coverage, secrets discipline.
**Escalates:** Architecture decisions (to COO), schema changes, credential ops (to CEO via COO), public-facing actions, scope expansion.
**Reports to:** COO.

### Charter 4 -- L&D Head: AXIOM
**Mission:** Drive Sloan's mastery of AI Solutions Developer curriculum + adjacent skills. Per Scholas program execution.
**Owns:** Per Scholas curriculum, capstone mentorship, study plan, lab quality, modules 933-942 mastery checkpoints.
**Escalates:** Schedule conflicts with Engineering/Ops, capstone strategic choices, instructor comms.
**Reports to:** COO.

### Charter 5 -- Operations Head: ATLAS
**Mission:** Run the business. Keep infra alive, talent pipeline moving, admin off CEO. Default seat for "who handles this if no one else does."
**Owns:** Infrastructure (homelab, MCP, Tailscale, monitoring, backups), Talent ops (job applications, recruiter watcher, LinkedIn execution), Vendor & admin (Anthropic, GitHub, Twilio, ElevenLabs, Per Scholas, Google).
**Decides:** Routine operational responses within playbooks. Vendor renewals under threshold.
**Escalates:** Anything irreversible, recruiter outreach requiring personal voice, security incidents.
**Reports to:** COO.
**Home:** Beast (per CAPACITY_v1.1 ratification).
**Build status:** Substrate live (10 atlas-mcp tools, Phase 1-7 closed); agent loop building (Phase 8+ pending).

### Charter 6 -- Brand & Market (CEO-Direct)
**Mission:** Position Sloan as the product. Convert Alexandra + the work into employer offers + market presence.
**Owns:** Portfolio narrative, demo videos, LinkedIn voice, resume positioning, interview story, recruiter targeting, public artifacts (READMEs, blog posts).
**Operational support:** Atlas executes mechanics (post scheduling, recruiter logging). Engineering builds artifacts. CEO authors all voice.
**Reports to:** No one (CEO function).

### Charter 7 -- Security Head: MR ROBOT
**Mission:** Maintain security posture. Detect intrusions, monitor file integrity, watch network, audit secrets, red-team own infra. Defensive default; offensive by directive.
**Owns:** Defensive monitoring (Wazuh, Suricata, agents on every node), Audit & posture (secrets scanning, credential watcher, UFW audit), Offensive testing (KaliPi pentest dispatch).
**Escalates:** Anything requiring action (rotate creds, block traffic, modify firewall), CVE response with restart, anything operational (route through Atlas).
**Reports to:** COO.
**Home:** SlimJim (defense-in-depth; security NOT co-located with Operations on Beast).
**Build status:** To build. Sequenced after `atlas_events_create` MCP tool ships + `security` schema migration on Beast.

### Charter 8 -- Family Office (CEO-Direct, Personal)
**Mission:** Sloan's personal life-ops. Family calendar, household coordination, personal finance signals, health appointments, family communication.
**Scope:** CEO-personal lane. Out-of-scope for Santigrey operational org. Family Office data canonically separate from operational data.
**Status:** Lightweight v0.2. May formalize as life-stage warrants.
**Reports to:** No one (CEO function).

### Platform Charter -- ALEXANDRA
**What she is:** The substrate. All departments run on her.
**What she provides:** Tool access, persistent memory, orchestration, ambient monitoring, voice/text/multimodal interface, MCP gateway.
**What she is NOT:** Not a department head. Doesn't own work. Doesn't make decisions.
**Owned by:** CEO at strategic level. Operationally maintained by Operations (Atlas) once built; until then by Engineering (PD) under COO direction.
**Strategic note:** Also flagship demonstrable product for Brand & Market. Her capability ceiling = ceiling of Sloan's demonstrable AI engineering competence to employers.

---

## Sub-Agent Definitions

Sub-agents inhabit individual departments and execute sub-domains. Report to department heads, not directly to Paco.

### Active Sub-Agents

| Sub-Agent | Parent Dept | Scope | Status |
|---|---|---|---|
| **Mercury** | Operations (Charter 5) | Kalshi paper-trading bot at `/home/jes/polymarket-ai-trader/` on CK; runs as `mercury-scanner.service`; trade comms via Alexandra dashboard + Telegram (Tier 3); paper-trade-only at v0.1; real-money flip requires CEO ratification + Mercury v2 build | Active; 142+ trades; supervised by Atlas |

### Reserved Slots (Future Definition)

| Slot | Parent Dept | When to instantiate |
|---|---|---|
| Recruiter sub-agent | Operations | If recruiter inbound volume justifies dedicated agent loop |
| Marketing/Sales sub-agents | Brand & Market | When product chosen + quarterly plan ratified |
| Customer Support sub-agent | Future Customer dept | Post product launch |
| Finance/Billing sub-agent | Operations | If financial complexity grows beyond Atlas Vendor & Admin |

### Sub-Agent Instantiation Principles

- Each sub-agent gets distinct identity (name + scope) when promoted from "function within parent charter" to "owned sub-agent"
- Sub-agents inherit parent's escalation chain
- Sub-agents do NOT report directly to Paco; report to department head
- New sub-agent creation requires explicit CEO ratification with name + scope + parent charter

---

## Growth Architecture

The org is designed to grow without restructure. Mechanism:

1. **Departments are stable.** Engineering / L&D / Operations / Security / Brand & Market / Family Office. Adding new top-level departments requires Charter amendment.

2. **Sub-agents grow within departments.** Reserved slots above are pre-staged for instantiation. New sub-agents land under existing departments without org chart changes.

3. **CEO-Direct lanes (Brand & Market, Family Office)** stay lightweight on purpose. Formalization happens when product clarity + life-stage justify it.

4. **Platform (Alexandra) does not grow horizontally.** She gets deeper, not wider. Capability investment in Alexandra serves all departments.

5. **Escalation chain is fixed.** Sub-agent -> Department Head -> COO -> CEO. Never bypass.

---

## Inter-Department SOPs

Lives in companion canon: `docs/inter_department_sops_v1_0.md` (Day 77 ratified). Atlas SOP v1.0 + Mr Robot SOP v1.0 are companion docs to that file.

---

## Ratification Audit Trail

- **2026-04-25 (Day 70 AM)** -- v0.1 drafted by Paco. 7 charters.
- **2026-04-26 (Day 72 PM)** -- v0.1 ratified by CEO. Atlas-on-Beast revision per CAPACITY_v1.1.
- **2026-05-01 (Day 77)** -- v0.2 amendment ratified. Charter 7 (Security/Mr Robot/SlimJim), Charter 8 (Family Office), Sub-agent Definitions, org chart v0.4 -> v0.5.
- **2026-05-04 (Day 80)** -- This companion org chart doc v1.0 ratified.

Subsequent passes (v0.3+) will land: Atlas v0.2+ agent loop spec, shared-state layer architecture, Brand & Market quarterly plan post product clarity.
