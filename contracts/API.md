# AnnaSetu AI API Contract

This document defines the public REST API for the AnnaSetu AI prototype.

All endpoints are under the base path `http://<host>:8000/api/`.

## Health Check

```
GET /health
```

**Response (200)**
```json
{
  "services": {
    "core": "live",
    "forecast": "stub",
    "waste": "stub",
    "safety": "stub",
    "marketplace": "stub"
  },
  "server_time": "2026-11-24T14:00:00Z"
}
```

## Core Demo Endpoints

### Clock
```
GET /demo/clock
POST /demo/advance {"minutes": <int>}
POST /demo/reset
```

- `GET /demo/clock` returns the current demo time and offset minutes.
- `POST /demo/advance` adds minutes to the demo clock (used for expiry testing).
- `POST /demo/reset` deletes the SQLite DB, recreates schema, reseeds data, and resets clock offset.

## Forecast Module (M2)

### Options
```
GET /forecast/options
```
Returns kitchens, slots, weather, events metadata.

### Recommend
```
POST /forecast/recommend {
  "kitchen_id": "1",
  "slot": "lunch",
  "date": "2026-11-30",
  "weather": "rain",
  "event": "exam",
  "safety_level": 0.75
}
```

**Semantics & Rules (Contract v1.1):**
- `safety_level` (`0.5`–`0.95`, default `0.75`): target share of similar situations in which the recommended quantity should cover demand (a quantile). Equivalent view: a shortage is treated as `level / (1 - level)` times worse than a surplus (`0.5 -> 1x`, `0.75 -> 3x`, `0.9 -> 9x`, `0.95 -> 19x`).
- `recommended` is a positive integer and **MUST be non-decreasing** in `safety_level`: `recommended(0.5) <= recommended(0.75) <= recommended(0.9) <= recommended(0.95)` for the same other inputs.
- `reasons[]` and `summary` describe **demand drivers** versus baseline only (weather, event, weekend), never the slider. A weekday/weekend factor may appear only if the request `date` really falls on it (derive it from the date).
- Optional response fields:
  - `forecast_median` (optional `int`): expected demand before the safety margin.
  - `safety_margin_pct` (optional `float`): percentage added on top of `forecast_median` by the slider (`recommended ~= forecast_median * (1 + safety_margin_pct / 100)`).
- **Fallback rule:** Any fallback without ML libraries must also be non-decreasing in `safety_level` (for example: `baseline * (1 + sum_of_effects) * (1 + (safety_level - 0.5) * 0.2)`).

**Response (illustrative numbers — Boys Hostel 1 Mess, Monday 2026-11-30)**
```json
{
  "kitchen_id": "1",
  "slot": "lunch",
  "date": "2026-11-30",
  "unit": "plates",
  "baseline": 180,
  "forecast_median": 151,
  "safety_margin_pct": 5.0,
  "recommended": 159,
  "safety_level": 0.75,
  "reasons": [
    {"factor": "Rain", "effect_pct": -6.0},
    {"factor": "Exam day", "effect_pct": -10.0}
  ],
  "summary": "-16%: Rain + exam",
  "history": [
    {"date": "2026-11-16", "actual": 176},
    {"date": "2026-11-17", "actual": 175},
    {"date": "2026-11-18", "actual": 182},
    {"date": "2026-11-19", "actual": 168},
    {"date": "2026-11-20", "actual": 190},
    {"date": "2026-11-21", "actual": 155},
    {"date": "2026-11-22", "actual": 145},
    {"date": "2026-11-23", "actual": 170},
    {"date": "2026-11-24", "actual": 178},
    {"date": "2026-11-25", "actual": 184},
    {"date": "2026-11-26", "actual": 172},
    {"date": "2026-11-27", "actual": 188},
    {"date": "2026-11-28", "actual": 158},
    {"date": "2026-11-29", "actual": 149}
  ],
  "model": "stub",
  "data_note": "Simulated data"
}
```
*(Arithmetic: `180 * 0.84 = 151.2 -> 151`; `151.2 * 1.05 = 158.76 -> 159`.)*

### Metrics
```
GET /forecast/metrics
```
Returns MAE for baseline and model.

## Waste Module (M2)

### Log
```
POST /waste/log {
  "kitchen_id": "string",
  "date": "YYYY-MM-DD",
  "slot": "string",
  "prepared": 200,
  "served": 180,
  "leftover": 20,
  "ran_short": false
}
```

### Logs List
```
GET /waste/logs?kitchen_id=<id>&limit=<n>
```

### Summary
```
GET /waste/summary?kitchen_id=<id>
```
**Response**
```json
{
  "unit": "plates",
  "days": [{"date":"2026-11-23","prepared":200,"served":180,"leftover":20}],
  "totals": {"prepared":2000,"served":1800,"leftover":200,"leftover_pct":10},
  "by_slot": [{"slot":"lunch","avg_leftover":10}],
  "shortage_count": 0
}
```

## Safety Module (M1)

### Categories
```
GET /safety/categories
```
**Response** – list of food categories with placeholder hours.

### Evaluate
```
POST /safety/evaluate {
  "donor_id": "string",
  "item_name": "string",
  "category_id": "string",
  "veg": true,
  "quantity": 20,
  "unit": "plates",
  "storage": "room_temp",
  "prepared_at": "2026-11-24T12:00:00Z",
  "kitchen_confirms_safe": true,
  "pickup_buffer_minutes": 45
}
```
**Response** – decision, reason, consume_by, label, record_id, disposal_id.

### Label Print
```
GET /safety/label/{label_id}/print
```
Returns printable HTML.

### Records & Disposals
```
GET /safety/records?donor_id=<id>
GET /safety/records.csv?donor_id=<id>
GET /safety/disposals?donor_id=<id>
```

## Marketplace Module (M3)

### Listings
```
GET /marketplace/listings?donor_id=&status=
POST /marketplace/listings { … }
```

### Nearby
```
GET /marketplace/nearby?recipient_id=<id>
```
Returns listings with distance, minutes_left, travel_minutes, score.

### Claim
```
POST /marketplace/listings/{id}/claim {"recipient_id": "string"}
```
Returns listing + 4‑digit pickup code (409 on second claim).

### Pickup
```
POST /marketplace/listings/{id}/pickup {"donor_id": "string", "code": "1234"}
```

### Served
```
POST /marketplace/listings/{id}/served {"recipient_id": "string", "people_served": 30}
```

### Needs & Pledges
```
GET /marketplace/needs?status=&recipient_id=&for_donor_id=
POST /marketplace/needs { … }
POST /marketplace/needs/{id}/pledge { … }
```

### Alerts & Impact
```
GET /alerts?user_id=&since=
POST /alerts/read {"user_id": "string"}
GET /impact?donor_id=<id>
```

---

All endpoints return JSON. Errors use HTTP 4xx with body `{"error":"code","message":"text"}`.
