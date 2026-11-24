"""
Safety Module Router
Importers: backend/modules/safety/__init__.py, backend/app.py
Affected API: GET /api/safety/categories, POST /api/safety/evaluate, GET /api/safety/label/{label_id}/print, GET /api/safety/records, GET /api/safety/records.csv, GET /api/safety/disposals, POST /api/safety/records/{record_id}/complete
Data schemas: SafetyEvaluateIn/Out, DisposalIn; safety_records, safety_disposals tables; CATEGORIES list
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype
"""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from typing import Optional, List
from .db import get_categories, get_category, evaluate_safety, create_disposal, get_records, get_disposals, complete_record


router = APIRouter(prefix="/safety", tags=["safety"])


@router.get("/status")
def status():
    """Module status."""
    return {"module": "safety", "mode": "stub", "status": "ok"}


class SafetyEvaluateIn(BaseModel):
    donor_id: str
    item_name: str
    category_id: str
    veg: bool
    quantity: float = Field(gt=0)
    unit: str
    storage: str
    prepared_at: str
    kitchen_confirms_safe: bool
    pickup_buffer_minutes: int = Field(default=45, ge=0)


class SafetyEvaluateOut(BaseModel):
    decision: str
    reason: str
    consume_by: Optional[str] = None
    label_id: Optional[str] = None
    record_id: Optional[str] = None
    disposal_id: Optional[int] = None


class DisposalIn(BaseModel):
    donor_id: str
    item_name: str
    quantity: float = Field(gt=0)
    unit: str
    route: str
    reason: str


@router.get("/categories")
def categories():
    return get_categories()


@router.post("/evaluate", response_model=SafetyEvaluateOut)
def evaluate(payload: SafetyEvaluateIn):
    return evaluate_safety(
        payload.donor_id, payload.item_name, payload.category_id, payload.veg,
        payload.quantity, payload.unit, payload.storage, payload.prepared_at,
        payload.kitchen_confirms_safe, payload.pickup_buffer_minutes
    )


@router.get("/label/{label_id}/print")
def print_label(label_id: str):
    html = f"""<!DOCTYPE html>
<html><head><title>Food Safety Label</title>
<style>body{{font-family:monospace;padding:20px;max-width:400px;margin:0 auto;}}
.label{{border:2px solid #333;padding:15px;}}.header{{text-align:center;font-weight:bold;font-size:18px;margin-bottom:10px;}}
.field{{display:flex;justify-content:space-between;margin:5px 0;}}.key{{font-weight:bold;}}
.warning{{color:red;font-weight:bold;text-align:center;margin-top:10px;}}</style></head>
<body><div class="label"><div class="header">ANNASETU FOOD SAFETY LABEL</div>
<div class="field"><span class="key">Label ID:</span><span>{label_id}</span></div>
<div class="field"><span class="key">Item:</span><span>Demo Item</span></div>
<div class="field"><span class="key">Prepared:</span><span>{__import__('core.clock').clock.get_demo_time().strftime('%Y-%m-%d %H:%M UTC')}</span></div>
<div class="field"><span class="key">Consume By:</span><span>TBD</span></div>
<div class="field"><span class="key">Storage:</span><span>Refrigerated</span></div>
<div class="warning">⚠ CONSUME BEFORE EXPIRY TIME</div></div></body></html>"""
    return Response(content=html, media_type="text/html")


@router.get("/records")
def records(donor_id: Optional[str] = None):
    return get_records(donor_id)


@router.get("/records.csv")
def records_csv(donor_id: Optional[str] = None):
    records = get_records(donor_id)
    if not records:
        return Response(content="record_id,donor_id,item_name,quantity,unit,expiry_or_consume_by,quantity_distributed,distribution_date\n", media_type="text/csv")
    lines = ["record_id,donor_id,item_name,quantity,unit,expiry_or_consume_by,quantity_distributed,distribution_date"]
    for r in records:
        lines.append(f"{r['record_id']},{r['donor_id']},{r['item_name']},{r['quantity_donated']},{r['unit']},{r['expiry_or_consume_by']},{r['quantity_distributed']},{r['distribution_date'] or ''}")
    return Response(content="\n".join(lines), media_type="text/csv")


@router.get("/disposals")
def disposals(donor_id: Optional[str] = None):
    return get_disposals(donor_id)


@router.post("/records/{record_id}/complete")
def complete_record_endpoint(record_id: str):
    complete_record(record_id)
    return {"ok": True, "record_id": record_id}


@router.post("/disposals")
def create_disposal_endpoint(payload: DisposalIn):
    disposal_id = create_disposal(payload.donor_id, payload.item_name, payload.quantity, payload.unit, payload.route, payload.reason)
    return {"ok": True, "disposal_id": disposal_id}