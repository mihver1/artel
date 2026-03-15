# Run modes

Artel supports four primary user-facing run modes today: print mode, local TUI mode, headless server mode, and remote TUI mode. For embedding and editor integrations, it also exposes RPC and ACP over stdio.

## Print mode

Use print mode for scripting, shell pipelines, and quick one-off prompts.

```bash
artel -p "generate a changelog entry for the latest commit"
```

Useful when:

- integrating Artel into scripts
- piping file content into a prompt
- getting a single response without opening the TUI

## Local TUI mode

Run the interactive TUI and the agent in the same process:

```bash
artel
```

This is the default mode when no subcommand or prompt flag is provided.

## Server mode

Run a headless Artel daemon that accepts remote connections:

```bash
artel serve
```

You can override the bind address and port:

```bash
artel serve --host 0.0.0.0 --port 7432
```

Use server mode when:

- the agent should run on a remote machine
- you want a long-lived daemon
- the client UI and agent runtime should live on different hosts

## Remote TUI mode

Connect the local TUI to a remote Artel server:

```bash
artel connect ws://host:7432
```

Useful flags:

```bash
artel connect ws://host:7432 --token <bearer-token>
artel connect ws://host:7432 --forward-credentials all
artel connect ws://host:7432 --forward-credentials anthropic,openai
```

Remote mode is useful when you want a lightweight local UI while the agent executes elsewhere.

## Continue and resume sessions

Continue the most recent session:

```bash
artel --continue
```

Resume a specific session:

```bash
artel --resume <session-id>
```

These flags apply to both print mode and the default TUI mode.

## RPC mode

If you need to embed Artel in another process, you can run a JSON-RPC server over stdin and stdout:

```bash
artel rpc
```

## ACP mode

If you need an ACP-compatible client to drive Artel over stdin and stdout, run:

```bash
artel acp
```

This mode is intended for editors, IDEs, and other frontends that speak the Agent Client Protocol.
See [ACP integration](acp.md) for the supported session lifecycle, permission modes, and per-session configuration options.

## Unavailable web surface in this checkout

The CLI still exposes `artel web`, but the current repository checkout does not include the full web UI runtime. Treat it as a reserved compatibility command rather than a supported run mode.
