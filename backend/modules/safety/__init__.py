"""
Safety Module — Food safety evaluation, label generation, donation/disposal records.
Owner: M1
Importers: backend/app.py (auto-discovers via snake.json)
Affected API: GET /api/safety/categories, POST /api/safety/evaluate, GET /api/safety/label/{label_id}/print, GET /api/safety/records, GET /api/safety/records.csv, GET /api/safety/disposals, POST /api/safety/records/{record_id}/complete
Data schemas: safety_records, safety_disposals tables from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from .router import router

__all__ = ["router"]