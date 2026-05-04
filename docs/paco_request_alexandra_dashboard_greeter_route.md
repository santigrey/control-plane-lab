# paco_request_alexandra_dashboard_greeter_route

**To:** Paco (P1) | **From:** PD | **Date:** 2026-05-04 (Day 80)
**Cycle:** Investigation deliverable for `paco_directive_alexandra_dashboard_persona_polarity_and_greeter`
**Repo HEAD at investigation:** cfd9f8acda81c29a62b4a5eb17bb7d089889dd14
**Mode:** Investigation-only. No code changed. No services restarted.

---

## 0. TL;DR

Three findings, all proven against running infrastructure:

1. **Bug 1 (page-load greeter)** — The greeter is NOT a `/chat` or `/chat/private` call. It is `POST /vision/analyze` (defined in `orchestrator/app.py` line 2045), called by JS function `autoGreet()` (`dashboard.py` line 165), triggered by `setTimeout(autoGreet, 300)` inside `startSession()` (line 217), which fires when the user clicks the `start-overlay` element rendered at line 93. The endpoint hardcodes a companion-mode persona system prompt with literal example strings `'Hey my love...'` and `'Hey babe...'` (app.py lines 2081–2095). The endpoint takes no `private`/`intimate` parameter and the client-side `autoGreet()` makes zero references to `privateMode`. localStorage cannot gate this route because the route never consults it.

2. **Bug 2 (queue:1 badge)** — Paco's forensics queried the wrong database. The orchestrator's `DATABASE_URL` resolves to `192.168.1.10:5432/controlplane` (the `control-postgres` pgvector container running on CiscoKid). DPF.5 in the directive queried `control-postgres-beast` on TheBeast — a different instance. The CiscoKid DB has exactly 1 open-status row in `public.agent_tasks`: id `6d5102a5-93e8-4972-846f-9acbabe2b795`, status=`approved`, title=`B2a SHIPPED — PostgreSQL on Beast (7/7 gates PASS, awaiting independent verification)`, assigned_to=`paco`, feedback=`done`, created 2026-04-26. The dashboard JS at line 145 filters `status==='pending_approval' || status==='approved'` from `/dashboard/agent_tasks` and renders the sum as the queue badge. `qc = 0 + 1 = 1`. The badge is correct; it is reflecting a real row that was never moved to a terminal state.

3. **Bug 3 (localStorage line 133)** — Confirmed correct. `let privateMode=localStorage.getItem('alexandra_private')==='1';` evaluates `null === '1'` to false on first load, defaulting to professional/Alexandra mode. No fix needed.

The recurring CFC-clears-localStorage-but-greeter-still-companion symptom is fully explained by Bug 1: the greeter never consulted localStorage. Bugs 1 and 3 are decoupled.

---

## 1. Pre-flight DPF.1 – DPF.7 results

| Probe | Result | Pass |
|---|---|---|
| DPF.1 | `dashboard.py` exists, 60057 bytes, mtime 2026-05-01 23:08 | YES |
| DPF.2 | `grep -c privateMode` = 5 (>= 4 required) | YES |
| DPF.3 | dashboard route NOT in app.py — defined as APIRouter in `dashboard.py` line 5, mounted in `app.py` line 36 (`app.include_router(dashboard_router)`). Directive's grep regex did not match because the route lives on the router, not on `app`. | YES (corrected target) |
| DPF.4 | `/dashboard/agent_tasks` route is in `dashboard.py` line 377, NOT `app.py` (same reason as DPF.3). | YES (corrected target) |
| DPF.5 | Directive's query targeted `control-postgres-beast` on TheBeast; returned 0 open rows. CORRECT-TARGET query (CiscoKid `control-postgres` container, where orchestrator actually points) returns 1 approved row. See Bug 2 section. | NO (mis-targeted by directive) |
| DPF.6 | `orchestrator.service` ActiveState=active, MainPID=1215999 | YES |
| DPF.7 | Cross-host SG sentinel — not executed this session; no canon script located in repo at investigation time. Flagging for Paco. | DEFERRED |

**DPF.7 deferral note:** the directive cites `Cross-host SG sentinel (5 probes; same as smoke hygiene cycle)` but I did not locate a sentinel script under `scripts/`, `tools/`, or `docs/` referencing SG2-SG6. If Paco wants this run, point at the canonical script path in the next directive.

---

## 2. Bug 1 root cause — page-load greeter route

### Trigger chain (verified in `dashboard.py`)

```
HTML line 93:  <div id="start-overlay" onclick="startSession()">click anywhere to begin</div>
JS  line 217: function startSession(){ ov.remove(); setTimeout(autoGreet, 300); }
JS  line 165: async function autoGreet() { ... await fetch('/vision/analyze', {method:'POST', body: <webcam-jpeg>}) ... appendMsg('alex', vd.description) ... fetch('/voice/speak', ...) ... }
```

### Why nginx shows zero POST /chat or POST /chat/private

Because the greeter never hits those routes. The greeter route is `POST /vision/analyze`. Nginx access log confirms continuous `POST /vision/analyze` 200 hits with `Referer: /dashboard` and matching User-Agent. Sample (CiscoKid `/var/log/nginx/access.log`, last 20 min at 15:43 UTC):

```
100.102.87.70 - - [04/May/2026:15:16:49 +0000] "POST /vision/analyze HTTP/1.1" 200 358 "https://sloan3.tail1216a3.ts.net/dashboard"
100.102.87.70 - - [04/May/2026:15:34:54 +0000] "POST /vision/analyze HTTP/1.1" 200 108 ...
100.102.87.70 - - [04/May/2026:15:36:07 +0000] "POST /vision/analyze HTTP/1.1" 200 126 ...
... (continuous)
```

### Why it always greets in companion-mode

`vision_analyze` in `orchestrator/app.py` line 2045 has two branches:
- `if prompt:` (form field) → professional system prompt, only used by `captureWebcam()` button path that passes a prompt.
- `else:` (no prompt — the autoGreet path) → hardcoded companion-mode system prompt at lines 2081–2095, with literal `'Hey my love'` and `'Hey babe'` example strings in the prompt.

The endpoint then calls `claude-haiku-4-5-20251001` with that system prompt. The persona vocabulary Sloan reports ("Hey love / Hey babe / you look calm and centered") is generated directly by Haiku from this hardcoded prompt — not by `_chat_persona_handler`, not by `/chat/private`.

### Why localStorage clearing does nothing

`autoGreet()` does not read `localStorage`, does not reference `privateMode`, and does not pass any flag to `/vision/analyze`. The endpoint always uses the persona prompt when called without a `prompt` form field. Clearing the `alexandra_private` key has no effect because the greeter never consults it.

### Architecture finding (SR #4 Path B / DB2)

Not HTMX, not websocket. Plain `fetch('/vision/analyze', {method:'POST', body: FormData(<webcam-jpeg>)})` from a vanilla JS function bound to a click handler on a full-screen overlay. The illusion of "on refresh" is because the overlay reappears on every page load and Sloan typically clicks through it within a second.

---

## 3. Bug 2 root cause — queue:1 badge

### The badge calculation (verified in `dashboard.py:145`)

```js
const tr = await fetch('/dashboard/agent_tasks');
const td = await tr.json();
const tks = td.tasks || [];
const pend = tks.filter(t => t.status === 'pending_approval').length;
const appr = tks.filter(t => t.status === 'approved').length;
const qc = pend + appr;
qb.textContent = 'queue: ' + qc;
```

### The endpoint (verified in `dashboard.py:377`)

```python
@router.get("/dashboard/agent_tasks")
async def dashboard_agent_tasks():
    with psycopg.connect(get_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT id, status, title, assigned_to, result, feedback, created_at, updated_at
                           FROM agent_tasks ORDER BY created_at DESC LIMIT 20""")
            ...
```

`get_db_url()` returns `os.getenv("DATABASE_URL")` (dashboard.py line 7 and memory/db.py line 12).

### The DB the orchestrator actually queries

`systemctl show orchestrator.service` + `/proc/<MainPID>/environ` confirm the running orchestrator has:

```
DATABASE_URL=postgresql://<USER>:<PASS>@192.168.1.10:5432/controlplane
```

That is the `control-postgres` pgvector container running ON CiscoKid (verified `sudo docker ps`: `control-postgres: pgvector/pgvector:pg16 (Up 21 hours (healthy))`).

### Status counts in the actual DB

```
status     | count
-----------+-------
approved   |     1   <-- THIS IS THE QUEUE:1 SOURCE
cancelled  |     2
completed  |    41
failed     |     2
```

### The single approved row

```
id          : 6d5102a5-93e8-4972-846f-9acbabe2b795
status      : approved
title       : B2a SHIPPED — PostgreSQL on Beast (7/7 gates PASS, awaiting independent verification)
assigned_to : paco
feedback    : done
created_at  : 2026-04-26 20:53:49 UTC
```

### Why Paco's forensics said 0 open rows

The directive's DPF.5 query was:
```
ssh beast "docker exec control-postgres-beast psql -U admin -d controlplane -t -c \"SELECT count(*) FROM public.agent_tasks WHERE status NOT IN ('completed', 'cancelled', 'failed', 'rejected');\""
```

That hit `control-postgres-beast` on TheBeast — a different postgres instance from the one the orchestrator queries. The two databases happen to share the schema name and table name but contain different rows. On TheBeast's instance the count IS 0; on CiscoKid's instance the count is 1. The dashboard reads CiscoKid's. There is no caching, no third source, no atlas.tasks involvement — just a target-mismatch in the verification query.

---

## 4. Bug 3 confirmation — localStorage line 133

Current line 133 in `dashboard.py`:

```js
let privateMode = localStorage.getItem('alexandra_private') === '1';
```

`localStorage.getItem(<missing-key>)` returns `null`. `null === '1'` is `false`. So when CFC clears localStorage, the next page load gets `privateMode = false` (professional/Alexandra mode), which is the intended default polarity.

Confirmed correct. **No fix at this line.** Paco's read in directive section 0 paragraph 3 stands.

---

## 5. Recommended fix scope (PD's input — Paco authors final fix-directive)

### Bug 1 — minimum-change patches, options ordered by surgical-ness

**Option A (smallest blast radius, recommended):** Make `autoGreet()` no-op when not in private mode. Single client-side change in `dashboard.py` inside `autoGreet()` body, immediately after `if(_greeted) return;`:

```js
if (!privateMode) { _greeted = true; return; }
```

Two lines. Zero changes to `app.py`. Zero changes to the `/vision/analyze` endpoint contract. Captures the polarity intent: companion mode greets; professional mode does not.

**Option B (gate the endpoint):** Add a `professional` form field passed by `autoGreet()`, branch in `vision_analyze` to use a neutral system prompt when `professional=true`. Larger surface; touches both client and server. Recommended only if Paco wants the professional-mode greeter to also speak (just without persona vocabulary).

**Option C (kill the auto-greet entirely):** Remove the `setTimeout(autoGreet, 300)` line in `startSession()`. Greeter only fires when user clicks the camera button. Simplest of all but changes UX. Sloan should weigh in.

### Bug 2 — minimum-change patches

**Option A (DB only — recommended):** Update the one stale row to `completed` in CiscoKid's `controlplane.public.agent_tasks`:

```sql
UPDATE public.agent_tasks
SET status='completed', updated_at=NOW()
WHERE id='6d5102a5-93e8-4972-846f-9acbabe2b795';
```

One row. Badge clears immediately. Feedback already says `done`; the row was never marked completed by whatever process Paco was running on 2026-04-26. This is the right fix because the badge is correct — the data was wrong.

**Option B (badge logic — NOT recommended):** Change the badge to filter out rows with non-empty `feedback`. Treats symptom not cause. Would mask future stale rows. Skip.

### Bug 3 — no fix

Confirmed already. Document closing this thread.

---

## 6. Patch surface estimate

| Bug | Files touched | LOC changed | Service restart | Risk |
|---|---|---|---|---|
| 1 (Option A) | `dashboard.py` (1 file) | +1 line | likely yes — `HTML` is a module-level constant loaded at import | LOW |
| 2 (Option A) | DB only | 1 SQL UPDATE | none | LOW |
| 3 | nothing | 0 | none | none |

The dashboard JS is inlined in the Python module string, so the `dashboard.py` change requires orchestrator restart for new JS to ship. Confirm in fix-directive.

---

## 7. Open questions for Paco

1. **Restart required for `dashboard.py` JS edit?** Module-level `HTML` constant — almost certainly yes, orchestrator restart needed for the new JS to ship to the browser. Confirm.
2. **Is the `control-postgres-beast` instance still load-bearing for anything?** If two separate `controlplane` databases exist, there's a sync-or-deprecate decision pending. Out of scope for this cycle but worth flagging.
3. **DPF.7 sentinel script path** — if cross-host SG verification is required for this fix cycle, point me at the script.
4. **Auto-greet scope** — does Sloan want the greeter to fire automatically on overlay-click in professional mode at all, or only in companion mode? Drives Option A vs Option C choice.

---

## 8. Status

`AWAITING PACO` — investigation complete, fix-directive pending.

— PD
