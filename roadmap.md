# Artel roadmap

Actionable roadmap based on the current product analysis.

## Product direction

**Target position:**

Artel is a **Python-native coding-agent platform** for local and remote development with:

- terminal-first workflows
- strong policy/rules
- inspectable server/control-plane APIs
- MCP interoperability
- automation/schedules
- practical agent/subagent workflows

**Explicit near-term non-goals:**

- employee/dashboard model as a core product axis
- web-first product strategy
- desktop app
- full parity with OpenCode breadth in one step

---

# Phase 1 — Fix trust and product reality

**Priority:** Highest  
**Horizon:** 1–2 weeks

## 1.1 README/docs/runtime parity
- [ ] Remove or soften claims that do not match the current checkout
- [ ] Reframe README around actually working surfaces: local TUI, print mode, server, remote connect, ACP/RPC, rules, MCP, worktree, delegation, schedules
- [ ] Decide how `artel web` should be presented:
  - [ ] hide from docs/help until real implementation exists, or
  - [ ] mark as unavailable in this checkout, or
  - [ ] ship a real working implementation
- [ ] Update CLI docs in `docs/cli.md`
- [ ] Update run mode docs in `docs/run-modes.md`
- [ ] Update README examples to only include verified flows

**Acceptance criteria**
- [ ] A clean checkout does not contradict README claims
- [ ] All documented top-level commands are either working or explicitly marked experimental/unavailable

## 1.2 Supported surface declaration
- [ ] Add `PRODUCT_SCOPE.md` or equivalent README section
- [ ] Define three categories:
  - [ ] supported now
  - [ ] experimental
  - [ ] out of current scope
- [ ] List all top-level surfaces under those categories

**Acceptance criteria**
- [ ] Contributors can tell what Artel promises users today
- [ ] Out-of-scope legacy ideas do not leak into product messaging

## 1.3 Smoke matrix for user-facing entrypoints
- [ ] Add a smoke checklist or automated smoke test matrix for:
  - [ ] `artel`
  - [ ] `artel -p`
  - [ ] `artel serve`
  - [ ] `artel connect`
  - [ ] `artel mcp ...`
  - [ ] `artel schedule ...`
  - [ ] `artel rules`
  - [ ] `artel ext ...`
- [ ] Document expected outcomes for each

**Acceptance criteria**
- [ ] Every primary entrypoint has a verified expected behavior
- [ ] Breakages are caught before docs drift again

---

# Phase 2 — Strengthen the terminal coding loop

**Priority:** Highest  
**Horizon:** 2–4 weeks

## 2.1 Git-centric workflow improvements
- [ ] Add first-class pending diff summary flow
- [ ] Add first-class changed-files summary flow
- [ ] Add optional auto-commit mode
- [ ] Add “undo last AI change” / rollback workflow
- [ ] Add better post-edit git status presentation
- [ ] Add structured diff summaries to server API where useful

**Acceptance criteria**
- [ ] User can request changes, inspect resulting diff, commit, and roll back without manual glue
- [ ] Core git workflows are productized, not just bash-based

## 2.2 Test/lint repair loop
- [ ] Add first-class “run tests” action
- [ ] Add first-class “run linter” action
- [ ] Add “fix failing tests” workflow
- [ ] Add “fix lint errors” workflow
- [ ] Detect common test/lint tools automatically where possible
- [ ] Compactly summarize failures for the agent
- [ ] Add retry loop support for repair cycles

**Acceptance criteria**
- [ ] Artel can run tests, interpret failures, edit code, and rerun tests in one coherent loop
- [ ] There are tests covering at least one happy-path repair cycle

## 2.3 Better context intake and focusing
- [ ] Improve codebase context selection before edits
- [ ] Add a stronger “relevant files” discovery flow
- [ ] Add architecture/exploration summaries that reduce unnecessary reads
- [ ] Improve focused-context heuristics for unknown repos
- [ ] Add regression tests for context selection quality

**Acceptance criteria**
- [ ] Fewer irrelevant file reads during common coding tasks
- [ ] Better first-pass answers in unfamiliar repositories

---

# Phase 3 — Evolve delegation into a real agent system

**Priority:** Highest  
**Horizon:** 3–6 weeks

## 3.1 First-class agent registry
- [ ] Introduce explicit agent definitions
- [ ] Add built-in agent types such as:
  - [ ] `readonly`
  - [ ] `generalist`
  - [ ] `investigator`
  - [ ] `executor`
- [ ] Define per-agent properties:
  - [ ] name
  - [ ] description
  - [ ] allowed tools
  - [ ] mode
  - [ ] model policy
  - [ ] max turns
  - [ ] max runtime

**Acceptance criteria**
- [ ] Agent behavior is driven by explicit definitions, not only ad-hoc prompt composition
- [ ] Different agent types are observable in code and tests

## 3.2 Replace thin delegation UX with named agents
- [ ] Extend `delegate_task` semantics to support named agent profiles
- [ ] Add user-facing commands for delegating to specific agent types
- [ ] Add tool restrictions per agent profile
- [ ] Add readonly/inherit distinctions where appropriate

**Acceptance criteria**
- [ ] Delegation becomes understandable as “send to X agent”, not only “spawn another run”
- [ ] Tests cover different agent-mode behaviors

## 3.3 Structured agent result contracts
- [ ] Define structured delegate result shape with fields such as:
  - [ ] summary
  - [ ] findings
  - [ ] changed files
  - [ ] commands run
  - [ ] unresolved blockers
- [ ] Return structured payloads through server APIs
- [ ] Keep human-readable summaries for TUI/CLI output

**Acceptance criteria**
- [ ] Delegate outcomes are machine-readable and operator-friendly
- [ ] Server clients do not need to parse arbitrary text blobs

## 3.4 Complete agent lifecycle controls
- [ ] Support spawn
- [ ] Support list
- [ ] Support inspect
- [ ] Support cancel
- [ ] Support retry
- [ ] Support fork-from-context or rerun-with-context
- [ ] Expose lifecycle across:
  - [ ] built-in tools
  - [ ] TUI commands
  - [ ] server API

**Acceptance criteria**
- [ ] Delegated runs can be fully managed from local and remote surfaces

---

# Phase 4 — MCP 2.0

**Priority:** Very high  
**Horizon:** 4–8 weeks

## 4.1 Rich MCP server state model
- [ ] Introduce normalized server states:
  - [ ] connected
  - [ ] disabled
  - [ ] failed
  - [ ] needs_auth
  - [ ] timeout
  - [ ] unavailable
- [ ] Return structured MCP status data in CLI and server API
- [ ] Improve `artel mcp status` output formatting

**Acceptance criteria**
- [ ] MCP status is actionable and consistent across CLI and API

## 4.2 Remote MCP auth lifecycle
- [ ] Add auth-required remote MCP flow support
- [ ] Add credential storage model
- [ ] Add reconnect-after-auth behavior
- [ ] Add auth removal/logout support
- [ ] Decide whether OAuth is in scope for v1 MCP parity

**Acceptance criteria**
- [ ] Remote MCP auth can be completed without manual file surgery
- [ ] At least one end-to-end auth-required integration test exists

## 4.3 MCP prompt/resource parity
- [ ] Expand MCP UX beyond tools to include:
  - [ ] prompts
  - [ ] resources
  - [ ] visibility/filtering controls
  - [ ] prefixing rules
- [ ] Add inventory/status display for those surfaces

**Acceptance criteria**
- [ ] Artel can inspect and expose MCP prompts/resources in a first-class way

## 4.4 MCP runtime hardening
- [ ] Add reconnect behavior where appropriate
- [ ] Add timeout controls per server
- [ ] Capture stderr/logs for diagnostics
- [ ] Improve config validation and error messages
- [ ] Ensure one bad MCP server does not poison the whole runtime bootstrap

**Acceptance criteria**
- [ ] MCP failures degrade gracefully
- [ ] Error messages explain what the operator should do next

---

# Phase 5 — Turn server/control plane into a real advantage

**Priority:** Very high  
**Horizon:** 4–8 weeks

## 5.1 Stabilize remote session lifecycle
- [ ] Make remote sessions first-class for:
  - [ ] create
  - [ ] resume
  - [ ] inspect
  - [ ] delete
  - [ ] compact
  - [ ] fork
  - [ ] reload runtime
- [ ] Verify parity between local and remote behaviors where intended
- [ ] Improve API consistency and error contracts

**Acceptance criteria**
- [ ] Remote clients can manage sessions as reliably as local clients
- [ ] Session APIs are documented and test-covered

## 5.2 Add session export/import
- [ ] Implement session export as JSON
- [ ] Implement session import from JSON
- [ ] Optionally support transcript export formats
- [ ] Add compatibility/versioning rules for exported data

**Acceptance criteria**
- [ ] Sessions can be moved between Artel instances or machines
- [ ] Export/import round-trip is tested

## 5.3 Better diagnostics surface
- [ ] Add or improve endpoints for:
  - [ ] effective config
  - [ ] runtime health
  - [ ] MCP status
  - [ ] provider readiness
  - [ ] schedule status
  - [ ] active delegate status
- [ ] Make diagnostics easy to inspect from CLI

**Acceptance criteria**
- [ ] Operators can answer “why is this not working?” without deep code inspection

---

# Phase 6 — Make the extension model strategic

**Priority:** High  
**Horizon:** 6–10 weeks

## 6.1 Clarify built-ins vs third-party extensions
- [ ] Explicitly separate:
  - [ ] bundled features
  - [ ] installable extensions
  - [ ] experimental extensions
- [ ] Update `artel ext list` output to show category/source/type
- [ ] Reflect this separation in docs

**Acceptance criteria**
- [ ] Users can clearly tell what ships with Artel and what is external

## 6.2 Add a skill layer or equivalent reusable capability layer
- [ ] Define lightweight reusable “skills” or policy/prompt packs
- [ ] Support global and project scope
- [ ] Allow skills to affect prompting, commands, and behavior without custom Python code

**Acceptance criteria**
- [ ] Common reusable workflows no longer require full extension packaging

## 6.3 Improve extension trust model
- [ ] Add extension trust prompts/consent model
- [ ] Add extension permission scopes where needed
- [ ] Validate registry metadata more strictly
- [ ] Improve safety messaging around extension install/enable

**Acceptance criteria**
- [ ] Extension installation is safer and easier to reason about in sensitive repos

---

# Phase 7 — Turn rules/policy into a category advantage

**Priority:** High  
**Horizon:** Parallel

## 7.1 Policy packs
- [ ] Add reusable policy packs such as:
  - [ ] repo standards pack
  - [ ] security pack
  - [ ] review pack
  - [ ] CI/testing pack
- [ ] Support global/project enabling of packs

**Acceptance criteria**
- [ ] Users can enable curated policy bundles instead of many individual rules

## 7.2 Structured rule effect visibility
- [ ] Show which tools are blocked by which rule
- [ ] Show which instruction text is injected by which rule
- [ ] Show which rule caused a refusal or override

**Acceptance criteria**
- [ ] Rule behavior is explainable instead of mysterious

## 7.3 Server-managed policy templates
- [ ] Add admin-manageable policy sets for remote/server use
- [ ] Support project policy templates
- [ ] Support session overrides with clear precedence

**Acceptance criteria**
- [ ] Remote Artel deployments can centrally govern behavior without prompt hacks

---

# Phase 8 — Optional: code intelligence

**Priority:** Medium  
**Horizon:** Later

## 8.1 Decide LSP strategy
- [ ] Decide whether Artel should:
  - [ ] stay grep/read/edit-first with no LSP
  - [ ] add thin LSP support
  - [ ] add full LSP subsystem later

## 8.2 Thin LSP spike (recommended first step)
- [ ] Add diagnostics support
- [ ] Add workspace symbols support
- [ ] Add document symbols support
- [ ] Expose those through API and/or tools
- [ ] Add tests for at least one language-server happy path

**Acceptance criteria**
- [ ] Artel can answer symbol-level questions more precisely than grep-only workflows

---

# Phase 9 — Optional: stronger automation productization

**Priority:** Medium  
**Horizon:** Later

## 9.1 Turn schedules into reusable jobs
- [ ] Add reusable scheduled job templates such as:
  - [ ] repo health summary
  - [ ] dependency scan summary
  - [ ] morning review
  - [ ] changelog prep
  - [ ] test sweep summary
- [ ] Add docs and examples for reusable jobs

**Acceptance criteria**
- [ ] Schedules become a productized automation surface, not just timer-driven prompts

## 9.2 PR/GitHub automation surface
- [ ] Decide whether PR automation is in scope
- [ ] If yes, add first-class flows for:
  - [ ] summarize branch diff
  - [ ] summarize PR context
  - [ ] checkout/inspect PR branch
  - [ ] run review prompt pack

**Acceptance criteria**
- [ ] Common PR review workflows can be run without bespoke shell glue

---

# 90-day execution sequence

## Days 1–14
- [ ] Fix README/docs/runtime mismatch
- [ ] Define supported product scope
- [ ] Add smoke matrix for top-level entrypoints
- [ ] Improve git-centric UX
- [ ] Add basic test/lint repair loop

## Days 15–35
- [ ] Introduce named agent registry
- [ ] Add agent profiles and lifecycle controls
- [ ] Add structured agent outputs
- [ ] Improve context selection/focusing

## Days 36–60
- [ ] Expand MCP state model
- [ ] Harden MCP runtime
- [ ] Improve server diagnostics
- [ ] Add session export/import
- [ ] Stabilize remote session lifecycle

## Days 61–90
- [ ] Clarify built-ins vs extensions
- [ ] Add skills/packs layer
- [ ] Add policy packs
- [ ] Run thin LSP spike
- [ ] Productize schedule/job patterns

---

# Do not do now

- [ ] Do not put employee/dashboard model back on the critical path
- [ ] Do not make web-first UX the main roadmap driver
- [ ] Do not start desktop work
- [ ] Do not build full LSP before core agent/MCP/server foundations are stronger
- [ ] Do not chase full OpenCode breadth in one release

---

# Success metrics

## Product
- [ ] A user can complete a common coding loop without manual shell glue
- [ ] Local and remote behaviors are coherent
- [ ] MCP setup/debug is reliable
- [ ] Delegation produces useful structured outcomes

## Engineering
- [ ] Smoke path is green for primary commands
- [ ] Integration coverage exists for MCP, schedules, delegate lifecycle, and remote session lifecycle
- [ ] Docs claims match runtime behavior

## Competitive
- [ ] Artel is clearly stronger than Aider in server/policy/MCP platform surfaces
- [ ] Artel is noticeably closer to Goose/Gemini CLI in agent-platform maturity
- [ ] Artel has a coherent identity distinct from both Aider and OpenCode

---

# Reference patterns to borrow intentionally

## From Aider
- [ ] Git-first workflow ergonomics
- [ ] Lint/test repair loop
- [ ] Terminal coding loop simplicity

## From OpenCode
- [ ] MCP depth
- [ ] Agent productization
- [ ] Session export/import
- [ ] Control-plane maturity
- [ ] Optional LSP direction

## From Gemini CLI
- [ ] Subagent architecture
- [ ] Hook system
- [ ] Skills/extensions model
- [ ] Checkpointing discipline
- [ ] Eval-driven development

## From Goose
- [ ] Schedules/automation productization
- [ ] ACP/server integration depth
- [ ] Built-in extension strategy
- [ ] Strong typed runtime thinking
