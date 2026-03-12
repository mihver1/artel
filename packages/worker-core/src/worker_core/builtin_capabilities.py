"""Built-in Artel capability registry.

These capabilities are bundled with the product and should load without
external extension installation while preserving a conceptual extension-like
registration boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from worker_core.mcp import MCPRegistry
from worker_core.orchestration import OrchestratorRuntime
from worker_core.worktree import WorktreeManager


@dataclass(slots=True)
class BuiltinCapability:
    name: str
    kind: str
    bundled: bool = True
    removable: bool = False
    instance: Any | None = None


def load_builtin_capabilities(*, project_dir: str = "") -> dict[str, BuiltinCapability]:
    worktree = BuiltinCapability(
        name="artel-worktree",
        kind="worktree",
        instance=WorktreeManager(),
    )
    orchestration = BuiltinCapability(
        name="artel-orchestration",
        kind="orchestration",
        instance=OrchestratorRuntime(worktrees=worktree.instance),
    )
    mcp = BuiltinCapability(
        name="artel-mcp",
        kind="mcp",
        instance=MCPRegistry(),
    )
    return {
        worktree.name: worktree,
        orchestration.name: orchestration,
        mcp.name: mcp,
    }


def builtin_capability_names() -> list[str]:
    return list(load_builtin_capabilities().keys())


__all__ = ["BuiltinCapability", "builtin_capability_names", "load_builtin_capabilities"]
