"""FastAPI router for backlog operations."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import from root package
import sys
from pathlib import Path
_root = Path(__file__).parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agileai.api.dependencies import get_db, get_current_user
from agileai.schemas.backlog import (
    BacklogIssueResponse,
    BacklogListResponse,
    BulkReorderRequest,
    DORCheckResponse,
    EstimationRequest,
    EstimationResponse,
    PrioritizationRequest,
    RankedBacklogResponse,
    ReadinessCheckRequest,
    ReorderRequest,
    ReorderResponse,
    SprintPullRequest,
    SprintPullResponse,
)
from agileai.services.backlog import (
    BacklogService,
    IssueNotFoundError,
    ReadinessEvaluationError,
)

router = APIRouter(prefix="/backlog", tags=["backlog"])


def get_backlog_service(session: AsyncSession = Depends(get_db)) -> BacklogService:
    """Dependency injection for BacklogService."""
    return BacklogService(session)


@router.get("/projects/{project_id}", response_model=BacklogListResponse)
async def list_backlog(
    project_id: str,
    issue_type: Optional[str] = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    include_scores: bool = False,
    limit: int = 100,
    offset: int = 0,
    svc: BacklogService = Depends(get_backlog_service),
) -> BacklogListResponse:
    """List backlog issues for a project."""
    issues = await svc.get_backlog(project_id, issue_type, include_scores)

    # Apply pagination
    paginated = issues[offset : offset + limit]
    total = len(issues)
    has_more = (offset + limit) < total

    items = [
        BacklogIssueResponse(
            **{c.key: getattr(i, c.key) for c in i.__table__.columns},
            priority_score=getattr(i, "_priority_score", None)
            and i._priority_score.score,
        )
        for i in paginated
    ]

    return BacklogListResponse(items=items, total=total, has_more=has_more)


@router.post("/projects/{project_id}/estimate", response_model=EstimationResponse)
async def request_estimation(
    project_id: str,
    body: EstimationRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    svc: BacklogService = Depends(get_backlog_service),
) -> EstimationResponse:
    """Request story point estimation for an issue."""
    try:
        result = await svc.request_estimate(body.issue_id)
    except IssueNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return EstimationResponse(
        issue_id=body.issue_id,
        suggested_points=result.suggested_points,
        raw_score=result.raw_score,
        confidence=result.confidence,
        rationale=result.rationale,
        ai_enhanced=result.ai_enhanced,
        ai_refinement_queued=True,
    )


@router.post(
    "/projects/{project_id}/prioritize", response_model=RankedBacklogResponse
)
async def rank_backlog(
    project_id: str,
    body: PrioritizationRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    svc: BacklogService = Depends(get_backlog_service),
) -> RankedBacklogResponse:
    """Get priority-ranked backlog for a project."""
    scores = await svc.get_ranked_backlog(project_id, body.weights)

    return RankedBacklogResponse(
        project_id=project_id,
        total=len(scores),
        items=[
            PriorityScoreResponse(
                issue_id=s.issue_id,
                score=s.score,
                rank=s.rank,
                breakdown=s.breakdown,
            )
            for s in scores
        ],
    )


@router.post("/projects/{project_id}/readiness", response_model=DORCheckResponse)
async def check_readiness(
    project_id: str,
    body: ReadinessCheckRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    svc: BacklogService = Depends(get_backlog_service),
) -> DORCheckResponse:
    """Evaluate an issue against Definition of Ready criteria."""
    try:
        result = await svc.check_readiness(
            body.issue_id, body.actor_id, body.actor_type
        )
    except IssueNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadinessEvaluationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DORCheckResponse(
        issue_id=result.issue_id,
        passed=result.passed,
        failed_criteria=result.failed_criteria,
        checked_at=result.checked_at,
        checked_by_id=result.checked_by_id,
        checked_by_type=result.checked_by_type,
        status_advanced_to_ready=result.passed,
    )


@router.patch(
    "/projects/{project_id}/reorder/{issue_id}", response_model=ReorderResponse
)
async def reorder_item(
    project_id: str,
    issue_id: str,
    body: ReorderRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    svc: BacklogService = Depends(get_backlog_service),
) -> ReorderResponse:
    """Reorder a single backlog item."""
    try:
        issue = await svc.reorder_single(issue_id, body.after_id, body.before_id)
    except IssueNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ReorderResponse(
        issue_id=issue_id,
        new_backlog_rank=issue.backlog_rank,
        success=True,
    )


@router.put("/projects/{project_id}/reorder", response_model=dict)
async def bulk_reorder(
    project_id: str,
    body: BulkReorderRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    svc: BacklogService = Depends(get_backlog_service),
) -> dict:
    """Bulk reorder backlog items (e.g., from drag-drop UI)."""
    await svc.bulk_reorder(project_id, body.ordered_ids)
    return {"success": True, "reordered_count": len(body.ordered_ids)}


@router.post(
    "/projects/{project_id}/sprint-pull", response_model=SprintPullResponse
)
async def pull_into_sprint(
    project_id: str,
    body: SprintPullRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    svc: BacklogService = Depends(get_backlog_service),
) -> SprintPullResponse:
    """Move ready issues into a sprint."""
    moved, skipped = await svc.pull_into_sprint(body.issue_ids, body.sprint_id, body.actor_id)

    return SprintPullResponse(
        sprint_id=body.sprint_id,
        requested=len(body.issue_ids),
        moved=len(moved),
        moved_issue_ids=moved,
        skipped_not_ready=skipped,
    )


@router.delete("/projects/{project_id}/issues/{issue_id}/sprint")
async def remove_from_sprint(
    project_id: str,
    issue_id: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    svc: BacklogService = Depends(get_backlog_service),
) -> dict:
    """Remove an issue from a sprint back to the backlog."""
    try:
        await svc.move_back_to_backlog(issue_id)
    except IssueNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"success": True, "issue_id": issue_id, "moved_to": "backlog"}


# Import these for type hints in responses
from agileai.schemas.backlog import PriorityScoreResponse
