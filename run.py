#!/usr/bin/env python3
"""
AnnaSetu AI — Application Entry Point
Starts the FastAPI server with uvicorn.
Usage: python run.py [--reset] [--port PORT]
"""
import argparse
import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def create_runtime_dir():
    """Create runtime directory and ensure DB exists."""
    runtime_dir = ROOT / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Start AnnaSetu AI server")
    parser.add_argument("--reset", action="store_true", help="Reset database and demo clock before starting")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on (default: 8000)")
    args = parser.parse_args()

    create_runtime_dir()

    # Import and run
    import uvicorn
    from backend.app import app

    if args.reset:
        print("[RESET] Resetting database and demo clock...")
        from backend.core.db import reset_database
        reset_database()
        print("[RESET] Database reset complete.")
    else:
        # Ensure database is initialized on normal startup too
        from backend.core.db import init_db, seed_database
        init_db()
        seed_database()

    # Get LAN IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print(f"\n{'='*50}")
    print(f"AnnaSetu AI starting on http://0.0.0.0:{args.port}")
    print(f"Local:   http://localhost:{args.port}")
    print(f"Network: http://{local_ip}:{args.port}")
    print(f"{'='*50}\n")

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()