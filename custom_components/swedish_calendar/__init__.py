import logging
import os

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

from .const import DOMAIN, CONF_SPECIAL_THEMES_DIR, SPECIAL_THEMES_FILE_NAME, CONF_EXCLUDE, SENSOR_TYPES, CONF_INCLUDE, \
    CONF_DAYS_BEFORE_TODAY, CONF_DAYS_AFTER_TODAY, CONF_CALENDAR, CONF_AUTO_UPDATE, CONF_DIR, CONF_SPECIAL_THEMES
from .provider import CalendarDataCoordinator
from .types import SpecialThemesConfig, CalendarConfig

CALENDAR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_INCLUDE, default=[]):
            vol.All(cv.ensure_list, vol.Length(min=0), [vol.In(SENSOR_TYPES)]),
        vol.Optional(CONF_DAYS_BEFORE_TODAY, default=0): cv.positive_int,
        vol.Optional(CONF_DAYS_AFTER_TODAY, default=0): cv.positive_int,
    }
)

THEMES_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_DIR, default=''): cv.string,
        vol.Optional(CONF_AUTO_UPDATE, default=False): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                # deprecated but hass cant move to an inner object, so we handle everything ourselves
                vol.Optional(CONF_SPECIAL_THEMES_DIR, default=''): cv.string,
                vol.Optional(CONF_SPECIAL_THEMES, default={}): THEMES_SCHEMA,
                vol.Optional(CONF_CALENDAR, default={}): CALENDAR_SCHEMA,
                vol.Optional(CONF_EXCLUDE, default=[]):
                    vol.All(cv.ensure_list, vol.Length(min=0), [vol.In(SENSOR_TYPES)]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    conf = config[DOMAIN]
    special_themes_config = get_special_themes_config(conf)
    calendar_config = get_calendar_config(conf)

    coordinator = CalendarDataCoordinator(hass, special_themes_config, calendar_config)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    hass.data[DOMAIN] = {
        "conf": conf,
        "coordinator": coordinator,
    }

    hass.async_create_task(async_load_platform(hass, Platform.SENSOR, DOMAIN, {}, conf))
    hass.async_create_task(async_load_platform(hass, Platform.CALENDAR, DOMAIN, {}, conf))

    return True


def get_special_themes_config(config: dict) -> SpecialThemesConfig:
    path = None
    deprecated_themes_path: str = config[CONF_SPECIAL_THEMES_DIR]
    new_themes_path: str = config[CONF_SPECIAL_THEMES][CONF_DIR]
    deprecated_since = 'v2.2.0'

    #  Warn and (maybe) migrate old config to new
    if deprecated_themes_path:
        if not new_themes_path:
            _LOGGER.error('WARNING! Config entry "%s" is deprecated since %s, please migrate to themes schema instead! '
                          'Using old value for now...',
                          CONF_SPECIAL_THEMES_DIR,
                          deprecated_since)
            new_themes_path = deprecated_themes_path
        else:
            _LOGGER.error('WARNING! Config entry "%s" is deprecated since %s, please remove from the config!',
                          CONF_SPECIAL_THEMES_DIR,
                          deprecated_since)
    if new_themes_path:
        path = os.path.join(new_themes_path, SPECIAL_THEMES_FILE_NAME)
        if not os.path.exists(path):
            _LOGGER.warning("Special themes is configured but file cannot be found at %s, please check your config",
                            path)
    auto_update = config[CONF_SPECIAL_THEMES][CONF_AUTO_UPDATE]

    return SpecialThemesConfig(path, auto_update)


def get_calendar_config(config: dict) -> CalendarConfig:
    calendar_config = config[CONF_CALENDAR]

    return CalendarConfig(
        includes=calendar_config[CONF_INCLUDE],
        days_before_today=calendar_config[CONF_DAYS_BEFORE_TODAY],
        days_after_today=calendar_config[CONF_DAYS_AFTER_TODAY]
    )
