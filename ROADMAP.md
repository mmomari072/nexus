# AgileAI Roadmap

> Milestone timeline for multi-agent parallel development.
> Sprints are 2 weeks. Start date: **2026-05-23**.

---

## Development Strategy

Before building secondary clients (CLI, TUI, Desktop, Agent Gateway), the DB schema and Web UI
are finalized and documented by Claude. This produces two catalogs that serve as the contract
for all other agents. See `DEVELOPMENT_PLAN.md §1.5` for full rationale.

```
Phase A (DB)  →  Phase B (Web UI)  →  Phase C (Catalog)  →  Phases 3–10 (clients)
   Sprint 1          Sprint 1           Sprint 2              Sprints 2–5
   Claude             Claude             Claude               Agent Alpha/Beta/Gamma/Delta
```

---

## Milestone Overview

```
2026-05-23 ────────────────────────────────────────────────────────── 2026-08-01
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
Sprint 1       Sprint 2       Sprint 3       Sprint 4       Sprint 5
2026-05-23     2026-06-07     2026-06-21     2026-07-05     2026-07-19
DB Design +    Catalog +      TUI +          Gateway +      Compression +
Web UI         CLI +          Desktop        Telegram +     Production
Complete       API expand                    Agent Ops      Release
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
M1: 2026-06-06 M2: 2026-06-20 M3: 2026-07-04 M4: 2026-07-18 M5: 2026-08-01
DB schema      Catalog        CLI + TUI       Agent gateway   v1.0.0
finalized +    published      working         operational     Production
Web UI done                                                   release
```

---

## Sprint 1: DB + Web UI Foundation (2026-05-23 → 2026-06-06)

**Sprint Goal:** DB schema fully specified across all 85 tables; Web UI has a real,
functional screen for every domain — no in-memory data, no stub tables.

**Owner:** Claude

### Deliverables

| # | Item | Track | Status |
|---|------|-------|--------|
| PA-01 | Audit AI & Identity tables (ai_models, agents, users, api_keys) | Phase A | 🔲 |
| PA-02 | Audit Issues tables (issues, assignments, labels, links, change_log) | Phase A | 🔲 |
| PA-03 | Audit Sprint tables (sprints, sprint_issues, goals, capacity, burndown) | Phase A | 🔲 |
| PA-04 | Audit Projects, RBAC, Skills tables | Phase A | 🔲 |
| PA-05 | Audit Agent Ops, Background Jobs, Quality Gates tables | Phase A | 🔲 |
| PA-06 | Audit Notifications, Wiki, Regulatory, Reports tables | Phase A | 🔲 |
| PA-07 | Write `docs/DB_CHANGES.md` — summary of all column additions | Phase A | 🔲 |
| PB-01 | Replace in-memory PROJECTS with real DB query | Phase B | 🔲 |
| PB-02 | Users list + detail screens (`/users`, `/users/{id}`) | Phase B | 🔲 |
| PB-03 | Task Queue screen (`/ops/tasks`) | Phase B | 🔲 |
| PB-04 | Notifications inbox (`/notifications`) | Phase B | 🔲 |
| PB-05 | Reports screen — velocity + burndown (`/reports`) | Phase B | 🔲 |
| PB-06 | Audit log screen (`/audit`) | Phase B | 🔲 |
| PB-07 | Approval workflows screen (`/approvals`) | Phase B | 🔲 |
| PB-08 | Wiki browser + editor (`/wiki`) | Phase B | 🔲 |
| PB-09 | Complete Agents roster — skills + availability | Phase B | 🔲 |
| PB-10 | Complete Sprint detail — burndown + standup log | Phase B | 🔲 |

**Milestone 1 criteria:**
- `python -c "from __init__ import *; print('OK')"` succeeds
- No table has only `id` + timestamps
- `GET /` shows real projects from DB
- All 16 Web UI screens render without error

---

## Sprint 2: Catalog + CLI + API Expansion (2026-06-07 → 2026-06-20)

**Sprint Goal:** Catalogs published; first CLI commands functional against real API endpoints.

### Deliverables

| # | Item | Owner | Status |
|---|------|-------|--------|
| PC-01 | `docs/DB_CATALOG.md` — entry for each of 85 tables | Claude | 🔲 |
| PC-02 | `docs/ROUTE_CATALOG.md` — entry for each web + API route | Claude | 🔲 |
| S2-01 | CLI: `agileai login / logout` with token file | Agent Alpha | 🔲 |
| S2-02 | CLI: `agileai backlog list/show/estimate/prioritize` | Agent Alpha | 🔲 |
| S2-03 | CLI: `agileai sprint list/create/start/complete` | Agent Alpha | 🔲 |
| S2-04 | CLI: `agileai agents list` + `agileai models list` | Agent Alpha | 🔲 |
| S2-05 | CLI: `pytest tests/test_cli.py` ≥ 10 tests | Agent Alpha | 🔲 |
| S2-06 | API: Sprint REST endpoints (`/api/v1/sprints/*`) | Agent Delta | 🔲 |
| S2-07 | API: Projects real DB (`/api/v1/projects/*`) | Agent Delta | 🔲 |
| S2-08 | API: Agents CRUD (`/api/v1/agents/*`) | Agent Delta | 🔲 |
| S2-09 | Alembic: `alembic init` + first migration | Agent Delta | 🔲 |
| S2-10 | `.env.example` + `pydantic-settings` config class | Agent Delta | 🔲 |

**Milestone 2 criteria:** `agileai backlog list proj-1` returns real data. Catalogs are published.

---

## Sprint 3: TUI + Desktop (2026-06-21 → 2026-07-04)

**Sprint Goal:** Terminal UI and Desktop app are navigable end-to-end.

### Deliverables

| # | Item | Owner | Status |
|---|------|-------|--------|
| S3-01 | TUI: LoginScreen + ProjectsScreen | Agent Beta | 🔲 |
| S3-02 | TUI: BacklogScreen — DataTable, `e`=estimate | Agent Beta | 🔲 |
| S3-03 | TUI: SprintsScreen + AgentsScreen | Agent Beta | 🔲 |
| S3-04 | TUI: IssueDetailScreen + theme.css | Agent Beta | 🔲 |
| S3-05 | Desktop: LoginDialog + MainWindow shell | Agent Gamma | 🔲 |
| S3-06 | Desktop: BacklogTable (QTableView) | Agent Gamma | 🔲 |
| S3-07 | Desktop: Sprint + Agents widgets | Agent Gamma | 🔲 |
| S3-08 | API: Notifications + Approvals endpoints | Agent Delta | 🔲 |
| S3-09 | API: Reports + Wiki endpoints | Agent Delta | 🔲 |

**Milestone 3 criteria:** `agileai tui` launches; Login → Projects → Backlog navigable.

---

## Sprint 4: Agent Gateway + Telegram (2026-07-05 → 2026-07-18)

**Sprint Goal:** AI agents can autonomously receive tasks, execute, and submit results.
Telegram users get sprint notifications.

### Deliverables

| # | Item | Owner | Status |
|---|------|-------|--------|
| S4-01 | Agent Gateway: poll / result / heartbeat REST API | Agent Alpha | 🔲 |
| S4-02 | Agent Gateway: MCP server tool definitions | Agent Alpha | 🔲 |
| S4-03 | Agent Gateway: context assembly (compressed) | Agent Alpha | 🔲 |
| S4-04 | Telegram: bot setup + /backlog /sprint /assign | Agent Beta | 🔲 |
| S4-05 | Telegram: /status /standup + sprint notifications | Agent Beta | 🔲 |
| S4-06 | Compression: APScheduler worker + Ollama summarization | Agent Gamma | 🔲 |
| S4-07 | Compression: nomic-embed-text embeddings | Agent Gamma | 🔲 |
| S4-08 | Desktop: PyInstaller packaging | Agent Gamma | 🔲 |

**Milestone 4 criteria:** Agent can authenticate, poll for a task, retrieve compressed context,
submit result. Sprint events arrive on Telegram.

---

## Sprint 5: Production (2026-07-19 → 2026-08-01)

**Sprint Goal:** Fully operational Docker Compose deployment. CI green. v1.0.0 released.

### Deliverables

| # | Item | Owner | Status |
|---|------|-------|--------|
| S5-01 | `docker-compose.prod.yml` — API + Ollama + nginx | Agent Delta | 🔲 |
| S5-02 | Alembic: auto-upgrade on startup | Agent Delta | 🔲 |
| S5-03 | GitHub Actions CI: lint + test + build | Agent Delta | 🔲 |
| S5-04 | E2E: Playwright tests (5 critical paths) | Agent Epsilon | 🔲 |
| S5-05 | Load testing: k6 API throughput | Agent Epsilon | 🔲 |
| S5-06 | Security audit: OWASP Top 10 | Agent Epsilon | 🔲 |
| S5-07 | Web: Reports dashboard + velocity charts | Agent Beta | 🔲 |
| S5-08 | Web: Approval workflows UI | Agent Alpha | 🔲 |
| S5-09 | Web: Global search + Audit trail viewer | Agent Alpha | 🔲 |
| S5-10 | CLI: packaging — pip install works | Agent Alpha | 🔲 |
| S5-11 | Documentation: README + API docs | Agent Delta | 🔲 |
| S5-12 | Release: v1.0.0 tag + changelog | All | 🔲 |

**Milestone 5 criteria:** `docker compose up` → fully operational system. CI green. v1.0.0 tagged.

---

## Dependency Graph

```
Phase A (DB Audit)  ──────────────────────────────────────────────────┐
          │                                                             │
          ▼                                                             │
Phase B (Web UI Complete) ──────────────────────────────────────────── │
          │                                                             │
          ▼                                                             │
Phase C (Catalog)  ──────────────────────────────────────────────────  │
          │                                                             │
          ├──► Phase 3 (CLI) ──────────────────────────────────────────┤
          │                                                             │
          ├──► Phase 4 (TUI) ──────────────────────────────────────────┤
          │                                                             │
          ├──► Phase 5 (Desktop) ──────────────────────────────────────┤
          │                                                             │
          ├──► Phase 9 (API expand) ──► Phase 10 (Production) ─────────┘
          │
          └──► Phase 6 (Gateway) ──► Phase 7 (Telegram)
                                └──► Phase 8 (Compression)
```

**Critical path:** Phase A → Phase B → Phase C → Phase 9 (Sprint/Projects API) → Phase 3 (CLI).
**Parallelisable after catalog:** Phases 3, 4, 5, 7 can run concurrently with Phase 9.

---

## Version Targets

| Version | Date | Contents |
|---------|------|----------|
| v0.1.0 | 2026-05-23 | Web UI + 85 ORM stubs (current) |
| v0.2.0 | 2026-06-06 | DB schema finalized + Web UI complete (M1) |
| v0.3.0 | 2026-06-20 | Catalogs published + CLI working + Sprint API (M2) |
| v0.4.0 | 2026-07-04 | TUI + Desktop navigable (M3) |
| v0.5.0 | 2026-07-18 | Agent gateway + Telegram + Compression (M4) |
| v1.0.0 | 2026-08-01 | Full production release (M5) |
