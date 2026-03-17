# Project Instructions

This file provides project-specific guidance for Artel when working in this repository.

## Project Overview

Artel is an extensible Python coding agent for local development, remote execution, and editor/server integrations.

Current primary product surfaces in this checkout:
- local TUI via `artel`
- one-shot print mode via `artel -p`
- continue/resume session workflows
- headless server via `artel serve`
- remote TUI via `artel connect`
- JSON-RPC via `artel rpc`
- ACP via `artel acp`
- rules and rule enforcement
- MCP configuration/runtime
- schedules
- orchestration/delegation
- built-in code, git, search, web, and LSP tools
- Python-native extensions

Important scope limits:
- `artel web` exists as a compatibility surface, but the full web UI/runtime is not shipped as a supported product surface in this checkout
- the old employee/dashboard model is out of scope and should not be reintroduced casually
- docs, README, and CLI help should reflect the actual shipped surfaces, not aspirational ones

Canonical scope reference:
- `PRODUCT_SCOPE.md`
- `README.md`
- `docs/product-scope.md`

## Repository Layout

Workspace packages:
- `packages/artel-ai/` — provider adapters, model abstractions, attachments, OAuth helpers
- `packages/artel-core/` — core agent logic, config, tools, rules, schedules, orchestration, MCP/LSP plumbing, CLI entrypoint
- `packages/artel-server/` — server, RPC, ACP, provider overlay, remote control-plane behavior
- `packages/artel-tui/` — Textual-based local/remote terminal UI
- `packages/artel-web/` — partial web-related code; do not assume full product parity

Other important paths:
- `tests/` — source of truth for expected behavior
- `docs/` — MkDocs content
- `extensions/` — example extension(s)
- `Artel implementation backlog v0.md` — historical backlog/spec reference
- `.artel/AGENTS.md` — this file

## Conventions

### General
- Use **Artel** naming consistently in user-facing text, docs, comments, and help output.
- Keep changes aligned with the current product scope.
- Prefer small, targeted changes over broad refactors unless the task explicitly calls for broader work.
- Prefer evidence from code and tests over assumptions.
- When changing behavior, update docs and tests in the same change when applicable.

### Python
- Python version target: **3.12**.
- Ruff line length is **100**.
- Follow existing typing style and dataclass usage patterns.
- Match the local style of the file you are editing instead of introducing a new style.
- Avoid adding unnecessary dependencies when existing workspace modules already cover the need.

### Architecture
- Put provider/model logic in `artel-ai`, not in UI/server layers.
- Put reusable domain logic in `artel-core`.
- Keep `artel-server` focused on transport/protocol/server concerns.
- Keep TUI-specific behavior in `artel-tui`.
- Do not place product-critical logic only in docs or only in UI layers; shared behavior should live in core/server as appropriate.

### Product/UX accuracy
- README, docs, CLI help, and ACP/RPC behavior should stay in sync.
- Do not overstate support for the web surface.
- Do not reintroduce the retired employee-centric product narrative unless the task explicitly requires historical validation.
- Prefer “orchestration/delegation” wording over old employee terminology for current features.

### Tests
- Always keep tests updated.
- Add or update targeted tests for any changed behavior.
- Prefer the smallest relevant test subset during iteration, but ensure affected coverage is updated.
- If you change docs that are validated by tests, update the corresponding doc tests too.

## Common Commands

### Setup
```bash
uv sync --dev
```

### Run tests
```bash
pytest -q
pytest -q tests/test_cli_smoke_matrix.py
pytest -q tests/test_acp_phase7.py tests/test_acp_protocol_integration.py
pytest -q tests/test_mcp_cli_and_runtime.py
pytest -q tests/test_schedule_cli.py tests/test_schedule_service.py
```

### Lint
```bash
ruff check .
```

### Docs
```bash
uv run mkdocs serve
```

### Run the product
```bash
uv run artel
uv run artel -p "explain this codebase"
uv run artel serve
uv run artel connect ws://127.0.0.1:7432
uv run artel acp
uv run artel rpc
```

## Change Guidance

### When editing CLI or product surfaces
Also inspect as needed:
- `packages/artel-core/src/artel_core/cli.py`
- `README.md`
- `docs/cli.md`
- `PRODUCT_SCOPE.md`
- `docs/product-scope.md`

### When editing ACP/RPC/server behavior
Also inspect as needed:
- `packages/artel-server/src/artel_server/server.py`
- `packages/artel-server/src/artel_server/rpc.py`
- `packages/artel-server/src/artel_server/acp.py`
- `tests/test_acp_phase7.py`
- `tests/test_acp_protocol_integration.py`

### When editing tools, rules, MCP, schedules, or orchestration
Also inspect related tests under `tests/`, especially:
- `tests/test_rules*.py`
- `tests/test_mcp*.py`
- `tests/test_schedule*.py`
- `tests/test_delegation*.py`
- `tests/test_orchestration*.py`
- `tests/test_worktree*.py`
- `tests/test_web_tools.py`
- `tests/test_lsp_runtime.py`

### When editing TUI behavior
Also inspect as needed:
- `packages/artel-tui/src/artel_tui/app.py`
- `packages/artel-tui/src/artel_tui/local_server.py`
- `packages/artel-tui/src/artel_tui/server_tray.py`
- relevant `tests/test_tui_*.py`

## Local State and Ignored Files

Be careful with local-only state. Do not accidentally commit local workspace data.

Examples of local/ignored paths:
- `.artel/` contents except `.artel/AGENTS.md`
- `.cursor/`
- `.neteragen/`
- `.warp/`
- other local scratch/state directories such as `.worker/` if present

Prefer committing only intentional source, test, and doc changes.

## Active Rules

These project rules are mandatory:
- Always keep tests updated.
- If a request conflicts with an active rule, do not carry it out.

## Practical Defaults

- Start by reading the smallest set of relevant files.
- Run targeted tests for the changed area before broader commands.
- Keep docs aligned with implementation.
- Avoid speculative feature claims.
- Preserve current Artel naming and product boundaries.
