"""NiceGUI-based Artel web runtime."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import asdict
from typing import Any

try:
    import websockets
except ModuleNotFoundError:  # pragma: no cover - optional until web extras are installed
    websockets = None  # type: ignore[assignment]

try:
    from nicegui import app, ui
except ModuleNotFoundError:  # pragma: no cover - optional until web extras are installed
    class _StubStorage:
        def __init__(self) -> None:
            self.general: dict[str, Any] = {}

    class _StubApp:
        def __init__(self) -> None:
            self.storage = _StubStorage()

    class _StubUI:
        def page(self, _path: str):
            def decorator(func: Any) -> Any:
                return func

            return decorator

        def run(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError(
                "NiceGUI is not installed. Run `uv sync --dev` "
                "(or install the artel-web dependencies) "
                "to use `artel web`."
            )

        def __getattr__(self, _name: str) -> Any:
            def _missing(*args: Any, **kwargs: Any) -> Any:
                raise RuntimeError(
                    "NiceGUI is not installed. Run `uv sync --dev` "
                    "(or install the artel-web dependencies) "
                    "to use `artel web`."
                )

            return _missing

    app = _StubApp()  # type: ignore[assignment]
    ui = _StubUI()  # type: ignore[assignment]

from artel_core.control import RemoteArtelControl

from artel_web.backend_store import WebMessageRecord, WebSessionRecord, WebTerminalContext
from artel_web.rendering import (
    render_follow_diff_markdown,
    render_follow_file_markdown,
    render_follow_task_markdown,
    render_follow_terminal_markdown,
    render_follow_tool_activity_markdown,
    render_message_markdown,
    render_tool_activity_markdown,
)

_ENGINEERING_THEME = """
body {
  background:
    radial-gradient(circle at top left, rgba(59,130,246,.12), transparent 24%),
    radial-gradient(circle at top right, rgba(168,85,247,.10), transparent 26%),
    linear-gradient(180deg, #07111f 0%, #0b1220 45%, #050b15 100%);
  color: #e5eefb;
}
.artel-shell {
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(8, 15, 28, 0.78);
  backdrop-filter: blur(22px);
  box-shadow: 0 24px 100px rgba(0, 0, 0, 0.42);
}
.artel-panel {
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(7, 12, 24, 0.92));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.03);
}
.artel-card {
  border: 1px solid rgba(148, 163, 184, 0.10);
  background: rgba(12, 19, 33, 0.88);
}
.artel-glow {
  box-shadow: 0 0 0 1px rgba(96, 165, 250, .18), 0 12px 48px rgba(59, 130, 246, .10);
}
.artel-title {
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #8fb8ff;
}
.artel-mono, .artel-mono * {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace;
}
.artel-scroll {
  scrollbar-width: thin;
}
.artel-scroll::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
.artel-scroll::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.22);
  border-radius: 999px;
}
"""


class WebControlClient(RemoteArtelControl):
    """Shared REST/WebSocket client for Artel Web."""

    def __init__(self, remote_url: str, auth_token: str = "") -> None:
        super().__init__(remote_url, auth_token)
        self.remote_url = remote_url

    async def list_delegates(self, session_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/api/sessions/{session_id}/delegates")

    async def get_delegate(self, session_id: str, run_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/api/sessions/{session_id}/delegates/{run_id}")

    async def cancel_delegate(self, session_id: str, run_id: str) -> dict[str, Any]:
        return await self.request(
            "POST",
            f"/api/sessions/{session_id}/delegates/{run_id}/cancel",
            json_data={},
        )

    async def delete_session(self, session_id: str) -> dict[str, Any]:
        return await self.request("DELETE", f"/api/sessions/{session_id}")

    async def run_worktree(self, session_id: str, arg: str) -> dict[str, Any]:
        return await self.request("POST", f"/api/sessions/{session_id}/wt", json_data={"arg": arg})


class WebRuntimeState:
    """Mutable UI state for a single NiceGUI client."""

    def __init__(self, *, remote_url: str, auth_token: str = "", project_dir: str = "") -> None:
        self.remote_url = remote_url
        self.auth_token = auth_token
        self.project_dir = project_dir
        self.control = WebControlClient(remote_url, auth_token)
        self.session_id = "default"
        self.sessions: list[WebSessionRecord] = []
        self.messages: list[WebMessageRecord] = []
        self.server_info: dict[str, Any] = {}
        self.diagnostics: dict[str, Any] = {}
        self.providers: list[dict[str, Any]] = []
        self.models: list[dict[str, Any]] = []
        self.prompts: list[dict[str, Any]] = []
        self.skills: list[dict[str, Any]] = []
        self.rules: list[dict[str, Any]] = []
        self.schedules: list[dict[str, Any]] = []
        self.delegates: list[dict[str, Any]] = []
        self.tasks_content: str = ""
        self.notes_content: str = ""
        self.terminal = WebTerminalContext()
        self.composer_text: str = ""
        self.status_text: str = "Ready"
        self.busy: bool = False
        self.ws_task: asyncio.Task[Any] | None = None
        self.ws: Any = None
        self._tool_call_names: dict[str, str] = {}

        self.session_list: Any = None
        self.chat_column: Any = None
        self.follow_task_md: Any = None
        self.follow_file_md: Any = None
        self.follow_diff_md: Any = None
        self.follow_terminal_md: Any = None
        self.follow_activity_md: Any = None
        self.server_meta_md: Any = None
        self.providers_md: Any = None
        self.prompts_md: Any = None
        self.skills_md: Any = None
        self.rules_md: Any = None
        self.schedule_md: Any = None
        self.delegates_md: Any = None
        self.tasks_editor: Any = None
        self.notes_editor: Any = None
        self.status_badge: Any = None
        self.composer: Any = None

    def _headers(self) -> dict[str, str]:
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}

    def _session_payloads(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.sessions]

    def _session_options(self) -> dict[str, str]:
        options: dict[str, str] = {}
        for session in self.sessions:
            label = session.title.strip() or session.id
            tail = []
            if session.model:
                tail.append(session.model)
            if session.messages:
                tail.append(f"{session.messages} msgs")
            if tail:
                label = f"{label} — {' · '.join(tail)}"
            options[session.id] = label
        return options

    def _session_select_value(self) -> str | None:
        options = self._session_options()
        if self.session_id in options:
            return self.session_id
        return next(iter(options), None)

    async def bootstrap(self) -> None:
        await self.refresh_all(ensure_session=True)
        await self.ensure_ws_listener()
        self.render_all()

    async def refresh_all(self, *, ensure_session: bool = False) -> None:
        sessions_payload = await self.control.list_sessions()
        sessions_items = sessions_payload.get("sessions", [])
        self.sessions = [WebSessionRecord(**item) for item in sessions_items]
        if ensure_session and not self.sessions:
            await self.control.set_session_project(
                self.session_id,
                self.project_dir or os.getcwd(),
            )
            sessions_payload = await self.control.list_sessions()
            sessions_items = sessions_payload.get("sessions", [])
            self.sessions = [WebSessionRecord(**item) for item in sessions_items]
        if self.sessions and self.session_id not in {item.id for item in self.sessions}:
            self.session_id = self.sessions[0].id

        server_info_payload = await self.control.get_server_info()
        diagnostics_payload = await self.control.get_server_diagnostics()
        providers_payload = await self.control.list_providers()
        models_payload = await self.control.list_models()
        prompts_payload = await self.control.list_prompts()
        skills_payload = await self.control.list_skills()
        rules_payload = await self.control.list_rules(project_dir=self.project_dir)
        schedules_payload = await self.control.list_schedules()

        self.server_info = server_info_payload
        self.diagnostics = diagnostics_payload
        self.providers = list(providers_payload.get("providers", []))
        self.models = list(models_payload.get("providers", []))
        self.prompts = list(prompts_payload.get("prompts", []))
        self.skills = list(skills_payload.get("skills", []))
        self.rules = list(rules_payload.get("rules", []))
        self.schedules = list(schedules_payload.get("schedules", []))

        await self.refresh_session_views()

    async def refresh_session_views(self) -> None:
        messages_payload = await self.control.get_session_messages(self.session_id)
        self.messages = [WebMessageRecord(**item) for item in messages_payload.get("messages", [])]

        delegates_payload = await self.control.list_delegates(self.session_id)
        self.delegates = list(delegates_payload.get("delegates", []))

        tasks_payload = await self.control.get_session_tasks(self.session_id)
        notes_payload = await self.control.get_session_notes(self.session_id)
        session_payload = await self.control.get_session(self.session_id)

        self.tasks_content = str(tasks_payload.get("content", ""))
        self.notes_content = str(notes_payload.get("content", ""))
        session_data = session_payload.get("session")
        if isinstance(session_data, dict):
            current = WebSessionRecord(**session_data)
            ids = {item.id for item in self.sessions}
            if current.id not in ids:
                self.sessions.append(current)
            else:
                self.sessions = [
                    current if item.id == current.id else item
                    for item in self.sessions
                ]

    async def ensure_ws_listener(self) -> None:
        if self.ws_task is not None and not self.ws_task.done():
            return
        self.ws_task = asyncio.create_task(self._ws_loop(), name="artel-web-ws")

    async def _ws_loop(self) -> None:
        while True:
            try:
                async with websockets.connect(
                    self.remote_url,
                    additional_headers=self._headers(),
                ) as websocket:
                    self.ws = websocket
                    async for raw in websocket:
                        payload = json.loads(raw)
                        await self.handle_ws_payload(payload)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.ws = None
                self.status_text = f"WebSocket reconnecting: {exc}"
                self.busy = False
                self.render_status()
                await asyncio.sleep(1.5)

    async def handle_ws_payload(self, payload: dict[str, Any]) -> None:
        if str(payload.get("session_id", "") or self.session_id) != self.session_id:
            msg_type = str(payload.get("type", ""))
            if msg_type not in {"status", "error"}:
                return

        msg_type = str(payload.get("type", ""))
        if msg_type == "reasoning_delta":
            if self.messages and self.messages[-1].role == "assistant":
                self.messages[-1].reasoning += str(payload.get("content", ""))
            else:
                self.messages.append(
                    WebMessageRecord(role="assistant", reasoning=str(payload.get("content", "")))
                )
            self.busy = True
            self.status_text = "Thinking"
        elif msg_type == "text_delta":
            if self.messages and self.messages[-1].role == "assistant":
                self.messages[-1].content += str(payload.get("content", ""))
            else:
                self.messages.append(
                    WebMessageRecord(
                        role="assistant",
                        content=str(payload.get("content", "")),
                    )
                )
            self.busy = True
            self.status_text = "Responding"
        elif msg_type == "tool_call":
            call_id = str(payload.get("call_id", "") or uuid.uuid4())
            tool_name = str(payload.get("tool", "tool"))
            self._tool_call_names[call_id] = tool_name
            self.messages.append(
                WebMessageRecord(
                    role="assistant",
                    content="",
                    tool_calls=[
                        {
                            "id": call_id,
                            "name": tool_name,
                            "arguments": json.dumps(payload.get("args", {}), ensure_ascii=False),
                        }
                    ],
                )
            )
            self.busy = True
            self.status_text = f"Tool: {tool_name}"
        elif msg_type == "tool_result":
            call_id = str(payload.get("call_id", "") or "")
            tool_name = str(payload.get("tool", "") or self._tool_call_names.get(call_id, "tool"))
            self.messages.append(
                WebMessageRecord(
                    role="tool",
                    content=str(payload.get("output", "") or ""),
                    tool_result={
                        "tool_call_id": call_id,
                        "content": str(payload.get("output", "") or ""),
                        "is_error": bool(payload.get("is_error", False)),
                        "display": payload.get("display"),
                    },
                    tool_calls=[
                        {
                            "id": call_id,
                            "name": tool_name,
                            "arguments": json.dumps({}, ensure_ascii=False),
                        }
                    ],
                )
            )
            self.busy = True
            self.status_text = f"Tool result: {tool_name}"
        elif msg_type == "status":
            self.busy = bool(payload.get("busy", False))
            self.status_text = str(payload.get("state", "idle"))
            if not self.busy:
                await self.refresh_session_views()
        elif msg_type == "error":
            self.messages.append(
                WebMessageRecord(
                    role="error",
                    content=str(payload.get("error", "Unknown error")),
                )
            )
            self.busy = False
            self.status_text = str(payload.get("error", "Error"))

        self.render_all()

    async def send_message(self) -> None:
        text = self.composer_text.strip()
        if not text:
            ui.notify("Message is empty", color="warning")
            return
        if self.ws is None:
            await self.ensure_ws_listener()
            await asyncio.sleep(0)
        if self.ws is None:
            ui.notify("WebSocket is not connected yet", color="negative")
            return
        self.messages.append(WebMessageRecord(role="user", content=text))
        self.composer_text = ""
        if self.composer is not None:
            self.composer.value = ""
        self.busy = True
        self.status_text = "Queued"
        self.render_all()
        await self.ws.send(
            json.dumps(
                {
                    "type": "message",
                    "content": text,
                    "session_id": self.session_id,
                }
            )
        )

    async def cancel_run(self) -> None:
        if self.ws is None:
            return
        await self.ws.send(json.dumps({"type": "cancel", "session_id": self.session_id}))
        self.busy = False
        self.status_text = "Cancelled"
        self.render_status()

    async def create_session(self) -> None:
        self.session_id = str(uuid.uuid4())
        project_dir = self.project_dir or os.getcwd()
        try:
            await self.control.set_session_project(self.session_id, project_dir)
        except RuntimeError:
            await self.control.set_session_title(self.session_id, f"Session {self.session_id[:8]}")
            await self.control.set_session_project(self.session_id, project_dir)
        await self.refresh_all()
        self.render_all()

    async def delete_current_session(self) -> None:
        await self.control.delete_session(self.session_id)
        await self.refresh_all()
        self.render_all()

    async def change_session(self, session_id: str) -> None:
        self.session_id = session_id
        await self.refresh_session_views()
        self.render_all()

    async def run_terminal_command(self, command: str) -> None:
        command = command.strip()
        if not command:
            return
        result = await self.control.run_bash(self.session_id, command)
        self.terminal = WebTerminalContext(
            command=str(result.get("command", command)),
            output=str(result.get("output", "")),
            exit_code=result.get("exit_code"),
        )
        self.status_text = f"Terminal: {command}"
        self.render_all()

    async def save_tasks(self) -> None:
        if self.tasks_editor is None:
            return
        self.tasks_content = str(self.tasks_editor.value or "")
        await self.control.put_session_tasks(self.session_id, self.tasks_content)
        ui.notify("Tasks saved", color="positive")

    async def save_notes(self) -> None:
        if self.notes_editor is None:
            return
        self.notes_content = str(self.notes_editor.value or "")
        await self.control.put_session_notes(self.session_id, self.notes_content)
        ui.notify("Notes saved", color="positive")

    def render_status(self) -> None:
        if self.status_badge is not None:
            if self.busy:
                tone = "bg-blue-500/15 text-blue-100"
            else:
                tone = "bg-emerald-500/15 text-emerald-200"
            self.status_badge.set_text(self.status_text)
            self.status_badge.classes(
                replace=f"px-3 py-1 rounded-full text-xs artel-mono {tone}"
            )

    def render_sessions(self) -> None:
        if self.session_list is None:
            return
        self.session_list.options = self._session_options()
        self.session_list.value = self._session_select_value()
        self.session_list.update()

    def render_chat(self) -> None:
        if self.chat_column is None:
            return
        self.chat_column.clear()
        with self.chat_column:
            if not self.messages:
                ui.markdown(
                    "### Follow-first engineering workspace\n\n"
                    "Start a session, inspect the repo, and drive "
                    "parallel Artel flows from one web surface."
                ).classes("w-full text-slate-200")
                return
            for message in self.messages:
                card_classes = "artel-card rounded-2xl p-4 w-full"
                with ui.card().classes(card_classes):
                    ui.markdown(render_message_markdown(message)).classes("w-full")
                    tool_md = render_tool_activity_markdown(message)
                    if tool_md.strip() and tool_md.strip() != "No tool activity yet.":
                        ui.separator().classes("bg-slate-700")
                        ui.markdown(tool_md).classes("w-full artel-mono")

    def render_follow(self) -> None:
        session = next((item for item in self.sessions if item.id == self.session_id), None)
        if session is None:
            session = WebSessionRecord(id=self.session_id, project_dir=self.project_dir)
        if self.follow_task_md is not None:
            self.follow_task_md.content = render_follow_task_markdown(
                session,
                self.messages,
                default_project_dir=self.project_dir or os.getcwd(),
                default_model=self.server_info.get("default_model", ""),
                command=self.terminal.command,
                output=self.terminal.output,
                exit_code=self.terminal.exit_code,
            )
            self.follow_task_md.update()
        if self.follow_file_md is not None:
            self.follow_file_md.content = render_follow_file_markdown(self.messages)
            self.follow_file_md.update()
        if self.follow_diff_md is not None:
            self.follow_diff_md.content = render_follow_diff_markdown(self.messages)
            self.follow_diff_md.update()
        if self.follow_terminal_md is not None:
            self.follow_terminal_md.content = render_follow_terminal_markdown(
                self.messages,
                command=self.terminal.command,
                output=self.terminal.output,
                exit_code=self.terminal.exit_code,
            )
            self.follow_terminal_md.update()
        if self.follow_activity_md is not None:
            self.follow_activity_md.content = render_follow_tool_activity_markdown(self.messages)
            self.follow_activity_md.update()

    def render_catalogs(self) -> None:
        if self.server_meta_md is not None:
            info_lines = [
                "### Control plane",
                f"- remote: `{self.remote_url}`",
                f"- project: `{self.server_info.get('project_dir', self.project_dir)}`",
                f"- default model: `{self.server_info.get('default_model', '')}`",
                f"- active sessions: `{self.diagnostics.get('active_sessions', 0)}`",
                f"- loaded extensions: `{self.server_info.get('loaded_extensions', 0)}`",
            ]
            scheduler = self.server_info.get("scheduler", {})
            if isinstance(scheduler, dict):
                info_lines.append(f"- schedules: `{scheduler.get('count', 0)}`")
                if scheduler.get("next_run_at"):
                    info_lines.append(f"- next run: `{scheduler.get('next_run_at')}`")
            self.server_meta_md.content = "\n".join(info_lines)
            self.server_meta_md.update()
        if self.providers_md is not None:
            provider_lines = ["### Providers"]
            for provider in self.providers[:8]:
                provider_name = provider.get("name", provider.get("id", "provider"))
                provider_status = provider.get("status", "")
                provider_lines.append(f"- **{provider_name}** — {provider_status}")
            self.providers_md.content = "\n".join(provider_lines)
            self.providers_md.update()
        if self.prompts_md is not None:
            lines = ["### Prompt library"]
            for prompt in self.prompts[:8]:
                lines.append(f"- **{prompt.get('name', '')}** — {prompt.get('preview', '')}")
            self.prompts_md.content = "\n".join(lines)
            self.prompts_md.update()
        if self.skills_md is not None:
            lines = ["### Skills"]
            for skill in self.skills[:8]:
                lines.append(f"- **{skill.get('name', '')}** — {skill.get('description', '')}")
            self.skills_md.content = "\n".join(lines)
            self.skills_md.update()
        if self.rules_md is not None:
            lines = ["### Rules"]
            for rule in self.rules[:8]:
                state = "enabled" if rule.get("enabled", False) else "disabled"
                lines.append(f"- `{rule.get('id', '')}` [{state}] — {rule.get('text', '')}")
            self.rules_md.content = "\n".join(lines)
            self.rules_md.update()
        if self.schedule_md is not None:
            lines = ["### Schedules"]
            for entry in self.schedules[:8]:
                schedule = entry.get("schedule", {}) if isinstance(entry, dict) else {}
                state = entry.get("state", {}) if isinstance(entry, dict) else {}
                schedule_id = schedule.get("id", "")
                schedule_kind = schedule.get("kind", "")
                next_run_at = state.get("next_run_at", "")
                lines.append(
                    f"- **{schedule_id}** — {schedule_kind} · next `{next_run_at}`"
                )
            self.schedule_md.content = "\n".join(lines)
            self.schedule_md.update()
        if self.delegates_md is not None:
            lines = ["### Parallel delegates"]
            for delegate in self.delegates[:8]:
                run_id = str(delegate.get("run_id", ""))[:8]
                status = delegate.get("status", "")
                task = delegate.get("task", "")
                lines.append(f"- **{run_id}** — {status} · {task}")
            self.delegates_md.content = "\n".join(lines)
            self.delegates_md.update()
        if self.tasks_editor is not None and self.tasks_editor.value != self.tasks_content:
            self.tasks_editor.value = self.tasks_content
        if self.notes_editor is not None and self.notes_editor.value != self.notes_content:
            self.notes_editor.value = self.notes_content

    def render_all(self) -> None:
        self.render_status()
        self.render_sessions()
        self.render_chat()
        self.render_follow()
        self.render_catalogs()


async def _mount_client(*, remote_url: str, auth_token: str, project_dir: str) -> None:
    state = WebRuntimeState(
        remote_url=remote_url,
        auth_token=auth_token,
        project_dir=project_dir,
    )
    ui.add_head_html(f"<style>{_ENGINEERING_THEME}</style>")
    await state.bootstrap()

    with ui.column().classes("w-full min-h-screen p-6 gap-4 artel-scroll"):
        header_classes = (
            "w-full items-center justify-between artel-shell "
            "rounded-[28px] px-6 py-4"
        )
        with ui.row().classes(header_classes):
            with ui.column().classes("gap-1"):
                ui.label("ARTEL WEB").classes("artel-title text-xs font-semibold")
                ui.label("Native follow-first engineering UI").classes(
                    "text-2xl font-semibold text-white"
                )
                ui.label(
                    "Parallel sessions, live agent streaming, and "
                    "control-plane observability in one glass cockpit."
                ).classes("text-sm text-slate-300")
            with ui.row().classes("items-center gap-3"):
                state.status_badge = ui.label(state.status_text).classes(
                    "px-3 py-1 rounded-full text-xs artel-mono bg-emerald-500/15 text-emerald-200"
                )
                ui.button(
                    "Refresh",
                    on_click=lambda: asyncio.create_task(state.refresh_all()),
                    icon="refresh",
                ).props("flat")
                ui.button(
                    "New session",
                    on_click=lambda: asyncio.create_task(state.create_session()),
                    icon="add",
                ).props("unelevated color=primary")
                ui.button(
                    "Delete",
                    on_click=lambda: asyncio.create_task(state.delete_current_session()),
                    icon="delete",
                ).props("flat color=red")

        with ui.row().classes("w-full gap-4 items-stretch"):
            with ui.column().classes("w-[20rem] shrink-0 gap-4"):
                with ui.card().classes("artel-panel rounded-3xl p-4 gap-3"):
                    ui.label("Sessions").classes("artel-title text-xs")
                    state.session_list = ui.select(
                        options=state._session_options(),
                        value=state._session_select_value(),
                        on_change=lambda e: asyncio.create_task(state.change_session(str(e.value))),
                    ).classes("w-full")
                    model_input = ui.input("Model override", value="").classes("w-full")
                    thinking_select = ui.select(
                        ["off", "minimal", "low", "medium", "high", "xhigh"],
                        value="off",
                        label="Thinking",
                    ).classes("w-full")
                    project_input = ui.input(
                        "Project path",
                        value=project_dir,
                    ).classes("w-full artel-mono")
                    with ui.row().classes("w-full gap-2"):
                        ui.button(
                            "Apply",
                            on_click=lambda: asyncio.create_task(
                                _apply_session_settings(
                                    state,
                                    model_input.value,
                                    project_input.value,
                                    thinking_select.value,
                                )
                            ),
                        ).props("unelevated color=primary")
                        ui.button(
                            "Cancel run",
                            on_click=lambda: asyncio.create_task(state.cancel_run()),
                            icon="stop",
                        ).props("flat color=orange")

                with ui.card().classes("artel-panel rounded-3xl p-4 gap-3"):
                    ui.label("Control plane").classes("artel-title text-xs")
                    state.server_meta_md = ui.markdown("")
                    state.providers_md = ui.markdown("")
                    state.delegates_md = ui.markdown("")

            with ui.column().classes("flex-1 min-w-0 gap-4"):
                with ui.card().classes("artel-panel artel-glow rounded-3xl p-4 gap-4 flex-1"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label("Conversation").classes("artel-title text-xs")
                        quick_cmd = ui.input(
                            "Shell / !cmd",
                            placeholder="pytest -q tests/test_web_rendering.py",
                        ).classes("w-[28rem] artel-mono")
                        ui.button(
                            "Run shell",
                            on_click=lambda: asyncio.create_task(
                                state.run_terminal_command(str(quick_cmd.value or ""))
                            ),
                            icon="terminal",
                        ).props("flat")
                    state.chat_column = ui.column().classes(
                        "w-full gap-3 max-h-[52vh] overflow-auto artel-scroll"
                    )
                    with ui.row().classes("w-full items-end gap-3"):
                        state.composer = ui.textarea(
                            label="Message",
                            placeholder=(
                                "Drive the current implementation forward. "
                                "Ask Artel to inspect files, run tests, "
                                "or coordinate delegates."
                            ),
                            value="",
                        ).classes("flex-1 artel-mono").props("autogrow outlined")
                        state.composer.on_value_change(
                            lambda e: setattr(state, "composer_text", str(e.value or ""))
                        )
                        with ui.column().classes("gap-2"):
                            ui.button(
                                "Send",
                                on_click=lambda: asyncio.create_task(state.send_message()),
                                icon="send",
                            ).props("unelevated color=primary")
                            ui.button(
                                "Fork",
                                on_click=lambda: asyncio.create_task(_fork_session(state)),
                                icon="call_split",
                            ).props("flat")
                            ui.button(
                                "Compact",
                                on_click=lambda: asyncio.create_task(_compact_session(state)),
                                icon="compress",
                            ).props("flat")

                with ui.grid(columns=2).classes("w-full gap-4"):
                    with ui.card().classes("artel-panel rounded-3xl p-4"):
                        ui.label("Follow: task").classes("artel-title text-xs")
                        state.follow_task_md = ui.markdown("")
                    with ui.card().classes("artel-panel rounded-3xl p-4"):
                        ui.label("Follow: focused file").classes("artel-title text-xs")
                        state.follow_file_md = ui.markdown("")
                    with ui.card().classes("artel-panel rounded-3xl p-4"):
                        ui.label("Follow: diff").classes("artel-title text-xs")
                        state.follow_diff_md = ui.markdown("")
                    with ui.card().classes("artel-panel rounded-3xl p-4"):
                        ui.label("Follow: terminal").classes("artel-title text-xs")
                        state.follow_terminal_md = ui.markdown("")
                    with ui.card().classes("artel-panel rounded-3xl p-4 col-span-2"):
                        ui.label("Follow: tool activity").classes("artel-title text-xs")
                        state.follow_activity_md = ui.markdown("")

            with ui.column().classes("w-[24rem] shrink-0 gap-4"):
                with ui.card().classes("artel-panel rounded-3xl p-4 gap-3"):
                    ui.label("Prompt / skill catalog").classes("artel-title text-xs")
                    state.prompts_md = ui.markdown("")
                    state.skills_md = ui.markdown("")
                    state.rules_md = ui.markdown("")
                    state.schedule_md = ui.markdown("")
                with ui.card().classes("artel-panel rounded-3xl p-4 gap-3"):
                    ui.label("Shared task board").classes("artel-title text-xs")
                    state.tasks_editor = ui.textarea(
                        value=state.tasks_content,
                    ).classes("w-full artel-mono").props("autogrow outlined")
                    ui.button(
                        "Save tasks",
                        on_click=lambda: asyncio.create_task(state.save_tasks()),
                        icon="save",
                    ).props("flat")
                with ui.card().classes("artel-panel rounded-3xl p-4 gap-3"):
                    ui.label("Operator notes").classes("artel-title text-xs")
                    state.notes_editor = ui.textarea(
                        value=state.notes_content,
                    ).classes("w-full artel-mono").props("autogrow outlined")
                    ui.button(
                        "Save notes",
                        on_click=lambda: asyncio.create_task(state.save_notes()),
                        icon="save",
                    ).props("flat")

    state.render_all()


async def _apply_session_settings(
    state: WebRuntimeState,
    model: str,
    project_dir: str,
    thinking_level: str,
) -> None:
    if project_dir.strip():
        await state.control.set_session_project(state.session_id, project_dir.strip())
        state.project_dir = project_dir.strip()
    if model.strip():
        await state.control.set_session_model(state.session_id, model.strip())
    if thinking_level:
        await state.control.set_session_thinking(state.session_id, str(thinking_level))
    await state.refresh_all()
    state.render_all()


async def _fork_session(state: WebRuntimeState) -> None:
    payload = await state.control.fork_session(state.session_id)
    new_session = payload.get("session", {})
    new_session_id = str(payload.get("session_id", new_session.get("id", "")) or "")
    if new_session_id:
        state.session_id = new_session_id
    await state.refresh_all()
    state.render_all()


async def _compact_session(state: WebRuntimeState) -> None:
    await state.control.compact_session(state.session_id)
    await state.refresh_session_views()
    state.render_all()


@ui.page("/")
async def index_page() -> None:
    remote_url = str(app.storage.general.get("remote_url", ""))
    auth_token = str(app.storage.general.get("auth_token", ""))
    project_dir = str(app.storage.general.get("project_dir", ""))
    if not remote_url:
        ui.label("Artel Web is not configured.").classes("text-red-300")
        return
    await _mount_client(remote_url=remote_url, auth_token=auth_token, project_dir=project_dir)


@ui.page("/health")
def health_page() -> None:
    ui.label('{"status": "ok", "surface": "artel-web"}').classes("artel-mono")


def _ensure_web_runtime_dependencies() -> None:
    if websockets is None:
        raise RuntimeError(
            "websockets is not installed. Run `uv sync --dev` "
            "(or install the artel-web dependencies) "
            "to use `artel web`."
        )


def run_web(
    *,
    host: str = "127.0.0.1",
    port: int = 8743,
    remote_url: str,
    auth_token: str = "",
    native: bool = False,
    open_browser: bool = True,
    project_dir: str = "",
) -> None:
    """Start the NiceGUI-based Artel web UI."""
    _ensure_web_runtime_dependencies()
    app.storage.general["remote_url"] = remote_url
    app.storage.general["auth_token"] = auth_token
    app.storage.general["project_dir"] = project_dir
    ui.run(
        host=host,
        port=port,
        title="Artel Web",
        reload=False,
        show=open_browser,
        native=native,
        storage_secret="artel-web-dev",
    )
