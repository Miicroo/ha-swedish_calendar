"""Test calendar conditions through Home Assistant validation and execution."""

from copy import deepcopy
from datetime import date, timedelta
import importlib
from unittest.mock import AsyncMock, patch

from freezegun import freeze_time
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
import voluptuous as vol

from custom_components.swedish_calendar.const import DOMAIN, SENSOR_TYPES
from custom_components.swedish_calendar.types import ApiData, SwedishCalendar, ThemeData
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import ConditionError, ConditionErrorMessage
from homeassistant.helpers import condition, translation
from homeassistant.helpers.update_coordinator import UpdateFailed

TODAY = date(2026, 11, 16)
CONDITION_KEYS = ("is_holiday", "is_holiday_eve", "is_flag_day")
SUPPORTS_CONDITIONS = hasattr(getattr(condition, "Condition", object), "_async_check")


@pytest.fixture
def require_conditions():
    """Skip the new API tests on older supported Home Assistant versions."""
    if not SUPPORTS_CONDITIONS:
        pytest.skip("This Home Assistant version predates condition platforms")


@pytest.fixture
def frozen_date():
    """Give every calendar lookup a known date without changing production time."""
    with freeze_time("2026-11-16 12:00:00") as freezer:
        yield freezer


@pytest.fixture
def api_payload():
    """Return a valid ordinary day in the provider's JSON format."""
    return {
        "datum": TODAY.isoformat(),
        "veckodag": "Måndag",
        "arbetsfri dag": "Nej",
        "röd dag": "Nej",
        "vecka": "47",
        "dag i vecka": "1",
        "namnsdag": ["Vibeke", "Viveka"],
        "flaggdag": "",
        "dag före arbetsfri helgdag": "Nej",
    }


@pytest.fixture
def calendar_data(api_payload):
    """Use the integration's parsed models as coordinator data."""
    return {TODAY: SwedishCalendar.from_api_data(ApiData.from_json(api_payload))}


@pytest.fixture
async def loaded_calendar(hass, require_conditions, frozen_date, calendar_data):
    """Set up a real entry with every sensor excluded and fetching mocked."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Swedish calendar",
        data={
            "exclude": list(SENSOR_TYPES),
            "local_mode": True,
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
    with patch(
        "custom_components.swedish_calendar.coordinator.CalendarDataCoordinator.update_data",
        new_callable=AsyncMock,
        return_value=calendar_data,
    ) as fetch:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        yield entry, fetch


@pytest.fixture
async def build_checker(hass, require_conditions):
    """Use Home Assistant's actual platform loader, validator and checker."""
    if condition.CONDITIONS not in hass.data:
        await condition.async_setup(hass)
    checkers = []

    async def build(config):
        validated = await condition.async_validate_condition_config(
            hass, deepcopy(config)
        )
        checker = await condition.async_from_config(hass, validated)
        checkers.append(checker)
        return checker

    yield build
    for checker in checkers:
        checker.async_unload()


def config_for(key, day="any"):
    """Build the public YAML configuration for a calendar condition."""
    return {"condition": f"{DOMAIN}.{key}", "options": {"day": day}}


def update_day(calendar_data, api_payload, **values):
    """Change provider values while leaving raw strings unmodified."""
    api_payload.update(values)
    calendar_data[TODAY] = SwedishCalendar.from_api_data(ApiData.from_json(api_payload))


async def test_condition_registration_is_version_compatible(hass):
    """Expose the three conditions only when the platform API is available."""
    platform = importlib.import_module(f"custom_components.{DOMAIN}.condition")
    registered = await platform.async_get_conditions(hass)
    assert set(registered) == (set(CONDITION_KEYS) if SUPPORTS_CONDITIONS else set())


async def test_condition_descriptions_and_translations_load_through_home_assistant(
    hass, loaded_calendar, build_checker
):
    """Load usable dropdown descriptions and translations through HA's caches."""
    await build_checker(config_for("is_holiday"))
    descriptions = await condition.async_get_all_descriptions(hass)
    assert {key for key in descriptions if key.startswith(f"{DOMAIN}.")} == {
        f"{DOMAIN}.{key}" for key in CONDITION_KEYS
    }
    for key in CONDITION_KEYS:
        description = descriptions[f"{DOMAIN}.{key}"]
        assert "target" not in description
        assert set(description["fields"]) == {"day"}
        field = description["fields"]["day"]
        assert field["required"] is False
        assert "default" not in field
        selector = field["selector"]["select"]
        assert selector["mode"] == "dropdown"
        assert selector["custom_value"] is False
        assert "any" not in selector["options"]
        assert len(selector["options"]) == len(set(selector["options"]))
    eve_options = descriptions[f"{DOMAIN}.is_holiday_eve"]["fields"]["day"]["selector"][
        "select"
    ]["options"]
    assert {"Julafton", "Midsommarafton", "Nyårsafton", "Påskafton"} <= set(eve_options)

    for language in ("en", "sv"):
        labels = await translation.async_get_translations(
            hass, language, "conditions", integrations={DOMAIN}
        )
        errors = await translation.async_get_translations(
            hass, language, "exceptions", integrations={DOMAIN}
        )
        for key in CONDITION_KEYS:
            prefix = f"component.{DOMAIN}.conditions.{key}"
            assert labels[f"{prefix}.name"]
            assert labels[f"{prefix}.fields.day.name"]
            assert labels[f"{prefix}.fields.day.description"]
        assert errors[
            f"component.{DOMAIN}.exceptions.calendar_data_unavailable.message"
        ]


@pytest.mark.parametrize(
    ("key", "field", "raw", "selected", "expected"),
    [
        (
            "is_holiday",
            "helgdag",
            "Kristi himmelsfärdsdag, Första maj",
            "Första Maj",
            True,
        ),
        (
            "is_holiday",
            "helgdag",
            "Kristi himmelsfärdsdag, Första maj",
            "maj",
            False,
        ),
        (
            "is_flag_day",
            "flaggdag",
            "Sveriges nationaldag, Pingstdagen",
            "Pingstdagen",
            True,
        ),
        (
            "is_flag_day",
            "flaggdag",
            "Sveriges nationaldag, Pingstdagen",
            "nationaldag",
            False,
        ),
        (
            "is_holiday_eve",
            "helgdagsafton",
            "  Skärtorsdagen , Trettondagsafton  ",
            "  skärtorsdagen  ",
            True,
        ),
        (
            "is_holiday",
            "helgdag",
            "Min nya helgdag",
            "Min nya helgdag",
            True,
        ),
        (
            "is_holiday_eve",
            "helgdagsafton",
            "Min nya afton",
            "Min nya afton",
            True,
        ),
        (
            "is_flag_day",
            "flaggdag",
            "En ny flagganledning",
            "En ny flagganledning",
            True,
        ),
    ],
)
async def test_named_conditions_match_complete_tokens(
    hass,
    loaded_calendar,
    build_checker,
    calendar_data,
    api_payload,
    key,
    field,
    raw,
    selected,
    expected,
):
    """Match whole names, including new online values, without substring matches."""
    update_day(calendar_data, api_payload, **{field: raw})
    checker = await build_checker(config_for(key, selected))
    fetch_count = loaded_calendar[1].call_count
    assert checker.async_check() is expected
    assert loaded_calendar[1].call_count == fetch_count
    assert api_payload[field] == raw
    attribute = {
        "helgdag": "holiday",
        "helgdagsafton": "eve",
        "flaggdag": "reason_for_flagging",
    }[field]
    assert calendar_data[TODAY].get_value_by_attribute(attribute) == raw
    assert not any(
        state.entity_id.startswith("sensor.swedish_calendar_")
        for state in hass.states.async_all()
    )


@pytest.mark.parametrize(
    "eve",
    [
        "Julafton",
        "Midsommarafton",
        "Nyårsafton",
        "Påskafton",
        "Skärtorsdagen",
        "Valborgsmässoafton",
        "Pingstafton",
        "Allhelgonaafton",
        "Trettondagsafton",
    ],
)
async def test_recognized_eves_match_when_local_provider_puts_them_in_holiday(
    loaded_calendar, build_checker, calendar_data, api_payload, eve
):
    """Recognize every supported afton even when another holiday coincides."""
    update_day(calendar_data, api_payload, helgdag=f"Juldagen, {eve}")
    named = await build_checker(config_for("is_holiday_eve", eve))
    any_eve = await build_checker(config_for("is_holiday_eve"))
    assert named.async_check() is True
    assert any_eve.async_check() is True


async def test_holiday_text_is_not_automatically_an_eve(
    loaded_calendar, build_checker, calendar_data, api_payload
):
    """Only recognized afton names can cross from holiday into the eve condition."""
    update_day(calendar_data, api_payload, helgdag="Juldagen, En egen helgdag")
    for selected in ("any", "Juldagen", "En egen helgdag"):
        checker = await build_checker(config_for("is_holiday_eve", selected))
        assert checker.async_check() is False


@pytest.mark.parametrize(
    ("options", "key", "field", "value"),
    [
        (None, "is_holiday", "helgdag", "Julafton"),
        ({}, "is_holiday_eve", "helgdagsafton", "Min nya afton"),
        ({"day": "any"}, "is_flag_day", "flaggdag", "FN-dagen"),
        ({"day": None}, "is_holiday", "helgdag", "Julafton"),
    ],
)
async def test_default_any_matches_a_present_day(
    loaded_calendar,
    build_checker,
    calendar_data,
    api_payload,
    options,
    key,
    field,
    value,
):
    """Omitting the field or options has the same meaning as selecting any."""
    update_day(calendar_data, api_payload, **{field: value})
    config = {"condition": f"{DOMAIN}.{key}"}
    if options is not None:
        config["options"] = options
    checker = await build_checker(config)
    assert checker.async_check() is True


@pytest.mark.parametrize("key", CONDITION_KEYS)
async def test_valid_ordinary_day_is_false_and_can_be_negated(
    loaded_calendar, build_checker, key
):
    """A valid day without celebrations is different from missing calendar data."""
    config = config_for(key)
    checker = await build_checker(config)
    negated = await build_checker({"condition": "not", "conditions": [config]})
    assert checker.async_check() is False
    assert negated.async_check() is True


@pytest.mark.parametrize("selected", [True, 1, [], {}, "", "   ", "x" * 256])
async def test_invalid_day_options_are_rejected(build_checker, selected):
    """Reject invalid input instead of coercing it to an unexpected day name."""
    with pytest.raises(vol.Invalid):
        await build_checker(config_for("is_holiday", selected))


@pytest.mark.parametrize("options", [None, {}, {"day": None}])
async def test_optional_day_stays_unset_after_validation(
    hass, require_conditions, options
):
    """Saving and reopening an unused filter must not activate it with a sentinel."""
    config = {"condition": f"{DOMAIN}.is_holiday"}
    if options is not None:
        config["options"] = options
    validated = await condition.async_validate_condition_config(hass, config)
    assert "day" not in validated["options"]


@pytest.mark.parametrize(
    "problem",
    [
        "no_entry",
        "unloaded",
        "no_coordinator",
        "fetch_failed",
        "missing_today",
        "themes_only",
        "wrong_date",
        "invalid_calendar",
        "invalid_field",
        "unknown",
        "unavailable",
    ],
)
async def test_missing_calendar_data_is_an_error_even_inside_not(
    hass, loaded_calendar, build_checker, calendar_data, api_payload, problem
):
    """An unavailable integration must never become a successful NOT condition."""
    entry = loaded_calendar[0]
    checker = await build_checker(config_for("is_holiday"))
    negated = await build_checker(
        {"condition": "not", "conditions": [config_for("is_holiday")]}
    )
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    if problem == "no_entry":
        assert await hass.config_entries.async_remove(entry.entry_id)
    elif problem == "unloaded":
        assert await hass.config_entries.async_unload(entry.entry_id)
    elif problem == "no_coordinator":
        hass.data[DOMAIN][entry.entry_id].pop("coordinator")
    elif problem == "fetch_failed":
        coordinator.async_set_update_error(UpdateFailed("Temporary fetch failure"))
    elif problem == "missing_today":
        calendar_data.clear()
    elif problem == "themes_only":
        calendar_data[TODAY] = SwedishCalendar.from_themes(
            ThemeData(TODAY.isoformat(), ["Julafton"])
        )
    elif problem == "wrong_date":
        update_day(
            calendar_data, api_payload, datum=(TODAY - timedelta(days=1)).isoformat()
        )
    elif problem == "invalid_calendar":
        calendar_data[TODAY] = {}
    elif problem in ("unknown", "unavailable"):
        update_day(calendar_data, api_payload, helgdag=problem)
    else:
        update_day(calendar_data, api_payload, helgdag=["Julafton"])

    await hass.async_block_till_done()
    with pytest.raises(ConditionErrorMessage):
        checker.async_check()
    with pytest.raises(ConditionError):
        negated.async_check()


async def test_checker_follows_recovery_and_a_reloaded_entry(
    hass, loaded_calendar, build_checker, calendar_data, api_payload
):
    """A saved checker must resolve the current coordinator on every evaluation."""
    entry = loaded_calendar[0]
    checker = await build_checker(config_for("is_flag_day", "FN-dagen"))
    old_coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    assert checker.async_check() is False

    old_coordinator.async_set_update_error(UpdateFailed("Temporary fetch failure"))
    with pytest.raises(ConditionErrorMessage):
        checker.async_check()
    update_day(calendar_data, api_payload, flaggdag="FN-dagen")
    old_coordinator.async_set_updated_data(calendar_data)
    assert checker.async_check() is True

    assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(ConditionErrorMessage):
        checker.async_check()
    update_day(calendar_data, api_payload, flaggdag="Nobeldagen")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    new_coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    assert new_coordinator is not old_coordinator
    assert checker.async_check() is False
    update_day(calendar_data, api_payload, flaggdag="FN-dagen")
    assert checker.async_check() is True


async def test_conditions_use_home_assistant_local_date_across_midnight(
    hass, loaded_calendar, build_checker, calendar_data, api_payload, frozen_date
):
    """Use the configured timezone and reject yesterday until today's data arrives."""
    previous_timezone = hass.config.time_zone
    await hass.config.async_set_time_zone("Europe/Stockholm")
    try:
        checker = await build_checker(config_for("is_holiday", "Julafton"))
        update_day(calendar_data, api_payload, helgdag="Julafton")
        frozen_date.move_to("2026-11-16 22:59:59+00:00")
        assert checker.async_check() is True

        frozen_date.move_to("2026-11-16 23:00:00+00:00")
        with pytest.raises(ConditionErrorMessage):
            checker.async_check()
        tomorrow = TODAY + timedelta(days=1)
        api_payload["datum"] = tomorrow.isoformat()
        calendar_data[tomorrow] = SwedishCalendar.from_api_data(
            ApiData.from_json(api_payload)
        )
        assert checker.async_check() is True
    finally:
        await hass.config.async_set_time_zone(previous_timezone)
