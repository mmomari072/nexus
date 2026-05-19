"""Web routes for AgileAI backlog interface."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path
_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agileai.api.dependencies import get_db, create_access_token, get_current_user
from agileai.api.routers.auth import hash_password, verify_password
from agileai.services.backlog import BacklogService

try:
    from __init__ import User
except ImportError:
    from agileai.models import User

router = APIRouter(tags=["web"])

# Configure Jinja2 templates
template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Root page - redirect to login or backlog."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    email: str = None,
    password: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle login form submission."""
    from sqlalchemy import select

    if not email or not password:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Email and password required"},
            status_code=400,
        )

    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid email or password"},
            status_code=401,
        )

    # Create token and redirect
    token = create_access_token(user_id=user.id)
    response = RedirectResponse(url="/backlog/proj-1", status_code=302)
    response.set_cookie("auth_token", token, httponly=True, max_age=86400)
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page."""
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    email: str = None,
    password: str = None,
    name: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle registration form submission."""
    from sqlalchemy import select

    if not all([email, password, name]):
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "All fields required"},
            status_code=400,
        )

    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Email already registered"},
            status_code=400,
        )

    # Create user
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Log them in
    token = create_access_token(user_id=user.id)
    response = RedirectResponse(url="/backlog/proj-1", status_code=302)
    response.set_cookie("auth_token", token, httponly=True, max_age=86400)
    return response


def get_token_from_cookie(request: Request) -> Optional[str]:
    """Extract JWT token from cookie."""
    return request.cookies.get("auth_token")


async def get_current_user_from_cookie(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Optional[dict]:
    """Get current user from cookie token."""
    token = get_token_from_cookie(request)
    if not token:
        return None

    from jose import jwt
    from agileai.api.dependencies import SECRET_KEY, ALGORITHM
    from sqlalchemy import select

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                return {"user_id": user_id, "user": user}
    except Exception:
        pass
    return None


@router.get("/backlog/{project_id}", response_class=HTMLResponse)
async def backlog_view(
    request: Request,
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Main backlog view."""
    user_info = await get_current_user_from_cookie(request, db)
    if not user_info:
        return RedirectResponse(url="/login", status_code=302)

    svc = BacklogService(db)
    backlog = await svc.get_backlog(project_id)

    return templates.TemplateResponse(
        "backlog/list.html",
        {
            "request": request,
            "project_id": project_id,
            "issues": backlog,
            "user": user_info["user"],
        },
    )


@router.get("/backlog/{project_id}/estimate", response_class=HTMLResponse)
async def estimate_modal(
    request: Request,
    project_id: str,
    issue_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get estimation form modal (HTMX)."""
    from sqlalchemy import select

    user_info = await get_current_user_from_cookie(request, db)
    if not user_info:
        return HTMLResponse("Unauthorized", status_code=401)

    result = await db.execute(
        select(lambda: None).from_statement(
            f"SELECT * FROM issues WHERE id = '{issue_id}' AND project_id = '{project_id}'"
        )
    )

    return templates.TemplateResponse(
        "backlog/estimate_modal.html",
        {
            "request": request,
            "project_id": project_id,
            "issue_id": issue_id,
        },
    )


@router.post("/backlog/{project_id}/estimate", response_class=HTMLResponse)
async def submit_estimate(
    request: Request,
    project_id: str,
    issue_id: str,
    difficulty: str,
    importance: str,
    db: AsyncSession = Depends(get_db),
):
    """Submit estimation (HTMX)."""
    user_info = await get_current_user_from_cookie(request, db)
    if not user_info:
        return HTMLResponse("Unauthorized", status_code=401)

    svc = BacklogService(db)
    result = await svc.request_estimate(issue_id)

    # Return updated issue row
    from sqlalchemy import select

    issue_result = await db.execute(
        select(lambda: None).from_statement(
            f"SELECT * FROM issues WHERE id = '{issue_id}'"
        )
    )

    return templates.TemplateResponse(
        "backlog/issue_row.html",
        {
            "request": request,
            "issue": None,  # TODO: fetch actual issue
            "story_points": result.suggested_points,
        },
    )


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    """Logout and clear cookie."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("auth_token")
    return response
