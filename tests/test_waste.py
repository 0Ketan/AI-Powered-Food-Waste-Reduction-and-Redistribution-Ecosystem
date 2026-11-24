"""
Waste Module Unit Tests
Importers: None (standalone test module)
Affected API: POST /waste/logs, GET /waste/logs, GET /waste/summary
Data schemas: waste_logs table from core/db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from backend.modules.waste.db import insert_log, get_logs, get_summary
from backend.core.db import init_db, seed_database, get_connection


@pytest.fixture(scope="module")
def setup_db():
    """Initialize test database."""
    init_db()
    seed_database()
    yield


def test_insert_and_get_logs(setup_db):
    """Test inserting and retrieving a waste log."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()

    assert kitchen, "No kitchen user found"
    kitchen_id = kitchen["id"]

    # Insert log (prepared = served + leftover)
    insert_log(
        kitchen_id=kitchen_id,
        date="2026-11-24",
        slot="lunch",
        prepared=100,
        served=85,
        leftover=15,
        ran_short=False
    )

    logs = get_logs(kitchen_id=kitchen_id, limit=5)
    assert isinstance(logs, list)
    assert len(logs) >= 1
    latest = logs[0]
    assert latest["kitchen_id"] == kitchen_id
    assert latest["prepared"] == 100


def test_get_summary(setup_db):
    """Test waste summary totals match logs posted."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()

    kitchen_id = kitchen["id"]

    # Post two logs
    insert_log(kitchen_id, "2026-11-23", "lunch", 200, 180, 20, False)
    insert_log(kitchen_id, "2026-11-23", "dinner", 150, 130, 20, True)

    summary = get_summary(kitchen_id=kitchen_id)
    assert "unit" in summary
    assert "totals" in summary
    assert "days" in summary
    totals = summary["totals"]
    assert totals["prepared"] >= 200   # at least the ones we just added
    assert totals["leftover"] >= 20


def test_summary_totals_match_logs(setup_db):
    """Verify waste summary totals agree with the raw logs."""
    conn = get_connection()
    kitchen = conn.execute("SELECT id FROM core_users WHERE role = 'kitchen' LIMIT 1").fetchone()
    conn.close()
    kitchen_id = kitchen["id"]

    logs = get_logs(kitchen_id=kitchen_id, limit=200)
    total_prepared = sum(l["prepared"] for l in logs)
    total_leftover = sum(l["leftover"] for l in logs)

    summary = get_summary(kitchen_id=kitchen_id)
    totals = summary["totals"]
    assert totals["prepared"] == total_prepared, \
        f"summary.prepared={totals['prepared']} != sum of logs={total_prepared}"
    assert totals["leftover"] == total_leftover, \
        f"summary.leftover={totals['leftover']} != sum of logs={total_leftover}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
