"""
AnnaSetu AI — FastAPI Application Entry Point
Module auto-discovery via snake.json + demo clock + health + static frontend.
"""
import json
import importlib.util
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .core.clock import get_demo_time, get_offset_minutes, advance, reset
from .core.router import router as core_router


MODULES_DIR = Path(__file__).parent / "modules"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


def load_module_routes(app: FastAPI) -> None:
    """Auto-discover and register module routers from snake.json files."""
    for snake_path in sorted(MODULES_DIR.glob("*/snake.json")):
        module_dir = snake_path.parent
        module_name = module_dir.name

        # Load snake.json metadata
        with open(snake_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        # Import the module's router from __init__.py
        init_path = module_dir / "__init__.py"
        if not init_path.exists():
            print(f"[warn] {module_name}: no __init__.py, skipping")
            continue

        # Use full module path for proper relative imports
        spec = importlib.util.spec_from_file_location(f"backend.modules.{module_name}", init_path)
        if spec is None or spec.loader is None:
            print(f"[warn] {module_name}: could not load spec, skipping")
            continue

        module = importlib.util.module_from_spec(spec)
        # Add to sys.modules so relative imports work
        import sys
        sys.modules[f"backend.modules.{module_name}"] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"[warn] {module_name}: import failed: {e}")
            continue

        # Register router if present
        router = getattr(module, "router", None)
        if router:
            # Module routers already have their prefix (e.g., /waste, /safety)
            # Mount at /api to get /api/waste/log, /api/safety/categories, etc.
            app.include_router(router, prefix="/api", tags=[meta["name"]])
            print(f"[ok] mounted {meta['name']} at /api/{meta['name']} (owner: {meta['owner']})")
        else:
            print(f"[warn] {module_name}: no 'router' attribute in __init__.py")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[START] AnnaSetu AI starting up...")
    print("[OK] Startup complete")
    yield
    # Shutdown
    print("[STOP] AnnaSetu AI shutting down...")


app = FastAPI(
    title="AnnaSetu AI",
    description="Food Waste Reduction & Redistribution Ecosystem",
    version="0.1.0",
    lifespan=lifespan,
)

# Core router (users)
app.include_router(core_router)

# Register module routes at app creation time (not in lifespan) to avoid TestClient double-registration
load_module_routes(app)

# Demo Clock endpoints
@app.get("/api/demo/clock")
def demo_clock():
    """Get current demo time and offset."""
    return {
        "demo_time_utc": get_demo_time().isoformat(),
        "offset_minutes": get_offset_minutes(),
    }

@app.post("/api/demo/advance")
def demo_advance(minutes: int):
    """Advance demo clock by minutes."""
    new_offset = advance(minutes)
    return {"offset_minutes": new_offset, "demo_time_utc": get_demo_time().isoformat()}

@app.post("/api/demo/reset")
def demo_reset():
    """Reset demo clock offset to 0 and reseed data."""
    from .core.db import seed_database
    new_offset = reset()
    seed_database()
    return {"offset_minutes": new_offset, "demo_time_utc": get_demo_time().isoformat()}


@app.get("/api/demo/users")
def demo_users():
    """Get demo users (alias for /api/users)."""
    from .core.users import get_users_for_frontend
    return {"users": get_users_for_frontend()}


# Top-level alert and impact endpoints (also available under /api/marketplace/*)
@app.get("/api/alerts")
def alerts_top(user_id: str, since: str = None, unread_only: bool = False):
    """Get alerts for a user (top-level alias)."""
    from .modules.marketplace.db import get_alerts as _get_alerts
    return _get_alerts(user_id, since, unread_only)


@app.post("/api/alerts/read")
def alerts_read_top(payload: dict = None, user_id: str = None):
    """Mark all alerts as read (top-level alias)."""
    from .modules.marketplace.db import mark_alerts_read as _mark_read
    uid = (payload.get("user_id") if isinstance(payload, dict) else None) or user_id
    if not uid:
        return {"ok": False, "error": "user_id required"}
    return _mark_read(uid)


@app.get("/api/impact")
def impact_top(donor_id: str):
    """Get impact stats (top-level alias)."""
    from .modules.marketplace.db import get_impact as _get_impact
    return _get_impact(donor_id)


@app.get("/api/marketplace/claims")
def marketplace_claims(recipient_id: str = None, donor_id: str = None):
    """Get all marketplace claims."""
    from .core.db import get_connection
    conn = get_connection()
    try:
        if recipient_id:
            rows = conn.execute(
                "SELECT * FROM mkt_claims WHERE recipient_id = ? ORDER BY claimed_at DESC",
                (recipient_id,)
            ).fetchall()
        elif donor_id:
            rows = conn.execute(
                """SELECT c.* FROM mkt_claims c
                   JOIN mkt_listings l ON c.listing_id = l.id
                   WHERE l.donor_id = ? ORDER BY c.claimed_at DESC""",
                (donor_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM mkt_claims ORDER BY claimed_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

# Health check – at both /health (legacy) and /api/health (spec)
@app.get("/health")
@app.get("/api/health")
def health():
    """Health check: lists all four modules with their mode."""
    from .core.clock import get_demo_time
    return {
        "modules": {
            "forecast": "stub",
            "waste": "stub",
            "safety": "stub",
            "marketplace": "stub",
        },
        "services": {
            "core": "live",
            "forecast": "stub",
            "waste": "stub",
            "safety": "stub",
            "marketplace": "stub"
        },
        "server_time": get_demo_time().isoformat()
    }

# Mount frontend static files
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "AnnaSetu AI API", "docs": "/docs", "health": "/health"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)