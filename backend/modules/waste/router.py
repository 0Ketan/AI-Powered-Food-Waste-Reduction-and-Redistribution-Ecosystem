"""
Waste Module Router
Importers: backend/modules/waste/__init__.py (imports router), backend/app.py (auto-discovers via snake.json)
Affected API: POST /api/waste/log, GET /api/waste/logs, GET /api/waste/summary
Data schemas: WasteLogIn, WasteLogOut Pydantic models; waste_logs table from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from .db import insert_log, get_logs, get_summary


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


@router.post("/logs", response_model=WasteLogOut)
@router.post("/log", response_model=WasteLogOut)
def log_waste(payload: WasteLogIn):
    """Log daily waste for a kitchen/slot."""
    from backend.core.clock import get_demo_time
    date_val = payload.date or get_demo_time().date().isoformat()
    slot_val = payload.slot or "lunch"
    
    prepared = payload.prepared or 0
    served = payload.served or 0
    leftover = payload.leftover or 0
    
    if payload.quantity_kg and prepared == 0:
        prepared = int(payload.quantity_kg)
        leftover = int(payload.quantity_kg)
        served = 0
    elif prepared > 0 and (served + leftover != prepared) and not payload.quantity_kg:
        raise HTTPException(status_code=400, detail="served + leftover must equal prepared")
        
    insert_log(
        payload.kitchen_id, date_val, slot_val,
        prepared, served, leftover, bool(payload.ran_short)
    )
    return {"ok": True, "id": 1, "log_id": "wst_1"}


@router.get("/logs")
def list_logs(kitchen_id: Optional[str] = None, limit: int = Query(50, le=200)):
    """List waste logs."""
    raw_logs = get_logs(kitchen_id, limit)
    # Return dict with 'logs' key for schemas/smoke_test compatibility
    return {"logs": raw_logs}


@router.get("/summary")
def summary(kitchen_id: Optional[str] = None):
    """Get aggregate waste summary."""
    return get_summary(kitchen_id)