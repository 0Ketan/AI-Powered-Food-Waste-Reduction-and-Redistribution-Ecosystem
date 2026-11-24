# AnnaSetu AI — User Flows

This document describes the end‑to‑end user flows with exact API calls. All times are ISO‑8601 UTC strings. All IDs are strings. Errors are HTTP 4xx with body `{"error":"code","message":"text"}`.

---

## F1 — Post Surplus (Donor posts leftover food)

**Goal:** A kitchen or processing unit has leftover food and wants to donate it.

### Step 1 — Safety Evaluation
```
POST /api/safety/evaluate
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

### Step 2 — Create Marketplace Listing (only if decision == "donate")
```
POST /api/marketplace/listings
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

**Response:**
```json
{
  "id": "lst_001",
  "donor_id": "1",
  "donor_name": "Boys Hostel 1 Mess",
  "item_name": "Veg Biryani",
  "category_id": "cooked_rice",
  "veg": true,
  "quantity": 30,
  "unit": "plates",
  "storage": "hot_held",
  "consume_by": "2026-11-24T16:00:00Z",
  "label_id": "lbl_abc123",
  "record_id": "rec_xyz789",
  "status": "open",
  "claimed_by": null,
  "people_served": null,
  "created_at": "2026-11-24T12:05:00Z"
}
```

**Alerts created:** `new_listing` alerts sent to all eligible recipients (NGOs and mandirs).

---

## F2 — Claim Flow (Recipient claims, donor confirms pickup, recipient serves)

### Step 1 — Recipient finds nearby listings
```
GET /api/marketplace/nearby?recipient_id=10
```

**Response:**
```json
[
  {
    "listing": { ...listing object... },
    "distance_km": 2.3,
    "minutes_left": 180,
    "travel_minutes": 7,
    "score": 0.82
  }
]
```
*Only shows open, unexpired listings. Veg‑only recipients (mandirs) never see non‑veg items. Travel time ≤ minutes_left.*

### Step 2 — Recipient claims
```
POST /api/marketplace/listings/lst_001/claim
{
  "recipient_id": "10"
}
```

**Success:**
```json
{
  "listing": { ...listing with status:"claimed", claimed_by:"10"... },
  "pickup_code": "7429"
}
```

**Double claim (409):**
```json
{ "error": "already_claimed", "message": "Listing already claimed" }
```

### Step 3 — Donor confirms pickup (gives code to recipient)
```
POST /api/marketplace/listings/lst_001/pickup
{
  "donor_id": "1",
  "code": "7429"
}
```

**Success:** listing status → `collected`
**Wrong code (400):**
```json
{ "error": "wrong_code", "message": "Invalid pickup code" }
```

### Step 4 — Recipient marks served
```
POST /api/marketplace/listings/lst_001/served
{
  "recipient_id": "10",
  "people_served": 25
}
```
Listing status → `distributed`

### Step 5 — Complete the donation record (safety)
```
POST /api/safety/records/rec_xyz789/complete
{
  "recipient_id": "10",
  "recipient_name": "Annapurna Seva Trust (demo NGO)",
  "recipient_address": "Demo Campus, Block A",
  "quantity_distributed": 25,
  "area_distributed": "Demo Campus, Block A",
  "distribution_date": "2026-11-24T14:30:00Z"
}
```

---

## F3 — Need & Pledge (Recipient posts a need, donor pledges)

### Step 1 — Recipient creates a need
```
POST /api/marketplace/needs
{
  "recipient_id": "10",
  "people": 50,
  "needed_by": "2026-11-25T12:00:00Z",
  "veg_only": true,
  "notes": "For lunch tomorrow"
}
```

### Step 2 — Donor views needs (with distance)
```
GET /api/marketplace/needs?for_donor_id=1
```

**Response includes `distance_km` for each need.**

### Step 3 — Donor pledges
```
POST /api/marketplace/needs/need_001/pledge
{
  "donor_id": "1",
  "quantity": 40,
  "unit": "plates",
  "note": "Can deliver by 11:30"
}
```

Need status → `pledged`, pledge added to `pledges[]`.

---

## F4 — Forecast & Waste Logging (Kitchen plans and logs)

### Forecast recommend
```
POST /api/forecast/recommend
{
  "kitchen_id": "1",
  "slot": "lunch",
  "date": "2026-11-30",
  "weather": "rain",
  "event": "exam",
  "safety_level": 0.75
}
```

**Response:**
```json
{
  "kitchen_id": "1",
  "slot": "lunch",
  "date": "2026-11-30",
  "unit": "plates",
  "baseline": 180,
  "recommended": 165,
  "safety_level": 0.75,
  "reasons": [
    {"factor": "weekend", "effect_pct": -8},
    {"factor": "rain", "effect_pct": -6},
    {"factor": "exam", "effect_pct": -10}
  ],
  "summary": "-24%: Saturday + rain + exam",
  "history": [{"date":"2026-11-23","actual":170}, ...],
  "model": "stub",
  "data_note": "Simulated data"
}
```

### Waste log
```
POST /api/waste/logs
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

### Waste summary
```
GET /api/waste/summary?kitchen_id=1
```

---

## F5 — Demo Clock Controls

```
GET /api/demo/clock
POST /api/demo/advance {"minutes": 60}
POST /api/demo/reset
```

Advancing the clock expires marketplace listings (status → `expired`) and triggers `expiring` alerts.

---

## F6 — Alerts & Impact

```
GET /api/alerts?user_id=10&since=2026-11-24T00:00:00Z
POST /api/alerts/read {"user_id": "10"}
GET /api/impact?donor_id=1
```