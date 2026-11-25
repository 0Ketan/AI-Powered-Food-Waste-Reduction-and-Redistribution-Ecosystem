"""
Forecast Simulation Module
Importers: backend/modules/forecast/db.py (for seeding)
Affected API: data/seed/forecast.json (120 days historical data)
Data schemas: history entries with kitchen_id, date, slot, actual, predicted
User instruction: Generate 120 days of simulated demand data per kitchen/slot
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Default seed for reproducibility
DEFAULT_SEED = 42

# Event and weather patterns that affect demand
EVENT_IMPACTS = {
    "exam": -10,      # Less attendance, lower demand
    "festival": 15,   # Higher attendance, special meals
    "holiday": -20,   # Very low attendance
    "sports": 5,      # Sports event day, slightly higher
    "normal": 0,
}

WEATHER_IMPACTS = {
    "sunny": 0,
    "cloudy": -2,
    "rain": -6,
    "hot": 3,
}

# Known exam dates for IIT Delhi (approximate)
EXAM_DATES = [
    "2026-11-15", "2026-11-16", "2026-11-17",  # Nov exams
    "2026-12-02", "2026-12-03", "2026-12-04",  # Dec exams
]

# Known festival dates (Diwali, Holi, etc. - approximate)
FESTIVAL_DATES = [
    "2026-10-31",  # Diwali
    "2026-03-25",  # Holi
    "2026-08-27",  # Raksha Bandhan
    "2026-09-28",  # Ganesh Chaturthi
]

# Known holidays (official + popular)
HOLIDAY_DATES = [
    "2026-11-26", "2026-11-27",  # Weekend days checked dynamically
    "2026-10-31",  # Diwali
    "2026-07-20",  # Guru Nanak Jayanti
    "2026-08-15",  # Independence Day
]


def get_date_type(date_str: str) -> str:
    """Determine if date is a weekday, exam, festival, or holiday."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = dt.weekday()

    # Weekend: Saturday (5) or Sunday (6)
    if weekday >= 5:
        return "weekend"

    # Check holidays
    if date_str in HOLIDAY_DATES:
        return "holiday"

    # Check festivals
    if date_str in FESTIVAL_DATES:
        return "festival"

    # Check exams
    if date_str in EXAM_DATES:
        return "exam"

    return "weekday"


def get_weather_for_date(date_str: str, rng: random.Random) -> str:
    """Get simulated weather for a date with seasonal patterns."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    month = dt.month

    # Summer (Mar-Jun): hotter, some rain
    # Monsoon (Jun-Sep): more rain
    # Winter (Oct-Dec): clearer
    # Spring (Jan-Feb): variable

    if month in [3, 4, 5, 6]:
        # Summer - hot days, some pre-monsoon rain
        weights = [0.25, 0.15, 0.35, 0.25]  # sunny, cloudy, rain, hot
    elif month in [7, 8, 9]:
        # Monsoon - rainy season
        weights = [0.15, 0.20, 0.50, 0.15]
    elif month in [10, 11, 12]:
        # Winter - clear days
        weights = [0.50, 0.25, 0.15, 0.10]
    else:
        # Jan, Feb - spring, variable
        weights = [0.35, 0.25, 0.20, 0.20]

    weather_pool = ["sunny", "cloudy", "rain", "hot"]
    return rng.choices(weather_pool, weights=weights, k=1)[0]


def simulate_day_demand(
    kitchen_id: str,
    kitchen_base: int,
    slot: str,
    date_str: str,
    rng: random.Random
) -> Dict[str, Any]:
    """Simulate demand for a single day with all factors combined."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = dt.weekday()

    # Start with baseline
    baseline = kitchen_base

    # 1. Weekend penalty (-25% on average)
    adjustments = {"weekday": 0, "weekend": -25}
    total_adj = adjustments.get(get_date_type(date_str), 0)

    # 2. Event adjustments
    if date_str in EXAM_DATES:
        total_adj += EVENT_IMPACTS["exam"]
    if date_str in FESTIVAL_DATES:
        total_adj += EVENT_IMPACTS["festival"]
    if date_str in HOLIDAY_DATES:
        total_adj += EVENT_IMPACTS["holiday"]

    # 3. Weather (deterministic from date for reproducibility)
    weather = get_weather_for_date(date_str, rng)
    total_adj += WEATHER_IMPACTS[weather]

    # 4. Slot factor (dinner is busier than lunch)
    slot_factor = 1.0
    if slot == "dinner":
        slot_factor = 1.15  # 15% more for dinner typically
    elif slot == "breakfast":
        slot_factor = 0.75  # 25% less for breakfast

    # Calculate predicted (with safety margin like the stub)
    # Apply adjustments and slot factor
    predicted = int(round(baseline * (1 + total_adj / 100) * slot_factor))

    # Add noise (±5-10% around prediction)
    noise_pct = rng.uniform(-0.08, 0.08)
    actual = max(0, int(round(predicted * (1 + noise_pct))))

    # Occasionally predicted won't match actual (for testing metrics)
    if rng.random() < 0.1:  # 10% chance
        actual = max(0, predicted + rng.randint(-15, 15))

    return {
        "date": date_str,
        "predicted": predicted,
        "actual": actual,
        "weather": weather,
    }


def generate_120_days(
    kitchen_id: str,
    kitchen_base: int,
    slots: List[str],
    start_date: Optional[str] = None,
    seed_offset: int = 0,
) -> List[Dict[str, Any]]:
    """Generate 120 days of simulated data for a kitchen/slot combination."""
    # Create deterministic seed per kitchen
    rng = random.Random(DEFAULT_SEED + seed_offset)

    if start_date is None:
        # Use a fixed reference date for determinism
        # Start from 120 days before a known stable date (Jan 1, 2027 for demo purposes)
        reference_date = datetime(2027, 1, 1)
        start = reference_date - timedelta(days=120)
        start_date = start.strftime("%Y-%m-%d")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    history = []

    for slot in slots:
        for day_offset in range(120):
            current_date = start_dt + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")

            day_data = simulate_day_demand(
                kitchen_id, kitchen_base, slot, date_str, rng
            )

            entry = {
                "kitchen_id": kitchen_id,
                "date": date_str,
                "slot": slot,
                "actual": day_data["actual"],
                "predicted": day_data["predicted"],
            }
            history.append(entry)

    return history


def generate_full_simulation() -> Dict[str, Any]:
    """Generate complete 120 days of data for all kitchens and slots."""
    # Kitchen configurations: kitchen_id -> base meal count
    # Based on core.json kitchen capacities
    kitchens = {
        "1": {"name": "Boys Hostel 1 Mess", "base": 180, "slots": ["lunch", "dinner"]},
        "2": {"name": "Girls Hostel 1 Mess", "base": 145, "slots": ["lunch", "dinner"]},
        "3": {"name": "PG Hostel Mess", "base": 95, "slots": ["lunch", "dinner"]},
    }

    all_history = []
    all_baselines = {}

    for kitchen_id, config in kitchens.items():
        seed_offset = int(kitchen_id) * 1000  # Different seed per kitchen
        history = generate_120_days(
            kitchen_id=kitchen_id,
            kitchen_base=config["base"],
            slots=config["slots"],
            seed_offset=seed_offset,
        )

        all_history.extend(history)
        all_baselines[kitchen_id] = {
            "lunch": config["base"],
            "dinner": int(round(config["base"] * 1.15))
        }

    return {
        "history": all_history,
        "baselines": all_baselines,
    }


def write_simulation_output(output_path: Path):
    """Generate and write simulation data to forecast.json."""
    data = generate_full_simulation()

    # Ensure file size stays under 2MB by limiting to 120 days total per kitchen-slot
    # With 120 days * 2 slots * 3 kitchens = 720 entries, should be well under 2MB

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Check file size
    file_size = output_path.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"Wrote {len(data['history'])} entries to {output_path}")
    print(f"File size: {size_mb:.2f} MB (limit: 2 MB)")

    if size_mb > 2:
        raise ValueError(f"File size {size_mb:.2f} MB exceeds 2 MB limit!")

    return output_path


if __name__ == "__main__":
    # Generate simulation data
    # Path is: simulate.py -> forecast/ -> backend/modules/ -> backend/ -> project_root/data/seed/
    output_path = Path(__file__).parent.parent.parent.parent / "data" / "seed" / "forecast.json"

    print(f"Generating 120 days of simulated data per kitchen/slot...")
    print(f"Output path: {output_path}")

    write_simulation_output(output_path)
    print("Simulation complete!")