"""Быстрая проверка работоспособности ключевых модулей.

Запуск: python smoke_test.py
"""
import asyncio

from app.services.validators import (
    is_valid_language,
    normalize_text,
    SUPPORTED_LANGUAGES,
)
from app.domain.texts import welcome_text


def check_validators() -> None:
    assert normalize_text("  hello  ") == "hello"
    assert is_valid_language("ru")
    assert not is_valid_language("xx")
    assert "ru" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES
    print("OK validators")


def check_texts() -> None:
    text = welcome_text(has_pair=False)
    assert "перевод" in text.lower()
    assert "русск" in text.lower()
    print("OK texts")


async def main() -> None:
    check_validators()
    check_texts()
    print("\nOK smoke test")


if __name__ == "__main__":
    asyncio.run(main())