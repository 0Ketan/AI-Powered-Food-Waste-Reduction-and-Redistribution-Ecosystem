"""
Marketplace Module Service Layer
Importers: backend/modules/marketplace/router.py
Affected API: All marketplace endpoints (listings, nearby, claim, pickup, served, needs, pledges, alerts, impact)
Data schemas: mkt_listings, mkt_claims, mkt_alerts, mkt_needs, mkt_pledges tables from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from typing import Optional, List, Dict
from .db import (
    create_listing, get_listings, get_listing, get_nearby_listings,
    claim_listing, pickup_listing, served_listing,
    create_need, get_needs, pledge_to_need,
    get_alerts, mark_alerts_read, get_impact
)


class MarketplaceService:
    """Business logic for marketplace operations."""

    # Listing operations
    @staticmethod
    def create_listing(donor_id: str, item_name: str, category_id: str, veg: bool,
                       quantity: float, unit: str, storage: str, consume_by: str,
                       label_id: Optional[str] = None, record_id: Optional[str] = None) -> str:
        """Create a marketplace listing."""
        return create_listing(donor_id, item_name, category_id, veg, quantity, unit, storage, consume_by, label_id, record_id)

    @staticmethod
    def get_listings(donor_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """Get marketplace listings with optional filters."""
        return get_listings(donor_id, status)

    @staticmethod
    def get_listing(listing_id: str) -> Optional[Dict]:
        """Get a single listing by ID."""
        return get_listing(listing_id)

    @staticmethod
    def get_nearby_listings(recipient_id: str, max_km: float = 10.0) -> List[Dict]:
        """Get nearby open listings for a recipient."""
        return get_nearby_listings(recipient_id, max_km)

    @staticmethod
    def claim_listing(listing_id: str, recipient_id: str) -> Dict:
        """Claim a listing - generates 4-digit pickup code."""
        return claim_listing(listing_id, recipient_id)

    @staticmethod
    def pickup_listing(listing_id: str, donor_id: str, code: str) -> Dict:
        """Verify pickup code and mark as collected."""
        return pickup_listing(listing_id, donor_id, code)

    @staticmethod
    def serve_listing(listing_id: str, recipient_id: str, people_served: int) -> Dict:
        """Mark listing as served/distributed."""
        return served_listing(listing_id, recipient_id, people_served)

    # Need operations
    @staticmethod
    def create_need(recipient_id: str, people: int, needed_by: str, veg_only: bool, notes: str = "") -> str:
        """Create a need request."""
        return create_need(recipient_id, people, needed_by, veg_only, notes)

    @staticmethod
    def get_needs(status: Optional[str] = None, recipient_id: Optional[str] = None, for_donor_id: Optional[str] = None) -> List[Dict]:
        """Get needs with optional filters."""
        return get_needs(status, recipient_id, for_donor_id)

    @staticmethod
    def pledge_to_need(need_id: str, donor_id: str, quantity: float, unit: str, note: str = "") -> Dict:
        """Pledge to fulfill a need."""
        return pledge_to_need(need_id, donor_id, quantity, unit, note)

    # Alert operations
    @staticmethod
    def get_alerts(user_id: str, since: Optional[str] = None, unread_only: bool = False) -> List[Dict]:
        """Get alerts for a user."""
        return get_alerts(user_id, since, unread_only)

    @staticmethod
    def mark_alerts_read(user_id: str) -> Dict:
        """Mark all alerts as read for a user."""
        return mark_alerts_read(user_id)

    # Impact operations
    @staticmethod
    def get_impact(donor_id: str) -> Dict:
        """Get impact statistics for a donor."""
        return get_impact(donor_id)