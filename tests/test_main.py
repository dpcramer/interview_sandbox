import pytest

from interview_sandbox.main import GREETINGS, greet, main


def test_greet_default():
    assert greet() == "Hello, World!"


def test_greet_name(name):
    assert greet(name) == f"Hello, {name}!"


def test_greet_strips_whitespace(name):
    assert greet(f"  {name}  ") == f"Hello, {name}!"


def test_greet_empty_name_raises():
    with pytest.raises(ValueError):
        greet("   ")


def test_main_prints_greeting(capsys, name):
    assert main([name]) == 0
    assert capsys.readouterr().out == f"Hello, {name}!\n"


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("en", "Hello, World!"),
        ("es", "¡Hola, mundo!"),
        ("fr", "Bonjour, le monde !"),
        ("de", "Hallo, Welt!"),
        ("zh", "你好，世界！"),
    ],
)
def test_greet_default_name_is_localized(language, expected):
    assert greet(language=language) == expected


def test_greet_name_in_language(name):
    assert greet(name, language="pt") == f"Olá, {name}!"


def test_greet_supports_twelve_languages():
    assert len(GREETINGS) == 12
    for language in GREETINGS:
        assert greet(language=language)


def test_greet_language_is_case_insensitive(name):
    assert greet(name, language=" ES ") == f"¡Hola, {name}!"


def test_greet_unsupported_language_raises(name):
    with pytest.raises(ValueError, match="unsupported language"):
        greet(name, language="xx")


def test_main_default_prints_hello_world(capsys):
    assert main([]) == 0
    assert capsys.readouterr().out == "Hello, World!\n"


def test_main_lang_flag(capsys, name):
    assert main([name, "--lang", "de"]) == 0
    assert capsys.readouterr().out == f"Hallo, {name}!\n"


def test_main_rejects_unknown_lang():
    with pytest.raises(SystemExit):
        main(["--lang", "xx"])
