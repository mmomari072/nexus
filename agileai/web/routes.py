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
    from __init__ import User
except ImportError:
    from agileai.models import User

router = APIRouter(tags=["web"])

# Simple HTML template
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #f8fafc; color: #334155; }}
        header {{ background: white; border-bottom: 1px solid #e2e8f0; padding: 1rem; }}
        main {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }}
        h1 {{ color: #2563eb; margin-bottom: 1rem; }}
        .container {{ max-width: 500px; margin: 2rem auto; }}
        form {{ display: flex; flex-direction: column; gap: 1rem; }}
        input {{ padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 0.375rem; }}
        button {{ padding: 0.75rem 1.5rem; background: #2563eb; color: white; border: none;
                 border-radius: 0.375rem; font-weight: 500; cursor: pointer; }}
        button:hover {{ background: #1e40af; }}
        .error {{ background: #fee2e2; color: #991b1b; padding: 0.75rem; border-radius: 0.375rem; }}
        a {{ color: #2563eb; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .actions {{ display: flex; gap: 1rem; margin: 2rem 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 0.25rem;
                 font-size: 0.75rem; font-weight: 600; background: #dbeafe; color: #1e40af; }}
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
            issues_html += f"""
            <tr>
                <td>{issue_id}</td>
                <td>{title}</td>
                <td><span class="badge">{status}</span></td>
                <td>{issue_type}</td>
                <td>
                    <a href="/backlog/{project_id}/estimate?issue_id={issue_id}">Estimate</a>
                </td>
            </tr>
            """
    else:
        issues_html = '<tr><td colspan="5" style="text-align:center; color: #999;">No issues in backlog</td></tr>'

    content = f"""
    <div style="margin-bottom: 2rem;">
        <h1>Backlog: {project_id}</h1>
        <a href="/logout" style="color: #dc2626;">Logout</a>
    </div>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Status</th>
                <th>Type</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {issues_html}
        </tbody>
    </table>
    """
    return HTMLResponse(BASE_HTML.format(title="Backlog - AgileAI", content=content))


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    """Logout and clear cookie."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("auth_token")
    return response
