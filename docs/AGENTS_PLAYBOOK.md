# Agents Playbook

Detailed instructions for each AI agent role on the AgileAI project.
Read this before starting any work. Also read `DEVELOPMENT_PLAN.md` and `docs/WORKFLOW.md`.

---

## 0. Universal Rules (All Agents)

1. **Read before writing.** Always run `git pull origin main` and read the files you'll touch before editing.
2. **Use the existing SDK.** All HTTP communication goes through `agileai/client/`. Never write raw HTTP calls.
3. **Test before PR.** Run `pytest` and ensure the tests you're responsible for pass.
4. **One branch per feature.** Branch names: `feature/phase-N-description` or `fix/short-description`.
5. **Never commit to `main` directly.** All work goes through PRs reviewed by Agent Epsilon.
6. **Small, focused PRs.** If a PR exceeds 400 lines of diff, split it.
7. **No secrets in code.** Config goes in `.env` loaded via `pydantic-settings`. Use `.env.example` for templates.
8. **Always async in FastAPI.** All DB queries use `async with AsyncSessionLocal() as db`.
9. **Respect the import order.** For root-level models: `from __init__ import SomeModel`. For service models: `from agileai.models import ...`.
10. **Mark tasks in-progress before starting, completed when done.** Update `docs/BOARD.md`.

---

## Agent Alpha — Actor (CLI + Agent Gateway)

### Sprint 1 Scope
Build `agileai/cli/` from scratch. This is a terminal command-line interface using Typer + Rich.

### Sprint 2 Scope
Build `agileai/agents/gateway.py` — the FastAPI router that agents poll for tasks.

### Starting Point
```bash
git checkout -b feature/phase-3-cli
pip install -e ".[dev]"
```

### CLI Architecture
```
agileai/cli/
├── __init__.py
├── main.py          # typer.Typer() root app, sub-apps attached here
├── config.py        # ~/.agileai/config.json (base_url, timeout)
├── auth.py          # login/logout, token stored in ~/.agileai/token
├── backlog.py       # backlog subcommand group
├── sprint.py        # sprint subcommand group
└── agents.py        # agents + models subcommand group
```

### Entry Point Pattern
```python
# agileai/cli/main.py
import typer
from agileai.cli.auth import app as auth_app
from agileai.cli.backlog import app as backlog_app
# ...
app = typer.Typer(name="agileai", help="AgileAI CLI")
app.add_typer(backlog_app, name="backlog")
app.add_typer(auth_app, name="auth")  # or top-level: login/logout

if __name__ == "__main__":
    app()
```

### Token Storage Pattern
```python
# agileai/cli/auth.py
from pathlib import Path
import json

CONFIG_DIR = Path.home() / ".agileai"
TOKEN_FILE = CONFIG_DIR / "token"
CONFIG_FILE = CONFIG_DIR / "config.json"

def save_token(token: str) -> None:
    CONFIG_DIR.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(token)

def load_token() -> str | None:
    return TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else None
```

### Rich Output Pattern
```python
from rich.console import Console
from rich.table import Table

console = Console()

def print_issues(issues: list) -> None:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=12)
    table.add_column("Title", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Priority", justify="center")
    table.add_column("Points", justify="right")
    for issue in issues:
        table.add_row(issue["id"][:12], issue["title"], issue["status"],
                      issue.get("priority","—"), str(issue.get("story_points","—")))
    console.print(table)
```

### Client Usage Pattern
```python
from agileai.client.sync_client import AgileAIClient
from agileai.cli.auth import load_token
from agileai.cli.config import load_config

def get_client() -> AgileAIClient:
    cfg = load_config()
    token = load_token()
    if not token:
        raise typer.BadParameter("Not logged in. Run: agileai login")
    return AgileAIClient(base_url=cfg["base_url"], token=token)
```

### Commands to Implement
```
agileai login                          # prompt email + password → store JWT
agileai logout                         # delete token file
agileai config set-url <url>           # save base_url to config

agileai backlog list <project_id>      # rich.Table of issues
agileai backlog show <project_id> <id> # single issue detail
agileai backlog estimate <project_id> <id> [--difficulty] [--importance]
agileai backlog prioritize <project_id>
agileai backlog reorder <project_id> <id> --after <ref_id>

agileai sprint list <project_id>       # sprint cards
agileai sprint create <project_id> --name --goal --start --end
agileai sprint start <project_id> <sprint_id>
agileai sprint complete <project_id> <sprint_id>

agileai agents list                    # roster with status
agileai models list                    # AI model registry
```

### Test Pattern
```python
# tests/test_cli.py
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from agileai.cli.main import app

runner = CliRunner()

def test_backlog_list_requires_login():
    result = runner.invoke(app, ["backlog", "list", "proj-1"])
    assert result.exit_code != 0 or "login" in result.output.lower()

def test_login_stores_token(tmp_path, monkeypatch):
    monkeypatch.setattr("agileai.cli.auth.CONFIG_DIR", tmp_path)
    with patch("agileai.client.sync_client.AgileAIClient.login", return_value="fake-token"):
        result = runner.invoke(app, ["login", "--email", "a@b.com", "--password", "pw"])
    assert (tmp_path / "token").exists()
```

### Definition of Done (Phase 3)
- [ ] `agileai --help` shows all commands
- [ ] `agileai login` stores token
- [ ] `agileai backlog list <id>` renders Rich table
- [ ] `agileai sprint list <id>` renders sprint cards
- [ ] `pytest tests/test_cli.py` ≥ 10 tests, all pass
- [ ] `pyproject.toml [project.scripts]` entry: `agileai = "agileai.cli.main:app"`

---

## Agent Beta — Actor (TUI + Telegram)

### Sprint 1 Scope
Build `agileai/tui/` using Textual.

### Sprint 2 Scope
Build `agileai/telegram/` using python-telegram-bot.

### Starting Point
```bash
git checkout -b feature/phase-4-tui
pip install -e ".[dev]"
python -c "import textual; print(textual.__version__)"
```

### TUI Architecture
```
agileai/tui/
├── __init__.py
├── app.py                # App(Application) — entry point
├── theme.css             # Textual CSS
├── bindings.py           # Key binding constants
└── screens/
    ├── login.py          # LoginScreen
    ├── projects.py       # ProjectsScreen
    ├── backlog.py        # BacklogScreen
    ├── issue_detail.py   # IssueDetailScreen
    ├── sprints.py        # SprintsScreen
    └── agents.py         # AgentsScreen
```

### App Pattern
```python
# agileai/tui/app.py
from textual.app import App, ComposeResult
from textual.binding import Binding
from agileai.tui.screens.login import LoginScreen
from agileai.tui.screens.projects import ProjectsScreen

class AgileAIApp(App):
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+b", "switch_screen('backlog')", "Backlog"),
    ]
    CSS_PATH = "theme.css"

    def on_mount(self) -> None:
        self.push_screen(LoginScreen())

def main() -> None:
    AgileAIApp().run()
```

### Screen Pattern
```python
# agileai/tui/screens/backlog.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Header, Footer, Button, Input
from textual.reactive import reactive

class BacklogScreen(Screen):
    project_id: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="backlog-table")
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Title", "Status", "Priority", "Points")
        await self.refresh_data()

    async def refresh_data(self) -> None:
        from agileai.client.async_client import AgileAIClient
        from agileai.tui.app import get_client
        client = get_client()
        backlog = await client.list_backlog(self.project_id)
        table = self.query_one(DataTable)
        table.clear()
        for issue in backlog.issues:
            table.add_row(issue.id[:12], issue.title, issue.status,
                         issue.priority, str(issue.story_points or "—"))

    def on_key(self, event) -> None:
        if event.key == "e":
            row = self.query_one(DataTable).cursor_row
            # Open estimation modal
            pass
```

### Key Bindings
| Key | Action |
|-----|--------|
| `j/k` or arrows | Navigate rows |
| `Enter` | Open detail |
| `e` | Estimate issue |
| `s` | Assign to sprint |
| `n` | New issue |
| `r` | Refresh |
| `q` | Back / Quit |
| `ctrl+p` | Projects |
| `ctrl+b` | Backlog |
| `ctrl+s` | Sprints |
| `ctrl+a` | Agents |

### Telegram Architecture
```
agileai/telegram/
├── __init__.py
├── bot.py                # Application entry, command registration
├── commands.py           # /backlog /sprint /assign /status /standup
└── notifications.py      # Push notifications via bot.send_message
```

### Telegram Pattern
```python
# agileai/telegram/bot.py
from telegram.ext import Application, CommandHandler
from agileai.telegram.commands import backlog_cmd, sprint_cmd, assign_cmd

def main() -> None:
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("backlog", backlog_cmd))
    app.add_handler(CommandHandler("sprint", sprint_cmd))
    app.run_polling()
```

### Definition of Done (Phase 4)
- [ ] `agileai tui` launches and shows LoginScreen
- [ ] Navigate to Projects → select project → BacklogScreen shows issues
- [ ] Press `e` on issue → estimation modal appears
- [ ] Navigate to Sprints screen, Agents screen
- [ ] No crashes during normal navigation

### Definition of Done (Phase 7)
- [ ] Bot responds to `/backlog proj-1` with formatted issue list
- [ ] Bot responds to `/sprint proj-1` with active sprint status
- [ ] Sprint start event sends notification to configured channel

---

## Agent Gamma — Actor (Desktop + Compression)

### Sprint 2 Scope
Build `agileai/desktop/` using PyQt6.

### Sprint 3 Scope
Build `agileai/compression/` using Ollama.

### Starting Point
```bash
git checkout -b feature/phase-5-desktop
pip install -e ".[dev]"
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
```

### Desktop Architecture
```
agileai/desktop/
├── __init__.py
├── main.py              # QApplication entry, agileai desktop
├── app.py               # AgileAIDesktop main class
├── windows/
│   ├── main_window.py   # MainWindow (MDI or docked)
│   └── login_dialog.py  # LoginDialog
├── widgets/
│   ├── backlog_table.py # QTableView + BacklogModel
│   ├── sprint_card.py   # Custom QWidget for sprint card
│   └── agent_roster.py  # Agent list widget
├── models/
│   ├── backlog_model.py # QAbstractTableModel for issues
│   └── sprint_model.py  # QAbstractListModel for sprints
└── workers.py           # QThread workers for async HTTP
```

### Worker Pattern
```python
# agileai/desktop/workers.py
from PyQt6.QtCore import QThread, pyqtSignal
from agileai.client.sync_client import AgileAIClient

class BacklogFetcher(QThread):
    data_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, client: AgileAIClient, project_id: str):
        super().__init__()
        self.client = client
        self.project_id = project_id

    def run(self) -> None:
        try:
            result = self.client.list_backlog(self.project_id)
            self.data_ready.emit(result.issues)
        except Exception as e:
            self.error.emit(str(e))
```

### Compression Architecture
```
agileai/compression/
├── __init__.py
├── worker.py            # APScheduler background job
├── compressor.py        # Ollama summarization
├── embedder.py          # nomic-embed-text via Ollama
└── context_builder.py   # Assemble context for agent gateway
```

### Compression Worker Pattern
```python
# agileai/compression/worker.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from agileai.compression.compressor import compress_issue

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", seconds=30)
async def process_compression_queue():
    async with AsyncSessionLocal() as db:
        jobs = await db.execute(
            select(BackgroundJob).where(
                BackgroundJob.job_type == "compress",
                BackgroundJob.status == "pending"
            ).limit(5)
        )
        for job in jobs.scalars():
            await compress_issue(db, job.entity_id)
            job.status = "completed"
        await db.commit()
```

### Ollama Pattern
```python
# agileai/compression/compressor.py
import ollama

async def summarize(text: str, model: str = "qwen2.5") -> str:
    response = await ollama.AsyncClient().chat(
        model=model,
        messages=[{"role": "user", "content": f"Summarize concisely:\n\n{text}"}]
    )
    return response.message.content
```

### Definition of Done (Phase 5)
- [ ] `agileai desktop` opens LoginDialog
- [ ] Login succeeds, MainWindow opens with project list
- [ ] BacklogTable shows issues with sorting
- [ ] Sprint widget shows sprint cards with progress

### Definition of Done (Phase 8)
- [ ] Worker processes `background_jobs` queue
- [ ] Summaries written to `context_snapshots`
- [ ] Embeddings written to `content_embeddings`
- [ ] Graceful degradation if Ollama not running

---

## Agent Delta — Actor (Backend API + DevOps)

### Ongoing Scope
Expand the API from 30% to 100% coverage, set up Alembic, and harden for production.

### Starting Point
```bash
git checkout -b feature/phase-9-api-expansion
```

### Priority Order
1. **Sprint API** (needed by CLI/TUI immediately)
2. **Projects API** (replace in-memory PROJECTS list)
3. **Agents API** (needed by gateway)
4. **Users API** (profile, team management)
5. **Notifications + Approvals API**
6. **Reports + Wiki API**
7. Alembic migrations
8. Docker + CI

### Router Pattern
Each new domain gets its own router file:
```
agileai/api/routers/
├── auth.py        ✅ done
├── backlog.py     ✅ done
├── sprints.py     🔲 to build
├── projects.py    🔲 to build
├── agents.py      🔲 to build (gateway-facing)
├── users.py       🔲 to build
├── notifications.py 🔲 to build
└── wiki.py        🔲 to build
```

### Sprint API Target Shape
```
GET  /api/v1/sprints/projects/{project_id}              → list sprints
POST /api/v1/sprints/projects/{project_id}              → create sprint
GET  /api/v1/sprints/{sprint_id}                        → get sprint
PUT  /api/v1/sprints/{sprint_id}                        → update sprint
POST /api/v1/sprints/{sprint_id}/start                  → start sprint
POST /api/v1/sprints/{sprint_id}/complete               → complete sprint
GET  /api/v1/sprints/{sprint_id}/issues                 → sprint issues
POST /api/v1/sprints/{sprint_id}/ceremony               → add ceremony
```

### Projects API (Replace In-Memory)
The `PROJECTS` list in `agileai/web/routes.py` must be replaced with real DB queries.
The `Project` model exists in `__init__.py` with `id, slug, status` fields.
Add `name` and `description` columns to Project (nullable, to avoid migration pain).

### Alembic Setup
```bash
alembic init alembic
# Edit alembic/env.py to use async SQLAlchemy
# Edit alembic.ini: sqlalchemy.url = sqlite+aiosqlite:///agileai.db
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

Replace the `Base.metadata.create_all` in `agileai/api/main.py` lifespan with:
```python
from alembic.config import Config
from alembic import command as alembic_command

async def run_migrations():
    alembic_cfg = Config("alembic.ini")
    alembic_command.upgrade(alembic_cfg, "head")
```

### Definition of Done (Phase 9)
- [ ] Sprint API endpoints all functional with tests
- [ ] Projects API functional (real DB, not in-memory)
- [ ] Agents API functional
- [ ] Alembic init done, first migration clean
- [ ] `.env.example` documents all env vars
- [ ] `docker-compose.prod.yml` builds and runs

---

## Agent Epsilon — Reviewer

### Scope
Review all PRs from Agents Alpha, Beta, Gamma, Delta. Do not build features.

### Review Checklist
For every PR, verify:

**Code quality:**
- [ ] No raw SQL — all queries via SQLAlchemy ORM
- [ ] All DB operations are `async`
- [ ] No hardcoded secrets, URLs, or tokens
- [ ] No `print()` — use `rich.console` in CLI, `logging` in API
- [ ] Type hints on all public functions
- [ ] No circular imports

**Tests:**
- [ ] Tests exist for the new code
- [ ] `pytest` passes with no failures
- [ ] Test coverage doesn't decrease

**Architecture:**
- [ ] Uses `agileai/client/` for HTTP — no raw requests
- [ ] New routers added to `agileai/api/main.py`
- [ ] New CLI commands added to `pyproject.toml` scripts section
- [ ] No re-implementation of existing functionality

**Security:**
- [ ] No SQL injection risk
- [ ] Auth required on new endpoints (`Depends(get_current_user)`)
- [ ] Form inputs validated via Pydantic

**PR format:**
- Approve with ✅ comment listing what was verified
- Request changes with specific line references
- Do not merge — human coordinator (Mohammad OMARI) merges

---

## Agent Zeta — Scrum Master

### Scope
Run sprint ceremonies, track impediments, update the board, and keep the team aligned.

### Responsibilities
- **Sprint planning:** At sprint start, confirm S1/S2/S3/S4 items are assigned, sized, and unblocked
- **Daily standup:** Each session, ask each active agent: "What did you complete? What's next? Any blockers?"
- **Impediment tracking:** Add blocked items to `docs/PROJECT_LOG.md` under ## Impediments
- **Sprint review:** At sprint end, update `docs/BOARD.md` — move items to Done, calculate velocity
- **Retrospective:** After each sprint, add a `## Sprint N Retrospective` section to PROJECT_LOG.md

### Board Update Protocol
When an item changes status, update `docs/BOARD.md`:
1. Move item to correct column
2. Add completion date if Done
3. Update the sprint velocity metric at the bottom

### Standup Format
```
## Daily Standup — 2026-MM-DD

### Agent Alpha
- Done: CLI login/logout commands
- Doing: backlog list command with Rich table
- Blocked: None

### Agent Beta
- Done: TUI LoginScreen
- Doing: ProjectsScreen
- Blocked: Needs Sprint API from Agent Delta (S1-10)
```

Write standups to `docs/PROJECT_LOG.md` under the relevant sprint section.

---

## Quick Reference

### Running the server
```bash
cd /path/to/nexus
python -m uvicorn agileai.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running tests
```bash
pytest tests/test_backlog.py -v          # existing tests
pytest tests/ -v                          # all tests
pytest tests/test_cli.py -v              # CLI tests (after Phase 3)
```

### Database reset
```bash
rm -f agileai.db agileai.db-shm agileai.db-wal
# Restart server — create_all recreates schema
```

### Checking routes
```bash
python -c "from agileai.api.main import app; [print(r.path) for r in app.routes if hasattr(r,'path')]"
```

### Key files
| File | Purpose |
|------|---------|
| `__init__.py` | All 85 ORM models — import from here |
| `agileai/api/main.py` | FastAPI app, route mounting |
| `agileai/api/dependencies.py` | JWT auth, DB session |
| `agileai/web/routes.py` | Web UI routes (66 routes) |
| `agileai/web/admin.py` | Generic admin CRUD |
| `agileai/client/sync_client.py` | HTTP client for CLI/Desktop |
| `agileai/client/async_client.py` | HTTP client for TUI/background |
| `agileai/services/backlog/service.py` | Backlog business logic |
