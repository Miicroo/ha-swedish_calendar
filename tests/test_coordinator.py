"""sTest coordinator."""
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from freezegun import freeze_time

from custom_components.swedish_calendar.coordinator import CalendarDataCoordinator
from custom_components.swedish_calendar.types import (
    ApiData,
    CacheConfig,
    CalendarConfig,
    SpecialThemesConfig,
    ThemeData,
)


def make_api_data(day: date, names: list[str]) -> ApiData:
    """Create API data for a given day."""
    return ApiData(
        date=day.isoformat(),
        weekday="Torsdag",
        work_free_day=False,
        red_day=False,
        week=42,
        day_of_week_index=4,
        name_day=names,
        reason_for_flagging=None,
        eve=None,
        holiday=None,
        day_before_work_free_holiday=False,
    )


async def test_update_data_refetches_when_cache_has_themes_only(hass):
    """Regression test for midnight refresh in local mode."""

    config = CalendarConfig(
        includes=[],
        days_before_today=0,
        days_after_today=0,
    )

    cache_config = CacheConfig(
        enabled=False,
        cache_dir="",
        retention=timedelta(days=7),
    )

    special_themes_config = SpecialThemesConfig(
        path="",
        auto_update=False,
    )

    api_provider = MagicMock()
    theme_provider = MagicMock()
    theme_updater = MagicMock()

    theme_updater.can_update.return_value = False

    with (
        patch(
            "custom_components.swedish_calendar.coordinator.LocalApiDataProvider",
            return_value=api_provider,
        ),
        patch(
            "custom_components.swedish_calendar.coordinator.LocalThemeDataProvider",
            return_value=theme_provider,
        ),
        patch(
            "custom_components.swedish_calendar.coordinator.LocalThemeDataUpdater",
            return_value=theme_updater,
        ),
        patch(
            "custom_components.swedish_calendar.coordinator.DateUtils.seconds_until_midnight",
            return_value=86400,
        ),
    ):
        coordinator = CalendarDataCoordinator(
            hass=hass,
            special_themes_config=special_themes_config,
            calendar_config=config,
            cache_config=cache_config,
            is_local_mode=True,
            conf={"exclude": []},
        )

    day1 = date(2026, 10, 15)
    day2 = day1 + timedelta(days=1)

    api_day1 = make_api_data(day1, ["Hedvig", "Hillevi"])
    api_day2 = make_api_data(day2, ["Signe", "Agneta"])

    # Theme data exists for both days, as in local mode.
    themes = [
        ThemeData(day1.isoformat(), ["Theme day 1"]),
        ThemeData(day2.isoformat(), ["Theme day 2"]),
    ]

    coordinator._api_data_provider.fetch_data = AsyncMock(
        side_effect=[
            [api_day1],
            [api_day2],
        ]
    )

    coordinator._theme_provider.fetch_data = AsyncMock(return_value=themes)

    # First day: initial API data is fetched.
    with freeze_time("2026-10-15"):
        result = await coordinator.update_data()

        assert result[day1].get_value_by_attribute("name_day") == [
            "Hedvig",
            "Hillevi",
        ]

    # Second day: date is already cached because of themes.
    with freeze_time("2026-10-16"):
        result = await coordinator.update_data()

        assert result[day2].get_value_by_attribute("name_day") == [
            "Signe",
            "Agneta",
        ]

    assert coordinator._api_data_provider.fetch_data.call_count == 2
