"""Core plan artifact models for spec-driven planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

PlanStatus: TypeAlias = Literal[
    "draft",
    "approved",
    "in_progress",
    "blocked",
    "completed",
    "abandoned",
]
PlanTemplateKind: TypeAlias = Literal["quick", "full"]
PlanStepStatus: TypeAlias = Literal["todo", "in_progress", "blocked", "done", "skipped"]
PlanStepPriority: TypeAlias = Literal["high", "medium", "low"]
PlanRelationScope: TypeAlias = Literal["structural", "lineage"]
PlanRelationType: TypeAlias = Literal[
    "child_of",
    "derived_from_step",
    "forked_from",
    "inherited_from",
]


@dataclass
class PlanRecord:
    id: str
    session_id: str
    title: str = ""
    goal: str = ""
    summary: str = ""
    status: PlanStatus = "draft"
    template_kind: PlanTemplateKind = "full"
    revision: int = 1
    requirements: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    context: list[str] = field(default_factory=list)
    design_notes: list[str] = field(default_factory=list)
    files_of_interest: list[str] = field(default_factory=list)
    validation: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    approved_at: str = ""
    completed_at: str = ""


@dataclass
class PlanStepRecord:
    id: str
    plan_id: str
    ordinal: int
    title: str = ""
    description: str = ""
    status: PlanStepStatus = "todo"
    priority: PlanStepPriority = "medium"
    acceptance_criteria: list[str] = field(default_factory=list)
    validation_targets: list[str] = field(default_factory=list)
    file_targets: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)
    expanded_by_plan_id: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class PlanRelationRecord:
    id: str
    session_id: str
    source_plan_id: str
    relation_type: PlanRelationType
    relation_scope: PlanRelationScope = "structural"
    source_step_id: str = ""
    target_plan_id: str = ""
    target_session_id: str = ""
    target_step_id: str = ""
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class SessionPlanStateRecord:
    session_id: str
    focused_plan_id: str = ""
    focused_step_id: str = ""
    last_acp_plan_revision: int = 0
    metadata: dict[str, object] = field(default_factory=dict)
    updated_at: str = ""


@dataclass
class SessionPlanSummary:
    session_id: str
    focused_plan_id: str = ""
    focused_plan_title: str = ""
    focused_plan_status: str = ""
    plan_count: int = 0


__all__ = [
    "PlanRecord",
    "PlanRelationRecord",
    "PlanRelationScope",
    "PlanRelationType",
    "PlanStatus",
    "PlanStepPriority",
    "PlanStepRecord",
    "PlanStepStatus",
    "PlanTemplateKind",
    "SessionPlanStateRecord",
    "SessionPlanSummary",
]
