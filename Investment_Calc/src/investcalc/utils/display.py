"""Display helpers for the CLI."""

from typing import Any


CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def print_header(title: str) -> None:
    width = 60
    print(f"\n{CYAN}{'═' * width}")
    print(f"  {BOLD}{title}{RESET}{CYAN}")
    print(f"{'═' * width}{RESET}\n")


def print_menu(title: str, menu: dict[str, str]) -> None:
    print(f"\n{YELLOW}  ── {title} ──{RESET}")
    for key, label in menu.items():
        print(f"    {BOLD}{key}{RESET}  {label}")
    print()


def print_result(result: Any) -> None:
    print(f"\n  {GREEN}► {result}{RESET}\n")


def print_dict(title: str, data: dict) -> None:
    print(f"\n  {GREEN}── {title} ──{RESET}")
    for k, v in data.items():
        if isinstance(v, float):
            print(f"    {k:<22} {v:,.4f}")
        else:
            print(f"    {k:<22} {v}")
    print()
