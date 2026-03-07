# Configuration

Worker loads configuration from a global file and then overlays project-specific settings on top.

## Config files

- Global: `~/.config/worker/config.toml`
- Project: `.worker/config.toml`
- Project instructions: `.worker/AGENTS.md`

Run this once to generate fully commented templates:

```bash
worker init
```

## Overlay model

Project config overrides global config. This lets you keep your personal defaults globally while tightening settings or changing models per repository.

## Minimal example

```toml
[agent]
model = "openai/gpt-4.1"
temperature = 0.0
max_turns = 50

[providers.openai]
api_key = "sk-..."

[permissions]
edit = "allow"
write = "allow"
bash = "ask"
```

## Main sections

### `agent`

Controls model selection and runtime behavior.

Useful settings include:

- `model` — default `provider/model-id`
- `small_model` — optional smaller model for utility tasks
- `temperature` — response determinism vs. creativity
- `max_turns` — agent loop limit per request
- `system_prompt` — additional instruction text
- `thinking` — reasoning budget level

### `providers`

Each provider lives under its own section:

```toml
[providers.openai]
api_key = "sk-..."
base_url = "https://api.openai.com/v1"
```

Provider blocks can also carry:

- custom headers
- provider-specific options
- custom base URLs
- model metadata overrides
- platform fields such as `region`, `project`, or `location`

### `permissions`

Control how much autonomy Worker gets for file and shell operations:

```toml
[permissions]
edit = "allow"
write = "allow"
bash = "ask"

[permissions.bash_commands]
"git *" = "allow"
"rm *" = "deny"
```

Supported policy values are `allow`, `ask`, and `deny`.

### `server`

Settings for `worker serve`, including:

- `host`
- `port`
- `auth_token`
- `tls_cert`
- `tls_key`
- `max_sessions`

### `extensions`

Controls extension storage, enable and disable lists, and registry definitions.

### `sessions`

Controls the session database path and auto-compaction behavior.

### `ui`

Controls TUI-specific preferences such as theme, cost visibility, reasoning visibility, and markdown rendering.

### `keybindings`

Lets you override Textual keybindings with a simple mapping.

## Useful commands

Show config file paths:

```bash
worker config
```

Print only the global config path:

```bash
worker config --global
```

Print only the project config path:

```bash
worker config --project
```

Print the merged effective configuration:

```bash
worker config print
```
