"""Pydantic schemas for backlog API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# -- Request schemas ----------------------------------------------------------


class EstimationRequest(BaseModel):
    """Request story point estimation for an issue."""

    issue_id: str


class PrioritizationRequest(BaseModel):
    """Request priority ranking of backlog issues."""

    project_id: str
    weights: Optional[dict[str, float]] = Field(
        default=None,
        description="Override default scoring weights (importance, urgency, value, ease)",
        examples=[{"importance": 50.0, "urgency": 30.0, "value": 15.0, "ease": 5.0}],
    )


class ReadinessCheckRequest(BaseModel):
    """Request Definition of Ready evaluation."""

    issue_id: str
    actor_id: str
    actor_type: Literal["user", "agent"] = "user"


class ReorderRequest(BaseModel):
    """Request to reorder a single backlog item."""

    issue_id: str
    after_id: Optional[str] = Field(
        default=None, description="Move after this issue (None = move to top)"
    )
    before_id: Optional[str] = Field(
        default=None, description="Move before this issue"
    )


class BulkReorderRequest(BaseModel):
    """Request bulk reorder of backlog (e.g., from drag-drop)."""

    project_id: str
    ordered_ids: list[str] = Field(..., min_length=1, max_length=500)


class SprintPullRequest(BaseModel):
    """Request to move issues into a sprint."""

    issue_ids: list[str] = Field(..., min_length=1, max_length=100)
    sprint_id: str
    actor_id: str


# -- Response schemas ---------------------------------------------------------


class EstimationResponse(BaseModel):
    """Result of story point estimation."""

    issue_id: str
    suggested_points: int
    raw_score: float
    confidence: Literal["high", "medium", "low"]
    rationale: str
    ai_enhanced: bool
    ai_refinement_queued: bool


class PriorityScoreResponse(BaseModel):
    """Single issue priority score."""

    issue_id: str
    score: float
    rank: int
    breakdown: dict[str, float]


class RankedBacklogResponse(BaseModel):
    """Ranked backlog response."""

    project_id: str
    total: int
    items: list[PriorityScoreResponse]


class DORCheckResponse(BaseModel):
    """Result of Definition of Ready evaluation."""

    issue_id: str
    passed: bool
    failed_criteria: list[str]
    checked_at: datetime
    checked_by_id: str
    checked_by_type: str
    status_advanced_to_ready: bool


class BacklogIssueResponse(BaseModel):
    """Backlog issue view (subset of full issue fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    issue_type: str
    status: str
    priority: str
    importance: str
    difficulty: str
    story_points: Optional[int]
    dor_passed: bool
    assignee_id: Optional[str]
    backlog_rank: Optional[float]
    created_at: datetime
    updated_at: datetime
    priority_score: Optional[float] = Field(
        default=None, description="Populated when include_scores=True"
    )


class BacklogListResponse(BaseModel):
    """List of backlog issues."""

    items: list[BacklogIssueResponse]
    total: int
    has_more: bool


class ReorderResponse(BaseModel):
    """Response from reorder operation."""

    issue_id: str
    new_backlog_rank: Optional[float]
    success: bool


class SprintPullResponse(BaseModel):
    """Response from sprint pull operation."""

    sprint_id: str
    requested: int
    moved: int
    moved_issue_ids: list[str]
    skipped_not_ready: list[str]
