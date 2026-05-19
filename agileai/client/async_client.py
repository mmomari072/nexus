"""Asynchronous HTTP client for AgileAI API."""

from typing import Any, Dict, Optional

import httpx

from agileai.client.exceptions import (
    AgileAIException,
    AuthenticationError,
    NotFoundError,
    ServerError,
    ValidationError,
)


class AsyncAgileAIClient:
    """Asynchronous client for AgileAI backlog API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        email: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """Initialize the async client.

        Args:
            base_url: Base URL of the API
            email: Email for authentication
            password: Password for authentication
            token: JWT token (if already authenticated)
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.email = email
        self.password = password

        # Retry configuration
        transport = httpx.HTTPTransport(
            limits=httpx.Limits(max_keepalive_connections=5),
            retries=3,
        )
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            transport=transport,
            timeout=30,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the client session."""
        await self.client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            json: JSON payload for POST/PUT requests
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Parsed JSON response
        """
        headers = kwargs.pop("headers", {})

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = await self.client.request(
                method, endpoint, json=json, headers=headers, **kwargs
            )
        except httpx.RequestError as e:
            raise AgileAIException(f"Request failed: {e}") from e

        # Handle different status codes
        if response.status_code == 401:
            raise AuthenticationError("Unauthorized - check your credentials")
        elif response.status_code == 404:
            raise NotFoundError(f"Resource not found: {response.text}")
        elif response.status_code == 422:
            raise ValidationError(f"Validation failed: {response.text}")
        elif response.status_code >= 500:
            raise ServerError(f"Server error ({response.status_code}): {response.text}")
        elif response.status_code >= 400:
            raise AgileAIException(f"HTTP {response.status_code}: {response.text}")

        try:
            return response.json()
        except ValueError:
            return {"status": "ok", "status_code": response.status_code}

    async def login(self, email: str, password: str) -> str:
        """Authenticate with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Access token
        """
        result = await self._request(
            "POST", "/api/v1/auth/login", json={"email": email, "password": password}
        )
        self.token = result["access_token"]
        self.email = email
        self.password = password
        return self.token

    async def register(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Register a new user.

        Args:
            email: User email
            password: User password
            name: User name

        Returns:
            User data
        """
        return await self._request(
            "POST",
            "/api/v1/auth/register",
            json={"email": email, "password": password, "name": name},
        )

    async def list_backlog(
        self,
        project_id: str,
        issue_type: Optional[str] = None,
        include_scores: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List backlog issues for a project.

        Args:
            project_id: Project ID
            issue_type: Filter by issue type (optional)
            include_scores: Include priority scores (optional)
            limit: Number of results (default 100)
            offset: Pagination offset (default 0)

        Returns:
            Backlog list response
        """
        params = {
            "include_scores": include_scores,
            "limit": limit,
            "offset": offset,
        }
        if issue_type:
            params["issue_type"] = issue_type

        return await self._request(
            "GET", f"/api/v1/backlog/projects/{project_id}", params=params
        )

    async def estimate_issue(
        self,
        project_id: str,
        issue_id: str,
        difficulty: str,
        importance: str,
        child_count: int = 0,
        has_external_dependencies: bool = False,
        issue_type: str = "task",
    ) -> Dict[str, Any]:
        """Request story point estimation for an issue.

        Args:
            project_id: Project ID
            issue_id: Issue ID
            difficulty: Difficulty level
            importance: Importance level
            child_count: Number of child issues
            has_external_dependencies: Whether issue has external dependencies
            issue_type: Type of issue

        Returns:
            Estimation response
        """
        return await self._request(
            "POST",
            f"/api/v1/backlog/projects/{project_id}/estimate",
            json={
                "issue_id": issue_id,
                "difficulty": difficulty,
                "importance": importance,
                "child_count": child_count,
                "has_external_dependencies": has_external_dependencies,
                "issue_type": issue_type,
            },
        )

    async def prioritize_backlog(
        self,
        project_id: str,
        difficulty_weight: float = 0.4,
        importance_weight: float = 0.4,
        urgency_weight: float = 0.2,
    ) -> Dict[str, Any]:
        """Get priority-ranked backlog for a project.

        Args:
            project_id: Project ID
            difficulty_weight: Weight for difficulty
            importance_weight: Weight for importance
            urgency_weight: Weight for urgency

        Returns:
            Ranked backlog response
        """
        return await self._request(
            "POST",
            f"/api/v1/backlog/projects/{project_id}/prioritize",
            json={
                "weights": {
                    "difficulty": difficulty_weight,
                    "importance": importance_weight,
                    "urgency": urgency_weight,
                }
            },
        )

    async def check_readiness(
        self,
        project_id: str,
        issue_id: str,
        actor_id: Optional[str] = None,
        actor_type: str = "user",
    ) -> Dict[str, Any]:
        """Check Definition of Ready for an issue.

        Args:
            project_id: Project ID
            issue_id: Issue ID
            actor_id: Actor ID (optional)
            actor_type: Type of actor

        Returns:
            Readiness check response
        """
        return await self._request(
            "POST",
            f"/api/v1/backlog/projects/{project_id}/readiness",
            json={
                "issue_id": issue_id,
                "actor_id": actor_id,
                "actor_type": actor_type,
            },
        )

    async def reorder_issue(
        self,
        project_id: str,
        issue_id: str,
        after_id: Optional[str] = None,
        before_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Reorder a single backlog issue.

        Args:
            project_id: Project ID
            issue_id: Issue to reorder
            after_id: Place after this issue
            before_id: Place before this issue

        Returns:
            Reorder response
        """
        return await self._request(
            "PATCH",
            f"/api/v1/backlog/projects/{project_id}/reorder/{issue_id}",
            json={"after_id": after_id, "before_id": before_id},
        )

    async def bulk_reorder(
        self, project_id: str, ordered_ids: list[str]
    ) -> Dict[str, Any]:
        """Bulk reorder backlog items.

        Args:
            project_id: Project ID
            ordered_ids: List of issue IDs in desired order

        Returns:
            Bulk reorder response
        """
        return await self._request(
            "PUT",
            f"/api/v1/backlog/projects/{project_id}/reorder",
            json={"ordered_ids": ordered_ids},
        )

    async def pull_into_sprint(
        self,
        project_id: str,
        issue_ids: list[str],
        sprint_id: str,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Move ready issues into a sprint.

        Args:
            project_id: Project ID
            issue_ids: List of issue IDs to move
            sprint_id: Target sprint ID
            actor_id: Actor ID (optional)

        Returns:
            Sprint pull response
        """
        return await self._request(
            "POST",
            f"/api/v1/backlog/projects/{project_id}/sprint-pull",
            json={"issue_ids": issue_ids, "sprint_id": sprint_id, "actor_id": actor_id},
        )

    async def remove_from_sprint(
        self, project_id: str, issue_id: str
    ) -> Dict[str, Any]:
        """Move an issue from sprint back to backlog.

        Args:
            project_id: Project ID
            issue_id: Issue to remove from sprint

        Returns:
            Remove response
        """
        return await self._request(
            "DELETE", f"/api/v1/backlog/projects/{project_id}/issues/{issue_id}/sprint"
        )
