"""Test sensor metadata and compatibility through config entry setup."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

from freezegun import freeze_time
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar.calendar import SwedishCalendarEvent
from custom_components.swedish_calendar.const import DOMAIN
from custom_components.swedish_calendar.types import ApiData, SwedishCalendar, ThemeData
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

TODAY = date(2026, 12, 24)
WEEKDAYS = [
    "Måndag",
    "Tisdag",
    "Onsdag",
    "Torsdag",
    "Fredag",
    "Lördag",
    "Söndag",
]
BOOLEAN_SENSORS = ["workfree_day", "red_day", "day_before_workfree_holiday"]
EXPECTED_SENSORS = {
    "date": ("sensor.date", "2026-12-24"),
    "weekday": ("sensor.week_day", "Torsdag"),
    "workfree_day": ("sensor.workfree_day", "Ja"),
    "red_day": ("sensor.red_day", "Nej"),
    "week": ("sensor.week", "52"),
    "day_of_week": ("sensor.day_of_week", "4"),
    "eve": ("sensor.eve", "Julafton"),
    "holiday": ("sensor.holiday", "unknown"),
    "day_before_workfree_holiday": ("sensor.day_before_workfree_holiday", "Nej"),
    "name_day": ("sensor.names_celebrated", "Eva"),
    "flag_day": ("sensor.reason_for_flagging", "unknown"),
    "theme_day": ("sensor.swedish_calendar_theme_day", "Julafton"),
}


@pytest.fixture(autouse=True)
def frozen_date():
    """Keep entity lookups and coordinator scheduling on a known date."""
    with freeze_time("2026-12-24 12:00:00") as freezer:
        yield freezer


@pytest.fixture
def api_payload():
    """Return calendar data in the API's actual JSON format."""
    return {
        "datum": "2026-12-24",
        "veckodag": "Torsdag",
        "arbetsfri dag": "Ja",
        "röd dag": "Nej",
        "vecka": "52",
        "dag i vecka": "4",
        "namnsdag": ["Eva"],
        "flaggdag": "",
        "helgdagsafton": "Julafton",
        "dag före arbetsfri helgdag": "Nej",
    }


@pytest.fixture
def calendar_data(api_payload):
    """Supply real parsed models without making external requests."""
    return {
        TODAY: SwedishCalendar.from_api_data(
            ApiData.from_json(api_payload)
        ).with_themes(ThemeData(TODAY.isoformat(), ["Julafton"]))
    }


@pytest.fixture
def fetch_calendar(calendar_data):
    """Mock fetching while retaining real entry, platform and entity setup."""
    with patch(
        "custom_components.swedish_calendar.coordinator.CalendarDataCoordinator.update_data",
        new_callable=AsyncMock,
        return_value=calendar_data,
    ) as fetch:
        yield fetch


async def setup_entry(hass, local_mode=True):
    """Set up every sensor using a complete config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Swedish calendar",
        data={
            "exclude": [],
            "local_mode": local_mode,
            "special_themes": {"dir": "", "auto_update": False},
            "calendar_config": {
                "include": [],
                "days_before_today": 0,
                "days_after_today": 0,
            },
            "cache": {"enabled": False, "dir": "", "retention": 7},
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def sensor_entity(hass, entity_id):
    """Get the registered sensor to verify its native value contract."""
    return hass.data["entity_components"]["sensor"].get_entity(entity_id)


async def test_entities_share_the_local_calendar_date(
    hass, fetch_calendar, frozen_date
):
    """At Stockholm midnight, display the same date that the coordinator used."""
    previous_zone = dt_util.DEFAULT_TIME_ZONE
    dt_util.set_default_time_zone(ZoneInfo("Europe/Stockholm"))
    try:
        frozen_date.move_to("2026-12-23 23:01:00+00:00")
        await setup_entry(hass)
        assert (
            hass.states.get("sensor.swedish_calendar_date").state == TODAY.isoformat()
        )
        assert SwedishCalendarEvent(TODAY - timedelta(days=1), "Yesterday").has_passed()
        assert not SwedishCalendarEvent(TODAY, "Today").has_passed()
    finally:
        dt_util.set_default_time_zone(previous_zone)


def assert_enum_metadata(state, options):
    """Check enum support, preserving compatibility with older Home Assistant."""
    if hasattr(SensorDeviceClass, "ENUM"):
        assert state.attributes["device_class"] == SensorDeviceClass.ENUM
        assert set(state.attributes["options"]) == set(options)
    else:
        assert "device_class" not in state.attributes
        assert "options" not in state.attributes


@pytest.mark.parametrize("local_mode", [False, True])
async def test_all_sensor_states_identities_and_metadata(
    hass, fetch_calendar, local_mode
):
    """Preserve all twelve existing sensors while publishing useful metadata."""
    entry = await setup_entry(hass, local_mode=local_mode)
    registry = er.async_get(hass)
    registered = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert {item.entity_id for item in registered if item.domain == "sensor"} == {
        f"sensor.swedish_calendar_{key}" for key in EXPECTED_SENSORS
    }

    for key, (unique_id, expected_state) in EXPECTED_SENSORS.items():
        entity_id = f"sensor.swedish_calendar_{key}"
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == expected_state
        assert registry.async_get(entity_id).unique_id == unique_id
        assert "unit_of_measurement" not in state.attributes
        assert "state_class" not in state.attributes

        entity = sensor_entity(hass, entity_id)
        assert isinstance(entity, SensorEntity)
        if key == "weekday" or key in BOOLEAN_SENSORS:
            options = WEEKDAYS if key == "weekday" else ["Ja", "Nej"]
            assert_enum_metadata(state, options)
            assert state.state in options
        elif key == "date":
            assert state.attributes["device_class"] == SensorDeviceClass.DATE
            assert type(entity.native_value) is date
            assert entity.native_value == TODAY
            assert "options" not in state.attributes
        else:
            assert "device_class" not in state.attributes
            assert "options" not in state.attributes
            if key in ("week", "day_of_week"):
                assert type(entity.native_value) is int
                assert entity.native_value == int(expected_state)


@pytest.mark.parametrize("weekday", WEEKDAYS)
async def test_every_weekday_is_a_valid_enum_state(
    hass, api_payload, calendar_data, fetch_calendar, weekday
):
    """All seven existing Swedish weekday values remain valid."""
    api_payload["veckodag"] = weekday
    calendar_data[TODAY].with_api_data(ApiData.from_json(api_payload))
    await setup_entry(hass)
    state = hass.states.get("sensor.swedish_calendar_weekday")
    assert state.state == weekday
    assert_enum_metadata(state, WEEKDAYS)


@pytest.mark.parametrize("value", ["Ja", "Nej"])
async def test_boolean_sensor_values_remain_swedish(
    hass, api_payload, calendar_data, fetch_calendar, value
):
    """Both outcomes retain their state strings for all three boolean sensors."""
    for field in ("arbetsfri dag", "röd dag", "dag före arbetsfri helgdag"):
        api_payload[field] = value
    calendar_data[TODAY].with_api_data(ApiData.from_json(api_payload))
    await setup_entry(hass)
    for key in BOOLEAN_SENSORS:
        state = hass.states.get(f"sensor.swedish_calendar_{key}")
        assert state.state == value
        assert_enum_metadata(state, ["Ja", "Nej"])


@pytest.mark.parametrize(
    "payload_kind", ["empty_optional", "blank_optional", "themes_only", "no_data"]
)
async def test_blank_and_missing_data_preserve_existing_fallbacks(
    hass, api_payload, calendar_data, fetch_calendar, payload_kind
):
    """Metadata must not turn existing empty values into invalid enum states."""
    if payload_kind in ("empty_optional", "blank_optional"):
        api_payload["namnsdag"] = []
        api_payload.pop("helgdagsafton")
        if payload_kind == "blank_optional":
            for field in ("helgdag", "helgdagsafton", "flaggdag"):
                api_payload[field] = ""
        calendar_data[TODAY] = SwedishCalendar.from_api_data(
            ApiData.from_json(api_payload)
        ).with_themes(ThemeData(TODAY.isoformat(), []))
    elif payload_kind == "themes_only":
        calendar_data[TODAY] = SwedishCalendar.from_themes(
            ThemeData(TODAY.isoformat(), [])
        )
    else:
        calendar_data.clear()

    await setup_entry(hass)
    for key in ("eve", "holiday", "name_day", "flag_day"):
        assert hass.states.get(f"sensor.swedish_calendar_{key}").state == "unknown"
    assert hass.states.get("sensor.swedish_calendar_theme_day").state == ""
    if payload_kind in ("themes_only", "no_data"):
        for key in ("date", "weekday", "week", "day_of_week"):
            assert hass.states.get(f"sensor.swedish_calendar_{key}").state == "unknown"
        for key in BOOLEAN_SENSORS:
            assert hass.states.get(f"sensor.swedish_calendar_{key}").state == "Nej"

    for key in ["weekday", *BOOLEAN_SENSORS]:
        state = hass.states.get(f"sensor.swedish_calendar_{key}")
        assert_enum_metadata(state, WEEKDAYS if key == "weekday" else ["Ja", "Nej"])
        options = state.attributes.get("options", [])
        assert "unknown" not in options
        assert "unavailable" not in options


async def test_multiple_text_values_are_not_enums(
    hass, api_payload, calendar_data, fetch_calendar
):
    """Keep list formatting, composite text and user-defined themes unchanged."""
    api_payload.update(
        {
            "namnsdag": ["Harry", "Harriet"],
            "helgdagsafton": "Trettondagsafton",
            "helgdag": "Kristi himmelsfärdsdag, Första Maj",
            "flaggdag": "Första maj, Kung Carl XVI Gustafs födelsedag",
        }
    )
    calendar_data[TODAY] = SwedishCalendar.from_api_data(
        ApiData.from_json(api_payload)
    ).with_themes(
        ThemeData(TODAY.isoformat(), ["Kanelbullens dag", "Min egen temadag"])
    )
    await setup_entry(hass)
    expected = {
        "name_day": "Harry,Harriet",
        "eve": "Trettondagsafton",
        "holiday": "Kristi himmelsfärdsdag, Första Maj",
        "flag_day": "Första maj, Kung Carl XVI Gustafs födelsedag",
        "theme_day": "Kanelbullens dag,Min egen temadag",
    }
    for key, value in expected.items():
        state = hass.states.get(f"sensor.swedish_calendar_{key}")
        assert state.state == value
        assert "device_class" not in state.attributes
        assert "options" not in state.attributes


@pytest.mark.parametrize(
    ("day", "week", "day_of_week"),
    [(date(2026, 12, 31), 53, 4), (date(2027, 1, 1), 53, 5)],
)
async def test_date_and_numbers_across_iso_year_boundary(
    hass,
    api_payload,
    calendar_data,
    fetch_calendar,
    frozen_date,
    day,
    week,
    day_of_week,
):
    """Keep the ISO week number intact when the calendar year changes."""
    frozen_date.move_to(day.isoformat() + " 12:00:00")
    api_payload.update(
        {"datum": day.isoformat(), "vecka": str(week), "dag i vecka": str(day_of_week)}
    )
    calendar_data.clear()
    calendar_data[day] = SwedishCalendar.from_api_data(ApiData.from_json(api_payload))
    await setup_entry(hass)
    assert hass.states.get("sensor.swedish_calendar_date").state == day.isoformat()
    assert sensor_entity(hass, "sensor.swedish_calendar_date").native_value == day
    for key, number in [("week", week), ("day_of_week", day_of_week)]:
        entity_id = f"sensor.swedish_calendar_{key}"
        assert hass.states.get(entity_id).state == str(number)
        assert type(sensor_entity(hass, entity_id).native_value) is int
        assert sensor_entity(hass, entity_id).native_value == number


async def test_custom_entity_id_survives_unload_and_reload(hass, fetch_calendar):
    """Updating sensor metadata must not replace an existing registry identity."""
    entry = await setup_entry(hass)
    registry = er.async_get(hass)
    old_id = "sensor.swedish_calendar_weekday"
    custom_id = "sensor.min_veckodag"
    registry.async_update_entity(old_id, new_entity_id=custom_id)
    await hass.async_block_till_done()
    original = registry.async_get(custom_id)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert registry.async_get(old_id) is None
    assert registry.async_get(custom_id).id == original.id
    assert registry.async_get(custom_id).unique_id == "sensor.week_day"
    assert hass.states.get(old_id) is None
    state = hass.states.get(custom_id)
    assert state.state == "Torsdag"
    assert_enum_metadata(state, WEEKDAYS)


async def test_coordinator_failure_and_recovery_preserve_availability(
    hass, calendar_data, fetch_calendar
):
    """The sensor base class must retain coordinator availability handling."""
    entry = await setup_entry(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    coordinator.async_set_update_error(
        UpdateFailed("Calendar is temporarily unavailable")
    )
    await hass.async_block_till_done()
    for key in EXPECTED_SENSORS:
        assert hass.states.get(f"sensor.swedish_calendar_{key}").state == "unavailable"

    coordinator.async_set_updated_data(calendar_data)
    await hass.async_block_till_done()
    for key, (_, expected_state) in EXPECTED_SENSORS.items():
        assert hass.states.get(f"sensor.swedish_calendar_{key}").state == expected_state
    assert_enum_metadata(hass.states.get("sensor.swedish_calendar_weekday"), WEEKDAYS)
