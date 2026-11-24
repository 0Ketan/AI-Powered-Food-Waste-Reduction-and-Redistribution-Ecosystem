"""
Forecast Module Router
Importers: backend/modules/forecast/__init__.py, backend/app.py
Affected API: GET /forecast/options, POST /forecast/recommend, GET /forecast/metrics
Data schemas: forecast_history, forecast_baselines tables from core/db.py; RecommendRequest/Response, OptionsResponse, MetricsResponse models
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from .db import (
    get_baseline, get_history, add_history_entry,
    get_all_kitchens, get_slots, get_weather_options, get_event_options,
    compute_adjustments, compute_mae
)


router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/status")
def status():
    """Module status."""
    return {"module": "forecast", "mode": "stub", "status": "ok"}


# ============================================================
# Request/Response Models
# ============================================================

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
    reasons: List[dict]
    summary: str
    history: List[dict]
    model: str = "stub"
    data_note: str = "Simulated data"


class OptionsResponse(BaseModel):
    kitchens: List[dict]
    slots: List[str]
    weather_options: List[str]
    event_options: List[str]


class MetricsResponse(BaseModel):
    baseline_mae: float
    model_mae: float
    history_count: int


# ============================================================
# Endpoints
# ============================================================

@router.get("/options", response_model=OptionsResponse)
def options():
    """Get available options for forecast requests."""
    kitchens = get_all_kitchens()
    return OptionsResponse(
        kitchens=kitchens,
        slots=get_slots(),
        weather_options=get_weather_options(),
        event_options=get_event_options(),
    )


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    """Get cooking quantity recommendation."""
    # Validate kitchen exists
    kitchens = get_all_kitchens()
    kitchen_ids = [k["id"] for k in kitchens]
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
    """Get forecast accuracy metrics."""
    kitchens = get_all_kitchens()
    kitchen_ids = [k["id"] for k in kitchens]
    if kitchen_id not in kitchen_ids:
        raise HTTPException(404, f"Kitchen {kitchen_id} not found")

    history = get_history(kitchen_id, slot)
    baseline_mae = compute_mae(kitchen_id, slot)
    # For stub, model MAE = baseline MAE (no ML model yet)
    return MetricsResponse(
        baseline_mae=round(baseline_mae, 2),
        model_mae=round(baseline_mae, 2),
        history_count=len(history),
    )