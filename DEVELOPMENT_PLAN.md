# AgileAI Development Plan

> **Local-first, AI-native Agile project management platform.**
> Humans and AI agents share the same task board, sprint workflows, and audit trail.
> Entirely on-premises — no external data transmission.

---

## 1. Project Status Snapshot (2026-05-23)

| Layer | Module | Status | Coverage |
|-------|--------|--------|----------|
| Data | SQLAlchemy ORM (85 tables) | ✅ Complete | 100% |
| API | FastAPI REST endpoints | 🟡 Partial | ~30% — backlog done, rest stubs |
| Auth | JWT + passlib | ✅ Complete | Web + API |
| SDK | HTTP Client (sync + async) | ✅ Complete | Full backlog API |
| Web UI | 66 routes, 85-table admin | ✅ Complete | All tables visible |
| CLI | agileai/cli/ | ❌ Not started | — |
| TUI | agileai/tui/ | ❌ Not started | — |
| Desktop | agileai/desktop/ | ❌ Not started | — |
| Agent Gateway | agileai/agents/ | ❌ Not started | — |
| Telegram Bot | — | ❌ Not started | — |
| Compression Agent | Ollama integration | ❌ Not started | — |
| Migrations | Alembic | ❌ Not started | Using create_all only |
| Tests | pytest | 🟡 Partial | 15/15 backlog; no UI/CLI/TUI tests |
| CI/CD | GitHub Actions | ❌ Not started | — |
| Production | Docker Compose | 🟡 Config only | Not wired |

---

## 2. Agent Team

Six AI agent roles are assigned to this project. Each has a dedicated playbook
in `docs/AGENTS_PLAYBOOK.md`.

| Agent Name | Role | Sprint 1 Owner | Sprint 2 Owner |
|------------|------|---------------|---------------|
| Agent Alpha | Actor — CLI | Phase 3: CLI | Phase 6: Agent Gateway (REST) |
| Agent Beta | Actor — TUI | Phase 4: TUI | Phase 7: Telegram Bot |
| Agent Gamma | Actor — Desktop | Phase 5: Desktop | Phase 8: Compression Agent |
| Agent Delta | Actor — Backend | API expansion + Alembic | Production hardening |
| Agent Epsilon | Reviewer | All PRs sprint 1 | All PRs sprint 2 |
| Agent Zeta | Scrum Master | Sprint 1 ceremonies | Sprint 2 ceremonies |

Human coordinator: **Mohammad OMARI** — approves PRs, resolves blockers.

---

## 3. Development Phases

### Phase 3 — CLI (`agileai/cli/`) 📅 Sprint 1

**Owner:** Agent Alpha  
**Branch:** `feature/phase-3-cli`  
**Estimated effort:** 3 days

Build a Typer-based CLI that uses the existing HTTP client SDK.

```
agileai login --email user@example.com
agileai logout
agileai backlog list <project_id>
agileai backlog estimate <project_id> <issue_id> --difficulty=medium --importance=high
agileai backlog prioritize <project_id>
agileai backlog reorder <project_id> <issue_id> --after=<ref_id>
agileai sprint list <project_id>
agileai sprint create <project_id> --name "Sprint 1" --goal "..."
agileai sprint start <project_id> <sprint_id>
agileai agents list
agileai models list
agileai config set-url http://localhost:8000
```

**Key files to create:**
- `agileai/cli/__init__.py`
- `agileai/cli/main.py` — Typer app entry point
- `agileai/cli/auth.py` — login/logout, token file at `~/.agileai/token`
- `agileai/cli/backlog.py` — backlog commands
- `agileai/cli/sprint.py` — sprint commands
- `agileai/cli/agents.py` — agent/model commands
- `agileai/cli/config.py` — config file at `~/.agileai/config.json`
- `tests/test_cli.py` — unit tests with mocked HTTP client

**Reuse:** `agileai/client/sync_client.py` — never re-implement HTTP calls.  
**Output format:** `rich.Table`, `rich.Panel`, `rich.Progress` for all output.  
**Definition of done:** All commands run, `pytest tests/test_cli.py` passes, `agileai --help` renders cleanly.

---

### Phase 4 — TUI (`agileai/tui/`) 📅 Sprint 1

**Owner:** Agent Beta  
**Branch:** `feature/phase-4-tui`  
**Estimated effort:** 4 days

Build a Textual-based terminal UI. Uses the async HTTP client.

**Screens:**
- `LoginScreen` — username/password form
- `ProjectsScreen` — project card grid, keyboard navigation
- `BacklogScreen` — issue table, `e`=estimate, `s`=sprint-assign, `r`=reorder, `n`=new
- `SprintsScreen` — sprint cards, `s`=start/complete, `Enter`=detail
- `AgentsScreen` — agent roster, status indicators
- `IssueDetailScreen` — 2-column layout, estimate button

**Key files to create:**
- `agileai/tui/__init__.py`
- `agileai/tui/app.py` — Textual App entry point, `agileai tui`
- `agileai/tui/screens/login.py`
- `agileai/tui/screens/projects.py`
- `agileai/tui/screens/backlog.py`
- `agileai/tui/screens/sprints.py`
- `agileai/tui/screens/agents.py`
- `agileai/tui/screens/issue_detail.py`
- `agileai/tui/bindings.py` — global key bindings
- `agileai/tui/theme.css` — Textual CSS

**Reuse:** `agileai/client/async_client.py`  
**Definition of done:** `agileai tui` launches, all screens navigable, no crashes.

---

### Phase 5 — Desktop (`agileai/desktop/`) 📅 Sprint 2

**Owner:** Agent Gamma  
**Branch:** `feature/phase-5-desktop`  
**Estimated effort:** 5 days

Build a PyQt6 desktop application.

**Windows:**
- `LoginDialog` — startup dialog
- `MainWindow` — MDI with project list sidebar
- `BacklogWidget` — sortable QTableView with drag reorder
- `SprintWidget` — sprint cards with progress bars
- `AgentsWidget` — agent roster with status indicators
- `IssueDetailWidget` — dock panel

**Key files to create:**
- `agileai/desktop/__init__.py`
- `agileai/desktop/main.py` — `QApplication` entry, `agileai desktop`
- `agileai/desktop/windows/main_window.py`
- `agileai/desktop/windows/login_dialog.py`
- `agileai/desktop/widgets/backlog_table.py`
- `agileai/desktop/widgets/sprint_card.py`
- `agileai/desktop/widgets/agent_roster.py`
- `agileai/desktop/models/backlog_model.py` — Qt item model
- `agileai/desktop/workers.py` — QThread workers for async HTTP

**Reuse:** `agileai/client/sync_client.py` (wrapped in QThread)  
**Definition of done:** `agileai desktop` opens, login works, backlog lists, no crashes.

---

### Phase 6 — Agent Gateway (`agileai/agents/`) 📅 Sprint 2

**Owner:** Agent Alpha (Sprint 2)  
**Branch:** `feature/phase-6-gateway`  
**Estimated effort:** 4 days

The agent gateway is the backbone of the multi-agent system. Agents poll it for
tasks, report results, and consume compressed context.

**REST endpoints to build:**
```
POST /api/v1/agents/{agent_id}/poll           → next TaskQueue item
POST /api/v1/agents/{agent_id}/result/{task}  → submit result
GET  /api/v1/agents/{agent_id}/context/{issue_id} → compressed context
POST /api/v1/agents/{agent_id}/heartbeat      → update availability
GET  /api/v1/tasks/queue                      → admin task queue view
POST /api/v1/tasks/assign                     → assign issue to agent
```

**MCP protocol support:**
- Implement MCP server endpoints alongside REST
- Transport: HTTP+SSE for streaming responses
- Tool definitions: `get_issue`, `update_status`, `submit_artifact`, `request_review`

**Key files to create:**
- `agileai/agents/__init__.py`
- `agileai/agents/gateway.py` — FastAPI router, `agileai/agents/gateway` prefix
- `agileai/agents/dispatcher.py` — task assignment logic
- `agileai/agents/context.py` — compressed context assembly
- `agileai/agents/mcp.py` — MCP server implementation
- `agileai/agents/schemas.py` — Pydantic schemas for agent protocol
- `tests/test_gateway.py`

**Definition of done:** Agent can authenticate, poll for tasks, submit results, retrieve compressed context. MCP tools respond correctly.

---

### Phase 7 — Telegram Bot 📅 Sprint 2

**Owner:** Agent Beta (Sprint 2)  
**Branch:** `feature/phase-7-telegram`  
**Estimated effort:** 2 days

```
/backlog <project_id>         → list current backlog (top 10)
/sprint <project_id>          → active sprint status
/assign <issue_id> @agent     → assign issue to agent
/status <issue_id> <status>   → update status
/standup <project_id>         → trigger standup collection
/notify on|off                → toggle notifications
```

**Key files to create:**
- `agileai/telegram/__init__.py`
- `agileai/telegram/bot.py` — python-telegram-bot Application
- `agileai/telegram/commands.py` — command handlers
- `agileai/telegram/notifications.py` — event-driven push notifications

**Definition of done:** Bot responds to all commands via private chat and group, sends sprint event notifications.

---

### Phase 8 — Compression Agent (Ollama) 📅 Sprint 3

**Owner:** Agent Gamma (Sprint 2+)  
**Branch:** `feature/phase-8-compression`  
**Estimated effort:** 3 days

Runs continuously as a background worker. Processes `background_jobs` with
`job_type = "compress"` using Ollama local models.

**Key files to create:**
- `agileai/compression/__init__.py`
- `agileai/compression/worker.py` — APScheduler worker, polls background_jobs
- `agileai/compression/compressor.py` — Ollama API calls, summarization logic
- `agileai/compression/embedder.py` — nomic-embed-text embedding generation
- `agileai/compression/context_builder.py` — assembles compressed context for gateway

**Models used:**
- Summarization: `qwen2.5` or `phi3:mini` (user choice)
- Embeddings: `nomic-embed-text`

**Definition of done:** Worker runs, processes jobs, writes to `context_snapshots` and `content_embeddings`. Agent gateway can retrieve pre-compressed context.

---

### Phase 9 — Backend API Expansion 📅 Sprint 1–3

**Owner:** Agent Delta (ongoing)  
**Branch:** `feature/phase-9-api-expansion`

Expand the ~30% API coverage to 100%. Currently only backlog API is fully implemented.

**Priority order:**
1. Sprint API (`/api/v1/sprints/*`) — needed by CLI/TUI
2. Agent API (`/api/v1/agents/*`) — needed by gateway
3. User API (`/api/v1/users/*`) — profile, team management
4. Project API (`/api/v1/projects/*`) — real project CRUD (not in-memory)
5. Notifications API (`/api/v1/notifications/*`)
6. Reports API (`/api/v1/reports/*`)
7. Wiki API (`/api/v1/wiki/*`)
8. Approval Workflows API (`/api/v1/approvals/*`)

**Also includes:**
- Alembic migration setup (replace `create_all` startup)
- Proper settings via `pydantic-settings` and `.env`
- Replace in-memory `PROJECTS` list with real DB queries
- Rate limiting on API routes

---

### Phase 10 — Production Hardening 📅 Sprint 3

**Owner:** Agent Delta  
**Branch:** `feature/phase-10-production`  
**Estimated effort:** 3 days

- `alembic init` and first migration from current schema
- `.env.example` with all required environment variables
- `docker-compose.prod.yml` — API + Ollama + nginx
- `Makefile` — common dev tasks
- GitHub Actions CI: lint → test → build
- E2E tests with Playwright (web UI critical paths)
- Load testing: k6 script for API throughput
- Security audit: OWASP Top 10 check

---

## 4. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| API response time (p95) | < 200ms for DB queries |
| Web UI page load | < 500ms |
| CLI response time | < 1s for list commands |
| Agent polling latency | < 100ms |
| Compression throughput | ≥ 10 issues/min on local hardware |
| Concurrent users | 50 without degradation |
| Data privacy | Zero external transmission (Ollama local) |
| Audit completeness | 100% field changes in `issue_change_log` |

---

## 5. Definition of Done (Project)

The project is "done" when:

- [ ] All 10 phases complete
- [ ] All 5 frontends functional: Web, CLI, TUI, Desktop, Telegram
- [ ] Agent gateway operational: actors can poll, execute, and submit
- [ ] Compression agent running against Ollama
- [ ] 100% API coverage (all 85-table data accessible via REST)
- [ ] Alembic migrations replace `create_all`
- [ ] CI pipeline: lint + test + build all green
- [ ] E2E tests cover login → backlog → estimate → sprint → complete
- [ ] Docker Compose `up` produces a fully operational system
- [ ] All `README.md` and API docs up to date

---

## 6. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Ollama not installed on target machine | Medium | High | Graceful degradation: skip compression if Ollama unavailable |
| PyQt6 packaging complexity | High | Medium | Use PyInstaller; test on Win/Mac/Linux |
| MCP protocol spec changes | Low | Medium | Pin to specific MCP version; adapt in Phase 6+ |
| SQLite concurrency limits | Medium | Medium | Use WAL mode (already enabled via aiosqlite) |
| Circular imports (web ↔ api) | Done | Done | Resolved by lazy imports in web module |
| DB schema drift between worktree and main | Medium | High | Always delete DB and re-create when changing models |

---

## 7. Technology Decisions (ADR Summary)

See `docs/ARCHITECTURE.md` for full Architecture Decision Records.

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Web framework | FastAPI | Async, Pydantic, auto-docs, excellent for agent APIs |
| ORM | SQLAlchemy 2.0 async | Type-safe, async-first, 85 tables manageable |
| Database | SQLite + aiosqlite | On-premises, portable, no external server |
| Web UI | Inline HTML templates + HTMX | No build step, fast iteration, works without JS framework |
| CLI | Typer + Rich | Pythonic, auto-help, beautiful output |
| TUI | Textual | Modern, async, reactive, well-maintained |
| Desktop | PyQt6 | Cross-platform, mature, powerful |
| Agent protocol | REST + MCP | REST for simplicity; MCP for Claude tool integration |
| Compression | Ollama (local) | Privacy-preserving, on-premises |
| Auth | JWT (jose) + bcrypt | Stateless, no session store needed |
