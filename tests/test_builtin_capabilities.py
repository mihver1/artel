"""Tests for first-party Artel capability scaffolding."""

from __future__ import annotations

import json


def test_load_builtin_capabilities_returns_bundled_capabilities() -> None:
    from worker_core.builtin_capabilities import load_builtin_capabilities
    from worker_core.mcp import MCPRegistry
    from worker_core.orchestration import OrchestratorRuntime
    from worker_core.worktree import WorktreeManager

    capabilities = load_builtin_capabilities(project_dir="/tmp/project")

    assert sorted(capabilities) == [
        "artel-mcp",
        "artel-orchestration",
        "artel-worktree",
    ]
    assert isinstance(capabilities["artel-worktree"].instance, WorktreeManager)
    assert isinstance(capabilities["artel-orchestration"].instance, OrchestratorRuntime)
    assert isinstance(capabilities["artel-mcp"].instance, MCPRegistry)
    assert capabilities["artel-worktree"].bundled is True
    assert capabilities["artel-worktree"].removable is False


def test_worktree_manager_allocates_stable_handle(tmp_path) -> None:
    from worker_core.worktree import WorktreeManager

    manager = WorktreeManager(base_dir=str(tmp_path / "worktrees"))

    first = manager.allocate(
        employee_id="emp-1",
        project_dir=str(tmp_path / "project"),
        task_slug="Implement dashboard",
    )
    second = manager.allocate(
        employee_id="emp-1",
        project_dir=str(tmp_path / "project"),
        task_slug="ignored",
    )

    assert first is second
    assert first.branch == "artel/emp-1/implement-dashboard"
    assert first.worktree_path.endswith("project-emp-1")
    assert manager.get("emp-1") == first


def test_worktree_manager_create_and_remove_use_git_worktree_commands(monkeypatch, tmp_path) -> None:
    from worker_core.worktree import WorktreeManager

    calls: list[list[str]] = []

    class _Result:
        def __init__(self, returncode=0, stderr=""):
            self.returncode = returncode
            self.stderr = stderr

    def fake_run(args, capture_output, text):
        calls.append(list(args))
        return _Result()

    monkeypatch.setattr("subprocess.run", fake_run)

    manager = WorktreeManager(base_dir=str(tmp_path / "worktrees"))
    handle = manager.create(
        employee_id="emp-1",
        project_dir=str(tmp_path / "project"),
        task_slug="Implement dashboard",
    )

    assert handle.created is True
    assert calls[0][:5] == [
        "git",
        "-C",
        str((tmp_path / "project").resolve()),
        "worktree",
        "add",
    ]

    removed = manager.remove("emp-1")
    assert removed is not None
    assert calls[1][:5] == [
        "git",
        "-C",
        str((tmp_path / "project").resolve()),
        "worktree",
        "remove",
    ]


def test_orchestrator_runtime_creates_updates_and_removes_employee(tmp_path) -> None:
    from worker_core.orchestration import OrchestratorRuntime

    runtime = OrchestratorRuntime()
    employee = runtime.create_employee(
        employee_id="emp-1",
        display_name="Alice",
        project_dir=str(tmp_path / "project"),
        assigned_task="Build dashboard",
        cmux_surface="surface-1",
    )

    assert employee.status == "queued"
    assert employee.cmux_surface == "surface-1"
    assert employee.branch == "artel/emp-1/build-dashboard"

    updated = runtime.update_employee("emp-1", status="running", update="Started work")
    assert updated is not None
    assert updated.status == "running"
    assert updated.latest_updates == ["Started work"]

    removed = runtime.remove_employee("emp-1")
    assert removed is not None
    assert runtime.employees.get("emp-1") is None
    assert runtime.worktrees.get("emp-1") is None


def test_orchestrator_runtime_creates_employee_session_with_surface(monkeypatch, tmp_path) -> None:
    from worker_core.orchestration import OrchestratorRuntime
    from worker_core.worktree import WorktreeHandle

    created = []

    class _Worktrees:
        def create(self, *, employee_id: str, project_dir: str, task_slug: str):
            created.append((employee_id, project_dir, task_slug))
            return WorktreeHandle(
                employee_id=employee_id,
                project_dir=project_dir,
                worktree_path=str(tmp_path / ".artel-worktrees" / employee_id),
                branch=f"artel/{employee_id}/build-dashboard",
                created=True,
            )

        def allocate(self, *, employee_id: str, project_dir: str, task_slug: str):
            raise AssertionError("allocate should not be called when create_worktree=True")

        def remove(self, employee_id: str, *, force: bool = False):
            return None

        def register(self, handle):
            return None

        def get(self, employee_id: str):
            return None

    async def fake_workspace_ensurer(name: str):
        assert name == "artel-main"
        from worker_core.cmux import CmuxWorkspaceRecord

        return CmuxWorkspaceRecord(id="ws-123", name="artel-main")

    async def fake_surface_ensurer(**kwargs):
        assert kwargs["title"] == "employee:Alice"
        assert kwargs["command"] == "artel"
        assert kwargs["workspace"] == "ws-123"
        assert kwargs["cwd"].endswith("/.artel-worktrees/emp-1")
        from worker_core.cmux import CmuxSurfaceRecord

        return CmuxSurfaceRecord(id="surface-123", title="employee:Alice", workspace="ws-123")

    async def fake_surface_create(**kwargs):
        raise AssertionError("surface_create fallback should not be called when ensure_surface succeeds")

    runtime = OrchestratorRuntime(
        worktrees=_Worktrees(),
        surface_creator=fake_surface_create,
        workspace_ensurer=fake_workspace_ensurer,
        surface_ensurer=fake_surface_ensurer,
    )
    employee = runtime.create_employee_session_sync(
        employee_id="emp-1",
        display_name="Alice",
        project_dir=str(tmp_path / "project"),
        assigned_task="Build dashboard",
        workspace="artel-main",
        command="artel",
        initial_prompt="",
        create_worktree=True,
    )

    assert created == [("emp-1", str(tmp_path / "project"), "Build dashboard")]
    assert employee.cmux_surface == "surface-123"
    assert employee.status == "ready"
    assert employee.latest_updates == ["Assigned: Build dashboard", "Launch mode: interactive Artel"]


def test_orchestrator_runtime_falls_back_to_surface_create_when_ensure_surface_returns_none(tmp_path) -> None:
    from worker_core.orchestration import OrchestratorRuntime
    from worker_core.worktree import WorktreeHandle

    class _Worktrees:
        def create(self, *, employee_id: str, project_dir: str, task_slug: str):
            return WorktreeHandle(
                employee_id=employee_id,
                project_dir=project_dir,
                worktree_path=str(tmp_path / ".artel-worktrees" / employee_id),
                branch=f"artel/{employee_id}/build-dashboard",
                created=True,
            )

        def allocate(self, *, employee_id: str, project_dir: str, task_slug: str):
            raise AssertionError("allocate should not be called when create_worktree=True")

        def remove(self, employee_id: str, *, force: bool = False):
            return None

        def register(self, handle):
            return None

        def get(self, employee_id: str):
            return None

    async def fake_workspace_ensurer(name: str):
        assert name == "artel-main"
        from worker_core.cmux import CmuxWorkspaceRecord

        return CmuxWorkspaceRecord(id="ws-123", name="artel-main")

    async def fake_surface_ensurer(**kwargs):
        assert kwargs["workspace"] == "ws-123"
        return None

    async def fake_surface_create(**kwargs):
        assert kwargs["title"] == "employee:Alice"
        assert kwargs["command"] == "artel -p 'Start by checking dashboard state'"
        assert kwargs["workspace"] == "ws-123"
        return "surface-456"

    runtime = OrchestratorRuntime(
        worktrees=_Worktrees(),
        surface_creator=fake_surface_create,
        workspace_ensurer=fake_workspace_ensurer,
        surface_ensurer=fake_surface_ensurer,
    )
    employee = runtime.create_employee_session_sync(
        employee_id="emp-1",
        display_name="Alice",
        project_dir=str(tmp_path / "project"),
        assigned_task="Build dashboard",
        workspace="artel-main",
        command="artel",
        initial_prompt="Start by checking dashboard state",
        create_worktree=True,
    )

    assert employee.cmux_surface == "surface-456"
    assert employee.status == "ready"
    assert employee.latest_updates == ["Assigned: Build dashboard", "Launch mode: one-shot prompt"]


def test_mcp_registry_reads_and_writes_artel_project_config(tmp_path) -> None:
    from worker_core.mcp import MCPConfig, MCPRegistry, MCPServerConfig

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    artel_dir = project_dir / ".artel"
    artel_dir.mkdir()
    (artel_dir / "mcp.json").write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "name": "filesystem",
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                        "env": {"ROOT": "/srv/project"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    registry = MCPRegistry()
    loaded = registry.load_project_config(str(project_dir))

    assert len(loaded.servers) == 1
    assert loaded.servers[0].name == "filesystem"
    assert loaded.servers[0].command == "npx"
    assert loaded.servers[0].env["ROOT"] == "/srv/project"

    written = registry.write_project_config(
        str(project_dir),
        MCPConfig(servers=[MCPServerConfig(name="browser", command="uvx")]),
    )
    saved = json.loads(written.read_text(encoding="utf-8"))

    assert written == artel_dir / "mcp.json"
    assert saved["servers"][0]["name"] == "browser"
    assert saved["servers"][0]["command"] == "uvx"


def test_runtime_bootstrap_binds_builtin_capabilities_into_extension_context(monkeypatch, tmp_path):
    from worker_core.bootstrap import bootstrap_runtime
    from worker_core.cli import _resolve_api_key
    from worker_core.config import WorkerConfig

    seen_contexts = []

    async def fake_load_ai_extensions_async(context=None):
        seen_contexts.append(context)
        return []

    async def fake_load_extensions_async(context=None):
        seen_contexts.append(context)
        return [], __import__("worker_core.extensions", fromlist=["HookDispatcher"]).HookDispatcher()

    class _Provider:
        async def close(self):
            return None

    class _Registry:
        def create(self, provider_type, api_key=None, **kwargs):
            return _Provider()

    monkeypatch.setattr("worker_core.bootstrap.create_default_registry", lambda: _Registry())
    monkeypatch.setattr("worker_core.bootstrap.load_ai_extensions_async", fake_load_ai_extensions_async)
    monkeypatch.setattr("worker_core.bootstrap.load_extensions_async", fake_load_extensions_async)
    monkeypatch.setattr(
        "worker_core.bootstrap.resolve_provider_runtime_config",
        lambda config, provider_name: (provider_name, {}),
    )
    monkeypatch.setattr(
        "worker_core.bootstrap.fetch_model_runtime_info",
        lambda config, provider_name, model_id: __import__("asyncio").sleep(0, result=(0, 0.0, 0.0)),
    )

    runtime = __import__("asyncio").run(
        bootstrap_runtime(
            WorkerConfig(),
            "openai",
            "gpt-4.1",
            project_dir=str(tmp_path),
            resolve_api_key=_resolve_api_key,
            include_extensions=True,
            runtime="local",
        )
    )

    assert runtime.extensions == []
    assert len(seen_contexts) == 2
    for context in seen_contexts:
        assert context is not None
        assert "builtin_capabilities" in context.extras
        assert sorted(context.extras["builtin_capabilities"]) == [
            "artel-mcp",
            "artel-orchestration",
            "artel-worktree",
        ]


def test_list_installed_extensions_includes_bundled_capabilities(monkeypatch):
    from worker_core.extensions_admin import list_installed_extensions

    class _Ext:
        version = "1.2.3"

    monkeypatch.setattr(
        "worker_core.extensions_admin.discover_extensions",
        lambda: {"worker-ext-demo": _Ext},
    )
    monkeypatch.setattr(
        "worker_core.extensions_admin.ext_manifest.list_entries",
        lambda: [type("Entry", (), {"name": "worker-ext-demo", "source": "git+https://example.com/demo.git"})()],
    )

    result = list_installed_extensions()
    names = [item.name for item in result]

    assert "artel-worktree" in names
    assert "artel-orchestration" in names
    assert "artel-mcp" in names
    assert "worker-ext-demo" in names
    bundled = {item.name: item for item in result if item.source == "bundled"}
    assert bundled["artel-worktree"].version == "bundled"
