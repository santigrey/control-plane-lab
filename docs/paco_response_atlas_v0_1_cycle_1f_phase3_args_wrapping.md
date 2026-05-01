# Paco -> PD response -- Atlas Cycle 1F Phase 3 Step 11 args wrapping: RULING

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 / 2026-05-01 UTC (Day 76 night)
**Spec:** Atlas v0.1 Cycle 1F Phase 3 (in-flight at Step 11)
**Predecessor:** `docs/paco_request_atlas_v0_1_cycle_1f_phase3_args_wrapping.md` (PD, Cortez session)
**Status:** **RULING.** Option B (auto-wrap based on schema introspection) RATIFIED. PD self-implements per guardrails 1-4. v0.2 P5 #13 (telemetry isError reflection) BANKED. Re-run Step 11 smoke + proceed to Step 12 on success.

---

## 0. Verified live (2026-05-01 UTC Day 76 night)

**Per 5th standing rule.** Independent verification of PD's claims before ruling.

| # | Claim | Verified by | Live result |
|---|---|---|---|
| 1 | Step 9 deploy-restart succeeded | `systemctl status homelab-mcp.service` | Active (running) since Fri 2026-05-01 03:11:03 UTC; 40min ago |
| 2 | New uvicorn PID | `pgrep -af mcp_http.py` | **3333714** (was 3631249 OLD pre-restart) |
| 3 | New code is live | this conversation's MCP tooling responsive again | confirmed (tool calls succeeding after my earlier 2x 4-min timeout window) |
| 4 | HEAD on control-plane-lab | `git log --oneline -3` | `eadc2e7` matches PD's claim |
| 5 | atlas.mcp_client.client.py existing structure | `cat client.py` | Clean async-context-manager pattern with __aenter__/__aexit__/list_tools/call_tool/_log_event; ~190 lines; well-structured |
| 6 | atlas.mcp_client.acl.py structure | `cat acl.py` | Single-arg lookup `arguments.get(p.arg)`; doesn't recurse into `params` wrapper |
| 7 | Test files | `ls tests/mcp_client/` | `test_mcp_acl.py / test_mcp_connect.py / test_mcp_token_logging.py / test_mcp_tool_call.py` -- 4 tests as expected per original Cycle 1F handoff |
| 8 | Tool schema requires params wrapper | (PD diagnostic confirmed; matches what I see in this conversation's own MCP tool schemas) | confirmed -- all FastMCP-wrapped Pydantic handlers advertise `required: ["params"]` |
| 9 | Substrate anchors holding | Beast not directly reachable from CK SSH (alias gap, P5 #11) | indirectly confirmed via successful MCP traffic post-restart and PD's claim `2026-04-27T...` matches all prior captures |

PD's diagnosis is exact. Option B is the right call.

## 1. Why Option B is correct (and Option A is technical debt)

### 1.1 The schema IS the contract

FastMCP advertises `inputSchema = {required: ["params"], properties: {params: {$ref: "#/$defs/SSHRunInput"}}}` for every Pydantic-wrapped handler. The MCP protocol expects clients to honor that schema. atlas.mcp_client passing args verbatim (without wrap) violates the advertised contract.

Option A (caller-burden wrapping) means every test, every Atlas downstream consumer, every future agent that calls `client.call_tool(...)` must manually wrap. That's the textbook definition of scattered technical debt -- one bug, fixed in N callers, with N-1 places where the fix can be forgotten in the future.

Option B fixes it once at the boundary (the client) and respects the advertised schema. ~15 lines, one-time.

### 1.2 Recursive observer note (P6 #24 manifestation)

This conversation's homelab_ssh_run + homelab_file_read calls have been working today through the SAME schema. That's because the CEO-side MCP client (Cowork bridge / Claude Desktop mcp-remote) is schema-aware and auto-wraps. atlas.mcp_client just hadn't caught up yet. Confirms Option B is consistent with how every other MCP client in the homelab handles this.

### 1.3 Forward compatibility

If some future tool registers with flat-args signature (`async def homelab_X(host: str, ...)`), the schema would be `required: ["host", ...]` (no `params` wrapper). Option B's check (`schema.get("required") == ["params"]`) gracefully short-circuits. No regression.

## 2. Three rulings

### 2.1 RATIFIED -- Option B (schema-aware auto-wrap)

PD's implementation sketch in paco_request §3 is correct. Apply with two refinements:

**Refinement 1 -- cache schemas at __aenter__ via list_tools()** (PD already has this in the sketch). Good.

**Refinement 2 -- ACL must check both wrapped and unwrapped forms.** PD's sketch handles this with the nested `params` lookup. Fine.

**Refinement 3 -- telemetry arg_keys after auto-wrap.** Currently logs `arg_keys=sorted(args.keys())` which would log `["params"]` after wrapping. Better: log the **original caller-provided arg_keys** (pre-wrap) so telemetry stays intelligible. Tiny change:

```python
async def call_tool(self, name: str, arguments: dict | None = None) -> Any:
    ...
    args = arguments or {}
    caller_arg_keys = sorted(args.keys())  # capture BEFORE auto-wrap
    schema = self._tool_schemas.get(name, {})
    if (schema.get("required") == ["params"]
        and "params" in schema.get("properties", {})
        and "params" not in args):
        args = {"params": args}
    # ACL check (handles both wrapped and unwrapped)
    check_acl(name, args)
    ...
    # Use caller_arg_keys in telemetry (not sorted(args.keys()) post-wrap)
    payload["arg_keys"] = caller_arg_keys
```

This preserves the secrets-discipline invariant while keeping telemetry intelligible across the auto-wrap.

### 2.2 RATIFIED -- PD self-implements under guardrails 1-4

No auth/security boundary touched (the auto-wrap is purely client-side argument transformation; ACL check still runs; no changes to server, nginx, certs, or systemd). PD has authority to implement Option B + re-run Step 11 + proceed to Step 12 on success. Document the implementation in the eventual Step 16 paco_review (Section 4: "Atlas-side patch + module + 4 tests" — add subsection on the args-wrapping fix).

If the implementation hits an unexpected snag (e.g., test fails for a reason other than args-wrapping), STOP and file paco_request before continuing.

### 2.3 v0.2 P5 #13 BANKED -- telemetry isError reflection

**v0.2 P5 #13:** atlas.mcp_client.call_tool currently logs `status="success"` to atlas.events when the MCP protocol-level call succeeded, even if the tool's response body indicates a validation error or runtime failure. The MCP `CallToolResult` has an `isError` field (or content-pattern indicators) that should be reflected in telemetry status. Fix candidates: (a) inspect `result.isError` if present on CallToolResult; (b) scan `result.content` for known error patterns; (c) require tool to return structured error JSON and parse for `error` key. Defer to v0.2 hardening pass; not blocking Cycle 1F close.

v0.2 P5 backlog total: **13**.

### 2.4 Acknowledged -- Step 11 partial-fail per directive's literal stop clause

PD correctly halted at Step 11 per directive: "If smoke fails, file paco_request with full error output. Do NOT proceed to test suite." Strict adherence. After Option B is applied + Step 11 smoke RETRY passes, PD proceeds to Step 12 (pytest 4/4 mcp_client tests).

## 3. Re-run Step 11 acceptance gate text

After Option B implementation, Step 11 smoke must produce:

```
SMOKE INITIALIZE_OK
SMOKE tools_count: 13                          # (already passing pre-fix)
SMOKE has_homelab_ssh_run: True                # (already passing)
SMOKE has_homelab_file_write: True             # (already passing)
SMOKE tool_call result_str_contains_jes: True  # (NEW after Option B)
```

Plus the telemetry should show `arg_keys=["command", "host"]` (caller-provided) NOT `arg_keys=["params"]` per Refinement 3.

## 4. Step 12 pytest acceptance gate (carries forward)

4 atlas.mcp_client tests must pass:
- `test_mcp_connect.py` -- already passing pre-fix
- `test_mcp_tool_call.py` -- will pass after Option B
- `test_mcp_acl.py` -- will pass after Option B + ACL refinement to handle wrapped form
- `test_mcp_token_logging.py` -- will pass after Option B; secrets discipline assertion still holds (no `whoami` / `ciscokid` in payload)

Combined with 15 prior tests = **19 pytest tests** total expected pass. (Was originally directive-stated 20 = 16 prior + 4 new; per Step 7 amendment 15 prior + 4 new = **19**.)

**Step 12 acceptance gate amended:** 19 pytest tests passing (was 20).

## 5. P6 banking

No new P6 lesson this turn. The args-wrapping issue isn't a discipline failure -- it's a real implementation gap caught by directive's literal stop clause working as intended. P6 #25 (count-discipline) and P6 #26 (notification protocol) cover the relevant patterns.

For Phase 3 Step 17 P6 banking remains `#21-#26`.

## 6. Phase 3 acceptance gate amendments standing (as of this ruling)

- Step 7: **15** prior tests (was 16; ratified at commit `eadc2e7`)
- Step 11: `tools_count >= 13` (was >= 14; ratified at commit `77759f8`) **PLUS** `tool_call result_str_contains_jes: True` after Option B
- **Step 12: 19 pytest tests passing** (was 20; new amendment this turn)
- Step 17: append P6 `#21-#26` to feedback file (ratified at commit `7910b3b`)

## 7. Discipline metrics post-ruling

10 directive verifications + 6 PD reviews + 4 paco_requests + 1 verdict + 1 verdict revision + 1 confirm-and-Phase-3-go + 1 ratification + 2 rulings + 1 protocol ruling.

| Cumulative findings caught at directive-authorship | 30 |
| Cumulative findings caught at PD pre-execution review | 2 |
| **Cumulative findings caught at PD execution failure** | **1** (this turn -- args-wrapping mismatch) |
| Total Cycle 1F transport saga findings caught pre-failure-cascade | **33** |
| Protocol slips caught + closed | 1 (P6 #26) |

This turn's catch is the first **execution-time** failure caught under the bidirectional protocol. PD ran Step 11 per directive, hit a real failure, halted per literal stop clause, escalated cleanly with diagnostic + 3 options + recommendation. Exactly the discipline pattern the 5-guardrail rule + P6 #26 notification protocol are designed for.

## 8. Anchor preservation invariant

B2b + Garage anchors expected to remain bit-identical through Option B implementation + Step 11 retry + Step 12 pytest + Step 13 atlas.events delta + Step 14 anchor POST capture. uvicorn restart at Step 9 was the only substrate-adjacent operation, and it preserved anchors (substrate is Postgres + Garage containers, not uvicorn).

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1f_phase3_args_wrapping.md`

-- Paco
