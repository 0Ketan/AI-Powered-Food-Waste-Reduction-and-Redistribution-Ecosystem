"""
Waste Module — Daily waste logging and summary statistics per kitchen/slot.
Owner: M2
Endpoints:
  POST /api/waste/log
  GET  /api/waste/logs
  GET  /api/waste/summary
"""
from .router import router

__all__ = ["router"]