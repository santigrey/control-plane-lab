#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
TARGET="${1:-single-node Ubuntu server}"
CONTEXT="${2:-deploy aiop-worker + api with systemd}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-6}"

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
    TARGET="$TARGET" CONTEXT="$CONTEXT" python3 - <<'PY'
import json
import os

target = os.environ["TARGET"]
context = os.environ["CONTEXT"]

prompt = (
    "Create an infrastructure deployment automation playbook. "
    f"Target: {target}. "
    f"Context: {context}. "
    "Return ONLY valid JSON (no markdown, no prose) in this exact top-level shape with these exact keys: "
    "objective, prechecks, plan, rollback, commands, verification, risks. "
    "Schema rules: objective is a non-empty string. Each array must contain only strings. "
    "No objects. No nested JSON. "
    "Use these exact counts: prechecks=5 strings, plan=8 strings, rollback=4 strings, "
    "commands=6 strings, verification=5 strings, risks=5 strings. "
    "Each array must contain only strings. No objects. No nested JSON. "
    "Use this exact template and replace values: "
    "{\"objective\":\"...\",\"prechecks\":[\"...\",\"...\",\"...\",\"...\",\"...\"],"
    "\"plan\":[\"...\",\"...\",\"...\",\"...\",\"...\",\"...\",\"...\",\"...\"],"
    "\"rollback\":[\"...\",\"...\",\"...\",\"...\"],"
    "\"commands\":[\"...\",\"...\",\"...\",\"...\",\"...\",\"...\"],"
    "\"verification\":[\"...\",\"...\",\"...\",\"...\",\"...\"],"
    "\"risks\":[\"...\",\"...\",\"...\",\"...\",\"...\"]}. "
    "All command entries must be executable shell command strings."
)

print(json.dumps({"prompt": prompt}))
PY
    return
  fi

  jq -nc --arg target "$TARGET" --arg context "$CONTEXT" '{
    prompt: (
      "Create an infrastructure deployment automation playbook. " +
      "Target: " + $target + ". " +
      "Context: " + $context + ". " +
      "Return ONLY valid JSON (no markdown, no prose) in this exact top-level shape with these exact keys: " +
      "objective, prechecks, plan, rollback, commands, verification, risks. " +
      "Schema rules: objective is a non-empty string. Each array must contain only strings. " +
      "No objects. No nested JSON. " +
      "Use these exact counts: prechecks=5 strings, plan=8 strings, rollback=4 strings, " +
      "commands=6 strings, verification=5 strings, risks=5 strings. " +
      "Each array must contain only strings. No objects. No nested JSON. " +
      "Use this exact template and replace values: " +
      "{\"objective\":\"...\",\"prechecks\":[\"...\",\"...\",\"...\",\"...\",\"...\"]," +
      "\"plan\":[\"...\",\"...\",\"...\",\"...\",\"...\",\"...\",\"...\",\"...\"]," +
      "\"rollback\":[\"...\",\"...\",\"...\",\"...\"]," +
      "\"commands\":[\"...\",\"...\",\"...\",\"...\",\"...\",\"...\"]," +
      "\"verification\":[\"...\",\"...\",\"...\",\"...\",\"...\"]," +
      "\"risks\":[\"...\",\"...\",\"...\",\"...\",\"...\"]}. " +
      "All command entries must be executable shell command strings."
    )
  }'
}

validate_with_jq() {
  printf '%s' "$RESP_BODY" | jq -e '
    .status == "ok"
    and ((.answer | fromjson?) as $p
      | ($p | type == "object")
      and ($p.objective | type == "string" and length > 0)
      and ($p.prechecks | type == "array" and length >= 5 and all(.[]; type == "string"))
      and ($p.plan | type == "array" and length >= 8 and all(.[]; type == "string"))
      and ($p.rollback | type == "array" and length >= 4 and all(.[]; type == "string"))
      and ($p.commands | type == "array" and length >= 6 and all(.[]; type == "string"))
      and ($p.verification | type == "array" and length >= 5 and all(.[]; type == "string"))
      and ($p.risks | type == "array" and all(.[]; type == "string"))
      and ((($p | keys) - ["objective","prechecks","plan","rollback","commands","verification","risks"]) | length == 0)
      and ((["objective","prechecks","plan","rollback","commands","verification","risks"] - ($p | keys)) | length == 0)
    )
  ' >/dev/null || return 1
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

required = {"objective", "prechecks", "plan", "rollback", "commands", "verification", "risks"}
if not isinstance(plan, dict):
    raise SystemExit(1)
if set(plan.keys()) != required:
    raise SystemExit(1)

ok = (
    isinstance(plan.get("objective"), str)
    and plan.get("objective", "").strip() != ""
    and isinstance(plan.get("prechecks"), list)
    and len(plan.get("prechecks", [])) >= 5
    and all(isinstance(x, str) for x in plan.get("prechecks", []))
    and isinstance(plan.get("plan"), list)
    and len(plan.get("plan", [])) >= 8
    and all(isinstance(x, str) for x in plan.get("plan", []))
    and isinstance(plan.get("rollback"), list)
    and len(plan.get("rollback", [])) >= 4
    and all(isinstance(x, str) for x in plan.get("rollback", []))
    and isinstance(plan.get("commands"), list)
    and len(plan.get("commands", [])) >= 6
    and all(isinstance(x, str) for x in plan.get("commands", []))
    and isinstance(plan.get("verification"), list)
    and len(plan.get("verification", [])) >= 5
    and all(isinstance(x, str) for x in plan.get("verification", []))
    and isinstance(plan.get("risks"), list)
    and all(isinstance(x, str) for x in plan.get("risks", []))
)

raise SystemExit(0 if ok else 1)
PY
  [[ $? -eq 0 ]] || return 1
}

LAST_BODY=""
for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  PAYLOAD="$(build_payload)"
  http_post_ask "$PAYLOAD"

  if [[ "$RESP_CODE" != "200" ]]; then
    LAST_BODY="$RESP_BODY"
    continue
  fi

  if [[ "$HAS_JQ" -eq 1 ]]; then
    if validate_with_jq; then
      echo "PLAYBOOK PASS"
      exit 0
    fi
  else
    if validate_with_python; then
      echo "PLAYBOOK PASS"
      exit 0
    fi
  fi

  LAST_BODY="$RESP_BODY"
done

fail "playbook validation failed after $MAX_ATTEMPTS attempts. Response body: $LAST_BODY"
