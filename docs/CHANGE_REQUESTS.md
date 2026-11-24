# AnnaSetu AI - Change Requests Log
Importers: None (documentation)
Affected API: All endpoints per contracts/API.md
Data schemas: All tables from core/db.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification

## Overview
This document tracks all change requests for the AnnaSetu AI hackathon prototype. Each change request should be linked to a PR and reviewed by the module owner.

## Change Request Template

### CR-XXXX: [Title]
- **Module**: [core/waste/safety/forecast/marketplace/frontend/contracts]
- **Owner**: [M1/M2/M3]
- **Type**: [feat/fix/docs/refactor/test]
- **Priority**: [P0/P1/P2]
- **Status**: [Open/In Progress/Review/Merged/Rejected]
- **Linked PR**: #[PR number]
- **Description**: [Detailed description]
- **Impact**: [API changes, DB schema, UI, contracts]
- **Testing**: [Unit tests, integration tests, manual verification]

---

## Change Requests

### CR-0001: Initial Skeleton Implementation
- **Module**: all
- **Owner**: M1 (lead), M2, M3
- **Type**: feat
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification. Includes folder structure, core infra, all 4 modules, frontend, contracts, tests, scripts, docs.
- **Impact**: Full project structure, all endpoints, database schema, frontend
- **Testing**: Smoke test, unit tests for all modules, ownership check

### CR-0002: Demo Clock Implementation
- **Module**: core
- **Owner**: M1
- **Type**: feat
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: Implement demo clock with SQLite persistence for testing expiry/alerts without waiting. Endpoints: GET /clock, POST /clock/advance, POST /clock/reset
- **Impact**: Core clock functionality, used by all modules for time-sensitive operations
- **Testing**: Unit tests in smoke_test.py

### CR-0003: Waste Logging Module
- **Module**: waste
- **Owner**: M2
- **Type**: feat
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: Implement waste logging with daily entries, summary statistics. Endpoints: POST /waste/log, GET /waste/logs, GET /waste/summary
- **Impact**: waste_logs table, waste module router/service/db
- **Testing**: tests/test_waste.py, smoke test

### CR-0004: Food Safety Module
- **Module**: safety
- **Owner**: M1
- **Type**: feat
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: Implement food safety evaluation with proceed/conditional/block decisions, label generation, disposal records. Endpoints: GET /safety/categories, POST /safety/evaluate, GET /safety/records, GET /safety/records.csv, POST /safety/disposals
- **Impact**: safety_categories, safety_evaluations, safety_disposals tables
- **Testing**: tests/test_safety.py, smoke test

### CR-0005: Forecast Module (Stub Mode)
- **Module**: forecast
- **Owner**: M2
- **Type**: feat
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: Implement forecast baseline + adjustment logic (no ML yet). Endpoints: GET /forecast/options, POST /forecast/recommend, GET /forecast/metrics. Includes baseline per kitchen/slot, weather/event/weekend adjustments, MAE tracking.
- **Impact**: forecast_history, forecast_baselines tables, simulate.py placeholder
- **Testing**: tests/test_forecast.py, smoke test

### CR-0006: Marketplace Module
- **Module**: marketplace
- **Owner**: M3
- **Type**: feat
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: Implement surplus listing, claim/pickup/serve flow with 4-digit codes, needs/pledges, alerts, impact tracking. Endpoints: POST/GET /marketplace/listings, GET /marketplace/nearby, POST /marketplace/listings/{id}/claim|pickup|served, POST/GET /marketplace/needs, POST /marketplace/needs/{id}/pledge, GET/POST /marketplace/alerts/read, GET /marketplace/impact
- **Impact**: mkt_listings, mkt_claims, mkt_alerts, mkt_needs, mkt_pledges tables
- **Testing**: tests/test_marketplace.py, smoke test

### CR-0007: Frontend Dashboard
- **Module**: frontend
- **Owner**: M1
- **Type**: feat
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: Single-page dashboard with tabs for Waste, Safety, Forecast, Marketplace. Real-time clock sync, forms for all module operations, responsive design.
- **Impact**: frontend/index.html, served as static files
- **Testing**: Manual browser test, smoke test

### CR-0008: Contracts Documentation
- **Module**: contracts
- **Owner**: M1
- **Type**: docs
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: API.md with all endpoint signatures, FLOWS.md with multi-module sequences
- **Impact**: API contracts, flow documentation
- **Testing**: Contract compliance in smoke test

### CR-0009: Ownership Enforcement
- **Module**: scripts
- **Owner**: M1
- **Type**: feat
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: OWNERS.json with patterns, check_ownership.py script to verify zero-conflict ownership
- **Impact**: Git workflow enforcement
- **Testing**: scripts/check_ownership.py passes

### CR-0010: Test Suite & Documentation
- **Module**: tests, docs
- **Owner**: M1, M2, M3
- **Type**: test, docs
- **Priority**: P0
- **Status**: Merged
- **Linked PR**: #1
- **Description**: Unit tests for all modules, smoke test, DEMO_SCRIPT.md, TEST_CHECKLIST.md, GIT_GUIDE.md
- **Impact**: Test coverage, documentation
- **Testing**: All tests pass

---

## Future Change Requests (Post-Hackathon)

### CR-0011: ML-Based Forecast Enhancement
- **Module**: forecast
- **Owner**: M2
- **Type**: feat
- **Priority**: P1
- **Status**: Open
- **Description**: Replace stub adjustments with trained ML model (LightGBM/XGBoost). Use historical data, weather API, event calendar.
- **Impact**: forecast/simulate.py, requirements-ml.txt, new model artifacts
- **Testing**: Model accuracy metrics, A/B test vs baseline

### CR-0012: Real-Time Notifications
- **Module**: marketplace, safety
- **Owner**: M1, M3
- **Type**: feat
- **Priority**: P1
- **Status**: Open
- **Description**: WebSocket/SSE for real-time alerts (new listings, claim updates, safety expirations)
- **Impact**: New WebSocket endpoints, frontend subscription logic
- **Testing**: Load test with concurrent connections

### CR-0013: Mobile-Responsive Frontend
- **Module**: frontend
- **Owner**: M1
- **Type**: feat
- **Priority**: P2
- **Status**: Open
- **Description**: Improve mobile UX, PWA support, offline capability
- **Impact**: frontend/index.html, new CSS/JS, service worker
- **Testing**: Mobile browser testing, Lighthouse audit

### CR-0014: Analytics Dashboard
- **Module**: frontend, all
- **Owner**: M1
- **Type**: feat
- **Priority**: P2
- **Status**: Open
- **Description**: Admin analytics: waste trends, safety compliance, forecast accuracy, marketplace velocity
- **Impact**: New endpoints for aggregated stats, frontend charts
- **Testing**: Data accuracy, chart rendering

### CR-0015: Multi-Language Support
- **Module**: frontend, contracts
- **Owner**: M1
- **Type**: feat
- **Priority**: P2
- **Status**: Open
- **Description**: i18n for English, Hindi, regional languages
- **Impact**: Frontend strings, API error messages
- **Testing**: Language switching, translation completeness

---

## Change Request Process

1. **Create CR**: Fill template above, assign owner based on module
2. **Review**: Owner reviews, may request changes
3. **Implement**: Create feature branch, implement, add tests
4. **PR**: Open PR to main, CI runs (ownership + smoke test)
5. **Merge**: Squash merge after approval
6. **Update**: Mark CR as Merged, link PR

## Ownership Reference

| Module | Owner |
|--------|-------|
| core | M1 |
| waste | M2 |
| safety | M1 |
| forecast | M2 |
| marketplace | M3 |
| frontend | M1 |
| contracts | M1 |
| scripts | M1/M3 |
| docs | M1 |
| tests | All (own their module tests) |