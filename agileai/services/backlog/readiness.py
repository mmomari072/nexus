"""Definition of Ready evaluation service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

# Import from root package
import sys
from pathlib import Path
_root = Path(__file__).parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from __init__ import (
    DefinitionOfReady,
    DORCheck,
    Issue,
    IssueChangeLog,
    IssueInstruction,
    IssueLink,
    StatusTransition,
)

from .domain import DORCheckResult
from .exceptions import IssueNotFoundError, ReadinessEvaluationError


ActorType = Literal["user", "agent"]


class ReadinessGateService:
    """
    Evaluates whether a backlog issue meets Definition of Ready criteria.

    Evaluation is idempotent: calling evaluate() again replaces prior dor_checks.
    If all criteria pass, the issue status can advance from 'backlog' to 'ready'.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def evaluate(
        self,
        issue_id: str,
        checked_by_id: str,
        checked_by_type: ActorType = "user",
    ) -> DORCheckResult:
        """Evaluate an issue against Definition of Ready criteria."""
        issue = await self._load_issue(issue_id)
        criteria = await self._load_criteria(issue.project_id, issue.issue_type)

        if not criteria:
            raise ReadinessEvaluationError(
                f"No DOR criteria defined for project={issue.project_id} "
                f"type={issue.issue_type}. Define them in definition_of_ready."
            )

        failed = await self._run_checks(issue, criteria, checked_by_id, checked_by_type)
        passed = len(failed) == 0

        issue.dor_passed = passed

        # Advance status if ready and currently in backlog
        if passed and issue.status == "backlog":
            issue.status = "ready"
            self._session.add(
                StatusTransition(
                    issue_id=issue_id,
                    from_status="backlog",
                    to_status="ready",
                    actor_id=checked_by_id,
                    actor_type=checked_by_type,
                    trigger_source="readiness_gate",
                )
            )
            self._session.add(
                IssueChangeLog(
                    issue_id=issue_id,
                    field_name="status",
                    old_value="backlog",
                    new_value="ready",
                    source="readiness_gate",
                    is_diff=False,
                )
            )

        return DORCheckResult(
            issue_id=issue_id,
            passed=passed,
            failed_criteria=failed,
            checked_at=datetime.now(timezone.utc).isoformat(),
            checked_by_id=checked_by_id,
            checked_by_type=checked_by_type,
        )

    async def _load_issue(self, issue_id: str) -> Issue:
        """Load an issue by ID, raising if not found."""
        stmt = select(Issue).where(Issue.id == issue_id)
        issue = (await self._session.execute(stmt)).scalar_one_or_none()
        if not issue:
            raise IssueNotFoundError(issue_id)
        return issue

    async def _load_criteria(
        self, project_id: str, issue_type: str
    ) -> list[DefinitionOfReady]:
        """Load DOR criteria for a project/issue_type combination."""
        stmt = (
            select(DefinitionOfReady)
            .where(
                or_(
                    DefinitionOfReady.project_id == project_id,
                    DefinitionOfReady.project_id.is_(None),
                )
            )
            .where(
                or_(
                    DefinitionOfReady.issue_type == issue_type,
                    DefinitionOfReady.issue_type.is_(None),
                )
            )
            .order_by(DefinitionOfReady.order_index)
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def _run_checks(
        self,
        issue: Issue,
        criteria: list[DefinitionOfReady],
        actor_id: str,
        actor_type: ActorType,
    ) -> list[str]:
        """Evaluate all criteria and record results."""
        # Replace existing checks atomically
        await self._session.execute(delete(DORCheck).where(DORCheck.issue_id == issue.id))

        failed = []
        for criterion in criteria:
            passed = self._evaluate_criterion(issue, criterion.criterion)
            self._session.add(
                DORCheck(
                    issue_id=issue.id,
                    criterion_id=criterion.id,
                    passed=passed,
                    checked_by_id=actor_id,
                )
            )
            if not passed:
                failed.append(criterion.criterion)

        return failed

    def _evaluate_criterion(self, issue: Issue, criterion: str) -> bool:
        """Evaluate a single criterion. Built-in checks below, others return False."""
        criterion_lower = criterion.lower().strip()

        if criterion_lower == "has_description":
            return bool(issue.description and len(issue.description) > 20)

        if criterion_lower == "has_story_points":
            return issue.story_points is not None

        if criterion_lower == "has_assignee":
            return issue.assignee_id is not None

        if criterion_lower == "has_acceptance_criteria":
            return any(
                i.instruction_type == "constraint" and i.is_active
                for i in issue.instructions
            )

        # Unknown criterion: requires manual human verification, return False
        return False
