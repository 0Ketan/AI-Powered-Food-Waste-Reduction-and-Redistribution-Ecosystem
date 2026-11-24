# Waste Module (M2)

**Owner:** Member 2 (M2)

## Purpose
Logs daily waste (prepared vs served) per kitchen/slot and provides summary statistics.

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/waste/log` | Log a waste entry |
| GET | `/waste/logs` | List recent waste logs (filter by kitchen_id, limit) |
| GET | `/waste/summary` | Aggregated summary for a kitchen |

## Request/Response

### POST /waste/log
```json
{
  "kitchen_id": "1",
  "date": "2026-11-24",
  "slot": "lunch",
  "prepared": 180,
  "served": 165,
  "leftover": 15,
  "ran_short": false
}
```

**Response:** The logged entry with generated ID.

### GET /waste/logs?kitchen_id=1&limit=10
Returns array of waste log entries.

### GET /waste/summary?kitchen_id=1
```json
{
  "unit": "plates",
  "days": [{"date": "2026-11-23", "prepared": 200, "served": 180, "leftover": 20}],
  "totals": {"prepared": 2000, "served": 1800, "leftover": 200, "leftover_pct": 10},
  "by_slot": [{"slot": "lunch", "avg_leftover": 10}],
  "shortage_count": 0
}
```

## Data Sources
- `data/seed/waste.json` — historical waste logs
- `data/seed/core.json` — kitchens, slots

## Stub Implementation
- In-memory append to `data/seed/waste.json` (simulated persistence)
- Summary computes totals, averages, leftover %, and shortage count