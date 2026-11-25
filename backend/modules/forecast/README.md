# Forecast Module (M2)

**Owner:** Member 2 (M2)

## Purpose
Provides cooking quantity recommendations for kitchens based on historical data, weather, events, and a safety level parameter.

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/forecast/options` | Returns metadata: kitchens, slots, weather options, event options |
| POST | `/forecast/recommend` | Returns recommended quantity with reasons |
| GET | `/forecast/metrics` | Returns MAE for baseline and model |

## Request/Response

### POST /forecast/recommend
```json
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
  "reasons": [{"factor": "weekend", "effect_pct": -8}],
  "summary": "-8%: Saturday",
  "history": [{"date": "2026-11-23", "actual": 170}],
  "model": "stub",
  "data_note": "Simulated data"
}
```

## Data Sources
- `data/seed/forecast.json` — history and baselines
- `data/seed/core.json` — kitchens, slots, weather_options, event_options

## Stub Implementation
- Baseline = average of last 7 days for that kitchen/slot
- Adjustments: weekend -8%, rain -6%, exam -10%, festival +15%, holiday -20%, sports +5%, hot +3%, cloudy 0%
- Safety level applies multiplier: `recommended = baseline * (1 + total_adjustment_pct/100) * safety_level`
- MAE computed against history

## Status Checklist
- S1: venv setup, server runs, endpoints tested — **done (reviewed)**
- S2: Waste module validation, ordering, ran_short counting, /summary maths — **done (reviewed)**
- S3: simulate.py with 120 days patterns per kitchen/slot — **implemented, awaiting review**
- S4: Baseline + quantile models (0.5, 0.75, 0.9) — **not done**
- S5: Reasons with effect_pct vs baseline — **not done**
- S6: /metrics with MAE comparison — **not done**
- S7: Tests passing, modules live — **not done**