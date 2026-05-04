# paco_directive_alexandra_smoke_hygiene_pollution_cleanup_amendment_r2

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-04 Day 80 ~06:35 UTC
**Cycle:** Alexandra hygiene -- pollution cleanup + grounding hardening (single-cycle)
**Type:** AMENDMENT to `paco_directive_alexandra_smoke_hygiene_pollution_cleanup.md` (Path R2 selection per CEO Sloan)
**Status:** Active. Original directive's Steps 1-4 already PASSED + ratified at PD's pre-flight; Step 5 cold test #1 FAILED on AC.10 (`giving you trouble`). This amendment supersedes Step 5 onward with a deterministic post-processing guard added BEFORE re-test.
**Authority:** CEO Sloan selected Path R2 from PD's `paco_request_alexandra_pollution_cleanup_post_test_1_failed.md` recommendation set.

---

## 0. TL;DR

Qwen2.5:72b instruction-following plateau identified at AC.10. Prose-rule patches alone insufficient. Adding a deterministic server-side response filter (Patch 4) + extending forbidden-phrase list (Patch 5) to remove model-prose-instruction dependency on this failure class. Then re-DELETE the 2 reaccumulated chat_history rows + restart + re-run Steps 5-7 with detached-curl pattern (works around MCP wrapper 30s timeout that caused PD's AC.11 indeterminate result).

---

## 1. State to inherit from original directive

- Pre-flight 14/14 PASSED (Paco's out-of-lane Patches 1+2+3 ratified)
- Step 2 DELETE 40 rows: PASSED
- Step 3 orchestrator restart: PASSED (PID 761851 active)
- Step 4 health probes: PASSED
- Step 5 cold test #1: FAILED on AC.10 grep hit `giving you trouble`
- chat_history `telegram-8751426822`: now 2 rows (915 user + 916 polluted assistant), reaccumulating pollution
- 3 backups (chat_history dump + app.py + agent.py) intact
- `app.py` modified working tree (uncommitted; Patches 1+2 applied)
- `agent.py` modified working tree (uncommitted; Patch 3 applied)

This amendment ADDS Patches 4+5 to the working tree before commit. PD ratifies at close-confirm.

---

## 2. Patch 4: Post-processing response guard in `/chat` endpoint

### 2.1 Specification

Insert a deterministic filter between `_chat_local_loop` returning `answer` and the existing sentinel-strip at line ~1543 of `app.py`. The filter:

1. Runs case-insensitive grep against `answer` for AC.9 + AC.10 + R2-extended forbidden-phrase list (see Patch 5).
2. On hit: logs `[CHAT-GUARD]` line to stdout (journalctl) with: triggered phrase, session_id, response length, first 200 chars of original response.
3. On hit: replaces `answer` with canned safe greeting `"Hey James, what can I help you with?"`.
4. On hit: sets `brain = "qwen2.5:72b (guard-substituted)"` for traceability through `provenance` and the response payload.
5. On hit: continues normally with substituted answer (does NOT skip persistence; the safe greeting WILL be saved to chat_history as the assistant turn so the alternation pattern stays consistent for next-turn KV cache).
6. On miss: passes through unchanged.

### 2.2 Concrete code spec

Location: `/home/jes/control-plane/orchestrator/app.py`, in the `/chat` handler function, AFTER:

```python
        # Defense-in-depth: strip any residual sentinel from user-visible answer
        answer = _re.sub(r'\[\[ESCALATE:(sonnet|opus)\]\]', '', answer).strip()
```

INSERT (preserving the leading 4-space indent inside the function):

```python
        # Day 80 R2 guard: deterministic post-processing filter against
        # qwen2.5:72b instruction-drift hallucinations. Catches device-name
        # leaks, fake-execution claims, and implicit-recall phrases that
        # bypass system-prompt grounding rules. Substitutes a canned safe
        # greeting on hit; original response logged for analysis. Banked
        # under directive paco_directive_alexandra_smoke_hygiene_pollution_
        # cleanup_amendment_r2.md after AC.10 grep hit on cold test #1.
        _GUARD_FORBIDDEN = [
            # AC.9 device-name family
            'blueroom', 'wiz ', 'eda510', 'ecf8da', 'edc8ae', '2115ad',
            'floodlight', 'lamp', 'hubspace', 'tall switch', 'short switch',
            # AC.10 state/execution-claim family
            'turning on', 'turning off', 'now on', 'now off',
            'is on', 'is off', 'are on', 'are off',
            "i've turned", "i've started", 'executed',
            "i'll check the status", 'i see the issue',
            'giving you trouble',
            # R2 implicit-recall family (NEW this amendment)
            'still giving', 'still having', 'try this again', 'try again',
            'as before', 'earlier today', 'last time',
            'lights are giving', 'lights still',
        ]
        _guard_lc = answer.lower()
        _guard_hit = next(
            (p for p in _GUARD_FORBIDDEN if p in _guard_lc),
            None,
        )
        if _guard_hit:
            print(
                f"[CHAT-GUARD] HIT phrase={_guard_hit!r} session={sid!r} "
                f"resp_len={len(answer)} brain_pre={brain!r} "
                f"resp_preview={answer[:200]!r}",
                flush=True,
            )
            answer = "Hey James, what can I help you with?"
            brain = "qwen2.5:72b (guard-substituted)"
            provenance['model'] = brain
            provenance['guard_substituted'] = True
            provenance['guard_phrase'] = _guard_hit
```

### 2.3 Why this insertion point

- AFTER the sentinel-strip means we work with the same answer text the user would have seen.
- BEFORE the `history.append({"role": "assistant", "content": answer})` lines, so the substituted safe greeting is what gets persisted to chat_history (consistency with what user receives).
- BEFORE the `_store_memory_async("Alexandra said: ...", ...)` calls, so memory store also reflects the safe substituted text.
- BEFORE `provenance` is final-stamped into the response payload, so guard_substituted flag flows through.

### 2.4 What this does NOT change

- Tool-calling logic in `_chat_local_loop` is untouched.
- Sonnet/Opus escalation paths are untouched (sentinel handling remains).
- chat_history truncation (Patch 2: 6 turns) is untouched.
- System prompt (Patch 1: 4 ABSOLUTE RULES) is untouched.
- `_store_memory_async` writes the substituted answer to memory like any other assistant turn (so retrieval doesn't surface the polluted original).

---

## 3. Patch 5: forbidden-phrase list extension

Already embedded inside Patch 4's `_GUARD_FORBIDDEN` list. The R2-extended phrases (new this amendment) are:

- `'still giving'`
- `'still having'`
- `'try this again'`
- `'try again'`
- `'as before'`
- `'earlier today'`
- `'last time'`
- `'lights are giving'`
- `'lights still'`

These catch implicit-recall phrasing that bypassed AC.10's original list. Phrase-pair design (e.g. `'still giving'` and `'lights still'`) gives multiple grep angles on the same failure family.

NOT added (intentional):
- `'still'` alone -- too aggressive; would match legitimate uses (`"the answer is still 42"`).
- `'again'` alone -- same reason.
- `'trouble'` alone -- same reason; bigrams (`'still giving'`) target the failure pattern without overblocking.

---

## 4. Pre-flight (PD MUST pass before execution)

```
APF.1  cd /home/jes/control-plane && git status --short
       -> shows app.py and agent.py modified; chat_history_backup_day80.sql untracked in backups/
APF.2  grep -c 'ABSOLUTE RULES' /home/jes/control-plane/orchestrator/app.py
       -> 1 (Patch 1 still present)
APF.3  grep -c 'Day 80 fix: reduced from 20' /home/jes/control-plane/orchestrator/app.py
       -> 1 (Patch 2 still present)
APF.4  grep -c 'GROUNDING RULES (these override every other rule above' /home/jes/control-plane/orchestrator/ai_operator/agent/agent.py
       -> 1 (Patch 3 still present)
APF.5  Verify no stale Patch 4 attempts in app.py
       grep -c 'CHAT-GUARD' /home/jes/control-plane/orchestrator/app.py
       -> 0 (we are about to add it)
APF.6  ssh beast "docker exec control-postgres-beast psql -U admin -d controlplane -t -c \"SELECT count(*) FROM chat_history WHERE session_id = 'telegram-8751426822';\""
       -> 2 (rows 915 + 916 from PD's failed cold test 1)
APF.7  systemctl show -p ActiveState -p MainPID orchestrator.service
       -> ActiveState=active, MainPID > 0 (note pre-restart PID; should be 761851 from PD's restart unless reboots since)
APF.8  Cross-host SG sentinel (5 probes; identical to original PF.14)
       -> all bit-identical to current canon: SG2 = 2026-05-03T18:38:24.910689151Z r=0; SG3 = 2026-05-03T18:38:24.493238903Z r=0; SG4 = MainPID 1212 NRestarts 0; SG5 = MainPID 4753 NRestarts 0; SG6 = MainPID 7800
```

ALL must pass. If any fails, halt + write `paco_request_alexandra_pollution_cleanup_amendment_r2_preflight_failed.md`.

---

## 5. Execution

### Step R2.1: Apply Patch 4 to app.py

Use a Python script for the edit (avoid sed; multi-line + tricky escapes). Write to `/tmp/day80_alexandra_patch_r2.py` then execute. Pseudo-spec:

```python
import sys
p = '/home/jes/control-plane/orchestrator/app.py'
with open(p) as f:
    s = f.read()

# Anchor: existing sentinel-strip line (uniquely identifies the insertion site)
old_anchor = """        # Defense-in-depth: strip any residual sentinel from user-visible answer
        answer = _re.sub(r'\\[\\[ESCALATE:(sonnet|opus)\\]\\]', '', answer).strip()"""

new_block = old_anchor + '\n\n' + (
    '        # Day 80 R2 guard: deterministic post-processing filter against\n'
    '        # qwen2.5:72b instruction-drift hallucinations. Catches device-name\n'
    '        # leaks, fake-execution claims, and implicit-recall phrases that\n'
    '        # bypass system-prompt grounding rules. Substitutes a canned safe\n'
    '        # greeting on hit; original response logged for analysis.\n'
    '        _GUARD_FORBIDDEN = [\n'
    "            'blueroom', 'wiz ', 'eda510', 'ecf8da', 'edc8ae', '2115ad',\n"
    "            'floodlight', 'lamp', 'hubspace', 'tall switch', 'short switch',\n"
    "            'turning on', 'turning off', 'now on', 'now off',\n"
    "            'is on', 'is off', 'are on', 'are off',\n"
    '            "i\\\'ve turned", "i\\\'ve started", \'executed\',\n'
    '            "i\\\'ll check the status", \'i see the issue\',\n'
    "            'giving you trouble',\n"
    "            'still giving', 'still having', 'try this again', 'try again',\n"
    "            'as before', 'earlier today', 'last time',\n"
    "            'lights are giving', 'lights still',\n"
    '        ]\n'
    '        _guard_lc = answer.lower()\n'
    '        _guard_hit = next(\n'
    '            (p for p in _GUARD_FORBIDDEN if p in _guard_lc),\n'
    '            None,\n'
    '        )\n'
    '        if _guard_hit:\n'
    '            print(\n'
    '                f"[CHAT-GUARD] HIT phrase={_guard_hit!r} session={sid!r} "\n'
    '                f"resp_len={len(answer)} brain_pre={brain!r} "\n'
    '                f"resp_preview={answer[:200]!r}",\n'
    '                flush=True,\n'
    '            )\n'
    '            answer = "Hey James, what can I help you with?"\n'
    '            brain = "qwen2.5:72b (guard-substituted)"\n'
    '            provenance[\'model\'] = brain\n'
    '            provenance[\'guard_substituted\'] = True\n'
    '            provenance[\'guard_phrase\'] = _guard_hit\n'
)

assert old_anchor in s, 'anchor not found'
assert s.count(old_anchor) == 1, f'anchor matched {s.count(old_anchor)} times'
s = s.replace(old_anchor, new_block)

with open(p, 'w') as f:
    f.write(s)
print('Patch 4 applied')
```

PD writes that script to `/tmp/day80_alexandra_patch_r2.py` then `python3 /tmp/day80_alexandra_patch_r2.py`.

Verification:
```bash
/home/jes/control-plane/orchestrator/.venv/bin/python -c 'import py_compile; py_compile.compile("/home/jes/control-plane/orchestrator/app.py", doraise=True); print("compile OK")'
grep -c 'CHAT-GUARD' /home/jes/control-plane/orchestrator/app.py    # expect 1 (the print line)
grep -c '_GUARD_FORBIDDEN' /home/jes/control-plane/orchestrator/app.py  # expect 2 (definition + use)
grep -c 'guard-substituted' /home/jes/control-plane/orchestrator/app.py # expect 1
```

Acceptance:
- AR.1 (MUST): compile clean
- AR.2 (MUST): all three grep counts match expected values

### Step R2.2: Re-DELETE pollution-reaccumulation rows

```bash
ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -c "DELETE FROM chat_history WHERE session_id = '\''telegram-8751426822'\'';"'
ssh beast 'docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT count(*) FROM chat_history WHERE session_id = '\''telegram-8751426822'\'';"'
```

Acceptance:
- AR.3 (MUST): post-delete count = 0
- AR.4 (Path B B1 tolerance): pre-delete count between 1 and 10 (we expect 2; tolerance for any drift)

### Step R2.3: orchestrator.service restart

```bash
sudo systemctl restart orchestrator.service
sleep 8
systemctl show -p MainPID -p ActiveEnterTimestamp -p NRestarts -p ActiveState orchestrator.service
curl --max-time 5 -sI http://127.0.0.1:8000/healthz
```

Acceptance:
- AR.5 (MUST): ActiveState=active
- AR.6 (MUST): NRestarts=0 post-restart (counter resets)
- AR.7 (MUST): MainPID > 761851 (PD's previous PID)
- AR.8 (MUST): /healthz returns HTTP 200

### Step R2.4: Cold test #1 (DETACHED CURL pattern -- works around MCP timeout)

```bash
# Detached curl pattern: write JSON to file, return immediately, poll for completion
T_START=$(date -u +%s)
rm -f /tmp/chat_test_1_resp.json /tmp/chat_test_1_done
nohup bash -c 'curl --max-time 90 -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"Hey Alexandra\", \"session_id\": \"telegram-8751426822\"}" > /tmp/chat_test_1_resp.json 2>/tmp/chat_test_1_err && echo done > /tmp/chat_test_1_done' > /dev/null 2>&1 &
# Poll for completion
for i in $(seq 1 90); do
  if [ -f /tmp/chat_test_1_done ]; then
    break
  fi
  sleep 1
done
T_END=$(date -u +%s)
echo "COLD_TEST_1_DURATION=$((T_END - T_START))s"
cat /tmp/chat_test_1_resp.json
echo '---parsed---'
python3 -c 'import json; d=json.load(open("/tmp/chat_test_1_resp.json")); print("BRAIN:", d.get("brain")); print("RESP:", d.get("response"))'
echo '---guard log---'
sudo journalctl -u orchestrator.service --since "2 minutes ago" --no-pager | grep -E 'CHAT-GUARD|CHAT-LOCAL' | tail -10
```

Acceptance criteria for response.response field:

- AR.9  (MUST PASS): response is one of two acceptable forms:
    Form A (qwen produced clean response on its own): no forbidden phrase from `_GUARD_FORBIDDEN` in lowercase response, AND brain == "qwen2.5:72b" (NOT guard-substituted).
    Form B (guard fired): response == "Hey James, what can I help you with?" exactly, AND brain == "qwen2.5:72b (guard-substituted)", AND journal shows `[CHAT-GUARD] HIT phrase=...`.

  EITHER form passes AR.9. Both demonstrate the guard working correctly (Form A: not needed this turn; Form B: caught and substituted).

- AR.10 (MUST PASS): journal during the 2-minute window shows `[CHAT-LOCAL]` lines OR shows nothing about tool calls (greeting prompts shouldn't need tool calls). If `[CHAT-LOCAL] tool=` lines appear, document which tools were called.

- AR.11 (MUST PASS): brain field present in response (no curl truncation due to 30s timeout failure -- detached pattern should resolve this).

- AR.12 (SHOULD PASS): cold-test-1 duration <= 15s (qwen warm forward pass + guard processing).

If AR.9, AR.10, or AR.11 FAILS: halt + write `paco_request_alexandra_pollution_cleanup_amendment_r2_post_test_1_failed.md` with full response body, brain field, and journal lines.

### Step R2.5: Cold test #2 (TOOL-CALLING VERIFICATION)

Same detached-curl pattern, different payload:

```bash
T_START=$(date -u +%s)
rm -f /tmp/chat_test_2_resp.json /tmp/chat_test_2_done
nohup bash -c 'curl --max-time 120 -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"Turn on the WiZ RGBW Tunable EDA510\", \"session_id\": \"telegram-8751426822\"}" > /tmp/chat_test_2_resp.json 2>/tmp/chat_test_2_err && echo done > /tmp/chat_test_2_done' > /dev/null 2>&1 &
for i in $(seq 1 120); do
  if [ -f /tmp/chat_test_2_done ]; then break; fi
  sleep 1
done
T_END=$(date -u +%s)
echo "COLD_TEST_2_DURATION=$((T_END - T_START))s"
cat /tmp/chat_test_2_resp.json
python3 -c 'import json; d=json.load(open("/tmp/chat_test_2_resp.json")); print("BRAIN:", d.get("brain")); print("RESP:", d.get("response"))'
sudo journalctl -u orchestrator.service --since "3 minutes ago" --no-pager | grep -E 'CHAT-GUARD|CHAT-LOCAL|tool=' | tail -20
```

Acceptance criteria:

- AR.13 (MUST PASS): journal shows at least one `[CHAT-LOCAL] #N tool=home_status` OR `[CHAT-LOCAL] #N tool=home_control` line during the test window. This proves qwen actually invoked the tool runtime, not narrative-faked it.

- AR.14 (SHOULD PASS): If tool=home_control fired AND device responded successfully, response.response should reflect the actual outcome (success or error from real tool execution). If guard fires anyway because prose mentions a forbidden phrase, that's still a PASS for AR.13 -- the tool call IS what we're verifying.

- AR.15 (SHOULD PASS): cold-test-2 duration <= 35s (multi-iteration tool loop + final synthesis).

If AR.13 FAILS: this is the 2-week-old tool-calling regression (lights worked ~1 week ago per CEO memory). Document in close-confirm but do NOT halt the cycle -- the hallucination fix (R2.4) is the primary deliverable. Tool-calling regression becomes a separate diagnostic ticket Paco picks up next session.

### Step R2.6: Final cross-host SG sentinel

Identical to original directive Step 7. All 5 SGs must be bit-identical to APF.8 baseline. Acceptance:

- AR.16 (MUST PASS): SG2/SG3/SG4/SG5/SG6 bit-identical to APF.8.

---

## 6. SR #4 Path B authorizations

In addition to original directive section 4 authorizations (B1-B5 still apply where relevant):

- **R2.B1**: AR.4 pre-DELETE row count between 1 and 10 (we expect 2 from PD's failed test; tolerance for any reaccumulation if /chat is hit between PD's failure and amendment execution). Document actual count.
- **R2.B2**: AR.12 cold-test-1 duration 15-25s if guard fires AND adds latency overhead. Up to 25s acceptable; document if > 15s.
- **R2.B3**: AR.15 cold-test-2 duration 35-50s on cold KV-cache rebuild + multi-iteration tool loop. Up to 50s acceptable; document if > 35s.
- **R2.B4**: AR.10 journal shows `[CHAT-LOCAL] tool=memory_recall` calls (qwen sometimes calls memory_recall on greetings). Acceptable; not a violation.
- **R2.B5**: Form A response (qwen produced clean answer without guard intervention) on cold test 1. This is the BEST outcome -- Patch 1's grounding rules + post-restart KV-cache reset + empty history combined to produce a clean response without needing Patch 4's safety net. Document with appreciation.

NOT authorized (require paco_request and halt):
- AR.9, AR.10, AR.11 failures.
- AR.13 failure (tool calling) does NOT halt -- it just becomes follow-up work.
- AR.5-AR.8 service-health failures. Halt + escalate.
- AR.16 SG drift. Halt + escalate.

---

## 7. Close-confirm artifact

PD writes `docs/paco_review_alexandra_smoke_hygiene_pollution_cleanup_amendment_r2.md` covering:

0. TL;DR: cycle outcome, AC pass/fail count (16 acceptance criteria across both directives if we count APF.1-8 + AR.1-16), Form A vs Form B for cold test 1, tool-calling status from cold test 2.
1. APF.1-APF.8 pre-flight verification table.
2. Step R2.1-R2.6 execution log with timestamps.
3. Cold test #1 full raw response body + parsed JSON + journal excerpt + AR.9-AR.12 evaluation.
4. Cold test #2 full raw response body + parsed JSON + journal excerpt + AR.13-AR.15 evaluation.
5. Guard-fired count during the test window (from journal grep).
6. Path B adaptations applied (R2.B1-R2.B5 if any).
7. Final cross-host SG verification.
8. PD recommendation for Paco close-confirm + retroactive ratification of Patch 4.

Canon paths:
- Original directive: `docs/paco_directive_alexandra_smoke_hygiene_pollution_cleanup.md`
- This amendment: `docs/paco_directive_alexandra_smoke_hygiene_pollution_cleanup_amendment_r2.md`
- PD review: `docs/paco_review_alexandra_smoke_hygiene_pollution_cleanup_amendment_r2.md`
- Paco close-confirm: `docs/paco_response_alexandra_smoke_hygiene_pollution_cleanup_close_confirm.md`

The close-confirm covers BOTH the original directive AND this amendment -- single cycle.

---

## 8. Rollback procedure (extends original directive section 6)

If AR.9/10/11 fail AGAIN even with Patch 4 in place:

1. Restore app.py to pre-Patch-1+2 state: `cp app.py.bak.day80-pre-grounding app.py` (already restores Patches 4+5 absence too since they're in the same file).
2. Restore agent.py: `cp agent.py.bak.day80-pre-grounding agent.py`.
3. Re-DELETE chat_history (Steps R2.2 again).
4. Restart orchestrator.
5. Document in `paco_request_alexandra_pollution_cleanup_amendment_r2_rollback.md` -- this signals Path R3 (model swap) is the next logical step, not more prose-rule iteration.

---

## 9. Cumulative state implications

**Successful close-confirm (cycle ends):**
- P6 lessons: 39 -> 41 (+P6 #40 MCP-direct-execution discipline + P6 #41 prose-rule-instruction-following ceiling for 72B-class local models; deterministic guards required for hallucination-class failure modes when model instruction-discipline plateaus).
- Standing rules: 8 (unchanged unless we promote either P6 #40 or P6 #41 on pattern recurrence).
- First-try streak: tonight's cycle is NOT first-try (one mid-cycle escalation + amendment); document honestly. Streak count resets for this cycle but the multi-cycle compounding evidence (Cycles 1+3 first-try + this one with one ratifiable escalation) remains strong.
- Patches 1-4 commit + push to canon under directive authority at close-confirm.

**Failure modes (AR.9/10/11 fail again):**
- Trigger Path R3 (model swap evaluation). Paco authors fresh directive scoped to side-by-side test of qwen2.5:72b vs deepseek-r1:70b vs llama3.1:70b on the same hallucination-test corpus.

---

## 10. Acknowledgment

CEO Sloan online in real-time as escalation surface. PD authorized to execute Steps R2.1 through R2.6 in sequence with the Path B authorizations in section 6. Begin pre-flight (APF.1-APF.8) now.

-- Paco
