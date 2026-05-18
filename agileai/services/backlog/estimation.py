"""Story point estimation service. Heuristic algorithm + optional AI refinement."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import from root package
import sys
from pathlib import Path
_root = Path(__file__).parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from __init__ import BackgroundJob, Issue, IssueChangeLog

from .domain import FIBONACCI, Difficulty, EstimationInput, EstimationResult, Importance


class EstimationService:
    """
    Derives story point estimates from issue signals.

    Two paths:
    1. Synchronous heuristic: instant, deterministic
    2. Async AI refinement: queues a background_job for the Assistant agent
    """

    def __init__(self, session: AsyncSession, enqueue_ai: bool = True) -> None:
        self._session = session
        self._enqueue_ai = enqueue_ai

    async def estimate(self, inp: EstimationInput) -> EstimationResult:
        """Estimate story points for an issue."""
        result = self._heuristic_estimate(inp)
        await self._persist_estimate(inp.issue_id, result)
        if self._enqueue_ai:
            await self._enqueue_ai_refinement(inp.issue_id)
        return result

    def _heuristic_estimate(self, inp: EstimationInput) -> EstimationResult:
        """Synchronous heuristic estimation based on difficulty, importance, and structure."""
        base = inp.difficulty.complexity_weight
        importance_modifier = 1.0 + (inp.importance.urgency_weight - 2.0) * 0.1
        child_overhead = min(inp.child_count * 0.3, 3.0)
        dep_overhead = 1.5 if inp.has_external_dependencies else 0.0
        spike_modifier = 1.5 if inp.issue_type == "spike" else 1.0

        raw = (base + child_overhead + dep_overhead) * importance_modifier * spike_modifier

        # Snap to nearest Fibonacci
        points = min(FIBONACCI, key=lambda f: abs(f - raw))

        confidence = (
            "high"
            if inp.difficulty != Difficulty.RESEARCH
            else ("low" if raw > 13 else "medium")
        )
        rationale = (
            f"Difficulty={inp.difficulty.value} (weight={base:.1f}), "
            f"children={inp.child_count}, dependencies={'yes' if inp.has_external_dependencies else 'no'}, "
            f"raw_score={raw:.2f} → nearest Fibonacci={points}"
        )

        return EstimationResult(
            suggested_points=points,
            raw_score=raw,
            confidence=confidence,
            rationale=rationale,
        )

    async def _persist_estimate(
        self, issue_id: str, result: EstimationResult
    ) -> None:
        """Persist the estimate to the database."""
        stmt = select(Issue).where(Issue.id == issue_id)
        row = (await self._session.execute(stmt)).scalar_one()
        old_points = row.story_points
        row.story_points = result.suggested_points

        self._session.add(
            IssueChangeLog(
                issue_id=issue_id,
                field_name="story_points",
                old_value=str(old_points) if old_points is not None else None,
                new_value=str(result.suggested_points),
                source="estimation_service",
                is_diff=False,
            )
        )

    async def _enqueue_ai_refinement(self, issue_id: str) -> None:
        """Queue an AI refinement job via the Assistant agent."""
        job = BackgroundJob(
            job_type="ai_estimate",
            entity_type="issue",
            entity_id=issue_id,
            status="pending",
            priority=5,
        )
        self._session.add(job)
