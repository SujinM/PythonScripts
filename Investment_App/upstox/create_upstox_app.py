"""
create_upstox_app.py
======================
Generates the installable `upstox_app` package by copying `app/` and
rewriting all internal imports from `from app.` → `from upstox_app.`.

IMPORTANT — architecture note
------------------------------
`upstox_app/` contains the REAL implementations (the distributed package).
`app/` contains thin wrappers that re-export from `upstox_app/`.

This script is designed for the OPPOSITE layout where `app/` has real code
and `upstox_app/` is the generated copy.  If `app/` only contains wrappers
(the current layout), running this script would create circular imports and
destroy the real implementations in `upstox_app/`.

This script will abort automatically if it detects that `app/` files are
wrapper stubs rather than real implementations.

Run from the upstox project root:
    python create_upstox_app.py
"""

import re
import shutil
import sys
from pathlib import Path

WRAPPER_MARKER = "# Auto-generated wrapper"


def _check_source_not_wrappers(src: Path) -> None:
    """Abort if app/ files are already wrapper stubs (circular-import risk)."""
    wrapper_files = [
        f for f in src.rglob("*.py")
        if f.name != "__init__.py"
        and WRAPPER_MARKER in f.read_text(encoding="utf-8")
    ]
    if wrapper_files:
        print("ERROR: The following app/ files are wrapper stubs, not real implementations.", file=sys.stderr)
        for f in wrapper_files:
            print(f"  {f}", file=sys.stderr)
        print(
            "\nRunning this script would copy the wrappers into upstox_app/ and create\n"
            "circular imports, destroying the real code.\n\n"
            "The real implementations already live in upstox_app/.\n"
            "There is nothing to generate — aborting.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    root = Path(__file__).resolve().parent
    src = root / "app"
    dst = root / "upstox_app"

    if not src.is_dir():
        print(f"ERROR: source directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    _check_source_not_wrappers(src)

    if dst.exists():
        print(f"Removing existing {dst}")
        shutil.rmtree(dst)

    shutil.copytree(src, dst)
    print(f"Copied {src} → {dst}")

    py_files = list(dst.rglob("*.py"))
    count = 0
    for f in py_files:
        original = f.read_text(encoding="utf-8")
        updated = re.sub(r"\bfrom app\.", "from upstox_app.", original)
        updated = re.sub(r"\bimport app\.", "import upstox_app.", updated)
        if updated != original:
            f.write_text(updated, encoding="utf-8")
            count += 1
            print(f"  Updated imports: {f.relative_to(root)}")

    print(f"\nDone. {count}/{len(py_files)} file(s) had imports rewritten.")


if __name__ == "__main__":
    main()
