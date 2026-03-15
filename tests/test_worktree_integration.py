from __future__ import annotations

from types import SimpleNamespace

import pytest


class _Footer:
    def __init__(self):
        self.model = ""
        self.cwd = ""

    def set_model(self, model: str) -> None:
        self.model = model

    def set_cwd(self, cwd: str) -> None:
        self.cwd = cwd


def test_wt_command_appears_in_command_suggestions():
    from worker_tui.app import WorkerApp

    app = WorkerApp()
    values = [suggestion.value for suggestion in app._command_suggestions()]

    assert "/wt" in values


@pytest.mark.asyncio
async def test_handle_command_dispatches_remote_wt_command():
    from worker_tui.app import WorkerApp

    class _RemoteClient:
        async def request(self, method: str, path: str, *, json_data=None):
            assert method == "POST"
            assert path.endswith("/wt")
            assert json_data == {"arg": "list"}
            return {
                "output": "Worktrees:\n- main [primary] /srv/project @ abc1234",
                "session": {"project_dir": "/srv/project", "model": "openai/gpt-4.1"},
            }

    app = WorkerApp(remote_url="ws://localhost:7432")
    app._remote_control_client = _RemoteClient()
    app.query_one = lambda selector, _cls=None: _Footer()  # type: ignore[method-assign]
    app.run_worker = lambda *args, **kwargs: None  # type: ignore[method-assign]
    seen_messages: list[tuple[str, str]] = []
    app._add_message = lambda content, role="assistant": seen_messages.append((content, role))  # type: ignore[method-assign]

    await app._cmd_wt("list")

    assert seen_messages == [("Worktrees:\n- main [primary] /srv/project @ abc1234", "tool")]


@pytest.mark.asyncio
async def test_handle_command_dispatches_local_wt_command(monkeypatch, tmp_path):
    from worker_tui.app import WorkerApp

    app = WorkerApp()
    app._session = SimpleNamespace(project_dir=str(tmp_path))
    seen_messages: list[tuple[str, str]] = []
    app._add_message = lambda content, role="assistant": seen_messages.append((content, role))  # type: ignore[method-assign]

    monkeypatch.setattr(
        "worker_core.worktree.run_worktree_command",
        lambda project_dir, arg: f"wt:{project_dir}:{arg}",
    )

    await app._cmd_wt("feature/demo")

    assert seen_messages == [(f"wt:{tmp_path}:feature/demo", "tool")]
