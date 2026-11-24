"""
User management for AnnaSetu AI.
Seeded personas for kitchens, processing units, NGOs, and mandirs.
"""
from typing import Optional
from .db import get_connection


def get_user(user_id: str) -> Optional[dict]:
    """Get a single user by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM core_users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_users(role: Optional[str] = None) -> list[dict]:
    """Get all users, optionally filtered by role."""
    conn = get_connection()
    try:
        if role:
            rows = conn.execute("SELECT * FROM core_users WHERE role = ?", (role,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM core_users").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_kitchens() -> list[dict]:
    """Get all kitchen/processing unit users."""
    return get_users("kitchen") + get_users("processing_unit")


def get_recipients() -> list[dict]:
    """Get all NGO and mandir users."""
    return get_users("ngo") + get_users("mandir")


def get_users_for_frontend() -> list[dict]:
    """Get users formatted for frontend demo user switcher."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM core_users ORDER BY role, name").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()