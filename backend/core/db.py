"""
Database helper for AnnaSetu AI.
Provides SQLite connection management and schema initialization.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent.parent / "runtime" / "annasetu.db"


def get_connection():
    """Get a new SQLite connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize all tables. Called on first startup and on demo reset."""
    conn = get_connection()
    try:
        # Demo clock table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS demo_clock (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                offset_minutes INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("INSERT OR IGNORE INTO demo_clock (id, offset_minutes) VALUES (1, 0)")

        # Users table (seeded from core.json)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS core_users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('kitchen', 'processing_unit', 'ngo', 'mandir')),
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                address TEXT,
                veg_only BOOLEAN NOT NULL DEFAULT 0,
                capacity_people INTEGER
            )
        """)

        # Waste logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS waste_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kitchen_id TEXT NOT NULL,
                date TEXT NOT NULL,
                slot TEXT NOT NULL,
                prepared INTEGER NOT NULL,
                served INTEGER NOT NULL,
                leftover INTEGER NOT NULL,
                ran_short BOOLEAN NOT NULL DEFAULT 0,
                plate_waste INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_waste_kitchen_date ON waste_logs(kitchen_id, date)")

        # Forecast history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS forecast_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kitchen_id TEXT NOT NULL,
                slot TEXT NOT NULL,
                date TEXT NOT NULL,
                predicted INTEGER NOT NULL,
                actual INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_forecast_history_kitchen_slot ON forecast_history(kitchen_id, slot)")

        # Forecast baselines table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS forecast_baselines (
                kitchen_id TEXT NOT NULL,
                slot TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (kitchen_id, slot)
            )
        """)

        # Safety evaluation records
        conn.execute("""
            CREATE TABLE IF NOT EXISTS safety_records (
                record_id TEXT PRIMARY KEY,
                donor_id TEXT NOT NULL,
                donor_name TEXT NOT NULL,
                donor_address TEXT,
                recipient_id TEXT,
                recipient_name TEXT,
                recipient_address TEXT,
                donation_date TEXT NOT NULL,
                item_name TEXT NOT NULL,
                batch_no TEXT,
                mfg_date TEXT,
                expiry_or_consume_by TEXT NOT NULL,
                quantity_donated REAL NOT NULL,
                unit TEXT NOT NULL,
                food_temperature_note TEXT,
                quantity_distributed REAL DEFAULT 0,
                area_distributed TEXT,
                distribution_date TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # Safety disposal records
        conn.execute("""
            CREATE TABLE IF NOT EXISTS safety_disposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                route TEXT NOT NULL CHECK (route IN ('animal_feed', 'compost')),
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # Marketplace listings
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mkt_listings (
                id TEXT PRIMARY KEY,
                donor_id TEXT NOT NULL,
                donor_name TEXT NOT NULL,
                item_name TEXT NOT NULL,
                category_id TEXT NOT NULL,
                veg BOOLEAN NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                storage TEXT NOT NULL,
                consume_by TEXT NOT NULL,
                label_id TEXT,
                record_id TEXT,
                status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'claimed', 'collected', 'distributed', 'expired')),
                claimed_by TEXT,
                people_served INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mkt_listings_donor ON mkt_listings(donor_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mkt_listings_status ON mkt_listings(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mkt_listings_consume_by ON mkt_listings(consume_by)")

        # Marketplace claims
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mkt_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                pickup_code TEXT NOT NULL,
                claimed_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(listing_id, recipient_id)
            )
        """)

        # Marketplace alerts
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mkt_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('new_listing', 'claimed', 'pledge', 'expiring')),
                message TEXT NOT NULL,
                read BOOLEAN NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mkt_alerts_user ON mkt_alerts(user_id, read)")

        # Marketplace needs
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mkt_needs (
                id TEXT PRIMARY KEY,
                recipient_id TEXT NOT NULL,
                recipient_name TEXT NOT NULL,
                people INTEGER NOT NULL,
                needed_by TEXT NOT NULL,
                veg_only BOOLEAN NOT NULL DEFAULT 0,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'pledged')),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # Marketplace pledges
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mkt_pledges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                need_id TEXT NOT NULL,
                donor_id TEXT NOT NULL,
                donor_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                note TEXT,
                pledged_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        conn.commit()
    finally:
        conn.close()


def seed_database():
    """Seed all tables from JSON seed files."""
    import json
    from datetime import datetime

    DATA_DIR = Path(__file__).parent.parent.parent / "data" / "seed"
    conn = get_connection()

    try:
        # Seed users from core.json
        with open(DATA_DIR / "core.json", "r", encoding="utf-8") as f:
            core = json.load(f)

        # Clear and reseed users
        conn.execute("DELETE FROM core_users")
        for k in core.get("kitchens", []):
            conn.execute(
                """INSERT INTO core_users (id, name, role, lat, lng, address, veg_only, capacity_people)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (k["id"], k["name"], "kitchen" if k["type"] in ("hostel", "canteen") else "processing_unit",
                 k["lat"], k["lon"], "", 0, k.get("capacity_plates", 0))
            )
        for r in core.get("recipients", []):
            conn.execute(
                """INSERT INTO core_users (id, name, role, lat, lng, address, veg_only, capacity_people)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (r["id"], r["name"], r["type"], r["lat"], r["lon"], "", 1 if r.get("veg_only") else 0, r.get("capacity", 0))
            )

        # Seed waste logs from waste.json
        with open(DATA_DIR / "waste.json", "r", encoding="utf-8") as f:
            waste = json.load(f)
        conn.execute("DELETE FROM waste_logs")
        for log in waste.get("logs", []):
            conn.execute(
                """INSERT INTO waste_logs (kitchen_id, date, slot, prepared, served, leftover, ran_short, plate_waste)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (log["kitchen_id"], log["date"], log["slot"], log["prepared"],
                 log["served"], log["leftover"], 1 if log.get("ran_short") else 0, log.get("plate_waste", 0))
            )

        # Seed marketplace listings from marketplace.json
        with open(DATA_DIR / "marketplace.json", "r", encoding="utf-8") as f:
            mkt = json.load(f)
        conn.execute("DELETE FROM mkt_listings")
        for listing in mkt.get("listings", []):
            conn.execute(
                """INSERT INTO mkt_listings (id, donor_id, donor_name, item_name, category_id, veg, quantity,
                   unit, storage, consume_by, label_id, record_id, status, claimed_by, people_served)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (listing["id"], listing["donor_id"], listing["donor_name"], listing["item_name"],
                 listing["category_id"], 1 if listing["veg"] else 0, listing["quantity"],
                 listing["unit"], listing["storage"], listing["consume_by"],
                 listing.get("label_id"), listing.get("record_id"),
                 listing.get("status", "open"), listing.get("claimed_by"), listing.get("people_served", 0))
            )

        conn.execute("DELETE FROM mkt_needs")
        for need in mkt.get("needs", []):
            conn.execute(
                """INSERT INTO mkt_needs (id, recipient_id, recipient_name, people, needed_by, veg_only, notes, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (need["id"], need["recipient_id"], need["recipient_name"], need["people"],
                 need["needed_by"], 1 if need.get("veg_only") else 0, need.get("notes", ""), need.get("status", "open"))
            )

        # Seed forecast history from forecast.json
        with open(DATA_DIR / "forecast.json", "r", encoding="utf-8") as f:
            forecast = json.load(f)
        conn.execute("DELETE FROM forecast_history")
        for entry in forecast.get("history", []):
            conn.execute(
                """INSERT INTO forecast_history (kitchen_id, slot, date, predicted, actual)
                   VALUES (?, ?, ?, ?, ?)""",
                (entry["kitchen_id"], entry["slot"], entry["date"], entry.get("predicted", 0), entry["actual"])
            )

        # Seed forecast baselines from forecast.json
        conn.execute("DELETE FROM forecast_baselines")
        for kitchen_id, slots in forecast.get("baselines", {}).items():
            for slot, quantity in slots.items():
                conn.execute(
                    """INSERT INTO forecast_baselines (kitchen_id, slot, quantity) VALUES (?, ?, ?)""",
                    (kitchen_id, slot, quantity)
                )

        conn.commit()
    finally:
        conn.close()


def reset_database():
    """Full reset: drop all tables and reinitialize + reseed."""
    conn = get_connection()
    try:
        tables = [
            "demo_clock", "core_users", "waste_logs", "safety_records",
            "safety_disposals", "mkt_listings", "mkt_claims", "mkt_alerts",
            "mkt_needs", "mkt_pledges", "forecast_history", "forecast_baselines"
        ]
        for t in tables:
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
    finally:
        conn.close()

    init_db()
    seed_database()


if __name__ == "__main__":
    reset_database()
    print("Database initialized and seeded.")