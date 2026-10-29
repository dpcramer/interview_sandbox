"""Hello world entry point. Run with: python -m interview_sandbox.main"""

import sys


def greet(name: str = "World") -> str:
    """Return a greeting for the given name."""
    name = name.strip()
    if not name:
        raise ValueError("name must not be empty")
    return f"Hello, {name}!"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    print(greet(args[0]) if args else greet())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
