# CLAUDE.md - AnnaSetu AI Project Guide for Claude Code

> **Read and obey AGENTS.md** before writing any code for this repository.
>
## Project Overview
AnnaSetu AI: AI-Powered Food Waste Reduction and Redistribution Ecosystem - Hackathon Prototype

## Architecture
- **Framework**: FastAPI + uvicorn
- **Database**: SQLite (stdlib sqlite3, no ORM)
- **Frontend**: Single HTML file served as static files
- **Modules**: Auto-discovery via snake.json in each module directory
- **Clock**: Demo clock with SQLite persistence for testing expiry/alerts

## Module Ownership (Zero-Conflict)
| Module | Owner | Paths |
|--------|-------|-------|
| Core | M1 | backend/core/**, backend/app.py |
| Waste | M2 | backend/modules/waste/** |
| Safety | M1 | backend/modules/safety/** |
| Forecast | M2 | backend/modules/forecast/** |
| Marketplace | M3 | backend/modules/marketplace/** |
| Frontend | M1 | frontend/** |
| Contracts | M1 | contracts/** |
| Scripts | M1/M3 | scripts/** |
| Tests | All | tests/test_<module>.py |

## Key Rules
1. **Modules NEVER import each other** - only `backend.core` and `contracts`
2. **Shared contracts** - Only M1 edits `contracts/API.md` and `contracts/FLOWS.md`
3. **Database schema** - Only M1 edits `backend/core/db.py`
4. **Run ownership check**: `python scripts/check_ownership.py` before committing

## Commands
```bash
# Start server
python run.py

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-ml.txt  # ML libs for forecast only

# Run tests
python -m pytest tests/ -v
python tests/smoke_test.py

# Check ownership
python scripts/check_ownership.py

# Fetch vendor (frontend)
python scripts/fetch_vendor.py
```

## API Endpoints (per contracts/API.md)
- Core: /health, /clock, /users
- Waste: /waste/log, /waste/logs, /waste/summary
- Safety: /safety/categories, /safety/evaluate, /safety/records, /safety/disposals
- Forecast: /forecast/options, /forecast/recommend, /forecast/metrics
- Marketplace: /marketplace/*

## Data Flow
Frontend orchestrates multi-module flows per contracts/FLOWS.md:
1. Waste logging → Safety evaluation → Marketplace listing
2. Forecast recommendation → Waste reduction planning
3. Need creation → Pledge → Listing → Claim/Pickup/Serve

## Demo Clock
- `GET /clock` - Returns demo time with offset
- `POST /clock/advance` - Adds hours for expiry testing
- `POST /clock/reset` - Resets to real time
- Stored in SQLite `demo_clock` table

## Testing
- Unit tests: `tests/test_<module>.py` (pytest)
- Smoke test: `tests/smoke_test.py` (starts/stops server)
- All tests must pass before merge