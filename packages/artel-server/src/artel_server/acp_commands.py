"""ACP slash-command helpers for Artel."""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass

from artel_core.board import (
    add_task_to_markdown,
    append_project_board_file,
    operator_notes_path,
    read_project_board_file,
    render_numbered_text,
    tasks_path,
    update_task_in_markdown,
)
from artel_core.delegation.formatting import format_run_detail, format_run_list
from artel_core.delegation.registry import get_registry as get_delegation_registry
from artel_core.extensions import ExtensionContext
from artel_core.git_surface import (
    render_git_diff,
    render_git_help,
    render_git_status,
    restore_all,
    restore_path,
    restore_paths,
)
from artel_core.mcp_runtime import McpRuntimeManager
from artel_core.session_rewind import collect_last_ai_changed_paths
from artel_core.worktree import run_worktree_command

from artel_server import server as server_mod


@dataclass(slots=True, frozen=True)
class AcpAvailableCommandSpec:
    name: str
    description: str
    hint: str | None = None


@dataclass(slots=True, frozen=True)
class AcpSlashResult:
    output: str
    is_error: bool = False


AVAILABLE_ACP_COMMANDS: tuple[AcpAvailableCommandSpec, ...] = (
    AcpAvailableCommandSpec("wt", "Manage git worktrees for the current repository", "list | <branch> | rm <path> | finish <path>"),
    AcpAvailableCommandSpec("status", "Show git status for the current project"),
    AcpAvailableCommandSpec("diff", "Show unstaged git diff", "[path]"),
    AcpAvailableCommandSpec("rollback", "Restore one path or all unstaged changes", "<path> | --all"),
    AcpAvailableCommandSpec("undo", "Undo the latest AI file edits in this session"),
    AcpAvailableCommandSpec("rewind", "Create a forked session rewound to an earlier message", "<message_index>"),
    AcpAvailableCommandSpec("mcp", "Show or reload MCP runtime state", "[reload]"),
    AcpAvailableCommandSpec("schedules", "List, show, run, or reload scheduled tasks", "[list|show <id>|run <id>|reload]"),
    AcpAvailableCommandSpec("delegates", "Inspect orchestration runs", "[list|show <id>|tail <id>|cancel <id>]"),
    AcpAvailableCommandSpec("agents", "Alias for /delegates", "[list|show <id>|tail <id>|cancel <id>]"),
    AcpAvailableCommandSpec("git", "Git command group alias", "status | diff [path] | rollback <path>|--all | help"),
    AcpAvailableCommandSpec("tasks", "Read the shared task board"),
    AcpAvailableCommandSpec("task-add", "Add a task to the shared task board", "<title>"),
    AcpAvailableCommandSpec("task-done", "Mark a task as done", "<task-id>"),
    AcpAvailableCommandSpec("notes", "Read operator notes"),
    AcpAvailableCommandSpec("note-add", "Append a short operator note", "<text>"),
)


def available_acp_commands() -> tuple[AcpAvailableCommandSpec, ...]:
    return AVAILABLE_ACP_COMMANDS


async def maybe_handle_slash_command(
    state: server_mod.ServerState,
    session_id: str,
    content: str,
) -> AcpSlashResult | None:
    stripped = content.strip()
    if not stripped.startswith("/"):
        return None

    command_text = stripped[1:]
    if not command_text.strip():
        return AcpSlashResult(output="Unknown command: /.", is_error=True)

    head, _, tail = command_text.partition(" ")
    command = head.strip().lower()
    arg = tail.strip()

    if command == "wt":
        return AcpSlashResult(output=run_worktree_command(_project_dir(state, session_id), arg))
    if command in {"status", "diff", "rollback", "git"}:
        return await _handle_git_command(state, session_id, command, arg)
    if command == "undo":
        return await _handle_undo(state, session_id)
    if command == "rewind":
        return await _handle_rewind(state, session_id, arg)
    if command == "mcp":
        return await _handle_mcp(state, session_id, arg)
    if command == "schedules":
        return await _handle_schedules(state, session_id, arg)
    if command in {"delegates", "agents"}:
        return await _handle_delegates(state, session_id, arg)
    if command == "tasks":
        return await _handle_tasks(state, session_id)
    if command == "task-add":
        return await _handle_task_add(state, session_id, arg)
    if command == "task-done":
        return await _handle_task_done(state, session_id, arg)
    if command == "notes":
        return await _handle_notes(state, session_id)
    if command == "note-add":
        return await _handle_note_add(state, session_id, arg)
    return AcpSlashResult(output=f"Unknown command: /{command}.", is_error=True)


def _project_dir(state: server_mod.ServerState, session_id: str) -> str:
    return server_mod._session_project_dir(state, session_id, state.sessions.get(session_id))


async def _handle_git_command(
    state: server_mod.ServerState,
    session_id: str,
    command: str,
    arg: str,
) -> AcpSlashResult:
    subarg = arg.strip()
    if command == "status":
        subarg = "status"
    elif command == "diff":
        subarg = f"diff {subarg}".strip()
    elif command == "rollback":
        subarg = f"rollback {subarg}".strip()

    parts = subarg.split(maxsplit=1) if subarg else []
    action = parts[0].lower() if parts else "status"
    rest = parts[1].strip() if len(parts) > 1 else ""
    cwd = _project_dir(state, session_id)

    if action in {"", "status"}:
        return AcpSlashResult(output=render_git_status(cwd=cwd))
    if action == "diff":
        return AcpSlashResult(output=render_git_diff(cwd=cwd, pathspec=rest))
    if action == "rollback":
        if rest == "--all":
            message = restore_all(cwd=cwd)
            return AcpSlashResult(output=message, is_error=message.startswith("git restore failed:"))
        message = restore_path(cwd=cwd, pathspec=rest)
        return AcpSlashResult(
            output=message,
            is_error=message.startswith("Usage:") or message.startswith("git restore failed:"),
        )
    if action == "help":
        return AcpSlashResult(output=render_git_help())
    return AcpSlashResult(output=render_git_help(), is_error=True)


async def _handle_undo(state: server_mod.ServerState, session_id: str) -> AcpSlashResult:
    messages = await server_mod._session_history_messages(state, session_id)
    paths = collect_last_ai_changed_paths(messages)
    if not paths:
        return AcpSlashResult(output="No recent AI file edits found to undo.")
    message = restore_paths(cwd=_project_dir(state, session_id), paths=paths)
    if message.startswith("git restore failed:"):
        return AcpSlashResult(output=message, is_error=True)
    return AcpSlashResult(
        output="Undid latest AI file changes:\n" + "\n".join(f"- {path}" for path in paths)
    )


async def _handle_rewind(state: server_mod.ServerState, session_id: str, arg: str) -> AcpSlashResult:
    if not arg.isdigit():
        return AcpSlashResult(output="Usage: /rewind <message_index>", is_error=True)
    idx = int(arg)
    payload = await server_mod._fork_server_session(state, session_id, up_to_message_idx=idx)
    new_session_id = str(payload.get("session_id", "")).strip()
    if not new_session_id:
        return AcpSlashResult(output="Rewind failed: missing forked session id.", is_error=True)
    return AcpSlashResult(
        output=(
            f"Created rewound session fork at message {idx}.\n"
            f"New session id: {new_session_id}\n"
            "Load or resume that session in the client to continue from the rewind point."
        )
    )


async def _handle_mcp(state: server_mod.ServerState, session_id: str, arg: str) -> AcpSlashResult:
    runtime = McpRuntimeManager()
    try:
        await runtime.load(
            ExtensionContext(
                project_dir=_project_dir(state, session_id),
                runtime="server",
                config=state.config,
            )
        )
        if arg.strip().lower() == "reload":
            await runtime.reload()
        output = runtime.status_text() or "(no output)"
        return AcpSlashResult(output=output)
    finally:
        await runtime.close()


async def _handle_schedules(state: server_mod.ServerState, session_id: str, arg: str) -> AcpSlashResult:
    command = arg.strip()
    try:
        parts = shlex.split(command) if command else []
    except ValueError as exc:
        return AcpSlashResult(output=f"schedules error: {exc}", is_error=True)

    service = state.schedule_service
    temporary_service = service is None
    if service is None:
        service = server_mod.ScheduleService(state)
        await service.reload()

    try:
        if not parts or parts[0] in {"list", "ls"}:
            snapshot = service.snapshot()
            return AcpSlashResult(output=_render_schedule_list(snapshot))
        if parts[0] == "reload" and len(parts) == 1:
            snapshot = await service.reload()
            return AcpSlashResult(output=f"Reloaded schedules: {snapshot.get('count', 0)} configured")
        if parts[0] == "run" and len(parts) == 2:
            snapshot = await service.run_now(parts[1])
            return AcpSlashResult(
                output=f"Triggered schedule: {parts[1]}\nnext={snapshot.get('next_run_at', '') or '-'}"
            )
        if parts[0] == "show" and len(parts) == 2:
            snapshot = service.snapshot()
            for item in snapshot.get("schedules", []):
                schedule = item.get("schedule", {})
                if str(schedule.get("id", "")) == parts[1]:
                    return AcpSlashResult(output=json.dumps(item, indent=2, sort_keys=True))
            return AcpSlashResult(output=f"Unknown schedule: {parts[1]}", is_error=True)
        return AcpSlashResult(
            output=(
                "Usage:\n"
                "  /schedules\n"
                "  /schedules list\n"
                "  /schedules show <id>\n"
                "  /schedules run <id>\n"
                "  /schedules reload"
            ),
            is_error=True,
        )
    finally:
        if temporary_service:
            with server_mod.suppress(Exception):
                await service.stop()


async def _handle_delegates(state: server_mod.ServerState, session_id: str, arg: str) -> AcpSlashResult:
    try:
        parts = shlex.split(arg) if arg.strip() else []
    except ValueError as exc:
        return AcpSlashResult(output=f"agents error: {exc}", is_error=True)

    registry = get_delegation_registry()
    if not parts or parts[0] in {"list", "ls"}:
        rendered = format_run_list(registry.list_runs(session_id))
        if rendered.startswith("Delegates:"):
            rendered = rendered.replace("Delegates:", "Orchestration runs:", 1)
        elif rendered == "No delegates found.":
            rendered = "No orchestration runs found."
        return AcpSlashResult(output=rendered)
    if parts[0] == "show" and len(parts) == 2:
        run = registry.get_session_run(session_id, parts[1])
        if run is None:
            return AcpSlashResult(output=f"delegates error: Unknown orchestration run: {parts[1]}", is_error=True)
        rendered = format_run_detail(run)
        if rendered.startswith("Delegate:"):
            rendered = rendered.replace("Delegate:", "Orchestration run:", 1)
        return AcpSlashResult(output=rendered)
    if parts[0] == "tail" and len(parts) == 2:
        run = registry.get_session_run(session_id, parts[1])
        if run is None:
            return AcpSlashResult(output=f"delegates error: Unknown orchestration run: {parts[1]}", is_error=True)
        lines = [f"Tail for orchestration run {parts[1]}:"]
        lines.extend(f"- {item}" for item in run.events[-10:])
        if run.latest_update:
            lines.extend(["", f"Latest: {run.latest_update}"])
        return AcpSlashResult(output="\n".join(lines))
    if parts[0] == "cancel" and len(parts) == 2:
        run = registry.get_session_run(session_id, parts[1])
        if run is None:
            return AcpSlashResult(output=f"delegates error: Unknown orchestration run: {parts[1]}", is_error=True)
        cancelled = registry.cancel(run.id)
        if not cancelled:
            return AcpSlashResult(output=f"Failed to cancel orchestration run: {parts[1]}", is_error=True)
        return AcpSlashResult(output=f"Cancelled orchestration run: {parts[1]}")
    return AcpSlashResult(
        output=(
            "Usage:\n"
            "  /delegates\n"
            "  /delegates list\n"
            "  /delegates show <run_id>\n"
            "  /delegates tail <run_id>\n"
            "  /delegates cancel <run_id>\n\n"
            "Alias: /agents"
        ),
        is_error=True,
    )


async def _handle_tasks(state: server_mod.ServerState, session_id: str) -> AcpSlashResult:
    content = await read_project_board_file(tasks_path(_project_dir(state, session_id)))
    if not content.strip():
        return AcpSlashResult(output="No tasks yet.")
    return AcpSlashResult(output=render_numbered_text(content))


async def _handle_task_add(state: server_mod.ServerState, session_id: str, arg: str) -> AcpSlashResult:
    title = arg.strip()
    if not title:
        return AcpSlashResult(output="Usage: /task-add <title>", is_error=True)
    path = tasks_path(_project_dir(state, session_id))
    content = await read_project_board_file(path)
    try:
        updated, task_id = add_task_to_markdown(content, title)
    except Exception as exc:
        return AcpSlashResult(output=f"Failed to add task: {exc}", is_error=True)
    await server_mod.asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
    await server_mod.asyncio.to_thread(path.write_text, updated, encoding="utf-8")
    return AcpSlashResult(output=f"Added task #{task_id}: {title}")


async def _handle_task_done(state: server_mod.ServerState, session_id: str, arg: str) -> AcpSlashResult:
    if not arg:
        return AcpSlashResult(output="Usage: /task-done <task-id>", is_error=True)
    try:
        task_id = int(arg)
    except ValueError:
        return AcpSlashResult(output="Usage: /task-done <task-id>", is_error=True)
    path = tasks_path(_project_dir(state, session_id))
    content = await read_project_board_file(path)
    try:
        updated = update_task_in_markdown(content, task_id, status="done")
    except Exception as exc:
        return AcpSlashResult(output=f"Failed to complete task: {exc}", is_error=True)
    await server_mod.asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
    await server_mod.asyncio.to_thread(path.write_text, updated, encoding="utf-8")
    return AcpSlashResult(output=f"Completed task #{task_id}")


async def _handle_notes(state: server_mod.ServerState, session_id: str) -> AcpSlashResult:
    content = await read_project_board_file(operator_notes_path(_project_dir(state, session_id)))
    if not content.strip():
        return AcpSlashResult(output="Operator notes are empty.")
    return AcpSlashResult(output=render_numbered_text(content))


async def _handle_note_add(state: server_mod.ServerState, session_id: str, arg: str) -> AcpSlashResult:
    text = arg.strip()
    if not text:
        return AcpSlashResult(output="Usage: /note-add <text>", is_error=True)
    await append_project_board_file(operator_notes_path(_project_dir(state, session_id)), text)
    return AcpSlashResult(output="Appended operator note.")


def _render_schedule_list(snapshot: dict[str, Any]) -> str:
    schedules = snapshot.get("schedules", [])
    if not schedules:
        return "No scheduled tasks configured."
    lines = [
        "Scheduled tasks: "
        f"{snapshot.get('count', len(schedules))} total; "
        f"next={snapshot.get('next_run_at', '') or '-'}"
    ]
    for item in schedules:
        schedule = item.get("schedule", {})
        state = item.get("state", {})
        trigger = (
            f"every {schedule.get('every_seconds', 0)}s"
            if schedule.get("kind") == "interval"
            else str(schedule.get("cron", ""))
        )
        lines.append(
            f"- {schedule.get('id', '')} "
            f"[{'enabled' if schedule.get('enabled') else 'disabled'}] "
            f"{schedule.get('kind', '')}={trigger} "
            f"status={state.get('last_status', 'idle')} "
            f"next={state.get('next_run_at', '') or '-'}"
        )
    return "\n".join(lines)
