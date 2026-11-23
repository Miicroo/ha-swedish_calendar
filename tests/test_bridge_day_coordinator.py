"""Test bridge day data through the local and online coordinator paths."""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

from freezegun import freeze_time
import pytest

from custom_components.swedish_calendar.api_data import ApiDataProvider
from custom_components.swedish_calendar.const import BRIDGE_DAY, THEME_DAY
from custom_components.swedish_calendar.coordinator import CalendarDataCoordinator
from custom_components.swedish_calendar.types import (
    CacheConfig,
    CalendarConfig,
    SpecialThemesConfig,
    ThemeData,
)
from custom_components.swedish_calendar.utils import DateUtils


def coordinator_for(hass, *, local=True, exclude=(), before=0, after=0):
    """Use the same coordinator and providers as config-entry setup."""
    return CalendarDataCoordinator(
        hass,
        SpecialThemesConfig(path="", auto_update=False),
        CalendarConfig(includes=[], days_before_today=before, days_after_today=after),
        CacheConfig(enabled=False, cache_dir="", retention=timedelta()),
        local,
        {"exclude": list(exclude)},
    )


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        ("2024-12-23", True),  # Sunday to Christmas Eve (work-free, not red)
        ("2026-01-05", True),  # Sunday to Epiphany
        ("2026-05-14", False),  # Ascension Day itself
        ("2026-05-15", True),  # Ascension Day to Saturday
        ("2026-05-16", False),  # Saturday
        ("2027-01-05", False),  # One working neighbour
        ("2029-04-30", True),  # May Day in the next month
    ],
)
async def test_local_bridge_day(hass, today, expected):
    """Derive real bridge days without extending the public calendar interval."""
    with freeze_time(today + " 12:00:00"):
        coordinator = coordinator_for(hass, exclude=[THEME_DAY])
        days = await coordinator.update_data()
        assert coordinator.bridge_day is expected
        assert set(days) == {date.fromisoformat(today)}


def api_day(day, work_free):
    """Build one calendar row in the online API format."""
    return {
        "datum": day,
        "veckodag": "Måndag",
        "arbetsfri dag": work_free,
        "röd dag": "Nej",
        "vecka": "17",
        "dag i vecka": "1",
        "namnsdag": [],
    }


async def test_online_bridge_day_midnight_and_missing_neighbor(hass):
    """Retry incomplete data, preserving themes without turning them into work days."""
    with freeze_time("2029-04-30 12:00:00") as clock:
        coordinator = coordinator_for(hass, local=False)
        coordinator._theme_provider.fetch_data = AsyncMock(
            return_value=[ThemeData("2029-05-01", ["Theme"])]
        )
        april = {"dagar": [api_day("2029-04-29", "Ja"), api_day("2029-04-30", "Nej")]}
        may_day = {"dagar": [api_day("2029-05-01", "Ja")]}
        get_json = AsyncMock(
            side_effect=[
                april,
                {"dagar": []},
                april,
                {"dagar": [api_day("2029-05-01", None)]},
                april,
                may_day,
                april,
                may_day,
            ]
        )
        coordinator._api_data_provider._get_json_from_url = get_json
        days = await coordinator.update_data()
        assert coordinator.bridge_day is None
        assert date(2029, 4, 29) not in days
        theme_only = days[date(2029, 5, 1)]
        assert theme_only.get_value_by_attribute("themes") == ["Theme"]
        assert theme_only.get_value_by_attribute("date") is None
        await coordinator.update_data()
        assert coordinator.bridge_day is None
        await coordinator.update_data()
        assert coordinator.bridge_day is True
        assert get_json.await_count == 6
        # The same complete dates need no further fetch.
        await coordinator.update_data()
        assert get_json.await_count == 6
        clock.move_to("2029-05-01 12:00:00")
        days = await coordinator.update_data()
        assert coordinator.bridge_day is False
        assert days[date(2029, 5, 1)].get_value_by_attribute("date") == "2029-05-01"
        assert get_json.await_count == 8


async def test_excluded_sensor_keeps_existing_provider_window(hass):
    """Disabling Bridge day keeps a same-day configuration at its original size."""
    with freeze_time("2026-05-15 12:00:00"):
        coordinator = coordinator_for(hass, exclude=[THEME_DAY, BRIDGE_DAY])
        fetch = AsyncMock(return_value=[])
        coordinator._api_data_provider.fetch_data = fetch
        await coordinator.update_data()
        fetch.assert_awaited_once_with(date(2026, 5, 15), date(2026, 5, 15))
        assert coordinator.bridge_day is None


def test_bridge_day_fetch_at_new_year_is_bounded():
    """Fetching Dec 30 through Jan 1 uses December and one day in January."""
    assert ApiDataProvider._get_url_patterns_for_date_range(
        date(2026, 12, 30), date(2027, 1, 1)
    ) == ["2026/12", "2027/1/1"]


@pytest.mark.parametrize(("month", "day", "hours"), [(3, 29, 23), (10, 25, 25)])
def test_schedule_next_local_midnight_across_dst(month, day, hours):
    """Schedule the next actual Stockholm midnight on DST transition days."""
    start = datetime(2026, month, day, tzinfo=ZoneInfo("Europe/Stockholm"))
    assert DateUtils.seconds_until_midnight(start) == hours * 3600 + 1
