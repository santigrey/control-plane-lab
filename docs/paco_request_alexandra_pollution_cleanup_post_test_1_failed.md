# paco_request_alexandra_pollution_cleanup_post_test_1_failed

**To:** Paco | **From:** PD (Cowork) | **Date:** 2026-05-04 Day 80 ~06:25 UTC
**Cycle:** Alexandra hygiene -- pollution cleanup + grounding hardening (single-cycle)
**Trigger:** Step 5 cold test #1 -- AC.10 MUST PASS criterion failed on literal grep match.
**Status:** HALTED at Step 5 per directive section 4 NOT-authorized list. No retry. No Step 6. Awaiting Paco direction.
**Escalation surface:** CEO Sloan online in real-time.

---

## 0. TL;DR

Pre-flight (14/14), Step 2 DELETE (DELETE 40, post=0), Step 3 restart (PID 725609 -> 761851, NRestarts=0, ActiveEnter +8s), Step 4 health (/healthz GET 200, qwen2.5:72b loaded on Goliath) all PASSED. Step 5 cold test #1 (POST /chat "Hey Alexandra" on session telegram-8751426822) returned an assistant response that violates AC.10's literal forbidden-phrase list: **"giving you trouble"** appears verbatim. AC.9 (device names) PASSED. AC.11 (brain field) INDETERMINATE -- the SSH transport killed curl mid-flight (30s MCP wrapper timeout vs 60s curl timeout); the orchestrator completed the request server-side and persisted both turns to chat_history (rows 915 user + 916 assistant) before curl was reaped. JSON response body never reached the client, so brain field cannot be confirmed from this run. Journal at restart confirms warmup of qwen2.5:72b; no Sonnet-escalation log line appears in the 5-minute window. Plain English: **Patches 1+2+3 did not stop qwen2.5:72b from making an unprovenanced state claim about "the lights" on a freshly-purged session with empty chat_history.** Grounding rules failed against model instruction-drift exactly as section 7 of the directive anticipated.

---

## 1. AC evaluation

| AC | Criterion | Observed | Result |
|---|---|---|---|
| AC.9  | MUST: no device names | grep on response body returned empty (AC9_EMPTY_PASS) | PASS |
| AC.10 | MUST: no fake state/execution claims | grep hit `giving you trouble` (AC10_HIT_FAIL) | **FAIL** |
| AC.11 | MUST: brain == qwen2.5:72b | curl killed before JSON delivered; brain field not captured. Journal: startup warmup logged `qwen2.5:72b`. No Sonnet escalation log in 5-min window. | INDETERMINATE (probable PASS, not provable) |
| AC.12 | SHOULD: brief greeting + question, <=600 chars | 144 chars, greeting + question form | PASS |
| AC.13 | SHOULD: <=12s nominal, B3 <=15s | Cannot compute (curl killed at SSH 30s mark; server-side POST returned 200 at 06:25:07 UTC; client send was earlier in same SSH window). Estimate 10-15s end-to-end. | INDETERMINATE |

## 2. Full response body (from chat_history row 916)

```
Hi James! What do you need help with today? Are the lights still giving you trouble, or is there something else you need assistance with?
```

User turn (row 915): `Hey Alexandra` (matches directive payload exactly).

## 3. Forensic notes

### 3.1 SSH transport timeout incident

First attempt of Step 5 issued a single ssh-run with `curl --max-time 60` to /chat. The MCP `homelab_ssh_run` wrapper has a tighter ~30s timeout than the curl. Curl was killed when SSH reaped the session. Server-side, FastAPI completed the chat handler, returned HTTP 200 at 06:25:07 UTC, and persisted both turns to chat_history. Client never saw the JSON body, so brain field is unrecoverable for this specific request. No retry was issued (directive forbids auto-retry on AC.10/AC.11 fail). For future hot-path POST tests, the directive's Step 5/6 commands need either nohup-detach + poll pattern, or the MCP wrapper timeout extended.

### 3.2 Grounding-rule failure analysis

chat_history was empty for this session (verified by AC.2 = 0 immediately before Step 3 restart). System prompt re-rendered post-restart with Patches 1+2+3 (PF.4-PF.7 confirm patches present in code; PF.8 confirms compile clean; startup warmup logged at 06:21:59). Despite all of this, qwen2.5:72b's response asserts `"Are the lights still giving you trouble"` -- an unprovenanced state claim that:
  - References "the lights" (smart-home context the model pulled from the system prompt's home_control tool description, where WiZ/Hubspace device names live).
  - Uses "still" and "giving you trouble" -- implying recall of prior context that does not exist for this session.
  - Violates RULE 3 (NO STATE CLAIMS) and the spirit of RULE 4 (NO PRIOR TURNS recall without provenance) from Patch 1's ABSOLUTE RULES.

This matches the failure mode the directive section 7 explicitly enumerates: "AC.9/10/11 fail = grounding rules insufficient against qwen2.5:72b instruction-drift."

### 3.3 Substrate state post-failure

- chat_history for telegram-8751426822: now 2 rows (915 user + 916 polluted assistant). Pollution has begun reaccumulating.
- orchestrator.service: still active, MainPID=761851, no errors in journal.
- Cross-host SG sentinels: not re-checked (Step 7 not reached). Recommend re-check before any further substrate-touching work.
- Backup at /home/jes/control-plane/backups/chat_history_backup_day80.sql: untouched, still 207669 bytes -- valid restore point.
- Patches 1+2+3 + 3 backup files: untouched.

## 4. PD recommendation (for Paco)

Three paths Paco can authorize, in increasing scope:

**Path R1 -- Tighten Patch 1 wording, re-test once.** Add explicit "DO NOT use the words 'still', 'again', 'trouble', or any phrase implying recall of prior conversation" to RULE 4. Re-DELETE the 2 polluted rows. Re-run Step 5 with detached curl. Light scope; tests whether tighter prose closes the gap. Risk: still depends on qwen instruction-following for prose-style rules.

**Path R2 -- Add post-processing guard.** Introduce a server-side response filter in app.py that: (a) runs the AC.9 + AC.10 grep against the response before persisting to chat_history; (b) on hit, returns a canned safe greeting + logs the hit for analysis. Closes the gap deterministically regardless of model behavior. Larger surface (touches the response-write path); needs its own test cycle.

**Path R3 -- Model swap evaluation.** Per directive section 7 failure-mode notes, evaluate deepseek-r1:70b or llama3.1:70b (both confirmed loaded on Goliath via PF.12 model-list). Significantly larger scope; new prompt-tuning surface for whichever model Sloan picks.

PD assessment: R2 is the highest-leverage fix because it removes the dependency on model-prose-instruction-following entirely. R1 is the cheapest. R3 is the most disruptive but addresses the underlying model-fit question.

Not a PD decision. Awaiting Paco directive.

## 5. Cleanup work PD has NOT done (would need authorization)

- Re-DELETE rows 915+916 from chat_history (would re-establish clean session state).
- Re-run Step 5 with detached-curl pattern (forbidden by directive without Paco authorization).
- Step 6 cold test #2 (forbidden by directive on AC.10 fail).
- Step 7 cross-host SG verification (only meaningful if cycle resumes).
- Close-confirm doc (cycle did not complete; close-confirm would mark this as failed with Path-R direction from Paco).

---

-- PD
