#!/usr/bin/env python3
"""
Fetch Vendor Dependencies Script
Downloads Chart.js (UMD) and Leaflet (JS/CSS + marker images) for offline use.
Importers: None (standalone script)
Affected API: None (script)
Data schemas: None (script)
User instruction: Build complete SKELETON of AnnaSetu AI hackathon prototype per detailed specification
"""
import subprocess
import sys
from pathlib import Path
import urllib.request
import shutil


def download_file(url: str, dest: Path) -> bool:
    """Download a file from URL to destination."""
    try:
        print(f"  Downloading {url}...")
        urllib.request.urlretrieve(url, dest)
        print(f"  ✓ Saved to {dest}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to download {url}: {e}")
        return False


def main():
    """Fetch vendor dependencies for frontend."""
    vendor_dir = Path(__file__).parent.parent / "frontend" / "vendor"
    vendor_dir.mkdir(parents=True, exist_ok=True)

    # Chart.js UMD bundle
    chart_dir = vendor_dir / "chart.js"
    chart_dir.mkdir(parents=True, exist_ok=True)
    print("Fetching Chart.js...")
    download_file(
        "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js",
        chart_dir / "chart.umd.min.js"
    )
    # Also get the map file for debugging
    download_file(
        "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js.map",
        chart_dir / "chart.umd.min.js.map"
    )

    # Leaflet JS
    leaflet_dir = vendor_dir / "leaflet"
    leaflet_dir.mkdir(parents=True, exist_ok=True)
    print("Fetching Leaflet JS...")
    download_file(
        "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js",
        leaflet_dir / "leaflet.js"
    )
    download_file(
        "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css",
        leaflet_dir / "leaflet.css"
    )

    # Leaflet marker images
    images_dir = leaflet_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    print("Fetching Leaflet marker images...")
    download_file(
        "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon.png",
        images_dir / "marker-icon.png"
    )
    download_file(
        "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        images_dir / "marker-icon-2x.png"
    )
    download_file(
        "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-shadow.png",
        images_dir / "marker-shadow.png"
    )

    # Create .gitkeep
    (vendor_dir / ".gitkeep").write_text("")

    print(f"\nVendor dependencies fetched to: {vendor_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())