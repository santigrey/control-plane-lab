"""pytest conftest -- sys.path shim so tests can import ai_operator.* without install."""
import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parent.parent / "orchestrator"
if str(_ORCH) not in sys.path:
    sys.path.insert(0, str(_ORCH))
