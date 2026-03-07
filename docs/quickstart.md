# Quick start

This guide gets you from a fresh install to a usable local Worker session.

## 1. Initialize configuration

```bash
worker init
```

Worker uses two config layers:

- global config in `~/.config/worker/config.toml`
- project overrides in `.worker/config.toml`

## 2. Configure a model provider

Set your default model in `provider/model-id` format:

```toml
[agent]
model = "anthropic/claude-sonnet-4-20250514"
```

Then add credentials either through environment variables or the provider section in your config:

```toml
[providers.anthropic]
api_key = "sk-ant-..."
```

You can also keep secrets out of the config file and rely on provider-specific environment variables such as `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.

## 3. Run a one-shot prompt

Use print mode when you want a single answer in a shell pipeline or script:

```bash
worker -p "summarize the architecture of this project"
```

Piped stdin is appended to the prompt automatically:

```bash
cat pyproject.toml | worker -p "explain the dependency layout"
```

## 4. Start the interactive TUI

Launch local interactive mode with:

```bash
worker
```

This runs the TUI and the agent in the same process, which is the simplest mode for normal local development.

## 5. Continue or resume work

Resume the last session:

```bash
worker --continue
```

Resume a specific session by ID:

```bash
worker --resume <session-id>
```

Both flags also work with print mode.

## 6. Inspect your effective setup

Check which config files exist:

```bash
worker config
```

Print the merged configuration:

```bash
worker config print
```

Next steps:

- Read [Configuration](configuration.md) to fine-tune permissions, providers, and UI behavior.
- Read [Run modes](run-modes.md) if you want to split the server and client across machines.
- Read [Extensions](extensions.md) if you want to add custom capabilities.
