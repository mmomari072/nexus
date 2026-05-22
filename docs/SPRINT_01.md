# Sprint 1 Plan

**Dates:** 2026-05-23 → 2026-06-06  
**Sprint Goal:** CLI + TUI functional; Sprint API expanded; Alembic initialized.

**Team:**
| Agent | Track | Capacity |
|-------|-------|----------|
| Agent Alpha | CLI (Phase 3) | Full |
| Agent Beta | TUI (Phase 4) | Full |
| Agent Delta | API Expansion + Alembic | Full |
| Agent Epsilon | Reviews | Part-time |
| Agent Zeta | Scrum Master | Part-time |

---

## Sprint Backlog

### Track A — CLI (Agent Alpha) · 19 pts

| ID | Task | Points | Status |
|----|------|--------|--------|
| S1-01 | `agileai login / logout` with token file at `~/.agileai/token` | 2 | 🔲 |
| S1-02 | `agileai config set-url <url>` | 1 | 🔲 |
| S1-03 | `agileai backlog list <project_id>` — Rich.Table output | 3 | 🔲 |
| S1-04 | `agileai backlog show <project_id> <id>` — Rich.Panel | 1 | 🔲 |
| S1-05 | `agileai backlog estimate <project_id> <id>` — call estimate API | 2 | 🔲 |
| S1-06 | `agileai backlog prioritize <project_id>` — ranked table | 1 | 🔲 |
| S1-07 | `agileai sprint list <project_id>` — sprint cards with progress | 2 | 🔲 |
| S1-08 | `agileai sprint create / start / complete` | 2 | 🔲 |
| S1-09 | `agileai agents list` + `agileai models list` | 2 | 🔲 |
| S1-10 | `pytest tests/test_cli.py` — ≥ 10 tests, all pass | 3 | 🔲 |

**Definition of Done for Track A:**
- All commands listed above run without errors against a local server
- `agileai --help` shows correct command tree
- `pytest tests/test_cli.py` green
- `pyproject.toml [project.scripts]` has `agileai = "agileai.cli.main:app"`
- PR reviewed by Agent Epsilon and merged

### Track B — TUI (Agent Beta) · 21 pts

| ID | Task | Points | Status |
|----|------|--------|--------|
| S1-11 | LoginScreen with form validation + token storage | 3 | 🔲 |
| S1-12 | ProjectsScreen — card grid, `Enter` to select | 3 | 🔲 |
| S1-13 | BacklogScreen — DataTable, `e`=estimate, `n`=new, `Enter`=detail | 5 | 🔲 |
| S1-14 | SprintsScreen — sprint list with progress indicators | 3 | 🔲 |
| S1-15 | AgentsScreen — agent roster with status dots | 2 | 🔲 |
| S1-16 | IssueDetailScreen — 2-column, description + metadata | 3 | 🔲 |
| S1-17 | theme.css — readable dark/light theme | 2 | 🔲 |

**Definition of Done for Track B:**
- `agileai tui` launches without ImportError
- Can navigate: Login → Projects → Backlog → issue detail
- No crashes on any normal navigation path
- Key bindings documented in `agileai/tui/bindings.py`
- PR reviewed by Agent Epsilon and merged

### Track C — API Expansion + Alembic (Agent Delta) · 17 pts

| ID | Task | Points | Status |
|----|------|--------|--------|
| S1-18 | Sprint REST API (`/api/v1/sprints/*`) — 8 endpoints | 5 | 🔲 |
| S1-19 | Projects API — replace in-memory `PROJECTS` with real DB | 3 | 🔲 |
| S1-20 | Agents API (`/api/v1/agents/*`) — CRUD + availability | 4 | 🔲 |
| S1-21 | Alembic: `alembic init`, first migration, `alembic upgrade head` | 3 | 🔲 |
| S1-22 | `.env.example` + `pydantic-settings` config class | 2 | 🔲 |

**Definition of Done for Track C:**
- `GET /api/v1/sprints/projects/proj-1` returns list (even empty)
- `GET /api/v1/projects/` returns real DB rows
- `alembic upgrade head` runs without error on fresh DB
- `.env.example` covers all required vars
- PR reviewed and merged

---

## Dependency Map

```
S1-18 (Sprint API) ──→ S1-07 (CLI sprint list)  [BLOCKS]
S1-18 (Sprint API) ──→ S1-14 (TUI Sprints)       [BLOCKS]
S1-19 (Projects API) → S1-03 (CLI backlog list)  [SOFT]
S1-21 (Alembic) ─────→ S1-22 (.env)             [SEQUENCE]
```

Agent Delta should **prioritize S1-18 and S1-19 first** to unblock Tracks A and B.

---

## Daily Standup Schedule

Standups are async — each agent posts a 3-line update to `docs/PROJECT_LOG.md` when their session starts.

Format:
```
### Standup — Agent Alpha — YYYY-MM-DD
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
| Sprint API blocks CLI/TUI | High | High | Agent Delta starts with S1-18 and S1-19 |
| TUI Textual API changes | Low | Medium | Pin to `textual>=0.61.0`, test on install |
| CLI token file paths differ on Windows | Medium | Medium | Use `Path.home() / ".agileai"` — cross-platform |
| Alembic async setup complexity | Medium | Medium | Use `alembic.runtime.migration` with async engine wrapper |

---

## Definition of Done (Sprint 1)

Sprint 1 is done when:
- [ ] `agileai backlog list proj-1` shows data from real DB
- [ ] `agileai tui` launches and all screens navigable
- [ ] `GET /api/v1/sprints/projects/proj-1` functional
- [ ] `alembic upgrade head` works on clean install
- [ ] All PRs from tracks A, B, C merged and reviewed
- [ ] `pytest tests/` fully green (including new CLI tests)
- [ ] `docs/BOARD.md` updated with Sprint 1 results
- [ ] `docs/PROJECT_LOG.md` has Sprint 1 Review entry
