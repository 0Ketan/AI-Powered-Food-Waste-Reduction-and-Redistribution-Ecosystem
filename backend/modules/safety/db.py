"""
Safety Module Database Operations
Importers: backend/modules/safety/router.py, backend/modules/safety/service.py
Affected API: GET /api/safety/categories, POST /api/safety/evaluate, GET /api/safety/label/{label_id}/print, GET /api/safety/records, GET /api/safety/disposals, POST /api/safety/records/{record_id}/complete
Data schemas: safety_records, safety_disposals tables from core/db.py; CATEGORIES list with hold_hours
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from backend.core.db import get_connection
from backend.core.clock import get_demo_time
from typing import Optional, List
from datetime import datetime, timedelta


# Safety categories with placeholder hold hours
CATEGORIES = [
    {"id": "cooked_rice", "name": "Cooked Rice", "hold_hours": 2, "risk": "high"},
    {"id": "cooked_dal", "name": "Cooked Dal", "hold_hours": 4, "risk": "medium"},
    {"id": "cooked_veg", "name": "Cooked Vegetables", "hold_hours": 4, "risk": "medium"},
    {"id": "bread", "name": "Bread/Chapati", "hold_hours": 8, "risk": "low"},
    {"id": "fruit", "name": "Cut Fruit", "hold_hours": 2, "risk": "high"},
    {"id": "salad", "name": "Raw Salad", "hold_hours": 2, "risk": "high"},
    {"id": "dairy", "name": "Dairy Items", "hold_hours": 2, "risk": "high"},
    {"id": "packaged", "name": "Packaged Snacks", "hold_hours": 24, "risk": "low"},
]


def get_categories() -> List[dict]:
    """Get all safety categories with hold hours."""
    return CATEGORIES


def get_category(category_id: str) -> Optional[dict]:
    """Get a single category by ID."""
    for cat in CATEGORIES:
        if cat["id"] == category_id:
            return cat
    return None


def evaluate_safety(donor_id: str, item_name: str, category_id: str, veg: bool,
                    quantity: float, unit: str, storage: str, prepared_at: str,
                    kitchen_confirms_safe: bool, pickup_buffer_minutes: int):
    """Evaluate food safety and return decision with label/record IDs."""
    from uuid import uuid4

    category = get_category(category_id)
    if not category:
        return {
            "decision": "reject",
            "reason": f"Unknown category: {category_id}",
            "consume_by": None,
            "label_id": None,
            "record_id": None,
            "disposal_id": None,
        }

    # Parse prepared time
    try:
        prepared_dt = datetime.fromisoformat(prepared_at.replace("Z", "+00:00"))
    except:
        prepared_dt = get_demo_time()

    hold_hours = category["hold_hours"]
    consume_by_dt = prepared_dt + timedelta(hours=hold_hours)
    now = get_demo_time()

    # Check if already expired
    if now >= consume_by_dt:
        return {
            "decision": "reject",
            "reason": f"Already past safe window ({hold_hours}h from preparation)",
            "consume_by": consume_by_dt.isoformat(),
            "label_id": None,
            "record_id": None,
            "disposal_id": None,
        }

    # Check buffer time
    pickup_ready = now + timedelta(minutes=pickup_buffer_minutes)
    if pickup_ready > consume_by_dt:
        return {
            "decision": "reject",
            "reason": f"Insufficient time for pickup before expiry (need {pickup_buffer_minutes}min buffer)",
            "consume_by": consume_by_dt.isoformat(),
            "label_id": None,
            "record_id": None,
            "disposal_id": None,
        }

    if not kitchen_confirms_safe:
        return {
            "decision": "reject",
            "reason": "Kitchen did not confirm safe handling",
            "consume_by": consume_by_dt.isoformat(),
            "label_id": None,
            "record_id": None,
            "disposal_id": None,
        }

    # Approved - create record
    record_id = f"rec_{uuid4().hex[:8]}"
    label_id = f"lbl_{uuid4().hex[:8]}"

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO safety_records (record_id, donor_id, donor_name, item_name, batch_no,
               mfg_date, donation_date, expiry_or_consume_by, quantity_donated, unit, food_temperature_note,
               quantity_distributed, distribution_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record_id, donor_id, "Demo Kitchen", item_name, f"BATCH-{uuid4().hex[:6].upper()}",
             prepared_dt.date().isoformat(), now.date().isoformat(), consume_by_dt.isoformat(), quantity, unit,
             storage, 0, None)
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "decision": "approve",
        "reason": f"Safe for donation. Must be consumed by {consume_by_dt.isoformat()}",
        "consume_by": consume_by_dt.isoformat(),
        "label_id": label_id,
        "record_id": record_id,
        "disposal_id": None,
    }


def create_disposal(donor_id: str, item_name: str, quantity: float, unit: str, route: str, reason: str):
    """Create a disposal record. Returns string disposal ID."""
    from uuid import uuid4
    disposal_id = f"disp_{uuid4().hex[:8]}"
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO safety_disposals (donor_id, item_name, quantity, unit, route, reason)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (donor_id, item_name, quantity, unit, route, reason)
        )
        conn.commit()
        return disposal_id
    finally:
        conn.close()


def get_records(donor_id: Optional[str] = None) -> List[dict]:
    """Get safety records."""
    conn = get_connection()
    try:
        if donor_id:
            rows = conn.execute(
                "SELECT * FROM safety_records WHERE donor_id = ? ORDER BY created_at DESC",
                (donor_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM safety_records ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_disposals(donor_id: Optional[str] = None) -> List[dict]:
    """Get disposal records."""
    conn = get_connection()
    try:
        if donor_id:
            rows = conn.execute(
                "SELECT * FROM safety_disposals WHERE donor_id = ? ORDER BY created_at DESC",
                (donor_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM safety_disposals ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def complete_record(record_id: str):
    """Mark a safety record as distributed."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE safety_records SET quantity_distributed = quantity_donated,
               distribution_date = ? WHERE record_id = ?""",
            (get_demo_time().isoformat(), record_id)
        )
        conn.commit()
    finally:
        conn.close()