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


class SwedishCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    data: dict[str, Any]
    is_reconfiguration: bool | None = None

    def _get_include_sensor_schema(self, default_includes: list[str]) -> vol.Schema:
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

    @staticmethod
    def _get_themes_schema(default_dir: str = os.path.dirname(__file__),
                           default_auto_update: bool = False) -> vol.Schema:
        return vol.Schema(
            {
                vol.Optional(CONF_DIR, default=default_dir): cv.string,
                vol.Optional(CONF_AUTO_UPDATE, default=default_auto_update): cv.boolean,
            },
        )

    @staticmethod
    def _get_not_excluded_sensors(data_map: dict[str, Any]):
        return [SENSOR_TYPES[key].friendly_name for key in SENSOR_TYPES
                if key not in data_map[CONF_EXCLUDE]]

    def _get_calendar_schema(self,
                             default_days_before_today: int = 0,
                             default_days_after_today: int = 0,
                             ) -> vol.Schema:
        all_sensors = SwedishCalendarConfigFlow._get_friendly_name_of_sensors()
        already_included_sensors = self._get_not_excluded_sensors(self.data)

        return vol.Schema(
            {
                vol.Optional(CONF_INCLUDE, default=already_included_sensors): selector({
                    "select": {
                        "options": all_sensors,
                        "multiple": True
                    }
                }),
                vol.Optional(CONF_DAYS_BEFORE_TODAY, default=default_days_before_today): cv.positive_int,
                vol.Optional(CONF_DAYS_AFTER_TODAY, default=default_days_after_today): cv.positive_int,
            }
        )

    @staticmethod
    def _get_cache_schema(default_enabled: bool = False,
                          default_dir: str = os.path.join(os.path.dirname(__file__), CONF_DEFAULT_CACHE_DIR),
                          default_retention_days: int = 7) -> vol.Schema:
        return vol.Schema(
            {
                vol.Optional(CONF_ENABLED, default=default_enabled): cv.boolean,
                vol.Optional(CONF_DIR, default=default_dir): cv.string,
                vol.Optional(CONF_RETENTION, default=default_retention_days): cv.positive_int,
            },
        )

    def _get_existing_config_entry(self):
        entries = self.hass.config_entries.async_entries(domain=DOMAIN)
        _LOGGER.warning(entries)
        if len(entries) == 0:
            return None
        elif len(entries) == 1:
            return entries[0]
        else:
            raise Exception('Multiple entries found, aborting')

    def _get_existing_config_entry_data(self):
        entry = self._get_existing_config_entry()
        return entry.data if entry is not None else None

    async def async_step_user(self, user_input: dict[str, Any] | None = None, reconfigure: bool = False):
        if self.is_reconfiguration is None:  # Value not set yet
            self.is_reconfiguration = reconfigure

        if not self.is_reconfiguration:  # On a reconfiguration we want an entry, since we are updating it
            self._async_abort_entries_match(match_dict={})

        if user_input is not None:
            excludes = [key for key in SENSOR_TYPES if SENSOR_TYPES[key].friendly_name not in user_input[CONF_INCLUDE]]
            self.data[CONF_EXCLUDE] = excludes
            return await self.async_step_special_themes()

        self.data = {}
        default_includes = self._get_not_excluded_sensors(self._get_existing_config_entry_data()) \
            if self.is_reconfiguration else self._get_friendly_name_of_sensors()  # reconfig -> get from entry, else all

        sensor_schema = self._get_include_sensor_schema(default_includes=default_includes)

        return self.async_show_form(step_id="user", data_schema=sensor_schema)

    async def async_step_special_themes(self, user_input: dict[str, Any] | None = None):
        if THEME_DAY in self.data[CONF_EXCLUDE]:
            return await self.async_step_calendar()

        if user_input is not None:
            self.data[CONF_SPECIAL_THEMES] = user_input
            return await self.async_step_calendar()

        if self.is_reconfiguration:
            entry = self._get_existing_config_entry_data()[CONF_SPECIAL_THEMES]
            schema = self._get_themes_schema(default_dir=entry[CONF_DIR], default_auto_update=entry[CONF_AUTO_UPDATE])
        else:
            schema = self._get_themes_schema()

        return self.async_show_form(step_id="special_themes", data_schema=schema)

    async def async_step_calendar(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            user_input[CONF_INCLUDE] = [key for key in SENSOR_TYPES
                                        if SENSOR_TYPES[key].friendly_name in user_input[CONF_INCLUDE]]
            self.data[CONF_CALENDAR] = user_input

            return await self.async_step_cache()

        if self.is_reconfiguration:
            entry = self._get_existing_config_entry_data()[CONF_CALENDAR]
            schema = self._get_calendar_schema(default_days_before_today=entry[CONF_DAYS_BEFORE_TODAY],
                                               default_days_after_today=entry[CONF_DAYS_AFTER_TODAY])
        else:
            schema = self._get_calendar_schema()

        return self.async_show_form(step_id="calendar", data_schema=schema)

    async def async_step_cache(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self.data[CONF_CACHE] = user_input

            if self.is_reconfiguration:
                await self.hass.config_entries.async_remove(self._get_existing_config_entry().entry_id)

            return self.async_create_entry(title=DOMAIN_FRIENDLY_NAME, data=self.data)

        if self.is_reconfiguration:
            entry = self._get_existing_config_entry_data()[CONF_CACHE]
            schema = self._get_cache_schema(default_enabled=entry[CONF_ENABLED],
                                            default_dir=entry[CONF_DIR],
                                            default_retention_days=entry[CONF_RETENTION])
        else:
            schema = self._get_cache_schema()

        return self.async_show_form(step_id="cache", data_schema=schema)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_user(reconfigure=True)

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
        new_themes_path: str | None = config[CONF_SPECIAL_THEMES][CONF_DIR]

        if deprecated_themes_path:
            if not new_themes_path:
                new_themes_path = deprecated_themes_path
        return new_themes_path

    @staticmethod
    def _get_friendly_name_of_sensors():
        return [SENSOR_TYPES[key].friendly_name
                for key in SENSOR_TYPES]
