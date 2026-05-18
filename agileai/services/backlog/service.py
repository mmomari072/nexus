"""BacklogService orchestrator — single entry point for all backlog operations."""

from __future__ import annotations

from typing import Literal, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Import from root package
import sys
from pathlib import Path
_root = Path(__file__).parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from __init__ import Issue, IssueLink, SprintIssue

from .domain import DORCheckResult, EstimationInput, EstimationResult, PriorityScore
from .estimation import EstimationService
from .exceptions import IssueNotFoundError
from .prioritization import PrioritizationService
from .readiness import ReadinessGateService


class BacklogService:
    """
    Orchestrator for all backlog operations.

    Wired via FastAPI dependency injection. All writes commit at router level.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._estimation = EstimationService(session)
        self._prioritization = PrioritizationService(session)
        self._readiness = ReadinessGateService(session)

    # -- Backlog queries -------------------------------------------------------

    async def get_backlog(
        self,
        project_id: str,
        issue_type: Optional[str] = None,
        include_scores: bool = False,
    ) -> list[Issue]:
        """Get backlog issues for a project, optionally with priority scores."""
        stmt = select(Issue).where(
            Issue.project_id == project_id,
            Issue.status.in_(("backlog", "ready")),
            Issue.sprint_id.is_(None),
        )

        if issue_type:
            stmt = stmt.where(Issue.issue_type == issue_type)

        stmt = stmt.order_by(
            Issue.backlog_rank.asc(),
            Issue.created_at.asc(),
        )

        issues = (await self._session.execute(stmt)).scalars().all()

        if include_scores:
            scores = await self._prioritization.rank_backlog(project_id)
            score_map = {s.issue_id: s for s in scores}
            for issue in issues:
                issue._priority_score = score_map.get(issue.id)

        return issues

    # -- Estimation ------------------------------------------------------------

    async def request_estimate(self, issue_id: str) -> EstimationResult:
        """Request a story point estimate for an issue."""
        issue = await self._load(issue_id)

        # Count children
        child_count_result = await self._session.execute(
            select(func.count()).where(Issue.parent_issue_id == issue_id)
        )
        child_count = (child_count_result.scalar() or 0)

        # Check for blocking dependencies
        has_deps = await self._has_blocking_deps(issue_id)

        inp = EstimationInput(
            issue_id=issue_id,
            difficulty=issue.difficulty,  # type: ignore
            importance=issue.importance,  # type: ignore
            child_count=child_count,
            has_external_dependencies=has_deps,
            issue_type=issue.issue_type,
        )

        return await self._estimation.estimate(inp)

    # -- Prioritization --------------------------------------------------------

    async def get_ranked_backlog(
        self,
        project_id: str,
        weights: Optional[dict[str, float]] = None,
    ) -> list[PriorityScore]:
        """Get ranked priority scores for all backlog issues."""
        return await self._prioritization.rank_backlog(project_id, weights)

    # -- Readiness gate --------------------------------------------------------

    async def check_readiness(
        self,
        issue_id: str,
        actor_id: str,
        actor_type: Literal["user", "agent"] = "user",
    ) -> DORCheckResult:
        """Evaluate an issue against Definition of Ready criteria."""
        return await self._readiness.evaluate(issue_id, actor_id, actor_type)

    # -- Sprint operations -----------------------------------------------------

    async def pull_into_sprint(
        self, issue_ids: list[str], sprint_id: str, actor_id: str
    ) -> tuple[list[str], list[str]]:
        """
        Move ready issues into a sprint. Enforces dor_passed=True.
        Returns (moved_ids, skipped_ids).
        """
        moved = []
        skipped = []

        for issue_id in issue_ids:
            issue = await self._load(issue_id)

            if not issue.dor_passed:
                skipped.append(issue_id)
                continue

            issue.sprint_id = sprint_id
            issue.status = "ready"
            self._session.add(SprintIssue(sprint_id=sprint_id, issue_id=issue_id))
            moved.append(issue_id)

        return moved, skipped

    async def move_back_to_backlog(self, issue_id: str) -> Issue:
        """Move an issue from a sprint back to the backlog."""
        issue = await self._load(issue_id)
        issue.sprint_id = None
        issue.status = "backlog"
        return issue

    # -- Ordering operations --------------------------------------------------

    async def reorder_single(
        self,
        issue_id: str,
        after_id: Optional[str] = None,
        before_id: Optional[str] = None,
    ) -> Issue:
        """
        Reorder a single issue using fractional indexing.
        after_id = move after this issue, before_id = move before this issue.
        """
        issue = await self._load(issue_id)

        if after_id is None and before_id is None:
            # Move to top
            issue.backlog_rank = 1.0
        elif after_id is not None and before_id is not None:
            # Insert between
            after = await self._load(after_id)
            before = await self._load(before_id)

            after_rank = after.backlog_rank or 0.0
            before_rank = before.backlog_rank or 1000.0

            new_rank = (after_rank + before_rank) / 2.0

            if abs(new_rank - after_rank) < 0.001:
                # Gap exhausted, need rebalance
                await self._rebalance_ranks(issue.project_id)
                # Recurse
                return await self.reorder_single(issue_id, after_id, before_id)

            issue.backlog_rank = new_rank
        elif before_id is not None:
            # Move before this issue
            before = await self._load(before_id)
            before_rank = before.backlog_rank or 1000.0
            issue.backlog_rank = (before_rank - 1.0) if before_rank > 1.0 else 0.5
        elif after_id is not None:
            # Move after this issue
            after = await self._load(after_id)
            after_rank = after.backlog_rank or 0.0
            issue.backlog_rank = (after_rank + 1.0)

        return issue

    async def bulk_reorder(self, project_id: str, ordered_ids: list[str]) -> None:
        """
        Bulk reorder: reassign ranks 1000, 2000, 3000... for a full list.
        Used by drag-and-drop reorder of entire board.
        """
        for i, issue_id in enumerate(ordered_ids, 1):
            issue = await self._load(issue_id)
            if issue.project_id != project_id:
                continue  # silently skip issues from other projects
            issue.backlog_rank = float(i * 1000)

    # -- Private helpers -------------------------------------------------------

    async def _load(self, issue_id: str) -> Issue:
        """Load an issue by ID, raising if not found."""
        stmt = select(Issue).where(Issue.id == issue_id)
        issue = (await self._session.execute(stmt)).scalar_one_or_none()
        if not issue:
            raise IssueNotFoundError(issue_id)
        return issue

    async def _has_blocking_deps(self, issue_id: str) -> bool:
        """Check if issue has any blocking dependencies."""
        stmt = select(IssueLink).where(
            IssueLink.source_id == issue_id,
            IssueLink.link_type == "is_blocked_by",
        )
        result = await self._session.execute(stmt)
        return result.first() is not None

    async def _rebalance_ranks(self, project_id: str) -> None:
        """
        Rebalance fractional ranks to evenly-spaced integers (1000, 2000, ...).
        Called when gaps become too small to insert between items.
        """
        stmt = (
            select(Issue)
            .where(Issue.project_id == project_id)
            .order_by(Issue.backlog_rank.asc())
        )
        issues = (await self._session.execute(stmt)).scalars().all()

        for i, issue in enumerate(issues, 1):
            issue.backlog_rank = float(i * 1000)
