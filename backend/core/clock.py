"""
Demo Clock — controllable time for testing expiry, alerts, and flows.
Offset is stored in SQLite (core DB) and applied to UTC now.
"""
from datetime import datetime, timedelta, timezone
from .db import get_connection


def get_demo_time() -> datetime:
    """Return current demo time (UTC + offset)."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT offset_minutes FROM demo_clock WHERE id = 1").fetchone()
        offset = row[0] if row else 0
        return datetime.now(timezone.utc) + timedelta(minutes=offset)
    finally:
        conn.close()


def get_offset_minutes() -> int:
    conn = get_connection()
    try:
        row = conn.execute("SELECT offset_minutes FROM demo_clock WHERE id = 1").fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def advance(minutes: int) -> int:
    """Add minutes to offset. Returns new offset."""
    conn = get_connection()
    try:
        current = conn.execute("SELECT offset_minutes FROM demo_clock WHERE id = 1").fetchone()[0]
        new_offset = current + minutes
        conn.execute("UPDATE demo_clock SET offset_minutes = ? WHERE id = 1", (new_offset,))
        conn.commit()
        return new_offset
    finally:
        conn.close()


def reset() -> int:
    """Reset offset to 0. Returns new offset (0)."""
    conn = get_connection()
    try:
        conn.execute("UPDATE demo_clock SET offset_minutes = 0 WHERE id = 1")
        conn.commit()
        return 0
    finally:
        conn.close()