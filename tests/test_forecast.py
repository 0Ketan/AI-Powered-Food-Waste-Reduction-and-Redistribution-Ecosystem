"""
Forecast Module Contract Tests (M1)
Implementation-agnostic HTTP contract tests against /api/forecast/*.
"""
import os
import sys
from pathlib import Path

os.environ["NO_PROXY"] = "localhost,127.0.0.1,0.0.0.0"
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.core.db import init_db, seed_database


@pytest.fixture(scope="module")
def client():
    """Initialize DB and return FastAPI TestClient."""
    init_db()
    seed_database()
    return TestClient(app)


def _get_first_kitchen_and_slot(client: TestClient) -> tuple[str, str]:
    resp = client.get("/api/forecast/options")
    assert resp.status_code == 200
    data = resp.json()
    assert data["kitchens"], "No kitchens returned by /api/forecast/options"
    assert data["slots"], "No slots returned by /api/forecast/options"
    return data["kitchens"][0]["id"], data["slots"][0]


def test_forecast_options_shape(client):
    """GET /api/forecast/options returns expected shape and types."""
    resp = client.get("/api/forecast/options")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("kitchens"), list) and len(data["kitchens"]) > 0
    assert isinstance(data.get("slots"), list) and len(data["slots"]) > 0
    assert isinstance(data.get("weather_options"), list)
    assert isinstance(data.get("event_options"), list)


def test_forecast_recommend_shape_and_types(client):
    """POST /api/forecast/recommend returns valid contract v1.1 shape and types."""
    kitchen_id, slot = _get_first_kitchen_and_slot(client)
    resp = client.post(
        "/api/forecast/recommend",
        json={
            "kitchen_id": kitchen_id,
            "slot": slot,
            "date": "2026-11-30",  # Monday
            "weather": "rain",
            "event": "exam",
            "safety_level": 0.75,
        },
    )
    assert resp.status_code == 200
    rec = resp.json()

    assert isinstance(rec.get("kitchen_id"), str)
    assert isinstance(rec.get("slot"), str)
    assert isinstance(rec.get("date"), str)
    assert isinstance(rec.get("unit"), str)
    assert isinstance(rec.get("baseline"), int)
    assert isinstance(rec.get("recommended"), int) and rec["recommended"] > 0
    assert isinstance(rec.get("safety_level"), (int, float))
    assert isinstance(rec.get("reasons"), list)
    for r in rec["reasons"]:
        assert isinstance(r.get("factor"), str)
        assert isinstance(r.get("effect_pct"), (int, float))
    assert isinstance(rec.get("summary"), str)
    assert isinstance(rec.get("history"), list)
    assert isinstance(rec.get("model"), str)
    assert isinstance(rec.get("data_note"), str)

    # Optional v1.1 fields: WARN if missing, check invariant if present
    median = rec.get("forecast_median")
    margin = rec.get("safety_margin_pct")
    if median is None:
        print("WARN: optional field 'forecast_median' missing from /api/forecast/recommend")
    if margin is None:
        print("WARN: optional field 'safety_margin_pct' missing from /api/forecast/recommend")
    if median is not None:
        assert isinstance(median, int) and median > 0
        if margin is None or margin >= 0:
            assert rec["recommended"] >= median, (
                f"recommended ({rec['recommended']}) < forecast_median ({median})"
            )


def test_forecast_monotonic_safety_level(client):
    """recommended must be non-decreasing across safety_level 0.5, 0.55, ..., 0.95."""
    kitchen_id, slot = _get_first_kitchen_and_slot(client)
    levels = [round(0.5 + 0.05 * i, 2) for i in range(10)]  # 0.50 .. 0.95
    recs = []
    for lvl in levels:
        resp = client.post(
            "/api/forecast/recommend",
            json={
                "kitchen_id": kitchen_id,
                "slot": slot,
                "date": "2026-11-30",
                "weather": "rain",
                "event": "exam",
                "safety_level": lvl,
            },
        )
        assert resp.status_code == 200
        val = resp.json()["recommended"]
        assert isinstance(val, int) and val > 0
        recs.append(val)

    for i in range(len(levels) - 1):
        assert recs[i] <= recs[i + 1], (
            f"Non-monotonic: safety_level {levels[i]} -> {recs[i]} > "
            f"safety_level {levels[i+1]} -> {recs[i+1]}"
        )


def test_forecast_weekday_weekend_matches_date(client):
    """Weekday/weekend factors in reasons/summary must match the request date."""
    kitchen_id, slot = _get_first_kitchen_and_slot(client)

    # Monday 2026-11-30 must NOT report weekend/Saturday/Sunday
    r_mon = client.post(
        "/api/forecast/recommend",
        json={
            "kitchen_id": kitchen_id,
            "slot": slot,
            "date": "2026-11-30",
            "weather": "clear",
            "event": "none",
            "safety_level": 0.75,
        },
    )
    assert r_mon.status_code == 200
    mon = r_mon.json()
    mon_factors = " ".join(str(r.get("factor", "")) for r in mon.get("reasons", [])).lower()
    mon_summary = str(mon.get("summary", "")).lower()
    for bad in ("weekend", "saturday", "sunday"):
        assert bad not in mon_factors, f"Monday 2026-11-30 had '{bad}' in reasons: {mon['reasons']}"
        assert bad not in mon_summary, f"Monday 2026-11-30 had '{bad}' in summary: {mon['summary']}"

    # Saturday 2026-11-28 must NOT report weekday/Monday..Friday, and should reflect weekend
    r_sat = client.post(
        "/api/forecast/recommend",
        json={
            "kitchen_id": kitchen_id,
            "slot": slot,
            "date": "2026-11-28",
            "weather": "clear",
            "event": "none",
            "safety_level": 0.75,
        },
    )
    assert r_sat.status_code == 200
    sat = r_sat.json()
    sat_factors = " ".join(str(r.get("factor", "")) for r in sat.get("reasons", [])).lower()
    sat_summary = str(sat.get("summary", "")).lower()
    assert ("weekend" in sat_factors) or ("saturday" in sat_factors) or ("weekend" in sat_summary) or ("saturday" in sat_summary), (
        f"Saturday 2026-11-28 missing weekend/saturday factor: reasons={sat['reasons']}, summary={sat['summary']}"
    )


def test_forecast_metrics_shape(client):
    """GET /api/forecast/metrics returns expected shape and types."""
    kitchen_id, slot = _get_first_kitchen_and_slot(client)
    resp = client.get("/api/forecast/metrics", params={"kitchen_id": kitchen_id, "slot": slot})
    assert resp.status_code == 200
    m = resp.json()
    assert isinstance(m.get("baseline_mae"), (int, float))
    assert isinstance(m.get("model_mae"), (int, float))
    assert isinstance(m.get("history_count"), int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
