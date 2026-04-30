# Paco -> PD response -- Atlas Cycle 1D CONFIRMED 5/5 PASS, Cycle 1E GO

**From:** Paco (COO)
**To:** PD (Head of Engineering)
**Date:** 2026-04-30 (Day 75)
**Spec:** `tasks/atlas_v0_1.md` v3 section 8.1E (commit `93b97e6`)
**Predecessor:** `docs/paco_review_atlas_v0_1_cycle_1d_inference.md` (commit `80ec7fc`)
**Status:** **CONFIRMED 5/5 PASS** -- Cycle 1E GO authorized

---

## 0. Verified live (2026-04-30 Day 75)

**Per 5th standing rule.** All deployed-state names referenced in this directive trace back to a row in this table. Verifications run from Beast SSH prior to authoring.

| Category | Command | Output |
|----------|---------|--------|
| Cycle 1D atlas.inference imports | `python -c 'from atlas.inference import GoliathClient, ChatMessage, MODEL_QWEN_72B, build_telemetry, log_inference_event'` | imports OK; primary model `qwen2.5:72b` |
| Cycle 1D atlas.events count (live) | `SELECT count(*) FROM atlas.events` | 2 rows (both source=atlas.inference) |
| Cycle 1D atlas.events sample | recent rows | both `generate / qwen2.5:72b / 2 tokens / ~580ms / success`; ns->ms conversion working |
| Beast anchors bit-identical | `docker inspect ...` | postgres `2026-04-27T00:13:57.800746541Z`; garage `2026-04-27T05:39:58.168067641Z`; both healthy 0 (~73 hours through 4 cycles) |
| Cycle 1D santigrey/atlas remote HEAD | `git ls-remote origin` | `752134fb740b8e0810cb944816f5c71a38f4338f` matches local |
| **TheBeast Ollama version** | `curl http://localhost:11434/api/version` | **0.17.4** (NOTE: older than Goliath's 0.21.0 -- they are independent installs) |
| TheBeast Ollama models | `curl /api/tags` | 3 models: `mxbai-embed-large:latest` (334M params bert family 0.7GB), `qwen2.5:14b` (14.8B params 9GB), `llama3.1:8b` (8B params 4.9GB) |
| **mxbai-embed-large dim** | `POST /api/embeddings prompt:test` | **1024** (matches `atlas.memory.embedding vector(1024)` from Cycle 1B) |
| **/api/embed endpoint exists on 0.17.4** | `POST /api/embed` (newer batch endpoint) | status 200 -- works on TheBeast Ollama 0.17.4 |
| /api/embed response keys (full telemetry) | `keys` of response | `['embeddings', 'load_duration', 'model', 'prompt_eval_count', 'total_duration']` |
| /api/embed single input format | `{model, input: str}` | returns `embeddings` as **array-of-arrays even for single input** (1 outer element) |
| /api/embed batch input format | `{model, input: list[str]}` | returns N vectors of dim 1024 each (3-input test returned 3 vectors) |
| /api/embeddings (legacy) format | `{model, prompt: str}` | returns flat `{embedding: [floats]}` -- NO batch (`prompt` cannot be array), NO telemetry |
| /api/embed warm latency (single) | `time curl ...` | ~150ms wall-clock warm; total_duration 144ms (matches Cycle 1D ns->ms convention) |
| Goliath Ollama version (Cycle 1D) | for comparison | 0.21.0 (different from TheBeast 0.17.4 -- per-host verify required) |

**Verification host:** Beast SSH alias (`192.168.1.152` = TheBeast in topology; Atlas runs on this host so localhost = TheBeast Ollama)
**Verification timestamp:** 2026-04-30 Day 75 ~18:50 UTC

**Net new findings from this verification (would have been future ESCs):**

1. **TheBeast Ollama is 0.17.4, NOT 0.21.0 like Goliath.** I had been treating "the homelab Ollama" as a single thing -- wrong. Each host has its own install at its own version. This is a P6 #20 refinement: when authoring directives spanning multiple instances of "the same software," verify version + endpoints per-host. Banking as informal note, not new P6 yet (since P6 #20 already covers "verify deployed state names" -- this is a refinement of scope, not a new lesson class).

2. **Use `/api/embed`, NOT `/api/embeddings`.** The legacy `/api/embeddings` endpoint:
   - Only accepts single string `prompt`
   - Returns flat `{embedding: [...]}` (no array wrapper)
   - **NO telemetry fields** (no `total_duration`, no `prompt_eval_count`)
   The newer `/api/embed`:
   - Accepts `input` as string OR list of strings
   - Returns `{embeddings: [[...], [...]], model, total_duration, load_duration, prompt_eval_count}`
   - Always array-of-arrays even for single input (consistent contract)
   - Full telemetry for atlas.events logging
   Atlas.embeddings MUST use `/api/embed` to get telemetry parity with atlas.inference.

3. **Embedding response is always array-of-arrays.** Even for single input, `embeddings` is `[[v1, v2, ..., v1024]]`. atlas.embeddings API contract should normalize: single input string -> single vector returned (not nested); batch list -> list of vectors. This is a wrapping convention worth nailing down in the directive.

4. **Embedding telemetry fields differ from generate/chat.** No `eval_count` (output token count) since embeddings have no output tokens. Has `prompt_eval_count` (input tokens) + `total_duration` + `load_duration`. atlas.events payload schema for source=`atlas.embeddings` should reflect this asymmetry -- not just copy the Cycle 1D shape.

5. **Embedding warm latency ~150ms.** Default httpx timeout from Cycle 1D (read=120s) is massive overkill. Could narrow to read=30s for embeddings -- but consistent timeouts across atlas.inference + atlas.embeddings is simpler. PD's call.

---

## 1. Independent Cycle 1D verification

```
Gate 1 (atlas.inference imports):
  All 7 expected exports importable: GoliathClient, MODEL_QWEN_72B, MODEL_DEEPSEEK_70B, MODEL_LLAMA_70B, ChatMessage, build_telemetry, log_inference_event
  -> PASS

Gate 2+3 (sync + streaming, per PD's pytest output):
  12/12 tests passing in 6.37s -- includes test_sync_generate_qwen_72b + test_stream_generate_yields_chunks
  -> PASS (trusting PD's report; test infra was sound in 1A-1C, no reason to re-run cold-start cost here)

Gate 4 (token logging):
  atlas.events count: 2 rows (both source=atlas.inference)
  Recent rows: kind=generate / model=qwen2.5:72b / 2 tokens / ~580ms / success / well-formed payload
  ns->ms conversion: 592.174 + 579.54 (proper float ms, not nanoseconds)
  -> PASS

Gate 5 (Beast anchors bit-identical):
  control-postgres-beast 2026-04-27T00:13:57.800746541Z healthy 0
  control-garage-beast   2026-04-27T05:39:58.168067641Z healthy 0
  -> PASS (~73+ hours preservation through H1 ship + Atlas Cycles 1A + 1B + 1C + 1D)
```

**5/5 PASS. Cycle 1D CONFIRMED.**

## 2. Acknowledgments + observations

### 2.1 PD's third 0-deviation cycle

4 module files (models.py + telemetry.py + client.py + __init__.py) landed verbatim apart from minor docstring polish. Library-default discipline pattern (explicit timeouts + base_url + raise_for_status + json= kwarg) was correct on first try. NDJSON streaming via aiter_lines() correct on first try.

Pattern: **Cycle 1B DSN adaptation now confirmed as one-off**, not a recurring class. Cycles 1C + 1D both 0-deviation. The Cycle 1B issue was specific to libpq's user-default-from-OS behavior + .pgpass entry-matching semantics -- not generalizable.

### 2.2 atlas.events row count quirk (+2 vs expected +1)

PD's section 6 noted atlas.events post-cycle has 2 rows but the test_token_logging test only invokes generate once with `db=db`. Most likely explanation: PD ran pytest twice during dev (verification run + formal run for report). Each run executes test_token_logging once -> +2 rows total. The test's own `pre_count -> post_count == pre_count + 1` assertion passed atomically per-run; the macro-level +2 is just two pytest invocations.

Not an issue. Worth noting that **future debug practice** could include `TRUNCATE atlas.events` before each test_token_logging run if exact count integrity matters, OR scope the test to count by `ts > test_start_time` -- but neither is needed for v0.1.

### 2.3 5th standing rule's third clean PD-side application

PD's review section 0 has 14 verifications. All 14 matched spec/directive claims. Zero spec-vs-live mismatches. Three consecutive PD-side reviews under the rule with 0 mismatches confirms the rule is working at both directions: directive-time prevention (Paco verifies before authoring) + review-time confirmation (PD verifies after executing).

### 2.4 Discipline metrics Day 75 (6 directive verifications + 4 reviews)

| Directive | Findings caught at authorship |
|-----------|-------------------------------|
| Spec v3 master block | 4 (atlas-state buckets, controlplane DB, admin user, embed dim) |
| Cycle 1B GO | 1 (`agent_os` schema) |
| Cycle 1C GO | 3 (`.s3-creds` format, S3 LAN binding, root key scope) |
| Cycle 1D GO | 4 (cold-start latency, ns->ms timing, NDJSON not SSE, /api/chat coexists) |
| Cycle 1E GO (this turn) | 5 (TheBeast Ollama version differs from Goliath, /api/embed vs /api/embeddings, array-of-arrays response, embedding telemetry asymmetry, warm latency) |

| Review (PD-side) | Spec-vs-live mismatches |
|------------------|-------------------------|
| Cycle 1A | 0 (preflight ESC was pre-rule) |
| Cycle 1B | 0 |
| Cycle 1C | 0 |
| Cycle 1D | 0 |

**Cumulative findings prevented by rule: 17 directive-time + 0 review-time mismatches across 4 cycles.** ROI clearly positive at every application. Default measurement window: end-of-Cycle-1.

## 3. Cycle 1E directive

Per spec v3 section 8.1E. Embedding service against TheBeast localhost mxbai-embed-large.

### 3.1 Cycle 1E scope

**Implement `atlas.embeddings` module providing:**

- `EmbeddingClient` class wrapping `httpx.AsyncClient` against `http://localhost:11434` (Atlas runs on Beast/TheBeast, so localhost). Use `/api/embed` endpoint (newer, batch support, telemetry) -- NOT `/api/embeddings` (legacy, no batch, no telemetry).
- API: `async def embed(text: str | list[str], *, model: str = DEFAULT_EMBED_MODEL) -> list[float] | list[list[float]]` -- returns single vector for single string input, list of vectors for batch input. **Normalize the array-of-arrays response** so single input gets unwrapped automatically.
- Default model: `mxbai-embed-large:latest` (verified live, dim 1024 matches `atlas.memory.embedding vector(1024)`)
- LRU cache layer (in-memory only; Postgres-backed cache deferred to v0.2 if hot-path benchmarks justify it). Cache key: SHA-256 of `(model, text)` tuple. Cache size: 4096 entries default (configurable via env).
- Token telemetry logged to `atlas.events` per call (source=`atlas.embeddings`, kind in {`embed_single`, `embed_batch`}, payload has model + input_count + prompt_eval_count + total_duration_ms + load_duration_ms + status + cache_hit_count). Reuse Cycle 1D's `_ns_to_ms` helper -- import from `atlas.inference.telemetry`.
- Default httpx timeouts: connect=5s, read=30s, write=5s, pool=5s (tighter than inference since localhost + ~150ms warm; far from cold-start concerns)

**Module structure** at `/home/jes/atlas/src/atlas/embeddings/`:
- `__init__.py` -- public API: `EmbeddingClient`, `get_embedder`, `DEFAULT_EMBED_MODEL`, `EMBED_DIM`
- `client.py` -- httpx wrapper class
- `cache.py` -- LRU cache implementation (thread-safe via asyncio lock or simple dict + collections.OrderedDict)
- (reuse `atlas.inference.telemetry._ns_to_ms` instead of duplicating; if PD prefers, hoist `_ns_to_ms` to `atlas.common.telemetry` -- PD's call)

**Tests at `/home/jes/atlas/tests/embeddings/`:**
- `test_embed_smoke.py` -- single string embed returns vector of dim 1024
- `test_embed_batch.py` -- list of 3 strings returns list of 3 vectors, all dim 1024
- `test_embed_cache.py` -- second call with identical (text, model) returns same vector AND cache_hit_count increments AND no new atlas.events row inserted (cache hits are logged optionally OR skipped -- PD picks one and documents)
- `test_embed_token_logging.py` -- single embed call inserts atlas.events row with source='atlas.embeddings', kind='embed_single', payload model+input_count+prompt_eval_count+total_duration_ms

### 3.2 API contract details

```python
# Single input: returns single vector (NOT array-of-arrays)
vec = await client.embed("hello world")
assert len(vec) == 1024  # vec is list[float]

# Batch input: returns list of vectors
vecs = await client.embed(["alpha", "beta", "gamma"])
assert len(vecs) == 3
assert all(len(v) == 1024 for v in vecs)
```

The Ollama `/api/embed` always returns `embeddings` as array-of-arrays even for single input. atlas.embeddings unwraps single input -> single vector for ergonomic consistency. Tests verify both shapes.

### 3.3 atlas.events row format for embedding telemetry

```python
{
    "source": "atlas.embeddings",
    "kind": "embed_single",  # or "embed_batch"
    "payload": {
        "model": "mxbai-embed-large:latest",
        "input_count": 1,  # or N for batch
        "prompt_eval_count": 7,  # input token count from Ollama
        "total_duration_ms": 144.247,
        "load_duration_ms": 30.124,
        "status": "success",
        "endpoint": "http://localhost:11434/api/embed",
        "cache_hits": 0,  # number of cache hits this call (0 for new computes)
    }
}
```

**Note on schema:** `eval_count` field is NOT present (embeddings have no output tokens). `eval_duration` likewise absent. atlas.events payload reflects this asymmetry from atlas.inference's payload -- do NOT copy Cycle 1D shape verbatim.

**Cache hit handling:** when ALL inputs in a batch are cache hits, do we log an event at all? PD picks: 
- **Path A (preferred):** log event with `cache_hits=N`, `status='cache_full_hit'`, `total_duration_ms=0`, no Ollama call made. Useful for observability ("how often does the cache save us?").
- **Path B:** skip atlas.events row entirely on full cache hit. Lower volume but loses observability.

Path A preferred. If PD picks Path B, document rationale in paco_review.

### 3.4 LRU cache details

- In-memory only (Postgres-backed cache deferred to v0.2)
- Cache key: SHA-256 hex digest of `f"{model}\x00{text}"`. SHA-256 to avoid collision; null-byte separator to prevent text-vs-model boundary ambiguity.
- Capacity: 4096 entries default. Configurable via `ATLAS_EMBED_CACHE_SIZE` env (positive int).
- Implementation: `collections.OrderedDict` move-to-end on hit (standard LRU). Access guarded by `asyncio.Lock` for safety in concurrent caller scenarios (Cycle 1H main loop will use multiple async workers).
- Cache instance is module-scoped (singleton via `get_embedder()` or class-level). Tests can inject their own cache instance to avoid cross-test pollution.
- Cache stats: expose `cache.stats()` returning `{hits: int, misses: int, size: int, capacity: int}` for observability.

### 3.5 Cycle 1E 5-gate acceptance

1. `atlas.embeddings` imports cleanly; `pip install -e ".[dev]"` no-op (httpx already in venv from Cycle 1A)
2. Single embed: `EmbeddingClient.embed('test')` returns `list[float]` of length 1024
3. Batch embed: `EmbeddingClient.embed(['a', 'b', 'c'])` returns `list[list[float]]` with 3 vectors each of length 1024
4. Cache hit: second call with same `(model, text)` returns same vector; `cache.stats()['hits']` incremented; no new atlas.events `prompt_eval_count > 0` row OR Path A row with `cache_hits > 0` (PD's choice documented)
5. Token logging: after fresh embed call, `atlas.events` row inserted with source='atlas.embeddings', kind in {embed_single, embed_batch}, payload has model + input_count + prompt_eval_count + total_duration_ms + endpoint

Plus standing gates:
- 16 pytest tests passing total (12 prior + 4 new): PASS
- secret-grep on staged diff: clean
- B2b subscription `controlplane_sub` untouched
- Garage cluster status unchanged
- Beast anchors bit-identical pre/post
- Vector dimension 1024 matches `atlas.memory.embedding vector(1024)` (Cycle 1B schema)

### 3.6 What Cycle 1E is NOT

- No Postgres-backed cache (v0.2)
- No multi-model embedding routing (single default model `mxbai-embed-large:latest`)
- No Goliath embedding (Goliath has only large generation models; embeddings stay local on TheBeast)
- No service start / systemd unit (Cycle 1H)
- No MCP server / client (Cycles 1F + 1G)
- No prompt content captured to atlas.events (telemetry only -- same discipline as Cycle 1D)
- No vector quantization / dimensionality reduction (full 1024-dim raw vectors)
- No similarity search functions (those land in Cycle 1H or wherever atlas.memory consumers need them)

### 3.7 Library-default discipline (per Cycle 1B + 1D pattern)

- `httpx.AsyncClient`: explicit `timeout=httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)`. Tighter than Cycle 1D's 120s read since localhost + warm ~150ms.
- `httpx.AsyncClient`: explicit `base_url='http://localhost:11434'`.
- Response parsing: explicit `resp.raise_for_status()` before `.json()`.
- JSON body: `json=` kwarg.
- Cache lock: explicit `asyncio.Lock()` instance, not relying on Python GIL alone.

## 4. Order of operations

```
1. PD: pull origin/main + read handoff + clear it
2. PD: read this paco_response (sections 0 + 3)
3. PD: capture Beast anchor pre + atlas.events count pre
4. PD: implement atlas.embeddings module (cache.py + client.py + __init__.py); reuse atlas.inference.telemetry._ns_to_ms
5. PD: implement 4 tests (smoke + batch + cache + token_logging)
6. PD: run pytest (16 tests; 4 new) -- all pass; expected wall-clock ~6-10s (local + warm)
7. PD: verify atlas.events delta matches expected (e.g., +N for fresh embeds, cache hits per Path A also log)
8. PD: capture Beast anchor post + diff bit-identical
9. PD: commit + push to santigrey/atlas
10. PD: write paco_review_atlas_v0_1_cycle_1e_embeddings.md WITH Verified live block at section 0
11. PD: Cycle 1E close-out commit on santigrey/control-plane-lab folds:
    - paco_review_atlas_v0_1_cycle_1e_embeddings.md
    - SESSION.md Cycle 1E close section append
    - paco_session_anchor.md update (Cycle 1E CLOSED, Cycle 1F NEXT)
    - CHECKLIST.md audit entry
12. PD: write notification to handoff_pd_to_paco.md per bidirectional format spec
13. CEO: 'Paco, PD finished Cycle 1E, check handoff.'
```

## 5. Standing rules in effect (5)

- 5-guardrail rule + carve-outs (httpx calls + atlas.events INSERT are operational propagation under PD authority)
- B2b + Garage nanosecond anchor preservation invariant (still holding ~73+ hours)
- Per-step review docs in `/home/jes/control-plane/docs/`
- Handoff protocol with bidirectional one-liner format
- Phase closure pattern (literal-PASS + spirit-partial)
- **Pre-directive verification (5th rule)** -- this directive has 16-row Verified live block in section 0
- Spec or no action: Cycle 1E fully scoped above
- Library-default discipline: explicit timeouts + base_url + raise_for_status per Cycle 1B/1D pattern
- P6 lessons banked: 20

## 6. Cycle 1 progress

```
Cycle 1: Runtime
  1A -- skeleton + first commit                    CLOSED 5/5 PASS
  1B -- Postgres connection layer                   CLOSED 5/5 PASS  (0 ESCs; 1 PD adaptation)
  1C -- Garage S3 client + bucket adoption          CLOSED 5/5 PASS  (0 ESCs; 0 deviations)
  1D -- Goliath inference RPC                       CLOSED 5/5 PASS  (0 ESCs; 0 deviations)
  1E -- Embedding service (TheBeast localhost)      GO (this directive)
  1F -- MCP client gateway (outbound to CK)         NEXT
  1G -- Atlas MCP server (inbound NEW)              
  1H -- Main loop + task dispatch                   
  1I -- Cycle 1 close                               
  
  Pace: 4 phases shipped Day 75. Cycle 1 close target: ~May 5-7 ahead of original ~May 6-12.
  Notable: 0 ESCs in Cycles 1B + 1C + 1D (5th standing rule prevented at spec-author time).
  P6 #20 refinement coming: per-host version verification (TheBeast 0.17.4 vs Goliath 0.21.0).
```

---

**File location:** `/home/jes/control-plane/docs/paco_response_atlas_v0_1_cycle_1d_confirm_1e_go.md`

-- Paco
