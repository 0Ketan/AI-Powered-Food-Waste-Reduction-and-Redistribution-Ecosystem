"""
Shared Pydantic Schemas for AnnaSetu AI
Importers: All modules (backend.modules.*.router.py), backend/app.py
Affected API: All endpoints per contracts/API.md
Data schemas: All request/response models
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# CORE SCHEMAS
# ============================================================================

class HealthResponse(BaseModel):
    status: Literal["ok"]
    time: str


class ClockResponse(BaseModel):
    demo_time: str
    offset_hours: float
    real_time: str


class ClockAdvanceRequest(BaseModel):
    hours: float = Field(gt=0, le=168)  # Max 1 week


class ClockAdvanceResponse(BaseModel):
    ok: bool
    new_demo_time: str


class ClockResetResponse(BaseModel):
    ok: bool
    demo_time: str


class User(BaseModel):
    id: str
    name: str
    role: Literal["kitchen", "ngo", "admin"]
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


class UsersResponse(BaseModel):
    users: List[User]


# ============================================================================
# WASTE SCHEMAS
# ============================================================================

class WasteLogRequest(BaseModel):
    kitchen_id: str
    item_name: str
    quantity_kg: float = Field(gt=0)
    category: str
    reason: str
    disposal_method: str


class WasteLogResponse(BaseModel):
    log_id: str


class WasteLogEntry(BaseModel):
    id: str
    kitchen_id: str
    item_name: str
    quantity_kg: float
    category: str
    reason: str
    disposal_method: str
    created_at: str


class WasteLogsResponse(BaseModel):
    logs: List[WasteLogEntry]


class WasteSummaryResponse(BaseModel):
    total_kg: float
    by_category: dict
    by_reason: dict
    by_disposal: dict


# ============================================================================
# SAFETY SCHEMAS
# ============================================================================

class SafetyCategory(BaseModel):
    id: str
    name: str
    max_hours_hot: int
    max_hours_cold: int
    max_hours_frozen: int


class SafetyCategoriesResponse(BaseModel):
    categories: List[SafetyCategory]


class SafetyEvaluateRequest(BaseModel):
    donor_id: str
    item_name: str
    category_id: str
    veg: bool
    quantity: float = Field(gt=0)
    unit: str
    storage: Literal["hot", "refrigerated", "frozen"]
    prepared_at: str  # ISO format
    kitchen_confirms_safe: bool
    pickup_buffer_minutes: int = Field(ge=0, le=120)


class SafetyCheck(BaseModel):
    check: str
    passed: bool
    detail: str


class SafetyEvaluateResponse(BaseModel):
    decision: Literal["proceed", "conditional", "block"]
    consume_by: str
    label_id: str
    record_id: str
    checks: List[SafetyCheck]


class SafetyRecord(BaseModel):
    id: str
    donor_id: str
    item_name: str
    category_id: str
    veg: bool
    quantity: float
    unit: str
    storage: str
    prepared_at: str
    consume_by: str
    label_id: str
    decision: str
    created_at: str


class SafetyRecordsResponse(BaseModel):
    records: List[SafetyRecord]


class SafetyDisposalRequest(BaseModel):
    donor_id: str
    item_name: str
    quantity: float = Field(gt=0)
    unit: str
    route: Literal["compost", "landfill", "animal_feed", "other"]
    reason: str


class SafetyDisposalResponse(BaseModel):
    disposal_id: str


class SafetyDisposal(BaseModel):
    id: str
    donor_id: str
    item_name: str
    quantity: float
    unit: str
    route: str
    reason: str
    created_at: str


class SafetyDisposalsResponse(BaseModel):
    disposals: List[SafetyDisposal]


# ============================================================================
# FORECAST SCHEMAS
# ============================================================================

class KitchenInfo(BaseModel):
    id: str
    name: str
    role: Literal["kitchen"]


class ForecastOptionsResponse(BaseModel):
    kitchens: List[KitchenInfo]
    slots: List[str]
    weather_options: List[str]
    event_options: List[str]


class ForecastRecommendRequest(BaseModel):
    kitchen_id: str
    slot: Literal["lunch", "dinner"]
    date: str  # YYYY-MM-DD
    weather: str
    event: str


class ForecastAdjustmentReason(BaseModel):
    factor: str
    delta: int


class ForecastRecommendResponse(BaseModel):
    baseline: int
    adjustments: List[ForecastAdjustmentReason]
    recommended: int
    date: str
    slot: str


class ForecastMetricsResponse(BaseModel):
    kitchen_id: str
    slot: str
    mae: float
    samples: int


# ============================================================================
# MARKETPLACE SCHEMAS
# ============================================================================

class MarketplaceListingRequest(BaseModel):
    donor_id: str
    item_name: str
    category_id: str
    veg: bool
    quantity: float = Field(gt=0)
    unit: str
    storage: Literal["hot", "refrigerated", "frozen"]
    consume_by: str  # ISO format
    label_id: Optional[str] = None
    record_id: Optional[str] = None


class MarketplaceListingResponse(BaseModel):
    listing_id: str


class MarketplaceListing(BaseModel):
    id: str
    donor_id: str
    item_name: str
    category_id: str
    veg: bool
    quantity: float
    unit: str
    storage: str
    consume_by: str
    label_id: Optional[str]
    record_id: Optional[str]
    status: Literal["open", "claimed", "picked_up", "served", "expired"]
    created_at: str


class MarketplaceListingsResponse(BaseModel):
    listings: List[MarketplaceListing]


class NearbyListing(BaseModel):
    id: str
    donor_id: str
    donor_name: str
    item_name: str
    category_id: str
    veg: bool
    quantity: float
    unit: str
    storage: str
    consume_by: str
    distance_km: float
    minutes_left: int
    travel_minutes: int
    score: float


class MarketplaceNearbyResponse(BaseModel):
    listings: List[NearbyListing]


class ClaimRequest(BaseModel):
    recipient_id: str


class ClaimResponse(BaseModel):
    pickup_code: str


class PickupRequest(BaseModel):
    donor_id: str
    code: str = Field(pattern=r"^\d{4}$")


class PickupResponse(BaseModel):
    ok: bool


class ServedRequest(BaseModel):
    recipient_id: str
    people_served: int = Field(gt=0)


class ServedResponse(BaseModel):
    ok: bool
    people_served: int


class NeedRequest(BaseModel):
    recipient_id: str
    people: int = Field(gt=0)
    needed_by: str  # ISO format
    veg_only: bool
    notes: str = ""


class NeedResponse(BaseModel):
    need_id: str


class Need(BaseModel):
    id: str
    recipient_id: str
    people: int
    needed_by: str
    veg_only: bool
    notes: str
    status: Literal["open", "fulfilled", "expired"]
    created_at: str


class NeedsResponse(BaseModel):
    needs: List[Need]


class PledgeRequest(BaseModel):
    donor_id: str
    quantity: float = Field(gt=0)
    unit: str
    note: str = ""


class PledgeResponse(BaseModel):
    ok: bool


class Alert(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: str


class AlertsResponse(BaseModel):
    alerts: List[Alert]


class MarkAlertsReadResponse(BaseModel):
    ok: bool
    count: int


class ImpactResponse(BaseModel):
    total_listings: int
    distributed_count: int
    total_people_served: int
    total_quantity_donated: float