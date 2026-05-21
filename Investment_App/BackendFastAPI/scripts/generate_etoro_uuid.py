#!/usr/bin/env python
"""
scripts/generate_etoro_uuid.py
────────────────────────────────
Generate UUIDs for eToro API testing.

Produces:
  - x-request-id  : random UUID4 used per API call
  - Bulk list      : multiple UUIDs at once (--count N)
  - Copy-ready     : formatted for use in headers / .env / curl

Usage (run from BackendFastAPI/ directory):
    python scripts/generate_etoro_uuid.py
    python scripts/generate_etoro_uuid.py --count 5
    python scripts/generate_etoro_uuid.py --count 1 --curl
    python scripts/generate_etoro_uuid.py --count 1 --env
"""

from __future__ import annotations

import argparse
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


def build_etoro_headers(request_id: str) -> dict[str, str]:
    """Return the eToro request headers with the given x-request-id."""
    return {
        "x-api-key":    "<YOUR_ETORO_API_KEY>",
        "x-user-key":   "<YOUR_ETORO_USER_KEY>",
        "x-request-id": request_id,
        "Accept":       "application/json",
    }


def print_plain(uuids: list[str]) -> None:
    print("Generated UUID(s):")
    for u in uuids:
        print(f"  {u}")


def print_curl(request_id: str) -> None:
    print("curl headers:")
    print(f'  -H "x-request-id: {request_id}" \\')
    print(f'  -H "x-api-key: <YOUR_ETORO_API_KEY>" \\')
    print(f'  -H "x-user-key: <YOUR_ETORO_USER_KEY>" \\')
    print(f'  -H "Accept: application/json"')


def print_env(request_id: str) -> None:
    print("# .env / environment variable:")
    print(f"ETORO_REQUEST_ID={request_id}")


def print_headers(request_id: str) -> None:
    headers = build_etoro_headers(request_id)
    print("Python headers dict:")
    print("  headers = {")
    for k, v in headers.items():
        print(f'      "{k}": "{v}",')
    print("  }")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate UUID(s) for eToro API testing."
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=1,
        help="Number of UUIDs to generate (default: 1)",
    )
    parser.add_argument(
        "--curl",
        action="store_true",
        help="Print curl-ready header flags",
    )
    parser.add_argument(
        "--env",
        action="store_true",
        help="Print .env-style variable",
    )
    parser.add_argument(
        "--headers",
        action="store_true",
        help="Print Python headers dict",
    )
    args = parser.parse_args()

    uuids = [generate_uuid() for _ in range(args.count)]

    # Always print the plain list
    print_plain(uuids)

    # Additional output formats (use first UUID for single-value formats)
    first = uuids[0]

    if args.curl:
        print()
        print_curl(first)

    if args.env:
        print()
        print_env(first)

    if args.headers:
        print()
        print_headers(first)

    # Default: show headers when no extra flag given and only 1 UUID requested
    if not (args.curl or args.env or args.headers):
        print()
        print_headers(first)


if __name__ == "__main__":
    main()
