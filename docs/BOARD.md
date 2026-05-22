# AgileAI Kanban Board

**Sprint 1** · 2026-05-23 → 2026-06-06
**Sprint Goal:** DB schema fully specified; Web UI complete with real DB screens.

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

### Phase A — DB Design Completion (Owner: Claude)

| ID | Task | Priority | Points |
|----|------|----------|--------|
| PA-01 | Audit AI & Identity tables | P0 | 2 |
| PA-02 | Audit Issues group | P0 | 3 |
| PA-03 | Audit Sprint group | P0 | 3 |
| PA-04 | Audit Projects, RBAC, Skills groups | P0 | 2 |
| PA-05 | Audit Agent Ops, Background Jobs, Quality Gates | P1 | 2 |
| PA-06 | Audit Notifications, Wiki, Regulatory, Reports | P1 | 2 |
| PA-07 | Write `docs/DB_CHANGES.md` | P0 | 1 |

**Total: 15 points**

### Phase B — Web UI Completion (Owner: Claude)

| ID | Task | Priority | Points |
|----|------|----------|--------|
| PB-01 | Replace in-memory PROJECTS with real DB | P0 | 2 |
| PB-02 | Users list screen (`/users`) | P0 | 2 |
| PB-03 | User detail screen (`/users/{id}`) | P1 | 1 |
| PB-04 | Complete Agents roster — skills + availability | P0 | 2 |
| PB-05 | Complete Sprint detail — burndown + standup log | P1 | 2 |
| PB-06 | Task Queue screen (`/ops/tasks`) | P1 | 2 |
| PB-07 | Notifications inbox (`/notifications`) | P1 | 2 |
| PB-08 | Reports screen (`/reports`) | P2 | 2 |
| PB-09 | Audit log screen (`/audit`) | P2 | 1 |
| PB-10 | Approval workflows screen (`/approvals`) | P2 | 1 |
| PB-11 | Wiki browser + editor (`/wiki`) | P2 | 2 |

**Total: 19 points**

---

## 📦 Product Backlog (Future Sprints)

### Sprint 2 (2026-06-07 → 2026-06-20) — Catalog + CLI + API

| ID | Task | Owner | Points |
|----|------|-------|--------|
| PC-01 | `docs/DB_CATALOG.md` — 85-table schema reference | Claude | 4 |
| PC-02 | `docs/ROUTE_CATALOG.md` — full route reference | Claude | 3 |
| S2-01 | CLI: `agileai login / logout` with token file | Agent Alpha | 2 |
| S2-02 | CLI: `agileai backlog list/show/estimate/prioritize` | Agent Alpha | 4 |
| S2-03 | CLI: `agileai sprint list/create/start/complete` | Agent Alpha | 2 |
| S2-04 | CLI: `agileai agents list` + `agileai models list` | Agent Alpha | 2 |
| S2-05 | CLI: `pytest tests/test_cli.py` ≥ 10 tests | Agent Alpha | 3 |
| S2-06 | API: Sprint REST endpoints (`/api/v1/sprints/*`) | Agent Delta | 5 |
| S2-07 | API: Projects real DB (`/api/v1/projects/*`) | Agent Delta | 3 |
| S2-08 | API: Agents CRUD (`/api/v1/agents/*`) | Agent Delta | 4 |
| S2-09 | Alembic: `alembic init` + first migration | Agent Delta | 3 |
| S2-10 | `.env.example` + pydantic-settings config class | Agent Delta | 2 |

### Sprint 3 (2026-06-21 → 2026-07-04) — TUI + Desktop

| ID | Task | Owner | Points |
|----|------|-------|--------|
| S3-01 | TUI: LoginScreen + ProjectsScreen | Agent Beta | 3 |
| S3-02 | TUI: BacklogScreen — DataTable, `e`=estimate | Agent Beta | 5 |
| S3-03 | TUI: SprintsScreen + AgentsScreen | Agent Beta | 3 |
| S3-04 | TUI: IssueDetailScreen + theme.css | Agent Beta | 3 |
| S3-05 | Desktop: LoginDialog + MainWindow shell | Agent Gamma | 5 |
| S3-06 | Desktop: BacklogTable (QTableView) | Agent Gamma | 5 |
| S3-07 | Desktop: Sprint + Agents widgets | Agent Gamma | 4 |
| S3-08 | API: Notifications + Approvals endpoints | Agent Delta | 4 |
| S3-09 | API: Reports + Wiki endpoints | Agent Delta | 4 |

### Sprint 4 (2026-07-05 → 2026-07-18) — Gateway + Telegram + Compression

| ID | Task | Owner | Points |
|----|------|-------|--------|
| S4-01 | Agent Gateway: poll / result / heartbeat API | Agent Alpha | 5 |
| S4-02 | Agent Gateway: MCP server tool definitions | Agent Alpha | 5 |
| S4-03 | Agent Gateway: context assembly | Agent Alpha | 3 |
| S4-04 | Telegram: bot + /backlog /sprint /assign | Agent Beta | 3 |
| S4-05 | Telegram: /status /standup + notifications | Agent Beta | 2 |
| S4-06 | Compression: APScheduler worker + Ollama | Agent Gamma | 3 |
| S4-07 | Compression: nomic-embed-text embeddings | Agent Gamma | 3 |
| S4-08 | Desktop: PyInstaller packaging | Agent Gamma | 3 |

### Sprint 5 (2026-07-19 → 2026-08-01) — Production + Polish

| ID | Task | Owner | Points |
|----|------|-------|--------|
| S5-01 | Docker: `docker-compose.prod.yml` | Agent Delta | 3 |
| S5-02 | Alembic: auto-upgrade on startup | Agent Delta | 2 |
| S5-03 | CI: GitHub Actions lint + test + build | Agent Delta | 3 |
| S5-04 | E2E: Playwright 5 critical paths | Agent Epsilon | 5 |
| S5-05 | Load testing: k6 script | Agent Epsilon | 2 |
| S5-06 | Security: OWASP review | Agent Epsilon | 3 |
| S5-07 | Web: Reports dashboard + velocity charts | Agent Beta | 5 |
| S5-08 | Web: Approval workflows + Global search | Agent Alpha | 4 |
| S5-09 | Web: Audit trail viewer | Agent Alpha | 3 |
| S5-10 | CLI: pip packaging | Agent Alpha | 2 |
| S5-11 | Docs: README update + API docs | Agent Delta | 2 |
| S5-12 | Release: v1.0.0 tag + changelog | All | 1 |

---

## Velocity Tracker

| Sprint | Committed | Delivered | Velocity |
|--------|-----------|-----------|----------|
| Sprint 0 (Pre-sprint) | — | 57 pts | — |
| Sprint 1 | 34 pts (Phase A + B) | — | TBD |
| Sprint 2 | 35 pts (Catalog + CLI + API) | — | TBD |
| Sprint 3 | 37 pts (TUI + Desktop) | — | TBD |
| Sprint 4 | 27 pts (Gateway + Telegram + Compression) | — | TBD |
| Sprint 5 | 35 pts (Production + Polish) | — | TBD |

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
