"""Клавиатуры:
- inline  — до 10 кнопок суммарно (жёсткий лимит VK),
- regular — до 50 кнопок (10 рядов × 5).

Для «Ещё →» используем именно regular-клавиатуру, чтобы показать все
языки разом без пагинации.
"""
from vkbottle import Callback, Keyboard, KeyboardButtonColor, Text

from app.services.validators import (
    OTHER_LANGUAGES,
    POPULAR_LANGUAGES,
    language_label,
)


# --- постоянная клавиатура главного меню ---

def welcome_keyboard() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("Выбрать пару языков"), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("На русский"), color=KeyboardButtonColor.POSITIVE)
    kb.add(Text("История"), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


# --- инлайн-клавиатуры для популярного выбора ---

def pair_confirm_keyboard(target: str) -> str:
    kb = Keyboard(inline=True)
    kb.add(
        Callback(
            f"Продолжить ({language_label(target)})",
            payload={"cmd": "keep_pair"},
        ),
        color=KeyboardButtonColor.POSITIVE,
    )
    kb.add(
        Callback("Сменить пару", payload={"cmd": "change_pair"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    return kb.get_json()


def source_language_keyboard() -> str:
    kb = Keyboard(inline=True)
    kb.add(
        Callback("🔍 Автоопределение", payload={"cmd": "source_auto"}),
        color=KeyboardButtonColor.PRIMARY,
    )
    kb.row()
    for i in range(0, 3):
        code = POPULAR_LANGUAGES[i]
        kb.add(
            Callback(
                language_label(code),
                payload={"cmd": "source_lang", "lang": code},
            )
        )
    kb.row()
    for i in range(3, 6):
        code = POPULAR_LANGUAGES[i]
        kb.add(
            Callback(
                language_label(code),
                payload={"cmd": "source_lang", "lang": code},
            )
        )
    kb.row()
    kb.add(
        Callback("Ещё →", payload={"cmd": "source_more"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    kb.add(
        Callback("🔁 Сразу на русский", payload={"cmd": "to_russian"}),
        color=KeyboardButtonColor.POSITIVE,
    )
    return kb.get_json()


def _popular_targets(source: str) -> list[str]:
    return [c for c in POPULAR_LANGUAGES if c != source]


def target_language_keyboard(source: str) -> str:
    kb = Keyboard(inline=True)
    targets = _popular_targets(source)
    for i in range(0, min(len(targets), 6), 3):
        if i > 0:
            kb.row()
        for code in targets[i : i + 3]:
            kb.add(
                Callback(
                    language_label(code),
                    payload={"cmd": "target_lang", "lang": code},
                )
            )
    kb.row()
    kb.add(
        Callback("Ещё →", payload={"cmd": "target_more"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    kb.add(
        Callback("← Назад", payload={"cmd": "target_back"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    return kb.get_json()


def after_translation_keyboard() -> str:
    kb = Keyboard(inline=True)
    kb.add(
        Callback("Ещё перевод", payload={"cmd": "again"}),
        color=KeyboardButtonColor.POSITIVE,
    )
    kb.add(
        Callback("Сменить пару", payload={"cmd": "change_pair"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    kb.row()
    kb.add(
        Callback("История", payload={"cmd": "show_history"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    return kb.get_json()


# --- обычные клавиатуры полного списка ---

def _build_full_languages_keyboard(
    codes: list[str], nav_buttons: list[tuple[str, str]]
) -> str:
    """Регулярная клавиатура: языки по 5 в ряд + ряд навигации."""
    kb = Keyboard(one_time=False, inline=False)
    chunk = 5
    for i in range(0, len(codes), chunk):
        if i:
            kb.row()
        for code in codes[i : i + chunk]:
            kb.add(Text(language_label(code)))
    kb.row()
    for label, color_name in nav_buttons:
        color = getattr(KeyboardButtonColor, color_name)
        kb.add(Text(label), color=color)
    return kb.get_json()


def full_source_languages_keyboard() -> str:
    """Полный список исходных языков на обычной клавиатуре."""
    return _build_full_languages_keyboard(
        OTHER_LANGUAGES,
        nav_buttons=[
            ("← К популярным", "SECONDARY"),
            ("Сразу на русский", "POSITIVE"),
            ("Отмена", "SECONDARY"),
        ],
    )


def full_target_languages_keyboard(exclude_source: str = "") -> str:
    """Полный список целевых языков (без исходного) на обычной клавиатуре."""
    codes = [c for c in OTHER_LANGUAGES if c != exclude_source]
    return _build_full_languages_keyboard(
        codes,
        nav_buttons=[
            ("← К популярным", "SECONDARY"),
            ("← Другой исходный", "SECONDARY"),
            ("Отмена", "SECONDARY"),
        ],
    )