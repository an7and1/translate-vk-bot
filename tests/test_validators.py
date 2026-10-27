import pytest

from app.services.validators import (
    SUPPORTED_LANGUAGES,
    is_valid_language,
    language_label,
    normalize_text,
    validate_pair,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  hello  ", "hello"),
        ("  привет  ", "привет"),
        ("a", "a"),
    ],
)
def test_normalize_text_ok(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "x" * 501])
def test_normalize_text_invalid(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_text(raw)


def test_language_codes() -> None:
    assert is_valid_language("ru")
    assert is_valid_language("en")
    assert not is_valid_language("xx")
    assert "ru" in SUPPORTED_LANGUAGES
    assert language_label("ru") == "Русский"


def test_validate_pair() -> None:
    validate_pair("en", "ru")
    validate_pair("auto", "ru")
    with pytest.raises(ValueError):
        validate_pair("ru", "ru")
