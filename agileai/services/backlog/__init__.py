"""Backlog service package — Clean Architecture for backlog management."""

# Import from domain (no external dependencies)
from .domain import Difficulty, Importance, EstimationInput, EstimationResult, PriorityScore, DORCheckResult  # noqa: F401
from .exceptions import BacklogError, IssueNotFoundError, ReadinessEvaluationError, EstimationError  # noqa: F401

# Lazy import service to avoid circular dependencies with models
def __getattr__(name):
    if name == "BacklogService":
        from .service import BacklogService
        return BacklogService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "BacklogService",
    "Difficulty",
    "Importance",
    "EstimationInput",
    "EstimationResult",
    "PriorityScore",
    "DORCheckResult",
    "BacklogError",
    "IssueNotFoundError",
    "ReadinessEvaluationError",
    "EstimationError",
]
