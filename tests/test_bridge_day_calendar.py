"""Check optional bridge days using the same calendar API as the HA calendar view."""

from zoneinfo import ZoneInfo

from freezegun import freeze_time
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar.const import BRIDGE_DAY, DOMAIN, SENSOR_TYPES
from homeassistant.util import dt as dt_util

CALENDAR = "calendar.swedish_calendar"


@pytest.fixture
def stockholm_time():
    """Use the same local calendar day for both UTC and local queries."""
    previous = dt_util.DEFAULT_TIME_ZONE
    dt_util.set_default_time_zone(ZoneInfo("Europe/Stockholm"))
    try:
        yield
    finally:
        dt_util.set_default_time_zone(previous)


async def setup_calendar(hass, include, *, before=0, after=0):
    """Use actual local calendar data and exclude every standalone sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "exclude": [*SENSOR_TYPES, BRIDGE_DAY],
            "local_mode": True,
            "calendar_config": {
                "include": include,
                "days_before_today": before,
                "days_after_today": after,
            },
            "cache": {"enabled": False, "dir": "", "retention": 7},
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def get_events(client, start, end):
    """Read all-day events via Home Assistant's public calendar HTTP endpoint."""
    response = await client.get(
        f"/api/calendars/{CALENDAR}", params={"start": start, "end": end}
    )
    assert response.status == 200
    return [
        (event["summary"], event["start"]["date"], event["end"]["date"])
        for event in await response.json()
    ]


@pytest.mark.parametrize("language,label", [("en", "Bridge day"), ("sv", "Klämdag")])
async def test_bridge_only_calendar(
    hass, hass_client, stockholm_time, monkeypatch, language, label
):
    """The sensor can be excluded while the calendar shows past and future bridge days."""
    monkeypatch.setattr(hass.config, "language", language, raising=False)
    with freeze_time("2026-01-03 12:00:00"):
        await setup_calendar(hass, [BRIDGE_DAY], before=1, after=2)
        assert hass.states.get("binary_sensor.swedish_calendar_bridge_day") is None
        assert hass.states.get(CALENDAR).attributes["message"] == label
    client = await hass_client()
    assert await get_events(client, "2025-12-01T00:00:00Z", "2026-05-31T00:00:00Z") == [
        (label, "2026-01-02", "2026-01-03"),
        (label, "2026-01-05", "2026-01-06"),
    ]
    # Jan 5 starts at 23:00 UTC on Jan 4 in Stockholm.
    assert (
        await get_events(client, "2026-01-03T00:00:00Z", "2026-01-04T23:00:00Z") == []
    )
    assert await get_events(client, "2026-01-04T23:00:00Z", "2026-01-04T23:10:00Z") == [
        (label, "2026-01-05", "2026-01-06"),
    ]


@pytest.mark.parametrize("include", [["holiday"], ["holiday", BRIDGE_DAY]])
async def test_bridge_days_alongside_existing_holidays(
    hass, hass_client, stockholm_time, include
):
    """Selecting bridge days adds to the same calendar and preserves holiday events."""
    with freeze_time("2024-12-23 12:00:00"):
        await setup_calendar(hass, include, after=1)
    client = await hass_client()
    events = await get_events(client, "2024-12-22T23:00:00Z", "2024-12-24T23:00:00Z")
    expected = [("Julafton", "2024-12-24", "2024-12-25")]
    if BRIDGE_DAY in include:
        expected.insert(0, ("Bridge day", "2024-12-23", "2024-12-24"))
    assert events == expected


async def test_calendar_state_refreshes_across_bridge_day(hass, stockholm_time):
    """With a today-only window, publish the event when the calendar day changes."""
    with freeze_time("2024-12-22 12:00:00") as clock:
        entry = await setup_calendar(hass, [BRIDGE_DAY])
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        assert hass.states.get(CALENDAR).state == "off"

        clock.move_to("2024-12-23 12:00:00")
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        state = hass.states.get(CALENDAR)
        assert state.state == "on"
        assert state.attributes["message"] == "Bridge day"
        assert state.attributes["all_day"] is True

        clock.move_to("2024-12-24 12:00:00")
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(CALENDAR).state == "off"


async def test_query_during_repeated_hour(hass, hass_client, stockholm_time):
    """A query from the first 02:55 to the second 02:05 still overlaps the day."""
    with freeze_time("2026-10-25 12:00:00"):
        await setup_calendar(hass, ["date", BRIDGE_DAY])
    client = await hass_client()
    assert await get_events(client, "2026-10-25T00:55:00Z", "2026-10-25T01:05:00Z") == [
        ("2026-10-25", "2026-10-25", "2026-10-26")
    ]
