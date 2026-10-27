"""Лёгкий in-memory менеджер состояний диалога.

Шаги:
- "choosing_source" — выбираем исходный язык;
- "choosing_target" — выбираем целевой язык (source_lang уже установлен);
- "waiting_text"     — ждём текст для перевода;
- "waiting_text_to_ru" — ждём текст, переводим на русский (авто-режим).
"""
from typing import TypedDict


class UserFlow(TypedDict, total=False):
    step: str
    source_lang: str
    target_lang: str


_store: dict[int, UserFlow] = {}


def get_flow(user_id: int) -> UserFlow:
    return _store.get(user_id, {})


def set_flow(user_id: int, **kwargs: str) -> None:
    flow = _store.setdefault(user_id, {})
    flow.update(kwargs)  # type: ignore[typeddict-item]


def clear_flow(user_id: int) -> None:
    _store.pop(user_id, None)