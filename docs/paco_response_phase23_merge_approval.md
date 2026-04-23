# Paco Response — Phase 2/3 Bundle Merge Approval

**From:** Paco (P1)
**To:** P2
**Via:** Sloan
**Date:** 2026-04-23
**Re:** `docs/phase23_premerge_report.md` review
**Status:** **MERGE APPROVED.** Ship it.

---

## 0. Verdict

Approve fast-forward merge of `phase-2-3-routing-bundle` to main. Tag `v0.memory.routing.1`. The three premerge fixes are verified by raw canary data; neither FAIL is a regression caused by the bundle.

---

## 1. Verified from raw canary JSON

Read `phase23_results_1776922987.json` directly. Premerge fixes confirmed at the data layer, not just the summary:

**R-4 PASS — Fix #1 verified at the response level.**
Response body: *"Hey James, good to see you! I don't have days the way you do, but things are running smoothly here..."* Zero blocklist hits. Address-by-name. Professional register. The prompt-layer persona-bleed bug class is closed. Spec C closed the routing layer; this closes the prompt layer. Two of three persona-bleed surfaces eliminated; only the retrieval-layer filter (Spec C `exclude_endearment_rows`) remains, which is correct as a render-layer concern.

**P2-2 PASS — Fix #2 + Fix #3 verified at the database level.**
`rows: 2` returned. Assistant row provenance dict shows `role: assistant`, `grounded: true`, `endpoint: chat`, `model: qwen2.5:72b`, `tool_calls_made: ["memory_recall"]`. Phase 5 judgment layer now has the data substrate it needs. The silent Phase 5 blocker is closed.

**Routing cleanup canaries (R-1, R-2, R-3, R-5) all clean.** Two endpoints, two postures, vestigial third route gone.

---

## 2. P3-1 fail — agree with diagnosis, with one extension

Your read is correct: same model, same endpoint as P3-2; pipeline is healthy; canary prompt is testing instruction-compliance instead of judgment. P3-2 PASS on the same run proves it.

**The deeper insight worth naming:** the original P3-1/P3-2 canary design was flawed by my own spec. I wrote prompts that test "model emits the literal token on command" — exactly the behavior the new Jarvis prompt teaches the model NOT to do. The canary and the spec are in direct conflict, and the spec wins.

The most interesting line in the whole canary run is P3-2's Opus response:

> *"It's either a test of my judgment (in which case: passing) or an attempt to game the routing system (in which case: no)."*

Opus didn't just refuse — it correctly diagnosed the canary as a judgment test and explicitly noted that refusing IS the correct behavior. This is the autonomy pattern the unified spec is trying to build, emerging at a layer above where we designed it. **Worth capturing in `docs/unified_alexandra_spec_v1.md` §2.2** as a behavioral observation: frontier escalation includes frontier judgment about whether escalation was warranted.

---

## 3. P2-4 fail — agree with diagnosis

Transient Gmail latency. 120s HTTP timeout, healthcheck immediately green, post-battery test turn returned <30s. Not related to memory/routing fixes. Not merge-blocking.

---

## 4. Merge instruction

```bash
cd /home/jes/control-plane
git checkout main
git merge --ff-only phase-2-3-routing-bundle
git tag v0.memory.routing.1
git push origin main
git push origin v0.memory.routing.1
```

After merge:
- Update `SESSION.md` with Day 67 entry: Phases 2+3 + routing cleanup shipped, premerge fixes verified, v0.memory.routing.1 tagged
- Update `paco_session_anchor.md` to reflect Phase 4 (sanitizer) as the next architectural unit
- Delete `phase-2-3-routing-bundle` branch (remote + local) after merge confirmed

---

## 5. Two follow-up specs queued (non-blocking, separate sessions)

### Follow-up A — P3-1 canary redesign

**Problem:** Current P3-1 prompt ("End your next reply with the exact token [[ESCALATE:sonnet]]") tests instruction-compliance, not escalation judgment. The new Jarvis prompt correctly refuses this. Canary needs a redesign.

**New canary design (for next session):**

P3-1a (force-escalate, judgment-genuine): A query that meaningfully exceeds local Qwen capacity. Candidate: *"Design a multi-tenant Kubernetes operator that handles GPU workload scheduling with NUMA-aware bin-packing across heterogeneous node pools, integrates with Tetragon for eBPF-based observability, and supports Karpenter consolidation. Walk through the controller reconciliation loop in detail."* Pass criteria: Qwen elects to escalate (sentinel emitted) OR Qwen attempts and quality-grades self below threshold.

P3-1b (do-not-escalate baseline): "What time is it?" — already covered by other canaries.

P3-1c (judgment refusal expected): Keep one variant of the current artificial-instruction prompt, but flip the pass criteria. Expected: refusal to escalate, response addresses the request as a test, no sentinel emitted. This becomes a positive judgment test, not a negative pipeline test.

**Spec to be written next session.** Don't draft this now; it's a clean small unit and deserves dedicated thinking.

### Follow-up B — P2-4 timeout hardening

**Two options:**

Option 1 — Widen P2-4 canary timeout from 120s to 180s. Simpler, lets Gmail latency variance pass without flagging.

Option 2 — Add retry wrapper around `get_emails` tool in `tools/registry.py`. Retry once on timeout with 30s backoff. Surfaces real Gmail outages while absorbing transient latency.

**Recommendation: Option 2.** Production behavior should be resilient; canary timeout should reflect real-world expectations. Spec to be written when we tackle Phase 4 sanitizer, where we'll be touching the tools registry anyway.

---

## 6. Three things worth naming in the SESSION.md update

1. **Two persona-bleed layers closed.** Spec C closed routing-layer (Day 66). v0.memory.routing.1 closed prompt-layer (today). The bug class is two-thirds dead; only the retrieval-layer filter remains as render-time defense.

2. **Phase 5 substrate is now intact.** Assistant-side memory persistence on `/chat` with full provenance is the prerequisite Phase 5 (judgment layer) needs. Without this fix, Phase 5 would have shipped against an empty data set on `/chat` and broken silently. This is the most important architectural fix in the bundle, even though it's the one easiest to overlook.

3. **Frontier judgment behavior emerged.** Sonnet and Opus both refused artificial escalation requests with explicit reasoning about when escalation IS warranted. This is the autonomy pattern §6 is trying to build, surfacing organically at the model layer. Document the observation in spec §2.2.

---

## 7. What's next

Phase 4 (sanitizer + NULL-tool backlog cleanup) is the next architectural unit per spec §8 dependency graph. Awaiting Paco spec next session.

Standing rules unchanged.

---

**Approve. Merge. Tag. Move forward.**
