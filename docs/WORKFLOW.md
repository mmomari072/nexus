# Development Workflow

How agents and humans collaborate on the AgileAI project.

---

## Git Workflow

### Branch Strategy

```
main
├── feature/phase-3-cli          ← Agent Alpha, Sprint 1
├── feature/phase-4-tui          ← Agent Beta, Sprint 1
├── feature/phase-5-desktop      ← Agent Gamma, Sprint 2
├── feature/phase-6-gateway      ← Agent Alpha, Sprint 2
├── feature/phase-7-telegram     ← Agent Beta, Sprint 2
├── feature/phase-8-compression  ← Agent Gamma, Sprint 3
├── feature/phase-9-api-expansion ← Agent Delta, ongoing
└── fix/<short-description>      ← any agent, bug fixes
```

### Rules
- **`main` is always green.** CI must pass before merge.
- **No force-push to `main`.** Ever.
- **Feature branches off `main`.** Pull latest before branching:
  ```bash
  git checkout main && git pull origin main
  git checkout -b feature/phase-3-cli
  ```
- **Commit often.** Small commits are easier to review.
- **Sign commits** with your agent name in the trailers:
  ```
  Co-Authored-By: Agent Alpha <noreply@anthropic.com>
  ```

---

## Commit Message Format

```
<type>(<scope>): <subject>

<body — optional, max 72 chars/line>

Co-Authored-By: Agent <Name> <noreply@anthropic.com>
```

### Types
| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `test` | Tests only |
| `docs` | Documentation |
| `refactor` | No new features/bugs |
| `perf` | Performance improvement |
| `chore` | Build, deps, config |

### Examples
```
feat(cli): add backlog list command with Rich table output

Implements agileai backlog list <project_id> using sync_client.
Renders issues as Rich.Table with status color coding.

Co-Authored-By: Agent Alpha <noreply@anthropic.com>
```

```
fix(web): handle missing project_id in sprint create route

Sprint creation was failing with 422 when project_id was not
in the form body. Added hidden input and server-side fallback.

Co-Authored-By: Agent Alpha <noreply@anthropic.com>
```

---

## Pull Request Process

### Opening a PR

1. Push your branch:
   ```bash
   git push -u origin feature/phase-3-cli
   ```

2. Open PR with this template:

```markdown
## Summary
- What this PR does (2-3 bullets)
- Which board items it closes (e.g., closes S1-01, S1-02)

## Type of change
- [ ] New feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Tests
- [ ] Docs

## Test plan
- [ ] `pytest tests/` passes
- [ ] Manually tested: describe what you ran
- [ ] New tests added: list test names

## Screenshots / output (if UI change)
Paste `agileai backlog list proj-1` output or screenshot here.

🤖 Generated with Claude Code (Agent Alpha)
```

3. Assign reviewer: **Agent Epsilon**

### Review SLA
- Agent Epsilon reviews within the same session if online.
- Human coordinator reviews within 24 hours for merges.

### Merge Criteria
- [ ] Agent Epsilon approved (✅ comment)
- [ ] `pytest` green
- [ ] No merge conflicts with `main`
- [ ] PR description complete

---

## Testing Requirements

### All PRs must include tests

| Code type | Test location | Minimum |
|-----------|--------------|---------|
| API router | `tests/test_<name>.py` | 5 tests |
| CLI command | `tests/test_cli.py` | 2 tests per command |
| Service layer | `tests/test_<service>.py` | 3 tests |
| TUI screen | Manual (document steps) | N/A |

### Running tests
```bash
# Specific module
pytest tests/test_backlog.py -v

# All tests
pytest -v

# With coverage
pytest --cov=agileai --cov-report=term-missing

# Fast (no slow DB tests)
pytest -m "not slow"
```

### Writing async tests
```python
import pytest
from httpx import AsyncClient, ASGITransport
from agileai.api.main import app

@pytest.mark.asyncio
async def test_sprint_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/sprints/projects/proj-1",
                                headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert "sprints" in resp.json()
```

---

## Code Style

### Formatting
```bash
black agileai/ tests/       # format
ruff check agileai/ tests/  # lint
mypy agileai/               # type check (slow, run before PR)
```

### Line length: 100 characters (configured in pyproject.toml)

### Import order (isort style)
```python
# 1. stdlib
from datetime import datetime
from typing import Optional

# 2. third-party
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 3. local — root models
from __init__ import Issue, Sprint

# 4. local — agileai package
from agileai.api.dependencies import get_db
from agileai.services.backlog.service import BacklogService
```

### No bare excepts
```python
# Bad
try:
    result = await db.execute(...)
except:
    pass

# Good
try:
    result = await db.execute(...)
except SQLAlchemyError as e:
    logger.warning("DB query failed: %s", e)
    return []
```

---

## Environment Setup

### First time
```bash
git clone https://github.com/mmomari072/nexus.git
cd nexus
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Start server
```bash
python -m uvicorn agileai.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Environment variables
Copy `.env.example` to `.env` and fill in:
```bash
cp .env.example .env
```

Key variables:
```
SECRET_KEY=change-me-in-production
DATABASE_URL=sqlite+aiosqlite:///agileai.db
OLLAMA_BASE_URL=http://localhost:11434
TELEGRAM_BOT_TOKEN=optional
```

---

## Agent Coordination Protocol

### Handoffs
When one agent's task depends on another agent's output:

1. **Blocking agent** creates a task in `docs/BOARD.md` with the dependency noted.
2. **Blocked agent** posts in `docs/PROJECT_LOG.md`:
   ```
   ## 2026-05-23 Impediment
   Agent Beta TUI is blocked on Sprint API (S1-10) from Agent Delta.
   Will work on AgentsScreen while waiting.
   ```
3. **Unblocking agent** mentions the completion in their next commit message and updates BOARD.md.

### Context handoff between sessions
If an agent needs to hand off mid-task to another agent:

1. Write a clear `## Handoff Note` at the top of `docs/PROJECT_LOG.md`
2. Include: current branch, what's done, what's next, any gotchas
3. The receiving agent reads this before starting

### Conflict resolution
If two agents need to touch the same file:
1. One agent handles it (assign ownership in BOARD.md)
2. The other adapts to the merged result
3. If unavoidable, the Reviewer (Agent Epsilon) arbitrates

---

## Release Process

### Version bumps
Update `pyproject.toml` version, then:
```bash
git tag -a v0.2.0 -m "Release v0.2.0: CLI + TUI functional"
git push origin v0.2.0
```

### Changelog format (CHANGELOG.md, to be created at v0.2.0)
```markdown
## [0.2.0] - 2026-06-06

### Added
- CLI: full backlog and sprint commands
- TUI: all 6 screens navigable

### Fixed
- Web: sprint creation now handles missing dates gracefully
```

---

## Useful Commands

```bash
# Check which routes are registered
python -c "from agileai.api.main import app; [print(r.path) for r in app.routes if hasattr(r,'path')]"

# Reset database (removes all data)
rm -f agileai.db agileai.db-shm agileai.db-wal

# Check model imports
python -c "from __init__ import Sprint, Agent, AIModel; print('OK')"

# Run server with debug logging
PYTHONDONTWRITEBYTECODE=1 python -m uvicorn agileai.api.main:app --reload --log-level debug

# Inspect a table via admin
open http://localhost:8000/admin/sprints

# Run specific test
pytest tests/test_backlog.py::test_list_backlog -v
```
