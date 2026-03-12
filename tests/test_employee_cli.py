"""CLI tests for Artel employee commands."""

from __future__ import annotations

import sys
from pathlib import Path

from click.testing import CliRunner

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "packages/worker-core/src"))


def test_employee_create_invokes_orchestrator_runtime(monkeypatch, tmp_path) -> None:
    from worker_core import cli as cli_mod
    from worker_core.cmux import CmuxPreflightResult
    from worker_core.orchestration import EmployeeRecord

    captured: dict[str, object] = {}

    class FakeRuntime:
        def create_employee_session_sync(self, **kwargs):
            captured.update(kwargs)
            return EmployeeRecord(
                employee_id=str(kwargs["employee_id"]),
                display_name=str(kwargs["display_name"]),
                assigned_task=str(kwargs["assigned_task"]),
                status="ready",
                cmux_surface="surface-123",
                project_path=str(kwargs["project_dir"]),
                worktree_path=str(tmp_path / ".artel-worktrees" / str(kwargs["employee_id"])),
                branch=f"artel/{kwargs['employee_id']}/task",
                latest_updates=[f"Assigned: {kwargs['assigned_task']}"],
            )

    monkeypatch.setattr("worker_core.cmux.preflight_cmux_management", lambda: CmuxPreflightResult(ok=True))
    monkeypatch.setattr("worker_core.orchestration.OrchestratorRuntime", FakeRuntime)

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.cli,
        [
            "employee",
            "create",
            "--name",
            "Alice Smith",
            "--task",
            "Review rendering cleanup",
            "--project-dir",
            str(tmp_path),
            "--workspace",
            "artel-main",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "employee_id": "alice-smith",
        "display_name": "Alice Smith",
        "project_dir": str(tmp_path.resolve()),
        "assigned_task": "Review rendering cleanup",
        "workspace": "artel-main",
        "command": "artel",
        "initial_prompt": "",
        "create_worktree": True,
    }
    assert "Employee created: alice-smith" in result.output
    assert "Surface: surface-123" in result.output


def test_employee_create_supports_planned_worktree_only(monkeypatch, tmp_path) -> None:
    from worker_core import cli as cli_mod
    from worker_core.cmux import CmuxPreflightResult
    from worker_core.orchestration import EmployeeRecord

    captured: dict[str, object] = {}

    class FakeRuntime:
        def create_employee_session_sync(self, **kwargs):
            captured.update(kwargs)
            return EmployeeRecord(
                employee_id="emp-42",
                display_name="Planner",
                assigned_task="Plan next slice",
                status="ready",
                cmux_surface="surface-456",
                project_path=str(kwargs["project_dir"]),
                worktree_path=str(tmp_path / ".artel-worktrees" / "emp-42"),
                branch="artel/emp-42/plan-next-slice",
            )

    monkeypatch.setattr("worker_core.cmux.preflight_cmux_management", lambda: CmuxPreflightResult(ok=True))
    monkeypatch.setattr("worker_core.orchestration.OrchestratorRuntime", FakeRuntime)

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.cli,
        [
            "employee",
            "create",
            "--id",
            "emp-42",
            "--name",
            "Planner",
            "--task",
            "Plan next slice",
            "--project-dir",
            str(tmp_path),
            "--no-create-worktree",
        ],
    )

    assert result.exit_code == 0
    assert captured["employee_id"] == "emp-42"
    assert captured["initial_prompt"] == ""
    assert captured["create_worktree"] is False
    assert "Employee created: emp-42" in result.output
    assert "Surface: surface-456" in result.output


def test_employee_create_reports_runtime_errors(monkeypatch) -> None:
    from worker_core import cli as cli_mod

    from worker_core.cmux import CmuxPreflightResult

    class FakeRuntime:
        def create_employee_session_sync(self, **kwargs):
            raise RuntimeError("git worktree add failed")

    monkeypatch.setattr("worker_core.cmux.preflight_cmux_management", lambda: CmuxPreflightResult(ok=True))
    monkeypatch.setattr("worker_core.orchestration.OrchestratorRuntime", FakeRuntime)

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.cli,
        ["employee", "create", "--name", "Alice", "--task", "Fail please"],
    )

    assert result.exit_code != 0
    assert "git worktree add failed" in result.output


def test_employee_create_fails_when_no_cmux_surface_was_created(monkeypatch, tmp_path) -> None:
    from worker_core import cli as cli_mod
    from worker_core.cmux import CmuxPreflightResult
    from worker_core.orchestration import EmployeeRecord

    class FakeRuntime:
        def create_employee_session_sync(self, **kwargs):
            return EmployeeRecord(
                employee_id="emp-no-surface",
                display_name="No Surface",
                assigned_task="Validate flow",
                status="queued",
                cmux_surface="",
                project_path=str(kwargs["project_dir"]),
                worktree_path=str(tmp_path / ".artel-worktrees" / "emp-no-surface"),
                branch="artel/emp-no-surface/validate-flow",
            )

    monkeypatch.setattr("worker_core.cmux.preflight_cmux_management", lambda: CmuxPreflightResult(ok=True))
    monkeypatch.setattr("worker_core.orchestration.OrchestratorRuntime", FakeRuntime)

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.cli,
        [
            "employee",
            "create",
            "--name",
            "No Surface",
            "--task",
            "Validate flow",
            "--project-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "no cmux surface" in result.output.lower() or "failed to create or locate a cmux surface" in result.output.lower()


def test_employee_create_fails_fast_when_cmux_management_is_unavailable(monkeypatch) -> None:
    from worker_core import cli as cli_mod
    from worker_core.cmux import CmuxPreflightResult

    monkeypatch.setattr(
        "worker_core.cmux.preflight_cmux_management",
        lambda: CmuxPreflightResult(
            ok=False,
            code="socket_unreachable",
            summary="Artel found the cmux socket path, but could not reach the cmux daemon for employee management.",
            details=["Socket: /tmp/cmux.sock"],
            guidance=[
                "Restart or reattach cmux so the socket accepts connections.",
                "CMUX_WORKSPACE_ID is optional for employee creation; cmux daemon reachability is not.",
            ],
        ),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.cli,
        ["employee", "create", "--name", "Alice", "--task", "Review backlog"],
    )

    assert result.exit_code != 0
    assert "could not reach the cmux daemon" in result.output.lower()
    assert "cmux_workspace_id is optional" in result.output.lower()


def test_employee_create_passes_initial_prompt_to_runtime(monkeypatch, tmp_path) -> None:
    from worker_core import cli as cli_mod
    from worker_core.cmux import CmuxPreflightResult
    from worker_core.orchestration import EmployeeRecord

    captured: dict[str, object] = {}

    class FakeRuntime:
        def create_employee_session_sync(self, **kwargs):
            captured.update(kwargs)
            return EmployeeRecord(
                employee_id="alice-smith",
                display_name="Alice Smith",
                assigned_task="Validate backlog next steps",
                status="ready",
                cmux_surface="surface-123",
                project_path=str(kwargs["project_dir"]),
                worktree_path=str(tmp_path / ".artel-worktrees" / "alice-smith"),
                branch="artel/alice-smith/validate-backlog-next-steps",
            )

    monkeypatch.setattr("worker_core.cmux.preflight_cmux_management", lambda: CmuxPreflightResult(ok=True))
    monkeypatch.setattr("worker_core.orchestration.OrchestratorRuntime", FakeRuntime)

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.cli,
        [
            "employee",
            "create",
            "--name",
            "Alice Smith",
            "--task",
            "Validate backlog next steps",
            "--project-dir",
            str(tmp_path),
            "--prompt",
            "Please inspect rendering cleanup",
        ],
    )

    assert result.exit_code == 0
    assert captured["initial_prompt"] == "Please inspect rendering cleanup"
