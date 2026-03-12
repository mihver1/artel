"""First-party Artel orchestration capability scaffolding."""

from __future__ import annotations

import asyncio
import shlex
from dataclasses import asdict, dataclass, field
from typing import Any, Awaitable, Callable

from worker_core import cmux
from worker_core.worktree import WorktreeHandle, WorktreeManager

SurfaceCreator = Callable[..., Awaitable[str]]
WorkspaceEnsurer = Callable[[str], Awaitable[cmux.CmuxWorkspaceRecord | None]]
SurfaceEnsurer = Callable[..., Awaitable[cmux.CmuxSurfaceRecord | None]]


@dataclass(slots=True)
class EmployeeRecord:
    employee_id: str
    display_name: str
    assigned_task: str = ""
    status: str = "idle"
    cmux_surface: str = ""
    project_path: str = ""
    worktree_path: str = ""
    branch: str = ""
    latest_updates: list[str] = field(default_factory=list)


class EmployeeRegistry:
    """Minimal registry backing future dashboard/orchestrator surfaces."""

    def __init__(self) -> None:
        self._records: dict[str, EmployeeRecord] = {}

    def add(self, record: EmployeeRecord) -> EmployeeRecord:
        self._records[record.employee_id] = record
        return record

    def get(self, employee_id: str) -> EmployeeRecord | None:
        return self._records.get(employee_id)

    def list(self) -> list[EmployeeRecord]:
        return list(self._records.values())

    def remove(self, employee_id: str) -> EmployeeRecord | None:
        return self._records.pop(employee_id, None)

    def update_status(self, employee_id: str, status: str, *, update: str = "") -> EmployeeRecord | None:
        record = self._records.get(employee_id)
        if record is None:
            return None
        record.status = status.strip() or record.status
        if update.strip():
            record.latest_updates.append(update.strip())
        return record


class OrchestratorRuntime:
    """Scaffold for Artel employee lifecycle orchestration."""

    def __init__(
        self,
        *,
        worktrees: WorktreeManager | None = None,
        employees: EmployeeRegistry | None = None,
        surface_creator: SurfaceCreator | None = None,
        workspace_ensurer: WorkspaceEnsurer | None = None,
        surface_ensurer: SurfaceEnsurer | None = None,
    ) -> None:
        self.worktrees = worktrees or WorktreeManager()
        self.employees = employees or EmployeeRegistry()
        self._surface_creator = surface_creator or cmux.surface_create
        self._workspace_ensurer = workspace_ensurer or cmux.ensure_workspace
        self._surface_ensurer = surface_ensurer or cmux.ensure_surface

    def create_employee(
        self,
        *,
        employee_id: str,
        display_name: str,
        project_dir: str,
        assigned_task: str,
        cmux_surface: str = "",
        create_worktree: bool = False,
    ) -> EmployeeRecord:
        handle = (
            self.worktrees.create(
                employee_id=employee_id,
                project_dir=project_dir,
                task_slug=assigned_task,
            )
            if create_worktree
            else self.worktrees.allocate(
                employee_id=employee_id,
                project_dir=project_dir,
                task_slug=assigned_task,
            )
        )
        record = EmployeeRecord(
            employee_id=employee_id,
            display_name=display_name,
            assigned_task=assigned_task,
            status="queued",
            cmux_surface=cmux_surface,
            project_path=handle.project_dir,
            worktree_path=handle.worktree_path,
            branch=handle.branch,
        )
        return self.employees.add(record)

    async def create_employee_session(
        self,
        *,
        employee_id: str,
        display_name: str,
        project_dir: str,
        assigned_task: str,
        workspace: str = "",
        command: str = "artel",
        create_worktree: bool = True,
        initial_prompt: str = "",
    ) -> EmployeeRecord:
        record = self.create_employee(
            employee_id=employee_id,
            display_name=display_name,
            project_dir=project_dir,
            assigned_task=assigned_task,
            create_worktree=create_worktree,
        )
        surface_title = f"employee:{display_name}"
        launch_command = command.strip() or "artel"
        normalized_prompt = initial_prompt.strip()
        if normalized_prompt:
            quoted_prompt = shlex.quote(normalized_prompt)
            launch_command = f"{launch_command} -p {quoted_prompt}"
        resolved_workspace = workspace.strip()
        if resolved_workspace:
            workspace_record = await self._workspace_ensurer(resolved_workspace)
            if workspace_record is not None:
                resolved_workspace = workspace_record.id or workspace_record.name or resolved_workspace

        surface_record = await self._surface_ensurer(
            title=surface_title,
            command=launch_command,
            cwd=record.worktree_path or record.project_path,
            workspace=resolved_workspace,
        )
        if surface_record is not None:
            record.cmux_surface = surface_record.id.strip()
        elif self._surface_creator is not None:
            surface_id = await self._surface_creator(
                title=surface_title,
                command=launch_command,
                cwd=record.worktree_path or record.project_path,
                workspace=resolved_workspace,
            )
            if surface_id:
                record.cmux_surface = surface_id.strip()
        if not record.cmux_surface:
            raise RuntimeError(
                "Failed to create or locate a cmux surface for the employee session. "
                "Make sure the cmux binary is installed, the daemon is reachable, and the target workspace is valid."
            )
        record.status = "ready"
        record.latest_updates.append(f"Assigned: {assigned_task}")
        if normalized_prompt:
            record.latest_updates.append("Launch mode: one-shot prompt")
        else:
            record.latest_updates.append("Launch mode: interactive Artel")
        return record

    def create_employee_session_sync(self, **kwargs: str | bool) -> EmployeeRecord:
        return asyncio.run(self.create_employee_session(**kwargs))

    def register_surface(self, employee_id: str, surface_id: str) -> EmployeeRecord | None:
        record = self.employees.get(employee_id)
        if record is None:
            return None
        record.cmux_surface = surface_id.strip()
        return record

    def attach_worktree(self, employee_id: str, handle: WorktreeHandle) -> EmployeeRecord | None:
        self.worktrees.register(handle)
        record = self.employees.get(employee_id)
        if record is None:
            return None
        record.project_path = handle.project_dir
        record.worktree_path = handle.worktree_path
        record.branch = handle.branch
        return record

    def update_employee(self, employee_id: str, *, status: str, update: str = "") -> EmployeeRecord | None:
        return self.employees.update_status(employee_id, status, update=update)

    def remove_employee(self, employee_id: str, *, force: bool = False) -> EmployeeRecord | None:
        self.worktrees.remove(employee_id, force=force)
        return self.employees.remove(employee_id)

    def serialize(self) -> list[dict[str, Any]]:
        return [asdict(record) for record in self.employees.list()]


__all__ = ["EmployeeRecord", "EmployeeRegistry", "OrchestratorRuntime"]
