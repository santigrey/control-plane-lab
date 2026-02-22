#!/usr/bin/env bash
set -euo pipefail

REPO="/home/jes/control-plane/orchestrator"
DB_CONTAINER="control-postgres"

cd "$REPO"

echo "[gate6] repo=$REPO"

# --- load env (DATABASE_URL etc.) ---
set -a
source "$REPO/.env"
set +a

# --- python env ---
PY="$REPO/.venv/bin/python"
export PYTHONPATH="$REPO"
export PYTHONUNBUFFERED=1

echo "[gate6] python=$PY"
echo "[gate6] PYTHONPATH=$PYTHONPATH"

# --- sanity compile ---
$PY -m py_compile ai_operator/worker/runner.py
$PY -m py_compile ai_operator/repo/patch_apply.py
echo "[gate6] py_compile OK"

# --- restart worker ---
sudo systemctl restart aiop-worker
echo "[gate6] worker restarted"

# --- enforce clean repo BEFORE patch.apply ---
dirty="$(git status --porcelain || true)"
if [[ -n "$dirty" ]]; then
  echo "[gate6] ERROR: repo not clean (require_clean=true). Fix with commit/stash or ignore rules."
  echo "$dirty"
  exit 2
fi
echo "[gate6] repo clean OK"

# --- enqueue demo tool tasks (ping -> sleep -> ping) ---
echo "[gate6] enqueue tool demo tasks..."
$PY ai_operator/dev/enqueue_demo.py

# --- enqueue artifact demo tasks ---
if [[ -f "$REPO/ai_operator/dev/enqueue_artifact_demo.py" ]]; then
  echo "[gate6] enqueue artifact demo tasks..."
  $PY ai_operator/dev/enqueue_artifact_demo.py
else
  echo "[gate6] WARN: ai_operator/dev/enqueue_artifact_demo.py not found, skipping"
fi

# --- create patch OUTSIDE repo to keep git clean ---
TS="$(date -u +%Y%m%dT%H%M%SZ)"
PATCH_PATH="/tmp/${TS}_gate6_demo.patch"

cat > "$PATCH_PATH" <<'PATCH'
diff --git a/artifacts/gate6_demo.txt b/artifacts/gate6_demo.txt
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/artifacts/gate6_demo.txt
@@ -0,0 +1 @@
+gate6_demo
PATCH

echo "[gate6] PATCH_PATH=$PATCH_PATH (outside repo)"

# --- enqueue patch.apply ---
TASK_ID="$(
  docker exec -i "$DB_CONTAINER" psql -U admin -d controlplane -Atq -c "
    INSERT INTO tasks (type, payload, priority, max_attempts)
    VALUES (
      'patch.apply',
      jsonb_build_object(
        'repo_path', '$REPO',
        'patch_path', '$PATCH_PATH',
        'name', 'gate6_demo',
        'purpose', 'phase2_gate6_patch_apply',
        'require_clean', true,
        'check_only', false
      ),
      10,
      3
    )
    RETURNING id;
  " | head -n 1 | tr -d '\r'
)"
echo "[gate6] patch.apply TASK_ID=$TASK_ID"

# --- wait up to ~25s ---
echo "[gate6] waiting for patch.apply to finish..."
for i in $(seq 1 25); do
  row="$(docker exec -i "$DB_CONTAINER" psql -U admin -d controlplane -Atq -c \
    "SELECT status||'|'||attempts||'|'||coalesce(left(last_error,120),'') FROM tasks WHERE id='${TASK_ID}'::uuid;" \
    | tr -d '\r' || true)"

  status="${row%%|*}"
  rest="${row#*|}"
  attempts="${rest%%|*}"
  err="${rest#*|}"

  echo "[gate6] poll $i status=$status attempts=$attempts err=${err:-<none>}"

  if [[ "$status" == "succeeded" || "$status" == "failed" ]]; then
    break
  fi
  sleep 1
done

echo
echo "==================== GATE6 VERIFY ===================="
docker exec -i "$DB_CONTAINER" psql -U admin -d controlplane -c \
"SELECT id, type, status, attempts, left(coalesce(last_error,''),160) AS err160
 FROM tasks
 WHERE id='${TASK_ID}'::uuid;"

echo
echo "[gate6] artifacts/docs:"
ls -lt "$REPO/artifacts/docs" 2>/dev/null | head -n 10 || true

echo
echo "[gate6] artifacts/patches:"
ls -lt "$REPO/artifacts/patches" 2>/dev/null | head -n 10 || true

echo
echo "[gate6] git status (should still be clean):"
git status --porcelain || true

echo "======================================================"
echo "[gate6] done."
