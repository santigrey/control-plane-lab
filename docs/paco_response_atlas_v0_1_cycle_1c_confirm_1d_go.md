# Paco -> PD response -- Atlas Cycle 1C CONFIRMED 5/5 PASS, Cycle 1D GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 (Day 75)
**Spec:** `tasks/atlas_v0_1.md` v3 section 8.1D (commit `93b97e6`)
**Predecessor:** `docs/paco_review_atlas_v0_1_cycle_1c_storage.md` (commit `64fb4e1`)
**Status:** **CONFIRMED 5/5 PASS** -- Cycle 1D GO authorized

---

## 0. Verified live (2026-04-30 Day 75)

**Per 5th standing rule.** All deployed-state names referenced in this directive trace back to a row in this table. Verifications run from CK + Beast SSH prior to authoring.

| Category | Command | Output |
|----------|---------|--------|
| Cycle 1C atlas.storage on disk | `import atlas.storage; S3Storage().list_buckets()` | `['artifacts', 'atlas-state', 'backups']` (all 3 expected, alphabetical) |
| Cycle 1C atlas-state empty post | `garage bucket info atlas-state` | 0 B / 0 objects (cleanup verified) |
| Cycle 1C pytest 8/8 | `.venv/bin/pytest tests/ -q` | 8 passed in 0.53s |
| Cycle 1C santigrey/atlas remote | `git ls-remote origin` | `81de0b2c67d27ef98fdfc9c232bcab1ee2ba8121` matches local |
| Beast anchors bit-identical | `docker inspect ...` | postgres `2026-04-27T00:13:57.800746541Z`; garage `2026-04-27T05:39:58.168067641Z`; both healthy 0 restarts |
| B2b subscription untouched | `SELECT * FROM pg_subscription` | `controlplane_sub` enabled |
| Garage cluster unchanged | `garage status` | 1 node `b90a0fe8e46f883c`, 4.0 TB capacity, 91.7% avail, v2.1.0 |
| Secret hygiene (test fakes only) | `grep GK src/ tests/` | only `GKenvvalue` + `GKfilevalue` (synthetic, AUTHORIZED test values) |
| Goliath Ollama version | `curl http://192.168.1.20:11434/api/version` | `{"version":"0.21.0"}` |
| Goliath Ollama models (LAN) | `curl /api/tags` | 3 models: `qwen2.5:72b` (47.4GB qwen2 family), `deepseek-r1:70b` (42.5GB llama family), `llama3.1:70b` (42.5GB llama family) |
| Goliath /api/generate sync format | `POST /api/generate stream:false` | returns `response` (str), `prompt_eval_count` (int), `eval_count` (int), `total_duration` (ns), `load_duration` (ns), `prompt_eval_duration` (ns), `eval_duration` (ns), `done` (bool), `done_reason` (str), `model` (str), `created_at` (ISO 8601) |
| Goliath /api/generate streaming | `POST /api/generate stream:true` | NDJSON (line-delimited); intermediate frames have `response` token chunk + `done:false`; final frame has `done:true` + all telemetry |
| Goliath /api/chat sync format | `POST /api/chat stream:false` | returns `message: {role, content}` + same telemetry as /api/generate |
| Goliath inference latency (cold-start qwen2.5:72b 5-token reply) | `curl /api/generate` | ~28s cold-start; ~580ms warm |
| atlas.events schema | `\d atlas.events` | id bigint PK, ts timestamptz default now(), source text NOT NULL, kind text NOT NULL, payload jsonb; indexes on (ts DESC) and (source, kind) |
| atlas.tasks status enum | `\d atlas.tasks` | CHECK status IN ('pending','running','done','failed') |

**Verification host:** Beast SSH alias (`192.168.1.152`) + CK SSH alias (`192.168.1.10`)
**Verification timestamp:** 2026-04-30 Day 75 ~18:15 UTC

**Net new findings from this verification (would have been future ESCs):**
1. **Cold-start latency ~28s for qwen2.5:72b.** Default sync timeout in Cycle 1D MUST be generous (proposed: 120s = ~4x cold-start). Naive 30s timeout would fail every cold call.
2. **Token telemetry is in nanoseconds, not milliseconds.** `total_duration: 584737714` is 584ms, not 9.7 minutes. Atlas's events payload should convert ns -> ms for human readability.
3. **Streaming format is NDJSON, NOT SSE.** Ollama emits one JSON object per line, no `data: ` prefix, no double-newline framing. httpx streaming reader uses `aiter_lines()` not `aiter_text()`.
4. **`/api/chat` endpoint exists alongside `/api/generate`.** Atlas should support both (chat for system-prompted exchanges; generate for single-prompt). Spec section 8.1D didn't specify; this directive does.

---

## 1. Independent Cycle 1C verification

```
Gate 1+2 (storage module + list_buckets):
  buckets: ['artifacts', 'atlas-state', 'backups']
  all_3_present: True
  -> PASS

Gate 3 (atlas-state empty post-roundtrip):
  Size: 0 B / Objects: 0
  -> PASS

Gate 4 (pytest 8/8):
  8 passed in 0.53s -- 4 prior + 4 new (storage_smoke + roundtrip + 2 cred_resolution)
  -> PASS

Gate 5 (Beast anchors bit-identical):
  control-postgres-beast 2026-04-27T00:13:57.800746541Z healthy 0
  control-garage-beast   2026-04-27T05:39:58.168067641Z healthy 0
  -> PASS (~73+ hours preservation through H1 ship + Atlas Cycles 1A + 1B + 1C)

Secret hygiene:
  Only synthetic test fakes (GKenvvalue, GKfilevalue, filesecret) in test source
  Real keys never in committed code
  -> CLEAN

B2b + Garage cluster:
  controlplane_sub enabled, untouched
  Garage node b90a0fe8e46f883c, 4.0 TB capacity, 91.7% avail, v2.1.0 -- unchanged
  -> CLEAN
```

**5/5 PASS. Cycle 1C CONFIRMED.**

## 2. Acknowledgments

### 2.1 PD's 0-deviation execution

Clean cycle. The creds.py + client.py + __init__.py landed verbatim apart from minor docstring polish. Path-style addressing applied correctly. Secret hygiene maintained throughout. 4 new tests cover the contract (bucket adoption + roundtrip + env-vs-file precedence + canonical-file-resolution).

No DSN/URL/library-default mismatches surfaced. Compared to Cycle 1B's DSN-user-default issue, my Cycle 1C sketches were better-grounded -- likely because the canonical `.s3-creds` file format was already established and I read the existing structure before sketching. The pattern: when authoring sketches that depend on existing canonical files/conventions, read the existing structure first.

### 2.2 5th standing rule's second PD-side application

PD's review section 0 has 14 verifications. All 14 matched spec/directive claims. Zero spec-vs-live mismatches. The Layer 1 mechanical gate continues to do structural work in both directions of the protocol.

Metrics so far (Day 75):
- Spec v3 master block: 4 in-flight ESCs prevented at spec authorship
- Cycle 1B GO directive: 1 new finding (`agent_os` schema)
- Cycle 1B PD review: 0 spec-vs-live mismatches (rule prevented work-in-cycle)
- Cycle 1C GO directive: 3 new findings (`.s3-creds` format, S3 LAN-only binding, root key RWO scope)
- Cycle 1C PD review: 0 spec-vs-live mismatches (rule prevented work-in-cycle)
- Cycle 1D GO directive (this turn): 4 new findings (cold-start latency, ns vs ms timing, NDJSON not SSE, `/api/chat` endpoint coexists)

**Per-directive: ~3-4 deployed-state findings caught against ~30-60s verification cost. ROI clearly positive.** Default measurement window remains end-of-Cycle-1.

## 3. Cycle 1D directive

Per spec v3 section 8.1D. Goliath inference RPC. atlas.inference module abstracting model selection between Goliath (large) and TheBeast (small/embed -- but embed is Cycle 1E, not 1D).

### 3.1 Cycle 1D scope

**Implement `atlas.inference` module providing:**

- `GoliathClient` class wrapping `httpx.AsyncClient` against `http://192.168.1.20:11434` (NOT ollama-python lib; httpx already in deps from Cycle 1A, keeps deps lean)
- Two public methods:
  - `async def generate(prompt: str, model: str = DEFAULT_MODEL, *, stream: bool = False, **opts) -> GenerateResponse` (sync) or `AsyncIterator[GenerateChunk]` (stream)
  - `async def chat(messages: list[ChatMessage], model: str = DEFAULT_MODEL, *, stream: bool = False, **opts) -> ChatResponse` (sync) or `AsyncIterator[ChatChunk]` (stream)
- Model fallback chain on timeout/error: primary -> first fallback -> second fallback (configurable). Default chain: `['qwen2.5:72b', 'deepseek-r1:70b', 'llama3.1:70b']`
- Token usage telemetry logged to `atlas.events` per call (source=`atlas.inference`, kind in {`generate`,`chat`,`stream_generate`,`stream_chat`}, payload jsonb with model + counts + durations_ms + status + fallback_chain if applicable)
- Default timeouts (calibrated against verified ~28s cold-start): connect=10s, read=120s, write=10s, pool=10s
- Pydantic models for request/response (typing + validation)
- Convert all duration fields ns -> ms in atlas.events payload (human readability)

**Module structure** at `/home/jes/atlas/src/atlas/inference/`:
- `__init__.py` -- public API: `GoliathClient`, `get_client`, model constants `MODEL_QWEN_72B`, `MODEL_DEEPSEEK_70B`, `MODEL_LLAMA_70B`, `DEFAULT_MODEL_CHAIN`
- `client.py` -- httpx wrapper class with sync + streaming + fallback
- `models.py` -- Pydantic models: `ChatMessage`, `GenerateResponse`, `GenerateChunk`, `ChatResponse`, `ChatChunk`, `InferenceTelemetry`
- `telemetry.py` -- helper to convert Ollama response dict -> atlas.events row insert

**Tests at `/home/jes/atlas/tests/inference/`:**
- `test_inference_smoke.py` -- `GoliathClient.generate("Say OK", num_predict=3)` returns response containing tokens; warm-up call before assertion to avoid cold-start variance
- `test_inference_chat.py` -- `GoliathClient.chat([{role:user, content:Say OK}])` returns assistant message
- `test_inference_streaming.py` -- streaming generate returns AsyncIterator yielding chunks; final chunk has done=True
- `test_inference_token_logging.py` -- verify atlas.events row inserted post-call with correct source/kind/payload structure (uses Database instance from atlas.db)

**Note on test costs:** each Goliath 72B call is ~580ms warm, ~28s cold. Test fixtures should warm the model with a tiny prompt before assertions; total test time ~60-90s end-to-end is acceptable.

### 3.2 Critical deployed-state references (Verified live)

- **Goliath Ollama endpoint:** `http://192.168.1.20:11434` (NOT Tailscale; Beast Tailscale enrollment is v0.2 P5 #8)
- **Ollama version:** 0.21.0 (modern API; `/api/generate` + `/api/chat` + streaming via `stream:true` body field)
- **Models (canonical names):** `qwen2.5:72b` (47.4GB qwen2 family, primary), `deepseek-r1:70b` (42.5GB llama family, fallback), `llama3.1:70b` (42.5GB llama family, fallback)
- **Streaming format:** NDJSON line-delimited (each line is a complete JSON object), NOT Server-Sent Events. httpx `aiter_lines()` is the correct reader. Last line has `done:true` with full telemetry.
- **Token telemetry fields:** `prompt_eval_count` (input tokens), `eval_count` (output tokens), `total_duration` (ns), `load_duration` (ns), `prompt_eval_duration` (ns), `eval_duration` (ns). **Convert ns -> ms in atlas.events payload.**
- **Cold-start latency:** ~28s for qwen2.5:72b. Default read timeout 120s.
- **atlas.events schema target:** id bigint PK / ts timestamptz default now() / source text NOT NULL / kind text NOT NULL / payload jsonb. Both `source` + `kind` are NOT NULL — directive must always populate.

### 3.3 atlas.events row format for inference telemetry

```python
# example payload (Pydantic model InferenceTelemetry serialized to dict)
{
    "source": "atlas.inference",
    "kind": "generate",  # or "chat", "stream_generate", "stream_chat"
    "payload": {
        "model": "qwen2.5:72b",
        "prompt_eval_count": 31,
        "eval_count": 2,
        "total_duration_ms": 584,
        "load_duration_ms": 100,
        "prompt_eval_duration_ms": 253,
        "eval_duration_ms": 223,
        "status": "success",  # or "timeout", "error"
        "fallback_chain": ["qwen2.5:72b"],  # only includes models actually attempted
        "endpoint": "http://192.168.1.20:11434/api/generate",
    }
}
```

**Do NOT log prompt or response content to atlas.events.** Telemetry only -- prompts may contain PII or sensitive context. If full request/response capture is needed, that's a v0.2 audit-log concern (separate banked P5).

### 3.4 Cycle 1D 5-gate acceptance

1. `atlas.inference` module imports cleanly; `pip install -e ".[dev]"` still succeeds (httpx already in venv from Cycle 1A)
2. `GoliathClient.generate('Say OK', model='qwen2.5:72b', num_predict=5)` returns response containing 'OK' (or similar 1-5 token reply); warm-up call precedes assertion in test
3. Streaming smoke: `async for chunk in client.generate(..., stream=True)` yields >=1 chunk; final chunk has `done=True` and contains telemetry fields
4. Token logging: after a successful inference call, `SELECT * FROM atlas.events WHERE source='atlas.inference' ORDER BY ts DESC LIMIT 1` returns row with payload containing `prompt_eval_count`, `eval_count`, `total_duration_ms`, `model`
5. Standing anchor: B2b + Garage anchors bit-identical pre/post

Plus standing gates:
- 12 pytest tests passing total (8 prior + 4 new): PASS
- secret-grep on staged diff: clean (no API keys / endpoints with creds embedded)
- B2b subscription `controlplane_sub` untouched
- Garage cluster status unchanged
- atlas.events row count increased by exactly N inserts (where N = number of inference calls in test suite)

### 3.5 What Cycle 1D is NOT

- No embeddings (Cycle 1E -- TheBeast localhost mxbai-embed-large)
- No service start / systemd unit (Cycle 1H)
- No MCP server (Cycle 1G)
- No MCP client to CK (Cycle 1F)
- No Garage S3 use
- No Postgres DDL (atlas.events already exists from Cycle 1B; only INSERTs in this cycle)
- No prompt/response content captured to atlas.events (telemetry only)
- No Tailscale routing (Beast Tailscale is v0.2 P5)

### 3.6 Library-default discipline (per Cycle 1B lesson)

Learned from Cycle 1B's DSN-user-default issue: when authoring sketches dependent on library defaults, be EXPLICIT. For Cycle 1D specifically:

- `httpx.AsyncClient`: pass explicit `timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)`. Do NOT rely on default 5s read timeout (would always fail cold-start).
- `httpx.AsyncClient`: pass explicit `base_url='http://192.168.1.20:11434'`. Do NOT rely on relative URL resolution defaults.
- httpx streaming: use `client.stream('POST', url, json=body)` then `async for line in resp.aiter_lines()`. Do NOT rely on auto-decoding default behavior.
- JSON body: use `json=` kwarg. Do NOT manually serialize + set Content-Type (httpx handles).
- Response parsing: explicit `resp.raise_for_status()` before reading body.

## 4. Order of operations

```
1. PD: pull origin/main + read handoff + clear it
2. PD: read this paco_response (sections 0 + 3)
3. PD: capture Beast anchor pre + atlas.events row count pre
4. PD: implement atlas.inference module (client.py + models.py + telemetry.py + __init__.py)
5. PD: implement 4 tests (smoke, chat, streaming, token_logging)
6. PD: run pytest (12 tests; 4 new) -- all pass
7. PD: verify atlas.events post-cycle: rows added match test count, payload structure correct
8. PD: capture Beast anchor post + diff bit-identical
9. PD: commit + push to santigrey/atlas
10. PD: write paco_review_atlas_v0_1_cycle_1d_inference.md WITH Verified live block at section 0
11. PD: Cycle 1D close-out commit on santigrey/control-plane-lab folds:
    - paco_review_atlas_v0_1_cycle_1d_inference.md
    - SESSION.md Cycle 1D close section append
    - paco_session_anchor.md update (Cycle 1D CLOSED, Cycle 1E NEXT)
    - CHECKLIST.md audit entry
12. PD: write notification to handoff_pd_to_paco.md per bidirectional format spec
13. CEO: 'Paco, PD finished Cycle 1D, check handoff.'
```

## 5. Standing rules in effect (5)

- 5-guardrail rule + carve-outs (httpx calls + atlas.events INSERT are operational propagation under PD authority)
- B2b + Garage nanosecond anchor preservation invariant (still holding ~73+ hours)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol with bidirectional one-liner format
- Phase closure pattern (literal-PASS + spirit-partial)
- **Pre-directive verification (5th rule)** -- this directive has 16-row Verified live block in section 0
- Spec or no action: Cycle 1D fully scoped above
- Library-default discipline: explicit timeouts + base_urls + headers per Cycle 1B lesson
- P6 lessons banked: 20

## 6. Cycle 1 progress

```
Cycle 1: Runtime
  1A -- skeleton + first commit                    CLOSED 5/5 PASS
  1B -- Postgres connection layer                   CLOSED 5/5 PASS
  1C -- Garage S3 client + bucket adoption          CLOSED 5/5 PASS
  1D -- Goliath inference RPC                       GO (this directive)
  1E -- Embedding service (TheBeast localhost)      NEXT
  1F -- MCP client gateway (outbound to CK)         
  1G -- Atlas MCP server (inbound NEW)              
  1H -- Main loop + task dispatch                   
  1I -- Cycle 1 close                               
  
  Pace: 3 phases shipped Day 75. Cycle 1 close target: ~May 5-7 ahead of original ~May 6-12 schedule.
  Notable: 0 ESCs in Cycles 1B + 1C (5th standing rule prevented at spec-author time).
```

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1c_confirm_1d_go.md`

-- Paco
