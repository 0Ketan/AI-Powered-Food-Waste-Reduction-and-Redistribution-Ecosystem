# AnnaSetu AI: Food Waste Reduction & Redistribution Prototype

A hackathon prototype for institutional kitchens (hostel messes, canteens, caterers) and food processing units to monitor food waste, reduce surplus by forecasting cooking volumes, identify safe-to-donate items, and redistribute to NGOs and mandirs.

## Purpose

This is a **prototype**, not production software. It demonstrates the AnnaSetu AI platform with simulated data and basic logic. No real login, SMS, road routing, FSSAI verification, or live data.

**Goals**: Build a working MVP that works without bugs, is easy to navigate, has simple code, and looks decent.

## Constraints

- **Version**: Python 3.10+
- **Backend**: FastAPI with SQLite
- **Frontend**: Plain HTML/CSS served by FastAPI (no Node, no build step)
- **Modules**: Forecast, Waste, Safety, Marketplace
- ** ownership**: Three developers (M1, M2, M3) with separate folders to avoid Git conflicts
- **Data**: Simulated, seeded at startup
- **Deployment**: Any machine that can run a Python 3.10+ HTTP server

## Priorities

1. **WORKS WITHOUT BUGS** > any other feature
2. Easy to navigate UI
3. Simple code (readable, no over-engineering)
4. Looks decent (using simple CSS)

## Quickstart

```bash
# Clone (if on a team)
git clone <repo_url>

# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py

# Open http://localhost:8000 in your browser
```

After app starts:
1. Open http://localhost:8000/api/health to see module status (`stub` = baseline, `live` = real logic)
2. Navigate to the frontend (page will show "UI coming" placeholder)
3. Run full test suite: `python tests/smoke_test.py`

## Module Overview

### 1. Forecast (M2 - Data & AI)
Predicts how much to cook per kitchen/slot/date. Uses baseline + quantile model (XGBoost/scikit-learn) trained on 120 days of simulated data per kitchen/slot. Explainability via differences or SHAP.

### 2. Waste (M2 - Data & AI)
Logs meal data (prepared, served, leftover, ran-short) and returns dashboard numbers.

### 3. Safety (M1 - Product & Interface)
Determines if leftover food is safe to donate based on kitchen confirmation and time until pickup. Creates printable labels and donation records. Routes non-donatable batches to animal feed/compost.

### 4. Marketplace (M3 - Listings & Despatches)
Integrates stakeholders: donors (kitchens), recipients (NGOs, mandirs). Features: listings, nearby ranking, claim+pickup code handshake, people served tracking, pledges, alerts.

## Architecture

- **Single-origin**: FastAPI serves frontend/ at `/`, API at `/api/*`
- **Auto-module discovery**: `backend/app.py` imports every folder in `backend/modules/` with `router.py`
- ** isolation ownership**: Each module (except core) lives in its own folder with its own tests
- **Demo clock**: `backend/core/clock.py` provides `now()` used everywhere; frontend can advance time via `/api/demo/advance`

## Project Structure

```
AnnaSetu AI/
├── run.py                    # Entry point
├── README.md                 # This file
├── AGENTS.md                 # Team agent conventions
├── CLAUDE.md                 # Claude Code workspace config
├── GEMINI.md                 # Gemini agent conventions
├── .cursorrules              # Cursor IDE config
├── OWNERS.json               # Path-prefix to member mapping
├── requirements.txt          # Runtime dependencies
├── requirements-ml.txt       # ML dependencies (only Forecast module)
├── .gitignore
├── .github/
│   ├── CODEOWNERS
│   └── copilot-instructions.md
├── contracts/                # API contracts & schemas
│   ├── API.md
│   └── FLOWS.md
├── frontend/                 # Placeholder for UI (later)
│   └── index.html
├── backend/                  # FastAPI application
│   ├── app.py
│   └── core/                 # Database, clock, users
├── modules/                  # Module-owning developers
│   ├── forecast/   (M2)
│   ├── waste/      (M2)
│   ├── safety/     (M1)
│   └── marketplace/(M3)
├── data/seed/              # Seeded JSON datasets
├── scripts/               # Utility scripts
├── tests/                 # Smoke tests
└── docs/                  # Demo scripts, checklists, guides
```

## Git Safety

- **Never commit to main**. Use feature branches (`m1/<topic>`, `m2/<topic>`, `m3/<topic>`)
- **Never use** `git add -A` without checking `git status` for unowned files
- **Always** run `python tests/smoke_test.py` at the end of your session
- Each developer edits only their own paths (lowercase in `OWNERS.json`)

## Testing

### Manual testing
```bash
curl http://localhost:8000/api/health
python run.py
# Open http://localhost:8000 in browser
```

### Automated testing
```bash
python tests/smoke_test.py
```

### Ownership verification
```bash
python scripts/check_ownership.py --member M1
```

## Module Status

- **core/** : M1 (always live)
- **forecast/** : M2 (stub + live mode)
- **waste/** : M2 (stub + live mode)
- **safety/** : M1 (stub + live mode)
- **marketplace/** : M3 (stub + live mode)

## Contact

Lead member: 0Ketan (@0Ketan on GitHub)
Team: M1, M2, M3 (GitHub handles: @0Ketan, @MEMBER2_GITHUB, @MEMBER3_GITHUB placeholders)

## License

Hackathon prototype. License TBD.
