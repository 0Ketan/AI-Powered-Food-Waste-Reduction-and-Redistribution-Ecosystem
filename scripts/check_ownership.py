#!/usr/bin/env python3
"""
Check Ownership Script
Verifies file ownership against OWNERS.json.
Supports:
  python scripts/check_ownership.py
  python scripts/check_ownership.py --member M1
"""
import sys
import json
import argparse
import fnmatch
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def matches_pattern(file_path: str, pattern: str) -> bool:
    """Check if normalized path matches OWNERS pattern."""
    p = file_path.replace("\\", "/").strip("/")
    pat = pattern.replace("\\", "/").strip("/")
    
    # Exact match (case-insensitive)
    if p.lower() == pat.lower():
        return True
        
    if pat.endswith("/**"):
        prefix = pat[:-3].lower()
        return p.lower() == prefix or p.lower().startswith(prefix + "/")
    elif pat.endswith("/*"):
        prefix = pat[:-2].lower()
        return p.lower().startswith(prefix + "/") and "/" not in p[len(prefix)+1:]
    
    # Root level files without slashes (e.g. README.md, run.py, requirements*.txt)
    if "/" not in pat:
        return "/" not in p and fnmatch.fnmatch(p.lower(), pat.lower())
    
    return fnmatch.fnmatch(p.lower(), pat.lower())


def get_owner_for_file(file_path: str, ownership: dict) -> list:
    """Return all members that own this file."""
    matching_owners = []
    for member, patterns in ownership.items():
        for pat in patterns:
            if matches_pattern(file_path, pat):
                if member.upper() not in matching_owners:
                    matching_owners.append(member.upper())
                break
    return matching_owners


def get_git_files(args=None):
    """Get list of files tracked by git."""
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except Exception:
        # Fallback to scanning project files
        files = []
        for p in PROJECT_ROOT.rglob("*"):
            if p.is_file() and not any(part in p.parts for part in ['venv', '.git', '__pycache__', 'runtime', 'node_modules']):
                files.append(str(p.relative_to(PROJECT_ROOT)))
        return files


def get_changed_files():
    """Get modified/staged/untracked files in working tree."""
    changed = set()
    try:
        # Check diff against HEAD
        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True
        )
        if res.returncode == 0:
            changed.update(res.stdout.splitlines())
            
        # Check cached / staged diff
        res2 = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=PROJECT_ROOT, capture_output=True, text=True
        )
        if res2.returncode == 0:
            changed.update(res2.stdout.splitlines())
            
        # Check status for untracked / uncommitted changes
        res3 = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT, capture_output=True, text=True
        )
        if res3.returncode == 0:
            for line in res3.stdout.splitlines():
                if len(line) > 3:
                    changed.add(line[3:].strip().replace('"', ''))
    except Exception:
        pass
        
    # Clean paths and filter out ignored/runtime paths
    cleaned = []
    for f in changed:
        f = f.strip().replace("\\", "/")
        if not f or any(f.startswith(p) for p in ['venv/', 'runtime/', '.git/', '__pycache__/']):
            continue
        cleaned.append(f)
    return cleaned


def main():
    parser = argparse.ArgumentParser(description="Verify file ownership per OWNERS.json")
    parser.add_argument("--member", type=str, help="Validate changes only belong to specified member (e.g. M1, M2, M3)")
    args = parser.parse_args()

    owners_file = PROJECT_ROOT / "OWNERS.json"
    if not owners_file.exists():
        print("ERROR: OWNERS.json not found")
        return 1

    with open(owners_file, "r", encoding="utf-8") as f:
        owners_data = json.load(f)

    ownership = owners_data.get("ownership", {})

    # If --member is provided, check changed files for violations
    if args.member:
        target_member = args.member.strip().upper()
        target_key = target_member.lower()

        if target_key not in ownership:
            print(f"ERROR: Unknown member '{args.member}'. Valid members: {list(ownership.keys())}")
            return 1

        changed_files = get_changed_files()
        violations = []

        for f in changed_files:
            owners = get_owner_for_file(f, ownership)
            if target_member not in owners:
                owned_by = ", ".join(owners) if owners else "unowned"
                violations.append(f"OWNERSHIP VIOLATION: '{f}' is not owned by {target_member} (owned by: {owned_by})")

        if violations:
            print(f"OWNERSHIP CHECK FAILED for member {target_member}:")
            for v in violations:
                print(f"  {v}")
            return 1
        else:
            if changed_files:
                print(f"OWNERSHIP CHECK PASSED: All {len(changed_files)} changed file(s) belong to {target_member}")
            else:
                print(f"OWNERSHIP CHECK PASSED: No changed files (clean working tree for {target_member})")
            return 0

    # Global check: check all tracked files
    tracked_files = get_git_files()
    errors = []
    
    for f in tracked_files:
        f_norm = f.replace("\\", "/")
        if any(f_norm.startswith(p) for p in ['venv/', 'runtime/', '.git/', 'node_modules/']):
            continue
        owners = get_owner_for_file(f_norm, ownership)
        if len(owners) == 0:
            errors.append(f"UNOWNED FILE: {f_norm}")
        elif len(owners) > 1:
            errors.append(f"OWNERSHIP CONFLICT: {f_norm} owned by multiple members: {', '.join(owners)}")

    if errors:
        print("OWNERSHIP CHECK FAILED:")
        for err in errors[:20]:
            print(f"  {err}")
        return 1

    print("OWNERSHIP CHECK PASSED: All files properly owned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
