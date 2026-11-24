"""
Forecast Module Database Operations
Importers: backend/modules/forecast/router.py, backend/modules/forecast/service.py
Affected API: GET /forecast/options, POST /forecast/recommend, GET /forecast/metrics
Data schemas: forecast_history, forecast_baselines tables from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from backend.core.db import get_connection
from typing import Optional, List
from datetime import date, datetime


def get_baseline(kitchen_id: str, slot: str) -> int:
    """Get baseline quantity for a kitchen/slot combination."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT quantity FROM forecast_baselines WHERE kitchen_id = ? AND slot = ?",
            (kitchen_id, slot)
        ).fetchone()
        return row["quantity"] if row else 100
    finally:
        conn.close()


def set_baseline(kitchen_id: str, slot: str, quantity: int):
    """Set/update baseline quantity for a kitchen/slot combination."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO forecast_baselines (kitchen_id, slot, quantity)
               VALUES (?, ?, ?)
               ON CONFLICT(kitchen_id, slot) DO UPDATE SET quantity = ?""",
            (kitchen_id, slot, quantity, quantity)
        )
        conn.commit()
    finally:
        conn.close()


def get_history(kitchen_id: str, slot: str, limit: int = 30) -> List[dict]:
    """Get forecast history for a kitchen/slot."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM forecast_history
               WHERE kitchen_id = ? AND slot = ?
               ORDER BY date DESC LIMIT ?""",
            (kitchen_id, slot, limit)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def add_history_entry(kitchen_id: str, slot: str, date_val: str, predicted: int, actual: int):
    """Add a forecast history entry."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO forecast_history (kitchen_id, slot, date, predicted, actual)
               VALUES (?, ?, ?, ?, ?)""",
            (kitchen_id, slot, date_val, predicted, actual)
        )
        conn.commit()
    finally:
        conn.close()


def get_all_kitchens() -> List[dict]:
    """Get all kitchen configurations."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM core_users WHERE role = 'kitchen'").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_slots() -> List[str]:
    """Get available meal slots."""
    return ["lunch", "dinner"]


def get_weather_options() -> List[str]:
    """Get available weather options."""
    return ["clear", "cloudy", "rain", "hot"]


def get_event_options() -> List[str]:
    """Get available event options."""
    return ["none", "exam", "festival", "holiday", "sports"]


def compute_adjustments(weather: str, event: str, target_date: date) -> tuple[float, List[dict]]:
    """Return (total_adjustment_pct, reasons_list)."""
    adjustments = {
        "weather": {"clear": 0, "cloudy": 0, "rain": -6, "hot": 3},
        "event": {"none": 0, "exam": -10, "festival": 15, "holiday": -20, "sports": 5},
    }
    reasons = []
    total = 0

    # Day of week adjustment
    if target_date.weekday() == 5:  # Saturday
        total += -8
        reasons.append({"factor": "weekend", "effect_pct": -8})
    elif target_date.weekday() == 6:  # Sunday
        total += -8
        reasons.append({"factor": "weekend", "effect_pct": -8})

    # Weather
    w = adjustments["weather"].get(weather, 0)
    if w != 0:
        total += w
        reasons.append({"factor": f"weather:{weather}", "effect_pct": w})

    # Event
    e = adjustments["event"].get(event, 0)
    if e != 0:
        total += e
        reasons.append({"factor": f"event:{event}", "effect_pct": e})

    return total, reasons


def compute_mae(kitchen_id: str, slot: str) -> float:
    """Compute Mean Absolute Error for baseline vs actual."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT actual FROM forecast_history WHERE kitchen_id = ? AND slot = ?",
            (kitchen_id, slot)
        ).fetchall()
        if not rows:
            return 0.0

        baseline = get_baseline(kitchen_id, slot)
        errors = [abs(row["actual"] - baseline) for row in rows]
        return sum(errors) / len(errors)
    finally:
        conn.close()