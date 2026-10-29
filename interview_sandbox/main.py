"""Hello world entry point. Run with: python -m interview_sandbox.main"""

import argparse

# The 12 most-spoken languages (Ethnologue), keyed by ISO 639-1 code.
# Each entry is (greeting template, localized word for "World").
GREETINGS: dict[str, tuple[str, str]] = {
    "en": ("Hello, {name}!", "World"),  # English
    "zh": ("你好，{name}！", "世界"),  # Mandarin Chinese
    "hi": ("नमस्ते, {name}!", "दुनिया"),  # Hindi
    "es": ("¡Hola, {name}!", "mundo"),  # Spanish
    "ar": ("مرحبا، {name}!", "العالم"),  # Arabic
    "fr": ("Bonjour, {name} !", "le monde"),  # French
    "bn": ("নমস্কার, {name}!", "বিশ্ব"),  # Bengali
    "pt": ("Olá, {name}!", "mundo"),  # Portuguese
    "ru": ("Привет, {name}!", "мир"),  # Russian
    "id": ("Halo, {name}!", "dunia"),  # Indonesian
    "ur": ("سلام، {name}!", "دنیا"),  # Urdu
    "de": ("Hallo, {name}!", "Welt"),  # German
}
DEFAULT_LANGUAGE = "en"


def greet(name: str | None = None, language: str = DEFAULT_LANGUAGE) -> str:
    """Return a greeting for the given name in the given language.

    With no name, greets the world in that language.
    """
    code = language.strip().lower()
    if code not in GREETINGS:
        supported = ", ".join(GREETINGS)
        raise ValueError(f"unsupported language {language!r}; use one of: {supported}")
    template, world = GREETINGS[code]

    if name is None:
        name = world
    name = name.strip()
    if not name:
        raise ValueError("name must not be empty")
    return template.format(name=name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a greeting.")
    parser.add_argument("name", nargs="?", help="who to greet (default: the world)")
    parser.add_argument(
        "-l",
        "--lang",
        default=DEFAULT_LANGUAGE,
        choices=sorted(GREETINGS),
        help=f"language code (default: {DEFAULT_LANGUAGE})",
    )
    args = parser.parse_args(argv)
    print(greet(args.name, language=args.lang))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
