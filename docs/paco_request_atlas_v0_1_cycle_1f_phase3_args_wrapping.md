# paco_request_atlas_v0_1_cycle_1f_phase3_args_wrapping

**Spec:** Atlas v0.1 Cycle 1F Phase 3 (combined fix + deploy-restart + build close)
**Step:** Step 11 end-to-end Beast smoke FAILED on tool_call args validation; BEFORE Step 12 pytest
**Status:** ESCALATION -- args-wrapping mismatch between atlas.mcp_client (passes verbatim) and FastMCP server schema (requires `params` wrapper). Initialize + list_tools OK; tool_call returns validation error. Filing per directive Step 11 explicit clause + P6 #26 notification protocol.
**Predecessor:** `docs/paco_response_atlas_v0_1_cycle_1f_phase3_pretest_flake.md` (HEAD `eadc2e7`); `docs/paco_request_atlas_v0_1_cycle_1f_phase3_pre_deploy.md` (Step 8 checkpoint)
**Author:** PD (Cortez session)
**Date:** 2026-04-30 / 2026-05-01 UTC (Day 76 night)
**Target host:** Beast (atlas.mcp_client) + CiscoKid (mcp_server.py schema reference)

---

## TL;DR

Step 9 deploy-restart succeeded. Mac mini + Cortez reconnected post-restart 200s. INITIALIZE_OK + tools_count=13 (matches amended gate). Telemetry to atlas.events working (mcp_event log lines for tools_list + tool_call both `status=success`).

**Step 11 partial fail:** atlas.mcp_client tool_call returns:
```
Error executing tool homelab_ssh_run: 1 validation error for homelab_ssh_runArguments
params
  Field required [type=missing, ...]
```

**Diagnosis confirmed:** server's tool inputSchema explicitly requires `params` wrapper:
```json
{
  "$defs": {"SSHRunInput": {...}},
  "properties": {"params": {"$ref": "#/$defs/SSHRunInput"}},
  "required": ["params"]
}
```

Wrapped form `{"params": {"host": "ciscokid", "command": "whoami"}}` → returns proper result `{"stdout": "jes", ...}` and telemetry shows `arg_keys=['params']` (NOT `["command", "host"]`).

**Root cause:** All 13 mcp_server.py handlers use Pydantic-wrapped signature `async def homelab_X(params: SomeInput)`. FastMCP advertises tool schema with `params` wrapper. atlas.mcp_client.call_tool passes `arguments` dict verbatim through to `mcp.ClientSession.call_tool(name, arguments)`. SDK does NOT auto-wrap based on schema. Mismatch.

This affects all 3 atlas tests that call_tool:
- `test_mcp_tool_call.py` (would fail validation)
- `test_mcp_acl.py` (ACL check happens BEFORE network call -- but the ACL itself looks for `arguments["path"]` while real call would have `arguments["params"]["path"]` — likely fails to deny)
- `test_mcp_token_logging.py` (would fail validation; secrets discipline assertion ironically passes because validation error has no `whoami`/`ciscokid` literal in payload)

B2b + Garage anchors bit-identical: `2026-04-27T00:13:57.800746541Z` + `2026-04-27T05:39:58.168067641Z` (76+ hours holding through Step 9 deploy-restart -- confirmed indirectly via successful MCP traffic).

---

## 1. Step 11 evidence

### 1.1 Initialize + list_tools (PASS)

```
SMOKE INITIALIZE_OK
SMOKE tools_count: 13
SMOKE tool_names: ['homelab_agent_status', 'homelab_create_task', 'homelab_file_read', 'homelab_file_write', 'homelab_get_profile', 'homelab_list_tasks', 'homelab_memory_search', 'homelab_memory_store', 'homelab_read_messages', 'homelab_send_message', 'homelab_ssh_run', 'homelab_update_profile', 'homelab_update_task']
SMOKE has_homelab_ssh_run: True
SMOKE has_homelab_file_write: True
```

### 1.2 tool_call (FAIL on validation)

First attempt with unwrapped args:
```python
result = await client.call_tool("homelab_ssh_run", {"host": "ciscokid", "command": "whoami"})
```
Result content (first 120 chars):
```
Error executing tool homelab_ssh_run: 1 validation error for homelab_ssh_runArguments
params
  Field required [type=miss...
```

Note: the call returned `status=success` at MCP protocol level (`mcp_event` row shows `status=success`, `kind=tool_call`, `arg_keys=["command", "host"]`) -- the validation error is in the tool's response BODY, not protocol-level error. So atlas.events row was inserted with status=success but the actual tool execution failed. This is a separate bug-class to flag.

### 1.3 Diagnostic re-call with wrapped args (PASS)

```python
result = await client.call_tool("homelab_ssh_run", {"params": {"host": "ciscokid", "command": "whoami"}})
```
Result:
```
WRAPPED result: {
  "host": "ciscokid",
  "command": "whoami",
  "stdout": "jes",
  "stderr": "",
  "exit_code": 0
}
```

Telemetry shows `arg_keys=['params']` and `status=success` (719.45ms duration on this wrapped call vs 19.77ms on the failed unwrapped call -- the wrapped call actually executed the SSH command).

## 2. Three resolution options for Paco ratification

### 2.1 Option A -- Update atlas.mcp_client tests + ACL to use wrapped form (MINIMAL CHANGE)

Update 3 test files to wrap args in `{"params": {...}}`. Update `acl.py` to look inside `arguments["params"]` (or both top-level AND nested for forward compat).

Pros: smallest diff (~6 lines across 4 files). Tests run cleanly.
Cons: caller burden -- every atlas.mcp_client.call_tool needs `params=` wrapping. Not ergonomic. Doesn't match the natural mcp.ClientSession API which expects flat args.

### 2.2 Option B -- Auto-wrap in atlas.mcp_client.call_tool based on tool schema

When call_tool is invoked, fetch the tool's inputSchema (cached at connect). If the schema has a single `params` property required, auto-wrap the arguments under `params`. This is a 10-15 line change in `client.py`.

Pros: ergonomic API; matches caller expectations; portable across FastMCP-server tools and direct-arg tools.
Cons: more code; may need updates if tool schemas vary.

### 2.3 Option C -- Server-side handler refactor (LARGEST CHANGE, NOT RECOMMENDED)

Change all 13 mcp_server.py handlers from `async def homelab_X(params: SomeInput)` to `async def homelab_X(host: str, command: str, ...)`. FastMCP would then advertise flat-arg schema.

Pros: schema becomes ergonomic for all clients.
Cons: HUGE diff -- 13 handler signatures + likely impacts THIS conversation's MCP tooling (Cowork client may be schema-aware and break). Out of scope for Phase 3.

### 2.4 PD recommendation

**Option B** -- auto-wrap in atlas.mcp_client based on schema introspection. Matches Paco's spec section 3.7 "Library-default discipline" — using the tool's advertised schema as the contract. ~15 lines of code; one-time fix; future-proof.

Fallback: Option A if Paco prefers minimal change for v0.1 close-out and defers schema-aware client to v0.2.

## 3. Schema-detection logic for option B (proposed)

```python
async def __aenter__(self) -> "McpClient":
    # ... existing connect logic ...
    await self._session.initialize()
    # NEW: cache tool schemas for auto-wrap
    self._tool_schemas = {}
    result = await self._session.list_tools()
    for t in result.tools:
        self._tool_schemas[t.name] = t.inputSchema
    return self

async def call_tool(self, name: str, arguments: dict | None = None) -> Any:
    # ...
    args = arguments or {}
    # Auto-wrap if schema requires single 'params' field and args are unwrapped
    schema = self._tool_schemas.get(name, {})
    if (schema.get("required") == ["params"]
        and "params" in schema.get("properties", {})
        and "params" not in args):
        args = {"params": args}
    # ACL check (now needs to handle both forms)
    check_acl(name, args)
    # ... rest of call_tool unchanged ...
```

And `check_acl` updated to handle wrapped form:
```python
def check_acl(tool_name: str, arguments: dict) -> None:
    for p in ACL_DENY_PATTERNS:
        if p.tool_name != tool_name:
            continue
        # Look in top-level args AND nested 'params'
        val = arguments.get(p.arg)
        if val is None and "params" in arguments and isinstance(arguments["params"], dict):
            val = arguments["params"].get(p.arg)
        if val is None:
            continue
        if p.pattern.search(str(val)):
            raise AtlasAclDenied(...)
```

## 4. Subsidiary issue (separate from this paco_request, flagging only)

Current atlas.mcp_client.call_tool logs `status="success"` to atlas.events even when the tool execution returned a validation error in its response body. The MCP protocol-level call succeeded (CallToolResult was returned), but the tool itself failed validation. The telemetry status field doesn't reflect this.

Fix candidates: parse `result.isError` if available on CallToolResult, OR scan result.content for error patterns. Defer to v0.2 P5 #13 if Paco agrees.

## 5. Asks of Paco

1. **Ratify** option A, B, or C (PD recommends B).
2. **Approve** PD self-implement the chosen fix under guardrail 1-4 of the 5-guardrail rule (no auth/security boundary touched; documented in eventual paco_review).
3. **Bank as v0.2 P5 #13**: telemetry status field should reflect tool execution result (not just protocol-level call success). OR include in this cycle close.
4. **Acknowledge** Step 11 partial-fail per directive's literal stop clause ("If smoke fails, file paco_request with full error output. Do NOT proceed to test suite."). PD did not run pytest at Step 12.

## 6. State at this pause

- Steps 1-10 complete (deploy-restart succeeded; new uvicorn PID 3333714 alive)
- Step 11 partial: initialize+list_tools PASS, tool_call FAIL on args validation
- Step 12-17 + Z: NOT started
- mcp_server.py.bak.phase3 still preserved (rollback available, but Step 9 deploy-restart was clean -- no rollback needed)
- Substrate B2b + Garage anchors bit-identical (confirmed indirectly via successful MCP traffic post-restart)
- atlas.mcp_client module on Beast: import-validated; just needs the wrapping fix per chosen option
- HEAD on control-plane-lab: `eadc2e7`
- HEAD on atlas: `6c0b8d6` (still unchanged; no atlas commit yet)

---

**File:** `docs/paco_request_atlas_v0_1_cycle_1f_phase3_args_wrapping.md` (untracked, transient until close-out)

-- PD
