"""
Safety Module Service Layer
Thin wrapper over db.py for use by router and tests.
Importers: backend/modules/safety/router.py
"""
from .db import (
    get_categories, get_category, evaluate_safety,
    create_disposal, get_records, get_disposals, complete_record
)

__all__ = [
    "get_categories", "get_category", "evaluate_safety",
    "create_disposal", "get_records", "get_disposals", "complete_record"
]
