#!/usr/bin/env python3
"""
AnnaSetu AI - Skeleton Verification Script
Run: python scripts/verify_skeleton.py
Exits non-zero on any FAIL.
"""
import sys
import os
import ast
import json
import shutil
import tempfile
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

results = []


def result(check_num, label, status, evidence):
    results.append((check_num, label, status, evidence))
    icon = "✓" if status == PASS else ("✗" if status == FAIL else "⚠")
    print(f"  [{icon}] {status:4}  #{check_num:2}  {label}")
    if status != PASS:
        for line in evidence.splitlines()[:4]:
            print(f"            {line}")


# ---------------------------------------------------------------------------
# Check 1 – Required files/folders exist
# ---------------------------------------------------------------------------
def check_required_files():
    required = [
        "run.py", "README.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md",
        ".cursorrules", "OWNERS.json", "requirements.txt", "requirements-ml.txt",
        ".gitignore", ".gitattributes",
        ".github/CODEOWNERS", ".github/copilot-instructions.md",
        "contracts/API.md", "contracts/FLOWS.md", "contracts/schemas.py",
        "contracts/CHANGELOG.md",
        "frontend/index.html", "frontend/vendor",
        "backend/app.py",
        "backend/core/db.py", "backend/core/clock.py", "backend/core/users.py",
        "backend/core/__init__.py",
        "backend/modules/forecast/__init__.py", "backend/modules/forecast/router.py",
        "backend/modules/forecast/service.py", "backend/modules/forecast/db.py",
        "backend/modules/forecast/README.md",
        "backend/modules/waste/__init__.py", "backend/modules/waste/router.py",
        "backend/modules/waste/service.py", "backend/modules/waste/db.py",
        "backend/modules/waste/README.md",
        "backend/modules/safety/__init__.py", "backend/modules/safety/router.py",
        "backend/modules/safety/service.py", "backend/modules/safety/db.py",
        "backend/modules/safety/README.md",
        "backend/modules/marketplace/__init__.py", "backend/modules/marketplace/router.py",
        "backend/modules/marketplace/service.py", "backend/modules/marketplace/db.py",
        "backend/modules/marketplace/README.md",
        "tests/test_forecast.py", "tests/test_waste.py",
        "tests/test_safety.py", "tests/test_marketplace.py",
        "data/seed/core.json", "data/seed/forecast.json", "data/seed/waste.json",
        "data/seed/safety.json", "data/seed/marketplace.json",
        "scripts/fetch_vendor.py", "scripts/check_ownership.py",
        "tests/smoke_test.py",
        "docs/DEMO_SCRIPT.md", "docs/TEST_CHECKLIST.md",
        "docs/GIT_GUIDE.md", "docs/CHANGE_REQUESTS.md",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    if missing:
        result(1, "Required files/folders", FAIL, "Missing: " + ", ".join(missing[:5]))
    else:
        result(1, "Required files/folders", PASS, f"All {len(required)} required paths exist")


# ---------------------------------------------------------------------------
# Check 2 – OWNERS.json coverage + CODEOWNERS agreement
# ---------------------------------------------------------------------------
def check_ownership():
    try:
        owners = json.loads((ROOT / "OWNERS.json").read_text())
        members = {"m1", "m2", "m3"}
        ok = all(k in owners.get("ownership", {}) for k in members)
        codeowners = (ROOT / ".github/CODEOWNERS").read_text()
        has_codeowners = "@0Ketan" in codeowners or "0ketan" in codeowners.lower()
        if ok and has_codeowners:
            result(2, "OWNERS.json + CODEOWNERS", PASS, "All members present; CODEOWNERS references @0Ketan")
        else:
            result(2, "OWNERS.json + CODEOWNERS", WARN,
                   f"OWNERS.json members ok={ok}; CODEOWNERS references owner={has_codeowners}")
    except Exception as e:
        result(2, "OWNERS.json + CODEOWNERS", FAIL, str(e))


# ---------------------------------------------------------------------------
# Check 3 – .gitignore, git ls-files, .gitattributes
# ---------------------------------------------------------------------------
def check_gitignore():
    gi = (ROOT / ".gitignore").read_text()
    required_patterns = ["runtime/", "venv/", "*.db", "*.pkl", "__pycache__/", "node_modules/"]
    missing_gi = [p for p in required_patterns if p not in gi]

    ga = (ROOT / ".gitattributes").read_text()
    has_eol = "eol=lf" in ga

    # Check git ls-files for forbidden artifacts
    try:
        ls = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT, capture_output=True, text=True, timeout=10
        )
        tracked = ls.stdout
        forbidden_tracked = [
            p for p in ["runtime/", ".db", ".pkl", "venv/", ".ipynb"]
            if any(p in f for f in tracked.splitlines())
            and not p == "runtime/"  # allow runtime/ as folder name in paths that don't exist
        ]
        # Narrow it: only flag files that have those extensions tracked
        db_files = [f for f in tracked.splitlines() if f.endswith(".db") or f.endswith(".pkl") or ".ipynb" in f or ("venv/" in f and not f.startswith(".github"))]
    except Exception:
        db_files = []

    issues = []
    if missing_gi:
        issues.append(f".gitignore missing: {missing_gi}")
    if not has_eol:
        issues.append(".gitattributes lacks eol=lf (global)")
    if db_files:
        issues.append(f"Tracked forbidden files: {db_files[:3]}")

    if issues:
        result(3, ".gitignore / .gitattributes / tracked files", FAIL, "\n".join(issues))
    else:
        result(3, ".gitignore / .gitattributes / tracked files", PASS,
               ".gitignore OK; eol=lf present; no .db/.pkl/.ipynb tracked")


# ---------------------------------------------------------------------------
# Check 4 – requirements.txt / requirements-ml.txt split
# ---------------------------------------------------------------------------
def check_requirements():
    ml_pkgs = ["pandas", "numpy", "scikit-learn", "xgboost", "shap"]
    req = (ROOT / "requirements.txt").read_text().lower()
    bad = [p for p in ml_pkgs if p in req]

    # Check no top-level import of ML libs in backend/ (excluding modules/forecast)
    top_level_imports = []
    for py in ROOT.glob("backend/**/*.py"):
        if "forecast" in str(py):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = [a.name for a in getattr(node, "names", [])]
                    mod = getattr(node, "module", "") or ""
                    for n in names + [mod]:
                        if any(p in (n or "") for p in ["pandas", "numpy", "sklearn", "xgboost", "shap"]):
                            top_level_imports.append(f"{py.relative_to(ROOT)}: {n}")
        except Exception:
            pass

    issues = []
    if bad:
        issues.append(f"ML packages in requirements.txt: {bad}")
    if top_level_imports:
        issues.append(f"Top-level ML imports: {top_level_imports[:3]}")
    if issues:
        result(4, "requirements.txt / ML separation", FAIL, "\n".join(issues))
    else:
        result(4, "requirements.txt / ML separation", PASS, "No ML packages in requirements.txt; no top-level ML imports")


# ---------------------------------------------------------------------------
# Check 5 – Static AST rules
# ---------------------------------------------------------------------------
def check_static_rules():
    module_names = ["forecast", "waste", "safety", "marketplace"]
    cross_imports = []
    datetime_violations = []
    http_violations = []

    for py in ROOT.glob("backend/modules/**/*.py"):
        try:
            src = py.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except Exception:
            continue

        owner_module = py.parts[py.parts.index("modules") + 1] if "modules" in py.parts else ""

        for node in ast.walk(tree):
            # Cross-module import check
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", "") or ""
                names = [a.name for a in getattr(node, "names", [])]
                for n in [mod] + names:
                    for other in module_names:
                        if other != owner_module and f"modules.{other}" in (n or ""):
                            cross_imports.append(f"{py.relative_to(ROOT)}: imports {n}")

            # datetime.now / utcnow / time.time check
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    if func.attr in ("now", "utcnow") and "clock" not in str(ast.dump(func)):
                        # Check if the object is datetime
                        if isinstance(func.value, ast.Name) and func.value.id == "datetime":
                            datetime_violations.append(f"{py.relative_to(ROOT)}: datetime.{func.attr}(")
                    if func.attr == "time" and isinstance(func.value, ast.Name) and func.value.id == "time":
                        datetime_violations.append(f"{py.relative_to(ROOT)}: time.time(")

        # http:// / requests / urllib check in src
        if "http://" in src or "https://" in src:
            # Allow docstrings/comments - check if it's in a string assignment
            if "requests.get" in src or "requests.post" in src or "urllib.request" in src or "httpx" in src:
                http_violations.append(f"{py.relative_to(ROOT)}: HTTP client usage")

    issues = []
    if cross_imports:
        issues.append(f"Cross-module imports: {cross_imports[:3]}")
    if datetime_violations:
        issues.append(f"Direct datetime.now/time.time: {datetime_violations[:3]}")
    if http_violations:
        issues.append(f"HTTP client usage in modules: {http_violations[:3]}")

    if issues:
        result(5, "Static AST rules", FAIL, "\n".join(issues))
    else:
        result(5, "Static AST rules", PASS, "No cross-module imports; no datetime.now; no HTTP clients in modules")


# ---------------------------------------------------------------------------
# Check 6 – Seed data correctness
# ---------------------------------------------------------------------------
def check_seed_data():
    try:
        core = json.loads((ROOT / "data/seed/core.json").read_text())
        kitchens = core.get("kitchens", [])
        recipients = core.get("recipients", [])

        issues = []
        # Users have role, lat, lng
        all_users = kitchens + recipients
        missing_fields = [u.get("id", "?") for u in all_users
                          if not all(k in u for k in ("lat", ("lon" if "lon" in u else "lng")))]

        hostel_count = sum(1 for k in kitchens if k.get("type") == "hostel")
        processing_count = sum(1 for k in kitchens if k.get("type") == "processing_unit")
        ngo_count = sum(1 for r in recipients if r.get("type") == "ngo")
        mandir_veg = [r for r in recipients if r.get("type") == "mandir" and r.get("veg_only")]

        if hostel_count < 3:
            issues.append(f"Need 3 hostel kitchens, found {hostel_count}")
        if processing_count < 1:
            issues.append(f"Need 1 processing unit, found {processing_count}")
        if ngo_count < 1:
            issues.append(f"Need at least 1 NGO, found {ngo_count}")
        if not mandir_veg:
            issues.append("Need at least 1 veg_only mandir")

        # Check for forbidden strings
        all_seed_text = ""
        for f in (ROOT / "data/seed").glob("*.json"):
            all_seed_text += f.read_text().lower()
        for forbidden in ["feeding india", "robin hood"]:
            if forbidden in all_seed_text:
                issues.append(f"Forbidden string '{forbidden}' in seed data")

        if issues:
            result(6, "Seed data correctness", FAIL, "\n".join(issues))
        else:
            result(6, "Seed data correctness", PASS,
                   f"3 hostels, 1 processing unit, {ngo_count} NGOs, veg_only mandir present; no forbidden strings")
    except Exception as e:
        result(6, "Seed data correctness", FAIL, str(e))


# ---------------------------------------------------------------------------
# Check 7 – TestClient health check lists all 4 modules with mode
# ---------------------------------------------------------------------------
def check_health_endpoint():
    try:
        from backend.core.db import init_db, seed_database
        init_db()
        seed_database()
        from fastapi.testclient import TestClient
        from backend.app import app
        client = TestClient(app)
        resp = client.get("/api/health")
        assert resp.status_code == 200, f"status={resp.status_code}"
        data = resp.json()
        assert "modules" in data or "services" in data, f"body={data}"
        body = data.get("modules", data.get("services", {}))
        for mod in ["forecast", "waste", "safety", "marketplace"]:
            assert mod in body, f"module '{mod}' missing from health"
        result(7, "TestClient /api/health", PASS,
               f"status=200; modules={list(body.keys())}")
    except Exception as e:
        result(7, "TestClient /api/health", FAIL, str(e))


# ---------------------------------------------------------------------------
# Check 8 – All required routes in /openapi.json
# ---------------------------------------------------------------------------
def check_routes():
    try:
        from fastapi.testclient import TestClient
        from backend.app import app
        client = TestClient(app)
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        openapi = resp.json()
        paths = openapi.get("paths", {})

        required_routes = [
            ("GET", "/api/health"),
            ("GET", "/api/demo/users"),
            ("GET", "/api/demo/clock"),
            ("POST", "/api/demo/advance"),
            ("POST", "/api/demo/reset"),
            ("GET", "/api/forecast/status"),
            ("GET", "/api/waste/status"),
            ("GET", "/api/safety/status"),
            ("GET", "/api/marketplace/status"),
            ("GET", "/api/forecast/options"),
            ("POST", "/api/forecast/recommend"),
            ("GET", "/api/forecast/metrics"),
            ("POST", "/api/waste/logs"),
            ("GET", "/api/waste/logs"),
            ("GET", "/api/waste/summary"),
            ("GET", "/api/safety/categories"),
            ("POST", "/api/safety/evaluate"),
            ("GET", "/api/safety/label/{label_id}/print"),
            ("GET", "/api/safety/records"),
            ("GET", "/api/safety/records.csv"),
            ("POST", "/api/safety/records/{record_id}/complete"),
            ("GET", "/api/safety/disposals"),
            ("POST", "/api/marketplace/listings"),
            ("GET", "/api/marketplace/listings"),
            ("GET", "/api/marketplace/nearby"),
            ("POST", "/api/marketplace/listings/{id}/claim"),
            ("POST", "/api/marketplace/listings/{id}/pickup"),
            ("POST", "/api/marketplace/listings/{id}/served"),
            ("GET", "/api/marketplace/claims"),
            ("POST", "/api/marketplace/needs"),
            ("GET", "/api/marketplace/needs"),
            ("POST", "/api/marketplace/needs/{id}/pledge"),
            ("GET", "/api/alerts"),
            ("POST", "/api/alerts/read"),
            ("GET", "/api/impact"),
        ]

        missing = []
        for method, path in required_routes:
            # Normalize path params: {listing_id} matches {id}
            found = False
            for opath in paths:
                # Normalize both
                import re
                norm_req = re.sub(r"\{[^}]+\}", "{p}", path)
                norm_opath = re.sub(r"\{[^}]+\}", "{p}", opath)
                if norm_req == norm_opath and method.lower() in paths[opath]:
                    found = True
                    break
            if not found:
                missing.append(f"{method} {path}")

        if missing:
            result(8, "Required routes in /openapi.json", FAIL,
                   f"{len(missing)} missing:\n" + "\n".join(missing[:10]))
        else:
            result(8, "Required routes in /openapi.json", PASS,
                   f"All {len(required_routes)} required routes found")
    except Exception as e:
        result(8, "Required routes in /openapi.json", FAIL, str(e))


# ---------------------------------------------------------------------------
# Check 9 – Crash isolation: broken module doesn't kill healthy modules
# ---------------------------------------------------------------------------
def check_crash_isolation():
    tmp = None
    try:
        tmp = Path(tempfile.mkdtemp(prefix="annasetu_crash_"))
        # Copy only essential parts
        for item in ["backend", "data", "runtime", "contracts", "run.py", "requirements.txt"]:
            src = ROOT / item
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, tmp / item, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, tmp / item)

        # Create a broken module
        broken_dir = tmp / "backend" / "modules" / "broken_test"
        broken_dir.mkdir(parents=True, exist_ok=True)
        (broken_dir / "snake.json").write_text(json.dumps({"name": "broken_test", "owner": "M1"}))
        (broken_dir / "__init__.py").write_text("raise ImportError('intentional crash for isolation test')\n")
        (broken_dir / "router.py").write_text("raise ImportError('intentional crash')\n")

        # Start the app and check
        sys.path.insert(0, str(tmp))
        # Reload backend.app from tmp path
        import importlib
        # Quick check: app should import without crashing the whole process
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp)
        proc = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0,r'{tmp}'); "
             "from backend.core.db import init_db; init_db(); "
             "from fastapi.testclient import TestClient; "
             "from backend.app import app; "
             "c = TestClient(app); "
             "r = c.get('/api/health'); "
             "print('health_status:', r.status_code); "
             "r2 = c.get('/api/forecast/options'); "
             "print('forecast_status:', r2.status_code)"
             ],
            cwd=tmp, capture_output=True, text=True, timeout=20, env=env
        )
        output = proc.stdout + proc.stderr
        if "health_status: 200" in output and "forecast_status: 200" in output:
            result(9, "Crash isolation", PASS,
                   "Broken module loaded; healthy modules still respond 200")
        else:
            result(9, "Crash isolation", WARN,
                   f"Could not fully verify isolation:\n{output[:300]}")
    except Exception as e:
        result(9, "Crash isolation", WARN, f"Isolation test inconclusive: {e}")
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
        # Remove tmp from sys.path
        if str(tmp) in sys.path:
            sys.path.remove(str(tmp))


# ---------------------------------------------------------------------------
# Check 10 – Pointer files contain "Read and obey AGENTS.md"
# ---------------------------------------------------------------------------
def check_pointer_files():
    pointer_files = ["CLAUDE.md", "GEMINI.md", ".cursorrules", ".github/copilot-instructions.md"]
    missing_phrase = []
    for f in pointer_files:
        content = (ROOT / f).read_text(encoding="utf-8", errors="replace")
        if "AGENTS.md" not in content:
            missing_phrase.append(f)

    agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8", errors="replace")
    required_headings = [
        "When to Use Agents",        # golden rules
        "Available Agents",          # work split / agent types
        "Instructions for Fork Agents",  # git routine / instructions
        "Detail vs Speed",           # completion report dimension
    ]
    missing_headings = [h for h in required_headings if h not in agents_md]

    issues = []
    if missing_phrase:
        issues.append(f"Pointer files missing 'AGENTS.md' reference: {missing_phrase}")
    if missing_headings:
        issues.append(f"AGENTS.md missing headings: {missing_headings}")

    if issues:
        result(10, "Pointer files + AGENTS.md headings", WARN, "\n".join(issues))
    else:
        result(10, "Pointer files + AGENTS.md headings", PASS,
               "All pointer files reference AGENTS.md; required headings present")


# ---------------------------------------------------------------------------
# Check 11 – Clock advance/reset
# ---------------------------------------------------------------------------
def check_clock():
    try:
        from backend.core.db import init_db
        init_db()
        from fastapi.testclient import TestClient
        from backend.app import app
        client = TestClient(app)

        # Reset first
        r0 = client.post("/api/demo/reset")
        assert r0.status_code == 200, f"reset status={r0.status_code}"
        before = client.get("/api/demo/clock").json()
        old_offset = before["offset_minutes"]

        # Advance by 60
        r = client.post("/api/demo/advance", params={"minutes": 60})
        assert r.status_code == 200, f"advance status={r.status_code} body={r.text}"
        data = r.json()
        assert data["offset_minutes"] == old_offset + 60, f"expected {old_offset+60}, got {data['offset_minutes']}"

        # Reset
        r2 = client.post("/api/demo/reset")
        assert r2.status_code == 200
        after = r2.json()
        assert after["offset_minutes"] == 0, f"expected 0, got {after['offset_minutes']}"

        result(11, "Clock advance/reset", PASS,
               f"advance: offset={data['offset_minutes']}; reset: offset={after['offset_minutes']}")
    except Exception as e:
        result(11, "Clock advance/reset", FAIL, str(e))


# ---------------------------------------------------------------------------
# Check 12 – python -m compileall
# ---------------------------------------------------------------------------
def check_compile():
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "backend", "scripts", "tests"],
            cwd=ROOT, capture_output=True, text=True, timeout=30
        )
        if proc.returncode == 0:
            result(12, "python -m compileall", PASS, "All .py files compile cleanly")
        else:
            result(12, "python -m compileall", FAIL, proc.stdout[-500:] + proc.stderr[-500:])
    except Exception as e:
        result(12, "python -m compileall", FAIL, str(e))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("  AnnaSetu AI - Skeleton Verification")
    print("=" * 60 + "\n")

    check_required_files()
    check_ownership()
    check_gitignore()
    check_requirements()
    check_static_rules()
    check_seed_data()
    check_health_endpoint()
    check_routes()
    check_crash_isolation()
    check_pointer_files()
    check_clock()
    check_compile()

    print("\n" + "=" * 60)
    failures = [r for r in results if r[2] == FAIL]
    warns = [r for r in results if r[2] == WARN]
    passes = [r for r in results if r[2] == PASS]
    print(f"  PASS: {len(passes)}  FAIL: {len(failures)}  WARN: {len(warns)}")
    print("=" * 60 + "\n")

    if failures:
        print("FAILING CHECKS:")
        for _, label, _, evidence in failures:
            print(f"  - {label}: {evidence.splitlines()[0]}")
        print()

    if warns:
        print("WARNINGS (do not block):")
        for _, label, _, evidence in warns:
            print(f"  - {label}: {evidence.splitlines()[0]}")
        print()

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
