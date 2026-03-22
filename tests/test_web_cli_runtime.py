"""CLI/runtime smoke tests for the experimental Artel web surface."""

from __future__ import annotations

import asyncio
from pathlib import Path

from click.testing import CliRunner


def _run_coro(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_web_cli_bootstraps_local_server_when_remote_url_missing(monkeypatch):
    import artel_tui.local_server as local_server_mod
    from artel_core import cli as cli_mod
    from artel_core.artel_bootstrap import ArtelBootstrapResult

    captured: dict[str, object] = {}
    expected_project_dir = str(Path("/tmp/project-web").resolve())

    monkeypatch.setattr(cli_mod.os, "getcwd", lambda: "/tmp/project-web")
    monkeypatch.setattr(
        "artel_core.artel_bootstrap.bootstrap_artel",
        lambda project_dir=None, command_name=None, prompt=None: ArtelBootstrapResult(
            project_dir=expected_project_dir,
            cmux_required=False,
            cmux_preflight=None,
        ),
    )

    async def fake_ensure_managed_local_server(project_dir: str):
        assert project_dir == expected_project_dir
        return local_server_mod.LocalServerHandle(
            remote_url="ws://127.0.0.1:9011",
            auth_token="artel_local_token",
            project_dir=project_dir,
            pid=4321,
        )

    def fake_run_web(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        local_server_mod,
        "ensure_managed_local_server",
        fake_ensure_managed_local_server,
    )
    monkeypatch.setattr("artel_web.app.run_web", fake_run_web)
    monkeypatch.setattr(cli_mod.asyncio, "run", _run_coro)

    runner = CliRunner()
    result = runner.invoke(cli_mod.cli, ["web", "--no-open-browser"])

    assert result.exit_code == 0
    assert captured == {
        "host": "127.0.0.1",
        "port": 8743,
        "remote_url": "ws://127.0.0.1:9011",
        "auth_token": "artel_local_token",
        "native": False,
        "open_browser": False,
        "project_dir": expected_project_dir,
    }


def test_web_cli_respects_explicit_remote_url_and_project_dir(monkeypatch):
    from artel_core import cli as cli_mod

    captured: dict[str, object] = {}

    def fake_run_web(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("artel_web.app.run_web", fake_run_web)

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.cli,
        [
            "web",
            "--host",
            "0.0.0.0",
            "--port",
            "8843",
            "--remote-url",
            "ws://example.com:7432",
            "--token",
            "tok_test",
            "--project-dir",
            "/srv/project",
            "--native",
            "--no-open-browser",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "host": "0.0.0.0",
        "port": 8843,
        "remote_url": "ws://example.com:7432",
        "auth_token": "tok_test",
        "native": True,
        "open_browser": False,
        "project_dir": "/srv/project",
    }


def test_run_web_requires_optional_dependencies(monkeypatch):
    import artel_web.app as web_app

    monkeypatch.setattr(web_app, "websockets", None)

    try:
        web_app.run_web(remote_url="ws://example.com:7432", open_browser=False)
    except RuntimeError as exc:
        assert "websockets is not installed" in str(exc)
    else:
        raise AssertionError("run_web should fail when optional dependencies are missing")


def test_session_select_value_only_returns_known_session_ids():
    from artel_web.app import WebRuntimeState
    from artel_web.backend_store import WebSessionRecord

    state = WebRuntimeState(remote_url="ws://example.com:7432")
    state.session_id = "missing"
    state.sessions = [WebSessionRecord(id="sess-1"), WebSessionRecord(id="sess-2")]

    assert state._session_select_value() == "sess-1"

    state.session_id = "sess-2"
    assert state._session_select_value() == "sess-2"

    state.sessions = []
    assert state._session_select_value() is None
