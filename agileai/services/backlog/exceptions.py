"""Exceptions for backlog operations."""


class BacklogError(Exception):
    """Base exception for all backlog service errors."""


class IssueNotFoundError(BacklogError):
    """Raised when an issue cannot be found."""

    def __init__(self, issue_id: str) -> None:
        super().__init__(f"Issue not found: {issue_id}")
        self.issue_id = issue_id


class ReadinessEvaluationError(BacklogError):
    """Raised when Definition of Ready evaluation fails or criteria are misconfigured."""


class EstimationError(BacklogError):
    """Raised when story point estimation inputs are invalid."""
