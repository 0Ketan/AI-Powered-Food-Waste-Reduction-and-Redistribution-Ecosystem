"""
Frontend Static Link & Asset Checker (M1)
Parses every HTML file in frontend/ and verifies every local <script src>,
<link href>, and <a href> target exists (vendor files only warn).
"""
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).parent.parent
FRONTEND_DIR = ROOT / "frontend"


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        if tag == "script" and "src" in attr_map:
            self.refs.append(("script", attr_map["src"]))
        elif tag == "link" and "href" in attr_map:
            self.refs.append(("link", attr_map["href"]))
        elif tag == "a" and "href" in attr_map:
            self.refs.append(("a", attr_map["href"]))


def _resolve_target(html_file: Path, ref: str) -> Path | None:
    clean = ref.split("#", 1)[0].split("?", 1)[0].strip()
    if not clean:
        return None
    if clean.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
        return None
    if clean.startswith("/api/"):
        return None
    if clean.startswith("/"):
        return FRONTEND_DIR / clean.lstrip("/")
    return (html_file.parent / clean).resolve()


def check_all_frontend_html() -> tuple[list[str], list[str], int]:
    html_files = sorted(FRONTEND_DIR.rglob("*.html"))
    failures = []
    warnings = []

    for html_file in html_files:
        parser = AssetParser()
        parser.feed(html_file.read_text(encoding="utf-8"))
        rel_html = html_file.relative_to(FRONTEND_DIR)

        for tag, ref in parser.refs:
            target = _resolve_target(html_file, ref)
            if target is None:
                continue
            if not target.exists():
                msg = f"{rel_html}: <{tag}> target missing -> {ref}"
                if "vendor/" in ref.replace("\\", "/"):
                    warnings.append(msg)
                else:
                    failures.append(msg)

    return failures, warnings, len(html_files)


def test_frontend_links():
    """Pytest entry point for frontend HTML link/asset verification."""
    failures, warnings, count = check_all_frontend_html()
    assert count >= 9, f"Expected at least 9 HTML pages, found {count}"
    for w in warnings:
        print(f"WARN: {w}")
    assert not failures, "Broken frontend references:\n" + "\n".join(failures)


if __name__ == "__main__":
    failures, warnings, count = check_all_frontend_html()
    print(f"Checked {count} HTML file(s) in {FRONTEND_DIR}")
    for w in warnings:
        print(f"WARN: {w}")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        sys.exit(1)
    print("PASS: All local <script>, <link>, and <a> targets exist.")
    sys.exit(0)
