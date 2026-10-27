"""Все тексты бота — единый источник формулировок."""
from app.services.translator import TranslationResult
from app.services.validators import language_label


def welcome_text(has_pair: bool, target: str | None = None) -> str:
    lines = [
        "Привет! Я Translate VK Bot — переводчик в одно сообщение.",
        "",
        "- Перевожу между 16+ языками.",
        "- Сначала выбираете исходный язык (или «Автоопределение»), затем — целевой.",
        "- Кнопка «Сразу на русский» переведёт с любого языка в один клик.",
        "- Запоминаю вашу пару языков и предлагаю продолжить с неё.",
        "- Веду историю последних переводов.",
        "",
    ]
    if has_pair and target:
        lines.append(f"В прошлый раз переводили на {language_label(target)}.")
        lines.append("Продолжим или выберем новую пару?")
    else:
        lines.append("Начните с выбора пары языков.")
    return "\n".join(lines)


def ask_source_language_text() -> str:
    return (
        "🌐 С какого языка переводим?\n"
        "Выберите «🔍 Автоопределение», если язык неизвестен, "
        "или конкретный исходный язык. Кнопка «Ещё →» откроет полный список "
        "языков в нижней клавиатуре."
    )


def ask_target_language_text(source: str = "auto") -> str:
    src = "🔍 авто" if source == "auto" else language_label(source)
    return (
        f"🎯 На какой язык переводим? (исходный: {src})\n"
        "Кнопка «Ещё →» откроет полный список языков в нижней клавиатуре."
    )


def full_source_list_text() -> str:
    return (
        "📚 Полный список исходных языков — внизу экрана.\n"
        "Выберите язык или нажмите «← К популярным» / «Отмена»."
    )


def full_target_list_text(source: str) -> str:
    src = "🔍 авто" if source == "auto" else language_label(source)
    return (
        f"📚 Полный список целевых языков (исходный: {src}) — внизу экрана.\n"
        "Выберите язык или «← К популярным» / «← Другой исходный» / «Отмена»."
    )


def confirm_pair_text(source: str, target: str) -> str:
    src = "авто" if source == "auto" else language_label(source)
    tgt = language_label(target)
    return f"Используем пару {src} -> {tgt}?"


def ask_text_text(target: str, source: str = "auto") -> str:
    src = "🔍 авто" if source == "auto" else language_label(source)
    return (
        f"✏️ Отправьте текст для перевода: {src} → {language_label(target)}.\n"
        f"Максимум 500 символов."
    )


def ask_text_to_russian_text() -> str:
    return (
        "✏️ Отправьте текст — определю язык и переведу на Русский.\n"
        "Работает с любого языка!"
    )


def invalid_text_text(reason: str) -> str:
    return f"{reason} Попробуйте ещё раз."


def translation_result_text(result: TranslationResult) -> str:
    tgt = language_label(result.target_lang)
    provider = {
        "mymemory": "MyMemory",
        "libretranslate": "LibreTranslate",
    }.get(result.provider, result.provider)
    return (
        f"Перевод на {tgt}:\n\n"
        f"{result.text}\n\n"
        f"(провайдер: {provider})"
    )


def rate_limit_text() -> str:
    return (
        "Сервисы перевода временно ограничили частоту.\n"
        "Подождите минуту и попробуйте снова."
    )


def service_down_text() -> str:
    return "Сервисы перевода недоступны. Попробуйте позже."


def history_empty_text() -> str:
    return "История пока пуста — сделайте первый перевод."


def same_language_text() -> str:
    return "Исходный и целевой языки совпадают. Выберите другую пару."


def help_text() -> str:
    return (
        "Команды:\n"
        "/start — начать заново\n"
        "/translate — выбрать пару языков\n"
        "/languages — список языков\n"
        "/history — последние переводы\n"
        "/cancel — сбросить диалог\n\n"
        "Подсказка: кнопка «На русский» переведёт текст с любого языка."
    )