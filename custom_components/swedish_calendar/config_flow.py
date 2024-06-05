import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigFlow
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector
from homeassistant.helpers.typing import ConfigType

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
    DOMAIN_FRIENDLY_NAME,
    SENSOR_TYPES,
    SPECIAL_THEMES_FILE_NAME,
    THEME_DAY,
)

_LOGGER = logging.getLogger(__name__)

THEMES_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_DIR, default=os.path.dirname(__file__)): cv.string,
        vol.Optional(CONF_AUTO_UPDATE, default=False): cv.boolean,
    },
)

CACHE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENABLED, default=False): cv.boolean,
        vol.Optional(CONF_DIR, default=os.path.join(os.path.dirname(__file__), CONF_DEFAULT_CACHE_DIR)): cv.string,
        vol.Optional(CONF_RETENTION, default=7): cv.positive_int,
    },
)


class SwedishCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    data: dict[str, Any]

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        self._async_abort_entries_match(match_dict={})

        if user_input is not None:
            excludes = [key for key in SENSOR_TYPES if SENSOR_TYPES[key].friendly_name not in user_input[CONF_INCLUDE]]
            self.data[CONF_EXCLUDE] = excludes
            return await self.async_step_special_themes()

        self.data = {}
        sensors = SwedishCalendarConfigFlow._get_friendly_name_of_sensors()
        sensor_schema = vol.Schema(
            {
                vol.Optional(CONF_INCLUDE, default=sensors): selector({
                    "select": {
                        "options": sensors,
                        "multiple": True
                    }
                })
            }
        )

        return self.async_show_form(step_id="user", data_schema=sensor_schema)

    async def async_step_special_themes(self, user_input: dict[str, Any] | None = None):
        if THEME_DAY in self.data[CONF_EXCLUDE]:
            return await self.async_step_calendar()

        if user_input is not None:
            self.data[CONF_SPECIAL_THEMES] = user_input
            return await self.async_step_calendar()

        return self.async_show_form(step_id="special_themes", data_schema=THEMES_SCHEMA)

    async def async_step_calendar(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            user_input[CONF_INCLUDE] = [key for key in SENSOR_TYPES
                                        if SENSOR_TYPES[key].friendly_name in user_input[CONF_INCLUDE]]
            self.data[CONF_CALENDAR] = user_input

            return await self.async_step_cache()
        all_sensors = SwedishCalendarConfigFlow._get_friendly_name_of_sensors()
        already_included_sensors = [SENSOR_TYPES[key].friendly_name for key in SENSOR_TYPES if
                                    key not in self.data[CONF_EXCLUDE]]

        calendar_schema = vol.Schema(
            {
                vol.Optional(CONF_INCLUDE, default=already_included_sensors): selector({
                    "select": {
                        "options": all_sensors,
                        "multiple": True
                    }
                }),
                vol.Optional(CONF_DAYS_BEFORE_TODAY, default=0): cv.positive_int,
                vol.Optional(CONF_DAYS_AFTER_TODAY, default=0): cv.positive_int,
            }
        )

        return self.async_show_form(step_id="calendar", data_schema=calendar_schema)

    async def async_step_cache(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self.data[CONF_CACHE] = user_input
            return self.async_create_entry(title=DOMAIN_FRIENDLY_NAME, data=self.data)

        return self.async_show_form(step_id="cache", data_schema=CACHE_SCHEMA)

    async def async_step_import(self, import_data: ConfigType):
        """Import entry from configuration.yaml."""

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        import_data = import_data.get(DOMAIN) or {}

        self.data = {
            CONF_EXCLUDE: [key for key in SENSOR_TYPES
                           if key in (import_data.get(CONF_EXCLUDE) or [])
                           ]
        }

        imported_cache_config = import_data.get(CONF_CACHE) or {}
        self.data[CONF_CACHE] = {
            CONF_ENABLED: imported_cache_config.get(CONF_ENABLED) or False,
            CONF_DIR: imported_cache_config.get(CONF_DIR) or os.path.join(os.path.dirname(__file__),
                                                                          CONF_DEFAULT_CACHE_DIR),
            CONF_RETENTION: imported_cache_config.get(CONF_RETENTION).days if CONF_RETENTION in imported_cache_config else 7,
        }

        imported_calendar_config = import_data.get(CONF_CALENDAR) or {}
        self.data[CONF_CALENDAR] = {
            CONF_INCLUDE: [key for key in SENSOR_TYPES
                           if key in (imported_calendar_config.get(CONF_INCLUDE) or [])],
            CONF_DAYS_BEFORE_TODAY: imported_calendar_config.get(CONF_DAYS_BEFORE_TODAY) or 0,
            CONF_DAYS_AFTER_TODAY: imported_calendar_config.get(CONF_DAYS_AFTER_TODAY) or 0
        }

        imported_themes_config = import_data.get(CONF_SPECIAL_THEMES) or {}
        self.data[CONF_SPECIAL_THEMES] = {
            CONF_DIR: SwedishCalendarConfigFlow.get_special_themes_dir(import_data) or '',
            CONF_AUTO_UPDATE: imported_themes_config.get(CONF_AUTO_UPDATE) or False
        }

        persistent_notification.async_create(
            self.hass,
            "The configuration has been migrated to a config entry and can be safely removed from configuration.yaml. "
            "All edits to the config in configuration.yaml will be ignored. "
            "<a href='/config/integrations/integration/swedish_calendar'>Go to integration</a>.",
            f'{DOMAIN_FRIENDLY_NAME} migrated',
            DOMAIN
        )

        return self.async_create_entry(title=DOMAIN_FRIENDLY_NAME, data=self.data)

    @staticmethod
    def get_special_themes_dir(config: dict) -> str | None:
        special_themes_dir = None
        themes_are_excluded = THEME_DAY in (config.get(CONF_EXCLUDE) or [])

        if not themes_are_excluded:
            user_defined_dir = SwedishCalendarConfigFlow._get_user_defined_special_themes_dir(config)
            dirs_to_search = [user_defined_dir, os.path.dirname(__file__)]

            for theme_dir in dirs_to_search:
                if theme_dir is not None:
                    maybe_path = os.path.join(theme_dir, SPECIAL_THEMES_FILE_NAME)
                    _LOGGER.debug("Locating specialThemes.json, trying %s", maybe_path)
                    if os.path.exists(maybe_path):
                        special_themes_dir = theme_dir
                        break

            if special_themes_dir is None:
                _LOGGER.warning('Special themes is not excluded but no specialThemes.json file can be found! Either '
                                'exclude %s, or add a config entry pointing to a directory containing specialThemes.json',
                                THEME_DAY)

        return special_themes_dir

    @staticmethod
    def _get_user_defined_special_themes_dir(config: dict) -> str | None:
        deprecated_themes_path: str | None = config.get(CONF_SPECIAL_THEMES_DIR)
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

    @staticmethod
    def _get_friendly_name_of_sensors():
        return [SENSOR_TYPES[key].friendly_name
                for key in SENSOR_TYPES]
