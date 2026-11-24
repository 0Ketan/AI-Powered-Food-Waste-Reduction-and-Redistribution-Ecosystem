"""
Marketplace Module Unit Tests
Importers: None (standalone test module)
Affected API: /marketplace/listings, /marketplace/nearby, /marketplace/listings/{id}/claim|pickup|served, /marketplace/needs, /marketplace/needs/{id}/pledge, /marketplace/alerts, /marketplace/alerts/read, /marketplace/impact
Data schemas: mkt_listings, mkt_claims, mkt_alerts, mkt_needs, mkt_pledges tables from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from backend.modules.marketplace.db import (
    create_listing, get_listings, get_nearby_listings,
    claim_listing, pickup_listing, served_listing,
    create_need, get_needs, pledge_to_need,
    get_alerts, mark_alerts_read, get_impact
)
from backend.modules.safety.db import get_categories
from backend.core.db import init_db, get_connection


@pytest.fixture(scope="module")
def setup_db():
    """Initialize test database."""
    init_db()
    yield


def test_create_and_get_listing(setup_db):
    """Test creating and retrieving a listing."""
    # Get users
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    ngo = conn.execute("SELECT id FROM core_users WHERE role = 'ngo' LIMIT 1").fetchone()
    conn.close()

    assert kitchen, "No kitchen user found"
    assert ngo, "No NGO user found"
    kitchen_id = kitchen["id"]
    ngo_id = ngo["id"]

    # Get category
    categories = get_categories()
    cat_id = categories[0]["id"]

    # Create listing
    listing_id = create_listing(
        donor_id=kitchen_id,
        item_name="Fresh Rice",
        category_id=cat_id,
        veg=True,
        quantity=50,
        unit="plates",
        storage="refrigerated",
        consume_by="2026-11-24T14:00:00Z",
        label_id="lbl_test",
        record_id="rec_test"
    )

    assert listing_id is not None
    assert listing_id.startswith("lst_")

    # Get listings
    listings = get_listings(donor_id=kitchen_id)
    assert len(listings) >= 1
    assert any(l["id"] == listing_id for l in listings)


def test_nearby_listings(setup_db):
    """Test getting nearby listings."""
    conn = get_connection()
    ngo = conn.execute("SELECT id FROM core_users WHERE role = 'ngo' LIMIT 1").fetchone()
    conn.close()

    assert ngo
    ngo_id = ngo["id"]

    nearby = get_nearby_listings(recipient_id=ngo_id)
    assert isinstance(nearby, list)
    for listing in nearby:
        assert "distance_km" in listing
        assert "minutes_left" in listing
        assert "travel_minutes" in listing
        assert "score" in listing


def test_claim_pickup_serve_flow(setup_db):
    """Test complete claim -> pickup -> serve flow."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    ngo = conn.execute("SELECT id FROM core_users WHERE role = 'ngo' LIMIT 1").fetchone()
    conn.close()

    assert kitchen and ngo
    kitchen_id = kitchen["id"]
    ngo_id = ngo["id"]

    categories = get_categories()
    cat_id = categories[0]["id"]

    # Create listing
    listing_id = create_listing(
        donor_id=kitchen_id,
        item_name="Test Dal",
        category_id=cat_id,
        veg=True,
        quantity=30,
        unit="plates",
        storage="hot",
        consume_by="2026-11-24T13:00:00Z",
        label_id="lbl_test2",
        record_id="rec_test2"
    )

    # Claim
    claim_result = claim_listing(listing_id, ngo_id)
    assert "pickup_code" in claim_result
    pickup_code = claim_result["pickup_code"]
    assert len(pickup_code) == 4
    assert pickup_code.isdigit()

    # Pickup
    pickup_result = pickup_listing(listing_id, kitchen_id, pickup_code)
    assert pickup_result["ok"] == True

    # Serve
    serve_result = served_listing(listing_id, ngo_id, 25)
    assert serve_result["ok"] == True
    assert serve_result["people_served"] == 25


def test_need_and_pledge(setup_db):
    """Test creating need and pledging to it."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    ngo = conn.execute("SELECT id FROM core_users WHERE role = 'ngo' LIMIT 1").fetchone()
    conn.close()

    assert kitchen and ngo
    kitchen_id = kitchen["id"]
    ngo_id = ngo["id"]

    # Create need
    need_id = create_need(
        recipient_id=ngo_id,
        people=100,
        needed_by="2026-11-24T18:00:00Z",
        veg_only=True,
        notes="Urgent"
    )

    assert need_id is not None
    assert need_id.startswith("need_")

    # Pledge to need
    pledge_result = pledge_to_need(need_id, kitchen_id, 50, "plates", "Can deliver by noon")
    assert pledge_result["ok"] == True

    # Get needs
    needs = get_needs(recipient_id=ngo_id)
    assert len(needs) >= 1


def test_alerts(setup_db):
    """Test alert operations."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()

    assert kitchen
    kitchen_id = kitchen["id"]

    # Get alerts
    alerts = get_alerts(user_id=kitchen_id)
    assert isinstance(alerts, list)

    # Mark read
    result = mark_alerts_read(user_id=kitchen_id)
    assert result["ok"] == True


def test_impact(setup_db):
    """Test impact statistics."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()

    assert kitchen
    kitchen_id = kitchen["id"]

    impact = get_impact(donor_id=kitchen_id)
    assert "total_listings" in impact
    assert "distributed_count" in impact
    assert "total_people_served" in impact
    assert "total_quantity_donated" in impact


if __name__ == "__main__":
    pytest.main([__file__, "-v"])