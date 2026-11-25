"""
Waste Module Database Operations
Importers: backend/modules/waste/router.py, backend/modules/waste/service.py
Affected API: POST /api/waste/log, GET /api/waste/logs, GET /api/waste/summary
Data schemas: waste_logs table from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from backend.core.db import get_connection
from typing import Optional


def insert_log(kitchen_id: str, date: str, slot: str, prepared: int, served: int, leftover: int, ran_short: bool, plate_waste: int = 0):
    """Insert a waste log entry."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO waste_logs (kitchen_id, date, slot, prepared, served, leftover, ran_short, plate_waste)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (kitchen_id, date, slot, prepared, served, leftover, 1 if ran_short else 0, plate_waste)
        )
        conn.commit()
    finally:
        conn.close()


def get_logs(kitchen_id: Optional[str] = None, limit: int = 50):
    """Get waste logs, optionally filtered by kitchen."""
    conn = get_connection()
    try:
        if kitchen_id:
            rows = conn.execute(
                "SELECT * FROM waste_logs WHERE kitchen_id = ? ORDER BY date DESC, id DESC LIMIT ?",
                (kitchen_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM waste_logs ORDER BY date DESC, id DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_summary(kitchen_id: Optional[str] = None):
    """Get aggregate summary statistics."""
    conn = get_connection()
    try:
        if kitchen_id:
            daily_rows = conn.execute(
                """SELECT date, SUM(prepared) as prepared, SUM(served) as served,
                          SUM(leftover) as leftover, SUM(CASE WHEN ran_short THEN 1 ELSE 0 END) as shortage_count
                   FROM waste_logs WHERE kitchen_id = ? GROUP BY date ORDER BY date""",
                (kitchen_id,)
            ).fetchall()

            total_row = conn.execute(
                """SELECT SUM(prepared) as prepared, SUM(served) as served,
                          SUM(leftover) as leftover, SUM(CASE WHEN ran_short THEN 1 ELSE 0 END) as shortage_count
                   FROM waste_logs WHERE kitchen_id = ?""",
                (kitchen_id,)
            ).fetchone()

            slot_rows = conn.execute(
                """SELECT slot, AVG(leftover) as avg_leftover
                   FROM waste_logs WHERE kitchen_id = ? GROUP BY slot""",
                (kitchen_id,)
            ).fetchall()
        else:
            daily_rows = conn.execute(
                """SELECT date, SUM(prepared) as prepared, SUM(served) as served,
                          SUM(leftover) as leftover, SUM(CASE WHEN ran_short THEN 1 ELSE 0 END) as shortage_count
                   FROM waste_logs GROUP BY date ORDER BY date"""
            ).fetchall()
            total_row = conn.execute(
                """SELECT SUM(prepared) as prepared, SUM(served) as served,
                          SUM(leftover) as leftover, SUM(CASE WHEN ran_short THEN 1 ELSE 0 END) as shortage_count
                   FROM waste_logs"""
            ).fetchone()
            slot_rows = conn.execute(
                """SELECT slot, AVG(leftover) as avg_leftover
                   FROM waste_logs GROUP BY slot"""
            ).fetchall()

        days = [dict(row) for row in daily_rows]
        totals = dict(total_row) if total_row else {"prepared": 0, "served": 0, "leftover": 0, "shortage_count": 0}
        # Handle NULL values from SUM() when no rows exist
        prepared = totals.get("prepared", 0) or 0
        served = totals.get("served", 0) or 0
        leftover = totals.get("leftover", 0) or 0
        shortage_count = totals.get("shortage_count", 0) or 0
        totals["prepared"] = prepared
        totals["served"] = served
        totals["leftover"] = leftover
        totals["shortage_count"] = shortage_count
        totals["leftover_pct"] = round((leftover / prepared * 100) if prepared > 0 else 0, 1)
        by_slot = [{"slot": row["slot"], "avg_leftover": round(row["avg_leftover"], 1)} for row in slot_rows]

        return {
            "unit": "plates",
            "days": days,
            "totals": totals,
            "by_slot": by_slot,
            "shortage_count": totals["shortage_count"],
            "total_kg": float(totals.get("leftover", 0)),
            "by_category": {"cooked_rice": totals.get("leftover", 0)},
            "by_reason": {"overproduction": totals.get("leftover", 0)},
            "by_disposal": {"donation": totals.get("leftover", 0)}
        }
    finally:
        conn.close()