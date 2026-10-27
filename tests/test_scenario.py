from unittest.mock import AsyncMock, patch

import pytest

from app.domain import scenario
from app.services.translator import (
    RateLimitError,
    TranslationError,
    TranslationResult,
)


@pytest.mark.asyncio
async def test_scenario_invalid_text() -> None:
    outcome = await scenario.run_translation(
        user_id=1, vk_id=1, raw_text="", source_lang="auto", target_lang="ru"
    )
    assert outcome.result is None
    assert outcome.error and outcome.error.startswith("invalid")


@pytest.mark.asyncio
async def test_scenario_same_language() -> None:
    outcome = await scenario.run_translation(
        user_id=1, vk_id=1, raw_text="hello", source_lang="ru", target_lang="ru"
    )
    assert outcome.result is None
    assert outcome.error and outcome.error.startswith("same_lang")


@pytest.mark.asyncio
async def test_scenario_success_saves() -> None:
    fake = TranslationResult(
        text="привет",
        source_lang="auto",
        target_lang="ru",
        provider="mymemory",
    )
    with patch.object(
        scenario, "translate_text", AsyncMock(return_value=fake)
    ), patch.object(
        scenario, "save_translation", AsyncMock()
    ) as save_mock, patch.object(
        scenario, "update_pair", AsyncMock()
    ) as upd_mock:
        outcome = await scenario.run_translation(
            user_id=1,
            vk_id=42,
            raw_text="hello",
            source_lang="auto",
            target_lang="ru",
        )

    assert outcome.error is None
    assert outcome.result == fake
    save_mock.assert_awaited_once()
    upd_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_scenario_rate_limit() -> None:
    with patch.object(
        scenario, "translate_text", AsyncMock(side_effect=RateLimitError("429"))
    ):
        outcome = await scenario.run_translation(
            user_id=1,
            vk_id=1,
            raw_text="hello",
            source_lang="auto",
            target_lang="ru",
        )
    assert outcome.error == "rate_limit"


@pytest.mark.asyncio
async def test_scenario_service_down() -> None:
    with patch.object(
        scenario, "translate_text", AsyncMock(side_effect=TranslationError("down"))
    ):
        outcome = await scenario.run_translation(
            user_id=1,
            vk_id=1,
            raw_text="hello",
            source_lang="auto",
            target_lang="ru",
        )
    assert outcome.error == "service_down"
