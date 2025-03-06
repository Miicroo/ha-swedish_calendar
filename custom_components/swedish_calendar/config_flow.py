import logging
import os
from typing import Any

import voluptuous as vol
from voluptuous import Optional

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry, ConfigFlow
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
    CONF_LOCAL_MODE,
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


class SwedishCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    data: dict[str, Any]
    config_entry: ConfigEntry | None = None

    def __init__(self):
        self.data = {}

    def _get_include_sensor_schema(self) -> vol.Schema:
        if self.config_entry:
            default_includes = self._get_not_excluded_sensors(self.config_entry.data)
        else:
            default_includes = self._get_friendly_name_of_sensors()

        return vol.Schema(
            {
                vol.Optional(CONF_INCLUDE, default=default_includes): selector({
                    "select": {
                        "options": self._get_friendly_name_of_sensors(),
                        "multiple": True
                    }
                })
            }
        )

    def _get_themes_schema(self) -> vol.Schema:
        entry_data = (self.config_entry.data.get(CONF_SPECIAL_THEMES) or {}) if self.config_entry else {}
        return vol.Schema(
            {
                vol.Optional(CONF_DIR, default=entry_data.get(CONF_DIR) or os.path.dirname(__file__)): cv.string,
                vol.Optional(CONF_AUTO_UPDATE, default=entry_data.get(CONF_AUTO_UPDATE) or False): cv.boolean,
            },
        )

    def _get_local_mode_schema(self) -> vol.Schema:
        entry_data = self.config_entry.data if self.config_entry else {}
        return vol.Schema(
            {
                vol.Optional(CONF_LOCAL_MODE, default=entry_data.get(CONF_LOCAL_MODE) or False): cv.boolean
            },
        )

    def _is_local_mode(self) -> bool:
        return self.data.get(CONF_LOCAL_MODE) or False

    @staticmethod
    def _get_not_excluded_sensors(data_map: dict[str, Any]):
        return [SENSOR_TYPES[key].friendly_name for key in SENSOR_TYPES
                if key not in data_map[CONF_EXCLUDE]]

    def _get_calendar_schema(self) -> vol.Schema:
        all_sensors = SwedishCalendarConfigFlow._get_friendly_name_of_sensors()
        entry_data = self.config_entry.data[CONF_CALENDAR] if self.config_entry else {}
        already_included_sensors = [
            SENSOR_TYPES[key].friendly_name
            for key in SENSOR_TYPES
            if key not in self.data[CONF_EXCLUDE] and (self.config_entry is None or key in entry_data.get(CONF_INCLUDE))
        ]

        return vol.Schema(
            {
                vol.Optional(CONF_INCLUDE, default=already_included_sensors): selector({
                    "select": {
                        "options": all_sensors,
                        "multiple": True
                    }
                }),
                vol.Optional(CONF_DAYS_BEFORE_TODAY,
                             default=entry_data.get(CONF_DAYS_BEFORE_TODAY) or 0): cv.positive_int,
                vol.Optional(CONF_DAYS_AFTER_TODAY, default=entry_data.get(CONF_DAYS_AFTER_TODAY) or 0): cv.positive_int
            }
        )

    def _get_cache_schema(self) -> vol.Schema:
        entry_data = self.config_entry.data[CONF_CACHE] if self.config_entry else {}
        default_dir = os.path.join(os.path.dirname(__file__), CONF_DEFAULT_CACHE_DIR)

        return vol.Schema(
            {
                vol.Optional(CONF_ENABLED, default=entry_data.get(CONF_ENABLED) or False): cv.boolean,
                vol.Optional(CONF_DIR, default=entry_data.get(CONF_DIR) or default_dir): cv.string,
                vol.Optional(CONF_RETENTION, default=entry_data.get(CONF_RETENTION) or 7): cv.positive_int,
            },
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if not self.config_entry:  # On a reconfiguration we want an entry, since we are updating it
            self._async_abort_entries_match(match_dict={})

        if user_input is not None:
            excludes = [key for key in SENSOR_TYPES if SENSOR_TYPES[key].friendly_name not in user_input[CONF_INCLUDE]]
            self.data[CONF_EXCLUDE] = excludes
            return await self.async_step_local_mode()

        self.data = {}  # Reset data object
        return self.async_show_form(step_id="user", data_schema=self._get_include_sensor_schema())

    async def async_step_local_mode(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self.data[CONF_LOCAL_MODE] = user_input[CONF_LOCAL_MODE]
            return await self.async_step_special_themes()

        return self.async_show_form(step_id="local_mode", data_schema=self._get_local_mode_schema())

    async def async_step_special_themes(self, user_input: dict[str, Any] | None = None):
        if THEME_DAY in self.data[CONF_EXCLUDE] or self._is_local_mode():
            return await self.async_step_calendar()

        if user_input is not None:
            self.data[CONF_SPECIAL_THEMES] = user_input
            return await self.async_step_calendar()

        return self.async_show_form(step_id="special_themes", data_schema=self._get_themes_schema())

    async def async_step_calendar(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            user_input[CONF_INCLUDE] = [key for key in SENSOR_TYPES
                                        if SENSOR_TYPES[key].friendly_name in user_input[CONF_INCLUDE]]
            self.data[CONF_CALENDAR] = user_input

            return await self.async_step_cache()

        return self.async_show_form(step_id="calendar", data_schema=self._get_calendar_schema())

    async def async_step_cache(self, user_input: dict[str, Any] | None = None):
        if self._is_local_mode():
            user_input = {}
            for key, rule in self._get_cache_schema().schema.items():
                if isinstance(key, Optional) and key.default is not None:
                    user_input[key.schema] = key.default() if callable(key.default) else key.default

            user_input[CONF_ENABLED] = False

        if user_input is not None:
            self.data[CONF_CACHE] = user_input

            if self.config_entry:
                await self.hass.config_entries.async_remove(self.config_entry.entry_id)

            return self.async_create_entry(title=DOMAIN_FRIENDLY_NAME, data=self.data)

        return self.async_show_form(step_id="cache", data_schema=self._get_cache_schema())

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        entries = self.hass.config_entries.async_entries(domain=DOMAIN)

        if len(entries) != 1:
            return self.async_abort(reason=f'Unexpected number of config entries, wanted 1 found {len(entries)}')
        else:
            self.config_entry = entries[0]
            return await self.async_step_user()

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
            CONF_RETENTION: imported_cache_config.get(
                CONF_RETENTION).days if CONF_RETENTION in imported_cache_config else 7,
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
        new_themes_path: str | None = (config.get(CONF_SPECIAL_THEMES) or {}).get(CONF_DIR)

        if deprecated_themes_path:
            if not new_themes_path:
                new_themes_path = deprecated_themes_path
        return new_themes_path

    @staticmethod
    def _get_friendly_name_of_sensors():
        return [SENSOR_TYPES[key].friendly_name
                for key in SENSOR_TYPES]
