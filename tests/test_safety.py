"""
Safety Module Unit Tests
Importers: None (standalone test module)
Affected API: /safety/categories, /safety/evaluate, /safety/records, /safety/records.csv, /safety/disposals
Data schemas: safety_records, safety_disposals tables from core/db.py
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from backend.modules.safety.db import (
    get_categories, evaluate_safety, get_records, get_disposals, create_disposal
)
from backend.core.db import init_db, get_connection, seed_database


@pytest.fixture(scope="module")
def setup_db():
    """Initialize test database."""
    init_db()
    seed_database()
    yield


def test_get_categories(setup_db):
    """Test getting safety categories."""
    categories = get_categories()
    assert len(categories) > 0
    assert all("id" in c and "name" in c for c in categories)


def test_evaluate_safety_approve(setup_db):
    """Test safety evaluation approves a fresh item."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()

    assert kitchen, "No kitchen user found"
    kitchen_id = kitchen["id"]

    categories = get_categories()
    # Use packaged (long hold time) so it passes
    packaged = next((c for c in categories if c["id"] == "packaged"), categories[-1])

    from backend.core.clock import get_demo_time
    prepared_at = get_demo_time().isoformat()

    result = evaluate_safety(
        donor_id=kitchen_id,
        item_name="Test Packaged Rice",
        category_id=packaged["id"],
        veg=True,
        quantity=10.0,
        unit="plates",
        storage="room_temp",
        prepared_at=prepared_at,
        kitchen_confirms_safe=True,
        pickup_buffer_minutes=45
    )

    assert "decision" in result
    assert result["decision"] in ["approve", "reject"]
    assert "consume_by" in result
    assert "label_id" in result
    assert "record_id" in result


def test_evaluate_safety_reject_expired(setup_db):
    """Test safety evaluation rejects an expired item."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()

    kitchen_id = kitchen["id"]
    categories = get_categories()
    cat = categories[0]  # cooked_rice: 2h hold

    # Prepared 10 hours ago (way past hold time)
    from datetime import datetime, timedelta, timezone
    old_time = (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()

    result = evaluate_safety(
        donor_id=kitchen_id,
        item_name="Old Rice",
        category_id=cat["id"],
        veg=True,
        quantity=5.0,
        unit="plates",
        storage="room_temp",
        prepared_at=old_time,
        kitchen_confirms_safe=True,
        pickup_buffer_minutes=45
    )

    assert result["decision"] == "reject"
    assert "reason" in result


def test_get_records(setup_db):
    """Test getting safety records."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()

    assert kitchen
    kitchen_id = kitchen["id"]
    records = get_records(donor_id=kitchen_id)
    assert isinstance(records, list)


def test_get_disposals(setup_db):
    """Test getting disposal records."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()

    assert kitchen
    kitchen_id = kitchen["id"]
    disposals = get_disposals(donor_id=kitchen_id)
    assert isinstance(disposals, list)


def test_create_disposal(setup_db):
    """Test creating a disposal record."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()

    assert kitchen
    kitchen_id = kitchen["id"]

    disposal_id = create_disposal(
        donor_id=kitchen_id,
        item_name="Old Bread",
        quantity=5.0,
        unit="loaves",
        route="compost",
        reason="expired"
    )

    assert disposal_id is not None
    assert disposal_id.startswith("disp_")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
