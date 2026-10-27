"""Клиенты перевода: MyMemory (основной) и LibreTranslate (fallback)."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import aiohttp

from app.config import get_settings

log = logging.getLogger(__name__)


class TranslationError(Exception):
    """Базовая ошибка перевода."""


class RateLimitError(TranslationError):
    """Сервис ограничил частоту запросов."""


@dataclass(frozen=True)
class TranslationResult:
    text: str
    source_lang: str
    target_lang: str
    provider: str


async def _mymemory(
    session: aiohttp.ClientSession, text: str, source: str, target: str
) -> str:
    # MyMemory не понимает "auto" — для автоопределения нужен "autodetect"
    mymemory_source = "autodetect" if source == "auto" else source
    params = {"q": text, "langpair": f"{mymemory_source}|{target}"}
    async with session.get(get_settings().mymemory_url, params=params) as resp:
        if resp.status == 429:
            raise RateLimitError("MyMemory: слишком много запросов.")
        data = await resp.json(content_type=None)

    payload = data.get("responseData") or {}
    translated = (payload.get("translatedText") or "").strip()
    status = int(data.get("responseStatus") or 200)
    if status != 200 or not translated:
        details = data.get("responseDetails") or "пустой ответ"
        raise TranslationError(f"MyMemory: {details}")
    lowered = translated.lower()
    if "too many requests" in lowered or "please select two distinct" in lowered:
        raise RateLimitError(f"MyMemory: {translated}")
    return translated


async def _libretranslate(
    session: aiohttp.ClientSession, text: str, source: str, target: str
) -> str:
    data = {
        "q": text,
        "source": "auto" if source == "auto" else source,
        "target": target,
        "format": "text",
    }
    async with session.post(get_settings().libretranslate_url, data=data) as resp:
        if resp.status == 429:
            raise RateLimitError("LibreTranslate: слишком много запросов.")
        if resp.status != 200:
            raise TranslationError(f"LibreTranslate: HTTP {resp.status}")
        payload = await resp.json(content_type=None)

    translated = (payload.get("translatedText") or "").strip()
    if not translated:
        raise TranslationError("LibreTranslate: пустой ответ.")
    return translated


async def translate_text(
    text: str, source: str, target: str
) -> TranslationResult:
    """Пробует провайдеров по очереди. Возвращает первый успешный ответ.

    Raises:
        RateLimitError: если оба сервиса ответили 429.
        TranslationError: если оба сервиса недоступны.
    """
    settings = get_settings()
    timeout = aiohttp.ClientTimeout(total=settings.translate_timeout)
    errors: list[str] = []
    rate_limited = 0

    async with aiohttp.ClientSession(timeout=timeout) as session:
        providers = (
            ("mymemory", _mymemory),
            ("libretranslate", _libretranslate),
        )
        for provider_name, fn in providers:
            try:
                translated = await fn(session, text, source, target)
                log.info("Перевод успешен через %s", provider_name)
                return TranslationResult(
                    text=translated,
                    source_lang=source,
                    target_lang=target,
                    provider=provider_name,
                )
            except RateLimitError as exc:
                rate_limited += 1
                errors.append(f"{provider_name}: {exc}")
                log.warning("%s", errors[-1])
            except (aiohttp.ClientError, TranslationError) as exc:
                errors.append(f"{provider_name}: {exc}")
                log.warning("%s", errors[-1])

    if rate_limited == 2:
        raise RateLimitError("Оба сервиса перевода ограничили частоту запросов.")
    raise TranslationError("Сервисы перевода недоступны. Попробуйте позже.")