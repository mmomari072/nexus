"""Client exceptions for AgileAI."""


class AgileAIException(Exception):
    """Base exception for AgileAI client."""

    pass


class AuthenticationError(AgileAIException):
    """Raised when authentication fails."""

    pass


class NotFoundError(AgileAIException):
    """Raised when a resource is not found."""

    pass


class ValidationError(AgileAIException):
    """Raised when request validation fails."""

    pass


class ServerError(AgileAIException):
    """Raised when server returns 5xx error."""

    pass
