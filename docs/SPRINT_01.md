# Sprint 1 Plan

**Dates:** 2026-05-23 → 2026-06-06
**Sprint Goal:** DB schema fully specified (no stub tables); Web UI has a real functional
screen for every domain — no in-memory data, no placeholder lists.

**Owner:** Claude (single actor this sprint)
**Reviewer:** Mohammad OMARI — approves PR before merge to main

---

## Context

Sprint 1 implements the "DB-first, Web UI as ground truth" strategy adopted 2026-05-23.
Before other agents can build CLI, TUI, Desktop, or Agent Gateway, they need:
1. A stable, complete DB schema (Phase A)
2. A working Web UI that proves the schema (Phase B)
3. Catalogs documenting both (Phase C — starts Sprint 2)

Secondary clients (Phases 3–10) are deferred to Sprint 2 onwards.

---

## Sprint Backlog

### Track A — DB Design Completion (Phase A) · 14 pts

| ID | Task | Group | Points | Status |
|----|------|-------|--------|--------|
| PA-01 | Audit AI & Identity: ai_models, agents, users, api_keys | AI & Identity | 2 | 🔲 |
| PA-02 | Audit Issues group: issues, assignments, labels, links, change_log, instructions, attachments | Issues | 3 | 🔲 |
| PA-03 | Audit Sprint group: sprints, sprint_issues, goals, capacity, burndown, ceremonies, standups | Sprints | 3 | 🔲 |
| PA-04 | Audit Projects, RBAC, Skills groups | Foundation | 2 | 🔲 |
| PA-05 | Audit Agent Ops, Background Jobs, Quality Gates groups | Ops | 2 | 🔲 |
| PA-06 | Audit Notifications, Wiki, Regulatory, Reports groups | Extended | 2 | 🔲 |
| PA-07 | Write `docs/DB_CHANGES.md` — column additions summary | Docs | 1 | 🔲 |

**Definition of Done for Track A:**
- `python -c "from __init__ import *; print('OK')"` succeeds
- No table has only `id` + timestamps (zero stub tables)
- Every table has a one-line docstring or comment
- `docs/DB_CHANGES.md` lists every column added or modified
- DB deletes and re-creates cleanly from the updated models

---

### Track B — Web UI Completion (Phase B) · 18 pts

| ID | Task | Route | Points | Status |
|----|------|-------|--------|--------|
| PB-01 | Replace in-memory `PROJECTS` list with real DB query | `GET /` | 2 | 🔲 |
| PB-02 | Users list screen | `GET /users` | 2 | 🔲 |
| PB-03 | User detail screen | `GET /users/{id}` | 1 | 🔲 |
| PB-04 | Complete Agents roster — skills + availability dots | `GET /agents` | 2 | 🔲 |
| PB-05 | Complete Sprint detail — burndown chart + standup log | `GET /project/{id}/sprints/{sid}` | 2 | 🔲 |
| PB-06 | Task Queue screen — queue table + execution log | `GET /ops/tasks` | 2 | 🔲 |
| PB-07 | Notifications inbox — list + mark-read | `GET /notifications` | 2 | 🔲 |
| PB-08 | Reports screen — velocity table + burndown summary | `GET /reports` | 2 | 🔲 |
| PB-09 | Audit log screen — access_log table with filters | `GET /audit` | 1 | 🔲 |
| PB-10 | Approval workflows screen — pending approvals list | `GET /approvals` | 1 | 🔲 |
| PB-11 | Wiki browser — page list + inline editor | `GET /wiki` | 2 | 🔲 |

**Definition of Done for Track B:**
- `GET /` shows real projects from DB (no hard-coded list)
- All 11 new screens render without error against a live DB
- No `PROJECTS = [...]` or similar in-memory stubs anywhere in routes.py
- HTMX actions (status-change, estimate, reorder) all hit real DB endpoints
- Server starts with `uvicorn agileai.api.main:app` — zero import errors

---

## Dependency Map

```
PA-01 → PA-02 → PA-03 → PA-04 → PA-05 → PA-06 (sequential, DB integrity order)
                                                   ↓
                                              PA-07 (DB_CHANGES.md)
                                                   ↓
PB-01 → PB-02 → ... → PB-11  (can run in any order AFTER Track A complete)
```

Track B must not start until Track A is complete — the Web UI depends on the finalized schema.

---

## Daily Standup Schedule

Standups are async — Claude posts a 3-line update to `docs/PROJECT_LOG.md` at session start.

Format:
```
### Standup — Claude — YYYY-MM-DD
- Done: ...
- Doing: ...
- Blocked: ...
```

---

## Sprint Ceremonies

| Ceremony | Date | Format |
|----------|------|--------|
| Sprint Planning | 2026-05-23 | This document |
| Standup | Daily | Async in PROJECT_LOG.md |
| Sprint Review | 2026-06-06 | Board update + demo notes in PROJECT_LOG.md |
| Retrospective | 2026-06-06 | 3 items: What went well / Improve / Actions |

---

## Risks

| Risk | Likelihood | Impact | Response |
|------|-----------|--------|----------|
| Stub table has deep FK dependencies | Medium | Medium | Add nullable columns; delete/recreate DB |
| Web UI route breaks after model change | Medium | Medium | Test each screen after Track A finishes |
| Wiki/Approval tables too complex for Sprint 1 | Low | Low | Defer to generic admin; deliver basic screen |
| DB recreate loses test seed data | High | Low | Write seed data script before Track A starts |

---

## Definition of Done (Sprint 1)

Sprint 1 is done when:
- [ ] All PA-01 through PA-07 tasks complete
- [ ] All PB-01 through PB-11 tasks complete
- [ ] `python -c "from __init__ import *"` runs without error
- [ ] `pytest tests/test_backlog.py` still passes (no regressions)
- [ ] `GET /` returns real DB projects
- [ ] Server starts from clean DB with zero errors
- [ ] `docs/DB_CHANGES.md` written and committed
- [ ] PR merged to main, reviewed by Mohammad OMARI
- [ ] `docs/BOARD.md` updated with Sprint 1 results
- [ ] `docs/PROJECT_LOG.md` has Sprint 1 Review entry
