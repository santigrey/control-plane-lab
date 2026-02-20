from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    # Minimal schema: {"type":"object","properties":{...},"required":[...]}
    schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def list(self) -> Dict[str, ToolSpec]:
        return dict(self._tools)

    def validate_args(self, schema: Dict[str, Any], args: Dict[str, Any]) -> None:
        # Lightweight validation (no jsonschema dependency)
        if schema.get("type") != "object":
            raise ValueError("Tool schema must be type=object")
        required = schema.get("required") or []
        props = schema.get("properties") or {}

        for k in required:
            if k not in args:
                raise ValueError(f"Missing required arg: {k}")

        for k, v in args.items():
            if k not in props:
                raise ValueError(f"Unexpected arg: {k}")
            expected_type = props[k].get("type")
            if expected_type == "string" and not isinstance(v, str):
                raise ValueError(f"Arg '{k}' must be string")
            if expected_type == "integer" and not isinstance(v, int):
                raise ValueError(f"Arg '{k}' must be integer")
            if expected_type == "number" and not isinstance(v, (int, float)):
                raise ValueError(f"Arg '{k}' must be number")
            if expected_type == "boolean" and not isinstance(v, bool):
                raise ValueError(f"Arg '{k}' must be boolean")

    def run(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        self.validate_args(tool.schema, args)
        return tool.handler(args)


# ---- Built-in tools ----

def _ping_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    message = args.get("message", "pong")
    return {"ok": True, "tool": "ping", "echo": message}


def default_registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(
        ToolSpec(
            name="ping",
            description="Connectivity sanity tool: echoes a message.",
            schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": [],
            },
            handler=_ping_handler,
        )
    )
    return r
