"""Configuration system — Pydantic models, TOML loading, template generation."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any, Literal

import tomli_w
from pydantic import BaseModel, Field

# ── Config paths ──────────────────────────────────────────────────

CONFIG_DIR = Path(os.environ.get("WORKER_CONFIG_DIR", "~/.config/worker")).expanduser()
GLOBAL_CONFIG = CONFIG_DIR / "config.toml"
AUTH_FILE = CONFIG_DIR / "auth.json"


# ── Pydantic models ──────────────────────────────────────────────


class AgentConfig(BaseModel):
    model: str = "anthropic/claude-sonnet-4-20250514"
    small_model: str = ""  # utility model for compaction, auto-title, etc.
    temperature: float = 0.0
    max_turns: int = 50
    system_prompt: str = ""
    thinking: str = "off"  # off | minimal | low | medium | high | xhigh

class ProviderModelConfig(BaseModel):
    name: str | None = None
    context_window: int | None = None
    max_output_tokens: int | None = None
    supports_tools: bool | None = None
    supports_vision: bool | None = None
    supports_reasoning: bool | None = None
    input_price_per_m: float | None = None
    output_price_per_m: float | None = None
    disabled: bool = False
    headers: dict[str, str] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
    variants: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    type: str = ""
    name: str = ""
    api_key: str = ""
    base_url: str = ""
    api_type: str = ""
    region: str = ""
    profile: str = ""
    api_version: str = ""
    project: str = ""
    location: str = ""
    env: list[str] = Field(default_factory=list)
    headers: dict[str, str] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
    timeout: int | bool | None = None  # milliseconds; false disables the timeout
    whitelist: list[str] = Field(default_factory=list)
    blacklist: list[str] = Field(default_factory=list)
    models: dict[str, ProviderModelConfig] = Field(default_factory=dict)
    requires_api_key: bool | None = None


class PermissionsConfig(BaseModel):
    edit: Literal["allow", "ask", "deny"] = "allow"
    write: Literal["allow", "ask", "deny"] = "allow"
    bash: Literal["allow", "ask", "deny"] = "ask"
    bash_commands: dict[str, Literal["allow", "ask", "deny"]] = Field(default_factory=dict)


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 7432
    auth_token: str = ""
    tls_cert: str = ""
    tls_key: str = ""
    max_sessions: int = 10


OFFICIAL_REGISTRY_URL = (
    "https://raw.githubusercontent.com/mihver1/worker-agent/main/registry/extensions.toml"
)


class RegistryConfig(BaseModel):
    name: str = ""
    url: str = ""


class ExtensionsConfig(BaseModel):
    dir: str = str(CONFIG_DIR / "extensions")
    enabled: list[str] = Field(default_factory=list)
    disabled: list[str] = Field(default_factory=list)
    registries: list[RegistryConfig] = Field(
        default_factory=lambda: [
            RegistryConfig(name="official", url=OFFICIAL_REGISTRY_URL),
        ]
    )


class SessionsConfig(BaseModel):
    db_path: str = str(CONFIG_DIR / "sessions.db")
    auto_compact: bool = True
    compact_threshold: float = 0.8


class UIConfig(BaseModel):
    theme: str = "dark"
    show_cost: bool = True
    show_reasoning: bool = True
    render_markdown: bool = True


class KeybindingsConfig(BaseModel):
    """Custom keybindings — keys are Textual key strings, values are action names."""

    bindings: dict[str, str] = Field(default_factory=dict)


class WorkerConfig(BaseModel):
    agent: AgentConfig = Field(default_factory=AgentConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    permissions: PermissionsConfig = Field(default_factory=PermissionsConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    extensions: ExtensionsConfig = Field(default_factory=ExtensionsConfig)
    sessions: SessionsConfig = Field(default_factory=SessionsConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    keybindings: KeybindingsConfig = Field(default_factory=KeybindingsConfig)


# ── Load config ───────────────────────────────────────────────────


def load_config(project_dir: str | None = None) -> WorkerConfig:
    """Load config: global → project overlay."""
    config = WorkerConfig()

    # Global config
    if GLOBAL_CONFIG.exists():
        with open(GLOBAL_CONFIG, "rb") as f:
            data = tomllib.load(f)
        config = WorkerConfig.model_validate(data)

    # Project config overlay
    if project_dir:
        project_config = Path(project_dir) / ".worker" / "config.toml"
        if project_config.exists():
            with open(project_config, "rb") as f:
                project_data = tomllib.load(f)
            # Merge: project overrides global
            merged = config.model_dump()
            _deep_merge(merged, project_data)
            config = WorkerConfig.model_validate(merged)

    return config


def persist_server_auth_token(token: str, project_dir: str | None = None) -> Path:
    """Persist server auth token to the config file that owns the effective setting."""
    target = GLOBAL_CONFIG
    data: dict[str, Any] = {}

    if GLOBAL_CONFIG.exists():
        with open(GLOBAL_CONFIG, "rb") as f:
            data = tomllib.load(f)

    if project_dir:
        project_config = Path(project_dir) / ".worker" / "config.toml"
        if project_config.exists():
            with open(project_config, "rb") as f:
                project_data = tomllib.load(f)
            project_server = project_data.get("server")
            if isinstance(project_server, dict) and "auth_token" in project_server:
                target = project_config
                data = project_data

    server_data = data.get("server")
    if not isinstance(server_data, dict):
        server_data = {}
        data["server"] = server_data
    server_data["auth_token"] = token

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(tomli_w.dumps(data), encoding="utf-8")
    return target


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# ── Resolve provider and model from "provider/model-id" format ───


def resolve_model(config: WorkerConfig) -> tuple[str, str]:
    """Parse 'provider/model-id' into (provider_name, model_id)."""
    model_str = config.agent.model
    if "/" in model_str:
        provider, model = model_str.split("/", 1)
        return provider, model
    return "anthropic", model_str


# ── Template generation ───────────────────────────────────────────

_GLOBAL_TEMPLATE = """\
# ═══════════════════════════════════════════════════════════════
# Worker — global configuration
# Documentation: https://github.com/worker-agent/worker#config
# ═══════════════════════════════════════════════════════════════

# ── Agent ─────────────────────────────────────────────────────
[agent]
# Model in provider/model-id format
# Examples:
#   "anthropic/claude-sonnet-4-20250514"
#   "openai/gpt-4.1"
#   "azure_openai/gpt-4.1"
#   "bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0"
#   "kimi/kimi-k2.5"
#   "google/gemini-2.5-pro"
#   "google_vertex/gemini-2.5-pro"
#   "vertex_anthropic/claude-sonnet-4@20250514"
#   "github_copilot/gpt-4.1"
#   "ollama/qwen3:32b"
model = "anthropic/claude-sonnet-4-20250514"

# Generation temperature (0.0 = deterministic, 1.0 = creative)
# temperature = 0.0

# Maximum number of agent-loop iterations per request
# max_turns = 50

# System prompt (appended to the built-in prompt)
# You can also use .worker/AGENTS.md in the project
# system_prompt = "You are a senior Python developer."

# Small model for utility tasks (compaction, auto-titles)
# Format: provider/model-id  (empty string = use the main model)
# Examples: "anthropic/claude-haiku-3" | "openai/gpt-4.1-mini"
# small_model = ""

# Extended thinking / reasoning
# off — disabled
# minimal | low | medium | high | xhigh — budget levels
# Anthropic: budget_tokens (1024..16384)
# OpenAI o-series: reasoning_effort (low/medium/high)
# thinking = "off"

# ── Providers
# Each provider is a separate [providers.<name>] section
# type: anthropic | openai | openai_compat | kimi | google | google_vertex
#       | vertex_anthropic
#       | bedrock | azure_openai | github_copilot | ollama | lmstudio | huggingface
#
# Authentication usually uses api_key;
# OAuth is available only for some providers (`worker login <provider>`)
# Environment variables also work:
#   ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, MOONSHOT_API_KEY,
#   AZURE_OPENAI_API_KEY, GH_TOKEN, GITHUB_TOKEN,
#   GROQ_API_KEY, MISTRAL_API_KEY, XAI_API_KEY,
#   TOGETHER_API_KEY, CEREBRAS_API_KEY, DEEPSEEK_API_KEY,
#   OPENROUTER_API_KEY, OLLAMA_API_KEY, HF_API_KEY

# [providers.anthropic]
# type = "anthropic"
# api_key = "sk-ant-..."         # or ANTHROPIC_API_KEY env
# # base_url = "https://api.anthropic.com"  # override if you need a proxy
# # [providers.anthropic.options]
# # beta_headers = ["files-api-2025-04-14"]
# # interleaved_thinking = true
# # fine_grained_tool_streaming = true
# # OAuth login for anthropic automatically uses Claude Code-style headers/tool naming

# [providers.openai]
# type = "openai"
# api_key = "sk-..."             # or OPENAI_API_KEY env
# # base_url = "https://api.openai.com/v1"
# # api_type = "chat"            # "chat" (completions) | "responses"

# [providers.kimi]
# type = "kimi"
# api_key = "sk-..."             # or MOONSHOT_API_KEY env
# # base_url = "https://api.kimi.com/coding/v1"
# # Kimi For Coding uses an Anthropic-compatible messages endpoint

# [providers.google]
# type = "google"
# api_key = "..."                # or GEMINI_API_KEY env

# [providers.google_vertex]
# type = "google_vertex"
# # project = "my-gcp-project"   # or GOOGLE_VERTEX_PROJECT / GOOGLE_CLOUD_PROJECT
# # location = "us-central1"     # default: global; also GOOGLE_VERTEX_LOCATION
# # [providers.google_vertex.options]
# # credentials_path = "/path/to/service-account.json"  # otherwise ADC is used
# # scopes = ["https://www.googleapis.com/auth/cloud-platform"]

# [providers.vertex_anthropic]
# type = "vertex_anthropic"
# # project = "my-gcp-project"
# # location = "us-east5"
# # [providers.vertex_anthropic.options]
# # credentials_path = "/path/to/service-account.json"
# # beta_headers = ["files-api-2025-04-14"]

# [providers.groq]
# type = "openai_compat"
# api_key = "gsk_..."
# base_url = "https://api.groq.com/openai/v1"

# [providers.mistral]
# type = "openai_compat"
# api_key = "..."
# base_url = "https://api.mistral.ai/v1"

# [providers.xai]
# type = "openai_compat"
# api_key = "xai-..."
# base_url = "https://api.x.ai/v1"

# [providers.openrouter]
# type = "openai_compat"
# api_key = "sk-or-..."
# base_url = "https://openrouter.ai/api/v1"
# # timeout = 300000               # milliseconds; false = no timeout
# # [providers.openrouter.headers]
# # "HTTP-Referer" = "https://example.com"
# # "X-Title" = "worker"

# [providers.together]
# type = "openai_compat"
# api_key = "..."
# base_url = "https://api.together.xyz/v1"

# [providers.cerebras]
# type = "openai_compat"
# api_key = "..."
# base_url = "https://api.cerebras.ai/v1"

# [providers.deepseek]
# type = "openai_compat"
# api_key = "sk-..."
# base_url = "https://api.deepseek.com/v1"

# [providers.huggingface]
# type = "huggingface"
# api_key = "hf_..."

# [providers.ollama]
# type = "ollama"
# # base_url = "http://localhost:11434/v1"  # default OpenAI-compatible endpoint
# # requires_api_key = false
# # `/models` fetches the model list directly from the Ollama API.
# # Models can also be referenced directly as ollama/<model-id>; to show them in /models,
# # define them in the section below.
# # [providers.ollama.models."qwen3:32b"]
# # name = "Qwen3 32B"
# # context_window = 131072

# [providers.ollama_cloud]
# type = "ollama"
# # api_key = "ollama_..."         # or OLLAMA_API_KEY env
# # base_url = "https://ollama.com/v1"
# # `/models` fetches the model list directly from the Ollama Cloud API.
# # Hosted Ollama uses the same OpenAI-compatible runtime as local Ollama.
# # [providers.ollama_cloud.models."gpt-oss:20b"]
# # name = "gpt-oss 20B via Ollama Cloud"
# # context_window = 200000

# [providers.lmstudio]
# type = "lmstudio"
# # base_url = "http://127.0.0.1:1234/v1"
# # requires_api_key = false        # if auth is enabled in LM Studio, you can set api_key
# # `/models` fetches the model list directly from the LM Studio API.
# # Models can also be referenced directly as lmstudio/<model-id>; to show them in /models,
# # define them in the section below.
# # [providers.lmstudio.models."openai/gpt-oss-20b"]
# # name = "LM Studio gpt-oss-20b"
# # context_window = 131072

# [providers.bedrock]
# type = "bedrock"
# # region = "us-east-1"
# # profile = "default"           # AWS profile from ~/.aws/credentials
# # base_url = "https://bedrock-runtime.us-east-1.amazonaws.com"  # optional custom endpoint
# # Credentials can come from the AWS credential chain (env/shared config/SSO/etc.)
# # [providers.bedrock.options]
# # access_key_id = "AKIA..."
# # secret_access_key = "..."
# # session_token = "..."          # optional STS session token

# [providers.azure_openai]
# type = "azure_openai"
# api_key = "..."
# base_url = "https://<resource>.openai.azure.com"
# # api_version = "2024-10-21"
# # api_type = "chat"            # "chat" for deployment path, "responses" for /openai/v1/responses

# [providers.github_copilot]
# type = "github_copilot"
# # api_key = "github_pat_..."    # or `worker login github_copilot`
# #                              # or COPILOT_GITHUB_TOKEN / GH_TOKEN / GITHUB_TOKEN
# # interactive login requires `gh` (`brew install gh` on macOS/Homebrew)
# # base_url = "https://api.githubcopilot.com"

# [providers.github_copilot_enterprise]
# type = "github_copilot"
# # api_key = "github_pat_..."    # or `worker login github_copilot_enterprise`
# # interactive login requires `gh` (`brew install gh` on macOS/Homebrew)
# # base_url = "https://api.githubcopilot.com"
# # [providers.github_copilot_enterprise.options]
# # github_host = "SUBDOMAIN.ghe.com"  # or GH_HOST for enterprise auth lookup via gh

# ── Permissions ───────────────────────────────────────────────
[permissions]
# Policy for each tool: "allow" | "ask" | "deny"
# "ask" — the agent requests confirmation before executing

# File editing
edit = "allow"

# File creation/overwrite
write = "allow"

# Shell command execution
bash = "ask"

# Rules for specific bash commands (glob patterns)
# The last matching rule wins
# [permissions.bash_commands]
# "git *" = "allow"
# "npm *" = "allow"
# "rm *" = "deny"
# "sudo *" = "deny"

# ── Server ────────────────────────────────────────────────────
[server]
# Host and port for `worker serve`
# host = "0.0.0.0"
# port = 7432

# Bearer token for client authentication
# Generated automatically on the first `worker serve`
# auth_token = "wkr_..."

# TLS (optional, reverse proxy recommended)
# tls_cert = "/path/to/cert.pem"
# tls_key = "/path/to/key.pem"

# Maximum concurrent sessions
# max_sessions = 10

# ── Extensions ────────────────────────────────────────────────
[extensions]
# Directory for installed extensions
# dir = "~/.config/worker/extensions"

# Enabled extensions (by name)
# enabled = ["worker-ext-websearch", "worker-ext-git"]

# Disabled extensions
# disabled = []

# Extension registries (official is enabled by default)
# Add a company or community registry:
#   worker ext registry add mycompany https://example.com/extensions.toml
# [[extensions.registries]]
# name = "official"
# url = "https://raw.githubusercontent.com/mihver1/worker-agent/main/registry/extensions.toml"

# ── Sessions ──────────────────────────────────────────────────
[sessions]
# Path to the sessions database
# db_path = "~/.config/worker/sessions.db"

# Auto-compaction near the context limit
# auto_compact = true

# Compaction threshold (fraction of the context window)
# compact_threshold = 0.8

# ── UI ────────────────────────────────────────────────────────
[ui]
# Theme: "dark" | "light" | "monokai" | "dracula"
# theme = "dark"

# Show token cost
# show_cost = true

# Show reasoning/thinking blocks
# show_reasoning = true

# Markdown rendering in the TUI
# render_markdown = true
"""

_PROJECT_TEMPLATE = """\
# ═══════════════════════════════════════════════════════════════
# Worker — project configuration (overrides global settings)
# ═══════════════════════════════════════════════════════════════

# [agent]
# model = "anthropic/claude-sonnet-4-20250514"
# temperature = 0.0
# max_turns = 50

# [permissions]
# edit = "allow"
# write = "allow"
# bash = "ask"
# [permissions.bash_commands]
# "git *" = "allow"
# "make *" = "allow"
"""

_AGENTS_MD_TEMPLATE = """\
# Project Instructions

<!-- Worker loads this file as additional system prompt context. -->
<!-- Add project-specific instructions, conventions, common commands here. -->

## Project Overview

<!-- Describe what this project does -->

## Conventions

<!-- Code style, naming, testing approach, etc. -->

## Common Commands

<!-- Build, test, lint commands for this project -->
"""


def generate_global_config() -> None:
    """Create ~/.config/worker/config.toml with the fully-commented template."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not GLOBAL_CONFIG.exists():
        GLOBAL_CONFIG.write_text(_GLOBAL_TEMPLATE, encoding="utf-8")


def generate_project_config(project_dir: str) -> None:
    """Create .worker/config.toml and .worker/AGENTS.md in the project."""
    worker_dir = Path(project_dir) / ".worker"
    worker_dir.mkdir(parents=True, exist_ok=True)

    config_path = worker_dir / "config.toml"
    if not config_path.exists():
        config_path.write_text(_PROJECT_TEMPLATE, encoding="utf-8")

    agents_path = worker_dir / "AGENTS.md"
    if not agents_path.exists():
        agents_path.write_text(_AGENTS_MD_TEMPLATE, encoding="utf-8")
