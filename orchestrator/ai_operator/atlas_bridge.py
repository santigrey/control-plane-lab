"""Atlas MCP client bridge for Alexandra orchestrator.

This module is Alexandra's gateway to atlas-mcp tools at
`https://sloan2.tail1216a3.ts.net:8443/mcp`. Calls flow:

    Alexandra :8000  ->  AtlasBridge  ->  mcp.ClientSession  ->  nginx :8443
         ->  uvicorn :8001  ->  atlas.mcp_server

Path A integration per Atlas v0.2 Cycle 2A ratification (commit `c3ede72`).

v0.2.0 tool subset (4 tools):
- atlas_memory_query     -- semantic search over atlas.memory
- atlas_memory_upsert    -- write to atlas.memory; server embeds
- atlas_events_search    -- audit log query
- atlas_inference_history -- token usage stats

6 tools deferred to v0.2.1+ (atlas_tasks_*).

Decouples Alexandra from Atlas internals: server-side ACL is the authoritative
authorization boundary; Alexandra inherits this discipline by treating atlas-mcp
as an external API contract.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

log = logging.getLogger(__name__)

ATLAS_MCP_URL = "https://sloan2.tail1216a3.ts.net:8443/mcp"
ATLAS_MCP_HEADERS = {"MCP-Protocol-Version": "2025-03-26"}

# v0.2.0 tool subset (per Cycle 2A Ask 2 ratification)
ALLOWED_TOOLS = frozenset(
    {
        "atlas_memory_query",
        "atlas_memory_upsert",
        "atlas_events_search",
        "atlas_inference_history",
    }
)

DEFAULT_TIMEOUT = 30.0


class AtlasBridgeError(Exception):
    """Wraps atlas-mcp transport / call failures for caller-friendly handling."""


class AtlasBridge:
    """Async context-manager wrapper around atlas-mcp ClientSession.

    Usage:
        async with AtlasBridge() as bridge:
            result = await bridge.call(
                "atlas_memory_query",
                {"query_text": "...", "top_k": 5},
            )

    Path X argshape (Pydantic-wrapped) per Cycle 1H/1I ratification: arguments are
    automatically wrapped in `{"params": {...}}` before send.
    """

    def __init__(
        self,
        url: str = ATLAS_MCP_URL,
        headers: Optional[dict[str, str]] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.url = url
        self.headers = dict(headers) if headers is not None else dict(ATLAS_MCP_HEADERS)
        self.timeout = timeout
        self._client_cm = None
        self._session_cm = None
        self._session: Optional[ClientSession] = None

    async def __aenter__(self) -> "AtlasBridge":
        try:
            self._client_cm = streamablehttp_client(self.url, headers=self.headers)
            r, w, _close = await self._client_cm.__aenter__()
            self._session_cm = ClientSession(r, w)
            self._session = await self._session_cm.__aenter__()
            await asyncio.wait_for(self._session.initialize(), timeout=self.timeout)
            return self
        except Exception as e:
            log.exception("AtlasBridge initialization failed")
            # Best-effort cleanup of any partially-entered context
            try:
                if self._session_cm is not None:
                    await self._session_cm.__aexit__(type(e), e, None)
            except Exception:
                pass
            try:
                if self._client_cm is not None:
                    await self._client_cm.__aexit__(type(e), e, None)
            except Exception:
                pass
            self._session = None
            self._session_cm = None
            self._client_cm = None
            raise AtlasBridgeError(
                f"atlas-mcp connection failed: {type(e).__name__}: {e}"
            ) from e

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if self._session_cm is not None:
                await self._session_cm.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            try:
                if self._client_cm is not None:
                    await self._client_cm.__aexit__(exc_type, exc_val, exc_tb)
            finally:
                self._session = None
                self._session_cm = None
                self._client_cm = None

    async def call(self, tool_name: str, arguments: dict) -> Any:
        """Invoke an atlas-mcp tool.

        Raises AtlasBridgeError on transport / call failure or tool denylist.

        Arguments are auto-wrapped in `{"params": {...}}` per Path X argshape.
        """
        if tool_name not in ALLOWED_TOOLS:
            raise AtlasBridgeError(
                f"tool '{tool_name}' not in v0.2.0 allowlist {sorted(ALLOWED_TOOLS)}"
            )
        if self._session is None:
            raise AtlasBridgeError(
                "AtlasBridge not initialized; use as async context manager"
            )
        wrapped_args = {"params": arguments}
        try:
            result = await asyncio.wait_for(
                self._session.call_tool(tool_name, wrapped_args),
                timeout=self.timeout,
            )
            return result
        except asyncio.TimeoutError as e:
            raise AtlasBridgeError(
                f"atlas-mcp call timeout after {self.timeout}s: {tool_name}"
            ) from e
        except Exception as e:
            log.exception("AtlasBridge call failed")
            raise AtlasBridgeError(
                f"atlas-mcp call failed: {tool_name}: {type(e).__name__}: {e}"
            ) from e

    async def list_tools(self) -> list[str]:
        if self._session is None:
            raise AtlasBridgeError("AtlasBridge not initialized")
        tools = await self._session.list_tools()
        return sorted(t.name for t in tools.tools)
