# Architecture Decision Records

Technical decisions made for the AgileAI platform, with rationale.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  Browser     CLI (Typer)   TUI (Textual)   Desktop (PyQt6)      │
│  Telegram    MCP Clients   Custom Scripts                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP / WebSocket / SSE
┌──────────────────────────▼──────────────────────────────────────┐
│                         API LAYER                                │
│  FastAPI (agileai/api/main.py)                                   │
│  ├── /api/v1/auth/*        JWT authentication                    │
│  ├── /api/v1/backlog/*     Backlog management                    │
│  ├── /api/v1/sprints/*     Sprint lifecycle                      │
│  ├── /api/v1/agents/*      Agent gateway (REST + MCP)            │
│  ├── /api/v1/users/*       User management                       │
│  ├── /api/v1/notifications/* Push notifications                  │
│  └── /web/*                Web UI (Jinja-style inline HTML)      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SQLAlchemy 2.0 async
┌──────────────────────────▼──────────────────────────────────────┐
│                        DATA LAYER                                │
│  SQLite (aiosqlite)   ·   85 tables   ·   14 concern groups      │
│  Full audit trail (issue_change_log, access_log)                 │
│  WAL mode for concurrent reads                                   │
└─────────────────────────────────────────────────────────────────┘
                           │ Ollama API
┌──────────────────────────▼──────────────────────────────────────┐
│                     BACKGROUND LAYER                             │
│  APScheduler   ·   Compression Worker   ·   Telegram Bot         │
│  context_snapshots   ·   content_embeddings                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## ADR-001: SQLite over PostgreSQL

**Status:** Accepted  
**Date:** 2026-05-01

**Context:** The platform must be on-premises in regulated environments with zero external data transmission. Some deployments have no DBA and no external DB server.

**Decision:** Use SQLite with aiosqlite for async access.

**Consequences:**
- ✅ Zero external server dependency
- ✅ Single-file database — easy backup (`cp agileai.db backup.db`)
- ✅ WAL mode enables concurrent reads (aligns with multi-agent polling)
- ❌ No horizontal scaling — single-writer constraint
- ❌ Limited to ~100 concurrent users before WAL contention
- Mitigation: WAL mode + connection pool size = 5

**Configuration:**
```python
# database.py
engine = create_async_engine(
    "sqlite+aiosqlite:///agileai.db",
    echo=False,
    connect_args={"check_same_thread": False},
    pool_size=5,
    max_overflow=10,
)
# Enable WAL on first connection
@event.listens_for(engine.sync_engine, "connect")
def set_wal(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
```

---

## ADR-002: Inline HTML Templates over Jinja2 Files

**Status:** Accepted  
**Date:** 2026-05-19

**Context:** Initial Jinja2 file-based templates caused `TemplateNotFoundError` due to path resolution issues between the worktree and main repo. The fix required significant path wrangling.

**Decision:** Embed HTML templates as Python string constants (`AUTH_HTML`, `APP_HTML`) in `agileai/web/routes.py`.

**Consequences:**
- ✅ No file path resolution issues — templates are always found
- ✅ Full Python format-string interpolation without Jinja syntax
- ✅ Single-file deployment of the web UI
- ❌ Large route file (1400+ lines)
- ❌ No template inheritance in Jinja2 sense — use Python functions instead
- Mitigation: Helper functions (`render_app`, `project_tabs`, `status_badge`) serve as the "layout system"

---

## ADR-003: HTMX over React/Vue for Web UI

**Status:** Accepted  
**Date:** 2026-05-19

**Context:** The team needed interactive UI without a full JS build pipeline. The platform is internal tooling, not a consumer product.

**Decision:** Use HTMX for AJAX interactions. All JS is inline in the HTML template.

**Consequences:**
- ✅ No build step (`npm`, `webpack`, `vite`)
- ✅ Works without a CDN for JS (HTMX can be served from `/static`)
- ✅ Progressive enhancement — works without JS for basic navigation
- ❌ Limited to HTMX's capabilities for complex interactions (drag-and-drop done with raw JS)
- Limitation: Real-time updates require polling (`hx-trigger="every 30s"`) not WebSocket

---

## ADR-004: Generic Admin CRUD via SQLAlchemy Introspection

**Status:** Accepted  
**Date:** 2026-05-20

**Context:** 85 tables across 14 groups — building bespoke UIs for each was not feasible in the initial phase.

**Decision:** `agileai/web/admin.py` uses `sqlalchemy.inspect(model).columns` to auto-generate list/create/edit/delete forms for every model. Dedicated UIs are built separately for high-value workflow tables.

**Consequences:**
- ✅ 100% table coverage with one implementation
- ✅ Self-healing — adding columns to a model auto-appears in admin forms
- ❌ Generic forms lack validation specific to domain (e.g., date range validation for sprints)
- Mitigation: Dedicated UIs for Sprints, Agents, Backlog replace generic admin for those tables

---

## ADR-005: Agent Protocol — REST + MCP Dual Transport

**Status:** Proposed  
**Date:** 2026-05-23

**Context:** AI agents (Claude, Ollama-backed) need to poll for tasks and receive tool definitions. Claude Code uses MCP. Custom agents may prefer REST.

**Decision:** Implement both:
- REST API at `/api/v1/agents/*` for custom agent integrations and polling
- MCP server at `/mcp/*` using HTTP+SSE transport for Claude tool use

**Tool definitions for MCP:**
```python
TOOLS = [
    {"name": "get_issue", "description": "Get issue details", "input_schema": {...}},
    {"name": "update_status", "description": "Change issue status", "input_schema": {...}},
    {"name": "submit_artifact", "description": "Attach result to issue", "input_schema": {...}},
    {"name": "request_review", "description": "Flag issue for review", "input_schema": {...}},
    {"name": "get_context", "description": "Get compressed issue context", "input_schema": {...}},
]
```

---

## ADR-006: JWT Auth — Cookie for Web, Bearer for API

**Status:** Accepted  
**Date:** 2026-05-19

**Context:** Web UI needs session persistence across page loads. API clients (CLI, agents) need stateless auth.

**Decision:**
- Web routes: JWT stored in `httponly` cookie (`auth_token`), 24h expiry
- API routes: JWT in `Authorization: Bearer <token>` header, 30min expiry (refreshable)

**Note:** The JWT secret (`SECRET_KEY`) is currently hardcoded in `agileai/api/dependencies.py`. Phase 9 (production hardening) will move this to `.env`.

---

## ADR-007: DB-First, Web UI as Ground Truth

**Status:** Accepted
**Date:** 2026-05-23

**Context:** With 85 ORM tables as stubs and 4 secondary clients planned (CLI, TUI, Desktop,
Agent Gateway), there was a risk that each client team would independently interpret the data
model — producing field-name drift, duplicate HTTP calls, and integration bugs discovered late.

**Decision:** Before any secondary client is built:
1. **Phase A** — Complete the DB schema (all 85 tables fully specified)
2. **Phase B** — Complete the Web UI (all screens functional against real DB, no in-memory data)
3. **Phase C** — Write two catalog documents:
   - `docs/DB_CATALOG.md` — one entry per table: columns, types, FKs, indexes, seed data
   - `docs/ROUTE_CATALOG.md` — one entry per route: params, auth, data sources, HTMX actions

Secondary clients (Phases 3–10) start only after the catalog is published.

**Consequences:**
- ✅ Single source of truth for data shapes — catalog consumed by all agent teams
- ✅ Web UI proves the schema works end-to-end before other clients are built
- ✅ Agent Alpha / Beta / Gamma can build CLI / TUI / Desktop reading catalog only — no source code diving
- ✅ Schema bugs discovered in Phase A/B, not in Phase 3–5 integration
- ❌ Sprint 1 has no secondary client output — only DB + Web UI
- ❌ Catalog maintenance burden — must be regenerated on schema changes
- Mitigation: Catalog is generated after Phase B is stable; schema changes require catalog update PR

---

## Module Structure Reference

```
nexus/                              ← repo root
├── __init__.py                     ← ALL 85 ORM models (import here)
├── base.py                         ← Base, TimestampMixin, generate_uuid
├── identity.py                     ← AIModel, Agent, User, APIKey (rich models)
├── issues.py                       ← Issue, IssueLabel, IssueLink, etc. (rich models)
├── database.py                     ← AsyncEngine, AsyncSessionLocal
├── agileai/
│   ├── api/
│   │   ├── main.py                 ← FastAPI app, route mounting, lifespan
│   │   ├── dependencies.py         ← get_db(), get_current_user(), create_access_token()
│   │   └── routers/
│   │       ├── auth.py             ← /api/v1/auth/*
│   │       └── backlog.py          ← /api/v1/backlog/*
│   ├── client/
│   │   ├── sync_client.py          ← Synchronous HTTP client (CLI, Desktop)
│   │   └── async_client.py         ← Async HTTP client (TUI, Gateway)
│   ├── services/
│   │   └── backlog/                ← Business logic (estimation, prioritization, readiness)
│   ├── schemas/
│   │   └── backlog.py              ← Pydantic request/response schemas
│   ├── web/
│   │   ├── routes.py               ← Web UI routes (1400+ lines)
│   │   └── admin.py                ← Generic admin CRUD (500 lines)
│   ├── cli/                        ← 🔲 Phase 3
│   ├── tui/                        ← 🔲 Phase 4
│   ├── desktop/                    ← 🔲 Phase 5
│   ├── agents/                     ← 🔲 Phase 6
│   ├── telegram/                   ← 🔲 Phase 7
│   └── compression/                ← 🔲 Phase 8
├── tests/
│   └── test_backlog.py             ← 15 passing integration tests
├── docs/                           ← Project documentation
├── DEVELOPMENT_PLAN.md
├── ROADMAP.md
├── BACKLOG.md
├── CLAUDE.md
└── pyproject.toml
```

---

## Key Design Invariants

These must never be violated:

1. **All ORM models import from root `__init__.py`**
   - Wrong: `from agileai.models import Sprint`
   - Right: `from __init__ import Sprint` (with sys.path trick in each module)

2. **No synchronous SQLAlchemy calls in FastAPI routes**
   - All queries: `await db.execute(select(Model)...)`

3. **Audit trail preserved**
   - `TimestampMixin` provides `created_at`/`updated_at` — never manually set these
   - Status changes to issues must also write to `issue_change_log` (enforcement pending)

4. **No external data transmission**
   - AI calls only via `anthropic` SDK (API key from `.env`) or Ollama (local)
   - No telemetry, no third-party analytics

5. **DB schema changes require nullable columns**
   - Until Alembic is set up (Phase 9), new columns must be `nullable=True`
   - After Alembic: proper `ALTER TABLE` migrations

6. **Web auth uses cookies, API auth uses Bearer tokens**
   - Web routes check `request.cookies.get("auth_token")`
   - API routes use `Depends(get_current_user)` which reads Bearer header
