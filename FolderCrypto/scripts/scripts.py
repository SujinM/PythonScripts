"""
Makefile-style command runner for development tasks.
Usage: python scripts.py <command>
"""

import sys
import subprocess
from pathlib import Path


def run(cmd: str) -> int:
    """Run a shell command."""
    print(f"→ {cmd}")
    return subprocess.call(cmd, shell=True)


def test() -> int:
    """Run all tests."""
    return run("pytest -v --cov=app --cov-report=term-missing --cov-report=html")


def test_fast() -> int:
    """Run tests without coverage."""
    return run("pytest -v")


def format_code() -> int:
    """Format code with Black."""
    return run("black app/ tests/")


def lint() -> int:
    """Run ruff linter."""
    return run("ruff check app/ tests/")


def typecheck() -> int:
    """Run mypy type checker."""
    return run("mypy app/")


def check() -> int:
    """Run all quality checks."""
    print("=" * 60)
    print("Running code quality checks...")
    print("=" * 60)

    commands = [
        ("Black format check", "black --check app/ tests/"),
        ("Ruff linter", "ruff check app/ tests/"),
        ("Mypy type check", "mypy app/"),
        ("Tests", "pytest --tb=short"),
    ]

    failed = []
    for name, cmd in commands:
        print(f"\n{'=' * 60}")
        print(f"Running: {name}")
        print(f"{'=' * 60}")
        if run(cmd) != 0:
            failed.append(name)

    print(f"\n{'=' * 60}")
    if failed:
        print(f"FAILED checks: {', '.join(failed)}")
        return 1
    else:
        print("All checks passed!")
        return 0


def clean() -> int:
    """Clean generated files."""
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        ".coverage",
        "dist",
        "build",
        "*.egg-info",
    ]

    for pattern in patterns:
        for path in Path(".").rglob(pattern):
            if path.is_file():
                path.unlink()
                print(f"Removed: {path}")
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
                print(f"Removed: {path}/")

    return 0


def help_text() -> int:
    """Show available commands."""
    print("""
Available commands:

  test         Run all tests with coverage
  test-fast    Run tests without coverage
  format       Format code with Black
  lint         Run ruff linter
  typecheck    Run mypy type checker
  check        Run all quality checks
  clean        Clean generated files
  help         Show this help message

Usage:
  python scripts.py <command>
    """)
    return 0


if __name__ == "__main__":
    commands = {
        "test": test,
        "test-fast": test_fast,
        "format": format_code,
        "lint": lint,
        "typecheck": typecheck,
        "check": check,
        "clean": clean,
        "help": help_text,
    }

    if len(sys.argv) < 2:
        print("Error: No command specified")
        help_text()
        sys.exit(1)

    command = sys.argv[1]
    if command not in commands:
        print(f"Error: Unknown command '{command}'")
        help_text()
        sys.exit(1)

    sys.exit(commands[command]())
