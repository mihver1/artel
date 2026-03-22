# Artel Web

`artel web` starts an experimental NiceGUI-based Artel cockpit.

Current focus areas:

- follow-first coding workflow instead of generic chat-only layout
- parallel sessions with quick switching
- live WebSocket streaming from the Artel server
- control-plane visibility for providers, schedules, prompts, skills, rules, and delegates
- editable shared task board and operator notes alongside the active session

Example:

```bash
artel web
artel web --port 8843
artel web --remote-url ws://host:7432 --token <bearer-token>
```

Current limitations:

- experimental quality; expect iteration
- not yet at feature parity with the TUI
- optimized for server-backed operation and orchestration visibility first
