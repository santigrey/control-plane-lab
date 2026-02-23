#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
TOPIC="${1:-${TOPIC:-AI incident response for a small SaaS company}}"

HAS_JQ=0
HAS_PY=0
command -v jq >/dev/null 2>&1 && HAS_JQ=1
command -v python3 >/dev/null 2>&1 && HAS_PY=1

if [[ "$HAS_JQ" -eq 0 && "$HAS_PY" -eq 0 ]]; then
  echo "ERROR: need jq or python3 for JSON validation" >&2
  exit 1
fi

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

http_post_ask() {
  local payload="$1"
  local body_file
  body_file="$(mktemp)"

  local status
  status="$(curl -sS -o "$body_file" -w "%{http_code}" -X POST "$BASE_URL/ask" -H 'Content-Type: application/json' --data "$payload")" || {
    rm -f "$body_file"
    fail "curl failed for POST /ask"
  }

  RESP_CODE="$status"
  RESP_BODY="$(cat "$body_file")"
  rm -f "$body_file"
}

build_payload() {
  if [[ "$HAS_PY" -eq 1 ]]; then
    TOPIC="$TOPIC" python3 - <<'PY'
import json
import os

topic = os.environ["TOPIC"]
prompt = (
    "You are producing a research playbook. "
    f"Topic: {topic}. "
    "Return ONLY valid JSON (no markdown, no prose) with exactly these keys: "
    "goal, assumptions, steps, deliverables, risks. "
    "Schema requirements: goal is a non-empty string; assumptions is an array; "
    "steps is an array with at least 5 items; deliverables is an array; risks is an array."
)
print(json.dumps({"prompt": prompt}))
PY
    return
  fi

  # Fallback builder if python3 is unavailable.
  jq -nc --arg topic "$TOPIC" '{
    prompt: (
      "You are producing a research playbook. Topic: " + $topic +
      ". Return ONLY valid JSON (no markdown, no prose) with exactly these keys: " +
      "goal, assumptions, steps, deliverables, risks. " +
      "Schema requirements: goal is a non-empty string; assumptions is an array; " +
      "steps is an array with at least 5 items; deliverables is an array; risks is an array."
    )
  }'
}

validate_with_jq() {
  printf '%s' "$RESP_BODY" | jq -e '
    .status == "ok"
    and ((.answer | fromjson?) as $p
      | ($p | type == "object")
      and ($p.goal | type == "string" and length > 0)
      and ($p.assumptions | type == "array")
      and ($p.steps | type == "array" and length >= 5)
      and ($p.deliverables | type == "array")
      and ($p.risks | type == "array")
    )
  ' >/dev/null || fail "playbook validation failed. Body: $RESP_BODY"
}

validate_with_python() {
  printf '%s' "$RESP_BODY" | python3 - <<'PY'
import json
import sys

resp = json.load(sys.stdin)
if resp.get("status") != "ok":
    raise SystemExit(1)

answer = resp.get("answer", "")
plan = json.loads(answer)

ok = (
    isinstance(plan, dict)
    and isinstance(plan.get("goal"), str)
    and plan.get("goal", "").strip() != ""
    and isinstance(plan.get("assumptions"), list)
    and isinstance(plan.get("steps"), list)
    and len(plan.get("steps", [])) >= 5
    and isinstance(plan.get("deliverables"), list)
    and isinstance(plan.get("risks"), list)
)

raise SystemExit(0 if ok else 1)
PY
  [[ $? -eq 0 ]] || fail "playbook validation failed. Body: $RESP_BODY"
}

PAYLOAD="$(build_payload)"
http_post_ask "$PAYLOAD"

[[ "$RESP_CODE" == "200" ]] || fail "POST /ask returned HTTP $RESP_CODE. Body: $RESP_BODY"

if [[ "$HAS_JQ" -eq 1 ]]; then
  validate_with_jq
else
  validate_with_python
fi

echo "PLAYBOOK PASS"
