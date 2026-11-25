"""
Waste Module Router
Importers: backend/modules/waste/__init__.py (imports router), backend/app.py (auto-discovers via snake.json)
Affected API: POST /api/waste/log, GET /api/waste/logs, GET /api/waste/summary
Data schemas: WasteLogIn, WasteLogOut Pydantic models; waste_logs table from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from .db import insert_log, get_logs, get_summary
from .validation import validate_waste_log, VALID_KITCHENS, VALID_SLOTS


router = APIRouter(prefix="/waste", tags=["waste"])


@router.get("/status")
def status():
    """Module status."""
    return {"module": "waste", "mode": "stub", "status": "ok"}


class WasteLogIn(BaseModel):
    kitchen_id: str
    date: Optional[str] = None
    slot: Optional[str] = "lunch"
    prepared: Optional[int] = 0
    served: Optional[int] = 0
    leftover: Optional[int] = 0
    ran_short: Optional[bool] = False
    item_name: Optional[str] = None
    quantity_kg: Optional[float] = None
    category: Optional[str] = None
    reason: Optional[str] = None
    disposal_method: Optional[str] = None


class WasteLogOut(BaseModel):
    ok: bool = True
    id: int = 1
    log_id: str = "wst_1"


def _make_error_response(error_code: str, message: str, status_code: int = 400) -> JSONResponse:
    """Create error response in the contract's shape."""
    return JSONResponse(
        status_code=status_code,
        content={"error": error_code, "message": message}
    )


@router.post("/logs", response_model=WasteLogOut)
@router.post("/log", response_model=WasteLogOut)
async def log_waste(request: Request):
    """Log daily waste for a kitchen/slot."""
    from backend.core.clock import get_demo_time

    # Read raw JSON body to validate before FastAPI's auto-parsing
    try:
        body = await request.json()
    except Exception:
        return _make_error_response("invalid_json", "Request body must be valid JSON")

    if not isinstance(body, dict):
        return _make_error_response("invalid_json", "Request body must be a JSON object")

    # Validate using shared validation function
    validation_error = validate_waste_log(body)
    if validation_error:
        return validation_error

    # Additional validation for served + leftover == prepared (stub rule)
    prepared = body.get("prepared", 0)
    served = body.get("served", 0)
    leftover = body.get("leftover", 0)
    quantity_kg = body.get("quantity_kg")

    if quantity_kg and prepared == 0:
        prepared = int(quantity_kg)
        leftover = int(quantity_kg)
        served = 0
    elif prepared > 0 and (served + leftover != prepared) and not quantity_kg:
        return _make_error_response("invalid_value", "served + leftover must equal prepared")

    try:
        insert_log(
            body["kitchen_id"],
            body.get("date") or get_demo_time().date().isoformat(),
            body.get("slot", "lunch"),
            prepared,
            served,
            leftover,
            bool(body.get("ran_short", False))
        )
    except Exception as e:
        return _make_error_response("server_error", f"Failed to store waste log: {str(e)}", 500)

    return {"ok": True, "id": 1, "log_id": "wst_1"}


@router.get("/logs")
def list_logs(kitchen_id: Optional[str] = None, limit: str = Query("50", description="Limit for results")):
    """List waste logs."""

    # Validate limit is a positive integer - first validate format via string length
    if len(limit) > 10:  # Max reasonable is 200, so anything longer than 10 chars is too big
        return _make_error_response("invalid_limit", "limit must be a positive integer")

    # Validate limit is a positive integer
    try:
        limit_int = int(limit)
        if limit_int < 1:
            return _make_error_response("invalid_limit", "limit must be a positive integer")
        if limit_int > 200:
            limit_int = 200
    except (ValueError, TypeError):
        return _make_error_response("invalid_limit", "limit must be a positive integer")

    if kitchen_id is not None and kitchen_id not in VALID_KITCHENS:
        return _make_error_response("invalid_kitchen", f"Kitchen {kitchen_id} not found")

    raw_logs = get_logs(kitchen_id, limit_int)
    # Return dict with 'logs' key for schemas/smoke_test compatibility
    return {"logs": raw_logs}


@router.get("/summary")
def summary(kitchen_id: Optional[str] = None):
    """Get aggregate waste summary."""
    if kitchen_id is not None and kitchen_id not in VALID_KITCHENS:
        return _make_error_response("invalid_kitchen", f"Kitchen {kitchen_id} not found")
    return get_summary(kitchen_id)