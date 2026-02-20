import json
import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("ai_operator")


def _json_log(payload: dict) -> None:
    # One-line JSON logs for journalctl parsing
    logger.info(json.dumps(payload, default=str, separators=(",", ":"), sort_keys=True))


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Adds:
      - request.state.run_id (uuid4)
      - response header X-Run-Id
    Emits:
      - request_start + request_end JSON logs
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        run_id = request.headers.get("X-Run-Id") or str(uuid.uuid4())
        request.state.run_id = run_id

        start = time.time()
        _json_log(
            {
                "event": "request_start",
                "run_id": run_id,
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query,
                "client": request.client.host if request.client else None,
            }
        )

        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            _json_log(
                {
                    "event": "request_error",
                    "run_id": run_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e),
                }
            )
            raise

        duration_ms = int((time.time() - start) * 1000)
        response.headers["X-Run-Id"] = run_id
        _json_log(
            {
                "event": "request_end",
                "run_id": run_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )
        return response
