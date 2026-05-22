# Project Log

Running record of decisions, standups, impediments, and sprint events.
Most recent entries at the top.

---

## Sprint 1 Start — 2026-05-23

**Sprint Goal:** CLI + TUI functional; Sprint API expanded; Alembic initialized.

**Team:**
- Agent Alpha → Phase 3 CLI (`feature/phase-3-cli`)
- Agent Beta → Phase 4 TUI (`feature/phase-4-tui`)
- Agent Delta → Phase 9 API Expansion (`feature/phase-9-api-expansion`)
- Agent Epsilon → Reviewer (all PRs)
- Agent Zeta → Scrum Master

**Sprint commitment:** 57 story points across 3 tracks.

**Impediments at sprint start:** None.

---

## Architecture Decision Log

### 2026-05-23 — DB-first strategy adopted

Mohammad OMARI requested a revised development strategy: complete the DB schema and Web UI
before building any secondary clients. Rationale: prevents field-name drift across clients,
proves the data model end-to-end, and produces a catalog that all agent teams can use as a
contract without reading source code.

**New phases added:**
- Phase A — DB Design Completion (all 85 tables fully specified)
- Phase B — Web UI Completion (all screens functional against real DB)
- Phase C — Catalog Writing (`docs/DB_CATALOG.md` + `docs/ROUTE_CATALOG.md`)

**Impact on roadmap:**
- Sprint 1 goal changed from "CLI + TUI functional" to "DB schema finalized + Web UI complete"
- Original Sprint 1 work (CLI, TUI, API expansion) moved to Sprint 2
- Sprint count increased from 4 to 5 (v1.0.0 target: 2026-08-01 vs. 2026-07-18)
- ADR-007 documents the decision in `docs/ARCHITECTURE.md`

**Artifacts updated:** DEVELOPMENT_PLAN.md, ROADMAP.md, docs/SPRINT_01.md, docs/BOARD.md, docs/ARCHITECTURE.md

---

### 2026-05-23 — Multi-agent development plan created

Mohammad OMARI requested a full development plan with artifacts for multi-agent parallel development. Created:
- `DEVELOPMENT_PLAN.md` — master plan with phases, agent assignments, DoD
- `ROADMAP.md` — 4-sprint timeline with milestones and dependency graph
- `docs/AGENTS_PLAYBOOK.md` — per-agent instructions (Alpha/Beta/Gamma/Delta/Epsilon/Zeta)
- `docs/BOARD.md` — Kanban board with Sprint 1 backlog (57 pts)
- `docs/WORKFLOW.md` — git workflow, PR process, testing requirements
- `docs/ARCHITECTURE.md` — ADRs and system overview
- `docs/SPRINT_01.md` — Sprint 1 plan
- Updated `BACKLOG.md` with Web UI coverage roadmap

**Key decisions documented:**
- ADR-001: SQLite over PostgreSQL (on-premises, portable)
- ADR-002: Inline HTML over Jinja2 files (path resolution)
- ADR-003: HTMX over React (no build step)
- ADR-004: Generic admin CRUD via introspection
- ADR-005: Dual REST + MCP transport for agent gateway
- ADR-006: JWT cookie for web, Bearer for API

### 2026-05-23 — Sprint model expanded

Added meaningful columns to `Sprint` model and related tables (SprintGoal, SprintCapacity, BurndownSnapshot, Ceremony, StandupRecord, StandupItem) — all `nullable=True` to avoid migration failures. Deleted agileai.db and let it recreate.

**Why:** Generic admin had id-only stubs. Dedicated Sprints UI needs name, goal, status, start/end dates.

### 2026-05-20 — Generic admin covers 85/85 tables

Built `agileai/web/admin.py` using SQLAlchemy introspection. All 85 tables now have list/create/edit/delete in the browser at `/admin`. Sidebar "Admin · All Tables" link added.

**Technique:** `sqlalchemy.inspect(model).columns` iterates column metadata; `col.type.python_type` drives input type selection (bool → checkbox, int → number, datetime → datetime-local, long text → textarea).

### 2026-05-20 — Web UI full redesign

Rewrote `agileai/web/routes.py` (1000+ line diff) with:
- Dark navy sidebar (#0f172a), 4-tab project nav, stats chips
- HTMX modals for estimate, sprint assign, new issue
- HTML5 drag-and-drop reorder with bulk-reorder endpoint
- Inline status dropdown updates (no page reload)

**Why inline HTML not Jinja2:** `Jinja2Templates` path resolution failed because `agileai/api/main.py` calculated template path as `parent.parent / "web" / "templates"`, but when running from the worktree, the templates directory didn't exist in the worktree. Inline string templates avoid this completely.

### 2026-05-19 — JWT auth added to web routes

Web routes use `httponly` cookie (`auth_token`, 24h expiry). API routes use Bearer token (30min). Two different expiry windows by design: web sessions last longer.

**Known issue:** JWT `SECRET_KEY` is still hardcoded in `agileai/api/dependencies.py`. Will be moved to `.env` in Phase 9 (production hardening). Tracked as S1-22.

### 2026-05-19 — Issue creation FK constraint

`Issue.created_by_id` is NOT NULL (FK to `users.id`). When the web UI creates issues, the JWT sub (user ID from cookie) may not match a row in the `users` table if the user registered in a fresh session or DB was recreated. Workaround: new issue route uses try/except and shows an alert-error. Real fix: ensure user row exists at login time (insert into users from auth token). Tracked as a bug.

---

## Impediments Log

_No current impediments. Add here when blocked._

Template:
```
### YYYY-MM-DD — Impediment: <title>
**Blocked agent:** Agent Beta
**Blocking item:** Sprint API (S1-10) not yet built by Agent Delta
**Impact:** TUI BacklogScreen cannot show real data
**Resolution:** Agent Beta works on AgentsScreen/LoginScreen in parallel while waiting
**Resolved:** YYYY-MM-DD (or: unresolved)
```

---

## Handoff Notes

_Use this section when handing off mid-task to another agent._

Template:
```
### Handoff: <feature> — <date>
**From:** Agent Alpha
**To:** Agent Beta
**Branch:** feature/phase-3-cli
**Status:** Login and backlog list commands complete. Sprint commands WIP.
**Next step:** Implement `agileai sprint list` using sync_client.list_sprints()
**Gotchas:**
- The sync_client doesn't have list_sprints() yet — needs to be added to agileai/client/sync_client.py first
- Token file is at ~/.agileai/token — load with agileai.cli.auth.load_token()
```

---

## Decisions Pending

| Decision | Options | Owner | Deadline |
|----------|---------|-------|----------|
| Compression model default | qwen2.5 vs phi3:mini | Mohammad OMARI | Before Sprint 3 |
| Desktop packaging target | Win only vs Win+Mac+Linux | Mohammad OMARI | Before Sprint 3 |
| Telegram notifications scope | Sprint events only vs all issue events | Mohammad OMARI | Before Sprint 2 |
| MCP transport | HTTP+SSE vs stdio | Mohammad OMARI | Before Phase 6 starts |
| Report chart library | Chart.js (web) vs matplotlib (export) | Agent Beta | Sprint 4 |

---

## Sprint Reviews

### Sprint 0 (Pre-sprint) Review — 2026-05-23

**Delivered:** 57 story points
- FastAPI + SQLAlchemy 85 ORM tables ✅
- JWT auth (web cookie + API Bearer) ✅
- HTTP client SDK (sync + async) ✅
- Backlog API (8 endpoints, 15 tests) ✅
- Web UI: 66 routes across auth/projects/backlog/sprints/agents/admin ✅
- Generic admin CRUD (all 85 tables) ✅
- Sprint model + Ceremony model expanded ✅

**Velocity established:** 57 points baseline (Sprint 0, no time constraint)

**Retrospective:**
- What went well: Clean Architecture for backlog service, reusable render_app() shell
- What to improve: Need real Alembic migrations — DB wipe-and-recreate is fragile
- Action: Agent Delta owns Alembic setup as S1-21 in Sprint 1
