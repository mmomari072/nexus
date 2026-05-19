# AgileAI API Documentation

## Quick Start

### Run the FastAPI server:
```bash
cd H:\MyCodes\MyGitHub\nexus
.venv_main\Scripts\python -m uvicorn agileai.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the API:
- **Root**: http://localhost:8000/
- **Docs (Swagger UI)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## API Endpoints

### System Endpoints

#### Health Check
```
GET /health
```
Returns server health status.

#### API Info
```
GET /
```
Returns API information and links.

---

### Backlog API (`/api/v1/backlog`)

#### List Backlog
```
GET /api/v1/backlog/projects/{project_id}
Query Parameters:
  - issue_type: str (optional) - Filter by issue type (task, bug, feature, etc.)
  - include_scores: bool (optional) - Include priority scores in response
```
Returns all backlog items for a project.

#### Request Estimation
```
POST /api/v1/backlog/projects/{project_id}/estimate
Body:
{
  "issue_id": "string",
  "difficulty": "trivial|easy|medium|hard|very_hard|research",
  "importance": "low|medium|high|critical",
  "child_count": 0,
  "has_external_dependencies": false,
  "issue_type": "task"
}
```
Estimates story points for an issue using the heuristic algorithm.

#### Prioritize Backlog
```
POST /api/v1/backlog/projects/{project_id}/prioritize
Body:
{
  "issue_id": "string",
  "importance": "low|medium|high|critical",
  "value_rating": 1-10,
  "urgency_rating": 1-10
}
```
Computes priority score for backlog ranking.

#### Check Readiness
```
POST /api/v1/backlog/projects/{project_id}/readiness
Body:
{
  "issue_id": "string",
  "user_id": "string"
}
```
Evaluates Definition of Ready criteria for an issue.

#### Reorder Single Item
```
POST /api/v1/backlog/projects/{project_id}/reorder/{issue_id}
Body:
{
  "before_id": "string (optional)" | "after_id": "string (optional)"
}
```
Moves a backlog item before or after another item.

#### Bulk Reorder
```
POST /api/v1/backlog/projects/{project_id}/reorder
Body:
{
  "issue_ids": ["string"]
}
```
Reorders the entire backlog by a new priority sequence.

#### Pull Into Sprint
```
POST /api/v1/backlog/projects/{project_id}/issues/{issue_id}/sprint
Body:
{
  "sprint_id": "string"
}
```
Moves an issue from backlog into an active sprint.

---

## Response Examples

### Success Response (200 OK)
```json
{
  "issue_id": "issue-1",
  "suggested_points": 5,
  "confidence": "high",
  "rationale": "Difficulty=medium (weight=2.0), children=0, dependencies=no, raw_score=2.40"
}
```

### Error Response (4xx/5xx)
```json
{
  "detail": "Issue not found"
}
```

---

## Database

- **Type**: SQLite with aiosqlite
- **Location**: `./agileai.db` (or set via `AGILEAI_DB_PATH` env var)
- **Auto-initialization**: Database tables created on server startup

---

## Environment Variables

- `AGILEAI_DB_PATH`: Path to SQLite database (default: `./agileai.db`)
- `AGILEAI_SQL_ECHO`: Enable SQLAlchemy query logging (default: empty/disabled)

---

## Testing

Run the full test suite:
```bash
cd H:\MyCodes\MyGitHub\nexus
.venv_main\Scripts\pytest tests/test_backlog.py -v
```

**Status**: All 15 tests passing ✓

---

## Architecture

- **Framework**: FastAPI with uvicorn
- **Database**: SQLAlchemy 2.0 async ORM with SQLite
- **Models**: 85 SQLAlchemy models in root package
- **Services**: Clean architecture with orchestrator pattern
- **Validation**: Pydantic schemas for request/response validation

---

## Development

The backlog feature implements full estimation, prioritization, and readiness gating:

1. **Estimation Service**: Heuristic algorithm based on difficulty, importance, dependencies
2. **Prioritization Service**: Multi-factor scoring for backlog ranking
3. **Readiness Gate**: Definition of Ready evaluation against configurable criteria
4. **Backlog Service**: Orchestrator combining all three services

See DEVELOPMENT_REPORT.md for implementation details.
