"""Валидация ввода и языковых кодов."""
MIN_TEXT_LEN = 1
MAX_TEXT_LEN = 500  # ограничение MyMemory

# Код языка -> подпись кнопки (с флагом). Добавить новый язык — одна строка.
SUPPORTED_LANGUAGES: dict[str, str] = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "de": "🇩🇪 Deutsch",
    "fr": "🇫🇷 Français",
    "es": "🇪🇸 Español",
    "zh": "🇨🇳 中文",
    "it": "🇮🇹 Italiano",
    "pt": "🇵🇹 Português",
    "ja": "🇯🇵 日本語",
    "ko": "🇰🇷 한국어",
    "tr": "🇹🇷 Türkçe",
    "uk": "🇺🇦 Українська",
    "pl": "🇵🇱 Polski",
    "nl": "🇳🇱 Nederlands",
    "ar": "🇸🇦 العربية",
    "sv": "🇸🇪 Svenska",
    "fi": "🇫🇮 Suomi",
    "cs": "🇨🇿 Čeština",
    "ro": "🇷🇴 Română",
    "hi": "🇮🇳 हिन्दी",
}

POPULAR_LANGUAGES: list[str] = ["ru", "en", "de", "fr", "es", "zh"]
OTHER_LANGUAGES: list[str] = [
    code for code in SUPPORTED_LANGUAGES if code not in POPULAR_LANGUAGES
]

LABEL_TO_CODE: dict[str, str] = {label: code for code, label in SUPPORTED_LANGUAGES.items()}


def normalize_text(raw: str) -> str:
    """Убирает лишние пробелы по краям и проверяет длину."""
    text = raw.strip()
    if not text:
        raise ValueError("Текст не может быть пустым.")
    if len(text) < MIN_TEXT_LEN:
        raise ValueError("Слишком короткий текст.")
    if len(text) > MAX_TEXT_LEN:
        raise ValueError(
            f"Текст длиннее {MAX_TEXT_LEN} символов — сервис перевода не примет."
        )
    return text


def is_valid_language(code: str) -> bool:
    return code in SUPPORTED_LANGUAGES


def language_label(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code, code)


def label_to_code(label: str) -> str | None:
    """Обратное преобразование: подпись кнопки → код языка."""
    return LABEL_TO_CODE.get(label.strip())


def validate_pair(source: str, target: str) -> None:
    """Запрещает перевод в тот же язык."""
    if source == target and source != "auto":
        raise ValueError("Исходный и целевой языки совпадают.")