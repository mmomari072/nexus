"""Synchronous HTTP client for AgileAI API."""

from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from agileai.client.exceptions import (
    AgileAIException,
    AuthenticationError,
    NotFoundError,
    ServerError,
    ValidationError,
)


class AgileAIClient:
    """Synchronous client for AgileAI backlog API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        email: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """Initialize the client.

        Args:
            base_url: Base URL of the API (e.g., http://localhost:8000)
            email: Email for authentication
            password: Password for authentication
            token: JWT token (if already authenticated)
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()

        # Add retry logic
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Authenticate if credentials provided
        if email and password and not token:
            self.login(email, password)

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            json: JSON payload for POST/PUT requests
            **kwargs: Additional arguments to pass to requests

        Returns:
            Parsed JSON response

        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If resource not found
            ValidationError: If request validation fails
            ServerError: If server returns 5xx error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = kwargs.pop("headers", {})

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = self.session.request(
                method, url, json=json, headers=headers, **kwargs
            )
        except requests.RequestException as e:
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
        except requests.exceptions.JSONDecodeError:
            return {"status": "ok", "status_code": response.status_code}

    def login(self, email: str, password: str) -> str:
        """Authenticate with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Access token
        """
        result = self._request(
            "POST", "/api/v1/auth/login", json={"email": email, "password": password}
        )
        self.token = result["access_token"]
        return self.token

    def register(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Register a new user.

        Args:
            email: User email
            password: User password
            name: User name

        Returns:
            User data
        """
        return self._request(
            "POST",
            "/api/v1/auth/register",
            json={"email": email, "password": password, "name": name},
        )

    def list_backlog(
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

        return self._request(
            "GET", f"/api/v1/backlog/projects/{project_id}", params=params
        )

    def estimate_issue(
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
            difficulty: Difficulty level (trivial, easy, medium, hard, very_hard, research)
            importance: Importance level (low, medium, high, critical)
            child_count: Number of child issues
            has_external_dependencies: Whether issue has external dependencies
            issue_type: Type of issue (task, story, bug, etc.)

        Returns:
            Estimation response with story points
        """
        return self._request(
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

    def prioritize_backlog(
        self,
        project_id: str,
        difficulty_weight: float = 0.4,
        importance_weight: float = 0.4,
        urgency_weight: float = 0.2,
    ) -> Dict[str, Any]:
        """Get priority-ranked backlog for a project.

        Args:
            project_id: Project ID
            difficulty_weight: Weight for difficulty (0-1)
            importance_weight: Weight for importance (0-1)
            urgency_weight: Weight for urgency (0-1)

        Returns:
            Ranked backlog response
        """
        return self._request(
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

    def check_readiness(
        self,
        project_id: str,
        issue_id: str,
        actor_id: Optional[str] = None,
        actor_type: str = "user",
    ) -> Dict[str, Any]:
        """Check Definition of Ready (DoR) for an issue.

        Args:
            project_id: Project ID
            issue_id: Issue ID
            actor_id: Actor ID (optional)
            actor_type: Type of actor (user, agent, system)

        Returns:
            Readiness check response
        """
        return self._request(
            "POST",
            f"/api/v1/backlog/projects/{project_id}/readiness",
            json={
                "issue_id": issue_id,
                "actor_id": actor_id,
                "actor_type": actor_type,
            },
        )

    def reorder_issue(
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
            after_id: Place after this issue (optional)
            before_id: Place before this issue (optional)

        Returns:
            Reorder response
        """
        return self._request(
            "PATCH",
            f"/api/v1/backlog/projects/{project_id}/reorder/{issue_id}",
            json={"after_id": after_id, "before_id": before_id},
        )

    def bulk_reorder(
        self, project_id: str, ordered_ids: list[str]
    ) -> Dict[str, Any]:
        """Bulk reorder backlog items.

        Args:
            project_id: Project ID
            ordered_ids: List of issue IDs in desired order

        Returns:
            Bulk reorder response
        """
        return self._request(
            "PUT",
            f"/api/v1/backlog/projects/{project_id}/reorder",
            json={"ordered_ids": ordered_ids},
        )

    def pull_into_sprint(
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
        return self._request(
            "POST",
            f"/api/v1/backlog/projects/{project_id}/sprint-pull",
            json={"issue_ids": issue_ids, "sprint_id": sprint_id, "actor_id": actor_id},
        )

    def remove_from_sprint(
        self, project_id: str, issue_id: str
    ) -> Dict[str, Any]:
        """Move an issue from sprint back to backlog.

        Args:
            project_id: Project ID
            issue_id: Issue to remove from sprint

        Returns:
            Remove response
        """
        return self._request(
            "DELETE", f"/api/v1/backlog/projects/{project_id}/issues/{issue_id}/sprint"
        )

    def close(self):
        """Close the client session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
