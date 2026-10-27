"""Хендлеры VK-бота-переводчика (vkbottle 4.x)."""
from __future__ import annotations

import logging

from vkbottle import EMPTY_KEYBOARD, GroupEventType
from vkbottle.bot import Bot, Message, MessageEvent

from app.bot import states
from app.bot.deps import reply, reply_event
from app.bot.keyboards import (
    after_translation_keyboard,
    full_source_languages_keyboard,
    full_target_languages_keyboard,
    pair_confirm_keyboard,
    source_language_keyboard,
    target_language_keyboard,
    welcome_keyboard,
)
from app.db.repository import (
    get_or_create_user,
    recent_translations,
)
from app.domain.scenario import run_translation
from app.domain.texts import (
    ask_source_language_text,
    ask_target_language_text,
    ask_text_text,
    ask_text_to_russian_text,
    confirm_pair_text,
    full_source_list_text,
    full_target_list_text,
    help_text,
    history_empty_text,
    invalid_text_text,
    rate_limit_text,
    same_language_text,
    service_down_text,
    translation_result_text,
    welcome_text,
)
from app.services.validators import label_to_code, language_label

log = logging.getLogger(__name__)


def register_handlers(bot: Bot) -> None:
    bot.on.message(text="/start")(cmd_start)
    bot.on.message(text=["/translate", "/languages"])(cmd_translate)
    bot.on.message(text="/history")(cmd_history)
    bot.on.message(text="/help")(cmd_help)
    bot.on.message(text="/cancel")(cmd_cancel)
    bot.on.message(text="Выбрать пару языков")(cmd_translate)
    bot.on.message(text="На русский")(cmd_to_russian)
    bot.on.message(text="История")(cmd_history)
    bot.on.message()(handle_text)
    bot.on.raw_event(
        GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent
    )(handle_callback)


async def _has_saved_pair(vk_id: int) -> tuple[bool, str, str]:
    user = await get_or_create_user(vk_id)
    items = await recent_translations(user.id, limit=1)
    if not items or not user.last_target_lang:
        return False, "auto", "ru"
    return True, user.last_source_lang or "auto", user.last_target_lang


async def _back_to_popular(message: Message, target_step: str) -> None:
    """Скрывает нижнюю (обычную) клавиатуру и показывает инлайн-меню популярных.

    Нужно два сообщения: одно с EMPTY_KEYBOARD, чтобы VK убрал нижнюю
    клавиатуру, второе — с инлайн-меню.
    """
    await message.answer(
        "↩️ Возвращаемся к популярным языкам…",
        keyboard=EMPTY_KEYBOARD,
    )
    if target_step == "source":
        states.set_flow(message.from_id, step="choosing_source")
        await reply(
            message,
            ask_source_language_text(),
            keyboard=source_language_keyboard(),
        )
    else:
        flow = states.get_flow(message.from_id)
        source = flow.get("source_lang", "auto")
        states.set_flow(
            message.from_id, step="choosing_target", source_lang=source
        )
        await reply(
            message,
            ask_target_language_text(source),
            keyboard=target_language_keyboard(source),
        )


async def cmd_start(message: Message) -> None:
    states.clear_flow(message.from_id)
    has_pair, source, target = await _has_saved_pair(message.from_id)

    await reply(message, "Обновляю меню…", keyboard=EMPTY_KEYBOARD)
    await reply(
        message,
        welcome_text(has_pair=has_pair, target=target if has_pair else None),
        keyboard=welcome_keyboard(),
    )
    if has_pair:
        await reply(
            message,
            confirm_pair_text(source, target),
            keyboard=pair_confirm_keyboard(target),
        )


async def cmd_translate(message: Message) -> None:
    states.clear_flow(message.from_id)
    has_pair, source, target = await _has_saved_pair(message.from_id)
    if has_pair:
        await reply(
            message,
            confirm_pair_text(source, target),
            keyboard=pair_confirm_keyboard(target),
        )
    else:
        states.set_flow(message.from_id, step="choosing_source")
        await reply(
            message,
            ask_source_language_text(),
            keyboard=source_language_keyboard(),
        )


async def cmd_to_russian(message: Message) -> None:
    states.set_flow(
        message.from_id,
        step="waiting_text_to_ru",
        source_lang="auto",
        target_lang="ru",
    )
    await reply(
        message, ask_text_to_russian_text(), keyboard=welcome_keyboard()
    )


async def cmd_history(message: Message) -> None:
    user = await get_or_create_user(message.from_id)
    items = await recent_translations(user.id, limit=5)
    if not items:
        await reply(
            message, history_empty_text(), keyboard=welcome_keyboard()
        )
        return

    lines = ["Последние переводы:"]
    for item in items:
        src = (
            "авто"
            if item.source_lang == "auto"
            else language_label(item.source_lang)
        )
        tgt = language_label(item.target_lang)
        preview_src = item.source_text[:40].replace("\n", " ")
        preview_tgt = item.translated_text[:40].replace("\n", " ")
        lines.append(
            f"- {src} -> {tgt}: «{preview_src}» => «{preview_tgt}»"
        )
    await reply(message, "\n".join(lines), keyboard=welcome_keyboard())


async def cmd_help(message: Message) -> None:
    await reply(message, help_text(), keyboard=welcome_keyboard())


async def cmd_cancel(message: Message) -> None:
    states.clear_flow(message.from_id)
    await reply(
        message,
        "Диалог сброшен. Отправьте /start, чтобы начать заново.",
        keyboard=welcome_keyboard(),
    )


async def handle_text(message: Message) -> None:
    if not message.text:
        return

    text = message.text.strip()
    flow = states.get_flow(message.from_id)
    step = flow.get("step")

    # --- навигация нижней клавиатуры ---
    if text == "← К популярным":
        target = "target" if step == "choosing_target" else "source"
        await _back_to_popular(message, target)
        return

    if text == "Сразу на русский":
        await cmd_to_russian(message)
        return

    if text == "← Другой исходный":
        await _back_to_popular(message, "source")
        return

    if text == "Отмена":
        await cmd_cancel(message)
        return

    # --- выбор языка из обычной клавиатуры ---
    if step in ("choosing_source", "choosing_target"):
        code = label_to_code(text)
        if code:
            if step == "choosing_source":
                states.set_flow(
                    message.from_id,
                    step="choosing_target",
                    source_lang=code,
                )
                await reply(
                    message,
                    ask_target_language_text(code),
                    keyboard=target_language_keyboard(code),
                )
                return
            # step == "choosing_target"
            source = flow.get("source_lang", "auto")
            if code == source:
                await reply(
                    message, same_language_text(), keyboard=welcome_keyboard()
                )
                return
            states.set_flow(
                message.from_id,
                step="waiting_text",
                source_lang=source,
                target_lang=code,
            )
            await reply(
                message,
                ask_text_text(code, source),
                keyboard=welcome_keyboard(),
            )
            return

    if step == "choosing_target":
        source = flow.get("source_lang", "auto")
        await reply(
            message,
            ask_target_language_text(source),
            keyboard=target_language_keyboard(source),
        )
        return

    if step not in ("waiting_text", "waiting_text_to_ru"):
        states.set_flow(message.from_id, step="choosing_source")
        await reply(
            message,
            ask_source_language_text(),
            keyboard=source_language_keyboard(),
        )
        return

    source = flow.get("source_lang", "auto")
    target = flow.get("target_lang", "ru")

    user = await get_or_create_user(message.from_id)
    outcome = await run_translation(
        user_id=user.id,
        vk_id=message.from_id,
        raw_text=message.text,
        source_lang=source,
        target_lang=target,
    )

    if outcome.error:
        code, _, detail = outcome.error.partition(":")
        if code == "rate_limit":
            await reply(message, rate_limit_text())
        elif code == "service_down":
            await reply(message, service_down_text())
        elif code == "same_lang":
            await reply(
                message,
                same_language_text(),
                keyboard=source_language_keyboard(),
            )
        else:
            await reply(message, invalid_text_text(detail or "Проверьте ввод."))
        return

    assert outcome.result is not None
    await reply(
        message,
        translation_result_text(outcome.result),
        keyboard=after_translation_keyboard(),
    )
    states.set_flow(
        message.from_id,
        step="waiting_text",
        source_lang=source,
        target_lang=target,
    )


async def handle_callback(event: MessageEvent) -> None:
    payload = event.payload or {}
    cmd = payload.get("cmd")
    user_id = event.user_id

    if cmd == "keep_pair":
        user = await get_or_create_user(user_id)
        target = user.last_target_lang or "ru"
        source = user.last_source_lang or "auto"
        states.set_flow(
            user_id,
            step="waiting_text",
            source_lang=source,
            target_lang=target,
        )
        await reply_event(
            event, ask_text_text(target, source), keyboard=welcome_keyboard()
        )
        await event.show_snackbar("Продолжаем с прошлой парой")
        return

    if cmd == "change_pair":
        states.set_flow(user_id, step="choosing_source")
        await reply_event(
            event,
            ask_source_language_text(),
            keyboard=source_language_keyboard(),
        )
        await event.show_snackbar("Выбираем пару")
        return

    if cmd == "source_auto":
        states.set_flow(user_id, step="choosing_target", source_lang="auto")
        await reply_event(
            event,
            ask_target_language_text("auto"),
            keyboard=target_language_keyboard("auto"),
        )
        await event.show_snackbar("Автоопределение")
        return

    if cmd == "source_lang":
        lang = payload.get("lang", "ru")
        states.set_flow(user_id, step="choosing_target", source_lang=lang)
        await reply_event(
            event,
            ask_target_language_text(lang),
            keyboard=target_language_keyboard(lang),
        )
        await event.show_snackbar(f"Исходный: {language_label(lang)}")
        return

    if cmd == "source_more":
        states.set_flow(user_id, step="choosing_source")
        await reply_event(
            event,
            full_source_list_text(),
            keyboard=full_source_languages_keyboard(),
        )
        await event.show_snackbar("Полный список языков")
        return

    if cmd == "target_lang":
        lang = payload.get("lang", "en")
        flow = states.get_flow(user_id)
        source = flow.get("source_lang", "auto")
        states.set_flow(
            user_id,
            step="waiting_text",
            source_lang=source,
            target_lang=lang,
        )
        await reply_event(
            event, ask_text_text(lang, source), keyboard=welcome_keyboard()
        )
        await event.show_snackbar(f"Цель: {language_label(lang)}")
        return

    if cmd == "target_more":
        flow = states.get_flow(user_id)
        source = flow.get("source_lang", "auto")
        states.set_flow(user_id, step="choosing_target", source_lang=source)
        await reply_event(
            event,
            full_target_list_text(source),
            keyboard=full_target_languages_keyboard(source),
        )
        await event.show_snackbar("Полный список языков")
        return

    if cmd == "target_back":
        states.set_flow(user_id, step="choosing_source")
        await reply_event(
            event,
            ask_source_language_text(),
            keyboard=source_language_keyboard(),
        )
        await event.show_snackbar("Назад")
        return

    if cmd == "to_russian":
        states.set_flow(
            user_id,
            step="waiting_text_to_ru",
            source_lang="auto",
            target_lang="ru",
        )
        await reply_event(
            event, ask_text_to_russian_text(), keyboard=welcome_keyboard()
        )
        await event.show_snackbar("Режим «на русский»")
        return

    if cmd == "again":
        flow = states.get_flow(user_id)
        target = flow.get("target_lang", "ru")
        source = flow.get("source_lang", "auto")
        states.set_flow(
            user_id,
            step="waiting_text",
            source_lang=source,
            target_lang=target,
        )
        await reply_event(
            event, ask_text_text(target, source), keyboard=welcome_keyboard()
        )
        await event.show_snackbar("Готов к новому переводу")
        return

    if cmd == "show_history":
        user = await get_or_create_user(user_id)
        items = await recent_translations(user.id, limit=5)
        if not items:
            await reply_event(
                event, history_empty_text(), keyboard=welcome_keyboard()
            )
        else:
            lines = ["Последние переводы:"]
            for item in items:
                src = (
                    "авто"
                    if item.source_lang == "auto"
                    else language_label(item.source_lang)
                )
                tgt = language_label(item.target_lang)
                lines.append(
                    f"- {src} -> {tgt}: «{item.translated_text[:60]}»"
                )
            await reply_event(
                event, "\n".join(lines), keyboard=welcome_keyboard()
            )
        await event.show_snackbar("История")
        return

    await reply_event(event, "Неизвестная команда. Отправьте /start.")