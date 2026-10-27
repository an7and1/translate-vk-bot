"""Хелперы для отправки сообщений и callback-ответов."""
from vkbottle.bot import Message, MessageEvent

_RANDOM_ID = 0


async def reply(message: Message, text: str, keyboard: str | None = None) -> None:
    await message.answer(text, keyboard=keyboard)


async def reply_event(
    event: MessageEvent, text: str, keyboard: str | None = None
) -> None:
    await event.ctx_api.messages.send(
        peer_id=event.peer_id,
        message=text,
        random_id=_RANDOM_ID,
        keyboard=keyboard,
    )
