# Marketplace Module (M3)

**Owner:** Member 3 (M3)

## Purpose
Matches surplus food listings with nearby recipients, handles claim/pickup/served flow, needs & pledges, and alerts/impact.

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/marketplace/listings` | List listings (filter by donor_id, status) |
| POST | `/marketplace/listings` | Create a listing (from safety evaluation) |
| GET | `/marketplace/nearby` | Nearby open listings for a recipient |
| POST | `/marketplace/listings/{id}/claim` | Recipient claims a listing |
| POST | `/marketplace/listings/{id}/pickup` | Donor confirms pickup with code |
| POST | `/marketplace/listings/{id}/served` | Recipient marks served |
| GET | `/marketplace/needs` | List needs (filter by status, recipient_id, for_donor_id) |
| POST | `/marketplace/needs` | Recipient creates a need |
| POST | `/marketplace/needs/{id}/pledge` | Donor pledges to a need |
| GET | `/alerts` | User alerts (filter by user_id, since) |
| POST | `/alerts/read` | Mark alerts read |
| GET | `/impact` | Donor impact summary |

## Request/Response

### POST /marketplace/listings
```json
{
  "donor_id": "1",
  "item_name": "Veg Biryani",
  "category_id": "cooked_rice",
  "veg": true,
  "quantity": 30,
  "unit": "plates",
  "storage": "hot_held",
  "consume_by": "2026-11-24T16:00:00Z",
  "label_id": "lbl_abc123",
  "record_id": "rec_xyz789"
}
```

### GET /marketplace/nearby?recipient_id=10
Returns listings with distance_km, minutes_left, travel_minutes, score. Veg-only recipients never see non-veg. Travel ≤ minutes_left.

### POST /marketplace/listings/{id}/claim
```json
{"recipient_id": "10"}
```
Returns listing + 4-digit pickup_code (409 if already claimed).

### POST /marketplace/listings/{id}/pickup
```json
{"donor_id": "1", "code": "7429"}
```
Status → collected (400 if wrong code).

### POST /marketplace/listings/{id}/served
```json
{"recipient_id": "10", "people_served": 25}
```
Status → distributed.

## Data Sources
- `data/seed/marketplace.json` — listings, needs, alerts (runtime)
- `data/seed/core.json` — kitchens, recipients, food_categories

## Stub Implementation
- Haversine distance for nearby filter
- In-memory status transitions: open → claimed → collected → distributed
- Alerts: new_listing, expiring (15 min), claimed, collected, distributed, pledged
- Impact: totals per donor (plates donated, people served, CO2e estimate)