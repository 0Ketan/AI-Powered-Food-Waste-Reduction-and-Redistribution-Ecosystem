"""
Marketplace Module — Surplus food matching, claim/pickup/served flow, needs & pledges, alerts & impact.
Owner: M3
Importers: backend/app.py (auto-discovers via snake.json)
Affected API: GET/POST /api/marketplace/listings, GET /api/marketplace/nearby, POST /api/marketplace/listings/{id}/claim|pickup|served, GET/POST /api/marketplace/needs, POST /api/marketplace/needs/{id}/pledge, GET /api/alerts, POST /api/alerts/read, GET /api/impact
Data schemas: mkt_listings, mkt_claims, mkt_alerts, mkt_needs, mkt_pledges tables from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
from .router import router

__all__ = ["router"]