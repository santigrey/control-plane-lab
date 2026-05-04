# paco_review_alexandra_dashboard_greeter_and_queue_badge_fix

**To:** Paco (P1) | **From:** PD (Cowork) | **Date:** 2026-05-04 Day 80 ~13:45 MT (~19:45 UTC)
**Cycle:** Alexandra fix — Bug 1 greeter polarity + Bug 2 stale queue:1 badge (bundled close-confirm)
**Directive:** `docs/paco_directive_alexandra_dashboard_greeter_and_queue_badge_fix.md`
**Companion investigation:** `docs/paco_request_alexandra_dashboard_greeter_route.md`
**Repo HEAD at directive author:** `f75ee85`
**Cumulative state at author:** P6=44, SR=8
**v2.2 governance:** First execution under v2.2 (session-start boot protocol active; DB forensic discipline applied; execution-lane gates active).

---

## 0. TL;DR

8/8 MUST-PASS AC = PASS. 3/3 SHOULD-PASS AS = PASS (AS.2 with non-fatal MQTT startup-transient note). ZERO rollback required.

- **Bug 1 +1-line patch** shipped to `dashboard.py` at L167. Orchestrator restarted clean (MainPID 1215999 → 1551163; /healthz 200).
- **Bug 2 single-row UPDATE** committed on CK primary container `control-postgres` (192.168.1.10:5432), replicated to Beast `control-postgres-beast` in <10s (B2b logical replication verified).
- **Behavioral proof** from nginx access.log: 0 `POST /vision/analyze` across ~2h41m of CEO UI activity in professional mode (AC.5); 1 hit at 20:29:13 UTC from CEO companion-mode regression test (AC.6). Pre-patch baseline from PD investigation: continuous hits on every page load.
- **Standing gates 6/6 bit-identical pre/post**.
- **2 B0 adaptations** applied (Paco source-surface errors corrected at execution time per first-cycle B0 standing meta-authority).

---

## 1. Pre-flight (DPF.1–DPF.7)

All gates PASS first-try. No B0 adaptation needed at preflight.

| Gate | Probe | Paco-stated expectation | PD-observed | Result |
|---|---|---|---|---|
| DPF.1 | `stat -c '%s %y' dashboard.py` | ~60057 bytes, mtime older than directive | `60057 2026-05-01 23:08:26.003450808 +0000` | PASS |
| DPF.2 | `grep -c '_greeted=true'` | 1 (anchor uniqueness) | 1 | PASS |
| DPF.3 | `sed -n '165,167p'` | 3-line anchor verbatim | bit-identical match | PASS |
| DPF.4 | CK primary row presence | 1 row, status=`approved` | id=`6d5102a5-93e8-4972-846f-9acbabe2b795` status=`approved` updated_at=`2026-04-26 21:11:47.414084+00` | PASS |
| DPF.5 | open-status row count | 1 (only the targeted row) | 1 | PASS |
| DPF.6a | CK mercury PID | 7800 | 7800 | PASS |
| DPF.6b | Beast atlas-mcp | PID 1212 active | 1212 active | PASS |
| DPF.6b | Beast atlas-agent | PID 4753 NRestarts=0 active | 4753 NRestarts=0 active | PASS |
| DPF.6c | Beast postgres anchor | `2026-05-03T18:38:24.910689151Z r=0` | bit-identical | PASS |
| DPF.6d | Beast garage anchor | `2026-05-03T18:38:24.493238903Z r=0` | bit-identical | PASS |
| DPF.7 | backup dir writable | writable | writable | PASS |

**Rollback bit-identicality value captured at DPF.4:** original `updated_at=2026-04-26 21:11:47.414084+00` (preserved here for audit; rollback not triggered).

---

## 2. Execution (Step 1–6)

One step at a time per SR #3. Each step gated on explicit CEO approval (`a`).

### Step 1 — Backup dashboard.py (CiscoKid)

```
cp dashboard.py dashboard.py.bak.day80-pre-greeter-fix
ls -la ...bak.day80-pre-greeter-fix
cmp -s dashboard.py dashboard.py.bak.day80-pre-greeter-fix && echo BACKUP_BIT_IDENTICAL
```

Output:
```
-rw-rw-r-- 1 jes jes 60057 May  4 17:45 ...bak.day80-pre-greeter-fix
BACKUP_BIT_IDENTICAL
```

### Step 2 — Patch dashboard.py (CiscoKid; Python heredoc atomic replace)

PD tooling choice (directive gave PD discretion: sed, python, or editor): Python heredoc with `str.replace` + count-asserts. Chosen for: deterministic count invariant (assert anchor count == 1), no sed `\n`-in-replacement hazard, atomic write.

Anchor (3 lines) → Replacement (4 lines, +1 new):
```
async function autoGreet(){
  if(_greeted)return;
  if(!privateMode){_greeted=true;return;}   ← new line at L167
  _greeted=true;
```

Output:
```
PATCH_APPLIED
-- grep !privateMode count --
2
-- sed 165-169 --
async function autoGreet(){
  if(_greeted)return;
  if(!privateMode){_greeted=true;return;}
  _greeted=true;
  const vs=document.getElementById('voice-status');
-- wc -l --
989 dashboard.py
-- diff backup vs current --
166a167
>   if(!privateMode){_greeted=true;return;}
```

**B0 adaptation #1 applied here:** grep count expected 1 → observed 2. See §5. Patch itself landed verbatim per diff + sed + wc.

Stop condition (diff = +1 -0 at 166a167 AND wc -l = 989): MET under B0. Proceeded on CEO approval.

### Step 3 — Restart orchestrator.service (CiscoKid)

Output:
```
MainPID=1551163
ActiveState=active
ActiveEnterTimestamp=Mon 2026-05-04 17:48:15 UTC
HTTP=200
```

New MainPID != 1215999 (pre-restart); ActiveState=active; /healthz GET = 200. All stop conditions met.

### Step 4 — CK primary single-row UPDATE (CiscoKid)

```
UPDATE public.agent_tasks SET status='completed', updated_at=NOW()
WHERE id='6d5102a5-93e8-4972-846f-9acbabe2b795' AND status='approved'
RETURNING id, status, updated_at;
```

Output:
```
 6d5102a5-93e8-4972-846f-9acbabe2b795 | completed | 2026-05-04 17:48:49.434376+00
(1 row)
UPDATE 1
```

Defensive predicate `AND status='approved'` held: 1 row returned.

### Step 5 — B2b logical replication verification (Beast)

PD tooling adaptation: directive specified `ssh beast` from CK; PD executed directly on Beast via homelab-mcp to avoid nested-quote hazard per hard rule "SSH to the node first, then run bash".

Output (after sleep 10):
```
 6d5102a5-93e8-4972-846f-9acbabe2b795 | completed | 2026-05-04 17:48:49.434376+00
```

Replica timestamp bit-identical to CK primary. B2b logical replication active; lag <10s (likely <1s per historical patterns).

### Step 6 — Behavioral verification

**Part A — PD-side (read-only):**

AC.7 queue count probe via `curl /dashboard/agent_tasks` + python sum filter:
```
OPEN_COUNT=0
```

**Part B — CEO browser-side:**

CEO drove both tests in-session (B4 path not invoked):

- **AC.5 (cold-load professional mode):** CEO launched UI multiple times (default professional, `alexandra_private` cleared). Network tab showed no `/vision/analyze` requests across dashboard document load + initial fetch burst (`dashboard`, `healthz`, `runs`, `agent_tasks`, `daily_brief`, `chat_history_by_date`, `chat_archive`, `wake-detect`). No alex chat bubble appeared before CEO wake-word interactions.
- **AC.6 (companion mode regression):** CEO ran `localStorage.setItem('alexandra_private','1')` + hard-refresh + clicked overlay. Confirmed: lock icon flipped closed/orange (🔒), alex chat bubble appeared within 10s with companion-mode greeter text.

**Authoritative nginx proof from `/var/log/nginx/access.log` (since orch restart 17:48:15 UTC to ~20:38 UTC, ~2h41m window):**

```
[04/May/2026:20:29:13 +0000] "POST /vision/analyze HTTP/1.1" 200 459
Count in window: 1
```

1 hit total at 20:29:13 — precisely the AC.6 companion-mode test timestamp. Zero hits during any professional-mode cold-load. Pre-patch PD investigation baseline (repo HEAD `cfd9f8a`): continuous hits on every dashboard load.

---

## 3. Acceptance criteria

### MUST-PASS (8/8)

| AC | Evidence | Result |
|---|---|---|
| AC.1 dashboard.py diff = +1 -0 | `diff` shows `166a167\n>   if(!privateMode){_greeted=true;return;}` | PASS |
| AC.2 Orch restart clean | MainPID 1551163 (new), ActiveState=active, /healthz GET 200 | PASS |
| AC.3 CK primary row completed | Step 4 RETURNING 1 row status=completed updated_at=2026-05-04 17:48:49.434376+00 (later than Step 4 invocation) | PASS |
| AC.4 Beast replica replicated within 60s | Replica row bit-identical timestamp after 10s sleep; lag <10s | PASS |
| AC.5 Zero `/vision/analyze` in 30s post-overlay-click (prof mode) | Zero hits across entire ~2h41m window during CEO professional-mode activity | PASS |
| AC.6 `/vision/analyze` fires + greeter bubble + lock flip in companion | 1 hit at 20:29:13 + CEO-confirmed lock flip + alex bubble (10s) | PASS |
| AC.7 Queue counter = 0 | `OPEN_COUNT=0` via /dashboard/agent_tasks | PASS |
| AC.8 Standing gates 6/6 bit-identical pre/post | See §4 table | PASS |

### SHOULD-PASS (3/3)

| AS | Evidence | Result |
|---|---|---|
| AS.1 nginx error/warn clean during cycle | Zero entries matching `2026/05/04 1[78]:` in /var/log/nginx/error.log | PASS |
| AS.2 Orchestrator journal clean (no crash backtraces / 5xx surge) | 0 `traceback\|error\|fatal\|critical` in 17:48:00-17:48:30 window; clean shutdown + startup + /healthz 200. **Note:** one expected non-fatal startup transient `MQTT executor failed to connect: [Errno 111] Connection refused` (SlimJim broker reachability lag during brand-new-PID startup; retries and recovers; not introduced by this cycle; appears on every orchestrator restart). | PASS |
| AS.3 `wc -l dashboard.py` drift exactly +1 | 988 (pre) → 989 (post) | PASS |

---

## 4. Standing gates pre/post comparison

| Gate | Pre (DPF.6) | Post (Step 6) | Bit-identical? |
|---|---|---|---|
| SG2 postgres-beast StartedAt + r | `2026-05-03T18:38:24.910689151Z r=0` | bit-identical | YES |
| SG3 garage-beast StartedAt + r | `2026-05-03T18:38:24.493238903Z r=0` | bit-identical | YES |
| SG4 atlas-mcp MainPID | 1212 active | 1212 active | YES |
| SG5 atlas-agent MainPID + NRestarts | 4753 NRestarts=0 active | bit-identical | YES |
| SG6 mercury-scanner MainPID | 7800 | 7800 | YES |
| Orchestrator MainPID (NOT a gate) | 1215999 | 1551163 | EXPECTED CHANGE |

All five canon standing gates (SG2/3/4/5/6) survived cycle with zero drift. Orchestrator MainPID change was required and explicitly excluded from gates per directive §4 AC.8.

---

## 5. Path B applications

**Two B0 standing-meta-authority adaptations applied.** B0 ratified by CEO 2026-05-04 ~11:32 MT for this cycle (directive §5). Both are structural/clerical (Paco source-surface errors); intent preserved.

### B0.1 — `grep -c '!privateMode'` post-patch expected count

- **Paco-stated** (directive §3 Step 2): "Expected first command: exactly 1 hit on the new line."
- **PD-observed:** backup already contained 1 pre-existing `!privateMode` at L134 inside `function togglePrivate(){privateMode=!privateMode;...}` (toggle assignment). Post-patch: 2 hits (L134 pre-existing + L167 new).
- **PD-applied:** corrected expected post-patch count → 2. Patch itself landed verbatim (diff = +1 -0 at 166a167; sed 165-169 exact-match; wc = 989).
- **Rationale:** structural/clerical. Directive's verified-live block grep-checked `_greeted=true` uniqueness (returned 1) but did not pre-check `!privateMode` count in existing source. Intent (professional-mode greeter guard at L167) preserved 100%.

### B0.2 — nginx log source for cold-load probe

- **Paco-stated** (directive §3 Step 6a/6c; §5 B3): `journalctl -u nginx | grep 'POST /vision/analyze'`
- **PD-observed:** first probe using `journalctl -u nginx` returned 0 hits across 5min window despite active CEO traffic. CEO browser-side confirmed AC.6 greeter bubble appeared (greeter did fire) → source-mismatch hypothesis.
- **PD-applied:** re-probed `/var/log/nginx/access.log` directly (matching PD's pre-patch investigation source; access logs are file-only, not journal-piped). Returned exactly 1 hit at 20:29:13 (attributable to AC.6 test).
- **Rationale:** directive B3 covers "`/var/log/nginx/access.log` not present (→ use journalctl)"; PD-observed inverse — access.log IS present, journalctl does NOT capture access logs from nginx in this config. File source is authoritative.

---

## 6. DB forensic discipline (v2.2 P6 #43/44)

- Orchestrator DATABASE_URL target verified via `systemctl cat orchestrator.service` reading `/home/jes/control-plane/orchestrator/.env`; resolved host:port:db = `192.168.1.10:5432/controlplane`.
- CK primary container `control-postgres` (pgvector) — authoritative for writes.
- Beast container `control-postgres-beast` — B2b replica-side; verified replication only, no writes.
- `/proc/<pid>/environ` NOT used (P6 #44). No credentials dumped. Host:port:db quoted; password NOT quoted.

---

## 7. Rollback

NOT EXECUTED. No stop-condition tripped. Backup `dashboard.py.bak.day80-pre-greeter-fix` preserved at `/home/jes/control-plane/orchestrator/ai_operator/dashboard/` for audit/reversibility. Original `updated_at` for row 6d5102a5... preserved in §1 (DPF.4 capture) for row-restore-bit-identicality if ever needed.

---

## 8. Commit + push

**Touched files (single commit):**
- `orchestrator/ai_operator/dashboard/dashboard.py` (+1 line at L167)
- `docs/paco_review_alexandra_dashboard_greeter_and_queue_badge_fix.md` (this doc, new)

Bug 2 is DB-only; no canon file change for the SQL itself. This doc records the UPDATE.

No anchor update. No SESSION.md update. Paco handles anchor/session at close-confirm ratification per v2.2 protocol.

---

## 9. Open questions / future-cycle flags

1. **Chat-history timestamp display bug.** CEO observed during AC.5/6 testing: rendered timestamps on historical chats show current UI-open time rather than created_at. Not in scope this cycle; candidate for future Alexandra hygiene cycle (likely a JS time-formatter fallback in `dashboard.py` chat_history_by_date render).
2. **Two-DB sync-or-deprecate decision.** PD investigation (repo HEAD `cfd9f8a`) surfaced; Paco directive §9 reiterated. Not actioned this cycle.
3. **SG sentinel script.** PD investigation §7 Q3; Paco directive §9. Not actioned this cycle.

**PD recommendations for Paco close-confirm ratification:**
- Ratify B0.1 + B0.2 adaptations.
- Bank P6 #45: "Paco pre-execution source-surface grep should cover all tokens that appear in post-patch verification predicates, not just the anchor uniqueness token" (natural extension of SR #7).
- Bank P6 #46: "nginx access logs are file-only in this fleet config (`/var/log/nginx/access.log`) and NOT captured by `journalctl -u nginx`; directive gates using access-log predicates must specify the file source explicitly" (natural extension of P6 #36).
- Update cumulative state P6=44 → P6=46, SR=8 (stable).
- Close implicit Bug 1 + Bug 2 tickets.

---

## 10. Status

`AWAITING PACO CLOSE-CONFIRM RATIFICATION`

— PD
