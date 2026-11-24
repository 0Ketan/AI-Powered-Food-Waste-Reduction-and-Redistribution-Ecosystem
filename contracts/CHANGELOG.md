# AnnaSetu AI - Contracts Changelog
Importers: None (documentation)
Affected API: All endpoints per contracts/API.md
Data schemas: All tables from core/db.py, contracts/schemas.py
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification

## [Unreleased]

### Added
- Initial API contract definitions in API.md
- Multi-module flow definitions in FLOWS.md
- Shared Pydantic schemas in schemas.py

## [1.0.0] - 2026-11-24

### Added - Core API
- `GET /health` - Health check endpoint
- `GET /clock` - Get current demo time with offset
- `POST /clock/advance` - Advance demo clock by hours
- `POST /clock/reset` - Reset demo clock to real time
- `GET /users` - List all users
- `GET /users/{user_id}` - Get specific user

### Added - Waste API
- `POST /waste/log` - Log waste entry
- `GET /waste/logs` - Get waste logs with filters
- `GET /waste/summary` - Get waste summary statistics

### Added - Safety API
- `GET /safety/categories` - Get safety categories
- `POST /safety/evaluate` - Evaluate food safety
- `GET /safety/records` - Get safety evaluation records
- `GET /safety/records.csv` - Export records as CSV
- `POST /safety/disposals` - Create disposal record

### Added - Forecast API
- `GET /forecast/options` - Get kitchens, slots, weather, events
- `POST /forecast/recommend` - Get forecast recommendation
- `GET /forecast/metrics` - Get forecast accuracy (MAE)

### Added - Marketplace API
- `POST /marketplace/listings` - Create surplus listing
- `GET /marketplace/listings` - Get listings with filters
- `GET /marketplace/nearby` - Get nearby open listings
- `POST /marketplace/listings/{id}/claim` - Claim listing (generates pickup code)
- `POST /marketplace/listings/{id}/pickup` - Verify pickup code
- `POST /marketplace/listings/{id}/served` - Mark as served
- `POST /marketplace/needs` - Create need request
- `GET /marketplace/needs` - Get needs with filters
- `POST /marketplace/needs/{id}/pledge` - Pledge to fulfill need
- `GET /marketplace/alerts` - Get user alerts
- `POST /marketplace/alerts/read` - Mark alerts as read
- `GET /marketplace/impact` - Get donor impact statistics

### Data Schemas (schemas.py)
- Core: HealthResponse, ClockResponse, User, UsersResponse
- Waste: WasteLogRequest/Response, WasteLogEntry, WasteLogsResponse, WasteSummaryResponse
- Safety: SafetyCategory, SafetyEvaluateRequest/Response, SafetyRecord, SafetyDisposalRequest/Response
- Forecast: ForecastOptionsResponse, ForecastRecommendRequest/Response, ForecastMetricsResponse
- Marketplace: MarketplaceListingRequest/Response, NearbyListing, Claim/Pickup/Served Request/Response, Need/Pledge Request/Response, Alert, ImpactResponse

---

## Versioning Policy
- **Major**: Breaking API changes (endpoint removal, request/response schema changes)
- **Minor**: New endpoints, optional fields added, new enum values
- **Patch**: Bug fixes, documentation updates, internal refactoring

## Deprecation Policy
- Deprecated endpoints marked in API.md with `⚠️ DEPRECATED`
- Minimum 1 version notice before removal
- Migration path documented in CHANGELOG