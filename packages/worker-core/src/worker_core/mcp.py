"""First-party Artel MCP capability scaffolding."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from worker_core.config import effective_project_mcp_path


@dataclass(slots=True)
class MCPServerConfig:
    name: str
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class MCPConfig:
    servers: list[MCPServerConfig] = field(default_factory=list)


class MCPRegistry:
    """Reads Artel/legacy project MCP config into a first-party structure."""

    def load_project_config(self, project_dir: str) -> MCPConfig:
        path = effective_project_mcp_path(project_dir)
        if not path.exists():
            return MCPConfig()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return MCPConfig()
        servers = data.get("servers", []) if isinstance(data, dict) else []
        result: list[MCPServerConfig] = []
        for item in servers:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "") or "").strip()
            if not name:
                continue
            args = item.get("args", [])
            env = item.get("env", {})
            result.append(
                MCPServerConfig(
                    name=name,
                    command=str(item.get("command", "") or "").strip(),
                    args=[str(arg) for arg in args] if isinstance(args, list) else [],
                    env={str(k): str(v) for k, v in env.items()} if isinstance(env, dict) else {},
                )
            )
        return MCPConfig(servers=result)

    def write_project_config(self, project_dir: str, config: MCPConfig) -> Path:
        path = effective_project_mcp_path(project_dir)
        target = Path(project_dir) / ".artel" / path.name if ".worker" in str(path) else path
        target.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "servers": [
                {
                    "name": server.name,
                    "command": server.command,
                    "args": server.args,
                    "env": server.env,
                }
                for server in config.servers
            ]
        }
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target


__all__ = ["MCPConfig", "MCPRegistry", "MCPServerConfig"]
