"""
Waste Module Service Layer
Thin wrapper over db.py for use by router and tests.
Importers: backend/modules/waste/router.py
"""
from .db import insert_log, get_logs, get_summary

__all__ = ["insert_log", "get_logs", "get_summary"]
