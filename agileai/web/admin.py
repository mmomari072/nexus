"""Generic admin CRUD covering all 85 ORM tables.

Introspects SQLAlchemy column metadata to auto-generate list/create/edit/delete
views for every registered model. Sidebar groups tables by concern.
"""
from __future__ import annotations

import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import inspect, select, delete as sql_delete
from sqlalchemy.exc import SQLAlchemyError

_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Import every model from the root package
try:
    from __init__ import (
        AIModel, Agent, User, APIKey,
        Role, Permission, RolePermission, ActorRoleAssignment,
        SkillDefinition, AgentSkill, IssueSkillRequirement,
        AssigneeTeam, AssigneeTeamMember, AgentTeam, AgentTeamMember,
        Project, Label, ProjectMetadata, DataClassification,
        Issue, IssueLabel, IssueLink, IssueAssignment, IssueWatcher,
        IssueInstruction, InstructionCompletion, IssueTemplate,
        Sprint, SprintIssue, SprintGoal, SprintCapacity, BurndownSnapshot,
        Ceremony, StandupRecord, StandupItem,
        DefinitionOfReady, DefinitionOfDone, DORCheck, DODCheck,
        Review, ReviewCriterion,
        StatusTransition, Handover, Impediment, Workflow, WorkflowStep, WorkflowRun,
        ComplianceCheck, ApprovalWorkflow, ApprovalRequest, AccessLog,
        AgentAvailability, TaskQueue, ExecutionLog, AgentFeedback,
        AgentLog, AgentMessage, AgentTokenUsage, AgentTokenBudget, TokenBudgetAlert,
        ProjectMemory, ContextCompressionRule, ContextSnapshot, ContentEmbedding,
        IssueChangeLog, Note, VelocityRecord, TimeEntry,
        Deliverable, DeliverableStatusHistory, DeliverableDistribution,
        DeliverableDependency, ExpectedDeliverable,
        ReportDefinition, ReportInstance, ReportSchedule,
        NotificationRule, NotificationTemplate, Notification,
        WikiPage, WikiPageVersion, Attachment,
        UserContact, TelegramCommand,
        BackgroundJob, PromptTemplate, PromptVersion, PromptFragment,
        ModelPerformance,
    )
except ImportError as e:  # pragma: no cover
    raise RuntimeError(f"Failed to import models for admin: {e}")

from agileai.api.dependencies import get_db  # noqa: E402

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Group registry — maps group label → list of model classes
# ---------------------------------------------------------------------------
GROUPS: list[tuple[str, str, list[type]]] = [
    ("AI & Identity",   "🧠", [AIModel, Agent, User, APIKey]),
    ("RBAC",            "🔐", [Role, Permission, RolePermission, ActorRoleAssignment]),
    ("Skills",          "🎯", [SkillDefinition, AgentSkill, IssueSkillRequirement]),
    ("Teams",           "👥", [AssigneeTeam, AssigneeTeamMember, AgentTeam, AgentTeamMember]),
    ("Projects",        "◫",  [Project, Label, ProjectMetadata, DataClassification]),
    ("Issues",          "📝", [Issue, IssueLabel, IssueLink, IssueAssignment, IssueWatcher,
                                IssueInstruction, InstructionCompletion, IssueTemplate]),
    ("Sprints",         "🏃", [Sprint, SprintIssue, SprintGoal, SprintCapacity, BurndownSnapshot,
                                Ceremony, StandupRecord, StandupItem]),
    ("Quality Gates",   "✓",  [DefinitionOfReady, DefinitionOfDone, DORCheck, DODCheck,
                                Review, ReviewCriterion]),
    ("Workflow",        "⚙",  [StatusTransition, Handover, Impediment,
                                Workflow, WorkflowStep, WorkflowRun]),
    ("Regulatory",      "⚖",  [ComplianceCheck, ApprovalWorkflow, ApprovalRequest, AccessLog]),
    ("Agent Ops",       "🤖", [AgentAvailability, TaskQueue, ExecutionLog, AgentFeedback,
                                AgentLog, AgentMessage, AgentTokenUsage, AgentTokenBudget,
                                TokenBudgetAlert]),
    ("Memory",          "🧩", [ProjectMemory, ContextCompressionRule, ContextSnapshot, ContentEmbedding]),
    ("History & Audit", "🕰", [IssueChangeLog, Note, VelocityRecord, TimeEntry]),
    ("Deliverables",    "📦", [Deliverable, DeliverableStatusHistory, DeliverableDistribution,
                                DeliverableDependency, ExpectedDeliverable]),
    ("Reports",         "📊", [ReportDefinition, ReportInstance, ReportSchedule]),
    ("Notifications",   "🔔", [NotificationRule, NotificationTemplate, Notification]),
    ("Knowledge Base",  "📚", [WikiPage, WikiPageVersion, Attachment]),
    ("Contacts",        "📇", [UserContact, TelegramCommand]),
    ("Jobs & Prompts",  "⚡", [BackgroundJob, PromptTemplate, PromptVersion, PromptFragment,
                                ModelPerformance]),
]

# Flat lookup table_name → (model_class, group_label, group_icon)
TABLE_REGISTRY: dict[str, tuple[type, str, str]] = {}
for group_label, group_icon, models in GROUPS:
    for m in models:
        TABLE_REGISTRY[m.__tablename__] = (m, group_label, group_icon)


# ---------------------------------------------------------------------------
# Introspection helpers
# ---------------------------------------------------------------------------
def get_columns(model: type) -> list[Any]:
    """Return all SQLAlchemy columns for a model."""
    return list(inspect(model).columns)


def col_input_html(col: Any, value: Any = None) -> str:
    """Render an HTML input control appropriate for the column type."""
    name = col.name
    val_attr = ""
    if value is not None and not isinstance(value, (datetime, date)):
        val_attr = f'value="{str(value).replace(chr(34), "&quot;")}"'
    elif value is not None:
        val_attr = f'value="{value.isoformat()}"'

    py_type = getattr(col.type, "python_type", str)
    try:
        pt = py_type
    except NotImplementedError:
        pt = str

    if pt is bool:
        checked = "checked" if value else ""
        return f'<input type="checkbox" name="{name}" {checked} class="form-control" style="width:auto">'
    if pt is int:
        return f'<input type="number" name="{name}" {val_attr} class="form-control">'
    if pt is float:
        return f'<input type="number" step="any" name="{name}" {val_attr} class="form-control">'
    if pt is datetime:
        return f'<input type="datetime-local" name="{name}" {val_attr} class="form-control">'
    if pt is date:
        return f'<input type="date" name="{name}" {val_attr} class="form-control">'
    # Long text fields
    length = getattr(col.type, "length", None)
    if length is None or (length and length > 255):
        v = value if value is not None else ""
        return f'<textarea name="{name}" rows="3" class="form-control">{v}</textarea>'
    return f'<input type="text" name="{name}" {val_attr} class="form-control">'


def coerce_value(col: Any, raw: str) -> Any:
    """Coerce a form string into the column's Python type."""
    if raw is None or raw == "":
        return None
    try:
        pt = col.type.python_type
    except NotImplementedError:
        pt = str
    try:
        if pt is bool:
            return raw in ("on", "true", "True", "1")
        if pt is int:
            return int(raw)
        if pt is float:
            return float(raw)
        if pt is datetime:
            return datetime.fromisoformat(raw)
        if pt is date:
            return date.fromisoformat(raw)
        return str(raw)
    except (ValueError, TypeError):
        return raw


def primary_key_col(model: type) -> Any:
    """Return the first primary key column."""
    pk = inspect(model).primary_key
    return pk[0] if pk else None


def row_label(row: Any, model: type) -> str:
    """Best-effort human label for a row."""
    for attr in ("name", "title", "label", "subject", "criterion", "slug", "email"):
        if hasattr(row, attr):
            v = getattr(row, attr)
            if v:
                return str(v)
    pk = primary_key_col(model)
    return str(getattr(row, pk.name, "—"))[:12] if pk else "—"


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------
def _render(content: str, request: Request, breadcrumb: str = "", title: str = "Admin") -> str:
    """Use the main app shell from routes.py."""
    from agileai.web.routes import render_app
    return render_app(
        title=title,
        content=content,
        active_tab="admin",
        breadcrumb=breadcrumb,
        user_name=_username(request),
    )


def _username(request: Request) -> str:
    from agileai.web.routes import get_user_from_cookie
    uid = get_user_from_cookie(request)
    return uid.split("@")[0] if uid else "User"


def admin_sidebar_css() -> str:
    return """
    <style>
      .admin-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem}
      .admin-group{background:white;border-radius:0.75rem;border:1.5px solid var(--c-border);padding:1.25rem}
      .admin-group h3{font-size:0.95rem;font-weight:700;margin-bottom:0.75rem;color:var(--c-text);display:flex;align-items:center;gap:0.5rem}
      .admin-group ul{list-style:none}
      .admin-group li{padding:0.4rem 0;border-bottom:1px solid #f1f5f9;font-size:0.85rem}
      .admin-group li:last-child{border-bottom:none}
      .admin-group a{color:var(--c-text);text-decoration:none;display:flex;justify-content:space-between;align-items:center}
      .admin-group a:hover{color:var(--c-primary)}
      .admin-group .count{font-size:0.7rem;color:var(--c-muted);font-family:monospace}
      .crumb-link{color:var(--c-muted);text-decoration:none}
      .crumb-link:hover{color:var(--c-primary)}
    </style>
    """


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_index(request: Request):
    """Show all 14 groups and the tables in each, with row counts."""
    from database import AsyncSessionLocal as async_session_maker
    counts: dict[str, int] = {}
    async with async_session_maker() as db:
        for table_name, (model, _, _) in TABLE_REGISTRY.items():
            try:
                pk = primary_key_col(model)
                result = await db.execute(select(pk))
                counts[table_name] = len(result.all())
            except SQLAlchemyError:
                counts[table_name] = 0

    sections = []
    for group_label, group_icon, models in GROUPS:
        items = ""
        for m in models:
            tn = m.__tablename__
            cnt = counts.get(tn, 0)
            items += (
                f'<li><a href="/admin/{tn}">'
                f'<span>{m.__name__}</span>'
                f'<span class="count">{cnt} · {tn}</span>'
                f'</a></li>'
            )
        sections.append(
            f'<div class="admin-group">'
            f'<h3>{group_icon} {group_label}</h3>'
            f'<ul>{items}</ul></div>'
        )

    total_tables = len(TABLE_REGISTRY)
    total_rows = sum(counts.values())
    content = admin_sidebar_css() + f"""
    <div class="page-header" style="margin-bottom:1.5rem">
      <h2 style="font-size:1.5rem;font-weight:700;color:var(--c-text);margin-bottom:0.25rem">⚙ Admin</h2>
      <p style="color:var(--c-muted);font-size:0.9rem">
        Generic CRUD for all {total_tables} database tables · {total_rows} total rows
      </p>
    </div>
    <div class="admin-grid">{''.join(sections)}</div>
    """
    breadcrumb = '<a href="/projects" class="crumb-link">Home</a><span class="sep">›</span><span class="current">Admin</span>'
    return HTMLResponse(_render(content, request, breadcrumb=breadcrumb, title="Admin · AgileAI"))


@router.get("/{table_name}", response_class=HTMLResponse)
async def admin_list(table_name: str, request: Request):
    """List all rows in a table."""
    if table_name not in TABLE_REGISTRY:
        return HTMLResponse(f"<h2>Unknown table: {table_name}</h2>", status_code=404)
    model, group_label, group_icon = TABLE_REGISTRY[table_name]
    cols = get_columns(model)

    from database import AsyncSessionLocal as async_session_maker
    rows: list[Any] = []
    error = ""
    async with async_session_maker() as db:
        try:
            result = await db.execute(select(model).limit(200))
            rows = list(result.scalars().all())
        except SQLAlchemyError as e:
            error = str(e)

    # Build the table
    visible_cols = cols[:8]  # cap to avoid wide tables
    th = "".join(f'<th>{c.name}</th>' for c in visible_cols) + "<th>Actions</th>"
    body = ""
    pk_col = primary_key_col(model)
    for row in rows:
        cells = ""
        for c in visible_cols:
            v = getattr(row, c.name, "")
            if v is None:
                v_str = '<span style="color:#cbd5e1">∅</span>'
            elif isinstance(v, bool):
                v_str = "✓" if v else "✗"
            elif isinstance(v, (datetime, date)):
                v_str = v.strftime("%Y-%m-%d %H:%M") if isinstance(v, datetime) else v.isoformat()
            else:
                v_str = str(v)[:60]
            cells += f"<td>{v_str}</td>"
        pk_val = getattr(row, pk_col.name, "")
        cells += (
            f'<td>'
            f'<a href="/admin/{table_name}/{pk_val}/edit" class="btn btn-ghost btn-sm">Edit</a> '
            f'<form method="post" action="/admin/{table_name}/{pk_val}/delete" style="display:inline" '
            f'onsubmit="return confirm(\'Delete this row?\')">'
            f'<button type="submit" class="btn btn-danger btn-sm">Delete</button>'
            f'</form>'
            f'</td>'
        )
        body += f"<tr>{cells}</tr>"

    if not rows and not error:
        body = f'<tr><td colspan="{len(visible_cols)+1}" class="empty-state" style="padding:3rem">No rows yet</td></tr>'

    err_html = f'<div class="alert alert-error">{error}</div>' if error else ""

    content = admin_sidebar_css() + f"""
    {err_html}
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem">
      <div>
        <h2 style="font-size:1.35rem;font-weight:700">{group_icon} {model.__name__}</h2>
        <p style="color:var(--c-muted);font-size:0.85rem">Table: <code>{table_name}</code> · Group: {group_label} · {len(rows)} rows</p>
      </div>
      <a href="/admin/{table_name}/new" class="btn btn-success">+ New {model.__name__}</a>
    </div>
    <table class="data-table">
      <thead><tr>{th}</tr></thead>
      <tbody>{body}</tbody>
    </table>
    """
    breadcrumb = (
        '<a href="/projects" class="crumb-link">Home</a>'
        '<span class="sep">›</span>'
        '<a href="/admin" class="crumb-link">Admin</a>'
        f'<span class="sep">›</span><span class="current">{model.__name__}</span>'
    )
    return HTMLResponse(_render(content, request, breadcrumb=breadcrumb, title=f"{model.__name__} · Admin"))


@router.get("/{table_name}/new", response_class=HTMLResponse)
async def admin_new(table_name: str, request: Request):
    if table_name not in TABLE_REGISTRY:
        return HTMLResponse("Unknown table", status_code=404)
    model, _, _ = TABLE_REGISTRY[table_name]
    return HTMLResponse(_render(_form_page(model, None, table_name), request,
                                breadcrumb=_form_breadcrumb(table_name, model, "New"),
                                title=f"New {model.__name__}"))


@router.post("/{table_name}/create")
async def admin_create(table_name: str, request: Request):
    if table_name not in TABLE_REGISTRY:
        return HTMLResponse("Unknown table", status_code=404)
    model, _, _ = TABLE_REGISTRY[table_name]
    cols = get_columns(model)
    form = await request.form()

    from database import AsyncSessionLocal as async_session_maker
    kwargs: dict[str, Any] = {}
    for c in cols:
        if c.name in form:
            kwargs[c.name] = coerce_value(c, form[c.name])
        elif getattr(c.type, "python_type", str) is bool:
            # Unchecked boolean — defaults to False
            kwargs[c.name] = False

    error = ""
    async with async_session_maker() as db:
        try:
            obj = model(**{k: v for k, v in kwargs.items() if v is not None or c.nullable})
            db.add(obj)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            error = str(e)

    if error:
        content = f'<div class="alert alert-error">{error}</div>' + _form_page(model, None, table_name)
        return HTMLResponse(_render(content, request,
                                    breadcrumb=_form_breadcrumb(table_name, model, "New"),
                                    title=f"New {model.__name__}"), status_code=400)
    return RedirectResponse(url=f"/admin/{table_name}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{table_name}/{row_id}/edit", response_class=HTMLResponse)
async def admin_edit(table_name: str, row_id: str, request: Request):
    if table_name not in TABLE_REGISTRY:
        return HTMLResponse("Unknown table", status_code=404)
    model, _, _ = TABLE_REGISTRY[table_name]
    pk = primary_key_col(model)
    from database import AsyncSessionLocal as async_session_maker
    async with async_session_maker() as db:
        result = await db.execute(select(model).where(pk == row_id))
        row = result.scalar_one_or_none()
    if row is None:
        return HTMLResponse("Row not found", status_code=404)
    return HTMLResponse(_render(_form_page(model, row, table_name), request,
                                breadcrumb=_form_breadcrumb(table_name, model, "Edit"),
                                title=f"Edit {model.__name__}"))


@router.post("/{table_name}/{row_id}/update")
async def admin_update(table_name: str, row_id: str, request: Request):
    if table_name not in TABLE_REGISTRY:
        return HTMLResponse("Unknown table", status_code=404)
    model, _, _ = TABLE_REGISTRY[table_name]
    pk = primary_key_col(model)
    cols = get_columns(model)
    form = await request.form()

    from database import AsyncSessionLocal as async_session_maker
    error = ""
    async with async_session_maker() as db:
        result = await db.execute(select(model).where(pk == row_id))
        row = result.scalar_one_or_none()
        if row is None:
            return HTMLResponse("Row not found", status_code=404)
        try:
            for c in cols:
                if c.name == pk.name:
                    continue
                if c.name in form:
                    setattr(row, c.name, coerce_value(c, form[c.name]))
                elif getattr(c.type, "python_type", str) is bool:
                    setattr(row, c.name, False)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            error = str(e)

    if error:
        return HTMLResponse(f'<div class="alert alert-error">{error}</div>', status_code=400)
    return RedirectResponse(url=f"/admin/{table_name}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{table_name}/{row_id}/delete")
async def admin_delete(table_name: str, row_id: str, request: Request):
    if table_name not in TABLE_REGISTRY:
        return HTMLResponse("Unknown table", status_code=404)
    model, _, _ = TABLE_REGISTRY[table_name]
    pk = primary_key_col(model)
    from database import AsyncSessionLocal as async_session_maker
    async with async_session_maker() as db:
        try:
            await db.execute(sql_delete(model).where(pk == row_id))
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            return HTMLResponse(f"Error: {e}", status_code=400)
    return RedirectResponse(url=f"/admin/{table_name}", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------------------------------------
# Form rendering
# ---------------------------------------------------------------------------
def _form_page(model: type, row: Any, table_name: str) -> str:
    cols = get_columns(model)
    pk_name = primary_key_col(model).name
    action_label = "Update" if row else "Create"
    action_url = f"/admin/{table_name}/{getattr(row, pk_name)}/update" if row else f"/admin/{table_name}/create"

    fields = ""
    for c in cols:
        # Skip auto-generated PKs and timestamps on create
        if not row and c.name == pk_name and c.default is not None:
            continue
        if c.name in ("created_at", "updated_at"):
            continue
        value = getattr(row, c.name, None) if row else None
        required = "" if c.nullable else "<span style='color:#ef4444'>*</span>"
        ctrl = col_input_html(c, value)
        fields += (
            f'<div class="form-group">'
            f'<label>{c.name} {required} '
            f'<span style="font-weight:400;color:var(--c-muted);font-size:0.7rem;text-transform:none">'
            f'{c.type.__class__.__name__.lower()}</span></label>{ctrl}</div>'
        )

    return f"""
    {admin_sidebar_css()}
    <div style="max-width:720px">
      <h2 style="font-size:1.35rem;font-weight:700;margin-bottom:0.25rem">{action_label} {model.__name__}</h2>
      <p style="color:var(--c-muted);font-size:0.85rem;margin-bottom:1.5rem">Table: <code>{table_name}</code></p>
      <form method="post" action="{action_url}" style="background:white;border:1.5px solid var(--c-border);border-radius:0.75rem;padding:1.5rem">
        {fields}
        <div style="display:flex;gap:0.75rem;justify-content:flex-end;margin-top:1rem">
          <a href="/admin/{table_name}" class="btn btn-ghost">Cancel</a>
          <button type="submit" class="btn btn-primary">{action_label}</button>
        </div>
      </form>
    </div>
    """


def _form_breadcrumb(table_name: str, model: type, action: str) -> str:
    return (
        '<a href="/projects" class="crumb-link">Home</a>'
        '<span class="sep">›</span>'
        '<a href="/admin" class="crumb-link">Admin</a>'
        '<span class="sep">›</span>'
        f'<a href="/admin/{table_name}" class="crumb-link">{model.__name__}</a>'
        f'<span class="sep">›</span><span class="current">{action}</span>'
    )
