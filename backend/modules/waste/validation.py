"""
Waste Module Validation
Importers: backend/modules/waste/router.py
Affected API: POST /api/waste/log
"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import Request
from fastapi.responses import JSONResponse
import json
from pathlib import Path

# Load valid values from core data
CORE_JSON_PATH = Path(__file__).parent.parent.parent.parent / "data" / "seed" / "core.json"

def _load_core_data() -> dict:
    """Load core.json data."""
    with open(CORE_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# Valid values from core (GET /api/forecast/options)
_core_data = _load_core_data()
VALID_KITCHENS = {k["id"] for k in _core_data.get("kitchens", [])}
VALID_SLOTS = set(_core_data.get("slots", ["breakfast", "lunch", "dinner"]))


def validate_waste_log(body: dict) -> Optional[JSONResponse]:
    """
    Validate waste log request body.
    Returns JSONResponse error if invalid, None if valid.
    """
    # Check kitchen_id is required and present
    if "kitchen_id" not in body:
        return JSONResponse(
            status_code=400,
            content={"error": "missing_field", "message": "kitchen_id is required"}
        )

    kitchen_id = body.get("kitchen_id")
    if kitchen_id not in VALID_KITCHENS:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_kitchen", "message": f"Kitchen {kitchen_id} not found"}
        )

    # Validate slot if provided
    slot = body.get("slot")
    if slot is not None and slot not in VALID_SLOTS:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_slot", "message": f"Slot {slot} not found"}
        )

    # Validate date if provided
    date_str = body.get("date")
    if date_str is not None:
        try:
            date.fromisoformat(date_str)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_date", "message": "Date must be a valid calendar date in YYYY-MM-DD format"}
            )

    # Validate numeric fields - integers >= 0, no bool, no floats, no strings
    for field in ["prepared", "served", "leftover"]:
        value = body.get(field)
        if value is not None:
            # Reject bool (True/False count as 1/0 in Python)
            if isinstance(value, bool):
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_type", "message": f"{field} must be an integer, not boolean"}
                )
            if not isinstance(value, int):
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_type", "message": f"{field} must be an integer"}
                )
            if value < 0:
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_value", "message": f"{field} must be non-negative"}
                )

    # Validate ran_short is a real boolean
    ran_short = body.get("ran_short")
    if ran_short is not None and not isinstance(ran_short, bool):
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_type", "message": "ran_short must be a boolean"}
        )

    # Validate quantity_kg if provided
    quantity_kg = body.get("quantity_kg")
    if quantity_kg is not None:
        if isinstance(quantity_kg, bool):
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_type", "message": "quantity_kg must be a number, not boolean"}
            )
        if not isinstance(quantity_kg, (int, float)):
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_type", "message": "quantity_kg must be a number"}
            )
        if quantity_kg < 0:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_value", "message": "quantity_kg must be non-negative"}
            )

    return None


async def validate_json_body(request: Request) -> Optional[JSONResponse]:
    """
    Read and validate raw JSON body before FastAPI's automatic parsing.
    Returns JSONResponse error if invalid, None if valid or empty body.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_json", "message": "Request body must be valid JSON"}
        )

    if not isinstance(body, dict):
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_json", "message": "Request body must be a JSON object"}
        )

    return validate_waste_log(body)