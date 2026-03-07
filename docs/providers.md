# Providers

Worker chooses models with a `provider/model-id` string such as `anthropic/claude-sonnet-4-20250514` or `openai/gpt-4.1`.

## How provider setup works

Most providers can be configured in one of these ways:

- set credentials in `~/.config/worker/config.toml`
- use provider-specific environment variables
- use `worker login <provider>` when OAuth is supported
- rely on cloud-native credential chains for platforms such as Bedrock or Vertex AI

Example:

```toml
[agent]
model = "openai/gpt-4.1"

[providers.openai]
api_key = "sk-..."
```

## Hosted API providers

These providers usually require an API key in config or an environment variable:

- `anthropic`
- `openai`
- `google`
- `kimi`
- `azure_openai`
- `github_copilot`
- `github_copilot_enterprise`

## Cloud platform backends

These typically rely on platform credentials and extra runtime fields:

- `bedrock`
- `google_vertex`
- `vertex_anthropic`

Examples of additional settings include `region`, `profile`, `project`, and `location`.

## OpenAI-compatible providers

Worker also supports a wide range of OpenAI-compatible endpoints:

- `groq`
- `mistral`
- `xai`
- `openrouter`
- `together`
- `cerebras`
- `deepseek`
- `302ai`
- `baseten`
- `fireworks`
- `helicone`
- `io-net`
- `nebius`

These usually need `api_key` plus a provider-specific `base_url`.

## Local and self-hosted providers

Worker includes integrations for local or self-hosted runtimes:

- `ollama`
- `ollama_cloud`
- `lmstudio`
- `llama.cpp`

These providers often use a local base URL and may not require an API key.

## OAuth login

Some providers support interactive login:

```bash
worker login <provider>
```

If a provider does not support OAuth, Worker will tell you which environment variable or config key to use instead.

## Tips

- Keep `agent.model` in `provider/model-id` format.
- Prefer environment variables for secrets on shared machines or CI.
- Use project config to override the global provider or model per repository.
- Set custom `base_url` values when routing through proxies or self-hosted gateways.
