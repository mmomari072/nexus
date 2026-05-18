"""Priority scoring service. Deterministic weighted prioritization algorithm."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Import from root package
import sys
from pathlib import Path
_root = Path(__file__).parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from __init__ import Issue, IssueLink

from .domain import Difficulty, Importance, PriorityScore


@dataclass
class _IssueFacts:
    """Internal: facts about an issue needed for scoring."""

    id: str
    importance: str
    difficulty: str
    story_points: Optional[int]
    due_date_days: Optional[int]
    blocks_count: int


class PrioritizationService:
    """
    Computes deterministic priority scores for backlog issues.

    Formula (0–100):
      importance_weight  × 40
      urgency_weight     × 25   (due date proximity)
      value_weight       × 20   (how many issues this unblocks)
      difficulty_weight  × 15   (inverse: easier = higher score for momentum)
    """

    WEIGHTS = {
        "importance": 40.0,
        "urgency": 25.0,
        "value": 20.0,
        "ease": 15.0,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def rank_backlog(
        self,
        project_id: str,
        weights: Optional[dict[str, float]] = None,
    ) -> list[PriorityScore]:
        """Rank all backlog issues for a project by priority score."""
        w = {**self.WEIGHTS, **(weights or {})}
        facts = await self._load_facts(project_id)

        # Score each issue
        scored = []
        for fact in facts:
            score = self._score_issue(fact, w)
            scored.append((fact.id, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1][0], reverse=True)

        # Build results with ranks
        results = []
        for rank, (issue_id, (score, breakdown)) in enumerate(scored, 1):
            results.append(
                PriorityScore(
                    issue_id=issue_id,
                    score=round(score, 2),
                    rank=rank,
                    breakdown={k: round(v, 2) for k, v in breakdown.items()},
                )
            )

        return results

    async def _load_facts(self, project_id: str) -> list[_IssueFacts]:
        """Load facts about all backlog issues in a project."""
        # Get all backlog issues
        stmt = select(Issue).where(
            Issue.project_id == project_id,
            Issue.status == "backlog",
        )
        issues = (await self._session.execute(stmt)).scalars().all()

        # Load blocking relationships
        blocks_map = {}
        for issue in issues:
            count_stmt = select(func.count()).select_from(IssueLink).where(
                and_(
                    IssueLink.source_id == issue.id,
                    IssueLink.link_type == "blocks",
                )
            )
            count = (await self._session.execute(count_stmt)).scalar() or 0
            blocks_map[issue.id] = count

        # Convert to facts
        facts = []
        for issue in issues:
            due_days = None
            if issue.due_date:
                delta = (issue.due_date - datetime.now(timezone.utc)).days
                due_days = delta

            facts.append(
                _IssueFacts(
                    id=issue.id,
                    importance=issue.importance,
                    difficulty=issue.difficulty,
                    story_points=issue.story_points,
                    due_date_days=due_days,
                    blocks_count=blocks_map.get(issue.id, 0),
                )
            )

        return facts

    def _score_issue(
        self, fact: _IssueFacts, weights: dict[str, float]
    ) -> tuple[float, dict[str, float]]:
        """Score a single issue. Returns (total_score, breakdown)."""
        importance = Importance(fact.importance)
        difficulty = Difficulty(fact.difficulty)

        importance_score = (importance.urgency_weight / 4.0) * weights["importance"]
        ease_score = (1.0 - difficulty.complexity_weight / 7.0) * weights["ease"]
        urgency_score = self._urgency_score(fact.due_date_days) * weights["urgency"]
        value_score = min(fact.blocks_count / 5.0, 1.0) * weights["value"]

        total = importance_score + ease_score + urgency_score + value_score

        breakdown = {
            "importance": importance_score,
            "urgency": urgency_score,
            "value": value_score,
            "ease": ease_score,
        }

        return (total, breakdown)

    @staticmethod
    def _urgency_score(due_date_days: Optional[int]) -> float:
        """Convert days until due date to urgency score (0.0–1.0)."""
        if due_date_days is None:
            return 0.0
        if due_date_days <= 0:
            return 1.0
        if due_date_days <= 3:
            return 0.9
        if due_date_days <= 7:
            return 0.7
        if due_date_days <= 14:
            return 0.4
        return 0.1
