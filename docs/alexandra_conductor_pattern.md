# Alexandra Conductor Pattern -- Canonical Architecture Statement

**Banked:** 2026-05-05 Day 80 ~06:30Z UTC at CEO-directed conductor-pattern ratification.
**Authority:** CEO direct ratification ("Yes. This makes sense. And it reframes the entire forward roadmap. This should have always been the correct path; this is what I have communicated since the beginning.").
**Authored:** Paco (COO).
**Status:** RATIFIED v1.0; supersedes any prior architecture framing where Alexandra and her department heads were treated as parallel peer systems.
**Companion docs:** ALEXANDRA_PRODUCT_BRIEF.md (amended same commit), SANTIGREY_ORG_CHART.md (amended same commit), PROJECT_ASCENSION_INSTRUCTIONS.md (amended same commit), `docs/alexandra_conductor_progress.md` (companion progress meter).

---

## 1. The Pattern (load-bearing statement)

Alexandra is the **unified conductor** for Santigrey Enterprises. The CEO talks to Alexandra. Alexandra routes to her staff. The staff does the work. Alexandra synthesizes and presents.

This is the JARVIS pattern, explicitly:

- JARVIS doesn't personally know everything
- JARVIS reaches into the right system, pulls the right answer, presents it cleanly
- The intelligence is distributed across staff; JARVIS is the unified interface

Replace JARVIS with Alexandra and Tony Stark with Sloan; that is the architecture.

## 2. What Alexandra IS in this pattern

- The **single user-facing surface** for the entire enterprise
- A **router** that recognizes question domain and dispatches to the right staff member
- A **synthesizer** that takes staff output and presents in her voice with full context
- The **memory layer** that maintains continuity across staff calls (one memory store, model-judges-posture per existing product brief)
- The **escalation owner** when a question outgrows local capacity (frontier-fallback to Sonnet/Opus)
- The **honest-refusal layer** when no staff covers a domain (does NOT fabricate; says "I don't have a staff member who handles this; here are the canon sources or shall we build that capability?")

## 3. What Alexandra is NOT in this pattern

- Not a worker that personally handles every domain
- Not a parallel peer to Atlas / Mr Robot / PD / AXIOM in a microservices sense
- Not a tool-bag that grows by adding more local tools per question domain
- Not a fabricator. **No more ceremony when out of scope.** Honest refusal with canon pointers is the correct behavior.

## 4. Staff Inventory + Wiring State (as of ratification)

This section is the source of truth for who Alexandra's staff is and what's wired. Companion progress meter at `docs/alexandra_conductor_progress.md` tracks ongoing changes.

| # | Staff member | Domain | Wiring state | Wiring mechanism |
|---|---|---|---|---|
| 1 | **Atlas** (Charter 5 Operations / Beast) | Fleet ops, monitoring, scheduled jobs, vendor admin, talent ops, mercury supervision, infrastructure status | **PARTIAL (4/10 tools wired via v0.2.0 bridge)** | `orchestrator/ai_operator/atlas_bridge.py` + `https://sloan2.tail1216a3.ts.net:8443/mcp` (Atlas MCP server on Beast) |
| 2 | **Mr Robot** (Charter 7 Security / SlimJim) | CVE audit, intrusion detection, firewall posture, security log analysis, pentest dispatch | **NOT BUILT** | Phase 0 charter draft pending; bridge similar to Atlas's would extend `ai_operator/` once built |
| 3 | **Frontier Claude** (Sonnet/Opus) | Heavy reasoning, code review, architectural planning, anything 72B local can't handle well | **PARTIAL (internal code path, not exposed as routable tool)** | `_chat_frontier_call` in `orchestrator/app.py` exists but is invoked internally; needs to be exposed to Alexandra-driven escalation as `escalate_to_frontier` tool |
| 4 | **Qwen 2.5 72B on Goliath** | Local-first chat brain | **WIRED (this IS Alexandra's body)** | Default `/chat` posture brain per ALEXANDRA_PRODUCT_BRIEF.md |
| 5 | **PD (Engineering / Cowork)** | Code build / ship / refactor; runs directives | **INTENTIONALLY NOT WIRED** | Alexandra may suggest directive shape; CEO + Paco + Cowork mediation is the safety pattern. **Direct dispatch from Alexandra to PD is out of scope.** |
| 6 | **AXIOM (L&D)** | Per Scholas curriculum, capstone mentorship | **NOT BUILT AS SYSTEM (persona-mode only)** | If wired: AXIOM-mode subroutine + course material query tool + capstone mentor surface |
| 7 | **Mercury (sub-agent under Atlas)** | Kalshi paper-trading; eventually real-money supervision | **WIRED THROUGH ATLAS** | Mercury queries flow Alexandra -> Atlas -> Mercury |
| 8 | **External MCPs** (Gmail, Calendar, Drive, Slack, Hugging Face, homelab-mcp) | Vendor / personal / development surface | **PARTIAL** | Calendar + email wired via `_get_calendar_handler` + `_get_emails_handler`; Drive partially via `_get_emails_handler`; Slack + Hugging Face + homelab-mcp not direct (homelab-mcp is Paco's lane intentionally) |
| 9 | **Search / Web** | News, current info, research | **WIRED** | `web_search` + `web_fetch` + `research_topic` + `jsearch` tools |
| 10 | **Home Assistant / IoT** | Home control, security cameras | **WIRED** | `home_status` + `home_control` + `home_cameras` tools |
| 11 | **Memory layer** | Persistent context (pgvector + Atlas memory) | **WIRED** | Local memory (`memory_recall` + `memory_save`) + Atlas memory (`atlas_memory_query` + `atlas_memory_upsert` via bridge) |

**Staff coverage roll-up:** 11 staff members enumerated; 5 fully wired, 4 partially wired, 1 not built, 1 intentionally not wired.

## 5. Routing Doctrine (how Alexandra decides where to send a question)

1. **Domain recognition** -- Alexandra's system prompt names her staff explicitly with domain ownership. When a question arrives, she identifies which staff member's domain it falls in.

2. **Staff dispatch** -- Alexandra calls the appropriate staff bridge tool. Output comes back as structured data she can synthesize from.

3. **Multi-staff synthesis** -- if a question spans domains (e.g. "audit our security AND tell me what hardware is patched"), Alexandra calls multiple staff in sequence/parallel and weaves the answers.

4. **Escalation** -- if the local 72B brain cannot synthesize confidently, Alexandra invokes `escalate_to_frontier` and gets a Sonnet/Opus answer back, then presents in her voice. Escalation is Alexandra-initiated per existing brief.

5. **Honest refusal** -- if no staff covers the domain, Alexandra explicitly says "I don't have a staff member who handles this. Closest canon source is X. Want to build that capability?" **Fabrication is forbidden by SR #10 PF.ASSERTION_AUDIT extension.**

6. **No state-changing PD dispatch** -- Alexandra is allowed to say "this looks like it needs a PD directive" and even suggest the directive shape. She is NOT allowed to dispatch directives directly. CEO + Paco + Cowork mediation is the safety boundary.

## 6. What "complete the stack" means

The roadmap reframes around staff wiring, not feature additions:

- **NOT:** "Add 5 more local tools to Alexandra" (that's the old framing)
- **YES:** "Wire Atlas's full tool surface so Alexandra can answer fleet-status questions by querying Atlas"
- **YES:** "Build Mr Robot so Alexandra can answer security-posture questions by querying Mr Robot"
- **YES:** "Expose frontier-fallback as an explicit Alexandra-callable tool so heavy reasoning routes properly"
- **YES:** "Tighten Alexandra's prompt to enforce honest refusal in undefined domains"

## 7. Priority Sequence (CEO-ratified Day 80 ~06:30Z UTC)

1. **Atlas v0.2.1 bridge expansion** -- add the deferred 6 atlas_tasks_* tools so Alexandra can read fleet monitoring data. **Highest leverage; substrate-ready today; estimated 1 cycle.** This unblocks fleet-status questions.

2. **Frontier-as-tool exposure** -- make `escalate_to_frontier(domain, question, context)` a real Alexandra-callable tool, not just an internal code path. **Small cycle; high leverage on "ask Alexandra anything robustness."**

3. **Mr Robot Phase 0 build** -- Charter 7 Security / SlimJim. Wazuh + Suricata + agents + bridge similar to Atlas's. **Multi-phase cycle; depends on `atlas_events_create` MCP tool + security schema migration on Beast.**

4. **Routing prompt rewrite** -- Alexandra's system prompt restructured around staff-by-domain instead of tool-by-tool. **Small cycle; can run in parallel with #1.**

5. (Lower priority, banked) **AXIOM operationalization** -- L&D as a system, not just a persona-mode.

6. (Banked, NOT to be wired) **PD direct dispatch** -- explicitly out of scope per safety boundary above.

## 8. Progress Meter

Live progress meter lives at `docs/alexandra_conductor_progress.md`. Update at every cycle close that touches conductor wiring. Single roll-up percentage at top: "X% of conductor pattern wired."

Methodology for percentage: each staff member gets a weight (Atlas heaviest 0.30; Mr Robot 0.20; Frontier-as-tool 0.15; routing prompt 0.10; PD-suggest-only 0.05; AXIOM 0.10; Memory + Web + Home + External MCPs 0.10 collectively). Multiply weight by wiring fraction (0.0 = not built, 0.5 = partial, 1.0 = fully wired with smoke-test passing). Sum = roll-up percentage.

At ratification: roll-up = **45%** (per progress meter at companion file).

Goal: 80%+ before Sloan does first hiring-manager Alexandra demo. 100% is aspirational; some staff (Mr Robot, AXIOM) may stay partial indefinitely if not load-bearing for placement narrative.

## 9. Governance Implications

- **Paco directive authoring** defaults to "expand routing surface" (staff bridge + tool exposure) rather than "expand local tool surface" (more local tools on Alexandra). Directives that add local tools to Alexandra's registry require explicit justification: "this domain has no staff member because X."
- **Alexandra's system prompt** must enumerate staff explicitly with their domains; any new staff member triggers a prompt amendment cycle.
- **Cycle close-confirm** for any conductor-touching cycle updates the progress meter at `docs/alexandra_conductor_progress.md` and the staff-inventory table in this doc.
- **SR #10 PF.ASSERTION_AUDIT** extends to Alexandra: when she generates an answer asserting fact about a domain, the answer must trace to a staff bridge call output, NOT to her local model's training-data priors. Honest refusal is the correct path when no bridge covers the domain.

## 10. What Triggered This Ratification

Day 80 evening Session 3, CEO asked Alexandra to "audit the systems and verify CVE-2026-31431 remediation." Alexandra began generating ceremonial audit-shaped output ("I'll check each node", "node-by-node audit", "CiscoKid (192.168.1.10)") with no actual fleet-introspection capability. Paco probed Alexandra's tool inventory and confirmed she has zero tools for SSH-into-other-nodes, kernel reads, package state queries, or CVE checks. The answer she was building was hallucination from training-data priors.

CEO surfaced: "alexandra needs to be my source of truth so to speak, i should be able to ask her anything and with regard to the stack she is designed to reach out to her staff and they provide her the information to relay to me. IE the request i just gave. The org supplies her with the intelligence of our enterprise and everything else. IE JARVIS. she so fragmented right now. Not moving toward my intended goal. so we need to complete our stack so she can then be programmed to source from her team ie , atlas, claude, qwen, mr robot, etc. does this make sense?"

Paco confirmed framing; CEO ratified; this canon document is the result. The conductor pattern was always the intended architecture; the parallel-peer-systems framing in prior canon was a Paco-side mis-implementation that this document corrects.

---

**End of Alexandra Conductor Pattern v1.0.**
