# RFC: Plan Graph and spec-driven planning artifacts

**Status:** Draft  
**Audience:** product, UX, runtime, storage, CLI/TUI/server implementers  
**Scope:** proposed feature; not implemented yet

## Summary

This RFC proposes a first-class **Plan Graph** for Artel: a durable, structured, non-repository artifact model for spec-driven development.

A session may contain **multiple plans**. Plans can be related as parent/child decomposition artifacts and may later gain additional dependency edges. Work can proceed against a focused child plan while progress, validation, and acceptance evidence roll up through the graph.

The proposal combines:

- **artifact-first UX**: plans live beside chat, not inside the repository and not as ephemeral assistant messages
- **spec-driven structure**: plans carry requirements, non-goals, implementation approach, validation, risks, and acceptance state
- **graph-based decomposition**: a large initiative plan can be decomposed into child plans attached to specific parent steps
- **execution traceability**: implementation and validation evidence can be attached to steps/plans and rolled up to parent plans

This RFC is intended to become the canonical reference for future implementation work.

## Motivation

Today, planning in coding agents often has recurring problems:

- important intent is scattered across chat messages
- requirements and non-goals are implicit
- long-running work drifts after resume/continue
- large initiatives are hard to decompose without losing traceability
- implementation progress is difficult to reconcile against the original plan

Artel already has sessions, resume/continue flows, orchestration, and multiple interaction surfaces. A durable plan artifact model fits naturally into that architecture and creates a foundation for **spec-driven development**.

## Goals

The feature should:

1. Let a session contain **multiple structured plans**.
2. Let a plan be created as a durable artifact **outside the repository**.
3. Support **root plans** and **child plans** created from a specific step in a parent plan.
4. Let the user and agent work against a single **focused plan** at a time.
5. Support **status roll-up** from child plans to parent steps and parent plans.
6. Support **validation and acceptance** at step and plan level.
7. Support **evidence capture** for implementation and validation work.
8. Make plan-vs-actual reconciliation possible.
9. Work across CLI, TUI, and server-backed surfaces.
10. Provide a strong basis for spec-driven workflows without forcing heavy ceremony for every task.

## Non-goals

This RFC does **not** require the following in an initial implementation:

- generating repository files such as `SPEC.md` by default
- requiring a plan for every coding action
- multi-user collaborative editing
- arbitrary cyclic graph relationships
- automatic decomposition of large plans into many child plans
- a full workflow engine or BPM system
- replacing the shared task board

## Design principles

### 1. Plan is an artifact, not a repository file

Plans must live in Artel-managed state, not in tracked source files by default.

### 2. Plan is structured, not just markdown text

Plans may render as markdown, but must be stored as structured data.

### 3. Multiple plans may exist in one session

A single session can hold many related plans.

### 4. Tree-first, graph-second

For initial implementation, parent/child decomposition should be the primary structure. Additional dependency-style relations may be layered on later.

### 5. Focused execution

Even if many plans exist in one session, one plan should be the **focused plan** for current work.

### 6. Spec-driven, but lightweight

Plans should support rigorous specification when needed, but the system must also support a lighter "quick plan" path.

### 7. Acceptance requires evidence

A plan or step should not be considered robustly complete based on status alone; validation and execution evidence should be attachable and inspectable.

## Terminology

### Session
The existing Artel conversational/runtime container. A session may own many plans.

### Plan
A durable artifact describing the intent, scope, approach, validation, and status of a task or initiative.

### Plan step
A structured unit of work within a plan.

### Root plan
A top-level initiative plan, for example "v2 of the app".

### Child plan
A plan derived from a specific parent plan step, used to decompose a larger plan.

### Focused plan
The plan currently selected for discussion, revision, or execution.

### Plan graph
The set of plans and relations in a session.

### Evidence
Attached execution or validation facts, such as changed files, test runs, builds, notes, commits, or deviations.

### Validation
Checks used to determine whether a step or plan satisfies its intended outcome.

### Acceptance
The review/approval decision that a draft plan is ready for execution or that executed work satisfies the plan.

## User experience model

Artel should expose three complementary working modes as part of the feature direction:

- **Ask**: discuss, explain, analyze
- **Plan**: create and refine plan artifacts
- **Code**: implement directly or execute an approved plan

`Plan` is not a later optional add-on. It is a first-class part of the intended runtime model alongside Ask and Code.

Different surfaces may ship management affordances at different times, but the underlying model should remain consistent from the start. In particular, the plan artifact model should not depend on CLI-only wrappers to exist.

## Discovery decisions for fit with current Artel architecture

This section captures initial discovery decisions intended to make the RFC fit naturally into the current Artel codebase.

### Existing architecture anchors

The current implementation already has strong extension points for this feature:

- `artel_core.sessions.SessionStore` provides durable SQLite-backed session persistence
- `artel_server.server` already owns session serialization and control-plane session mutations
- `artel_server.acp` already exposes session modes and session updates over ACP
- `artel_core.control` already provides a shared client contract for remote-capable surfaces

The Plan Graph feature should attach to those existing seams instead of inventing a separate storage/runtime model.

### Discovery decision: mode semantics

`Plan` should be introduced as a real session mode id alongside `ask` and `code`.

Mode selection should primarily change the **system prompt and planning posture** of the agent. It should not be treated as the same thing as the permission system.

In other words:

- `ask` selects an ask-oriented system prompt
- `plan` selects a plan-oriented system prompt
- `code` selects an execution-oriented system prompt

Permission approval remains a separate layer.

In `plan` mode, Artel should receive plan-management tools and prompting that steer it toward creating and refining plans. Repository mutation constraints should be enforced by the normal policy/prompt/tooling layers, not by overloading the meaning of mode itself.

### Discovery decision: ACP is first-class

Plan workflows must work cleanly over ACP in the first iteration.

ACP support is not only a transport compatibility goal. It is part of the core architecture for this feature.

The current ACP stack already has:

- session modes
- session config/state updates
- standard plan-related schema types

The ACP standard available in the current environment includes:

- `Plan`
- `PlanEntry`
- `AgentPlanUpdate`

Artel should use those standard ACP plan structures for interoperable client display.

Because ACP's standard plan model is flatter than the richer internal Artel Plan Graph model, the expected behavior is:

- Artel stores the full structured plan graph internally
- ACP exposes a projection of that data suitable for standard client plan views
- the first projection target should be the **focused plan**

That preserves standards compatibility without collapsing Artel's richer internal model to the ACP minimum shape.

### Discovery decision: storage fit

Plans should be persisted in the same SQLite database used for session persistence, but in dedicated plan-specific tables.

Recommended storage shape:

- `plans`
- `plan_steps`
- `plan_relations`
- `session_plan_state`
- later: `plan_evidence`

This intentionally avoids storing plans as project JSON files such as `.artel/plans.json`.

### Discovery decision: focused plan storage

The current focused plan should be persisted per session, but it is better stored in dedicated plan/session state than as an early one-off field bolted directly into the core `sessions` table.

Recommended shape:

- `session_plan_state.session_id`
- `session_plan_state.focused_plan_id`
- room for future session-plan fields such as focused step, last projected ACP plan revision, or view state

This keeps the session core lightweight while still allowing focus to survive resume/load/reconnect flows.

### Discovery decision: session summary projection

Session serializers should expose only lightweight plan summary fields, not the whole graph.

Recommended minimum fields to project in session summaries:

- `focused_plan_id`
- `focused_plan_title`
- `focused_plan_status`
- `plan_count`

That is sufficient for TUI, server-backed surfaces, and ACP-aware clients to show plan context without bloating ordinary session payloads.

### Discovery decision: structural edges vs lineage edges

Not all plan relations should be treated identically.

#### Structural relations

These are used for active graph semantics and should remain strongly owned by the destination session workspace:

- `child_of`
- `derived_from_step`
- later, possibly `depends_on`

These relations can be stored as normal graph edges inside the plan workspace.

#### Lineage relations

These are historical references that may cross session boundaries:

- `forked_from`
- `inherited_from`

When a session is forked, the plan workspace should be copied into the new session with new plan ids, while retaining lineage references back to the source workspace.

Those lineage references should not prevent later deletion of the source session. They should therefore be modeled as typed historical refs, not as ownership edges that make deletion impossible.

### Discovery decision: session lifecycle semantics

The plan workspace should participate in normal session lifecycle behavior:

- `resume` restores the plan workspace and focused plan
- `load_session` over ACP restores the same focused plan state
- `fork_session` copies the plan workspace and preserves lineage metadata
- deleting a session cascades deletion of session-owned plans and structural edges, while leaving copied descendants in forked sessions intact

## Core user workflows

### Workflow A: create a root plan

Example:

> Create a plan for v2 of the application.

Artel creates a root plan with sections such as:

- goal
- context
- requirements
- non-goals
- design notes
- implementation steps
- validation
- risks

Initial status: `draft`.

### Workflow B: derive a child plan from a parent step

Example:

> Create a subplan for feature X from step 3 of the v2 plan.

Artel should:

1. identify the parent plan
2. identify the specific parent step being decomposed
3. create a new child plan
4. link the child plan to the parent step
5. mark the parent step as expanded by the child plan

This relation is a key traceability requirement.

### Workflow C: switch focus to a child plan

Example:

> Work on the feature X plan.

Artel sets the child plan as the focused plan for current execution and discussion while preserving its relation to the root plan.

### Workflow D: refine and approve a plan

Example:

> Update the plan to avoid external dependencies. Then approve it.

Artel updates the plan artifact instead of generating disconnected messages. Approval changes plan status and records who/what approved it.

### Workflow E: execute a plan or step

Example:

> Execute this plan.

Or:

> Execute step 2 only.

Artel performs implementation work in Code mode, recording evidence and updating statuses.

### Workflow F: reconcile actual work with the plan

After execution, Artel should be able to report:

- planned files vs actually changed files
- planned validation vs actually run validation
- completed, skipped, blocked, and deviated steps
- parent roll-up status

## Required plan structure

A plan should support at least the following sections.

### Identity and metadata

- plan id
- session id
- title
- status
- revision/version
- created at
- updated at
- author/source

### Intent

- goal
- summary
- context

### Spec-driven sections

- requirements
- non-goals
- open questions
- risks

### Design section

- design notes
- implementation approach
- files of interest

### Execution section

- steps
- dependencies or blockers
- focused work area

### Quality section

- validation plan
- acceptance criteria
- evidence
- deviations from original plan

## Recommended plan shapes

### Quick plan

For smaller tasks, Artel may produce a lighter structure:

- summary
- files of interest
- steps
- validation
- risks

### Full spec plan

For larger work, Artel should include:

- goal
- context
- requirements
- non-goals
- design notes
- implementation approach
- steps
- validation
- acceptance criteria
- risks
- open questions

## Graph model

### Primary structure: decomposition tree

The first implementation should treat parent/child decomposition as the primary relation. This gives predictable roll-up and simpler UX.

### Secondary structure: typed relations

Additional relation types may be added later, for example:

- `child_of`
- `derived_from`
- `depends_on`
- `blocks`
- `related_to`
- `supersedes`

Initial implementation should prioritize `child_of` plus explicit linkage to a parent step.

## Key traceability rule

A child plan should link to:

- its **parent plan**, and
- the specific **parent step** it expands

This is more useful than linking only to the parent plan.

Example:

- Root plan: `Build app v2`
- Parent step: `Implement feature X`
- Child plan: `Feature X detailed plan`

The child plan is then the decomposition artifact for that exact parent step.

## Proposed data model

The exact schema can evolve, but the conceptual model should look like this.

### Plan

```json
{
  "id": "plan_123",
  "session_id": "sess_456",
  "title": "Build app v2",
  "status": "draft",
  "revision": 1,
  "goal": "Ship the v2 application architecture and key features",
  "summary": "Root initiative plan for v2",
  "context": ["Current app has v1-only onboarding and API boundaries"],
  "requirements": ["Feature X must support tenant-aware auth"],
  "non_goals": ["Do not redesign billing in this phase"],
  "design_notes": ["Prefer incremental migration over rewrite"],
  "files_of_interest": ["packages/...", "tests/..."],
  "validation": ["Run focused backend and UI tests"],
  "acceptance_criteria": ["All required child plans approved or complete"],
  "risks": ["Migration order may block onboarding updates"],
  "open_questions": ["Need final API versioning choice"],
  "created_at": 0,
  "updated_at": 0
}
```

### PlanStep

```json
{
  "id": "step_1",
  "plan_id": "plan_123",
  "title": "Implement feature X",
  "description": "Deliver feature X for v2 scope",
  "status": "todo",
  "acceptance_criteria": ["Feature X behavior matches approved spec"],
  "validation_targets": ["tests/test_feature_x.py"],
  "expanded_by_plan_id": null
}
```

### PlanRelation

```json
{
  "id": "rel_1",
  "source_plan_id": "plan_feature_x",
  "target_plan_id": "plan_123",
  "relation_type": "child_of",
  "target_step_id": "step_1"
}
```

### PlanEvidence

```json
{
  "id": "ev_1",
  "plan_id": "plan_feature_x",
  "step_id": "step_2",
  "kind": "test_run",
  "payload": {
    "command": "pytest -q tests/test_feature_x.py",
    "result": "passed"
  },
  "created_at": 0
}
```

## Status model

### Plan statuses

Minimum recommended set:

- `draft`
- `approved`
- `in_progress`
- `blocked`
- `completed`
- `abandoned`

### Step statuses

Minimum recommended set:

- `todo`
- `in_progress`
- `blocked`
- `done`
- `skipped`

## Status roll-up rules

When a parent step is expanded by a child plan:

- child `completed` -> parent step `done`
- child `in_progress` -> parent step `in_progress`
- child `blocked` -> parent step `blocked`
- child `abandoned` -> parent step remains unresolved unless explicitly accepted as skipped/abandoned

A parent plan status should be derived from its steps plus any explicit plan-level state.

Recommended roll-up heuristics:

- if any required step is `blocked`, parent tends toward `blocked`
- if any step is `in_progress`, parent tends toward `in_progress`
- if all required steps are `done` or accepted `skipped`, parent may become `completed`
- `approved` is a pre-execution readiness state and should not imply execution progress

## Focus model

A session may contain many plans, but there should be one primary focus pointer:

- `focused_plan_id`

This keeps execution coherent even when the graph is large.

Focus is an execution/navigation concept and should not alter structural relationships.

## Evidence model

Statuses alone are not enough. The system should attach evidence to plans and steps.

Recommended evidence kinds:

- note
- file_change
- test_run
- command
- build
- commit
- pull_request
- review_decision
- deviation

Evidence should support both human review and future automation.

## Validation model

Validation must exist at two levels.

### 1. Plan validation before approval

A draft plan should be checkable for structural completeness. For example:

- does it have a clear goal?
- are requirements stated?
- are non-goals stated for non-trivial work?
- are validation steps present?
- are major risks or open questions called out?
- if it is a child plan, is the parent step linkage present?

This is **artifact validation**, not execution validation.

### 2. Execution validation after implementation

After work is performed, the system should validate whether:

- acceptance criteria were met
- planned checks were run
- blocking deviations occurred
- the resulting state is consistent with the plan status

This is **delivery validation**.

## Acceptance model

Approval and acceptance are distinct.

### Approval
Approval means a draft plan is accepted as a basis for implementation.

Typical transition:

- `draft` -> `approved`

### Acceptance after execution
Acceptance means the executed work satisfies the plan.

Typical transition:

- `in_progress` -> `completed`

Acceptance should consider:

- step completion state
- validation results
- attached evidence
- unresolved deviations

## Authoring guidelines

When Artel creates or revises a plan, it should answer these questions explicitly:

1. What are we doing?
2. Why are we doing it?
3. What is in scope?
4. What is explicitly out of scope?
5. How will we implement it?
6. How will we validate it?
7. What could go wrong?

For child plans, it should also answer:

8. Which parent step does this decompose?
9. How does completion of this child plan satisfy the parent step?

## Review checklist for plan approval

Before approving a plan, reviewers or the user should be able to check:

- the goal is concrete
- requirements are testable enough to guide implementation
- non-goals prevent obvious scope creep
- steps are actionable
- validation is realistic
- risks/open questions are visible
- parent linkage exists for child plans
- the plan is focused enough to execute without major ambiguity

## Execution checklist

Before Artel executes a plan or step, it should be able to answer:

- which plan is currently focused?
- is the plan approved, or has the user explicitly requested immediate execution?
- which steps are selected for execution?
- what validations are expected afterward?
- are there dependencies or blockers from related plans?

## Reconciliation checklist

After execution, Artel should be able to produce a reconciliation summary:

- planned steps completed
- planned steps skipped or blocked
- files expected vs files changed
- validations planned vs validations run
- deviations from the approved plan
- parent roll-up impact

## Suggested surface behavior

### CLI

CLI wrappers may be added later if product usage justifies them.

Possible future commands:

```bash
artel plan create "Build app v2"
artel plan list
artel plan show <plan-id>
artel plan focus <plan-id>
artel plan approve <plan-id>
artel plan execute <plan-id>
artel plan execute <plan-id> --step <step-id>
artel plan create-child <parent-plan-id> --step <step-id> --title "Feature X"
artel plan graph
artel plan validate <plan-id>
artel plan reconcile <plan-id>
```

### TUI

Possible future TUI elements:

- mode switch: Ask / Plan / Code
- plan list in session context
- focused plan view
- breadcrumb for parent/child lineage
- plan graph or tree inspector
- actions: revise, approve, execute, validate, reconcile

### Server/API

Possible future operations:

- create/read/update/list plans by session
- create child plan from parent step
- set focused plan
- validate/approve plan
- attach evidence
- compute graph status and reconciliation view

### ACP

Plan support should be designed to work over ACP as a first-class transport, not as an afterthought.

At minimum, the architecture should support:

- `plan` as a real ACP session mode alongside `ask` and `code`
- session config/state updates that expose focused plan information
- plan lifecycle operations reachable through ACP-compatible session interactions
- emission of standard ACP plan updates using the protocol's plan schema types
- parity between server-backed UI surfaces and ACP-capable clients where practical

The product should avoid coupling plan workflows exclusively to REST-only control-plane affordances if that would make ACP integration artificial later.

Because the ACP standard plan shape is flatter than the full internal Plan Graph model, ACP should be treated as a standards-compliant projection surface rather than the full internal source of truth.

## Storage considerations

Plans should be persisted outside chat message history, even if linked to sessions.

Recommended approach:

- store plans in dedicated plan tables/collections
- keep relations separate from plan bodies
- keep session-plan focus/state separate from the core session row when practical
- keep evidence append-only where practical
- track plan revision numbers
- record the parent plan revision a child plan was derived from when available

A practical shape for the current codebase is:

- `plans`
- `plan_steps`
- `plan_relations`
- `session_plan_state`
- later: `plan_evidence`

That last point about parent-plan revision helps later drift detection.

## Schema proposal for the current `sessions.db`

This section proposes a storage shape that fits the current Artel codebase and existing SQLite session store patterns.

### Storage style: hybrid normalized + JSON sections

A practical fit for the existing code is a hybrid model:

- keep **plans, steps, relations, and session-plan focus** in dedicated tables
- keep richer list-like sections such as requirements or risks in JSON text columns
- keep evidence append-only in a later table

This matches the current `SessionStore` style, which already stores some structured message fields as JSON while keeping the main entity model relational.

### Table: `plans`

Purpose: store the durable plan artifact body for one session-owned plan.

Recommended columns:

- `id TEXT PRIMARY KEY`
- `session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE`
- `title TEXT NOT NULL DEFAULT ''`
- `goal TEXT NOT NULL DEFAULT ''`
- `summary TEXT NOT NULL DEFAULT ''`
- `status TEXT NOT NULL DEFAULT 'draft'`
- `template_kind TEXT NOT NULL DEFAULT 'full'` — for example `quick` or `full`
- `revision INTEGER NOT NULL DEFAULT 1`
- `requirements_json TEXT NOT NULL DEFAULT '[]'`
- `non_goals_json TEXT NOT NULL DEFAULT '[]'`
- `context_json TEXT NOT NULL DEFAULT '[]'`
- `design_notes_json TEXT NOT NULL DEFAULT '[]'`
- `files_of_interest_json TEXT NOT NULL DEFAULT '[]'`
- `validation_json TEXT NOT NULL DEFAULT '[]'`
- `acceptance_criteria_json TEXT NOT NULL DEFAULT '[]'`
- `risks_json TEXT NOT NULL DEFAULT '[]'`
- `open_questions_json TEXT NOT NULL DEFAULT '[]'`
- `metadata_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`
- `approved_at TEXT NOT NULL DEFAULT ''`
- `completed_at TEXT NOT NULL DEFAULT ''`

Notes:

- plan-level rich sections stay structured without forcing dozens of auxiliary tables too early
- `metadata_json` leaves room for future non-core data without immediate schema churn
- `session_id` ownership stays explicit and makes cascade deletion straightforward

### Table: `plan_steps`

Purpose: store ordered steps inside a plan.

Recommended columns:

- `id TEXT PRIMARY KEY`
- `plan_id TEXT NOT NULL REFERENCES plans(id) ON DELETE CASCADE`
- `ordinal INTEGER NOT NULL`
- `title TEXT NOT NULL DEFAULT ''`
- `description TEXT NOT NULL DEFAULT ''`
- `status TEXT NOT NULL DEFAULT 'todo'`
- `priority TEXT NOT NULL DEFAULT 'medium'`
- `acceptance_criteria_json TEXT NOT NULL DEFAULT '[]'`
- `validation_targets_json TEXT NOT NULL DEFAULT '[]'`
- `file_targets_json TEXT NOT NULL DEFAULT '[]'`
- `metadata_json TEXT NOT NULL DEFAULT '{}'`
- `expanded_by_plan_id TEXT NOT NULL DEFAULT ''`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Notes:

- `ordinal` gives a stable order for rendering, approval, and ACP projection
- `priority` aligns naturally with ACP plan entry priority support
- `expanded_by_plan_id` is a convenience pointer; the canonical graph relationship still lives in `plan_relations`

### Table: `plan_relations`

Purpose: store typed edges between plans and steps.

Recommended columns:

- `id TEXT PRIMARY KEY`
- `session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE`
- `source_plan_id TEXT NOT NULL REFERENCES plans(id) ON DELETE CASCADE`
- `source_step_id TEXT NOT NULL DEFAULT ''`
- `target_plan_id TEXT NOT NULL DEFAULT ''`
- `target_session_id TEXT NOT NULL DEFAULT ''`
- `target_step_id TEXT NOT NULL DEFAULT ''`
- `relation_type TEXT NOT NULL`
- `relation_scope TEXT NOT NULL DEFAULT 'structural'` — for example `structural` or `lineage`
- `metadata_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL`

Notes:

- only `source_plan_id` is treated as a hard foreign-key-owned edge
- target references are stored as ids/refs instead of hard foreign keys so lineage edges can survive source-session deletion semantics cleanly
- service-layer validation should enforce that structural in-session edges point to valid current plans/steps

Expected relation types in early iterations:

- structural:
  - `child_of`
  - `derived_from_step`
- lineage:
  - `forked_from`
  - `inherited_from`

### Table: `session_plan_state`

Purpose: store session-scoped plan workspace state without overloading the main `sessions` row.

Recommended columns:

- `session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE`
- `focused_plan_id TEXT NOT NULL DEFAULT ''`
- `focused_step_id TEXT NOT NULL DEFAULT ''`
- `last_acp_plan_revision INTEGER NOT NULL DEFAULT 0`
- `metadata_json TEXT NOT NULL DEFAULT '{}'`
- `updated_at TEXT NOT NULL`

Notes:

- `focused_plan_id` survives resume/load/reconnect flows
- `focused_step_id` is optional but leaves room for future execution UX
- `last_acp_plan_revision` can help avoid redundant ACP plan emissions later without polluting the core session row

### Later table: `plan_evidence`

Purpose: append-only execution and validation evidence.

Recommended future columns:

- `id TEXT PRIMARY KEY`
- `session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE`
- `plan_id TEXT NOT NULL REFERENCES plans(id) ON DELETE CASCADE`
- `step_id TEXT NOT NULL DEFAULT ''`
- `kind TEXT NOT NULL`
- `payload_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL`

This can be deferred until execution and reconciliation become first-class implementation goals.

### Recommended indexes

At minimum:

- `idx_plans_session_updated` on `(session_id, updated_at DESC)`
- `idx_plan_steps_plan_ordinal` on `(plan_id, ordinal)`
- `idx_plan_relations_source` on `(source_plan_id, relation_type)`
- `idx_plan_relations_target` on `(target_session_id, target_plan_id, relation_type)`

### ACP projection shape

The internal Artel Plan Graph model is richer than the ACP standard plan shape. The first interoperable projection should therefore be based on the **focused plan**.

Recommended projection rules:

- the focused internal plan projects to one ACP `Plan`
- ordered `plan_steps` project to ACP `PlanEntry[]`
- internal `priority` maps directly to ACP priority values `high|medium|low`
- internal step status maps to ACP status conservatively:
  - `todo` -> `pending`
  - `blocked` -> `pending` with `_meta.artel_status = "blocked"`
  - `in_progress` -> `in_progress`
  - `done` -> `completed`
  - `skipped` -> `completed` with `_meta.artel_status = "skipped"`

This preserves ACP compatibility while retaining richer Artel semantics in `_meta` and in the internal store.

### Session summary projection

A lightweight serialized session payload should include at least:

- `focused_plan_id`
- `focused_plan_title`
- `focused_plan_status`
- `plan_count`

Those summary fields are sufficient for TUI, server-backed surfaces, and ACP-aware clients to present plan context without embedding the whole graph into normal session summaries.

### Migration fit

The current `SessionStore.open()` already performs additive schema updates using `CREATE TABLE IF NOT EXISTS` plus lightweight migration steps.

The recommended implementation strategy is therefore:

- keep using the existing `sessions.db`
- create plan tables lazily during store initialization
- avoid a separate plan database unless a later scaling need clearly appears

## Stage 0 exit checklist

Stage 0 (Discovery) should be considered complete only when the following decisions are explicitly accepted.

### Product and runtime model

- `plan` is accepted as a first-class mode alongside `ask` and `code`
- mode semantics are defined primarily in terms of system prompt/runtime posture, not permission policy
- the first iteration is expected to support many plans per session, not a single-plan-only storage shape
- one focused plan per session is accepted as the execution/navigation model

### ACP and transport fit

- ACP support for `plan` mode is accepted as an initial requirement
- the focused plan projection over ACP will use the protocol's standard `Plan` / `PlanEntry` / `AgentPlanUpdate` types
- minimum session summary fields for ACP-aware clients are accepted:
  - `focused_plan_id`
  - `focused_plan_title`
  - `focused_plan_status`
  - `plan_count`
- the internal Artel Plan Graph is accepted as richer than the ACP projection model
- plan workflows are not allowed to become REST-only by accident

### Storage and schema fit

- plans will live in the existing `sessions.db`, not in project JSON files
- the initial schema shape is accepted in principle:
  - `plans`
  - `plan_steps`
  - `plan_relations`
  - `session_plan_state`
  - later `plan_evidence`
- `session_plan_state` is accepted as the place for focused plan state
- plan sections may use JSON columns where that keeps the schema practical
- additive/lazy schema migration through store initialization is accepted as the migration strategy

### Graph and lifecycle semantics

- child plans must link to a specific parent step, not only to a parent plan
- tree-first decomposition is accepted for early implementation
- typed lineage edges such as `forked_from` / `inherited_from` are accepted as distinct from active structural edges
- resume/load must restore focused plan state
- fork semantics are accepted in principle:
  - plan workspace copies into the new session
  - copied plans receive new ids
  - lineage metadata is retained
- deleting a session cascades deletion of session-owned plans and structural edges

### Validation and testing readiness

- validation, approval, and acceptance are treated as distinct concepts
- a layered test strategy is accepted:
  - storage tests
  - service tests
  - ACP tests
  - server/API tests
  - TUI or remote control happy-path tests
- Phase 1 is not expected to solve full reconciliation or evidence automation

### Ready-to-start criteria for Phase 1

Phase 1 can start when all of the following are true:

- no unresolved disagreement remains about mode semantics
- no unresolved disagreement remains about ACP being first-class for plans
- no unresolved disagreement remains about storage in `sessions.db`
- no unresolved disagreement remains about `session_plan_state` for focus storage
- no unresolved disagreement remains about focused-plan ACP projection
- the implementation can proceed without reopening the question of single-plan vs multi-plan storage

## Plan drift and revision handling

This RFC intentionally does not solve drift completely, but the model should prepare for it.

Useful future fields:

- `derived_from_plan_revision`
- `last_reconciled_at`
- `drift_status`

This enables future checks such as:

- the child plan was derived from an older parent revision
- the parent changed materially after child approval
- acceptance may require revalidation

## Relationship to task board

Plan artifacts and the shared task board are different concepts.

### Plan graph

- session-scoped or initiative-scoped specification artifacts
- rich structure
- good for intent, design, validation, and traceability

### Task board

- shared operational tracking layer
- lightweight task state management
- cross-session/project visibility

A plan may later export steps to the task board, but the task board should not replace the plan model.

## Safety and policy considerations

Plan mode should generally be non-mutating with respect to the repository. Code mode performs implementation.

Approval should provide a natural boundary between:

- planning/specification
- implementation/execution

The system should preserve user intent if they explicitly bypass a formal plan and ask Artel to implement directly.

## Phased implementation approach

### Phase 1: plan mode and artifact basics

- introduce `plan` as a first-class mode alongside Ask and Code
- create plan artifacts outside the repo
- basic structured schema
- draft/approved lifecycle
- simple validation
- single focused plan in session
- architecture fit for ACP session mode/state
- standards-compliant ACP plan projection for focused plan display

#### Phase 1 decomposition

##### Workstream 1. Core storage and domain model

Goal:

- establish the minimum durable model for plans in the existing session database

Scope:

- create store schema for:
  - `plans`
  - `plan_steps`
  - `plan_relations`
  - `session_plan_state`
- define plan/step/relation dataclasses or equivalent domain objects
- implement basic persistence operations for:
  - create plan
  - get plan
  - list plans by session
  - update plan body
  - set focused plan
  - list steps
- persist timestamps and integer revision

Out of scope:

- evidence capture
- reconciliation reports
- deep dependency graph semantics

Phase 1 exit criteria for this workstream:

- plan artifacts survive session resume/reload
- one session can own multiple plans in storage
- focused plan state persists independently of chat history

#### Detailed task decomposition: Workstream 1

The following tasks further decompose Workstream 1 into implementation-sized units.

##### Task 1.1 — Introduce core plan domain models

Goal:

- define the minimum internal plan types used across storage, services, ACP projection, and later UI work

Recommended scope:

- add plan-focused core models in `artel_core`
- define at least:
  - `PlanRecord`
  - `PlanStepRecord`
  - `PlanRelationRecord`
  - `SessionPlanStateRecord`
- keep plan-level list sections as typed Python fields even if persisted as JSON text
- define stable literal/status value sets for:
  - plan status
  - step status
  - relation type
  - relation scope
  - template kind

Implementation notes:

- prefer local dataclass style consistent with the current codebase
- keep persistence-oriented fields and domain-oriented fields close enough to avoid repeated conversion boilerplate
- do not over-design evidence or reconciliation types yet

Exit criteria:

- other modules can depend on a stable internal plan model
- status values are centralized instead of being stringly-typed everywhere

##### Task 1.2 — Extend session store schema with plan tables

Goal:

- add additive schema support for plan persistence inside the existing `sessions.db`

Recommended scope:

- create tables if missing:
  - `plans`
  - `plan_steps`
  - `plan_relations`
  - `session_plan_state`
- add required indexes
- integrate schema creation into the existing store initialization path
- ensure schema bootstrapping remains safe on pre-plan databases

Implementation notes:

- follow the current `SessionStore.open()` migration style
- prefer `CREATE TABLE IF NOT EXISTS` and additive migrations over destructive rewrites
- preserve foreign-key behavior for session-owned rows

Exit criteria:

- opening the store on a fresh or old database creates all required plan tables safely
- deleting a session cascades correctly to session-owned plan tables

##### Task 1.3 — Add persistence methods for plans and focus state

Goal:

- provide the minimum store API needed by Phase 1 services and transports

Recommended scope:

- add store methods for:
  - create plan
  - update plan
  - get plan by id
  - list plans for session
  - create/update/list plan steps
  - create/list plan relations
  - get/set session focused plan state
  - count plans for session
- make plan reads return structured core record types, not loose dicts
- ensure writes update plan/session timestamps as needed

Implementation notes:

- keep method names consistent with existing `SessionStore` naming patterns
- prefer explicit APIs over a single generic mutation method
- avoid prematurely adding broad search/query surfaces

Exit criteria:

- the store can fully support a basic create/read/update/focus workflow for plans
- callers do not need to manually parse JSON columns outside the store layer

##### Task 1.4 — Define relation and lineage validation rules at the store/service boundary

Goal:

- keep storage flexible without allowing semantically invalid graph state to leak in unchecked

Recommended scope:

- define minimum invariants for early writes:
  - structural relations must reference valid in-session plans
  - `derived_from_step` relations must point to a valid source/target step context
  - lineage relations may reference copied or historical ids without hard foreign-key ownership
- decide which checks belong in raw store methods vs a higher-level plan service
- document or codify the distinction clearly

Implementation notes:

- store-level integrity should cover relational safety
- service-level integrity should cover product semantics
- do not block future cross-session lineage by over-constraining foreign keys

Exit criteria:

- the code has a clear boundary between raw persistence and semantic validation
- structural vs lineage relations are not accidentally treated the same way

##### Task 1.5 — Add session-plan summary helpers

Goal:

- provide a compact way to compute focused-plan summary fields for session serialization and ACP use

Recommended scope:

- add helpers to resolve:
  - focused plan id
  - focused plan title
  - focused plan status
  - plan count for session
- keep these helpers independent from full graph loading where possible
- ensure they work even when the runtime session object is not currently loaded into memory

Implementation notes:

- these helpers will likely be reused by both server serialization and ACP session updates
- prefer direct lightweight queries over loading every plan body

Exit criteria:

- session summary projection can be implemented without duplicating store logic in transports

##### Task 1.6 — Define fork/copy persistence baseline

Goal:

- decide how the storage layer will support future plan workspace copying for session forks

Recommended scope:

- specify how plan ids are regenerated during a session fork
- specify how copied step ids and relation endpoints are remapped inside the new session
- specify how lineage refs such as `forked_from` or `inherited_from` are recorded
- Phase 1 may stop at helper design plus tests, even if full fork-copy behavior lands slightly later

Implementation notes:

- this task is about avoiding a dead-end storage design, not necessarily finishing every fork behavior immediately
- id remapping should be deterministic within one copy operation and opaque outside it

Exit criteria:

- the plan schema and persistence APIs do not block later implementation of forked plan workspaces

##### Task 1.7 — Add targeted storage and migration tests

Goal:

- prove the store layer is safe enough to build the rest of Phase 1 on top of it

Recommended scope:

- test fresh database initialization
- test migration from a database without plan tables
- test plan create/read/update/list operations
- test step ordering persistence
- test focused-plan persistence in `session_plan_state`
- test session deletion cascade behavior
- where possible, test baseline relation semantics and copied-id remapping helpers

Implementation notes:

- keep tests narrow and store-focused
- use temporary session databases in the same style as existing session-related tests

Exit criteria:

- plan storage is covered well enough that later ACP/mode work can assume it is stable

##### Workstream 2. Session mode support

Goal:

- introduce `plan` as a real session mode in the runtime model

Scope:

- extend mode/state handling so `ask`, `plan`, and `code` are all supported
- define `plan` mode semantics as system-prompt/runtime posture, not permission policy
- ensure local and remote session state can carry the current mode
- make sure the mode can coexist with existing thinking/model/session metadata

Out of scope:

- final polished UI for all surfaces
- advanced mode-specific policy engines

Phase 1 exit criteria for this workstream:

- a session can enter and remain in `plan` mode
- runtime prompt construction can differentiate `plan` from `ask` and `code`
- no existing `ask`/`code` behavior regresses

##### Workstream 3. ACP support for plan mode and plan projection

Goal:

- make plan mode and focused-plan visibility work through ACP in the first iteration

Scope:

- add `plan` as an ACP session mode id
- expose focused-plan session summary fields for ACP-aware clients
- emit standards-compliant ACP `Plan` updates for the focused plan using:
  - `Plan`
  - `PlanEntry`
  - `AgentPlanUpdate`
- define the initial mapping from internal step status/priority to ACP plan entry fields

Out of scope:

- full graph visualization over ACP
- rich bidirectional ACP editing of arbitrary plan graph structure

Phase 1 exit criteria for this workstream:

- an ACP client can observe `plan` as a valid session mode
- an ACP client can receive a focused-plan projection for display
- ACP support does not force Artel to flatten its internal plan model permanently

##### Workstream 4. Session serialization and control-plane projection

Goal:

- expose minimal plan-aware session context through existing server/session summaries

Scope:

- extend session serialization with lightweight plan summary fields:
  - `focused_plan_id`
  - `focused_plan_title`
  - `focused_plan_status`
  - `plan_count`
- keep full plan graph retrieval separate from normal session summary payloads
- prepare control-plane integration points for future plan CRUD operations

Out of scope:

- full REST surface for every future plan action
- rich graph payloads in every session summary

Phase 1 exit criteria for this workstream:

- remote-capable surfaces can show that a session has an active focused plan
- session payload size remains lightweight and predictable

##### Workstream 5. Basic plan lifecycle service

Goal:

- implement the first usable plan artifact workflow

Scope:

- create root plan
- update plan sections
- set focused plan
- approve plan
- validate plan for structural completeness
- render focused plan into a form suitable for agent responses and ACP projection

Out of scope:

- child plans
- status roll-up across plan graphs
- execution/reconciliation logic

Phase 1 exit criteria for this workstream:

- a user can create and refine a plan artifact in a session
- a plan can move from `draft` to `approved`
- structural validation can fail with actionable feedback

##### Workstream 6. Tests and migration safety

Goal:

- land Phase 1 with confidence and without breaking existing session behavior

Scope:

- add schema/store tests for plan persistence
- add mode tests for `plan`
- add ACP tests for:
  - `plan` mode exposure
  - focused-plan updates
  - ACP plan projection
- add session lifecycle tests for:
  - resume/load with focused plan state
  - fork baseline semantics where applicable
- ensure migrations remain additive and safe for existing session databases

Out of scope:

- exhaustive end-to-end graph execution tests
- evidence/reconciliation coverage from later phases

Phase 1 exit criteria for this workstream:

- existing ask/code session tests still pass
- new plan-mode and plan-storage behaviors are covered by targeted tests
- migration path is verified on a pre-plan session database shape

#### Phase 1 overall success criteria

Phase 1 should be considered successful when all of the following are true:

- Artel supports `plan` as a real mode alongside `ask` and `code`
- the current session can own durable plan artifacts outside chat history
- one focused plan can be persisted and restored per session
- ACP clients can see `plan` mode and receive a standard focused-plan projection
- the first iteration is useful without requiring child-plan graphs or execution automation

### Phase 2: multiple plans and child decomposition

- many plans per session
- child plan from parent step
- status roll-up
- focused plan switching
- evidence capture

### Phase 3: richer graph and reconciliation

- typed relations beyond `child_of`
- graph inspection
- planned-vs-actual reconciliation reports
- revision and drift metadata

### Phase 4: deeper execution integration

- execute selected steps
- attach evidence automatically from tool runs/tests
- tighter TUI/server UX
- optional task board export

## Acceptance criteria for this RFC's feature direction

The eventual implementation should make the following true:

1. A session can hold multiple plans.
2. A child plan can be linked to a specific parent step.
3. A focused plan can be selected independently of graph structure.
4. Plan and step statuses can be rolled up across parent/child boundaries.
5. Validation exists both before approval and after implementation.
6. Evidence can be attached and inspected.
7. Reconciliation between planned and actual work is possible.
8. The model remains usable from CLI, TUI, server-backed contexts, and ACP-based clients.

## Open questions

These are intentionally left for future design work:

- Should approval be required before plan execution by default?
- How much manual editing of plan sections should users have in each surface?
- Should quick plans and full spec plans share one schema with optional sections, or distinct templates?
- How should graph visualization work in TUI versus web?
- Which ACP session updates and config options should expose focused plan and plan-mode state beyond the initial minimum set?
- Which evidence should be attached automatically from tool activity?
- How aggressively should parent/child revision drift be surfaced?
- When should Artel suggest creating a child plan automatically?

## Rationale

This direction gives Artel a durable planning/specification primitive that fits naturally with its existing session model while enabling larger, traceable, multi-stage work. It creates a foundation for spec-driven development without forcing every task into heavyweight process.

## References and inspiration

This proposal is informed by two broad ideas from modern agent products:

- structured, spec-driven workflows
- artifact-first UX where durable outputs live outside raw chat history

Artel should adapt those strengths to its own session, orchestration, and multi-surface model rather than copying any one product literally.
