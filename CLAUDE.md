# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AgileAI** is a local-first, AI-native Agile project management platform supporting multi-human and multi-agent collaboration. Built for regulated environments, it implements full Scrum methodology with first-class AI agent integration. The platform is entirely on-premises with no external data transmission.

**Core Value Proposition**: Humans and AI agents share the same task board, sprint workflows, and audit trail. Four different agent roles (Actor, Reviewer, Assistant, Compressor) integrate seamlessly with human team members.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 with async support (aiosqlite)
- **Database**: SQLite (single-file, portable, suitable for on-premises regulation)
- **AI Integration**: 
  - External: Anthropic Claude API
  - Local: Ollama (phi3:mini, mistral:7b, qwen2.5, nomic-embed-text for embeddings)
- **Frontends**: Web UI, Desktop UI (PyQt6), CLI (Typer + Rich), TUI (Textual)
- **External Integrations**: Telegram bot (python-telegram-bot), MCP server protocol
- **Tooling**: Alembic (migrations), APScheduler (background jobs), pytest + asyncio for testing

## Architecture

Three-layer design:

1. **Frontend Layer**: Web, Desktop, CLI, Textual TUI — all stateless
2. **API Layer**: FastAPI core with async session handling, Pydantic schemas, authentication (JWT + passlib)
3. **Data Layer**: SQLAlchemy ORM with 85 tables across 14 concern groups, all async-first

### Key Modules (at project root: `/home/omari/ai_agent_tools/nexus/`)

- **`identity.py`**: AIModel, Agent, User, APIKey — defines agent and user identities
- **`issues.py`**: Issue, IssueLabel, IssueLink, IssueAssignment — Scrum board entities
- **`database.py`**: AsyncEngine setup, session factory, trigger registration for audit trail
- **`__init__.py`**: Centralized model imports — registers all 85 ORM models with metadata before migrations

These three files define core models that are imported by the FastAPI services and agent gateway. They're foundational — changes here cascade across the platform.

## Database Schema (85 Tables in 14 Groups)

Key groups referenced most often:

| Group | Purpose | Key Tables |
|-------|---------|-----------|
| AI & Identity | Agent and user registration | `ai_models`, `agents`, `users`, `api_keys` |
| Issues | Scrum board state | `issues`, `issue_assignments`, `issue_change_log`, `issue_instructions` |
| Sprints | Sprint lifecycle and metrics | `sprints`, `sprint_issues`, `burndown_snapshots`, `sprint_capacity` |
| Skills | Agent capability matching | `skill_definitions`, `agent_skills`, `issue_skill_requirements` |
| RBAC | Access control | `roles`, `permissions`, `role_permissions`, `actor_role_assignments` |
| Agent Ops | Task dispatch, logs, feedback | `task_queue`, `execution_logs`, `agent_feedback`, `agent_availability` |
| Quality Gates | Readiness and completion criteria | `definition_of_ready`, `definition_of_done`, `dor_checks`, `dod_checks` |
| Regulatory | Audit trail and approvals | `access_log`, `compliance_checks`, `approval_workflows`, `approval_requests` |

See `schema.md` for the full reference with field descriptions.

## Agent System Fundamentals

Agents are first-class team members. Every agent has:
- An identity (id, name, api_key for authentication)
- A role: `actor` (executes tasks), `reviewer` (validates work), `assistant` (advisory), `compressor` (local offline summarization), `scrum_master` (facilitates ceremonies)
- Skills declared in `agent_skills` (skill matching for task assignment)
- Team memberships and project assignments via `actor_role_assignments`
- Availability status in `agent_availability` (tracks if agent is online/busy)

**Task Flow**: Issue created → Agent assigned → Task queued in `task_queue` → Agent polls via gateway (REST or MCP) → Receives compressed context via `project_memory` and `context_snapshots` → Executes → Attaches result to issue → Updates `issue_change_log` for audit

**Compression Agent** runs locally via Ollama and processes `background_jobs` continuously, writing summaries back to notes and execution logs for context optimization.

## Common Development Commands

```bash
# Setup
pip install -e ".[dev]"

# Database initialization (creates sqlite DB and runs seed data if provided)
agileai db init

# Migrations (Alembic)
alembic upgrade head     # Apply all pending migrations
alembic revision --autogenerate -m "description"  # Create migration
alembic downgrade -1     # Revert last migration

# Testing
pytest                   # Run all tests
pytest tests/test_issues.py  # Run single test file
pytest -k test_assign_issue  # Run specific test by name
pytest --cov=agileai    # Run with coverage report

# Linting & type checking
black agileai/           # Format code
ruff check agileai/      # Lint
mypy agileai/            # Type check (slow, but catches real issues)

# Running the server
agileai serve            # Start FastAPI on http://localhost:8000
agileai tui              # Launch terminal UI
agileai agent register --name "AgentName" --model "model-id" --role "actor"  # Register agent

# Code style
Line length: 100 (black and ruff configured)
Target Python: 3.11+
Async mode: pytest-asyncio with auto mode enabled
```

## Code Patterns & Conventions

**Async Everything**: All database operations use `async`/`await`. SessionLocal is async. Use `asynccontextmanager` for fixture cleanup.

**SQLAlchemy 2.0 + Async**: All models inherit from `Base` (defined in `models/base.py`). Use `Mapped[...]` type hints with `mapped_column()`. Foreign keys are strings referencing table names, not live objects — lazy loading not supported in async context.

**Audit Trail**: `TimestampMixin` automatically registers `created_at` and `updated_at` triggers on all inheriting tables via SQLite event hooks in `database.py`. Never manually update these fields.

**Pydantic Schemas**: Separate Pydantic schemas from ORM models. Schemas in API routes, ORM models in database layer. Use `ConfigDict(from_attributes=True)` to bridge them.

**Authentication**: API keys stored in `api_keys` table. Agents authenticate with their token via header. FastAPI dependency injection for current_user.

**Error Handling**: Exceptions cascade from models → services → API routes. Use `HTTPException` for API errors with proper status codes.

**Background Jobs**: Long-running operations (compression, summarization) queued in `background_jobs` table and picked up by the Compressor Agent. Never block the request-response cycle.

## Key Files to Read First When Starting

1. `README.md` — High-level overview and feature list
2. `agents.md` — Agent roles, registration, and task flow  
3. `schema.md` — Database schema reference (65 pages, searchable)
4. `identity.py` — Agent and user identity structure
5. `issues.py` — Issue and task board models
6. `database.py` — Async engine setup and session management

## Important Constraints for Regulated Environments

- **No external data transmission**: All data stays on-premises. Ollama runs locally.
- **Full audit trail**: Every field change logged in `issue_change_log`. Access patterns recorded in `access_log`.
- **Data classification**: Each project has `data_classifications` for sensitivity levels.
- **Approval workflows**: Regulatory workflows defined in `approval_workflows` and monitored in `compliance_checks`.
- **Version control**: Deliverables have `deliverable_status_history` for immutable records.

## Performance Considerations

- **Context compression**: Use Compressor Agent (Ollama) to summarize long issue histories before sending to external AI. Query `context_snapshots` for pre-computed summaries.
- **Async patterns**: All I/O is async. Never use `sync` SQLAlchemy calls in FastAPI endpoints.
- **Indexing**: SQLite has limited indexing. Schema is denormalized for common queries (e.g., `issue_assignments` duplication for fast lookup).
- **Burndown snapshots**: Pre-computed sprint metrics stored daily in `burndown_snapshots` to avoid real-time aggregation.

## Entry Points

- **CLI**: `agileai/cli/main.py` — Typer app with commands
- **Web API**: `agileai/api/main.py` — FastAPI app
- **Agent Gateway**: `agileai/agents/gateway.py` — Handles REST and MCP protocol
- **Services Layer**: `agileai/services/` — Business logic (assignment, sprint planning, compression)
