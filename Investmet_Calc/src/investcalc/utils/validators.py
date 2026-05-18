"""Input validation helpers."""


def get_float(prompt: str) -> float:
    while True:
        raw = input(f"  {prompt}: ").strip()
        try:
            return float(raw.replace(",", ""))
        except ValueError:
            print("  Please enter a valid number.")


def get_int(prompt: str) -> int:
    while True:
        raw = input(f"  {prompt}: ").strip()
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a valid integer.")


def get_choice(prompt: str, options: list[str]) -> str:
    opts = "/".join(options)
    while True:
        raw = input(f"  {prompt} ({opts}): ").strip().lower()
        if raw in options:
            return raw
        print(f"  Choose one of: {opts}")
