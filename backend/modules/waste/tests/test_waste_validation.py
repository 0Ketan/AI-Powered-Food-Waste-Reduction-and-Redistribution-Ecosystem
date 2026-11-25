"""
Waste Module Validation Tests (M2)
Tests for validation, ran_short counting, /summary maths, ordering.
Uses temporary database via pytest tmp_path + monkeypatch.
"""
import sys
from pathlib import Path
import os
import sqlite3
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi.testclient import TestClient
from backend.app import app
from backend.core import db as core_db
from backend.core import init_db


# Hand-worked example for test_waste_summary:
# Log 1: kitchen=1, date=2026-11-20, slot=lunch, prepared=150, served=130, leftover=20, ran_short=False
# Log 2: kitchen=1, date=2026-11-20, slot=dinner, prepared=120, served=110, leftover=10, ran_short=True
#
# Totals for 2026-11-20:
#   prepared = 150 + 120 = 270
#   served   = 130 + 110 = 240
#   leftover = 20 + 10 = 30
#   leftover_pct = 30/270 * 100 = 11.111... -> round to 1 decimal = 11.1
#   ran_short_count = 1 (only dinner)
#
# By slot averages:
#   lunch: avg_leftover = 20.0
#   dinner: avg_leftover = 10.0


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Create temporary database and monkeypatch DB_PATH."""
    db_path = tmp_path / "test.db"

    # Patch the DB_PATH in core_db module
    monkeypatch.setattr(core_db, "DB_PATH", Path(tmp_path) / "test.db")

    # Re-initialize schema
    core_db.init_db()

    yield

    # No cleanup needed, tmp_path is auto-cleaned


def test_valid_log_accepted(temp_db):
    """A valid log is accepted (200, row stored)."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100,
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 200
    assert r.json() == {"ok": True, "id": 1, "log_id": "wst_1"}


def test_negative_prepared_rejected(temp_db):
    """Negative prepared is rejected with status 400 and error shape."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": -10,
        "served": 5,
        "leftover": 5,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_value"
    assert "non-negative" in data["message"]


def test_negative_served_rejected(temp_db):
    """Negative served is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100,
        "served": -5,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_value"


def test_negative_leftover_rejected(temp_db):
    """Negative leftover is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100,
        "served": 105,
        "leftover": -5,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_value"


def test_string_number_rejected(temp_db):
    """String number is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": "100",
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_type"


def test_float_rejected(temp_db):
    """Float is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100.5,
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_type"


def test_bool_rejected(temp_db):
    """Boolean is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": True,
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_type"
    assert "boolean" in r.json()["message"]


def test_missing_kitchen_id_rejected(temp_db):
    """Missing kitchen_id is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100,
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "missing_field"


def test_unknown_kitchen_rejected(temp_db):
    """Unknown kitchen_id is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "999",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100,
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_kitchen"


def test_unknown_slot_rejected(temp_db):
    """Unknown slot is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "invalid",
        "prepared": 100,
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_slot"


def test_invalid_date_rejected(temp_db):
    """Invalid date (2026-02-30) is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-02-30",
        "slot": "lunch",
        "prepared": 100,
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_date"


def test_malformed_date_rejected(temp_db):
    """Malformed date is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026/11/20",
        "slot": "lunch",
        "prepared": 100,
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_date"


def test_ran_short_string_rejected(temp_db):
    """ran_short as string is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100,
        "served": 85,
        "leftover": 15,
        "ran_short": "yes"
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_type"


def test_ran_short_number_rejected(temp_db):
    """ran_short as number is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100,
        "served": 85,
        "leftover": 15,
        "ran_short": 1
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_type"


def test_invalid_json_rejected(temp_db):
    """Invalid JSON body is rejected."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post(
        "/api/waste/log",
        content='not json',
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_json"


def test_served_plus_leftover_not_equal_prepared(temp_db):
    """served + leftover != prepared is rejected (stub rule)."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100,
        "served": 85,
        "leftover": 20,
        "ran_short": False
    })
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "invalid_value"


def test_rejected_request_writes_nothing(temp_db):
    """A rejected request writes nothing to the database."""
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)

    # Get initial count
    conn = sqlite3.connect("runtime/annasetu.db")
    cur = conn.execute("SELECT COUNT(*) FROM waste_logs WHERE kitchen_id = '1'")
    before_count = cur.fetchone()[0]
    conn.close()

    # Send invalid request
    client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": -10,
        "served": 5,
        "leftover": 5,
        "ran_short": False
    })

    # Count should be unchanged
    conn = sqlite3.connect("runtime/annasetu.db")
    cur = conn.execute("SELECT COUNT(*) FROM waste_logs WHERE kitchen_id = '1'")
    after_count = cur.fetchone()[0]
    conn.close()

    assert before_count == after_count


def test_valid_log_stored(temp_db):
    """Valid log is stored in database."""
    from fastapi.testclient import TestClient
    from backend.app import app
    import sqlite3
    from backend.core import db as core_db

    client = TestClient(app)

    r = client.post("/api/waste/log", json={
        "kitchen_id": "1",
        "date": "2026-11-20",
        "slot": "lunch",
        "prepared": 100,
        "served": 85,
        "leftover": 15,
        "ran_short": False
    })
    assert r.status_code == 200

    # Verify stored in temp DB - need to get the patched DB_PATH
    from backend.core import db as core_db
    conn = sqlite3.connect(str(core_db.DB_PATH))
    cur = conn.execute("SELECT * FROM waste_logs WHERE kitchen_id = '1' AND date = '2026-11-20'")
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[4] == 100  # prepared (index 4)
    assert row[5] == 85   # served (index 5)
    assert row[6] == 15   # leftover (index 6)