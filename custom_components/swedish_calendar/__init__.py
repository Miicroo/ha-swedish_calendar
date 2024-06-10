from datetime import timedelta
import logging
import os

from homeassistant import config_entries
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

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

PLATFORMS = [
    Platform.CALENDAR,
    Platform.SENSOR
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    conf = dict(entry.data)

    special_themes_config = get_special_themes_config(conf)
    calendar_config = get_calendar_config(conf)
    cache_config = get_cache_config(conf)

    data_coordinator = CalendarDataCoordinator(hass, special_themes_config, calendar_config, cache_config)

    # Fetch initial data so we have data when entities subscribe
    await data_coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "conf": conf,
        "coordinator": data_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    # No config entry exists and configuration.yaml config exists, trigger the import flow.
    if not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=config
            )
        )

    return True


def get_special_themes_config(config: dict) -> SpecialThemesConfig:
    special_themes_path = None
    themes_are_excluded = THEME_DAY in config[CONF_EXCLUDE]

    if not themes_are_excluded:
        user_defined_dir = config[CONF_SPECIAL_THEMES][CONF_DIR]
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


def get_calendar_config(config: dict) -> CalendarConfig:
    calendar_config = config[CONF_CALENDAR]

    return CalendarConfig(
        includes=calendar_config[CONF_INCLUDE],
        days_before_today=calendar_config[CONF_DAYS_BEFORE_TODAY],
        days_after_today=calendar_config[CONF_DAYS_AFTER_TODAY]
    )


def get_cache_config(config: dict) -> CacheConfig:
    cache_config = config[CONF_CACHE]
    retention_config = cache_config[CONF_RETENTION]
    retention = retention_config if isinstance(retention_config, timedelta) else timedelta(days=retention_config)
    return CacheConfig(
        enabled=cache_config[CONF_ENABLED],
        cache_dir=cache_config[CONF_DIR],
        retention=retention
    )
