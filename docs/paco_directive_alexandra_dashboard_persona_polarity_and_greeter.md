# paco_directive_alexandra_dashboard_persona_polarity_and_greeter

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-04 Day 80 ~09:50 MT (15:50 UTC)
**Cycle:** Alexandra dashboard hygiene -- persona-polarity bug + greeter route + queue-counter staleness (single-cycle)
**Type:** Standalone directive. NOT an amendment to the smoke hygiene cycle (that one closed at d0f0491).
**Authority:** CEO Sloan online in real-time as escalation surface. Reports persistent companion-mode greeting on dashboard refresh after browser localStorage cleared by CFC; reports queue:1 badge persisting after agent_tasks queue cleared in DB.

---

## 0. TL;DR

Three bugs identified by Paco-side forensics on `dashboard.py` + nginx access log + DB state:

1. **Page-load greeter fires companion mode independent of lock state.** Symptom: refreshing the dashboard greets with "Hey love / Hey babe / you look calm and centered" -- pure persona vocabulary -- without any user message having been sent. Forensic evidence: nginx access log for the past 15 minutes shows ZERO POST /chat or POST /chat/private requests from the user's browser, but the user reports persistent companion greeting on refresh. Therefore the greeter is firing on page load, not on user message, and is using a route that produces persona output independent of the localStorage `alexandra_private` flag that gates `sendChat()`.

2. **Queue:1 badge sourced from somewhere other than `public.agent_tasks` open-status filter.** Forensic evidence: agent_tasks now has 0 rows in pending_approval/approved/in_progress (only completed/cancelled/failed terminal states); but the dashboard still renders queue:1 in the header. Likely source: `/healthz` `worker.queued_tasks` reads from `public.tasks` (not `agent_tasks`) and that table has 0 queued/running rows currently -- so the queue counter is either (a) reading from a third source PD must identify, (b) reading from `/dashboard/agent_tasks` GET endpoint which has its own status filter, or (c) cached browser-side. nginx access log shows continuous polling of `GET /dashboard/agent_tasks` returning 8359 bytes -- that is the source endpoint to inspect.

3. **`alexandra_private` localStorage default polarity wrong on first load.** Code at `dashboard.py:133`: `let privateMode = localStorage.getItem('alexandra_private') === '1';` -- this defaults to false (professional/Alexandra mode) when the key is absent, which is correct semantics. BUT user reports CFC cleared localStorage and the next refresh STILL greeted in companion mode. This confirms bug 1 (the greeter does not consult `privateMode`); it is not a bug in this line. Document the line as correct, do not modify it.

---

## 1. Read-only forensics already complete (Paco-side; PD ratifies at pre-flight)

| Probe | Result |
|---|---|
| Dashboard source location | `/home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py` (60057 bytes, last modified May 1 23:08) |
| Backups present | `dashboard.py.bak` + `.bak.20260402_062724` + `.bak.greet` + `.bak.toggle.1776838868` |
| `_chat_persona_handler` callers in app.py | Only line 1655 (inside `/chat/private` when `intimate=true`); NOT called from `/chat` |
| nginx 15-min log POST /chat count | 0 (verified at 09:44 MT) |
| nginx 15-min log POST /chat/private count | 0 (verified at 09:44 MT) |
| nginx 15-min log GET /dashboard/agent_tasks count | continuous polling, 200 8359 bytes |
| public.agent_tasks status counts | 2 cancelled / 42 completed / 2 failed (NO open-status rows) |
| public.tasks status counts | 81 succeeded / 2 failed (NO queued/running rows) |
| atlas.tasks status counts | 9175 done / 1 failed / 4 running (4 running rows from 2026-05-01 race tests; might be the queue:1 source) |

## 2. Pre-flight verification (PD MUST PASS before execution)

```
DPF.1  ls -la /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py
       -> exists, ~60KB
DPF.2  grep -c 'privateMode' /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py
       -> >= 4 (toggle + sendChat + voice + updatePrivateUI)
DPF.3  grep -nE 'def get_dashboard_html|def dashboard|@app.get.*dashboard' /home/jes/control-plane/orchestrator/app.py
       -> identifies the route handler that serves /dashboard
DPF.4  grep -nE '@app.get..\"\/dashboard\/agent_tasks' /home/jes/control-plane/orchestrator/app.py
       -> identifies queue counter source endpoint
DPF.5  ssh beast "docker exec control-postgres-beast psql -U admin -d controlplane -t -c \"SELECT count(*) FROM public.agent_tasks WHERE status NOT IN ('completed', 'cancelled', 'failed', 'rejected');\""
       -> 0
DPF.6  systemctl show -p MainPID -p ActiveState orchestrator.service
       -> active, MainPID > 0
DPF.7  Cross-host SG sentinel (5 probes; same as smoke hygiene cycle)
       -> SG2-SG6 bit-identical to canon
```

ALL must pass. If any fails, halt + write paco_request.

## 3. Investigation step (PD does this BEFORE any code change)

PD investigates the page-load greeter. The dashboard's HTML/JS template lives inside `dashboard.py` as Python string literals. Search for:

- Any `fetch(` call inside the dashboard JS that fires on page load (not on user click)
- Any `<script>` block that runs on `DOMContentLoaded` or `window.onload`
- Any auto-greet logic, auto-message logic, or session-bootstrap call
- Any `appendMsg('alex', ...)` call that runs without prior user input

Write findings into a paco_request file:
`docs/paco_request_alexandra_dashboard_greeter_route.md`

DO NOT patch yet. The investigation surfaces what to patch.

## 4. Investigation step for queue:1

PD investigates the queue counter:

- Find where `/dashboard/agent_tasks` is implemented in `app.py`
- Confirm what status filter it applies (likely something like `WHERE status IN ('pending_approval', 'approved', 'in_progress')` or similar)
- If filter includes a status not in the canonical 4 (cancelled/completed/failed/approved we have), find what status the row(s) actually have
- Sample the JSON response: `curl -s https://sloan3.tail1216a3.ts.net/dashboard/agent_tasks | head -100`
- Identify the row(s) showing as queue:1

Write findings into the same paco_request file.

## 5. Investigation step for the page-load greeter route

If bug 1's investigation surfaces that the greeter calls a specific endpoint on page load, PD documents:

- Which endpoint it hits
- What request body it sends
- Whether it consults `privateMode` before calling
- What system prompt the endpoint uses

This is critical -- without knowing the route, we can't fix the bug. **Likely candidates** (PD verifies which):
- A `/chat/greet` or `/dashboard/greet` route
- An auto-call to `/chat` with a synthetic message like "Hello"
- A direct call to `/chat/private?intimate=1` ignoring `privateMode`

## 6. SR #4 Path B authorizations

- **DB1**: queue:1 source might be a 4th table I haven't found (e.g. `pending_events`, `messages` with status filter). PD authorized to expand search to all tables in `controlplane` DB without paco_request. Document.
- **DB2**: page-load greeter might use HTMX or websocket instead of fetch. PD authorized to inspect any client-side JS framework usage. Document.
- **DB3**: if the greeter route is found to be a direct call to `_chat_persona_handler` from server-side rendering (not client fetch), PD authorized to document the architecture without proposing fix yet. Halt at investigation; write paco_request with findings.

NOT authorized: any code change. This directive is **investigation-only**. PD writes paco_request with findings; Paco authors a fix-directive based on those findings.

## 7. Why investigation-only

Last night's pattern was: I write a fix directive based on incomplete forensics; PD executes; symptom persists; we amend; symptom persists again. The pattern is broken because we are patching code paths that aren't the symptom source.

This directive enforces evidence-before-action: PD finds the actual route that's firing the greeter, finds the actual table feeding queue:1, then we know what to fix. No patching until we know.

## 8. Deliverable

PD writes `docs/paco_request_alexandra_dashboard_greeter_route.md` containing:

0. TL;DR of findings
1. Pre-flight DPF.1-DPF.7 results table
2. **Bug 1 root cause**: which route fires the greeter, what system prompt it uses, why localStorage doesn't gate it
3. **Bug 2 root cause**: which table/endpoint feeds queue:1, which row(s) are showing
4. **Bug 3 confirmation**: that line 133 is correct, no fix needed there
5. PD's recommendation for fix scope: minimum-change patch to make greeter consult `privateMode` (or never auto-greet on page load); minimum-change patch to make queue counter reflect cleared state
6. Estimated patch surface (lines of code, files touched, services to restart)

Then Paco authors a fix-directive based on PD's findings. **Two directives total**: this investigation directive + a follow-up fix directive after Paco reads PD's request.

## 9. CEO escalation surface

CEO Sloan is online and in real-time. Any halting condition surfaces to him directly, not to a paco_request queue.

-- Paco
