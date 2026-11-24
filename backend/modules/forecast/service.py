"""
Forecast Module Service Layer
Importers: backend/modules/forecast/router.py
Affected API: GET /forecast/options, POST /forecast/recommend, GET /forecast/metrics
Data schemas: forecast_history, forecast_baselines tables from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from typing import Optional, List, Dict
from datetime import date
from .db import (
    get_baseline, get_history, add_history_entry,
    get_all_kitchens, get_slots, get_weather_options, get_event_options,
    compute_adjustments, compute_mae
)


class ForecastService:
    """Business logic for forecast operations."""

    @staticmethod
    def get_options() -> Dict:
        """Get all available options for forecast requests."""
        return {
            "kitchens": get_all_kitchens(),
            "slots": get_slots(),
            "weather_options": get_weather_options(),
            "event_options": get_event_options(),
        }

    @staticmethod
    def recommend(kitchen_id: str, slot: str, target_date: date,
                  weather: str = "clear", event: str = "none",
                  safety_level: float = 0.75) -> Dict:
        """Get cooking quantity recommendation."""
        # Validate kitchen exists
        kitchens = get_all_kitchens()
        kitchen_ids = [k["id"] for k in kitchens]
        if kitchen_id not in kitchen_ids:
            raise ValueError(f"Kitchen {kitchen_id} not found")

        baseline = get_baseline(kitchen_id, slot)
        total_adj, reasons = compute_adjustments(weather, event, target_date)
        recommended = int(round(baseline * (1 + total_adj / 100) * safety_level))
        recommended = max(0, recommended)

        history = get_history(kitchen_id, slot)

        # Build summary string
        summary_parts = []
        for r in reasons:
            sign = "+" if r["effect_pct"] > 0 else ""
            summary_parts.append(f"{sign}{r['effect_pct']}%: {r['factor']}")
        summary = ", ".join(summary_parts) if summary_parts else "No adjustments"

        return {
            "kitchen_id": kitchen_id,
            "slot": slot,
            "date": str(target_date),
            "unit": "plates",
            "baseline": baseline,
            "recommended": recommended,
            "safety_level": safety_level,
            "reasons": reasons,
            "summary": summary,
            "history": history,
            "model": "stub",
            "data_note": "Simulated data"
        }

    @staticmethod
    def get_metrics(kitchen_id: str, slot: str) -> Dict:
        """Get forecast accuracy metrics."""
        kitchens = get_all_kitchens()
        kitchen_ids = [k["id"] for k in kitchens]
        if kitchen_id not in kitchen_ids:
            raise ValueError(f"Kitchen {kitchen_id} not found")

        history = get_history(kitchen_id, slot)
        baseline_mae = compute_mae(kitchen_id, slot)

        return {
            "baseline_mae": round(baseline_mae, 2),
            "model_mae": round(baseline_mae, 2),  # For stub, model MAE = baseline MAE
            "history_count": len(history)
        }

    @staticmethod
    def record_actual(kitchen_id: str, slot: str, target_date: date,
                      predicted: int, actual: int):
        """Record actual consumption for metrics tracking."""
        add_history_entry(kitchen_id, slot, str(target_date), predicted, actual)