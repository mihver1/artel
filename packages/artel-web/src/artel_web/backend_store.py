"""State models for the Artel web surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WebBackendEntry:
    name: str = ""
    url: str = ""
    kind: str = ""


@dataclass(slots=True)
class WebMessageRecord:
    role: str
    content: str = ""
    reasoning: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_result: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class WebSessionRecord:
    id: str
    title: str = ""
    model: str = ""
    project_dir: str = ""
    thinking_level: str = "off"
    messages: int = 0
    created_at: str = ""
    updated_at: str = ""
    exists: bool = True
    rule_overrides: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WebTerminalContext:
    command: str = ""
    output: str = ""
    exit_code: int | None = None


__all__ = [
    "WebBackendEntry",
    "WebMessageRecord",
    "WebSessionRecord",
    "WebTerminalContext",
]
