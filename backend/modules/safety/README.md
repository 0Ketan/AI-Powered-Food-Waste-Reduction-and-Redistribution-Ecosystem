# Safety Module (M1)

**Owner:** Member 1 (M1)

## Purpose
Evaluates food safety for donations, generates printable labels, and maintains donation/disposal records.

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/safety/categories` | List food categories with placeholder safe hours |
| POST | `/safety/evaluate` | Evaluate a donation for safety |
| GET | `/safety/label/{label_id}/print` | Printable HTML label |
| GET | `/safety/records` | List donation records (filter by donor_id) |
| GET | `/safety/records.csv` | CSV export of records |
| GET | `/safety/disposals` | List disposal records (filter by donor_id) |
| POST | `/safety/records/{record_id}/complete` | Complete a donation record with distribution details |

## Request/Response

### POST /safety/evaluate
```json
{
  "donor_id": "1",
  "item_name": "Veg Biryani",
  "category_id": "cooked_rice",
  "veg": true,
  "quantity": 30,
  "unit": "plates",
  "storage": "hot_held",
  "prepared_at": "2026-11-24T12:00:00Z",
  "kitchen_confirms_safe": true,
  "pickup_buffer_minutes": 45
}
```

**Success (donate):**
```json
{
  "decision": "donate",
  "reason": "Safe to donate",
  "consume_by": "2026-11-24T16:00:00Z",
  "minutes_left": 240,
  "label": {
    "label_id": "lbl_abc123",
    "food_name": "Veg Biryani",
    "source": "Boys Hostel 1 Mess",
    "prepared_at": "2026-11-24T12:00:00Z",
    "consume_by": "2026-11-24T16:00:00Z",
    "veg": "Vegetarian"
  },
  "record_id": "rec_xyz789",
  "disposal_id": null
}
```

**Failure (animal_feed_compost):**
```json
{
  "decision": "animal_feed_compost",
  "reason": "Room‑temp storage exceeds safe hours for cooked rice",
  "consume_by": null,
  "minutes_left": null,
  "label": null,
  "record_id": null,
  "disposal_id": "disp_001"
}
```

## Data Sources
- `data/seed/core.json` — food_categories with placeholder hours
- `data/seed/safety.json` — records and disposals (runtime)

## Stub Implementation
- Decision logic: safe_hours = category placeholder for storage type; elapsed = now - prepared_at; remaining = safe_hours*60 - elapsed - pickup_buffer. If remaining > 0 and kitchen_confirms_safe → donate, else animal_feed_compost.
- Label generated with consume_by = prepared_at + safe_hours.
- Records stored in `data/seed/safety.json`.