import pytest

from interview_sandbox.main import greet, main


def test_greet_default():
    assert greet() == "Hello, Joe!"


def test_greet_name():
    assert greet("Ada") == "Hello, Ada!"


def test_greet_strips_whitespace():
    assert greet("  Ada  ") == "Hello, Ada!"


def test_greet_empty_name_raises():
    with pytest.raises(ValueError):
        greet("   ")


def test_main_prints_greeting(capsys):
    assert main(["Ada"]) == 0
    assert capsys.readouterr().out == "Hello, Ada!\n"
