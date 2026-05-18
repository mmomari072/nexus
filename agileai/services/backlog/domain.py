"""Domain logic and value objects for backlog operations. Zero dependencies on AgileAI codebase."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Difficulty(str, Enum):
    """Issue difficulty levels with complexity weights."""

    TRIVIAL = "trivial"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    RESEARCH = "research"

    @property
    def complexity_weight(self) -> float:
        """Relative complexity: higher = more complex."""
        return {
            "trivial": 0.5,
            "easy": 1.0,
            "medium": 2.0,
            "hard": 3.5,
            "very_hard": 5.0,
            "research": 7.0,
        }[self.value]


class Importance(str, Enum):
    """Issue importance levels with urgency weights."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def urgency_weight(self) -> float:
        """Relative urgency: higher = more urgent."""
        return {
            "critical": 4.0,
            "high": 3.0,
            "medium": 2.0,
            "low": 1.0,
        }[self.value]


# Fibonacci sequence for story point estimation
FIBONACCI = [1, 2, 3, 5, 8, 13, 21]


@dataclass(frozen=True)
class EstimationInput:
    """Inputs to the estimation algorithm. Pure value object."""

    issue_id: str
    difficulty: Difficulty
    importance: Importance
    child_count: int
    has_external_dependencies: bool
    issue_type: str


@dataclass(frozen=True)
class EstimationResult:
    """Result of story point estimation. Pure value object."""

    suggested_points: int
    raw_score: float
    confidence: str  # 'high' | 'medium' | 'low'
    rationale: str
    ai_enhanced: bool = False


@dataclass(frozen=True)
class PriorityScore:
    """Computed priority score for a backlog item."""

    issue_id: str
    score: float  # 0.0–100.0, higher = do sooner
    rank: int  # Ordinal position within project backlog
    breakdown: dict[str, float]  # Component scores: {"importance": 40.0, ...}


@dataclass(frozen=True)
class DORCheckResult:
    """Result of Definition of Ready evaluation."""

    issue_id: str
    passed: bool
    failed_criteria: list[str]
    checked_at: str  # ISO datetime
    checked_by_id: str
    checked_by_type: str  # 'user' | 'agent'
