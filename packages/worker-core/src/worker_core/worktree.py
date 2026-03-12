"""First-party Artel worktree capability scaffolding."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class WorktreeHandle:
    employee_id: str
    project_dir: str
    worktree_path: str
    branch: str
    created: bool = False


class WorktreeManager:
    """Lightweight worktree planner and git-backed executor for Artel employee sessions."""

    def __init__(self, *, base_dir: str | None = None) -> None:
        self._base_dir = Path(base_dir).expanduser() if base_dir else None
        self._handles: dict[str, WorktreeHandle] = {}

    def allocate(self, *, employee_id: str, project_dir: str, task_slug: str = "task") -> WorktreeHandle:
        existing = self._handles.get(employee_id)
        if existing is not None:
            return existing

        project_path = Path(project_dir).resolve(strict=False)
        safe_project = _slugify(project_path.name or "project")
        safe_task = _slugify(task_slug or "task")
        branch = f"artel/{employee_id}/{safe_task}"
        root = self._base_dir or (project_path.parent / ".artel-worktrees")
        worktree_path = root / f"{safe_project}-{employee_id}"
        handle = WorktreeHandle(
            employee_id=employee_id,
            project_dir=str(project_path),
            worktree_path=str(worktree_path),
            branch=branch,
            created=False,
        )
        self._handles[employee_id] = handle
        return handle

    def create(self, *, employee_id: str, project_dir: str, task_slug: str = "task") -> WorktreeHandle:
        handle = self.allocate(
            employee_id=employee_id,
            project_dir=project_dir,
            task_slug=task_slug,
        )
        if handle.created:
            return handle

        Path(handle.worktree_path).parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                "git",
                "-C",
                handle.project_dir,
                "worktree",
                "add",
                "-b",
                handle.branch,
                handle.worktree_path,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "git worktree add failed")
        handle.created = True
        self._handles[employee_id] = handle
        return handle

    def register(self, handle: WorktreeHandle) -> None:
        self._handles[handle.employee_id] = handle

    def get(self, employee_id: str) -> WorktreeHandle | None:
        return self._handles.get(employee_id)

    def list(self) -> list[WorktreeHandle]:
        return list(self._handles.values())

    def remove(self, employee_id: str, *, force: bool = False) -> WorktreeHandle | None:
        handle = self._handles.pop(employee_id, None)
        if handle is None:
            return None
        if handle.created:
            args = [
                "git",
                "-C",
                handle.project_dir,
                "worktree",
                "remove",
            ]
            if force:
                args.append("--force")
            args.append(handle.worktree_path)
            result = subprocess.run(args, capture_output=True, text=True)
            if result.returncode != 0:
                self._handles[employee_id] = handle
                raise RuntimeError(result.stderr.strip() or "git worktree remove failed")
            handle.created = False
        return handle


def _slugify(value: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed or "task"


__all__ = ["WorktreeHandle", "WorktreeManager"]
