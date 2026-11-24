# AnnaSetu AI - Test Checklist
Importers: None (documentation)
Affected API: All endpoints per contracts/API.md
Data schemas: All tables from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification

## Overview
This checklist ensures all test scenarios pass for the hackathon prototype.

## Pre-Test Setup
- [ ] Python 3.10+ installed
- [ ] Virtual environment created: `python -m venv venv`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] ML dependencies installed: `pip install -r requirements-ml.txt` (optional, for forecast)
- [ ] Database initialized: run server once or run `python -c "from backend.core.db import init_db; init_db()"`

## Unit Tests (pytest)

### Core Module Tests
- [ ] `python -m pytest tests/test_core.py -v` (if exists)

### Waste Module Tests
- [ ] `python -m pytest tests/test_waste.py -v`
  - [ ] test_log_waste passes
  - [ ] test_get_waste_logs passes
  - [ ] test_get_waste_summary passes

### Safety Module Tests
- [ ] `python -m pytest tests/test_safety.py -v`
  - [ ] test_get_categories passes
  - [ ] test_evaluate_safety passes
  - [ ] test_get_records passes
  - [ ] test_get_disposals passes
  - [ ] test_create_disposal passes

### Marketplace Module Tests
- [ ] `python -m pytest tests/test_marketplace.py -v`
  - [ ] test_create_and_get_listing passes
  - [ ] test_nearby_listings passes
  - [ ] test_claim_pickup_serve_flow passes
  - [ ] test_need_and_pledge passes
  - [ ] test_alerts passes
  - [ ] test_impact passes

### Forecast Module Tests
- [ ] `python -m pytest tests/test_forecast.py -v`
  - [ ] test_get_all_kitchens passes
  - [ ] test_get_slots passes
  - [ ] test_get_weather_options passes
  - [ ] test_get_event_options passes
  - [ ] test_baseline_operations passes
  - [ ] test_history_operations passes
  - [ ] test_compute_adjustments passes
  - [ ] test_compute_mae passes

## Smoke Test (Integration)
- [ ] `python tests/smoke_test.py`
  - [ ] Server starts successfully
  - [ ] /health endpoint returns 200
  - [ ] /clock endpoints work
  - [ ] /users endpoints work
  - [ ] /waste endpoints work
  - [ ] /safety endpoints work
  - [ ] /forecast endpoints work
  - [ ] /marketplace endpoints work
  - [ ] Server shuts down cleanly

## API Contract Tests (per contracts/API.md)

### Core Endpoints
- [ ] GET /health
- [ ] GET /clock
- [ ] POST /clock/advance
- [ ] POST /clock/reset
- [ ] GET /users
- [ ] GET /users/{user_id}

### Waste Endpoints
- [ ] POST /waste/log
- [ ] GET /waste/logs
- [ ] GET /waste/summary

### Safety Endpoints
- [ ] GET /safety/categories
- [ ] POST /safety/evaluate
- [ ] GET /safety/records
- [ ] GET /safety/records.csv
- [ ] POST /safety/disposals

### Forecast Endpoints
- [ ] GET /forecast/options
- [ ] POST /forecast/recommend
- [ ] GET /forecast/metrics

### Marketplace Endpoints
- [ ] POST /marketplace/listings
- [ ] GET /marketplace/listings
- [ ] GET /marketplace/nearby
- [ ] POST /marketplace/listings/{id}/claim
- [ ] POST /marketplace/listings/{id}/pickup
- [ ] POST /marketplace/listings/{id}/served
- [ ] POST /marketplace/needs
- [ ] GET /marketplace/needs
- [ ] POST /marketplace/needs/{id}/pledge
- [ ] GET /marketplace/alerts
- [ ] POST /marketplace/alerts/read
- [ ] GET /marketplace/impact

## Frontend Tests
- [ ] Frontend loads at http://localhost:8000
- [ ] Dashboard tabs switch correctly
- [ ] Waste logging form submits
- [ ] Safety evaluation form submits
- [ ] Forecast recommendation form submits
- [ ] Marketplace listing creation works
- [ ] Clock display updates

## Ownership Tests
- [ ] `python scripts/check_ownership.py` passes

## Edge Cases
- [ ] Empty database handles gracefully
- [ ] Invalid IDs return 404/400 appropriately
- [ ] Malformed JSON returns 422
- [ ] Clock advance/reset works correctly
- [ ] Expired listings filtered in nearby
- [ ] Pickup code validation works (4 digits)
- [ ] MAE calculation with insufficient data

## Performance Checks
- [ ] Server starts in < 3 seconds
- [ ] API responses < 200ms for simple queries
- [ ] Database connections properly closed

## Sign-off
- [ ] All unit tests pass
- [ ] Smoke test passes
- [ ] Ownership check passes
- [ ] Frontend loads without console errors
- [ ] Demo script executes successfully