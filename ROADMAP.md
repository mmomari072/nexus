# AgileAI Roadmap

> Milestone timeline for multi-agent parallel development.
> Sprints are 2 weeks. Start date: **2026-05-23**.

---

## Milestone Overview

```
2026-05-23 ──────────────────────────────────────────────────── 2026-07-18
    │                    │                    │                    │
    ▼                    ▼                    ▼                    ▼
Sprint 1            Sprint 2            Sprint 3            Sprint 4
2026-05-23          2026-06-07          2026-06-21          2026-07-05
CLI + TUI +         Desktop +           Compression +       Analytics +
API Expand          Gateway +           Alembic +           Reports +
                    Telegram            CI/CD               Polish
    │                    │                    │                    │
    ▼                    ▼                    ▼                    ▼
M1: 2026-06-06      M2: 2026-06-20      M3: 2026-07-04      M4: 2026-07-18
CLI working         Agent gateway       Full system          Production
TUI working         operational         on Docker            release
```

---

## Sprint 1: Foundation Frontends (2026-05-23 → 2026-06-06)

**Sprint Goal:** All command-line and terminal users can interact with the full backlog and sprint workflow without touching the browser.

### Deliverables

| # | Item | Owner | Status |
|---|------|-------|--------|
| S1-01 | CLI: `agileai login/logout` with token file | Agent Alpha | 🔲 Backlog |
| S1-02 | CLI: `agileai backlog list/estimate/prioritize` | Agent Alpha | 🔲 Backlog |
| S1-03 | CLI: `agileai sprint list/create/start` | Agent Alpha | 🔲 Backlog |
| S1-04 | CLI: `agileai agents list / models list` | Agent Alpha | 🔲 Backlog |
| S1-05 | CLI: `pytest tests/test_cli.py` (≥10 tests) | Agent Alpha | 🔲 Backlog |
| S1-06 | TUI: Login screen + Projects screen | Agent Beta | 🔲 Backlog |
| S1-07 | TUI: Backlog screen with keyboard nav | Agent Beta | 🔲 Backlog |
| S1-08 | TUI: Sprints + Agents screens | Agent Beta | 🔲 Backlog |
| S1-09 | TUI: Issue detail screen | Agent Beta | 🔲 Backlog |
| S1-10 | API: Sprint REST endpoints | Agent Delta | 🔲 Backlog |
| S1-11 | API: User/Project real DB queries | Agent Delta | 🔲 Backlog |
| S1-12 | API: Agents REST endpoints | Agent Delta | 🔲 Backlog |
| S1-13 | Alembic: init + first migration | Agent Delta | 🔲 Backlog |

**Milestone 1 criteria:** `agileai backlog list proj-1` returns formatted table with real data from the DB.

---

## Sprint 2: Agent Infrastructure (2026-06-07 → 2026-06-20)

**Sprint Goal:** AI agents can autonomously receive tasks, execute them, and submit results via the gateway. Telegram users get live notifications.

### Deliverables

| # | Item | Owner | Status |
|---|------|-------|--------|
| S2-01 | Desktop: Login + MainWindow shell | Agent Gamma | 🔲 Backlog |
| S2-02 | Desktop: Backlog QTableView | Agent Gamma | 🔲 Backlog |
| S2-03 | Desktop: Sprint + Agents widgets | Agent Gamma | 🔲 Backlog |
| S2-04 | Agent Gateway: poll / result / heartbeat | Agent Alpha | 🔲 Backlog |
| S2-05 | Agent Gateway: MCP server (tool definitions) | Agent Alpha | 🔲 Backlog |
| S2-06 | Agent Gateway: context assembly | Agent Alpha | 🔲 Backlog |
| S2-07 | Telegram: bot setup + /backlog /sprint | Agent Beta | 🔲 Backlog |
| S2-08 | Telegram: /assign /status /standup | Agent Beta | 🔲 Backlog |
| S2-09 | Telegram: notifications on sprint events | Agent Beta | 🔲 Backlog |
| S2-10 | API: Notifications + Approvals endpoints | Agent Delta | 🔲 Backlog |
| S2-11 | API: Reports + Wiki endpoints | Agent Delta | 🔲 Backlog |
| S2-12 | Web UI: Replace in-memory PROJECTS with DB | Agent Delta | 🔲 Backlog |

**Milestone 2 criteria:** An agent can authenticate, poll for a task, receive compressed context, execute, and submit a result. Sprint notifications arrive on Telegram.

---

## Sprint 3: Compression + Production (2026-06-21 → 2026-07-04)

**Sprint Goal:** The platform runs in production Docker Compose with Ollama, full audit trail, and CI pipeline.

### Deliverables

| # | Item | Owner | Status |
|---|------|-------|--------|
| S3-01 | Compression: APScheduler worker | Agent Gamma | 🔲 Backlog |
| S3-02 | Compression: Ollama summarization | Agent Gamma | 🔲 Backlog |
| S3-03 | Compression: nomic-embed-text embeddings | Agent Gamma | 🔲 Backlog |
| S3-04 | Production: `docker-compose.prod.yml` | Agent Delta | 🔲 Backlog |
| S3-05 | Production: `.env.example` + settings | Agent Delta | 🔲 Backlog |
| S3-06 | Production: Alembic auto-upgrade on start | Agent Delta | 🔲 Backlog |
| S3-07 | CI: GitHub Actions lint + test + build | Agent Delta | 🔲 Backlog |
| S3-08 | E2E: Playwright web UI tests (5 critical paths) | Agent Epsilon | 🔲 Backlog |
| S3-09 | Desktop: packaging with PyInstaller | Agent Gamma | 🔲 Backlog |
| S3-10 | CLI: packaging + pip install works | Agent Alpha | 🔲 Backlog |

**Milestone 3 criteria:** `docker compose up` produces fully operational system. CI is green.

---

## Sprint 4: Analytics + Polish (2026-07-05 → 2026-07-18)

**Sprint Goal:** Stakeholders have dashboards, reports, and a wiki. The platform is documented and release-ready.

### Deliverables

| # | Item | Owner | Status |
|---|------|-------|--------|
| S4-01 | Web: Reports dashboard | Agent Beta | 🔲 Backlog |
| S4-02 | Web: Velocity + burndown charts | Agent Beta | 🔲 Backlog |
| S4-03 | Web: Wiki / Knowledge base browser | Agent Beta | 🔲 Backlog |
| S4-04 | Web: Notifications inbox | Agent Beta | 🔲 Backlog |
| S4-05 | Web: Approval workflows UI | Agent Alpha | 🔲 Backlog |
| S4-06 | Web: Global search across all entities | Agent Alpha | 🔲 Backlog |
| S4-07 | Web: Audit trail viewer | Agent Alpha | 🔲 Backlog |
| S4-08 | Load testing: k6 API throughput | Agent Epsilon | 🔲 Backlog |
| S4-09 | Security audit: OWASP Top 10 | Agent Epsilon | 🔲 Backlog |
| S4-10 | Documentation: full README + API docs | Agent Delta | 🔲 Backlog |
| S4-11 | Release: v1.0.0 tag + changelog | All | 🔲 Backlog |

**Milestone 4 criteria:** v1.0.0 tagged, all tests green, Docker Compose up produces full system.

---

## Dependency Graph

```
Phase 1 (Auth + SDK)  ──────────────────────────────────────────────┐
          │                                                           │
          ▼                                                           │
Phase 2 (Web UI) ──────► Phase 9 (API expand) ──► Phase 10 (Prod)   │
          │                      │                                    │
          ├──► Phase 3 (CLI) ────┤                                   │
          │                      │                                    │
          ├──► Phase 4 (TUI) ────┤                                   │
          │                      │                                    │
          ├──► Phase 5 (Desktop)─┤                                   │
          │                      │                                    │
          └──► Phase 6 (Gateway)─┴──► Phase 8 (Compression) ────────┘
                    │
                    └──► Phase 7 (Telegram)
```

**Critical path:** Phase 9 (API expand) blocks CLI/TUI real-data functionality.  
**Parallelisable:** Phases 3, 4, 5, 7 can run concurrently with Phase 9.

---

## Version Targets

| Version | Date | Contents |
|---------|------|----------|
| v0.1.0 | 2026-05-23 | Web UI complete (current) |
| v0.2.0 | 2026-06-06 | CLI + TUI functional |
| v0.3.0 | 2026-06-20 | Agent gateway + Telegram operational |
| v0.4.0 | 2026-07-04 | Compression + CI + Docker production |
| v1.0.0 | 2026-07-18 | Full platform release |
