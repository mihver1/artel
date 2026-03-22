# CLI reference

This page summarizes the main commands exposed by the `artel` CLI.

## Top-level usage

```bash
artel [OPTIONS] [COMMAND]
```

Top-level options:

- `-p, --prompt TEXT` — run a one-shot prompt in print mode
- `-c, --continue` — continue the most recent session
- `-r, --resume TEXT` — resume a specific session by ID

## Core commands

### `artel`

Starts the local TUI when you do not provide a subcommand or `--prompt`.

### `artel init`

Creates:

- `~/.config/artel/config.toml`
- `.artel/config.toml`
- `.artel/AGENTS.md`

### `artel serve`

Starts the headless server daemon.

Options:

- `--host TEXT`
- `--port INTEGER`

### `artel connect URL`

Connects the TUI to a remote Artel server.

Options:

- `--token TEXT`
- `--forward-credentials TEXT`

### `artel web`

Starts the experimental NiceGUI-based Artel web UI.

Options:

- `--host TEXT`
- `--port INTEGER`
- `--remote-url TEXT`
- `--token TEXT`
- `--native`
- `--no-open-browser`

### `artel config`

Shows config file paths.

Options:

- `--global`
- `--project`

Subcommands:

- `artel config print` — print merged effective config as TOML

### `artel rpc`

Starts a JSON-RPC server on stdin and stdout for embedding scenarios.

### `artel acp`

Starts an ACP agent on stdin and stdout for ACP-compatible clients.
See [ACP integration](acp.md) for session behavior, supported controls, and permission flow details.

### `artel login PROVIDER`

Attempts OAuth login for a supported provider.

## Extension commands

### `artel ext install SOURCE`

Install an extension from a name, URL, or local path.

### `artel ext list`

List installed extensions.

### `artel ext remove NAME`

Remove an installed extension.

### `artel ext update [NAME]`

Update one extension or all installed extensions.

### `artel ext search QUERY`

Search configured extension registries.

### `artel ext registry list`

List configured extension registries.

### `artel ext registry add NAME URL`

Add a custom registry.

### `artel ext registry remove NAME`

Remove a custom registry.

## Useful examples

```bash
artel -p "review the latest changes"
artel --continue
artel --resume 7f1f7f80-0000-0000-0000-000000000000
artel serve --host 0.0.0.0 --port 7432
artel connect ws://example.com:7432 --token artel_example
artel web --port 8843
artel config print
artel ext search git
```
