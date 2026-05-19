"""Web routes for AgileAI backlog interface."""

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path
_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agileai.api.dependencies import get_db, create_access_token, get_current_user
from agileai.api.routers.auth import hash_password, verify_password

try:
    from __init__ import User, Issue
except ImportError:
    from agileai.models import User, Issue

router = APIRouter(tags=["web"])

# Simple HTML template
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #f8fafc; color: #334155; }}
        header {{ background: white; border-bottom: 1px solid #e2e8f0; padding: 1rem; }}
        main {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }}
        h1 {{ color: #2563eb; margin-bottom: 1rem; }}
        .header-actions {{ display: flex; gap: 1rem; justify-content: space-between; margin-bottom: 2rem; align-items: center; }}
        .container {{ max-width: 500px; margin: 2rem auto; }}
        form {{ display: flex; flex-direction: column; gap: 1rem; }}
        input, select, textarea {{ padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 0.375rem; font-family: inherit; }}
        button {{ padding: 0.75rem 1.5rem; background: #2563eb; color: white; border: none;
                 border-radius: 0.375rem; font-weight: 500; cursor: pointer; }}
        button:hover {{ background: #1e40af; }}
        button.secondary {{ background: #6b7280; }}
        button.secondary:hover {{ background: #4b5563; }}
        .error {{ background: #fee2e2; color: #991b1b; padding: 0.75rem; border-radius: 0.375rem; }}
        .success {{ background: #dcfce7; color: #166534; padding: 0.75rem; border-radius: 0.375rem; }}
        a {{ color: #2563eb; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .actions {{ display: flex; gap: 1rem; margin: 2rem 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 0.25rem;
                 font-size: 0.75rem; font-weight: 600; background: #dbeafe; color: #1e40af; }}
        .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%;
                 background-color: rgba(0,0,0,0.5); }}
        .modal.show {{ display: block; }}
        .modal-content {{ background-color: #fefefe; margin: 5% auto; padding: 2rem; border-radius: 0.5rem;
                        width: 90%; max-width: 500px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }}
        .modal-header h2 {{ margin: 0; }}
        .close-btn {{ font-size: 2rem; cursor: pointer; }}
        .form-group {{ margin-bottom: 1rem; }}
        .form-group label {{ display: block; margin-bottom: 0.5rem; font-weight: 500; }}
        .score-display {{ padding: 1rem; background: #f1f5f9; border-radius: 0.375rem; margin-top: 1rem; }}
        .spinner {{ display: inline-block; width: 1rem; height: 1rem; border: 2px solid #e2e8f0;
                   border-top-color: #2563eb; border-radius: 50%; animation: spin 0.6s linear infinite; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .draggable {{ cursor: move; }}
        tr.dragging {{ opacity: 0.5; }}
    </style>
</head>
<body>
    <header><h2>AgileAI Backlog Manager</h2></header>
    <main>{content}</main>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Root page with login and register options."""
    content = """
    <h1>AgileAI - Backlog Manager</h1>
    <p>Local-first AI-native Agile project management</p>
    <div class="actions">
        <a href="/login" class="btn">🔐 Login</a>
        <a href="/register" class="btn">📝 Register</a>
    </div>
    <div style="margin-top: 2rem;">
        <p><a href="/docs">📖 API Documentation (Swagger)</a></p>
        <p><a href="/health">💚 Health Check</a></p>
    </div>
    """
    return HTMLResponse(BASE_HTML.format(title="Home - AgileAI", content=content))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    content = """
    <div class="container">
        <h1>Login</h1>
        <form method="post" action="/login">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p style="margin-top: 1rem;">Don't have an account? <a href="/register">Register here</a></p>
    </div>
    """
    return HTMLResponse(BASE_HTML.format(title="Login - AgileAI", content=content))


@router.post("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    email: str = Form(None),
    password: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle login form submission."""
    from sqlalchemy import select

    if not email or not password:
        error = '<div class="error">Email and password required</div>'
        content = f"""
        <div class="container">
            <h1>Login</h1>
            {error}
            <form method="post" action="/login">
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
        """
        return HTMLResponse(BASE_HTML.format(title="Login - AgileAI", content=content), status_code=400)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        error = '<div class="error">Invalid email or password</div>'
        content = f"""
        <div class="container">
            <h1>Login</h1>
            {error}
            <form method="post" action="/login">
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
        """
        return HTMLResponse(BASE_HTML.format(title="Login - AgileAI", content=content), status_code=401)

    token = create_access_token(user_id=user.id)
    response = RedirectResponse(url="/backlog/proj-1", status_code=302)
    response.set_cookie("auth_token", token, httponly=True, max_age=86400)
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page."""
    content = """
    <div class="container">
        <h1>Register</h1>
        <form method="post" action="/register">
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Register</button>
        </form>
        <p style="margin-top: 1rem;">Already have an account? <a href="/login">Login here</a></p>
    </div>
    """
    return HTMLResponse(BASE_HTML.format(title="Register - AgileAI", content=content))


@router.post("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle registration form submission."""
    from sqlalchemy import select

    if not all([email, password, name]):
        error = '<div class="error">All fields required</div>'
        content = f"""
        <div class="container">
            <h1>Register</h1>
            {error}
            <form method="post" action="/register">
                <input type="text" name="name" placeholder="Full Name" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Register</button>
            </form>
        </div>
        """
        return HTMLResponse(BASE_HTML.format(title="Register - AgileAI", content=content), status_code=400)

    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        error = '<div class="error">Email already registered</div>'
        content = f"""
        <div class="container">
            <h1>Register</h1>
            {error}
            <form method="post" action="/register">
                <input type="text" name="name" placeholder="Full Name" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Register</button>
            </form>
        </div>
        """
        return HTMLResponse(BASE_HTML.format(title="Register - AgileAI", content=content), status_code=400)

    username = email.split("@")[0]
    user = User(email=email, username=username, password_hash=hash_password(password), name=name)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user_id=user.id)
    response = RedirectResponse(url="/backlog/proj-1", status_code=302)
    response.set_cookie("auth_token", token, httponly=True, max_age=86400)
    return response


@router.get("/backlog/{project_id}", response_class=HTMLResponse)
async def backlog_view(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Display backlog for a project."""
    from sqlalchemy import select
    from agileai.services.backlog import BacklogService

    # Check if user is authenticated via cookie
    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        return RedirectResponse(url="/login", status_code=302)

    svc = BacklogService(db)
    try:
        issues = await svc.get_backlog(project_id, include_scores=False)
    except Exception:
        issues = []

    issues_html = ""
    if issues:
        for issue in issues:
            status = getattr(issue, "status", "todo")
            issue_type = getattr(issue, "type", "story")
            title = getattr(issue, "title", "Untitled")
            issue_id = getattr(issue, "id", "")
            points = getattr(issue, "story_points", "-")
            sprint_id = getattr(issue, "sprint_id", None)
            issues_html += f"""
            <tr class="draggable" draggable="true" data-issue-id="{issue_id}">
                <td style="text-align: center; cursor: move; user-select: none;">⋮</td>
                <td>{issue_id}</td>
                <td>{title}</td>
                <td><span class="badge">{status}</span></td>
                <td>{issue_type}</td>
                <td>{points}</td>
                <td style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    <button hx-get="/backlog/{project_id}/estimate?issue_id={issue_id}"
                            hx-target="#modal-content"
                            class="secondary"
                            style="padding: 0.35rem 0.75rem; font-size: 0.875rem;">
                        Est
                    </button>
                    {'' if sprint_id else f'<button hx-get="/backlog/{project_id}/sprint-select?issue_id={issue_id}" hx-target="#modal-content" class="secondary" style="padding: 0.35rem 0.75rem; font-size: 0.875rem;">+Sprint</button>'}
                </td>
            </tr>
            """
    else:
        issues_html = '<tr><td colspan="7" style="text-align:center; color: #999;">No issues in backlog</td></tr>'

    content = f"""
    <div class="header-actions">
        <div>
            <h1>Backlog: {project_id}</h1>
        </div>
        <div style="display: flex; gap: 1rem;">
            <a href="/backlog/{project_id}/prioritize" style="padding: 0.5rem 1rem; background: #3b82f6; color: white; border-radius: 0.375rem;">📊 Prioritized View</a>
            <a href="/logout" style="color: #dc2626;">🚪 Logout</a>
        </div>
    </div>
    <table>
        <thead>
            <tr>
                <th style="width: 40px;">⋮</th>
                <th>ID</th>
                <th>Title</th>
                <th>Status</th>
                <th>Type</th>
                <th>Points</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody id="backlog-table">
            {issues_html}
        </tbody>
    </table>

    <div id="modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modal-title">Form</h2>
                <span class="close-btn" onclick="document.getElementById('modal').classList.remove('show')">&times;</span>
            </div>
            <div id="modal-content"></div>
        </div>
    </div>

    <script>
        document.getElementById('modal').addEventListener('htmx:load', function() {{
            document.getElementById('modal').classList.add('show');
        }});

        // Drag and drop for reordering
        let draggedRow = null;
        const backlogTable = document.getElementById('backlog-table');

        if (backlogTable) {{
            const rows = backlogTable.querySelectorAll('tr.draggable');

            rows.forEach(row => {{
                row.addEventListener('dragstart', (e) => {{
                    draggedRow = row;
                    row.classList.add('dragging');
                    e.dataTransfer.effectAllowed = 'move';
                }});

                row.addEventListener('dragend', () => {{
                    row.classList.remove('dragging');
                    draggedRow = null;
                }});

                row.addEventListener('dragover', (e) => {{
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                    if (row !== draggedRow) {{
                        row.style.borderTop = '2px solid #2563eb';
                    }}
                }});

                row.addEventListener('dragleave', () => {{
                    row.style.borderTop = '';
                }});

                row.addEventListener('drop', async (e) => {{
                    e.preventDefault();
                    row.style.borderTop = '';

                    if (row !== draggedRow && draggedRow) {{
                        // Reorder: move draggedRow before row
                        backlogTable.insertBefore(draggedRow, row);

                        // Send reorder request
                        const issueIds = Array.from(backlogTable.querySelectorAll('tr.draggable'))
                            .map(r => r.dataset.issueId);

                        await fetch('/backlog/{project_id}/bulk-reorder', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                project_id: '{project_id}',
                                ordered_ids: issueIds
                            }})
                        }});
                    }}
                }});
            }});
        }}
    </script>
    """
    return HTMLResponse(BASE_HTML.format(title="Backlog - AgileAI", content=content))


@router.get("/backlog/{project_id}/estimate", response_class=HTMLResponse)
async def estimate_form(
    project_id: str,
    issue_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show estimation form for an issue."""
    content = f"""
    <form hx-post="/backlog/{project_id}/estimate"
          hx-target="#modal-content"
          style="display: flex; flex-direction: column; gap: 1rem;">
        <input type="hidden" name="issue_id" value="{issue_id}">

        <div class="form-group">
            <label for="story_points">Story Points:</label>
            <select name="story_points" id="story_points" required>
                <option value="">Select points...</option>
                <option value="1">1 - Trivial</option>
                <option value="2">2 - Very Small</option>
                <option value="3">3 - Small</option>
                <option value="5">5 - Medium</option>
                <option value="8">8 - Large</option>
                <option value="13">13 - Very Large</option>
                <option value="21">21 - Huge</option>
            </select>
        </div>

        <div class="form-group">
            <label for="rationale">Rationale:</label>
            <textarea name="rationale" id="rationale" rows="4" placeholder="Why this estimate?" required></textarea>
        </div>

        <div style="display: flex; gap: 1rem;">
            <button type="submit">Save Estimate</button>
            <button type="button" class="secondary" onclick="document.getElementById('modal').classList.remove('show')">Cancel</button>
        </div>
    </form>
    """
    return HTMLResponse(content)


@router.post("/backlog/{project_id}/estimate", response_class=HTMLResponse)
async def save_estimate(
    project_id: str,
    issue_id: str = Form(...),
    story_points: int = Form(...),
    rationale: str = Form(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Save estimation for an issue."""
    from sqlalchemy import update

    try:
        stmt = update(Issue).where(Issue.id == issue_id).values(
            story_points=story_points
        )
        await db.execute(stmt)
        await db.commit()

        return HTMLResponse(
            '<div class="success">✓ Estimate saved successfully!</div>',
            status_code=200
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="error">✗ Error saving estimate: {str(e)}</div>',
            status_code=400
        )


@router.get("/backlog/{project_id}/prioritize", response_class=HTMLResponse)
async def prioritize_view(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Display prioritized backlog view."""
    from agileai.services.backlog import BacklogService

    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        return RedirectResponse(url="/login", status_code=302)

    svc = BacklogService(db)
    try:
        ranked = await svc.prioritize_backlog(project_id)
    except Exception:
        ranked = []

    issues_html = ""
    if ranked:
        for i, issue in enumerate(ranked, 1):
            score = getattr(issue, "_priority_score", None)
            score_val = score.score if score else 0
            title = getattr(issue, "title", "Untitled")
            issue_id = getattr(issue, "id", "")
            issues_html += f"""
            <tr>
                <td>{i}</td>
                <td>{issue_id}</td>
                <td>{title}</td>
                <td style="text-align: right;">{score_val:.1f}</td>
            </tr>
            """
    else:
        issues_html = '<tr><td colspan="4" style="text-align:center; color: #999;">No ranked issues</td></tr>'

    content = f"""
    <div class="header-actions">
        <div>
            <h1>Prioritized Backlog: {project_id}</h1>
        </div>
        <div style="display: flex; gap: 1rem;">
            <a href="/backlog/{project_id}" style="padding: 0.5rem 1rem; background: #3b82f6; color: white; border-radius: 0.375rem;">📋 Back to Backlog</a>
            <a href="/logout" style="color: #dc2626;">🚪 Logout</a>
        </div>
    </div>
    <table>
        <thead>
            <tr>
                <th>Rank</th>
                <th>ID</th>
                <th>Title</th>
                <th>Score</th>
            </tr>
        </thead>
        <tbody>
            {issues_html}
        </tbody>
    </table>
    """
    return HTMLResponse(BASE_HTML.format(title="Prioritized Backlog - AgileAI", content=content))


@router.post("/backlog/{project_id}/bulk-reorder")
async def bulk_reorder(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Bulk reorder backlog issues."""
    from sqlalchemy import update

    try:
        body = await request.json()
        ordered_ids = body.get("ordered_ids", [])

        for order, issue_id in enumerate(ordered_ids):
            stmt = update(Issue).where(Issue.id == issue_id).values(
                backlog_order=order
            )
            await db.execute(stmt)

        await db.commit()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}, 400


@router.get("/backlog/{project_id}/sprint-select", response_class=HTMLResponse)
async def sprint_select_form(
    project_id: str,
    issue_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Show sprint selection form."""
    from sqlalchemy import select

    try:
        # Get available sprints for this project
        # For now, just return a simple form with common sprint names
        sprint_options = """
        <option value="">Select a sprint...</option>
        <option value="sprint-1">Sprint 1</option>
        <option value="sprint-2">Sprint 2</option>
        <option value="sprint-3">Sprint 3</option>
        """

        content = f"""
        <form hx-post="/backlog/{project_id}/add-to-sprint"
              hx-target="#modal-content"
              style="display: flex; flex-direction: column; gap: 1rem;">
            <input type="hidden" name="issue_id" value="{issue_id}">

            <div class="form-group">
                <label for="sprint_id">Sprint:</label>
                <select name="sprint_id" id="sprint_id" required>
                    {sprint_options}
                </select>
            </div>

            <div style="display: flex; gap: 1rem;">
                <button type="submit">Add to Sprint</button>
                <button type="button" class="secondary" onclick="document.getElementById('modal').classList.remove('show')">Cancel</button>
            </div>
        </form>
        """
        return HTMLResponse(content)
    except Exception as e:
        return HTMLResponse(f'<div class="error">Error: {str(e)}</div>', status_code=400)


@router.post("/backlog/{project_id}/add-to-sprint", response_class=HTMLResponse)
async def add_to_sprint(
    project_id: str,
    issue_id: str = Form(...),
    sprint_id: str = Form(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Add issue to sprint."""
    from sqlalchemy import update

    try:
        stmt = update(Issue).where(Issue.id == issue_id).values(
            sprint_id=sprint_id
        )
        await db.execute(stmt)
        await db.commit()

        return HTMLResponse(
            f'<div class="success">✓ Issue added to {sprint_id}! <a href="/backlog/{project_id}" hx-boost="true">Reload</a></div>',
            status_code=200
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="error">✗ Error: {str(e)}</div>',
            status_code=400
        )


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    """Logout and clear cookie."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("auth_token")
    return response
