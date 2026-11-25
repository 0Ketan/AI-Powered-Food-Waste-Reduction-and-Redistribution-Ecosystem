"""
Waste Module Summary Tests (M2)
Tests for summary maths, ran_short counting, ordering, unit per kitchen.
"""
import sys
from pathlib import Path
import pytest
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi.testclient import TestClient
from backend.app import app
from backend.core import db as core_db
from backend.core import init_db


# Hand-worked example:
# Log 1: kitchen=1, date=2026-11-20, slot=lunch, prepared=150, served=130, leftover=20, ran_short=False
# Log 2: kitchen=1, date=2026-11-20, slot=dinner, prepared=120, served=110, leftover=10, ran_short=True
# Log 3: kitchen=1, date=2026-11-21, slot=lunch, prepared=200, served=180, leftover=20, ran_short=False
# Log 4: kitchen=2, date=2026-11-20, slot=lunch, prepared=100, served=90, leftover=10, ran_short=False
#
# Kitchen 1, date 2026-11-20:
#   prepared = 150 + 120 = 270
#   served   = 130 + 110 = 240
#   leftover = 20 + 10 = 30
#   leftover_pct = 30/270 * 100 = 11.111... -> round to 1 decimal = 11.1
#   ran_short_count = 1 (only dinner)
#   by_slot: lunch avg_leftover = 20.0, dinner avg_leftover = 10.0
#
# Kitchen 1, date 2026-11-21:
#   prepared = 200, served = 180, leftover = 20
#   leftover_pct = 20/200 * 100 = 10.0
#   ran_short_count = 0
#   by_slot: lunch avg_leftover = 20.0
#
# Kitchen 1 totals:
#   prepared = 270 + 200 = 470
#   served = 240 + 180 = 420
#   leftover = 30 + 20 = 50
#   leftover_pct = 50/470 * 100 = 10.638... -> round to 1 decimal = 10.6
#   ran_short_count = 1
#   by_slot: lunch avg = (20+20)/2 = 20.0, dinner avg = 10.0
#
# Kitchen 2, date 2026-11-20:
#   prepared = 100, served = 90, leftover = 10
#   leftover_pct = 10/100 * 100 = 10.0
#   ran_short_count = 0
#   by_slot: lunch avg_leftover = 10.0
#
# Kitchen 3 (empty): all zeros


@pytest.fixture
def temp_db_with_data(monkeypatch, tmp_path):
    """Create temporary database with test data."""
    # Patch the DB_PATH
    monkeypatch.setattr(core_db, "DB_PATH", Path(tmp_path) / "test.db")
    core_db.init_db()

    # Insert test data
    import sqlite3
    conn = sqlite3.connect(str(core_db.DB_PATH))
    try:
        conn.execute("""INSERT INTO waste_logs (kitchen_id, date, slot, prepared, served, leftover, ran_short)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      ("1", "2026-11-20", "lunch", 150, 130, 20, 0))
        conn.execute("""INSERT INTO waste_logs (kitchen_id, date, slot, prepared, served, leftover, ran_short)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      ("1", "2026-11-20", "dinner", 120, 110, 10, 1))
        conn.execute("""INSERT INTO waste_logs (kitchen_id, date, slot, prepared, served, leftover, ran_short)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      ("1", "2026-11-21", "lunch", 200, 180, 20, 0))
        conn.execute("""INSERT INTO waste_logs (kitchen_id, date, slot, prepared, served, leftover, ran_short)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      ("2", "2026-11-20", "lunch", 100, 90, 10, 0))
        conn.commit()
    finally:
        conn.close()

    yield


def test_summary_totals_correct(temp_db_with_data):
    """Summary totals should match hand-worked arithmetic."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/summary?kitchen_id=1")
    data = r.json()

    # Hand-worked: prepared=470, served=420, leftover=50
    assert data["totals"]["prepared"] == 470
    assert data["totals"]["served"] == 420
    assert data["totals"]["leftover"] == 50


def test_leftover_pct_formula(temp_db_with_data):
    """leftover_pct = (leftover / prepared) * 100, rounded to 1 decimal."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/summary?kitchen_id=1")
    data = r.json()

    # 50/470 * 100 = 10.638... -> round to 1 decimal = 10.6
    assert data["totals"]["leftover_pct"] == 10.6


def test_shortage_count_from_ran_short(temp_db_with_data):
    """shortage_count counts ran_short=True entries."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/summary?kitchen_id=1")
    data = r.json()

    # Only 1 entry has ran_short=True (dinner)
    assert data["shortage_count"] == 1


def test_by_slot_avg_leftover(temp_db_with_data):
    """by_slot avg_leftover is average per slot."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/summary?kitchen_id=1")
    data = r.json()

    by_slot = {s["slot"]: s["avg_leftover"] for s in data["by_slot"]}
    # lunch: (20+20)/2 = 20.0
    # dinner: 10/1 = 10.0
    assert by_slot["lunch"] == 20.0
    assert by_slot["dinner"] == 10.0


def test_unit_per_kitchen(temp_db_with_data):
    """Summary includes unit per kitchen."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/summary?kitchen_id=1")
    data = r.json()

    assert data["unit"] == "plates"


def test_days_list(temp_db_with_data):
    """days list contains date-level aggregates."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/summary?kitchen_id=1")
    data = r.json()

    assert "days" in data
    assert isinstance(data["days"], list)
    assert len(data["days"]) == 2  # Two dates: 2026-11-20 and 2026-11-21

    # Days should be sorted ascending by date
    assert data["days"][0]["date"] == "2026-11-20"
    assert data["days"][1]["date"] == "2026-11-21"

    # Day 1: 2026-11-20
    day1 = data["days"][0]
    assert day1["date"] == "2026-11-20"
    assert day1["prepared"] == 270
    assert day1["served"] == 240
    assert day1["leftover"] == 30
    assert day1["shortage_count"] == 1

    # Day 2: 2026-11-21
    day2 = data["days"][1]
    assert day2["date"] == "2026-11-21"
    assert day2["prepared"] == 200
    assert day2["served"] == 180
    assert day2["leftover"] == 20
    assert day2["shortage_count"] == 0


def test_ordering(temp_db_with_data):
    """Logs ordered by date DESC, id descending."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/logs?kitchen_id=1&limit=10")
    data = r.json()

    logs = data["logs"]
    # Should be ordered by date DESC, then id DESC
    # So 2026-11-21 comes before 2026-11-20
    assert logs[0]["date"] == "2026-11-21"
    assert logs[0]["slot"] == "lunch"
    # Then 2026-11-20 entries (2 of them, ordered by id DESC - latest first)
    # Since dinner was inserted after lunch, dinner has higher id
    assert logs[1]["date"] == "2026-11-20"
    assert logs[1]["slot"] == "dinner"
    assert logs[2]["date"] == "2026-11-20"
    assert logs[2]["slot"] == "lunch"


def test_summary_totals_equal_sum_of_logs(temp_db_with_data):
    """totals should equal the sum of the returned logs."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    # Get summary
    r = client.get("/api/waste/summary?kitchen_id=1")
    summary_data = r.json()

    # Get logs
    r = client.get("/api/waste/logs?kitchen_id=1&limit=10")
    logs_data = r.json()

    logs = logs_data["logs"]

    # Sum the logs
    sum_prepared = sum(log["prepared"] for log in logs)
    sum_served = sum(log["served"] for log in logs)
    sum_leftover = sum(log["leftover"] for log in logs)

    assert summary_data["totals"]["prepared"] == sum_prepared
    assert summary_data["totals"]["served"] == sum_served
    assert summary_data["totals"]["leftover"] == sum_leftover


def test_empty_kitchen(temp_db_with_data):
    """Summary for unknown kitchen_id returns 400 error."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    # Kitchen 999 doesn't exist, should return 400
    r = client.get("/api/waste/summary?kitchen_id=999")
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_kitchen"


def test_ordering_with_same_date_tie(temp_db_with_data):
    """Ordering with same date tie broken by id descending."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/logs?kitchen_id=1&limit=10")
    data = r.json()

    logs = data["logs"]
    # Both 2026-11-20 entries should be ordered by id descending
    # dinner was inserted after lunch, so dinner has higher id
    nov20_logs = [log for log in data["logs"] if log["date"] == "2026-11-20"]
    assert len(nov20_logs) == 2
    assert nov20_logs[0]["slot"] == "dinner"  # Higher id comes first
    assert nov20_logs[1]["slot"] == "lunch"


def test_limit_and_invalid_limit(temp_db_with_data):
    """Test limit parameter and invalid limits."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    # limit 1
    r = client.get("/api/waste/logs?kitchen_id=1&limit=1")
    data = r.json()
    assert len(data["logs"]) == 1

    # limit 2
    r = client.get("/api/waste/logs?kitchen_id=1&limit=2")
    data = r.json()
    assert len(data["logs"]) == 2

    # limit larger than row count (kitchen 1 has 3 rows)
    r = client.get("/api/waste/logs?kitchen_id=1&limit=100")
    data = r.json()
    assert len(data["logs"]) == 3

    # limit 0 - should be 400
    r = client.get("/api/waste/logs?kitchen_id=1&limit=0")
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_limit"

    # limit -1
    r = client.get("/api/waste/logs?kitchen_id=1&limit=-1")
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_limit"

    # limit "abc"
    r = client.get("/api/waste/logs?kitchen_id=1&limit=abc")
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_limit"

    # limit 1.5
    r = client.get("/api/waste/logs?kitchen_id=1&limit=1.5")
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_limit"

    # limit 10**18
    r = client.get("/api/waste/logs?kitchen_id=1&limit=1000000000000000000")
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_limit"


def test_unknown_kitchen_on_logs(temp_db_with_data):
    """GET /logs with unknown kitchen_id returns 400."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/logs?kitchen_id=999")
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_kitchen"


def test_unknown_kitchen_on_summary(temp_db_with_data):
    """GET /summary with unknown kitchen_id returns 400."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/summary?kitchen_id=999")
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_kitchen"


def test_without_kitchen_id(temp_db_with_data):
    """Behaviour without kitchen_id stays as today (all kitchens)."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.get("/api/waste/logs?limit=10")
    data = r.json()
    # Should return all kitchens
    assert "logs" in data
    assert len(data["logs"]) >= 4

    r = client.get("/api/waste/summary")
    data = r.json()
    assert "totals" in data
    assert "unit" in data