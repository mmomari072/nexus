# AgileAI Platform

A local-first, AI-native Agile project management platform supporting multi-human and multi-agent collaboration. Built for regulated environments.

## Overview

AgileAI implements full Scrum methodology with first-class AI agent integration. Humans and AI agents share the same task board, sprint workflows, and audit trail. The platform runs entirely on-premises — no data leaves your facility.

## Key Features

- Full Scrum workflow: backlog → sprint planning → board → standups → review → retrospective
- Multi-agent support: Assistant, Actor, Reviewer, and Compressor agent roles
- Local AI compression: context optimization via Ollama (zero API cost)
- Regulatory-grade audit trail: field-level change log, access log, compliance checks
- Controlled document management: deliverables with version control, integrity hashing, expiry monitoring
- Remote control: Telegram bot interface for mobile management
- Four frontends: Web UI, Desktop UI, CLI, Textual TUI — all sharing one API
- MCP server: Claude and MCP-compatible agents can natively read/write the board

## Architecture

```
Web UI / Desktop / CLI / Textual TUI
              ↓
        FastAPI Core API
        ↙           ↘
   SQLite DB     Agent Gateway
                (REST + MCP)
                     ↓
          AI Agents (Claude / Ollama / Custom)
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0
- **Database**: SQLite (via aiosqlite for async)
- **Migrations**: Alembic
- **Local AI**: Ollama (compression, embeddings, summarization)
- **External AI**: Anthropic Claude API
- **CLI**: Typer + Rich
- **TUI**: Textual
- **Desktop**: PyQt6
- **Telegram**: python-telegram-bot

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Initialize database
agileai db init

# Start API server
agileai serve

# Launch TUI
agileai tui

# Register first agent
agileai agent register --name "Zephyr" --model phi3:mini --role compressor
```

## Project Structure

```
agileai/
├── agileai/
│   ├── models/          # SQLAlchemy ORM models (85 tables, 26 modules)
│   ├── api/             # FastAPI routes and Pydantic schemas
│   ├── agents/          # Agent lifecycle, gateway, protocols
│   ├── gateway/         # REST + MCP agent gateway
│   ├── services/        # Business logic layer
│   └── utils/           # Shared utilities
├── docs/
│   ├── agents.md        # Agent system documentation
│   ├── schema.md        # Full database schema reference
│   └── workflow.md      # Scrum workflow documentation
├── migrations/          # Alembic migration files
├── tests/
└── scripts/             # Seed data, maintenance scripts
```

## Database Schema

85 tables across 14 concern groups. See `docs/schema.md` for full reference.

| Group | Tables |
|---|---|
| AI & Identity | ai_models, agents, users, api_keys |
| Skills | skill_definitions, agent_skills, issue_skill_requirements |
| RBAC | roles, permissions, role_permissions, actor_role_assignments |
| Teams | assignee_teams, assignee_team_members, agent_teams, agent_team_members |
| Projects | projects, labels, project_metadata, data_classifications |
| Issues | issues, issue_labels, issue_links, issue_assignments, issue_watchers, issue_instructions, instruction_completions, issue_templates |
| Sprints | sprints, sprint_issues, sprint_goals, sprint_events, sprint_capacity, burndown_snapshots |
| Ceremonies | ceremonies, standup_records, standup_items |
| Quality Gates | definition_of_ready, definition_of_done, dor_checks, dod_checks |
| Workflow | status_transitions, handovers, impediments, workflows, workflow_steps, workflow_runs |
| Regulatory | compliance_checks, approval_workflows, approval_requests, access_log |
| Agent Ops | agent_availability, task_queue, execution_logs, agent_feedback, agent_logs, agent_messages |
| Memory & Compression | project_memory, context_compression_rules, context_snapshots, content_embeddings |
| Deliverables | deliverables, deliverable_status_history, deliverable_distributions, deliverable_dependencies, expected_deliverables |
| Reports | report_definitions, report_instances, report_schedules |
| History | issue_change_log, notes, velocity_records, time_entries |
| Notifications | notification_rules, notification_templates, notifications |
| Contacts | user_contacts, telegram_commands |
| Jobs | background_jobs |

## License

Internal use — Jordan Atomic Energy Commission
# nexus
