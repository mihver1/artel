"""Artel core compatibility package.

Public API::

    from worker_core import AgentSession, AgentEvent, AgentEventType
    from worker_core import load_config, WorkerConfig
    from worker_core import Tool, Extension, HookDispatcher
    from worker_core import SessionStore
    from worker_core import export_html
"""

from worker_core.agent import AgentEvent, AgentEventType, AgentSession
from worker_core.cmux import (
    ArtelWorkspaceBootstrap,
    CmuxSurfaceRecord,
    CmuxWorkspaceRecord,
    bootstrap_artel_workspace,
    ensure_artel_dashboard_surface,
    ensure_artel_orchestrator_surface,
    ensure_artel_workspace,
    reuse_current_surface,
)
from worker_core.config import ArtelConfig, WorkerConfig, load_config
from worker_core.control import (
    ArtelControl,
    RemoteArtelControl,
    RemoteWorkerControl,
    WorkerControl,
    remote_rest_base_url,
)
from worker_core.export import export_html
from worker_core.extensions import Extension, HookDispatcher
from worker_core.mcp import MCPConfig, MCPRegistry, MCPServerConfig
from worker_core.sessions import SessionStore
from worker_core.tools import Tool

__all__ = [
    "AgentEvent",
    "AgentEventType",
    "AgentSession",
    "ArtelConfig",
    "ArtelControl",
    "ArtelWorkspaceBootstrap",
    "CmuxSurfaceRecord",
    "CmuxWorkspaceRecord",
    "Extension",
    "HookDispatcher",
    "MCPConfig",
    "MCPRegistry",
    "MCPServerConfig",
    "bootstrap_artel_workspace",
    "ensure_artel_dashboard_surface",
    "ensure_artel_orchestrator_surface",
    "ensure_artel_workspace",
    "reuse_current_surface",
    "RemoteArtelControl",
    "RemoteWorkerControl",
    "SessionStore",
    "Tool",
    "WorkerConfig",
    "WorkerControl",
    "export_html",
    "load_config",
    "remote_rest_base_url",
]
