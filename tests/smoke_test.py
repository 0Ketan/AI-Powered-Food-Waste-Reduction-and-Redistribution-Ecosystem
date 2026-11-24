"""
Smoke Test for AnnaSetu AI Backend
Importers: run.py (for server startup), backend/app.py, all module routers
Affected API: All endpoints - /health, /clock, /users, /forecast/*, /waste/*, /safety/*, /marketplace/*
Data schemas: All module data schemas from core/db.py and individual module db.py files
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
import sys
import os
import subprocess
import time
import requests
import json
from pathlib import Path

# Ensure localhost requests bypass sandbox proxy
os.environ["NO_PROXY"] = "localhost,127.0.0.1,0.0.0.0"
os.environ["no_proxy"] = "localhost,127.0.0.1,0.0.0.0"

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
SERVER_PROCESS = None


def start_server():
    """Start the FastAPI server in background."""
    global SERVER_PROCESS
    if SERVER_PROCESS is not None:
        return
    print("Starting server...")
    SERVER_PROCESS = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=Path(__file__).parent.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # Wait for server to start
    time.sleep(3)
    print("Server started")


def stop_server():
    """Stop the FastAPI server."""
    global SERVER_PROCESS
    if SERVER_PROCESS:
        print("Stopping server...")
        SERVER_PROCESS.terminate()
        try:
            SERVER_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            SERVER_PROCESS.kill()
        SERVER_PROCESS = None
        print("Server stopped")


def setup_module(module):
    """Start server for pytest collection."""
    start_server()


def teardown_module(module):
    """Stop server after pytest collection."""
    stop_server()


def test_health():
    """Test health endpoint."""
    print("\n=== Testing /health ===")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    data = r.json()
    assert "services" in data
    print(f"PASS Health OK: {data['services']}")
    return True


def test_clock():
    """Test clock endpoints."""
    print("\n=== Testing /api/demo/clock ===")
    # Get current time
    r = requests.get(f"{BASE_URL}/api/demo/clock")
    assert r.status_code == 200
    data = r.json()
    assert "demo_time_utc" in data
    print(f"PASS Current time: {data['demo_time_utc']}")

    # Test advance
    r = requests.post(f"{BASE_URL}/api/demo/advance", params={"minutes": 60})
    assert r.status_code == 200
    data = r.json()
    assert data["offset_minutes"] == 60
    print(f"PASS Offset set: {data['offset_minutes']} minutes")

    # Reset offset
    r = requests.post(f"{BASE_URL}/api/demo/reset")
    assert r.status_code == 200
    print("PASS Offset reset")
    return True


def test_users():
    """Test users endpoint."""
    print("\n=== Testing /api/users ===")
    r = requests.get(f"{BASE_URL}/api/users")
    assert r.status_code == 200
    data = r.json()
    assert "users" in data
    assert len(data["users"]) > 0
    print(f"PASS Users loaded: {len(data['users'])} users")
    for u in data["users"]:
        print(f"  - {u['id']}: {u['name']} ({u['role']})")
    return True


def test_forecast():
    """Test forecast module endpoints."""
    print("\n=== Testing /api/forecast ===")
    # Options
    r = requests.get(f"{BASE_URL}/api/forecast/options")
    assert r.status_code == 200
    data = r.json()
    assert "kitchens" in data
    assert "slots" in data
    print(f"PASS Options: {len(data['kitchens'])} kitchens, slots: {data['slots']}")

    # Recommend
    if data["kitchens"]:
        kitchen_id = data["kitchens"][0]["id"]
        slot = data["slots"][0]
        payload = {
            "kitchen_id": kitchen_id,
            "slot": slot,
            "date": "2026-11-24",
            "weather": "clear",
            "event": "none",
            "safety_level": 0.75
        }
        r = requests.post(f"{BASE_URL}/api/forecast/recommend", json=payload)
        assert r.status_code == 200
        rec = r.json()
        assert "recommended" in rec
        assert "baseline" in rec
        print(f"PASS Recommend: baseline={rec['baseline']}, recommended={rec['recommended']}, summary={rec['summary']}")

    # Metrics
    if data["kitchens"]:
        kitchen_id = data["kitchens"][0]["id"]
        slot = data["slots"][0]
        r = requests.get(f"{BASE_URL}/api/forecast/metrics", params={"kitchen_id": kitchen_id, "slot": slot})
        assert r.status_code == 200
        metrics = r.json()
        assert "baseline_mae" in metrics
        print(f"PASS Metrics: baseline_mae={metrics['baseline_mae']}")
    return True


def test_waste():
    """Test waste module endpoints."""
    print("\n=== Testing /api/waste ===")
    # Get users first
    r = requests.get(f"{BASE_URL}/api/users")
    users = r.json()["users"]
    kitchen_users = [u for u in users if u["role"] == "kitchen"]
    assert kitchen_users, "No kitchen users found"
    kitchen_id = kitchen_users[0]["id"]

    # Log waste
    payload = {
        "kitchen_id": kitchen_id,
        "item_name": "Test Rice",
        "quantity_kg": 5.0,
        "category": "cooked_rice",
        "reason": "overproduction",
        "disposal_method": "donation"
    }
    r = requests.post(f"{BASE_URL}/api/waste/log", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "log_id" in data
    log_id = data["log_id"]
    print(f"PASS Waste logged: {log_id}")

    # Get logs
    r = requests.get(f"{BASE_URL}/api/waste/logs", params={"kitchen_id": kitchen_id})
    assert r.status_code == 200
    logs = r.json()
    assert "logs" in logs
    print(f"PASS Logs retrieved: {len(logs['logs'])} entries")

    # Get summary
    r = requests.get(f"{BASE_URL}/api/waste/summary", params={"kitchen_id": kitchen_id})
    assert r.status_code == 200
    summary = r.json()
    assert "total_kg" in summary
    print(f"PASS Summary: total_kg={summary['total_kg']}")
    return True


def test_safety():
    """Test safety module endpoints."""
    print("\n=== Testing /api/safety ===")
    # Get users
    r = requests.get(f"{BASE_URL}/api/users")
    users = r.json()["users"]
    kitchen_users = [u for u in users if u["role"] == "kitchen"]
    assert kitchen_users, "No kitchen users found"
    kitchen_id = kitchen_users[0]["id"]

    # Categories
    r = requests.get(f"{BASE_URL}/api/safety/categories")
    assert r.status_code == 200
    categories = r.json()
    assert len(categories) > 0
    print(f"PASS Categories: {len(categories)} items")
    cat_id = categories[0]["id"]

    # Evaluate safety
    payload = {
        "donor_id": kitchen_id,
        "item_name": "Test Rice",
        "category_id": cat_id,
        "veg": True,
        "quantity": 10.0,
        "unit": "plates",
        "storage": "refrigerated",
        "prepared_at": "2026-11-24T10:00:00Z",
        "kitchen_confirms_safe": True,
        "pickup_buffer_minutes": 45
    }
    r = requests.post(f"{BASE_URL}/api/safety/evaluate", json=payload)
    assert r.status_code == 200
    eval_result = r.json()
    assert "decision" in eval_result
    assert "consume_by" in eval_result
    print(f"PASS Evaluate: decision={eval_result['decision']}, consume_by={eval_result['consume_by']}")

    # Records
    r = requests.get(f"{BASE_URL}/api/safety/records", params={"donor_id": kitchen_id})
    assert r.status_code == 200
    records = r.json()
    print(f"PASS Records: {len(records)} items")

    # CSV
    r = requests.get(f"{BASE_URL}/api/safety/records.csv", params={"donor_id": kitchen_id})
    assert r.status_code == 200
    assert "record_id" in r.text
    print("PASS CSV export works")

    # Disposals
    r = requests.get(f"{BASE_URL}/api/safety/disposals", params={"donor_id": kitchen_id})
    assert r.status_code == 200
    disposals = r.json()
    print(f"PASS Disposals: {len(disposals)} items")

    # Create disposal
    disp_payload = {
        "donor_id": kitchen_id,
        "item_name": "Old Bread",
        "quantity": 5.0,
        "unit": "loaves",
        "route": "compost",
        "reason": "expired"
    }
    r = requests.post(f"{BASE_URL}/api/safety/disposals", json=disp_payload)
    assert r.status_code == 200
    disp = r.json()
    assert "disposal_id" in disp
    print(f"PASS Disposal created: {disp['disposal_id']}")

    return True


def test_marketplace():
    """Test marketplace module endpoints."""
    print("\n=== Testing /api/marketplace ===")
    # Get users
    r = requests.get(f"{BASE_URL}/api/users")
    users = r.json()["users"]
    kitchen_users = [u for u in users if u["role"] == "kitchen"]
    ngo_users = [u for u in users if u["role"] == "ngo"]
    assert kitchen_users, "No kitchen users found"
    assert ngo_users, "No NGO users found"
    kitchen_id = kitchen_users[0]["id"]
    ngo_id = ngo_users[0]["id"]

    # Get categories from safety for listing
    r = requests.get(f"{BASE_URL}/api/safety/categories")
    categories = r.json()
    cat_id = categories[0]["id"]

    # Create listing
    payload = {
        "donor_id": kitchen_id,
        "item_name": "Fresh Rice",
        "category_id": cat_id,
        "veg": True,
        "quantity": 50,
        "unit": "plates",
        "storage": "refrigerated",
        "consume_by": "2026-11-24T14:00:00Z",
        "label_id": "lbl_test123",
        "record_id": "rec_test123"
    }
    r = requests.post(f"{BASE_URL}/api/marketplace/listings", json=payload)
    assert r.status_code == 200
    listing = r.json()
    assert "listing_id" in listing
    listing_id = listing["listing_id"]
    print(f"PASS Listing created: {listing_id}")

    # Get listings
    r = requests.get(f"{BASE_URL}/api/marketplace/listings", params={"donor_id": kitchen_id})
    assert r.status_code == 200
    listings = r.json()
    print(f"PASS Listings: {len(listings)} items")

    # Nearby listings
    r = requests.get(f"{BASE_URL}/api/marketplace/nearby", params={"recipient_id": ngo_id})
    assert r.status_code == 200
    nearby = r.json()
    print(f"PASS Nearby: {len(nearby)} listings")
    if nearby:
        print(f"  First: {nearby[0]['item_name']} - {nearby[0]['distance_km']}km, {nearby[0]['minutes_left']}min left")

    # Claim listing
    r = requests.post(f"{BASE_URL}/api/marketplace/listings/{listing_id}/claim", json={"recipient_id": ngo_id})
    assert r.status_code == 200
    claim = r.json()
    assert "pickup_code" in claim
    pickup_code = claim["pickup_code"]
    print(f"PASS Claimed: pickup_code={pickup_code}")

    # Pickup listing
    r = requests.post(f"{BASE_URL}/api/marketplace/listings/{listing_id}/pickup", json={"donor_id": kitchen_id, "code": pickup_code})
    assert r.status_code == 200
    pickup = r.json()
    assert pickup["ok"] == True
    print(f"PASS Picked up")

    # Serve listing
    r = requests.post(f"{BASE_URL}/api/marketplace/listings/{listing_id}/served", json={"recipient_id": ngo_id, "people_served": 45})
    assert r.status_code == 200
    served = r.json()
    assert served["ok"] == True
    print(f"PASS Served: {served['people_served']} people")

    # Create need
    need_payload = {
        "recipient_id": ngo_id,
        "people": 100,
        "needed_by": "2026-11-24T18:00:00Z",
        "veg_only": True,
        "notes": "Urgent need"
    }
    r = requests.post(f"{BASE_URL}/api/marketplace/needs", json=need_payload)
    assert r.status_code == 200
    need = r.json()
    assert "need_id" in need
    need_id = need["need_id"]
    print(f"PASS Need created: {need_id}")

    # Get needs
    r = requests.get(f"{BASE_URL}/api/marketplace/needs", params={"recipient_id": ngo_id})
    assert r.status_code == 200
    needs = r.json()
    print(f"PASS Needs: {len(needs)} items")

    # Pledge to need
    r = requests.post(f"{BASE_URL}/api/marketplace/needs/{need_id}/pledge", json={"donor_id": kitchen_id, "quantity": 50, "unit": "plates", "note": "Can deliver by noon"})
    assert r.status_code == 200
    pledge = r.json()
    assert pledge["ok"] == True
    print(f"PASS Pledged")

    # Alerts
    r = requests.get(f"{BASE_URL}/api/marketplace/alerts", params={"user_id": kitchen_id})
    assert r.status_code == 200
    alerts = r.json()
    print(f"PASS Alerts: {len(alerts)} items")

    # Mark alerts read
    r = requests.post(f"{BASE_URL}/api/marketplace/alerts/read", json={"user_id": kitchen_id})
    assert r.status_code == 200
    print(f"PASS Alerts marked read")

    # Impact
    r = requests.get(f"{BASE_URL}/api/marketplace/impact", params={"donor_id": kitchen_id})
    assert r.status_code == 200
    impact = r.json()
    assert "total_listings" in impact
    print(f"PASS Impact: listings={impact['total_listings']}, served={impact['total_people_served']}")

    return True


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 60)
    print("ANNASETU AI - SMOKE TEST")
    print("=" * 60)

    tests = [
        ("Health", test_health),
        ("Clock", test_clock),
        ("Users", test_users),
        ("Forecast", test_forecast),
        ("Waste", test_waste),
        ("Safety", test_safety),
        ("Marketplace", test_marketplace),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"FAIL {name} FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    # Start server
    start_server()

    try:
        # Wait a bit more for server to be fully ready
        time.sleep(2)

        # Run tests
        success = run_all_tests()

        # Exit with appropriate code
        sys.exit(0 if success else 1)
    finally:
        stop_server()