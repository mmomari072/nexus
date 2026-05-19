"""Tests for backlog services and API endpoints."""

import pytest
import sys
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Add repository root to path so we can import from __init__
sys.path.insert(0, str(Path(__file__).parent.parent))

from __init__ import (
    Base,
    Issue,
    Project,
    User,
    DefinitionOfReady,
    DORCheck,
)
from agileai.services.backlog import (
    BacklogService,
    Difficulty,
    Importance,
    EstimationInput,
    IssueNotFoundError,
    ReadinessEvaluationError,
)
from agileai.services.backlog.domain import FIBONACCI
from agileai.services.backlog.estimation import EstimationService


@pytest.fixture
async def db_session() -> AsyncSession:
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a test project."""
    project = Project(
        id="proj-1",
        slug="test-project",
        status="active",
    )
    db_session.add(project)
    await db_session.commit()
    return project


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id="user-1",
        name="Test User",
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def issue(db_session: AsyncSession, project: Project, user: User) -> Issue:
    """Create a test issue in backlog status."""
    issue = Issue(
        id="issue-1",
        project_id=project.id,
        title="Test Issue",
        description="A test issue for estimation",
        issue_type="task",
        status="backlog",
        priority="medium",
        importance="medium",
        difficulty="medium",
        created_by_id=user.id,
        created_by_type="user",
    )
    db_session.add(issue)
    await db_session.commit()
    return issue


# -- Domain tests (no DB needed) -----------------------------------------------


def test_difficulty_weights():
    """Test difficulty complexity weights."""
    assert Difficulty.TRIVIAL.complexity_weight == 0.5
    assert Difficulty.EASY.complexity_weight == 1.0
    assert Difficulty.MEDIUM.complexity_weight == 2.0
    assert Difficulty.HARD.complexity_weight == 3.5
    assert Difficulty.VERY_HARD.complexity_weight == 5.0
    assert Difficulty.RESEARCH.complexity_weight == 7.0


def test_importance_weights():
    """Test importance urgency weights."""
    assert Importance.CRITICAL.urgency_weight == 4.0
    assert Importance.HIGH.urgency_weight == 3.0
    assert Importance.MEDIUM.urgency_weight == 2.0
    assert Importance.LOW.urgency_weight == 1.0


def test_fibonacci_sequence():
    """Test Fibonacci sequence."""
    assert FIBONACCI == [1, 2, 3, 5, 8, 13, 21]


# -- EstimationService tests --------------------------------------------------


@pytest.mark.asyncio
async def test_estimate_issue_trivial(
    db_session: AsyncSession, issue: Issue
) -> None:
    """Test estimation for a trivial issue."""
    service = EstimationService(db_session, enqueue_ai=False)

    inp = EstimationInput(
        issue_id=issue.id,
        difficulty=Difficulty.TRIVIAL,
        importance=Importance.MEDIUM,
        child_count=0,
        has_external_dependencies=False,
        issue_type="task",
    )

    result = await service.estimate(inp)

    assert result.suggested_points == 1
    assert result.confidence == "high"
    assert "Difficulty=trivial" in result.rationale

    # Verify persisted to DB
    updated_issue = await db_session.get(Issue, issue.id)
    assert updated_issue.story_points == 1


@pytest.mark.asyncio
async def test_estimate_issue_research(
    db_session: AsyncSession, issue: Issue
) -> None:
    """Test estimation for a research issue."""
    service = EstimationService(db_session, enqueue_ai=False)

    inp = EstimationInput(
        issue_id=issue.id,
        difficulty=Difficulty.RESEARCH,
        importance=Importance.HIGH,
        child_count=2,
        has_external_dependencies=True,
        issue_type="spike",
    )

    result = await service.estimate(inp)

    assert result.suggested_points in FIBONACCI
    assert result.confidence == "low" or result.confidence == "medium"


@pytest.mark.asyncio
async def test_estimate_with_children(
    db_session: AsyncSession, project: Project, user: User
) -> None:
    """Test estimation penalizes issues with many children."""
    parent = Issue(
        id="parent-1",
        project_id=project.id,
        title="Parent Issue",
        issue_type="story",
        status="backlog",
        priority="medium",
        importance="medium",
        difficulty="easy",
        created_by_id=user.id,
        created_by_type="user",
    )
    db_session.add(parent)

    # Add children
    for i in range(3):
        child = Issue(
            id=f"child-{i}",
            project_id=project.id,
            parent_issue_id=parent.id,
            title=f"Child {i}",
            issue_type="task",
            status="backlog",
            priority="medium",
            importance="medium",
            difficulty="trivial",
            created_by_id=user.id,
            created_by_type="user",
        )
        db_session.add(child)

    await db_session.commit()

    service = EstimationService(db_session, enqueue_ai=False)

    inp = EstimationInput(
        issue_id=parent.id,
        difficulty=Difficulty.EASY,
        importance=Importance.MEDIUM,
        child_count=3,
        has_external_dependencies=False,
        issue_type="story",
    )

    result = await service.estimate(inp)

    assert result.suggested_points > 1


# -- ReadinessGateService tests -----------------------------------------------


@pytest.mark.asyncio
async def test_dor_missing_criteria(
    db_session: AsyncSession, issue: Issue, user: User
) -> None:
    """Test readiness check fails when no criteria are defined."""
    from agileai.services.backlog.readiness import ReadinessGateService

    service = ReadinessGateService(db_session)

    with pytest.raises(ReadinessEvaluationError):
        await service.evaluate(issue.id, user.id)


@pytest.mark.asyncio
async def test_dor_has_description_criterion(
    db_session: AsyncSession, project: Project, issue: Issue, user: User
) -> None:
    """Test Definition of Ready: has_description criterion."""
    from agileai.services.backlog.readiness import ReadinessGateService

    # Add criterion
    criterion = DefinitionOfReady(
        id="dor-1",
        project_id=project.id,
        criterion="has_description",
        order_index=1,
    )
    db_session.add(criterion)
    await db_session.commit()

    service = ReadinessGateService(db_session)

    # Issue has description, should pass
    result = await service.evaluate(issue.id, user.id)
    assert result.passed
    assert issue.dor_passed


@pytest.mark.asyncio
async def test_dor_has_story_points_criterion(
    db_session: AsyncSession, project: Project, issue: Issue, user: User
) -> None:
    """Test Definition of Ready: has_story_points criterion."""
    from agileai.services.backlog.readiness import ReadinessGateService

    # Add criterion
    criterion = DefinitionOfReady(
        id="dor-1",
        project_id=project.id,
        criterion="has_story_points",
        order_index=1,
    )
    db_session.add(criterion)
    await db_session.commit()

    service = ReadinessGateService(db_session)

    # Issue has no story_points yet, should fail
    result = await service.evaluate(issue.id, user.id)
    assert not result.passed
    assert "has_story_points" in result.failed_criteria

    # Add story points and check again
    issue.story_points = 5
    await db_session.commit()

    result = await service.evaluate(issue.id, user.id)
    assert result.passed


# -- BacklogService tests -----------------------------------------------------


@pytest.mark.asyncio
async def test_backlog_list(
    db_session: AsyncSession, project: Project, issue: Issue
) -> None:
    """Test listing backlog issues."""
    service = BacklogService(db_session)

    backlog = await service.get_backlog(project.id)

    assert len(backlog) == 1
    assert backlog[0].id == issue.id


@pytest.mark.asyncio
async def test_backlog_list_with_scores(
    db_session: AsyncSession, project: Project, issue: Issue
) -> None:
    """Test listing backlog with priority scores."""
    service = BacklogService(db_session)

    backlog = await service.get_backlog(project.id, include_scores=True)

    assert len(backlog) == 1
    assert hasattr(backlog[0], "_priority_score")
    assert backlog[0]._priority_score is not None


@pytest.mark.asyncio
async def test_request_estimate(
    db_session: AsyncSession, issue: Issue
) -> None:
    """Test requesting estimation through BacklogService."""
    service = BacklogService(db_session)

    result = await service.request_estimate(issue.id)

    assert result.suggested_points in FIBONACCI
    assert result.confidence in ("high", "medium", "low")


@pytest.mark.asyncio
async def test_request_estimate_nonexistent(
    db_session: AsyncSession,
) -> None:
    """Test estimation for nonexistent issue raises error."""
    service = BacklogService(db_session)

    with pytest.raises(IssueNotFoundError):
        await service.request_estimate("nonexistent-id")


@pytest.mark.asyncio
async def test_reorder_single(
    db_session: AsyncSession, project: Project, user: User
) -> None:
    """Test reordering a single backlog item."""
    # Create two issues
    issue1 = Issue(
        id="issue-1",
        project_id=project.id,
        title="First",
        issue_type="task",
        status="backlog",
        priority="medium",
        importance="medium",
        difficulty="medium",
        backlog_rank=1000.0,
        created_by_id=user.id,
        created_by_type="user",
    )
    issue2 = Issue(
        id="issue-2",
        project_id=project.id,
        title="Second",
        issue_type="task",
        status="backlog",
        priority="medium",
        importance="medium",
        difficulty="medium",
        backlog_rank=2000.0,
        created_by_id=user.id,
        created_by_type="user",
    )
    db_session.add_all([issue1, issue2])
    await db_session.commit()

    service = BacklogService(db_session)

    # Move issue2 before issue1
    result = await service.reorder_single("issue-2", before_id="issue-1")

    assert result.backlog_rank is not None
    assert result.backlog_rank < issue1.backlog_rank


@pytest.mark.asyncio
async def test_bulk_reorder(
    db_session: AsyncSession, project: Project, user: User
) -> None:
    """Test bulk reordering (entire list)."""
    # Create three issues
    ids = []
    for i in range(3):
        issue = Issue(
            id=f"issue-{i}",
            project_id=project.id,
            title=f"Issue {i}",
            issue_type="task",
            status="backlog",
            priority="medium",
            importance="medium",
            difficulty="medium",
            created_by_id=user.id,
            created_by_type="user",
        )
        db_session.add(issue)
        ids.append(issue.id)

    await db_session.commit()

    service = BacklogService(db_session)

    # Reorder in reverse
    await service.bulk_reorder(project.id, list(reversed(ids)))

    # Verify new ranks
    for i, issue_id in enumerate(reversed(ids), 1):
        issue = await db_session.get(Issue, issue_id)
        assert issue.backlog_rank == float(i * 1000)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
