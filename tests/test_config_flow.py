"""Config flow that sets up the integration through the HomeAssistant UI."""
import os
from typing import Any

from custom_components.swedish_calendar import (
    CONF_AUTO_UPDATE,
    CONF_CACHE,
    CONF_CALENDAR,
    CONF_DAYS_AFTER_TODAY,
    CONF_DAYS_BEFORE_TODAY,
    CONF_DIR,
    CONF_ENABLED,
    CONF_EXCLUDE,
    CONF_INCLUDE,
    CONF_RETENTION,
    CONF_SPECIAL_THEMES,
    DOMAIN,
    SENSOR_TYPES,
    THEME_DAY,
)
from custom_components.swedish_calendar.config_flow import SwedishCalendarConfigFlow
from custom_components.swedish_calendar.const import (
    CONF_DEFAULT_CACHE_DIR,
    CONF_LOCAL_MODE,
    DOMAIN_FRIENDLY_NAME,
)
from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.data_entry_flow import FlowResult, FlowResultType


async def test_flow_included_sensors(hass):
    """Test flow: include/exclude sensors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    sensor_keys = [key for key in SENSOR_TYPES]
    excludes = [sensor_keys[0], sensor_keys[1]]
    includes = [
        SENSOR_TYPES[key].friendly_name for key in sensor_keys if key not in excludes
    ]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_INCLUDE: includes}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "local_mode"

    handler = hass.config_entries.flow._progress[result["flow_id"]]
    assert handler.data[CONF_EXCLUDE] == excludes


async def _set_up_sensor_inclusion(hass, sensor_type_keys: list[str]) -> FlowResult:
    # Set up excluded/included sensors
    included_sensor_config = {
        CONF_INCLUDE: [SENSOR_TYPES[key].friendly_name for key in sensor_type_keys]
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=included_sensor_config
    )


async def test_flow_local_mode(hass):
    """Test flow: local mode."""
    result = await _set_up_sensor_inclusion(hass, [THEME_DAY])
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "local_mode"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCAL_MODE: False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "special_themes"

    flow_handler = hass.config_entries.flow._progress[result["flow_id"]]
    local_mode_value = flow_handler.data[CONF_LOCAL_MODE]
    assert not local_mode_value


async def test_flow_special_themes(hass):
    """Test flow: special themes."""
    result = await _set_up_sensor_inclusion(hass, [THEME_DAY])
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCAL_MODE: False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "special_themes"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_DIR: "/my_dir", CONF_AUTO_UPDATE: True}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "calendar"

    flow_handler = hass.config_entries.flow._progress[result["flow_id"]]
    themes_configuration = flow_handler.data[CONF_SPECIAL_THEMES]
    assert themes_configuration[CONF_DIR] == "/my_dir"
    assert themes_configuration[CONF_AUTO_UPDATE]


async def test_flow_calendar(hass):
    """Test flow: calendar."""
    # Set up excluded/included sensors
    included_sensors = [list(SENSOR_TYPES.keys())[0]]
    friendly_names_included = [
        SENSOR_TYPES[key].friendly_name for key in included_sensors
    ]
    result = await _set_up_sensor_inclusion(hass, included_sensors)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCAL_MODE: False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "calendar"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_INCLUDE: friendly_names_included,
            CONF_DAYS_BEFORE_TODAY: 7,
            CONF_DAYS_AFTER_TODAY: 14,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cache"

    flow_handler = hass.config_entries.flow._progress[result["flow_id"]]
    calendar_configuration = flow_handler.data[CONF_CALENDAR]
    assert calendar_configuration[CONF_INCLUDE] == included_sensors
    assert calendar_configuration[CONF_DAYS_BEFORE_TODAY] == 7
    assert calendar_configuration[CONF_DAYS_AFTER_TODAY] == 14


async def test_flow_cache(hass):
    """Test flow: cache."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "cache"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cache"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLED: True, CONF_DIR: "/my_path", CONF_RETENTION: 14},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    cache_configuration = result["data"][CONF_CACHE]
    assert cache_configuration[CONF_ENABLED]
    assert cache_configuration[CONF_DIR] == "/my_path"
    assert cache_configuration[CONF_RETENTION] == 14


async def test_full_flow(hass):
    """Test full config flow."""
    # User step
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["step_id"] == "user"

    # Include all sensors
    included_sensors = [key for key in SENSOR_TYPES]
    included_sensors_friendly_names = [
        SENSOR_TYPES[key].friendly_name for key in included_sensors
    ]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_INCLUDE: included_sensors_friendly_names}
    )

    # Local mode step
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["step_id"] == "local_mode"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCAL_MODE: False}
    )

    # Special themes step
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["step_id"] == "special_themes"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_DIR: "/my_dir", CONF_AUTO_UPDATE: True}
    )

    # Calendar step
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["step_id"] == "calendar"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_INCLUDE: included_sensors_friendly_names,
            CONF_DAYS_BEFORE_TODAY: 7,
            CONF_DAYS_AFTER_TODAY: 14,
        },
    )

    # Cache step
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["step_id"] == "cache"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLED: True, CONF_DIR: "/my_path", CONF_RETENTION: 14},
    )

    # Assert result
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DOMAIN_FRIENDLY_NAME

    # Assert entry
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert result["data"] == entry.data

    # Assert data, makes sure that no step has messed with the data that another step has set up
    assert entry.data[CONF_EXCLUDE] == []
    assert entry.data[CONF_SPECIAL_THEMES][CONF_DIR] == "/my_dir"
    assert entry.data[CONF_SPECIAL_THEMES][CONF_AUTO_UPDATE]
    assert entry.data[CONF_CALENDAR][CONF_INCLUDE] == included_sensors
    assert entry.data[CONF_CALENDAR][CONF_DAYS_BEFORE_TODAY] == 7
    assert entry.data[CONF_CALENDAR][CONF_DAYS_AFTER_TODAY] == 14
    assert entry.data[CONF_CACHE][CONF_ENABLED]
    assert entry.data[CONF_CACHE][CONF_DIR] == "/my_path"
    assert entry.data[CONF_CACHE][CONF_RETENTION] == 14


async def test_flow_special_themes_dont_configure_special_themes_if_theme_day_is_excluded(
    hass,
):
    """Test special themes form is ignored if theme day sensor is excluded."""
    # Don't include theme day, go straight to calendar set up
    result = await _set_up_sensor_inclusion(hass, [])
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCAL_MODE: False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "calendar"


async def test_flow_special_themes_dont_configure_special_themes_if_local_mode(
    hass,
):
    """Test special themes form is ignored if theme day sensor is excluded."""
    # Don't include theme day, go straight to calendar set up
    result = await _set_up_sensor_inclusion(hass, [THEME_DAY])
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCAL_MODE: True}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "calendar"


""" Test config flow schemas ."""


def _config_flow_file_dir():
    return os.path.dirname(
        os.path.abspath("custom_components/swedish_calendar/config_flow.py")
    )


async def test_get_include_sensor_schema_defaults_to_all_sensors():
    """Test default schema for sensor inclusion/exclusion."""
    handler = SwedishCalendarConfigFlow()
    schema = handler._get_include_sensor_schema()

    default_schema = schema({})
    all_sensors = [SENSOR_TYPES[key].friendly_name for key in SENSOR_TYPES]

    assert default_schema[CONF_INCLUDE] == all_sensors


async def test_get_local_mode_schema_defaults():
    """Test default schema for special themes."""
    handler = SwedishCalendarConfigFlow()
    schema = handler._get_local_mode_schema()

    default_schema = schema({})

    assert not default_schema[CONF_LOCAL_MODE]


async def test_get_special_themes_schema_defaults():
    """Test default schema for special themes."""
    handler = SwedishCalendarConfigFlow()
    schema = handler._get_themes_schema()

    default_schema = schema({})

    assert default_schema[CONF_DIR] == _config_flow_file_dir()
    assert not default_schema[CONF_AUTO_UPDATE]


async def test_get_calendar_schema_defaults():
    """Test default schema for calendar."""
    handler = SwedishCalendarConfigFlow()
    handler.data[CONF_EXCLUDE] = []  # Will always be set

    schema = handler._get_calendar_schema()

    default_schema = schema({})
    all_sensors = [SENSOR_TYPES[key].friendly_name for key in SENSOR_TYPES]

    assert default_schema[CONF_INCLUDE] == all_sensors
    assert default_schema[CONF_DAYS_BEFORE_TODAY] == 0
    assert default_schema[CONF_DAYS_AFTER_TODAY] == 0


async def test_get_cache_schema_defaults():
    """Test default schema for cache."""
    handler = SwedishCalendarConfigFlow()
    schema = handler._get_cache_schema()

    default_schema = schema({})

    assert not default_schema[CONF_ENABLED]
    assert (
        default_schema[CONF_DIR]
        == f"{_config_flow_file_dir()}/{CONF_DEFAULT_CACHE_DIR}"
    )
    assert default_schema[CONF_RETENTION] == 7


def _entry(data: dict[str:Any]) -> ConfigEntry:
    return ConfigEntry(
        domain=DOMAIN, source="unittest", title=DOMAIN, version=1, data=data
    )


async def test_get_include_sensor_schema_entry_present():
    """Test (reconfiguration) schema for sensor inclusion/exclusion when a config entry is already present."""
    handler = SwedishCalendarConfigFlow()
    handler.config_entry = _entry({CONF_EXCLUDE: [THEME_DAY]})
    schema = handler._get_include_sensor_schema()

    actual_schema = schema({})
    all_sensors_except_theme_day = [
        SENSOR_TYPES[key].friendly_name for key in SENSOR_TYPES if key != THEME_DAY
    ]
    assert actual_schema[CONF_INCLUDE] == all_sensors_except_theme_day


async def test_get_special_themes_schema_entry_present():
    """Test (reconfiguration) schema for special themes when a config entry is already present."""
    handler = SwedishCalendarConfigFlow()
    handler.config_entry = _entry(
        {CONF_SPECIAL_THEMES: {CONF_DIR: "/my_dir", CONF_AUTO_UPDATE: True}}
    )
    schema = handler._get_themes_schema()

    actual_schema = schema({})

    assert actual_schema[CONF_DIR] == "/my_dir"
    assert actual_schema[CONF_AUTO_UPDATE]


async def test_get_calendar_schema_entry_present():
    """Test (reconfiguration) schema for calendar when a config entry is already present."""
    handler = SwedishCalendarConfigFlow()
    handler.data[CONF_EXCLUDE] = []  # Will always be set
    handler.config_entry = _entry(
        {
            CONF_CALENDAR: {
                CONF_INCLUDE: [THEME_DAY],
                CONF_DAYS_BEFORE_TODAY: 1,
                CONF_DAYS_AFTER_TODAY: 1,
            }
        }
    )

    schema = handler._get_calendar_schema()

    actual_schema = schema({})

    assert actual_schema[CONF_INCLUDE] == [SENSOR_TYPES[THEME_DAY].friendly_name]
    assert actual_schema[CONF_DAYS_BEFORE_TODAY] == 1
    assert actual_schema[CONF_DAYS_AFTER_TODAY] == 1


async def test_get_calendar_schema_entry_present_but_sensor_is_in_exclude_list():
    """Test calendar schema only includes union of includes from entry and sensors not in exclude list."""
    handler = SwedishCalendarConfigFlow()
    handler.data[CONF_EXCLUDE] = ["week"]
    handler.config_entry = _entry(
        {
            CONF_CALENDAR: {
                CONF_INCLUDE: [THEME_DAY, "week"],
            }
        }
    )

    schema = handler._get_calendar_schema()
    actual_schema = schema({})

    # Don't show excluded sensors by default
    assert actual_schema[CONF_INCLUDE] == [SENSOR_TYPES[THEME_DAY].friendly_name]


async def test_get_cache_schema_entry_present():
    """Test (reconfiguration) schema for cache when a config entry is already present."""
    handler = SwedishCalendarConfigFlow()
    handler.config_entry = _entry(
        {CONF_CACHE: {CONF_DIR: "/my_dir", CONF_ENABLED: True, CONF_RETENTION: 10}}
    )
    schema = handler._get_cache_schema()

    actual_schema = schema({})

    assert actual_schema[CONF_ENABLED]
    assert actual_schema[CONF_DIR] == "/my_dir"
    assert actual_schema[CONF_RETENTION] == 10
