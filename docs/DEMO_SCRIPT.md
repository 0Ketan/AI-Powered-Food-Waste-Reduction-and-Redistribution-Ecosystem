# AnnaSetu AI - Demo Script

## Overview
This document provides a step-by-step demo script for the AnnaSetu AI hackathon prototype.

## Prerequisites
- Python 3.10+
- Virtual environment set up
- Server running on `http://localhost:8000`
- Frontend served at `http://localhost:8000` (FastAPI static files)

## Demo Flow (5 minutes)

### 1. Health Check (30 seconds)
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "ok", "time": "..."}`

### 2. Clock Operations (30 seconds)
```bash
# Get current demo time
curl http://localhost:8000/clock

# Advance clock by 2 hours (simulate time passing for expiry testing)
curl -X POST http://localhost:8000/clock/advance -H "Content-Type: application/json" -d '{"hours": 2}'

# Reset clock
curl -X POST http://localhost:8000/clock/reset -H "Content-Type: application/json"
```

### 3. User Management (30 seconds)
```bash
# List all users
curl http://localhost:8000/users

# Get specific user
curl http://localhost:8000/users/kitchen_001
```

### 4. Waste Logging (1 minute)
```bash
# Log waste entry
curl -X POST http://localhost:8000/waste/log \
  -H "Content-Type: application/json" \
  -d '{
    "kitchen_id": "kitchen_001",
    "item_name": "Cooked Rice",
    "quantity_kg": 5.0,
    "category": "cooked_rice",
    "reason": "overproduction",
    "disposal_method": "donation"
  }'

# Get waste logs
curl "http://localhost:8000/waste/logs?kitchen_id=kitchen_001"

# Get waste summary
curl "http://localhost:8000/waste/summary?kitchen_id=kitchen_001"
```

### 5. Safety Evaluation (1 minute)
```bash
# Get safety categories
curl http://localhost:8000/safety/categories

# Evaluate food safety
curl -X POST http://localhost:8000/safety/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "donor_id": "kitchen_001",
    "item_name": "Chicken Curry",
    "category_id": "cat_cooked_meat",
    "veg": false,
    "quantity": 20,
    "unit": "plates",
    "storage": "hot",
    "prepared_at": "2026-11-24T10:00:00Z",
    "kitchen_confirms_safe": true,
    "pickup_buffer_minutes": 45
  }'

# Get safety records
curl "http://localhost:8000/safety/records?donor_id=kitchen_001"

# Create disposal record
curl -X POST http://localhost:8000/safety/disposals \
  -H "Content-Type: application/json" \
  -d '{
    "donor_id": "kitchen_001",
    "item_name": "Expired Bread",
    "quantity": 10,
    "unit": "loaves",
    "route": "compost",
    "reason": "expired"
  }'
```

### 6. Forecast Operations (1 minute)
```bash
# Get forecast options (kitchens, slots, weather, events)
curl http://localhost:8000/forecast/options

# Get recommendation
curl -X POST http://localhost:8000/forecast/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "kitchen_id": "kitchen_001",
    "slot": "lunch",
    "date": "2026-11-24",
    "weather": "clear",
    "event": "none"
  }'

# Get forecast metrics (MAE)
curl "http://localhost:8000/forecast/metrics?kitchen_id=kitchen_001&slot=lunch"
```

### 7. Marketplace Operations (1 minute)
```bash
# Create listing
curl -X POST http://localhost:8000/marketplace/listings \
  -H "Content-Type: application/json" \
  -d '{
    "donor_id": "kitchen_001",
    "item_name": "Fresh Vegetables",
    "category_id": "cat_veg",
    "veg": true,
    "quantity": 30,
    "unit": "plates",
    "storage": "refrigerated",
    "consume_by": "2026-11-24T14:00:00Z",
    "label_id": "lbl_123",
    "record_id": "rec_123"
  }'

# Get nearby listings (as NGO)
curl "http://localhost:8000/marketplace/nearby?recipient_id=ngo_001"

# Claim listing (as NGO)
curl -X POST http://localhost:8000/marketplace/listings/lst_abc123/claim \
  -H "Content-Type: application/json" \
  -d '{"recipient_id": "ngo_001"}'

# Pickup listing (as kitchen, using pickup code from claim)
curl -X POST http://localhost:8000/marketplace/listings/lst_abc123/pickup \
  -H "Content-Type: application/json" \
  -d '{"donor_id": "kitchen_001", "code": "1234"}'

# Serve listing (as NGO)
curl -X POST http://localhost:8000/marketplace/listings/lst_abc123/served \
  -H "Content-Type: application/json" \
  -d '{"recipient_id": "ngo_001", "people_served": 25}'

# Create need
curl -X POST http://localhost:8000/marketplace/needs \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": "ngo_001",
    "people": 100,
    "needed_by": "2026-11-24T18:00:00Z",
    "veg_only": true,
    "notes": "Urgent need for dinner"
  }'

# Get impact
curl "http://localhost:8000/marketplace/impact?donor_id=kitchen_001"
```

### 8. Frontend Demo (2 minutes)
Open `http://localhost:8000` in browser and demonstrate:
- Dashboard with waste/safety/forecast/marketplace tabs
- Real-time clock sync
- Interactive forms for each module
- Multi-module flows (waste → safety → marketplace)

## Key Talking Points
1. **Zero-conflict ownership** - M1/M2/M3 own distinct modules
2. **Demo clock** - Test expiry/alerts without waiting
3. **Module isolation** - No cross-imports, only core/contracts
4. **FastAPI + SQLite** - Lightweight, no ORM
5. **Contracts-driven** - API.md and FLOWS.md define interfaces

## Troubleshooting
- If server fails: check `python run.py` output
- If DB errors: delete `data/annasetu.db` and restart
- If frontend 404: ensure `frontend/index.html` exists