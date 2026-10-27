"""Бизнес-сценарий: валидация -> перевод -> сохранение."""
from __future__ import annotations

from dataclasses import dataclass

from app.db.repository import save_translation, update_pair
from app.services.translator import (
    RateLimitError,
    TranslationError,
    TranslationResult,
    translate_text,
)
from app.services.validators import normalize_text, validate_pair


@dataclass(frozen=True)
class ScenarioOutcome:
    result: TranslationResult | None = None
    error: str | None = None


async def run_translation(
    user_id: int,
    vk_id: int,
    raw_text: str,
    source_lang: str,
    target_lang: str,
) -> ScenarioOutcome:
    try:
        text = normalize_text(raw_text)
        validate_pair(source_lang, target_lang)
    except ValueError as exc:
        err = "same_lang" if "совпадают" in str(exc) else "invalid"
        return ScenarioOutcome(error=f"{err}:{exc}")

    try:
        result = await translate_text(text, source_lang, target_lang)
    except RateLimitError:
        return ScenarioOutcome(error="rate_limit")
    except TranslationError:
        return ScenarioOutcome(error="service_down")

    await save_translation(
        user_id=user_id,
        source_text=text,
        translated_text=result.text,
        source_lang=source_lang,
        target_lang=target_lang,
        provider=result.provider,
    )
    await update_pair(vk_id=vk_id, source=source_lang, target=target_lang)
    return ScenarioOutcome(result=result)
