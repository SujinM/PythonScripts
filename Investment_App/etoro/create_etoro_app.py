"""
create_etoro_app.py
====================
Generates the installable `etoro_app` package by copying `app/` and
rewriting all internal imports from `from app.` → `from etoro_app.`.

Run from the etoro project root:
    python create_etoro_app.py
"""

import re
import shutil
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    src = root / "app"
    dst = root / "etoro_app"

    if not src.is_dir():
        print(f"ERROR: source directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    if dst.exists():
        print(f"Removing existing {dst}")
        shutil.rmtree(dst)

    shutil.copytree(src, dst)
    print(f"Copied {src} → {dst}")

    py_files = list(dst.rglob("*.py"))
    count = 0
    for f in py_files:
        original = f.read_text(encoding="utf-8")
        updated = re.sub(r"\bfrom app\.", "from etoro_app.", original)
        updated = re.sub(r"\bimport app\.", "import etoro_app.", updated)
        if updated != original:
            f.write_text(updated, encoding="utf-8")
            count += 1
            print(f"  Updated imports: {f.relative_to(root)}")

    print(f"\nDone. {count}/{len(py_files)} file(s) had imports rewritten.")


if __name__ == "__main__":
    main()
