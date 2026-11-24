"""Behaviour spot-checks for AnnaSetu AI."""
import sys
sys.path.insert(0, '.')

from backend.core.db import reset_database
reset_database()
from fastapi.testclient import TestClient
from backend.app import app
c = TestClient(app)

PASS = 0
FAIL = 0


def check(label, cond, evidence=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[PASS] {label}")
    else:
        FAIL += 1
        print(f"[FAIL] {label} | {evidence}")


# --- SPOT CHECK a: Safe item approves ---
r = c.post('/api/safety/evaluate', json={
    'donor_id': '1', 'item_name': 'Fresh Roti', 'category_id': 'packaged',
    'veg': True, 'quantity': 50, 'unit': 'plates', 'storage': 'room_temp',
    'prepared_at': '2026-11-24T15:00:00Z', 'kitchen_confirms_safe': True, 'pickup_buffer_minutes': 10
})
d = r.json()
check("Safe item approves (packaged, fresh)", r.status_code == 200 and d.get('decision') == 'approve',
      f"status={r.status_code} decision={d.get('decision')} reason={d.get('reason','')[:60]}")

# --- SPOT CHECK b: 6h old room_temp cooked rice -> reject with plain-English reason & routes to animal_feed_compost ---
from datetime import datetime, timedelta, timezone
old_time = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
r = c.post('/api/safety/evaluate', json={
    'donor_id': '1', 'item_name': 'Old Rice', 'category_id': 'cooked_rice',
    'veg': True, 'quantity': 10, 'unit': 'plates', 'storage': 'room_temp',
    'prepared_at': old_time, 'kitchen_confirms_safe': True, 'pickup_buffer_minutes': 10
})
d = r.json()
check("6h old cooked_rice at room_temp -> reject", r.status_code == 200 and d.get('decision') == 'reject',
      f"status={r.status_code} decision={d.get('decision')}")
check("Item routes to animal_feed/compost", d.get('route') in ('animal_feed', 'compost'), f"route={d.get('route')}")
check("Reject reason is plain English (non-empty)", bool(d.get('reason')), f"reason={d.get('reason')}")
print(f"       reason: {d.get('reason','')[:80]}")

# --- SPOT CHECK c: Second claim gets 409 ---
# Create a veg listing first
r = c.post('/api/marketplace/listings', json={
    'donor_id': '1', 'item_name': 'Dal Makhani', 'category_id': 'cooked_dal',
    'veg': True, 'quantity': 30, 'unit': 'plates', 'storage': 'hot_held',
    'consume_by': '2026-11-25T20:00:00Z'
})
lid = r.json().get('listing_id')
check("Listing created", bool(lid), f"status={r.status_code}")

r1 = c.post(f'/api/marketplace/listings/{lid}/claim', json={'recipient_id': '10'})
check("First claim succeeds (200)", r1.status_code == 200, f"status={r1.status_code}")

r2 = c.post(f'/api/marketplace/listings/{lid}/claim', json={'recipient_id': '12'})
check("Second claim gets 409", r2.status_code == 409, f"status={r2.status_code} body={r2.text[:60]}")

# --- SPOT CHECK d: Wrong pickup code gets 400 ---
pickup_code = r1.json().get('pickup_code', '')
r_bad = c.post(f'/api/marketplace/listings/{lid}/pickup',
               json={'donor_id': '1', 'code': '0000'})
check("Wrong pickup code -> 400", r_bad.status_code in (400, 401), f"status={r_bad.status_code}")

# --- SPOT CHECK e: Veg-only mandir never sees non-veg listings ---
r = c.post('/api/marketplace/listings', json={
    'donor_id': '1', 'item_name': 'Chicken Curry', 'category_id': 'cooked_dal',
    'veg': False, 'quantity': 20, 'unit': 'plates', 'storage': 'hot_held',
    'consume_by': '2026-11-25T20:00:00Z'
})
r6 = c.get('/api/marketplace/nearby', params={'recipient_id': '11'})  # mandir, veg_only
nearby = r6.json() if isinstance(r6.json(), list) else []
non_veg = [l for l in nearby if not l.get('veg', True)]
check("Veg-only mandir never sees non-veg listings", len(non_veg) == 0,
      f"non-veg shown: {len(non_veg)}, total nearby: {len(nearby)}")

# --- SPOT CHECK f: Forecast recommend - summary string + higher safety_level = more ---
r_lo = c.post('/api/forecast/recommend', json={
    'kitchen_id': '1', 'slot': 'lunch', 'date': '2026-11-24',
    'weather': 'clear', 'event': 'none', 'safety_level': 0.5
})
r_hi = c.post('/api/forecast/recommend', json={
    'kitchen_id': '1', 'slot': 'lunch', 'date': '2026-11-24',
    'weather': 'clear', 'event': 'none', 'safety_level': 0.9
})
lo = r_lo.json(); hi = r_hi.json()
check("Forecast recommend returns summary string", bool(lo.get('summary')), f"summary={lo.get('summary')}")
check("Higher safety_level -> more recommended",
      hi.get('recommended', 0) > lo.get('recommended', 0),
      f"lo={lo.get('recommended')} hi={hi.get('recommended')}")
print(f"       safety=0.5 recommended={lo.get('recommended')}")
print(f"       safety=0.9 recommended={hi.get('recommended')}")

# --- SPOT CHECK g: Waste summary totals match logs posted ---
r_before = c.get('/api/waste/summary', params={'kitchen_id': '1'})
before_tot = r_before.json().get('totals', {}).get('prepared', 0)
c.post('/api/waste/logs', json={
    'kitchen_id': '1', 'date': '2026-11-24', 'slot': 'dinner',
    'prepared': 150, 'served': 130, 'leftover': 20, 'ran_short': False
})
r_after = c.get('/api/waste/summary', params={'kitchen_id': '1'})
after_tot = r_after.json().get('totals', {}).get('prepared', 0)
check("Waste summary total increments by logged amount",
      after_tot == before_tot + 150, f"before={before_tot} after={after_tot} expected={before_tot+150}")

# --- SPOT CHECK h: Clock advance marks near-expiry listing expired ---
# Create listing that expires in 30 minutes
from backend.core.clock import get_demo_time
near_expiry_time = (get_demo_time() + timedelta(minutes=30)).isoformat()
r_exp_list = c.post('/api/marketplace/listings', json={
    'donor_id': '1', 'item_name': 'Expiring Soon Kheer', 'category_id': 'dairy',
    'veg': True, 'quantity': 15, 'unit': 'bowls', 'storage': 'cold',
    'consume_by': near_expiry_time
})
exp_lid = r_exp_list.json().get('listing_id')
r_before_adv = c.get(f'/api/marketplace/listings/{exp_lid}')
check("Listing is initially open", r_before_adv.json().get('status') == 'open')

r_adv = c.post('/api/demo/advance', params={'minutes': 60})
check("Clock advance 60 min returns offset=60",
      r_adv.json().get('offset_minutes') == 60, f"offset={r_adv.json().get('offset_minutes')}")

r_after_adv = c.get(f'/api/marketplace/listings/{exp_lid}')
check("Listing expiring within 1 hour is marked 'expired' after 60 min advance",
      r_after_adv.json().get('status') == 'expired',
      f"status={r_after_adv.json().get('status')}")

# Reset clock
c.post('/api/demo/reset')

print()
print("=" * 50)
print(f"Spot checks: {PASS} PASS  {FAIL} FAIL")
print("=" * 50)
sys.exit(0 if FAIL == 0 else 1)
