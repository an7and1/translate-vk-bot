"""Репозиторий пользователей и истории переводов."""
from sqlalchemy import select

from app.db.models import Translation, User
from app.db.session import session_factory


async def get_or_create_user(vk_id: int) -> User:
    async with session_factory()() as session:
        stmt = select(User).where(User.vk_id == vk_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if user is None:
            user = User(vk_id=vk_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def update_pair(vk_id: int, source: str, target: str) -> None:
    async with session_factory()() as session:
        stmt = select(User).where(User.vk_id == vk_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if user is None:
            user = User(vk_id=vk_id)
            session.add(user)
        user.last_source_lang = source
        user.last_target_lang = target
        await session.commit()


async def save_translation(
    user_id: int,
    source_text: str,
    translated_text: str,
    source_lang: str,
    target_lang: str,
    provider: str,
) -> None:
    async with session_factory()() as session:
        session.add(
            Translation(
                user_id=user_id,
                source_text=source_text,
                translated_text=translated_text,
                source_lang=source_lang,
                target_lang=target_lang,
                provider=provider,
            )
        )
        await session.commit()


async def recent_translations(user_id: int, limit: int = 5) -> list[Translation]:
    async with session_factory()() as session:
        stmt = (
            select(Translation)
            .where(Translation.user_id == user_id)
            .order_by(Translation.created_at.desc())
            .limit(limit)
        )
        return list((await session.execute(stmt)).scalars().all())
