from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.mark.asyncio
async def test_handle_command_routes_git_aliases(monkeypatch):
    from artel_tui.app import ArtelApp

    app = ArtelApp()
    seen: list[tuple[str, str]] = []

    async def fake_cmd_git(cmd: str, arg: str) -> None:
        seen.append((cmd, arg))

    monkeypatch.setattr(app, "_cmd_git", fake_cmd_git)

    await app._handle_command("/status")
    await app._handle_command("/diff app.py")
    await app._handle_command("/rollback --all")

    assert seen == [
        ("/status", ""),
        ("/diff", "app.py"),
        ("/rollback", "--all"),
    ]


@pytest.mark.asyncio
async def test_handle_command_routes_compact_without_awaiting_worker():
    from artel_tui.app import ArtelApp

    app = ArtelApp()
    compact = MagicMock()
    app._cmd_compact = compact  # type: ignore[method-assign]

    await app._handle_command("/compact summarize this")

    compact.assert_called_once_with("summarize this")
