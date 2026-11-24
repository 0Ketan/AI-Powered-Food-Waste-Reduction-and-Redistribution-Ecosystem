"""
Marketplace Module Database Operations
Importers: backend/modules/marketplace/router.py, backend/modules/marketplace/service.py
Affected API: All marketplace endpoints (listings, nearby, claim, pickup, served, needs, pledges, alerts, impact)
Data schemas: mkt_listings, mkt_claims, mkt_alerts, mkt_needs, mkt_pledges tables from core/db.py; haversine for distance
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from backend.core.db import get_connection
from backend.core.clock import get_demo_time
from backend.core.users import get_user
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import uuid4
import math
from fastapi import HTTPException


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two lat/lng points."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def create_listing(donor_id: str, item_name: str, category_id: str, veg: bool,
                   quantity: float, unit: str, storage: str, consume_by: str,
                   label_id: Optional[str] = None, record_id: Optional[str] = None):
    """Create a marketplace listing."""
    donor = get_user(donor_id)
    if not donor:
        raise ValueError("Donor not found")

    listing_id = f"lst_{uuid4().hex[:8]}"
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO mkt_listings (id, donor_id, donor_name, item_name, category_id, veg,
               quantity, unit, storage, consume_by, label_id, record_id, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')""",
            (listing_id, donor_id, donor["name"], item_name, category_id,
             1 if veg else 0, quantity, unit, storage, consume_by, label_id, record_id)
        )

        # Create alerts for nearby recipients
        recipients = [u for u in get_connection().execute("SELECT * FROM core_users WHERE role IN ('ngo', 'mandir')").fetchall()]
        for rec in recipients:
            dist = haversine(donor["lat"], donor["lng"], rec["lat"], rec["lng"])
            if dist <= 10:  # 10km radius
                conn.execute(
                    """INSERT INTO mkt_alerts (user_id, type, message)
                       VALUES (?, 'new_listing', ?)""",
                    (rec["id"], f"New listing nearby: {item_name} ({quantity} {unit})")
                )
        conn.commit()
        return listing_id
    finally:
        conn.close()


def get_listings(donor_id: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
    """Get marketplace listings."""
    conn = get_connection()
    try:
        query = "SELECT * FROM mkt_listings WHERE 1=1"
        params = []
        if donor_id:
            query += " AND donor_id = ?"
            params.append(donor_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_listing(listing_id: str) -> Optional[dict]:
    """Get a single listing by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM mkt_listings WHERE id = ?", (listing_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_nearby_listings(recipient_id: str, max_km: float = 10.0) -> List[dict]:
    """Get nearby open listings for a recipient with distance and time calculations."""
    recipient = get_user(recipient_id)
    if not recipient:
        return []

    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM mkt_listings WHERE status = 'open' ORDER BY created_at DESC"
        ).fetchall()

        results = []
        for row in rows:
            donor = get_user(row["donor_id"])
            if not donor:
                continue
            dist = haversine(recipient["lat"], recipient["lng"], donor["lat"], donor["lng"])
            if dist > max_km:
                continue

            # Calculate minutes left until expiry
            consume_by = datetime.fromisoformat(row["consume_by"].replace("Z", "+00:00"))
            now = get_demo_time()
            minutes_left = int((consume_by - now).total_seconds() / 60)

            # Estimate travel time (walking ~5 km/h = 12 min/km)
            travel_minutes = int(dist * 12)

            # Simple score: higher for closer, more time left, veg match
            # Hard filter: veg_only recipients never see non-veg listings
            if recipient.get("veg_only") and not row["veg"]:
                continue  # Skip non-veg listings for veg-only recipients
            score = 0
            score += (60 - travel_minutes) * 2
            score += max(0, minutes_left) // 10
            score -= dist * 5

            results.append({
                **dict(row),
                "distance_km": round(dist, 1),
                "minutes_left": minutes_left,
                "travel_minutes": travel_minutes,
                "score": score,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    finally:
        conn.close()


def claim_listing(listing_id: str, recipient_id: str):
    """Claim a listing - generates 4-digit pickup code."""
    import random
    pickup_code = f"{random.randint(1000, 9999)}"

    conn = get_connection()
    try:
        listing = conn.execute("SELECT * FROM mkt_listings WHERE id = ?", (listing_id,)).fetchone()
        if not listing:
            raise HTTPException(404, "Listing not found")
        if listing["status"] != "open":
            raise HTTPException(409, "Listing already claimed or expired")

        conn.execute(
            """INSERT INTO mkt_claims (listing_id, recipient_id, pickup_code)
               VALUES (?, ?, ?)""",
            (listing_id, recipient_id, pickup_code)
        )
        conn.execute("UPDATE mkt_listings SET status = 'claimed', claimed_by = ? WHERE id = ?",
                     (recipient_id, listing_id))

        # Alert donor
        conn.execute(
            """INSERT INTO mkt_alerts (user_id, type, message)
               VALUES (?, 'claimed', ?)""",
            (listing["donor_id"], f"Your listing '{listing['item_name']}' was claimed")
        )
        conn.commit()
        return {"pickup_code": pickup_code, "listing": dict(listing)}
    finally:
        conn.close()


def pickup_listing(listing_id: str, donor_id: str, code: str):
    """Verify pickup code and mark as collected."""
    conn = get_connection()
    try:
        claim = conn.execute(
            "SELECT * FROM mkt_claims WHERE listing_id = ?", (listing_id,)
        ).fetchone()
        if not claim:
            raise HTTPException(404, "No claim found")
        if claim["pickup_code"] != code:
            raise HTTPException(400, "Invalid pickup code")

        # Verify donor owns the listing (not in claims table - check listing)
        listing = conn.execute("SELECT * FROM mkt_listings WHERE id = ?", (listing_id,)).fetchone()
        if not listing:
            raise HTTPException(404, "Listing not found")
        if listing["donor_id"] != donor_id:
            raise HTTPException(403, "Not your listing")

        conn.execute("UPDATE mkt_listings SET status = 'collected' WHERE id = ?", (listing_id,))
        conn.execute(
            """INSERT INTO mkt_alerts (user_id, type, message)
               VALUES (?, 'pledge', ?)""",
            (claim["recipient_id"], f"Pickup confirmed for listing {listing_id}")
        )
        conn.commit()
        return {"ok": True, "listing_id": listing_id}
    finally:
        conn.close()


def served_listing(listing_id: str, recipient_id: str, people_served: int):
    """Mark listing as served/distributed."""
    conn = get_connection()
    try:
        claim = conn.execute(
            "SELECT * FROM mkt_claims WHERE listing_id = ? AND recipient_id = ?",
            (listing_id, recipient_id)
        ).fetchone()
        if not claim:
            raise HTTPException(404, "Claim not found")

        conn.execute(
            "UPDATE mkt_listings SET status = 'distributed', people_served = ? WHERE id = ?",
            (people_served, listing_id)
        )
        conn.commit()
        return {"ok": True, "listing_id": listing_id, "people_served": people_served}
    finally:
        conn.close()


def create_need(recipient_id: str, people: int, needed_by: str, veg_only: bool, notes: str = ""):
    """Create a need request."""
    recipient = get_user(recipient_id)
    if not recipient:
        raise ValueError("Recipient not found")

    need_id = f"need_{uuid4().hex[:8]}"
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO mkt_needs (id, recipient_id, recipient_name, people, needed_by, veg_only, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (need_id, recipient_id, recipient["name"], people, needed_by, 1 if veg_only else 0, notes)
        )
        # Alert nearby donors
        donors = [u for u in get_connection().execute("SELECT * FROM core_users WHERE role IN ('kitchen', 'processing_unit')").fetchall()]
        for donor in donors:
            dist = haversine(recipient["lat"], recipient["lng"], donor["lat"], donor["lng"])
            if dist <= 10:
                conn.execute(
                    """INSERT INTO mkt_alerts (user_id, type, message)
                       VALUES (?, 'pledge', ?)""",
                    (donor["id"], f"New need nearby: {people} people by {needed_by}")
                )
        conn.commit()
        return need_id
    finally:
        conn.close()


def get_needs(status: Optional[str] = None, recipient_id: Optional[str] = None, for_donor_id: Optional[str] = None) -> List[dict]:
    """Get needs with optional filters."""
    conn = get_connection()
    try:
        query = "SELECT * FROM mkt_needs WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if recipient_id:
            query += " AND recipient_id = ?"
            params.append(recipient_id)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def pledge_to_need(need_id: str, donor_id: str, quantity: float, unit: str, note: str = ""):
    """Pledge to fulfill a need."""
    donor = get_user(donor_id)
    if not donor:
        raise ValueError("Donor not found")

    conn = get_connection()
    try:
        need = conn.execute("SELECT * FROM mkt_needs WHERE id = ?", (need_id,)).fetchone()
        if not need:
            raise HTTPException(404, "Need not found")
        if need["status"] != "open":
            raise HTTPException(409, "Need already pledged or closed")

        conn.execute(
            """INSERT INTO mkt_pledges (need_id, donor_id, donor_name, quantity, unit, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (need_id, donor_id, donor["name"], quantity, unit, note)
        )
        conn.execute("UPDATE mkt_needs SET status = 'pledged' WHERE id = ?", (need_id,))
        conn.commit()
        return {"ok": True, "need_id": need_id}
    finally:
        conn.close()


def get_alerts(user_id: str, since: Optional[str] = None, unread_only: bool = False) -> List[dict]:
    """Get alerts for a user."""
    conn = get_connection()
    try:
        query = "SELECT * FROM mkt_alerts WHERE user_id = ?"
        params = [user_id]
        if since:
            query += " AND created_at >= ?"
            params.append(since)
        if unread_only:
            query += " AND read = 0"
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def mark_alerts_read(user_id: str):
    """Mark all alerts as read for a user."""
    conn = get_connection()
    try:
        conn.execute("UPDATE mkt_alerts SET read = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


def get_impact(donor_id: str) -> dict:
    """Get impact statistics for a donor."""
    conn = get_connection()
    try:
        # Total listings
        total_listings = conn.execute(
            "SELECT COUNT(*) as cnt FROM mkt_listings WHERE donor_id = ?", (donor_id,)
        ).fetchone()["cnt"]

        # Distributed listings
        distributed = conn.execute(
            "SELECT COUNT(*) as cnt, SUM(people_served) as total_served FROM mkt_listings WHERE donor_id = ? AND status = 'distributed'",
            (donor_id,)
        ).fetchone()

        # Total quantity donated
        total_qty = conn.execute(
            "SELECT SUM(quantity) as total FROM mkt_listings WHERE donor_id = ?", (donor_id,)
        ).fetchone()["total"] or 0

        return {
            "donor_id": donor_id,
            "total_listings": total_listings,
            "distributed_count": distributed["cnt"] or 0,
            "total_people_served": distributed["total_served"] or 0,
            "total_quantity_donated": total_qty,
            "unit": "plates",
        }
    finally:
        conn.close()