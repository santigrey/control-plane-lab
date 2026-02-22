#!/usr/bin/env bash
set -euo pipefail

REPO="/home/jes/control-plane/orchestrator"
PY="$REPO/.venv/bin/python"
export PYTHONPATH="$REPO"

echo "[gate6] repo=$REPO"
echo "[gate6] python=$PY"
echo "[gate6] PYTHONPATH=$PYTHONPATH"

cd "$REPO"

# compile quick health check
$PY -m py_compile ai_operator/repo/patch_apply.py
$PY -m py_compile ai_operator/worker/runner.py
echo "[gate6] py_compile OK"

# REQUIRE CLEAN (no untracked, no modified)
if [[ -n "$(git status --porcelain)" ]]; then
  echo "[gate6] ERROR: repo not clean (require_clean=true)."
  git status --porcelain
  exit 1
fi

# restart worker (needs sudo)
sudo systemctl restart aiop-worker
echo "[gate6] worker restarted"

# load env so dev enqueuers work
set -a
source "$REPO/.env"
set +a

echo "[gate6] enqueue tool demo tasks..."
$PY ai_operator/dev/enqueue_demo.py

echo "[gate6] enqueue artifact demo tasks..."
$PY ai_operator/dev/enqueue_artifact_demo.py

# create a demo patch in *repo-root* artifacts/patches
PATCH_PATH="$($PY - <<'PY'
import os
from datetime import datetime, timezone

repo = "/home/jes/control-plane/orchestrator"
ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out_dir = os.path.join(repo, "artifacts", "patches")
os.makedirs(out_dir, exist_ok=True)

path = os.path.join(out_dir, f"{ts}_gate6_demo.patch")
patch = """diff --git a/artifacts/gate6_demo.txt b/artifacts/gate6_demo.txt
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/artifacts/gate6_demo.txt
@@ -0,0 +1 @@
+gate6_demo
"""
with open(path, "w", encoding="utf-8") as f:
    f.write(patch)

print(path)
PY
)"
echo "[gate6] PATCH_PATH=$PATCH_PATH"

# enqueue patch.apply task
TASK_ID="$(
  docker exec -i control-postgres psql -U admin -d controlplane -Atq -c \
  "INSERT INTO tasks (type, payload, priority, max_attempts)
   VALUES (
     'patch.apply',
     jsonb_build_object(
       'repo_path','$REPO',
       'patch_path','$PATCH_PATH',
       'name','gate6_demo',
       'purpose','phase2_gate6_patch_apply',
       'require_clean', true,
       'check_only', false
     ),
     10,
     3
   )
   RETURNING id;" | head -n 1 | tr -d '\r'
)"
echo "[gate6] patch.apply TASK_ID=$TASK_ID"

echo "[gate6] waiting for patch.apply to finish..."
for i in $(seq 1 12); do
  row="$(docker exec -i control-postgres psql -U admin -d controlplane -Atq -c \
    "SELECT status||'|'||attempts||'|'||coalesce(left(last_error,120),'') FROM tasks WHERE id='${TASK_ID}'::uuid;" \
    | head -n 1 | tr -d '\r')"
  status="${row%%|*}"
  rest="${row#*|}"
  attempts="${rest%%|*}"
  err="${rest#*|}"
  [[ -z "$err" ]] && err="<none>"
  echo "[gate6] poll $i status=$status attempts=$attempts err=$err"
  [[ "$status" == "succeeded" || "$status" == "failed" ]] && break
  sleep 1
done

echo
echo "==================== GATE6 VERIFY ===================="
docker exec -i control-postgres psql -U admin -d controlplane < "$REPO/ai_operator/dev/gate6_verify.sql" | tail -n 80 || true

echo
echo "[gate6] artifacts/docs:"
ls -lt "$REPO/artifacts/docs" | head -n 10 || true
echo
echo "[gate6] artifacts/patches:"
ls -lt "$REPO/artifacts/patches" | head -n 10 || true

echo
echo "[gate6] git status (should still be clean):"
git status --porcelain || true
echo "======================================================"
echo "[gate6] done."
