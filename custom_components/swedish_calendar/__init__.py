from datetime import timedelta
import logging
import os

import voluptuous as vol

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform

from .const import (
    CONF_AUTO_UPDATE,
    CONF_CACHE,
    CONF_CALENDAR,
    CONF_DAYS_AFTER_TODAY,
    CONF_DAYS_BEFORE_TODAY,
    CONF_DEFAULT_CACHE_DIR,
    CONF_DIR,
    CONF_ENABLED,
    CONF_EXCLUDE,
    CONF_INCLUDE,
    CONF_RETENTION,
    CONF_SPECIAL_THEMES,
    CONF_SPECIAL_THEMES_DIR,
    DOMAIN,
    SENSOR_TYPES,
    SPECIAL_THEMES_FILE_NAME,
    THEME_DAY,
)
from .coordinator import CalendarDataCoordinator
from .types import CacheConfig, CalendarConfig, SpecialThemesConfig

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

CACHE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENABLED, default=False): cv.string,
        vol.Optional(CONF_DIR, default=os.path.join(os.path.dirname(__file__), CONF_DEFAULT_CACHE_DIR)): cv.string,
        vol.Optional(CONF_RETENTION, default=timedelta(days=7)): vol.All(
            cv.time_period, cv.positive_timedelta
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                # deprecated but hass can't move to an inner object, so we handle everything ourselves
                vol.Optional(CONF_SPECIAL_THEMES_DIR, default=''): cv.string,
                vol.Optional(CONF_SPECIAL_THEMES, default={}): THEMES_SCHEMA,
                vol.Optional(CONF_CACHE, default={}): CACHE_SCHEMA,
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
    cache_config = get_cache_config(conf)

    coordinator = CalendarDataCoordinator(hass, special_themes_config, calendar_config, cache_config)

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
    special_themes_path = None
    themes_are_excluded = THEME_DAY in config[CONF_EXCLUDE]

    if not themes_are_excluded:
        user_defined_dir = _get_user_defined_special_themes_dir(config)
        dirs_to_search = [user_defined_dir, os.path.dirname(__file__)]

        for theme_dir in dirs_to_search:
            if theme_dir is not None:
                maybe_path = os.path.join(theme_dir, SPECIAL_THEMES_FILE_NAME)
                _LOGGER.debug("Locating specialThemes.json, trying %s", maybe_path)
                if os.path.exists(maybe_path):
                    special_themes_path = maybe_path
                    break

        if special_themes_path is None:
            _LOGGER.warning('Special themes is not excluded but no specialThemes.json file can be found! Either '
                            'exclude %s, or add a config entry pointing to a directory containing specialThemes.json',
                            THEME_DAY)

    auto_update = config[CONF_SPECIAL_THEMES][CONF_AUTO_UPDATE]

    return SpecialThemesConfig(special_themes_path, auto_update)


def _get_user_defined_special_themes_dir(config: dict) -> str | None:
    deprecated_themes_path: str | None = config[CONF_SPECIAL_THEMES_DIR]
    new_themes_path: str | None = config[CONF_SPECIAL_THEMES][CONF_DIR]
    deprecated_since = 'v2.2.0'

    #  Warn and (maybe) migrate old config to new
    if deprecated_themes_path:
        if not new_themes_path:
            _LOGGER.warning('WARNING! Config entry "%s" is deprecated since %s, please migrate to themes schema '
                            'instead! Using old value for now...',
                            CONF_SPECIAL_THEMES_DIR,
                            deprecated_since)
            new_themes_path = deprecated_themes_path
        else:
            _LOGGER.warning('WARNING! Config entry "%s" is deprecated since %s, please remove from the config!',
                            CONF_SPECIAL_THEMES_DIR,
                            deprecated_since)
    return new_themes_path


def get_calendar_config(config: dict) -> CalendarConfig:
    calendar_config = config[CONF_CALENDAR]

    return CalendarConfig(
        includes=calendar_config[CONF_INCLUDE],
        days_before_today=calendar_config[CONF_DAYS_BEFORE_TODAY],
        days_after_today=calendar_config[CONF_DAYS_AFTER_TODAY]
    )


def get_cache_config(config: dict) -> CacheConfig:
    cache_config = config[CONF_CACHE]

    return CacheConfig(
        enabled=cache_config[CONF_ENABLED],
        cache_dir=cache_config[CONF_DIR],
        retention=cache_config[CONF_RETENTION]
    )
