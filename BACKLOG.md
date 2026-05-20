# Backlog Feature Implementation

## Overview

The AgileAI backlog feature implements a comprehensive, scalable backlog management system using Clean Architecture principles. It enables teams to organize, prioritize, estimate, and refine issues before sprint planning.

## Architecture

### Four-Service Composition Pattern

The backlog system is built around four focused services, each with a single responsibility:

```
BacklogService (Orchestrator)
├── EstimationService     → Derives story point estimates
├── PrioritizationService → Computes weighted priority scores  
├── ReadinessGateService  → Evaluates Definition of Ready
└── Core operations       → Reordering, sprint pull-in
```

### Layer Structure

```
FastAPI Router (agileai/api/routers/backlog.py)
    ↓
Pydantic Schemas (agileai/schemas/backlog.py)
    ↓
BacklogService (agileai/services/backlog/service.py)
    ├── EstimationService (estimation.py)
    ├── PrioritizationService (prioritization.py)
    └── ReadinessGateService (readiness.py)
    ↓
Domain Objects (agileai/services/backlog/domain.py)
    ↓
SQLAlchemy ORM (Issue, DefinitionOfReady, DORCheck, etc.)
    ↓
SQLite Database
```

## Files

### Services (`agileai/services/backlog/`)

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports |
| `domain.py` | Value objects, enums, pure logic (zero dependencies) |
| `exceptions.py` | Domain-specific exceptions |
| `estimation.py` | Story point estimation algorithm + AI queueing |
| `prioritization.py` | Weighted priority scoring algorithm |
| `readiness.py` | Definition of Ready evaluation |
| `service.py` | BacklogService orchestrator (single entry point) |

### API (`agileai/api/routers/`)

| File | Purpose |
|------|---------|
| `backlog.py` | FastAPI router with 7 endpoints |

### Schemas (`agileai/schemas/`)

| File | Purpose |
|------|---------|
| `backlog.py` | Pydantic request/response models |

### Tests (`tests/`)

| File | Purpose |
|------|---------|
| `test_backlog.py` | Comprehensive test suite (unit + integration) |

### Database

| File | Purpose |
|------|---------|
| `alembic/versions/0002_add_backlog_rank_to_issues.py` | Migration for backlog_rank field |

## API Endpoints

All endpoints are under `/api/v1/backlog/projects/{project_id}/...`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | List backlog issues with pagination |
| `POST` | `/estimate` | Request story point estimation |
| `POST` | `/prioritize` | Get priority-ranked backlog |
| `POST` | `/readiness` | Evaluate Definition of Ready |
| `PATCH` | `/reorder/{issue_id}` | Reorder single item (fractional indexing) |
| `PUT` | `/reorder` | Bulk reorder (entire list) |
| `POST` | `/sprint-pull` | Move issues into a sprint |
| `DELETE` | `/issues/{issue_id}/sprint` | Remove issue from sprint |

## Key Design Decisions

### 1. Fractional Indexing for Reordering

**Why:** Allows O(1) insertion between backlog items without renumbering.

**How:** Backlog items have a `backlog_rank REAL` (float) field. To insert between rank 1000 and 2000, assign rank 1500. Rebalancing happens automatically when gaps become too small, spreading items back to 1000, 2000, 3000...

**Example:**
```
Initial: [1000, 2000, 3000]
Insert between 1st and 2nd: [1000, 1500, 2000, 3000]
Insert between 1st and 2nd again: [1000, 1250, 1500, 2000, 3000]
Gap exhausted? Rebalance: [1000, 2000, 3000, 4000, 5000]
```

### 2. Heuristic + Optional AI Estimation

**Why:** Deterministic fast path for MVP, asynchronous AI refinement for accuracy.

**Algorithm:** Rule-based mapping of `difficulty` + `importance` + `child_count` + `external_dependencies` to Fibonacci points.

**AI Refinement:** When enabled, queues a `background_job` with `job_type='ai_estimate'` for the Assistant agent (Ollama) to process asynchronously. The API returns immediately with the heuristic estimate; the agent writes back a refined estimate later.

**Fibonacci Scale:** 1, 2, 3, 5, 8, 13, 21 (standard Scrum)

### 3. Weighted Priority Scoring

**Formula (0–100):**
- Importance × 40%
- Urgency (due date proximity) × 25%
- Value (unblocks other issues) × 20%
- Ease (inverse of difficulty) × 15%

**Weights are overridable per project** via `project_metadata` — no code changes needed for tuning.

### 4. Definition of Ready as Structured Checks

**Built-in Criteria:**
- `has_description` — description exists and > 20 chars
- `has_story_points` — story_points is not null
- `has_assignee` — assignee_id is not null
- `has_acceptance_criteria` — at least one `IssueInstruction` with type='constraint'

**Unknown Criteria:** Return `False`, requiring manual human verification.

**Status Advance:** If all criteria pass, issue status advances from `backlog` → `ready` automatically.

### 5. Clean Separation of Concerns

**Router:** HTTP contract only, zero business logic
**BacklogService:** Orchestration facade, delegates to subordinate services
**Subordinate Services:** Single responsibility each, fully testable in isolation
**Domain Objects:** Pure Python, zero dependencies on AgileAI codebase

**Testing:** Each layer can be tested independently without mocking.

## Usage Examples

### List Backlog with Scores

```python
service = BacklogService(session)
backlog = await service.get_backlog(
    project_id="proj-1",
    include_scores=True
)
```

### Estimate an Issue

```python
result = await service.request_estimate("issue-1")
# Returns: EstimationResult(suggested_points=5, raw_score=4.8, confidence="high", ...)
```

### Rank All Backlog Items

```python
scores = await service.get_ranked_backlog(
    project_id="proj-1",
    weights={"importance": 50, "urgency": 20, ...}  # optional override
)
# Returns: [PriorityScore(issue_id="1", score=95.2, rank=1, breakdown={...}), ...]
```

### Evaluate Definition of Ready

```python
result = await service.check_readiness(
    issue_id="issue-1",
    actor_id="user-1",
    actor_type="user"
)
# Returns: DORCheckResult(passed=True, failed_criteria=[], status_advanced_to_ready=True)
```

### Reorder a Single Item

```python
await service.reorder_single(
    issue_id="issue-3",
    after_id="issue-1",      # Move after this
    before_id="issue-2"      # And before this
)
```

### Move Issues into a Sprint

```python
moved, skipped = await service.pull_into_sprint(
    issue_ids=["issue-1", "issue-2", "issue-3"],
    sprint_id="sprint-1",
    actor_id="user-1"
)
# Returns: (["issue-1", "issue-2"], ["issue-3"])  # issue-3 not ready
```

## Audit Trail

All backlog operations that modify issues produce:
- `IssueChangeLog` rows for field-level audit (old_value → new_value)
- `StatusTransition` rows for status changes (backlog → ready, etc.)
- `DORCheck` rows for readiness evaluations

These are immutable records for regulated environments.

## Extension Points

### Add a New Priority Dimension

Edit `PrioritizationService.WEIGHTS` and `_score_issue()`:

```python
WEIGHTS = {
    "importance": 40.0,
    "urgency": 25.0,
    "value": 20.0,
    "ease": 15.0,
    "stakeholder_pressure": 10.0,  # NEW
}
```

### Add a New DoR Criterion

Edit `ReadinessGateService._evaluate_criterion()`:

```python
if criterion_lower == "has_link_to_epic":
    return any(link.link_type == "is_child_of_epic" for link in issue.links)
```

### Customize Estimation Algorithm

Override `EstimationService._heuristic_estimate()` or implement a subclass.

### Add Estimation via External API

Implement a new estimation provider and plug it into the estimation flow.

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| List backlog | O(n log n) | Sorted by backlog_rank + created_at |
| Estimate single | O(1) | Heuristic is pure function |
| Rank backlog | O(n log n) | Scores computed for all items |
| Reorder single | O(1) | Fractional indexing |
| Bulk reorder | O(n) | Full list renumbering |
| Rebalance ranks | O(n) | Runs only when gaps exhaust |
| Check readiness | O(m) | m = number of DOR criteria |

For typical backlogs (<500 items), all operations complete in <100ms.

## Future Enhancements (Phase 2)

- [ ] **Filter support:** By issue_type, label, assignee, epic
- [ ] **AI-driven estimation:** Ollama integration for semantic understanding
- [ ] **Capacity-aware prioritization:** Account for sprint capacity when ranking
- [ ] **Bulk operations:** Estimate all unpointed items in one call
- [ ] **Grooming ceremony support:** Schedule, facilitate, track grooming sessions
- [ ] **Metrics & dashboards:** Velocity tracking, readiness metrics, burnup charts
- [ ] **Automation rules:** Auto-estimate based on templates, auto-assign DoR criteria
- [ ] **Integration with agents:** Assistant agent suggests priorities, reviews completeness

## Testing

Run the test suite:

```bash
pytest tests/test_backlog.py -v
```

Test coverage includes:
- Domain logic (enums, algorithms)
- EstimationService (heuristic accuracy, persistence)
- PrioritizationService (scoring, weighting)
- ReadinessGateService (DOR evaluation, status transitions)
- BacklogService (orchestration, error handling)
- API endpoints (request/response contracts)

## Troubleshooting

**Issue: "No DOR criteria defined for project=X type=Y"**
- Ensure `DefinitionOfReady` rows are seeded for your project/issue_type combination
- Add global criteria with `project_id=NULL` as fallback

**Issue: Estimated points don't seem right**
- Check the `EstimationResult.rationale` field for the reasoning
- Verify `difficulty`, `importance`, `child_count` inputs are correct
- Override weights per project via `project_metadata`

**Issue: Reorder operations are slow**
- Backlog size >1000 items? Rebalance is O(n) at that scale
- Consider archiving old completed issues to reduce active backlog
- Monitor `backlog_rank` gaps; trigger manual rebalance when smallest gap < 1.0

---

# Web UI Coverage Roadmap

## Gap Analysis (2026-05-20)

The Web UI currently exposes only 4 of the 85 ORM tables — leaving 81 tables (95%) inaccessible through the browser. This roadmap closes that gap.

### Coverage matrix

| Group | Tables | Covered | Missing |
|-------|-------:|--------:|--------:|
| AI & Identity | 4 | 1 (User) | 3 |
| Skills | 3 | 0 | 3 |
| RBAC | 4 | 0 | 4 |
| Teams | 4 | 0 | 4 |
| Projects | 4 | 1 (Project) | 3 |
| Issues | 8 | 2 (Issue, IssueLabel) | 6 |
| Sprints | 8 | 0 | 8 |
| Quality Gates | 6 | 0 | 6 |
| Workflow & Automation | 6 | 0 | 6 |
| Regulatory & Compliance | 4 | 0 | 4 |
| Agent Operations | 9 | 0 | 9 |
| Memory & Compression | 4 | 0 | 4 |
| Deliverables | 5 | 0 | 5 |
| Reports | 3 | 0 | 3 |
| Notifications | 3 | 0 | 3 |
| Knowledge Base | 3 | 0 | 3 |
| Contacts | 2 | 0 | 2 |
| Jobs & Prompts & Analytics | 5 | 0 | 5 |
| **TOTALS** | **85** | **4** | **81** |

## Strategy

Building 81 bespoke pages is wasteful — most stub tables only need basic CRUD. The chosen approach:

1. **Generic admin shell** — an `/admin` section that introspects SQLAlchemy column metadata to auto-generate list/create/edit/delete views for every table. Sidebar groups tables by concern. One implementation covers all 85.
2. **Dedicated workflow UIs** — for high-value tables with rich domain semantics (Sprints, Agents, Ceremonies, BackgroundJobs, Notifications, ApprovalRequests), build polished purpose-built screens that sit on top of the same data.
3. **Iterative replacement** — start with the generic admin for coverage, then progressively replace generic views with dedicated UIs where workflow complexity warrants it.

## Implementation phases

### Phase A — Generic Admin (covers all 85 tables in one pass)
- [x] Inventory all models and group assignments
- [ ] `/admin` index — list 14 groups
- [ ] `/admin/{table}` — list rows, paginated, with column introspection
- [ ] `/admin/{table}/new` — create row, form fields auto-generated from column types
- [ ] `/admin/{table}/{id}/edit` — edit row
- [ ] `/admin/{table}/{id}` — view row with FK link-throughs
- [ ] `/admin/{table}/{id}/delete` — confirm + delete
- [ ] Sidebar "Admin" entry with collapsible group menu

### Phase B — Dedicated UIs for top workflow tables
- [ ] Sprints (8 tables) — replaces current empty Sprints tab
- [ ] Agents & AI Models (3 tables) — agent roster, model registry, API keys
- [ ] Ceremonies + Standups (3 tables) — sprint ceremonies calendar
- [ ] Quality Gates (DoR/DoD) — per-project criteria editor + checks
- [ ] Task Queue + Execution Logs — agent ops dashboard
- [ ] Background Jobs — job queue monitor
- [ ] Notifications — inbox with rules editor
- [ ] Approval Requests + Workflows — approvals queue

### Phase C — Cross-cutting polish
- [ ] Global search across all entities
- [ ] Audit trail viewer (IssueChangeLog, AccessLog, DeliverableStatusHistory)
- [ ] Reports dashboard (ReportDefinition → ReportInstance)
- [ ] Wiki / Knowledge base browser
- [ ] Telegram integration settings

## Phase A scope (Generic Admin) — full table inventory

**AI & Identity:** `ai_models`, `agents`, `api_keys` (User already covered)
**Skills:** `skill_definitions`, `agent_skills`, `issue_skill_requirements`
**RBAC:** `roles`, `permissions`, `role_permissions`, `actor_role_assignments`
**Teams:** `assignee_teams`, `assignee_team_members`, `agent_teams`, `agent_team_members`
**Projects:** `labels`, `project_metadata`, `data_classifications`
**Issues:** `issue_links`, `issue_assignments`, `issue_watchers`, `issue_instructions`, `instruction_completions`, `issue_templates`
**Sprints:** `sprints`, `sprint_issues`, `sprint_goals`, `sprint_capacity`, `burndown_snapshots`, `ceremonies`, `standup_records`, `standup_items`
**Quality Gates:** `definition_of_ready`, `definition_of_done`, `dor_checks`, `dod_checks`, `reviews`, `review_criteria`
**Workflow:** `status_transitions`, `handovers`, `impediments`, `workflows`, `workflow_steps`, `workflow_runs`
**Regulatory:** `compliance_checks`, `approval_workflows`, `approval_requests`, `access_log`
**Agent Ops:** `agent_availability`, `task_queue`, `execution_logs`, `agent_feedback`, `agent_logs`, `agent_messages`, `agent_token_usage`, `agent_token_budget`, `token_budget_alerts`
**Memory:** `project_memory`, `context_compression_rules`, `context_snapshots`, `content_embeddings`
**Deliverables:** `deliverables`, `deliverable_status_history`, `deliverable_distributions`, `deliverable_dependencies`, `expected_deliverables`
**Reports:** `report_definitions`, `report_instances`, `report_schedules`
**Notifications:** `notification_rules`, `notification_templates`, `notifications`
**Knowledge Base:** `wiki_pages`, `wiki_page_versions`, `attachments`
**Contacts:** `user_contacts`, `telegram_commands`
**Jobs/Prompts/Analytics:** `background_jobs`, `prompt_templates`, `prompt_versions`, `prompt_fragments`, `model_performance`
**History/Audit:** `issue_change_log`, `notes`, `velocity_records`, `time_entries`

