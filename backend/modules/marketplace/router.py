"""
Marketplace Module Router
Importers: backend/modules/marketplace/__init__.py, backend/app.py
Affected API: GET/POST /api/marketplace/listings, GET /api/marketplace/nearby, POST /api/marketplace/listings/{id}/claim|pickup|served, GET/POST /api/marketplace/needs, POST /api/marketplace/needs/{id}/pledge, GET /api/alerts, POST /api/alerts/read, GET /api/impact
Data schemas: mkt_listings, mkt_claims, mkt_alerts, mkt_needs, mkt_pledges tables from core/db.py; SafetyEvaluateIn/Out models from safety/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List
from .db import (
    create_listing, get_listings, get_listing, get_nearby_listings,
    claim_listing, pickup_listing, served_listing,
    create_need, get_needs, pledge_to_need,
    get_alerts, mark_alerts_read, get_impact
)


router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/status")
def status():
    """Module status."""
    return {"module": "marketplace", "mode": "stub", "status": "ok"}


# ============================================================
# Listing Models
# ============================================================

class ListingCreate(BaseModel):
    donor_id: str
    item_name: str
    category_id: str
    veg: bool
    quantity: float = Field(gt=0)
    unit: str
    storage: str
    consume_by: str
    label_id: Optional[str] = None
    record_id: Optional[str] = None


class ClaimPayload(BaseModel):
    recipient_id: str


class PickupPayload(BaseModel):
    donor_id: str
    code: str


class ServedPayload(BaseModel):
    recipient_id: str
    people_served: int = Field(gt=0)


# ============================================================
# Listing Endpoints
# ============================================================

@router.post("/listings")
def create_listing_endpoint(payload: ListingCreate):
    """Create a new marketplace listing."""
    listing_id = create_listing(
        payload.donor_id, payload.item_name, payload.category_id, payload.veg,
        payload.quantity, payload.unit, payload.storage, payload.consume_by,
        payload.label_id, payload.record_id
    )
    return {"ok": True, "listing_id": listing_id}


@router.get("/listings")
def list_listings(donor_id: Optional[str] = None, status: Optional[str] = None):
    """Get listings with optional filters."""
    return get_listings(donor_id, status)


@router.get("/listings/{listing_id}")
def get_listing_endpoint(listing_id: str):
    """Get a single listing by ID."""
    listing = get_listing(listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    return listing


@router.get("/nearby")
def nearby_listings(recipient_id: str = Query(...), max_km: float = Query(10.0)):
    """Get nearby open listings for a recipient."""
    return get_nearby_listings(recipient_id, max_km)


@router.post("/listings/{listing_id}/claim")
def claim_listing_endpoint(listing_id: str, payload: ClaimPayload):
    """Claim a listing - generates 4-digit pickup code."""
    return claim_listing(listing_id, payload.recipient_id)


@router.post("/listings/{listing_id}/pickup")
def pickup_listing_endpoint(listing_id: str, payload: PickupPayload):
    """Verify pickup code and mark as collected."""
    return pickup_listing(listing_id, payload.donor_id, payload.code)


@router.post("/listings/{listing_id}/served")
def served_listing_endpoint(listing_id: str, payload: ServedPayload):
    """Mark listing as served/distributed."""
    return served_listing(listing_id, payload.recipient_id, payload.people_served)


# ============================================================
# Need Models
# ============================================================

class NeedCreate(BaseModel):
    recipient_id: str
    people: int = Field(gt=0)
    needed_by: str
    veg_only: bool
    notes: str = ""


class PledgePayload(BaseModel):
    donor_id: str
    quantity: float = Field(gt=0)
    unit: str
    note: str = ""


# ============================================================
# Need Endpoints
# ============================================================

@router.post("/needs")
def create_need_endpoint(payload: NeedCreate):
    """Create a need request."""
    need_id = create_need(
        payload.recipient_id, payload.people, payload.needed_by,
        payload.veg_only, payload.notes
    )
    return {"ok": True, "need_id": need_id}


@router.get("/needs")
def list_needs(
    status: Optional[str] = None,
    recipient_id: Optional[str] = None,
    for_donor_id: Optional[str] = None
):
    """Get needs with optional filters."""
    return get_needs(status, recipient_id, for_donor_id)


@router.post("/needs/{need_id}/pledge")
def pledge_to_need_endpoint(need_id: str, payload: PledgePayload):
    """Pledge to fulfill a need."""
    return pledge_to_need(need_id, payload.donor_id, payload.quantity, payload.unit, payload.note)


# ============================================================
# Alert Endpoints
# ============================================================

class AlertReadPayload(BaseModel):
    user_id: Optional[str] = None


@router.get("/alerts")
def get_user_alerts(
    user_id: str = Query(...),
    since: Optional[str] = None,
    unread_only: bool = False
):
    """Get alerts for a user."""
    return get_alerts(user_id, since, unread_only)


@router.post("/alerts/read")
def mark_alerts_read_endpoint(
    payload: Optional[AlertReadPayload] = Body(None),
    user_id: Optional[str] = Query(None)
):
    """Mark all alerts as read for a user."""
    uid = (payload.user_id if payload and payload.user_id else None) or user_id
    if not uid:
        raise HTTPException(400, "user_id is required")
    return mark_alerts_read(uid)


# ============================================================
# Impact Endpoints
# ============================================================

@router.get("/impact")
def get_donor_impact(donor_id: str = Query(...)):
    """Get impact statistics for a donor."""
    return get_impact(donor_id)