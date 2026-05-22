# AgileAI Kanban Board

**Sprint 1** · 2026-05-23 → 2026-06-06  
**Sprint Goal:** CLI + TUI functional; API expanded for sprints and projects.

Last updated: 2026-05-23

---

## ✅ Done

| ID | Item | Agent | Sprint | Completed |
|----|------|-------|--------|-----------|
| F-01 | FastAPI app skeleton + health check | — | 0 | 2026-05-19 |
| F-02 | SQLAlchemy 85-table ORM | — | 0 | 2026-05-19 |
| F-03 | JWT authentication (API + web) | — | 0 | 2026-05-19 |
| F-04 | HTTP client SDK (sync + async) | — | 0 | 2026-05-19 |
| F-05 | Backlog API (8 endpoints, 15 tests) | — | 0 | 2026-05-19 |
| F-06 | Web UI: Auth (login/register/logout) | — | 0 | 2026-05-19 |
| F-07 | Web UI: Projects list + cards | — | 0 | 2026-05-20 |
| F-08 | Web UI: Backlog tab (CRUD, drag-reorder) | — | 0 | 2026-05-20 |
| F-09 | Web UI: Sprints tab (real DB, CRUD) | — | 0 | 2026-05-23 |
| F-10 | Web UI: Agents roster + AI Models | — | 0 | 2026-05-23 |
| F-11 | Web UI: Generic admin CRUD (85 tables) | — | 0 | 2026-05-20 |
| F-12 | Web UI: Issue detail view | — | 0 | 2026-05-20 |
| F-13 | Sprint model expanded (name, dates, goal, status) | — | 0 | 2026-05-23 |
| F-14 | Ceremony / StandupRecord / SprintGoal models enriched | — | 0 | 2026-05-23 |

---

## 🔄 In Progress

_None currently. Sprint 1 starts now._

---

## 👁 In Review

_Empty._

---

## 📋 Sprint 1 Backlog

### Phase 3 — CLI (Owner: Agent Alpha)

| ID | Task | Priority | Points |
|----|------|----------|--------|
| S1-01 | `agileai login / logout` with token file | P0 | 2 |
| S1-02 | `agileai config set-url` | P0 | 1 |
| S1-03 | `agileai backlog list <project_id>` — Rich table | P0 | 3 |
| S1-04 | `agileai backlog show <project_id> <id>` | P1 | 1 |
| S1-05 | `agileai backlog estimate <project_id> <id>` | P1 | 2 |
| S1-06 | `agileai backlog prioritize <project_id>` | P1 | 1 |
| S1-07 | `agileai sprint list <project_id>` | P0 | 2 |
| S1-08 | `agileai sprint create / start / complete` | P1 | 2 |
| S1-09 | `agileai agents list` + `agileai models list` | P2 | 2 |
| S1-10 | `pytest tests/test_cli.py` ≥ 10 tests | P0 | 3 |

**Total: 19 points**

### Phase 4 — TUI (Owner: Agent Beta)

| ID | Task | Priority | Points |
|----|------|----------|--------|
| S1-11 | LoginScreen with form + auth | P0 | 3 |
| S1-12 | ProjectsScreen — card grid, keyboard nav | P0 | 3 |
| S1-13 | BacklogScreen — DataTable, `e` for estimate | P0 | 5 |
| S1-14 | SprintsScreen — sprint cards | P1 | 3 |
| S1-15 | AgentsScreen — agent roster | P2 | 2 |
| S1-16 | IssueDetailScreen — 2-column | P1 | 3 |
| S1-17 | theme.css — dark/light theme | P2 | 2 |

**Total: 21 points**

### Phase 9 — API Expansion (Owner: Agent Delta)

| ID | Task | Priority | Points |
|----|------|----------|--------|
| S1-18 | Sprint REST API (`/api/v1/sprints/*`) | P0 | 5 |
| S1-19 | Projects API — replace in-memory PROJECTS | P0 | 3 |
| S1-20 | Agents API (`/api/v1/agents/*`) | P1 | 4 |
| S1-21 | Alembic: init + first migration | P1 | 3 |
| S1-22 | `.env.example` + pydantic-settings config | P1 | 2 |

**Total: 17 points**

---

## 📦 Product Backlog (Future Sprints)

### Sprint 2 (2026-06-07 → 2026-06-20)

| ID | Task | Owner | Points |
|----|------|-------|--------|
| S2-01 | Desktop: Login + MainWindow | Agent Gamma | 5 |
| S2-02 | Desktop: BacklogTable (QTableView) | Agent Gamma | 5 |
| S2-03 | Desktop: Sprint + Agents widgets | Agent Gamma | 4 |
| S2-04 | Agent Gateway: poll / result / heartbeat API | Agent Alpha | 5 |
| S2-05 | Agent Gateway: MCP server tool definitions | Agent Alpha | 5 |
| S2-06 | Agent Gateway: context assembly | Agent Alpha | 3 |
| S2-07 | Telegram: bot + /backlog /sprint | Agent Beta | 3 |
| S2-08 | Telegram: /assign /status /standup | Agent Beta | 2 |
| S2-09 | Telegram: sprint event notifications | Agent Beta | 2 |
| S2-10 | API: Notifications + Approvals | Agent Delta | 4 |
| S2-11 | API: Reports + Wiki | Agent Delta | 4 |
| S2-12 | Web: Replace in-memory projects with DB | Agent Delta | 2 |

### Sprint 3 (2026-06-21 → 2026-07-04)

| ID | Task | Owner | Points |
|----|------|-------|--------|
| S3-01 | Compression: APScheduler worker | Agent Gamma | 3 |
| S3-02 | Compression: Ollama summarization | Agent Gamma | 3 |
| S3-03 | Compression: nomic-embed-text embeddings | Agent Gamma | 3 |
| S3-04 | Docker: `docker-compose.prod.yml` | Agent Delta | 3 |
| S3-05 | Settings: `.env` + pydantic-settings full | Agent Delta | 2 |
| S3-06 | Alembic: auto-upgrade on startup | Agent Delta | 2 |
| S3-07 | CI: GitHub Actions pipeline | Agent Delta | 3 |
| S3-08 | E2E: Playwright 5 critical paths | Agent Epsilon | 5 |
| S3-09 | Desktop: PyInstaller packaging | Agent Gamma | 3 |

### Sprint 4 (2026-07-05 → 2026-07-18)

| ID | Task | Owner | Points |
|----|------|-------|--------|
| S4-01 | Web: Reports dashboard | Agent Beta | 5 |
| S4-02 | Web: Velocity + burndown charts | Agent Beta | 4 |
| S4-03 | Web: Wiki browser | Agent Beta | 3 |
| S4-04 | Web: Notifications inbox | Agent Beta | 3 |
| S4-05 | Web: Approval workflows UI | Agent Alpha | 4 |
| S4-06 | Web: Global search | Agent Alpha | 3 |
| S4-07 | Web: Audit trail viewer | Agent Alpha | 3 |
| S4-08 | Load testing: k6 script | Agent Epsilon | 2 |
| S4-09 | Security: OWASP review | Agent Epsilon | 3 |
| S4-10 | Docs: README update + API docs | Agent Delta | 2 |
| S4-11 | Release: v1.0.0 tag + changelog | All | 1 |

---

## Velocity Tracker

| Sprint | Committed | Delivered | Velocity |
|--------|-----------|-----------|----------|
| Sprint 0 (Pre-sprint) | — | 57 pts | — |
| Sprint 1 | 57 pts | — | TBD |
| Sprint 2 | 44 pts | — | TBD |
| Sprint 3 | 27 pts | — | TBD |
| Sprint 4 | 33 pts | — | TBD |

---

## Labels

| Label | Meaning |
|-------|---------|
| P0 | Must-have for sprint goal |
| P1 | High value, fits in sprint |
| P2 | Nice-to-have, can slip |
| 🔴 Blocked | Blocked by another task |
| 🟡 At risk | May not make sprint |
| 🟢 On track | Progressing normally |
