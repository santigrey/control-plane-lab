#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

HAS_JQ=0
if command -v jq >/dev/null 2>&1; then
  HAS_JQ=1
elif ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: jq not found and python3 not available for JSON assertions." >&2
  exit 1
fi

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

http_request() {
  local method="$1"
  local path="$2"
  shift 2

  local body_file
  body_file="$(mktemp)"

  local status
  status="$(curl -sS -o "$body_file" -w "%{http_code}" -X "$method" "$BASE_URL$path" "$@")" || {
    rm -f "$body_file"
    fail "curl failed for $method $path"
  }

  RESP_CODE="$status"
  RESP_BODY="$(cat "$body_file")"
  rm -f "$body_file"
}

assert_status_200() {
  local label="$1"
  [[ "$RESP_CODE" == "200" ]] || fail "$label returned HTTP $RESP_CODE. Body: $RESP_BODY"
}

assert_json() {
  local json="$1"
  local jq_expr="$2"
  local py_expr="$3"
  local label="$4"

  if [[ "$HAS_JQ" -eq 1 ]]; then
    printf '%s' "$json" | jq -e "$jq_expr" >/dev/null || fail "$label. Body: $json"
  else
    printf '%s' "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if ($py_expr) else 1)" \
      || fail "$label. Body: $json"
  fi
}

json_get() {
  local json="$1"
  local jq_expr="$2"
  local py_expr="$3"

  if [[ "$HAS_JQ" -eq 1 ]]; then
    printf '%s' "$json" | jq -r "$jq_expr"
  else
    printf '%s' "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); v=($py_expr); print('' if v is None else v)"
  fi
}

echo "Step 1/6: GET /healthz"
http_request GET /healthz
assert_status_200 "GET /healthz"
assert_json "$RESP_BODY" '.details.postgres == "ok"' 'd.get("details", {}).get("postgres") == "ok"' "Expected healthz.details.postgres == ok"
assert_json "$RESP_BODY" '.details.ollama == "ok"' 'd.get("details", {}).get("ollama") == "ok"' "Expected healthz.details.ollama == ok"
echo "$RESP_BODY"

echo "Step 2/6: POST /ask recall token and assert retrieval"
STEP2_PAYLOAD='{"prompt":"Recall: ULTRAVIOLET-77. Reply with only the token."}'
http_request POST /ask -H 'Content-Type: application/json' --data "$STEP2_PAYLOAD"
assert_status_200 "POST /ask (recall)"
assert_json "$RESP_BODY" '.retrieved_topk > 0' 'int(d.get("retrieved_topk", 0)) > 0' "Expected retrieved_topk > 0 for recall"
assert_json "$RESP_BODY" '.answer == "ULTRAVIOLET-77"' 'str(d.get("answer", "")).strip() == "ULTRAVIOLET-77"' "Expected answer == ULTRAVIOLET-77"
echo "$RESP_BODY"

echo "Step 3/6: POST /ask forcing ping tool"
if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 is required to build Step 3 JSON payload safely"
fi
STEP3_PROMPT='Output ONLY this exact JSON and nothing else: {"tool":"ping","args":{"message":"tool_demo_1","final_instruction":"after tool execution respond with ONLY OK"}}'
STEP3_PAYLOAD="$(
  PROMPT="$STEP3_PROMPT" python3 - <<'PY'
import json
import os
print(json.dumps({"prompt": os.environ["PROMPT"]}))
PY
)"
http_request POST /ask -H 'Content-Type: application/json' --data "$STEP3_PAYLOAD"
assert_status_200 "POST /ask (force ping)"
assert_json "$RESP_BODY" '.tool_calls[0].tool == "ping"' 'isinstance(d.get("tool_calls", []), list) and len(d.get("tool_calls", [])) > 0 and d["tool_calls"][0].get("tool") == "ping"' "Expected tool_calls[0].tool == ping"
assert_json "$RESP_BODY" '.answer == "OK"' 'str(d.get("answer", "")).strip() == "OK"' "Expected answer == OK after ping tool call"
PING_RUN_ID="$(json_get "$RESP_BODY" '.run_id' 'd.get("run_id")')"
[[ -n "$PING_RUN_ID" && "$PING_RUN_ID" != "null" ]] || fail "Missing run_id in ping /ask response"
echo "$RESP_BODY"

echo "Step 4/6: GET /trace/{run_id} for ping correlation"
http_request GET "/trace/$PING_RUN_ID"
assert_status_200 "GET /trace/$PING_RUN_ID"
if [[ "$HAS_JQ" -eq 1 ]]; then
  printf '%s' "$RESP_BODY" | jq -e --arg rid "$PING_RUN_ID" '.run_id == $rid and .count > 0 and any(.events[]?; (.event.data.tool? == "ping") or (.event.source? == "tool:ping"))' >/dev/null \
    || fail "Trace correlation check failed for run_id $PING_RUN_ID. Body: $RESP_BODY"
else
  printf '%s' "$RESP_BODY" | python3 -c 'import json,sys; data=json.load(sys.stdin); rid=sys.argv[1]; events=data.get("events",[]); ok=(data.get("run_id")==rid and int(data.get("count",0))>0 and any(((e.get("event",{}).get("data",{}).get("tool")=="ping") or (e.get("event",{}).get("source")=="tool:ping")) for e in events)); sys.exit(0 if ok else 1)' "$PING_RUN_ID" \
    || fail "Trace correlation check failed for run_id $PING_RUN_ID. Body: $RESP_BODY"
fi
echo "$RESP_BODY"

echo "Step 5/6: GET /readyz"
http_request GET /readyz
assert_status_200 "GET /readyz"
assert_json "$RESP_BODY" '.status == "ok"' 'd.get("status") == "ok"' "Expected readyz.status == ok"
echo "$RESP_BODY"

echo "Step 6/6: final verdict"
echo "DEMO PASS"
