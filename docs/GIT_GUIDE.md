# AnnaSetu AI - Git Guide
Importers: None (documentation)
Affected API: None (documentation)
Data schemas: OWNERS.json
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification

## Overview
This guide documents the Git workflow for the AnnaSetu AI hackathon prototype to ensure zero merge conflicts via strict ownership.

## Branch Strategy
- `main` - Stable, demo-ready code (protected)
- `master` - Development branch (current)
- Feature branches: `M1/feature-name`, `M2/feature-name`, `M3/feature-name`

## Ownership Model (Zero-Conflict)

### M1 (Lead) - Core, Frontend, Safety
**Owns:**
- `backend/app.py`
- `backend/core/**`
- `frontend/**`
- `backend/modules/safety/**`
- `contracts/API.md`
- `contracts/FLOWS.md`
- `docs/DEMO_SCRIPT.md`
- `docs/TEST_CHECKLIST.md`
- `scripts/check_ownership.py`
- `requirements.txt`
- `README.md`

### M2 - Forecast, Waste
**Owns:**
- `backend/modules/forecast/**`
- `backend/modules/waste/**`
- `requirements-ml.txt`
- `data/seed/forecast.json`
- `data/seed/waste.json`

### M3 - Marketplace
**Owns:**
- `backend/modules/marketplace/**`
- `data/seed/marketplace.json`
- `scripts/fetch_vendor.py`

## Workflow Rules

### 1. Never Edit Another Member's Files
- Check `OWNERS.json` before editing
- Run `python scripts/check_ownership.py` before committing

### 2. Create Feature Branches
```bash
# M1 example
git checkout -b M1/add-frontend-dashboard

# M2 example
git checkout -b M2/improve-forecast-model

# M3 example
git checkout -b M3/add-marketplace-alerts
```

### 3. Commit Messages
Follow conventional commits:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Scopes: `core`, `waste`, `safety`, `forecast`, `marketplace`, `frontend`, `contracts`, `docs`, `scripts`

Examples:
```
feat(safety): add conditional decision for hot food
fix(forecast): correct MAE calculation for empty history
docs(contracts): update API.md with new endpoints
```

### 4. Pull Request Process
1. Push feature branch
2. Create PR to `main`
3. CI runs: ownership check + smoke test
4. Code review (if needed)
5. Squash and merge to `main`

### 5. Merge Conflicts Prevention
- **Modules NEVER import each other** - only `backend.core` and `contracts`
- **Shared contracts** - Only M1 edits `contracts/API.md` and `contracts/FLOWS.md`
- **Database schema** - Only M1 edits `backend/core/db.py` (tables defined there)
- **Frontend** - Only M1 edits `frontend/**`

## Module Auto-Discovery
Each module has a `snake.json` that registers its routes:
```json
{
  "name": "waste",
  "prefix": "/waste",
  "router_module": "backend.modules.waste.router",
  "router_attr": "router"
}
```
App auto-discovers and includes all routers.

## Demo Clock
- Stored in SQLite (`demo_clock` table)
- `GET /clock` returns current demo time
- `POST /clock/advance` adds hours
- `POST /clock/reset` resets to real time
- Used for testing expiry/alerts without waiting

## Database
- Single SQLite file: `data/annasetu.db`
- Schema in `backend/core/db.py` → `init_db()`
- Each module has its own `db.py` with table-specific functions
- No ORM - raw sqlite3 for simplicity

## Running Tests
```bash
# Unit tests
python -m pytest tests/ -v

# Smoke test (starts/stops server)
python tests/smoke_test.py

# Ownership check
python scripts/check_ownership.py
```

## Quick Commands
```bash
# Start server
python run.py

# Install deps
pip install -r requirements.txt
pip install -r requirements-ml.txt  # for forecast ML

# Check ownership
python scripts/check_ownership.py

# Fetch vendor (frontend)
python scripts/fetch_vendor.py
```

## Emergency: Fixing Ownership Conflicts
If ownership check fails:
1. Identify conflicting files from error output
2. Coordinate with owning member
3. Move file to correct module or update OWNERS.json
4. Re-run check

## Pre-Commit Hook (Recommended)
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/sh
python scripts/check_ownership.py
```
Make executable: `chmod +x .git/hooks/pre-commit`