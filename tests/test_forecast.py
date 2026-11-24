"""
Forecast Module Unit Tests
Importers: None (standalone test module)
Affected API: /forecast/options, /forecast/recommend, /forecast/metrics
Data schemas: forecast_history, forecast_baselines tables from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from backend.modules.forecast.db import (
    get_baseline, set_baseline, get_history, add_history_entry,
    get_all_kitchens, get_slots, get_weather_options, get_event_options,
    compute_adjustments, compute_mae
)
from backend.core.db import init_db, get_connection


@pytest.fixture(scope="module")
def setup_db():
    """Initialize test database."""
    init_db()
    yield


def test_get_all_kitchens(setup_db):
    """Test getting all kitchen configurations."""
    kitchens = get_all_kitchens()
    assert len(kitchens) > 0
    assert all("id" in k and "name" in k and "role" in k for k in kitchens)
    assert all(k["role"] == "kitchen" for k in kitchens)


def test_get_slots(setup_db):
    """Test getting meal slots."""
    slots = get_slots()
    assert slots == ["lunch", "dinner"]


def test_get_weather_options(setup_db):
    """Test getting weather options."""
    weather = get_weather_options()
    assert "clear" in weather
    assert "rain" in weather
    assert "hot" in weather
    assert "cloudy" in weather


def test_get_event_options(setup_db):
    """Test getting event options."""
    events = get_event_options()
    assert "none" in events
    assert "exam" in events
    assert "festival" in events
    assert "holiday" in events
    assert "sports" in events


def test_baseline_operations(setup_db):
    """Test getting and setting baselines."""
    kitchens = get_all_kitchens()
    kitchen_id = kitchens[0]["id"]

    # Get baseline (should have default)
    baseline = get_baseline(kitchen_id, "lunch")
    assert isinstance(baseline, int)
    assert baseline > 0

    # Set baseline
    set_baseline(kitchen_id, "lunch", 150)
    new_baseline = get_baseline(kitchen_id, "lunch")
    assert new_baseline == 150


def test_history_operations(setup_db):
    """Test forecast history operations."""
    kitchens = get_all_kitchens()
    kitchen_id = kitchens[0]["id"]

    # Add history entry
    add_history_entry(kitchen_id, "lunch", "2026-11-20", 120, 115)
    add_history_entry(kitchen_id, "lunch", "2026-11-21", 130, 125)

    # Get history
    history = get_history(kitchen_id, "lunch")
    assert len(history) >= 2
    assert all("predicted" in h and "actual" in h for h in history)


def test_compute_adjustments(setup_db):
    """Test adjustment computation."""
    from datetime import date

    # Test clear weather, no event, weekday
    total, reasons = compute_adjustments("clear", "none", date(2026, 11, 23))  # Monday
    assert total == 0
    assert len(reasons) == 0

    # Test rain
    total, reasons = compute_adjustments("rain", "none", date(2026, 11, 23))
    assert total == -6
    assert any(r["factor"] == "weather:rain" for r in reasons)

    # Test festival
    total, reasons = compute_adjustments("clear", "festival", date(2026, 11, 23))
    assert total == 15
    assert any(r["factor"] == "event:festival" for r in reasons)

    # Test weekend
    total, reasons = compute_adjustments("clear", "none", date(2026, 11, 28))  # Saturday
    assert total == -8
    assert any(r["factor"] == "weekend" for r in reasons)


def test_compute_mae(setup_db):
    """Test MAE computation."""
    kitchens = get_all_kitchens()
    kitchen_id = kitchens[0]["id"]

    # Add some history
    add_history_entry(kitchen_id, "dinner", "2026-11-22", 100, 95)
    add_history_entry(kitchen_id, "dinner", "2026-11-23", 100, 105)

    mae = compute_mae(kitchen_id, "dinner")
    assert mae == 5.0  # (5 + 5) / 2 = 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])