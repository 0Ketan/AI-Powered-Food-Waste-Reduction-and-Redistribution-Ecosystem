"""
Core Module Router - Health, Clock, Users
Importers: backend/app.py
Affected API: GET /api/users, GET /health, GET /api/demo/clock
Data schemas: User from core_users table
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from fastapi import APIRouter
from .users import get_users_for_frontend, get_users, get_kitchens, get_recipients

router = APIRouter(prefix="/api", tags=["core"])


@router.get("/users")
def list_users():
    """List all users (kitchens, NGOs, mandirs)."""
    users = get_users_for_frontend()
    return {"users": users}


@router.get("/users/kitchens")
def list_kitchens():
    """List all kitchens and processing units."""
    kitchens = get_kitchens()
    return {"kitchens": kitchens}


@router.get("/users/recipients")
def list_recipients():
    """List all NGOs and mandirs."""
    recipients = get_recipients()
    return {"recipients": recipients}