#!/bin/bash
# canaries/reachability_probe.sh
# Reachability Probe v1.0 -- Project Ascension fleet SSH N×N matrix
# Per docs/homelab_reachability_v1_0.md
#
# Usage:
#   bash canaries/reachability_probe.sh           # full A<->A matrix from CK
#   bash canaries/reachability_probe.sh --json    # machine-readable output
#   bash canaries/reachability_probe.sh --quick   # source-host-only outbound
#
# Exit:
#   0 = all pairs PASS
#   1 = one or more pairs FAIL
#   2 = script error (canon mismatch / orchestrator host issue)

set -u

JSON_MODE=false
QUICK_MODE=false
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --quick) QUICK_MODE=true ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# Class A node inventory (must match docs/homelab_reachability_v1_0.md)
# Format: name:lan_ip:user
NODES_A=(
  "ciscokid:192.168.1.10:jes"
  "beast:192.168.1.152:jes"
  "slimjim:192.168.1.40:jes"
  "goliath:192.168.1.20:jes"
  "kalipi:192.168.1.254:jes"
  "pi3:192.168.1.139:jes"
  "macmini:192.168.1.13:jes"
)

SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o LogLevel=ERROR"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ORCHESTRATOR=$(hostname -s 2>/dev/null || echo unknown)

results_pass=0
results_fail=0
results_skip=0
results_lines=()

probe_pair() {
  local src_name="$1" src_ip="$2" src_user="$3"
  local tgt_name="$4" tgt_ip="$5" tgt_user="$6"

  if [ "$src_name" = "$tgt_name" ]; then return; fi

  local cmd_inner="ssh $SSH_OPTS ${tgt_user}@${tgt_ip} 'echo OK' 2>&1"
  local cmd_outer="ssh $SSH_OPTS ${src_user}@${src_ip} \"$cmd_inner\""
  local output
  output=$(eval "$cmd_outer" 2>&1)
  local exit_code=$?

  if [ $exit_code -eq 0 ] && [ "$output" = "OK" ]; then
    results_pass=$((results_pass + 1))
    results_lines+=("PASS|${src_name}|${tgt_name}|${src_user}@${src_ip}->${tgt_user}@${tgt_ip}|")
  else
    results_fail=$((results_fail + 1))
    local fail_summary
    fail_summary=$(echo "$output" | head -1 | tr '|' ';' | tr -d '\n')
    results_lines+=("FAIL|${src_name}|${tgt_name}|${src_user}@${src_ip}->${tgt_user}@${tgt_ip}|${fail_summary}")
  fi
}

# Mode A: --quick = only outbound from current host
if [ "$QUICK_MODE" = true ]; then
  src_entry=""
  for entry in "${NODES_A[@]}"; do
    IFS=':' read -r n ip u <<< "$entry"
    if [ "$n" = "$ORCHESTRATOR" ]; then src_entry="$entry"; fi
  done
  if [ -z "$src_entry" ]; then
    echo "ERROR: orchestrator host '$ORCHESTRATOR' not in canon NODES_A" >&2
    exit 2
  fi
  IFS=':' read -r src_name src_ip src_user <<< "$src_entry"
  for tgt_entry in "${NODES_A[@]}"; do
    IFS=':' read -r tgt_name tgt_ip tgt_user <<< "$tgt_entry"
    if [ "$src_name" = "$tgt_name" ]; then continue; fi
    # Direct outbound (not via SSH-of-SSH)
    if ssh $SSH_OPTS "${tgt_user}@${tgt_ip}" "echo OK" 2>/dev/null | grep -q OK; then
      results_pass=$((results_pass + 1))
      results_lines+=("PASS|${src_name}|${tgt_name}|${src_user}@${src_ip}->${tgt_user}@${tgt_ip}|")
    else
      results_fail=$((results_fail + 1))
      results_lines+=("FAIL|${src_name}|${tgt_name}|${src_user}@${src_ip}->${tgt_user}@${tgt_ip}|connect or auth fail")
    fi
  done
else
  # Mode B: full A<->A matrix
  for src_entry in "${NODES_A[@]}"; do
    IFS=':' read -r src_name src_ip src_user <<< "$src_entry"
    for tgt_entry in "${NODES_A[@]}"; do
      IFS=':' read -r tgt_name tgt_ip tgt_user <<< "$tgt_entry"
      probe_pair "$src_name" "$src_ip" "$src_user" "$tgt_name" "$tgt_ip" "$tgt_user"
    done
  done
fi

total=$((results_pass + results_fail))

if [ "$JSON_MODE" = true ]; then
  printf '{"timestamp":"%s","orchestrator":"%s","mode":"%s","total":%d,"pass":%d,"fail":%d,"pairs":[' \
    "$TIMESTAMP" "$ORCHESTRATOR" "$([ "$QUICK_MODE" = true ] && echo quick || echo full)" "$total" "$results_pass" "$results_fail"
  first=true
  for line in "${results_lines[@]}"; do
    IFS='|' read -r status src tgt path err <<< "$line"
    if [ "$first" = false ]; then printf ','; fi
    first=false
    printf '{"status":"%s","src":"%s","tgt":"%s","path":"%s","err":"%s"}' \
      "$status" "$src" "$tgt" "$path" "$err"
  done
  printf ']}\n'
else
  echo "Reachability Probe -- $TIMESTAMP"
  echo "Orchestrator: $ORCHESTRATOR"
  echo "Mode: $([ "$QUICK_MODE" = true ] && echo 'quick (outbound from $ORCHESTRATOR)' || echo 'full A<->A matrix')"
  echo "Total: $total pairs | PASS: $results_pass | FAIL: $results_fail"
  echo "---"
  for line in "${results_lines[@]}"; do
    IFS='|' read -r status src tgt path err <<< "$line"
    if [ "$status" = "PASS" ]; then
      printf "  \033[32mPASS\033[0m %-12s -> %-12s\n" "$src" "$tgt"
    else
      printf "  \033[31mFAIL\033[0m %-12s -> %-12s  (%s)\n" "$src" "$tgt" "$err"
    fi
  done
fi

if [ $results_fail -gt 0 ]; then exit 1; fi
exit 0
