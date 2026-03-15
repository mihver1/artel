# Product scope

This page describes which Artel surfaces are supported in the current checkout.

## Supported now

- local TUI via `artel`
- one-shot print mode via `artel -p`
- continue/resume session flow
- headless server via `artel serve`
- remote TUI via `artel connect`
- JSON-RPC via `artel rpc`
- ACP via `artel acp`
- rules and rule enforcement
- MCP configuration and runtime basics
- schedules
- built-in worktree/search/web tools
- orchestration/delegation tools
- Python-native extensions

## Unavailable in this checkout

- full web UI runtime behind `artel web`

The `artel web` command is still present as a compatibility surface, but the current checkout does not ship the full web implementation. Running it will fail with an explanatory runtime error.

## Notes

This scope reflects the current repository state and should stay aligned with README, CLI help, and the docs site.
