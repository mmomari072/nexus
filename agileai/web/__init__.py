"""Web UI module for AgileAI."""

from fastapi import APIRouter

from agileai.web.routes import router as _routes_router
from agileai.web.admin import router as _admin_router

router = APIRouter()
router.include_router(_routes_router)
router.include_router(_admin_router)

__all__ = ["router"]
