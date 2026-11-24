"""
Forecast Module (M2) — Cooking quantity recommendation engine with baseline + adjustments.
Endpoints: /forecast/options, /forecast/recommend, /forecast/metrics
"""
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/status")
def status():
    """Module status."""
    return {"module": "forecast", "mode": "stub", "status": "ok"}


DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "seed"


class RecommendRequest(BaseModel):
    kitchen_id: str
    slot: str
    date: date
    weather: Optional[str] = "clear"
    event: Optional[str] = "none"
    safety_level: float = Field(default=0.75, ge=0.0, le=1.0)


class RecommendResponse(BaseModel):
    kitchen_id: str
    slot: str
    date: str
    unit: str = "plates"
    baseline: int
    recommended: int
    safety_level: float
    reasons: list[dict]
    summary: str
    history: list[dict]
    model: str = "stub"
    data_note: str = "Simulated data"


class OptionsResponse(BaseModel):
    kitchens: list[dict]
    slots: list[str]
    weather_options: list[str]
    event_options: list[str]


class MetricsResponse(BaseModel):
    baseline_mae: float
    model_mae: float
    history_count: int


def load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_baseline(kitchen_id: str, slot: str) -> int:
    data = load_json("forecast.json")
    return data.get("baselines", {}).get(kitchen_id, {}).get(slot, 100)


def get_history(kitchen_id: str, slot: str, limit: int = 7) -> list[dict]:
    data = load_json("forecast.json")
    history = [
        h for h in data.get("history", [])
        if h["kitchen_id"] == kitchen_id and h["slot"] == slot
    ]
    history.sort(key=lambda x: x["date"], reverse=True)
    return history[:limit]


def compute_adjustments(weather: str, event: str, target_date: date) -> tuple[float, list[dict]]:
    """Return (total_adjustment_pct, reasons_list)."""
    adjustments = {
        "weather": {"clear": 0, "cloudy": 0, "rain": -6, "hot": 3},
        "event": {"none": 0, "exam": -10, "festival": 15, "holiday": -20, "sports": 5},
    }
    reasons = []
    total = 0

    # Day of week adjustment
    if target_date.weekday() == 5:  # Saturday
        total += -8
        reasons.append({"factor": "weekend", "effect_pct": -8})
    elif target_date.weekday() == 6:  # Sunday
        total += -8
        reasons.append({"factor": "weekend", "effect_pct": -8})

    # Weather
    w = adjustments["weather"].get(weather, 0)
    if w != 0:
        total += w
        reasons.append({"factor": f"weather:{weather}", "effect_pct": w})

    # Event
    e = adjustments["event"].get(event, 0)
    if e != 0:
        total += e
        reasons.append({"factor": f"event:{event}", "effect_pct": e})

    return total, reasons


def compute_mae(kitchen_id: str, slot: str) -> float:
    data = load_json("forecast.json")
    history = [
        h for h in data.get("history", [])
        if h["kitchen_id"] == kitchen_id and h["slot"] == slot
    ]
    if not history:
        return 0.0
    baseline = get_baseline(kitchen_id, slot)
    errors = [abs(h["actual"] - baseline) for h in history]
    return sum(errors) / len(errors)


@router.get("/options", response_model=OptionsResponse)
def options():
    core = load_json("core.json")
    return OptionsResponse(
        kitchens=core.get("kitchens", []),
        slots=core.get("slots", []),
        weather_options=core.get("weather_options", []),
        event_options=core.get("event_options", []),
    )


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    # Validate kitchen exists
    core = load_json("core.json")
    kitchen_ids = [k["id"] for k in core.get("kitchens", [])]
    if req.kitchen_id not in kitchen_ids:
        raise HTTPException(404, f"Kitchen {req.kitchen_id} not found")

    baseline = get_baseline(req.kitchen_id, req.slot)
    total_adj, reasons = compute_adjustments(req.weather, req.event, req.date)
    recommended = int(round(baseline * (1 + total_adj / 100) * req.safety_level))
    recommended = max(0, recommended)

    history = get_history(req.kitchen_id, req.slot)

    # Build summary string
    summary_parts = []
    for r in reasons:
        sign = "+" if r["effect_pct"] > 0 else ""
        summary_parts.append(f"{sign}{r['effect_pct']}%: {r['factor']}")
    summary = ", ".join(summary_parts) if summary_parts else "No adjustments"

    return RecommendResponse(
        kitchen_id=req.kitchen_id,
        slot=req.slot,
        date=str(req.date),
        baseline=baseline,
        recommended=recommended,
        safety_level=req.safety_level,
        reasons=reasons,
        summary=summary,
        history=history,
    )


@router.get("/metrics", response_model=MetricsResponse)
def metrics(
    kitchen_id: str = Query(...),
    slot: str = Query(...),
):
    core = load_json("core.json")
    kitchen_ids = [k["id"] for k in core.get("kitchens", [])]
    if kitchen_id not in kitchen_ids:
        raise HTTPException(404, f"Kitchen {kitchen_id} not found")

    history = [
        h for h in load_json("forecast.json").get("history", [])
        if h["kitchen_id"] == kitchen_id and h["slot"] == slot
    ]

    baseline_mae = compute_mae(kitchen_id, slot)
    # For stub, model MAE = baseline MAE (no ML model yet)
    return MetricsResponse(
        baseline_mae=round(baseline_mae, 2),
        model_mae=round(baseline_mae, 2),
        history_count=len(history),
    )