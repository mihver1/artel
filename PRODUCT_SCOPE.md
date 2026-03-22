# Product scope

This document is the canonical source of truth for which Artel surfaces are supported in the current checkout.

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

## Experimental / partial

- macOS server-tray companion flow (`artel server-tray`)
- NiceGUI-based `artel web` surface for follow-first orchestration, parallel sessions, and control-plane visibility; functional but not yet at TUI parity

## Out of current scope

- a full web-first product strategy
- a desktop app as a primary surface
- the old employee/dashboard model as a core product axis
- parity with broader multi-surface products in a single step

## Notes

- `artel web` is available as an experimental surface built on NiceGUI and the existing Artel server control plane.
- This document should stay aligned with README, CLI help, and the docs site.
