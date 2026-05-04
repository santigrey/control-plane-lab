# paco_directive_alexandra_dashboard_greeter_and_queue_badge_fix

**To:** PD (Cowork) | **From:** Paco | **Date:** 2026-05-04 Day 80 ~11:25 MT (17:25 UTC)
**Cycle:** Alexandra fix — Bug 1 greeter polarity + Bug 2 stale queue:1 badge (single bundled cycle; Option A both)
**Authority:** CEO Sloan ratified Option A polarity 2026-05-04 ~11:20 MT after Paco state-back of PD investigation findings. **Authority expansion 2026-05-04 ~11:32 MT:** PD has B0 standing-meta-authority for execution-time correction of Paco source-surface errors (see §5)
**Companion to:** `docs/paco_request_alexandra_dashboard_greeter_route.md` (PD investigation deliverable for directive `cfd9f8a`)
**Supersedes:** investigation portion of `cfd9f8a`. Bug 3 (localStorage line 133) confirmed correct by PD; documented as closed; no patch.
**Repo HEAD at directive author:** `f75ee85`
**Cumulative state at author:** P6=44, SR=8
**First session under v2.2 governance.**

---

## 0. TL;DR

Two surgical patches, both Option-A scope per PD's investigation. No `app.py` `/vision/analyze` endpoint changes. No `setTimeout(autoGreet, 300)` removal.

1. **Bug 1 (greeter polarity).** Insert one client-side guard in `dashboard.py` `autoGreet()` body. Professional mode (`privateMode=false`) suppresses the page-load webcam-vision greeter. Companion mode continues to greet as today. +1 line of JS, total LOC change.
2. **Bug 2 (stale queue:1 badge).** Mark single stale `approved` row `6d5102a5-93e8-4972-846f-9acbabe2b795` (B2a PostgreSQL ship 2026-04-26, feedback already `done`) as `completed` in CK primary `controlplane.public.agent_tasks`. Badge clears immediately. Replicates to Beast through B2b logical replication.

Orthogonal patches; bundled because both are Option-A surgical scope, low blast radius, and share verification surface (dashboard reload).

---

## 1. Verified-live block (Paco source-surface preflight per SR #7)

All probes run by Paco at directive-author time via homelab MCP read-only. `/proc/<pid>/environ` NOT used (P6 #44).

| Surface | Probe | Verified value at author |
|---|---|---|
| dashboard.py path | `find /home/jes/control-plane -name dashboard.py -not -path '*/.venv/*'` | `/home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py` |
| dashboard.py size + mtime | `stat -c '%s %y'` | 60057 bytes, mtime 2026-05-01 23:08:26 UTC |
| dashboard.py LOC | `wc -l` | 988 lines |
| `_greeted=true` occurrences (uniqueness) | `grep -n '_greeted=true' dashboard.py` | exactly 1 hit at line 167 |
| autoGreet anchor block | `sed -n '165,168p' \| cat -An` | line 165 `async function autoGreet(){`, line 166 `  if(_greeted)return;`, line 167 `  _greeted=true;` (verified 2-space indent, minified style) |
| line 133 localStorage default | `grep -n 'let privateMode' dashboard.py` | `let privateMode=localStorage.getItem('alexandra_private')==='1';` (PD investigation confirmed correct; do NOT touch) |
| orchestrator unit | `systemctl cat orchestrator.service` | Type=simple, User=jes, WorkingDirectory=`/home/jes/control-plane/orchestrator`, EnvironmentFile=-`/home/jes/control-plane/orchestrator/.env`, ExecStart=`./.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000`, Restart=always (NO `--reload`; restart REQUIRED for dashboard.py change to ship) |
| orchestrator state | `systemctl show -p ActiveState -p MainPID` | ActiveState=active, MainPID=1215999, ActiveEnterTimestamp Mon 2026-05-04 13:14:20 UTC |
| orchestrator DB target (P6 #43) | `systemctl cat` confirms env loaded from `.env`; `docker inspect control-postgres` confirms LAN bind | container `control-postgres` bound `192.168.1.10:5432`. Orchestrator DATABASE_URL via `.env` resolves to `postgresql://***@192.168.1.10:5432/controlplane` (per PD investigation; not re-fetched this session to avoid env-leak surface). **CK primary is the authoritative target for the UPDATE.** Beast `control-postgres-beast` is REPLICA-SIDE; not authoritative for write state. |
| stale row presence on CK primary | `docker exec control-postgres psql -U admin -d controlplane -t -c "SELECT id,status,title,assigned_to,feedback FROM public.agent_tasks WHERE status IN ('approved','pending_approval');"` | exactly 1 row: `6d5102a5-93e8-4972-846f-9acbabe2b795 \| approved \| B2a SHIPPED — PostgreSQL on Beast (7/7 gates PASS, awaiting independent verification) \| paco \| done` |
| Standing gates baseline (pre-cycle) | atlas-mcp PID 1212 active; atlas-agent PID 4753 NRestarts=0 active; mercury PID 7800 active; postgres-beast StartedAt 2026-05-03T18:38:24.910689151Z r=0; garage-beast StartedAt 2026-05-03T18:38:24.493238903Z r=0 | bit-identical to anchor 2026-05-04 17:11 UTC |

**Patch anchor block (3 lines, content-unique across file):**
```
async function autoGreet(){
  if(_greeted)return;
  _greeted=true;
```

---

## 2. Pre-flight verification (PD MUST PASS before execution)

DPF.1 — dashboard.py exists at canonical path:
```
stat -c '%s %y' /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py
```
Expected: ~60057 bytes (± small drift acceptable), mtime older than this directive. If size drifted >5%, halt + paco_request.

DPF.2 — patch anchor unique:
```
grep -c '_greeted=true' /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py
```
Expected: `1`. If `>1`, halt + paco_request (anchor ambiguity); B1 not authorized for grep-uniqueness drift.

DPF.3 — anchor block matches verbatim:
```
sed -n '165,167p' /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py
```
Expected exactly 3 lines:
```
async function autoGreet(){
  if(_greeted)return;
  _greeted=true;
```
If line numbers drifted but content matches at different lines, B1 authorized (apply by content match).

DPF.4 — stale row presence:
```
sudo docker exec control-postgres psql -U admin -d controlplane -t -c "SELECT id, status, updated_at FROM public.agent_tasks WHERE id='6d5102a5-93e8-4972-846f-9acbabe2b795';"
```
Expected: exactly 1 row, status=`approved`. **Capture `updated_at` into review (rollback bit-identicality requires original timestamp).** If row absent OR status!=`approved`, halt + paco_request.

DPF.5 — NO other open-status rows:
```
sudo docker exec control-postgres psql -U admin -d controlplane -t -c "SELECT count(*) FROM public.agent_tasks WHERE status IN ('pending_approval','approved','in_progress','running','queued');"
```
Expected: `1` (only the row in DPF.4). If `>1`, halt + paco_request — unexpected open rows surfaced since Paco's preflight; CEO call needed before bulk action.

DPF.6 — standing gates baseline capture (paste outputs into review for pre/post comparison):
```
ssh beast 'systemctl show -p MainPID -p NRestarts atlas-mcp.service atlas-agent.service'
ssh ciscokid 'systemctl show -p MainPID mercury-scanner.service'
ssh beast 'docker inspect control-postgres-beast --format "{{.State.StartedAt}} r={{.RestartCount}}"'
ssh beast 'docker inspect control-garage-beast --format "{{.State.StartedAt}} r={{.RestartCount}}"'
```
Expected: matches verified-live block table.

DPF.7 — backup directory writable:
```
test -w /home/jes/control-plane/orchestrator/ai_operator/dashboard/ && echo writable || echo READONLY
```
Expected: `writable`. If readonly, halt.

---

## 3. Execution

One-step-at-a-time per SR #3. Each step gates the next. Standing gates re-checked between steps.

### Step 1 — Backup dashboard.py
```
cp /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py \
   /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py.bak.day80-pre-greeter-fix
ls -la /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py.bak.day80-pre-greeter-fix
```
Stop condition: backup file present, size matches source byte-for-byte (`cmp -s` should exit 0).

### Step 2 — Patch dashboard.py (insert greeter guard line)

Using python `str_replace`-equivalent for atomic 3-line-anchor swap. PD’s discretion on tooling (sed, python, or editor); content match is what matters.

Replace EXACT 3-line anchor:
```
async function autoGreet(){
  if(_greeted)return;
  _greeted=true;
```

With EXACT 4-line replacement:
```
async function autoGreet(){
  if(_greeted)return;
  if(!privateMode){_greeted=true;return;}
  _greeted=true;
```

Indent: 2-space (matches file convention; verified). Style: minified, no spaces around `!`, `=`, `{}`, `()` (matches existing line 166 `if(_greeted)return;`).

Verification post-patch:
```
grep -n '!privateMode' /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py
sed -n '165,169p' /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py
```
Expected first command: exactly 1 hit on the new line.
Expected second command:
```
async function autoGreet(){
  if(_greeted)return;
  if(!privateMode){_greeted=true;return;}
  _greeted=true;
  const vs=document.getElementById('voice-status');
```

Stop condition: `grep -c '!privateMode' dashboard.py` returns `1`; `wc -l dashboard.py` returns `989` (was 988). If counts wrong, halt + paco_request (do NOT proceed to restart).

### Step 3 — Restart orchestrator
```
sudo systemctl restart orchestrator.service
sleep 3
systemctl show -p ActiveState -p MainPID -p ActiveEnterTimestamp orchestrator.service
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/healthz
```
Expected: ActiveState=active, NEW MainPID (not 1215999), HTTP 200 from /healthz GET (P6 #42: GET not HEAD).

Stop condition: any non-200 from /healthz, or service fails to enter active state within 30s. If failed: rollback Step 2, restart orchestrator, paco_request.

### Step 4 — DB UPDATE (Bug 2 fix)
```
sudo docker exec control-postgres psql -U admin -d controlplane -c "UPDATE public.agent_tasks SET status='completed', updated_at=NOW() WHERE id='6d5102a5-93e8-4972-846f-9acbabe2b795' AND status='approved' RETURNING id, status, updated_at;"
```

Note the `AND status='approved'` defensive predicate — if anything has moved the row since DPF.4, the UPDATE returns 0 rows and we halt without harm.

Expected output: 1 row returned showing status=`completed` and fresh updated_at.

Stop condition: 0 rows returned OR error. Halt + paco_request.

### Step 5 — Replication verification
Wait 10s for replication, then:
```
ssh beast 'sudo docker exec control-postgres-beast psql -U admin -d controlplane -t -c "SELECT status, updated_at FROM public.agent_tasks WHERE id='\''6d5102a5-93e8-4972-846f-9acbabe2b795'\'';"'
```
Expected: status=`completed`, updated_at matches Step 4 (validates B2b logical replication active).

Stop condition: replica still shows `approved` after 60s. Halt + paco_request (replication lag investigation needed).

### Step 6 — Behavioral verification (cold dashboard load)

This step requires CEO browser interaction OR PD-side curl scripting; specify per PD capability.

6a — Pre-test nginx log baseline:
```
sudo journalctl -u nginx --since '30 seconds ago' --no-pager | grep -c 'POST /vision/analyze'
```
Expected: capture baseline count.

6b — Cold load with localStorage cleared (default professional mode):
CEO Sloan: navigate to `https://sloan3.tail1216a3.ts.net/dashboard` in private window OR with localStorage.clear() executed. Click "click anywhere to begin" overlay. Wait 30 seconds. Confirm:
- No alex chat bubble appears with greeter text.
- Top-badges shows `queue: 0` (green).
- Lock icon = open (🔓 / professional mode).

6c — Post-test nginx log:
```
sudo journalctl -u nginx --since '30 seconds ago' --no-pager | grep 'POST /vision/analyze' | tail -10
```
Expected: ZERO new POST /vision/analyze in the 30s window post-overlay-click.

6d — Companion-mode regression test:
CEO Sloan: in browser console, run `localStorage.setItem('alexandra_private','1')`, hard-refresh dashboard, click overlay, wait 10s. Confirm:
- Alex chat bubble appears with greeter description.
- Lock icon = closed + orange border (🔒 / companion).
- nginx log shows POST /vision/analyze in the 10s window post-click.

Stop condition: 6b shows POST /vision/analyze fired, OR 6d shows greeter SUPPRESSED. Either case = patch failed; rollback Step 2 + restart + revert Step 4.

---

## 4. Acceptance Criteria

### MUST-PASS
- **AC.1** dashboard.py contains exactly one new line `  if(!privateMode){_greeted=true;return;}` between original line 166 and original line 167; surrounding lines bit-identical to pre-patch (use `diff dashboard.py.bak.day80-pre-greeter-fix dashboard.py` — expect exactly 1 added line, 0 removed).
- **AC.2** Orchestrator restart clean: new MainPID > 0, ActiveState=active, /healthz returns 200 (GET).
- **AC.3** agent_tasks row 6d5102a5 status=`completed` on CK primary; updated_at >= Step 4 invocation time.
- **AC.4** Beast replica shows same row status=`completed` within 60s of Step 4 (B2b logical replication verified).
- **AC.5** Cold dashboard load with localStorage cleared (default professional mode): ZERO POST /vision/analyze in 30s post-overlay-click; ZERO greeter chat bubble.
- **AC.6** Cold dashboard load with `alexandra_private`='1' (companion mode): POST /vision/analyze present within 10s post-overlay-click; greeter chat bubble appears (companion-mode greeter still functional).
- **AC.7** Dashboard top-badges queue counter shows `queue: 0` (green styling).
- **AC.8** Standing gates 6/6 bit-identical pre vs post (postgres-beast + garage-beast StartedAt unchanged + 0 RestartCount; atlas-mcp PID 1212 unchanged; atlas-agent PID 4753 NRestarts=0 unchanged; mercury PID 7800 unchanged). Orchestrator MainPID change is EXPECTED (not a gate).

### SHOULD-PASS
- **AS.1** nginx error log clean of new ERROR/WARN entries during cycle window.
- **AS.2** orchestrator.service journal clean of crash backtraces or 5xx surge during restart.
- **AS.3** No drift in `wc -l dashboard.py` other than +1 (988 → 989).

---

## 5. Path B authorizations (SR #4)

- **B0 (CEO standing meta-authority for this directive):** PD authorized to verify Paco's source-surface claims (file paths, line numbers, indent style, anchor uniqueness, SQL identifiers, command syntax, command output formats) AT EXECUTION TIME and adapt to ground truth WITHOUT halting for paco_request, when ALL of:
  - The error is structural / clerical (wrong line number, missing path component, indent mismatch, anchor-block typo, sed/grep regex error, command-syntax error, output-format misread).
  - The corrected adaptation preserves directive intent UNCHANGED — greeter-polarity semantics (companion greets, professional silent) and Bug 2 single-row UPDATE scope are inviolable.
  - The adaptation is documented in review: original Paco-stated value → PD-observed ground truth → PD-applied corrected value → rationale.
  Ratified by CEO Sloan 2026-05-04 ~11:32 MT for this cycle. Extends SR #4 (pre-execution adaptation only) into execution time. The NOT-authorized list below still binds — scope expansion (touching other files, modifying intent, exceeding patch surface) remains halt-and-paco_request. If pattern proves sound across cycles, promotion to SR #9 may follow.
- **B1 (line-number drift):** if `sed -n '165,167p'` does not return the exact 3-line anchor block but `grep -c '_greeted=true'` still returns 1 AND content match found elsewhere in the file, PD adapts the patch to the content-match location. Document line-number drift in review.
- **B2 (psql connection method):** if `sudo docker exec control-postgres psql -U admin` fails on auth, PD MAY use `psql "$DATABASE_URL" -c '...'` reading from `.env`. Quote ONLY host:port:database in review (not credentials). DB forensic discipline applied.
- **B3 (nginx log path drift):** if `/var/log/nginx/access.log` not present (rotated, journald-only mode), PD uses `journalctl -u nginx --since '<TS>' --until '<TS>' --no-pager` (no `-n` cap; P6 #36).
- **B4 (browser-side AC.5/6 deferred):** if CEO browser interaction not available in PD execution window, PD captures pre-restart `journalctl -u nginx -n 100 --no-pager | grep 'POST /vision/analyze'` baseline, marks AC.5/6 PENDING_CEO, dispatches a paco_request asking Sloan to perform the cold-load tests at his next dashboard interaction. AC.7 (queue: 0 visible) PD captures via `curl -s http://127.0.0.1:8000/dashboard/agent_tasks | python3 -c 'import json,sys;d=json.load(sys.stdin);print(sum(1 for t in d["tasks"] if t["status"] in ("pending_approval","approved")))'` — expected `0`.

### NOT authorized (halt + paco_request)
- Modifying `vision_analyze` endpoint in `app.py` (Option B explicitly out of scope).
- Removing `setTimeout(autoGreet, 300)` in `startSession()` (Option C explicitly out of scope).
- Modifying `_greeted` semantics elsewhere in dashboard.py (lines 191, 209 — the existing `_greeted=false` resets on dark-frame and post-greet — untouched).
- Modifying line 133 localStorage default (Bug 3 confirmed correct).
- Modifying the orchestrator's `.env` file.
- Changing UPDATE WHERE predicate beyond `id='6d5102a5...' AND status='approved'`.
- Bulk operations on agent_tasks (must be the single targeted row).

---

## 6. Rollback

### dashboard.py rollback
```
cp /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py.bak.day80-pre-greeter-fix \
   /home/jes/control-plane/orchestrator/ai_operator/dashboard/dashboard.py
sudo systemctl restart orchestrator.service
sleep 3
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/healthz
```

### agent_tasks rollback
Using original `updated_at` captured in DPF.4 review output (pre-patch timestamp; quote in review for restore-bit-identicality):
```
sudo docker exec control-postgres psql -U admin -d controlplane -c "UPDATE public.agent_tasks SET status='approved', updated_at='<ORIGINAL_UPDATED_AT_FROM_DPF.4>' WHERE id='6d5102a5-93e8-4972-846f-9acbabe2b795';"
```

### Rollback acceptance
- dashboard.py byte-for-byte match against backup (`cmp -s` exit 0).
- agent_tasks row status=`approved`, updated_at = pre-patch value.
- Standing gates 6/6 bit-identical to baseline.

---

## 7. Close-confirm artifacts (PD writes)

- `docs/paco_review_alexandra_dashboard_greeter_and_queue_badge_fix.md` covering:
  - DPF.1–DPF.7 outputs verbatim
  - Step 1–6 commands run + outputs
  - AC.1–AC.8 PASS/FAIL/DEFERRED with evidence quotes
  - AS.1–AS.3 PASS/FAIL
  - Standing gates pre/post comparison table
  - Path B applied (if any) + rationale
  - DB forensic discipline applied (host:port quoted, NOT credentials)
  - Rollback NOT executed (or, if executed, full trace)
- Both secrets-scan layers + literal-sweep CLEAN before commit (P6 #34 forward-redaction)
- Single git commit on `control-plane`:
  - Touched files: `orchestrator/ai_operator/dashboard/dashboard.py` (1 line added)
  - Bug 2 is DB-only — no canon file change for the SQL itself; the close-confirm doc records the UPDATE
- No anchor / SESSION.md update by PD; Paco handles at close-confirm-ratification

---

## 8. Pre-flight-checked code surface (Paco verification per P6 #42)

- **Indent convention:** 2-space minified JS in HTML triple-quoted Python string (verified `cat -An` line 165-167).
- **HTTP method:** /healthz uses GET (`curl -s -o /dev/null -w '%{http_code}'`), NOT HEAD (P6 #42).
- **Restart requirement:** orchestrator.service restart MANDATORY for dashboard.py JS edit (HTML is module-level constant, no `--reload` flag in ExecStart).
- **DB target:** all writes to CK primary container `control-postgres` at `192.168.1.10:5432` (orchestrator DATABASE_URL target). Beast `control-postgres-beast` is REPLICA-SIDE and verifies replication only (not authoritative for write).
- **Env handling:** if PD needs DATABASE_URL credentials, source from `.env` file directly; do NOT use `/proc/<pid>/environ` (P6 #44); do NOT echo credentials in review (DB forensic discipline).
- **Replication check window:** B2b logical replication asynchronous; 10s wait + 60s timeout window in Step 5 sized to historical lag patterns (typical < 1s).
- **Backup naming:** `.bak.day80-pre-greeter-fix` follows the `.bak.day80-pre-*` convention from Alexandra hygiene cycle (rollback discoverability).

---

## 9. Out-of-scope but flagged for future cycle

(Per PD investigation §7 open questions; not action items for this directive)

- **Two-DB sync-or-deprecate decision:** `control-postgres-beast` was the target of prior verification queries; PD's investigation surfaced that orchestrator points at CK `control-postgres` exclusively. If `control-postgres-beast` is intended only as the B2b replica downstream of CK, that's correct architecture per DATA_MAP. If anything writes directly to it, that's a divergent state. **Recommend:** Mr Robot future build adds an integrity check that asserts Beast `agent_tasks` is byte-identical to CK at every gate-check.
- **Vision-mode neutral prompt for professional Alexandra:** if Sloan later wants Alexandra to also greet on page-load (with a non-companion neutral system prompt), the Option B server-side fix becomes scoped — add `professional` form field to `/vision/analyze` and branch in the else-block. Out of scope this cycle.
- **DPF.7 sentinel script absence:** PD's investigation §7 Q3 noted no canonical SG sentinel script located. Future cycle: codify a `scripts/standing_gates_probe.sh` that prints the 6-gate snapshot in deterministic order. Atlas Domain 2 work could pick this up.

— Paco
