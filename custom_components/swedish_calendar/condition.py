"""Calendar day conditions without changing the existing sensor states."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConditionErrorMessage
from homeassistant.helpers import condition as ha_condition
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .types import SwedishCalendar

CONF_DAY = 'day'
ANY_DAY = 'any'

# Local mode reports some eves in the holiday field, and moves all eve names
# there when a holiday and an eve coincide. Keep those source values intact.
_HOLIDAY_EVE_NAMES = frozenset(name.casefold() for name in (
    'Trettondagsafton',
    'Skärtorsdagen',
    'Påskafton',
    'Valborgsmässoafton',
    'Pingstafton',
    'Midsommarafton',
    'Allhelgonaafton',
    'Julafton',
    'Nyårsafton',
))

CONDITIONS: dict[str, type[ha_condition.Condition]] = {}

# Older supported Home Assistant versions have no modern condition checker.
# They keep the existing entities and simply do not offer these UI conditions.
if hasattr(ha_condition, 'Condition') and hasattr(ha_condition.Condition, '_async_check'):
    from homeassistant.const import CONF_OPTIONS

    _DAY_SCHEMA = vol.Schema({
        vol.Required(CONF_OPTIONS, default=dict): {
            vol.Optional(CONF_DAY): vol.Any(
                None, vol.All(str, str.strip, vol.Length(min=1, max=255))
            ),
        },
    })

    class _CalendarDayCondition(ha_condition.Condition):
        """Match a day in the current loaded integration's calendar data."""

        key: str
        attribute: str

        @classmethod
        async def async_validate_config(cls, hass: HomeAssistant, config: ConfigType) -> ConfigType:
            """Validate the selected day, including names supplied by the API."""
            validated = _DAY_SCHEMA(config)
            if validated[CONF_OPTIONS].get(CONF_DAY) is None:
                validated[CONF_OPTIONS].pop(CONF_DAY, None)
            return validated

        def __init__(self, hass: HomeAssistant, config: ha_condition.ConditionConfig) -> None:
            super().__init__(hass, config)
            assert config.options is not None
            self._day = config.options.get(CONF_DAY, ANY_DAY).casefold()

        async def _async_setup(self) -> None:
            """Load the error message using Home Assistant's translation cache."""
            translations = await async_get_translations(
                self._hass, self._hass.config.language, 'exceptions', {DOMAIN}
            )
            self._unavailable_message = translations[
                f'component.{DOMAIN}.exceptions.calendar_data_unavailable.message'
            ]

        def _unavailable(self) -> ConditionErrorMessage:
            """Keep missing data an error, including inside a NOT condition."""
            return ConditionErrorMessage(f'{DOMAIN}.{self.key}', self._unavailable_message)

        def _today_calendar(self) -> SwedishCalendar:
            """Read the current coordinator each time so reloads cannot leave stale data."""
            entries = [entry for entry in self._hass.config_entries.async_entries(DOMAIN)
                       if entry.state is ConfigEntryState.LOADED]
            if len(entries) != 1:
                raise self._unavailable()

            runtime = self._hass.data.get(DOMAIN, {}).get(entries[0].entry_id, {})
            coordinator = runtime.get('coordinator')
            if coordinator is None or not coordinator.last_update_success or not coordinator.data:
                raise self._unavailable()

            today = dt_util.now().date()
            calendar = coordinator.data.get(today)
            if not isinstance(calendar, SwedishCalendar) or calendar.get_value_by_attribute('date') != today.isoformat():
                raise self._unavailable()
            return calendar

        def _names(self, calendar: SwedishCalendar, attribute: str) -> set[str]:
            """Compare complete comma-separated names, never substrings."""
            value = calendar.get_value_by_attribute(attribute)
            if value is None:
                return set()
            if not isinstance(value, str):
                raise self._unavailable()
            names = {name.strip().casefold() for name in value.split(',') if name.strip()}
            if names & {STATE_UNKNOWN, STATE_UNAVAILABLE}:
                raise self._unavailable()
            return names

        def _day_names(self, calendar: SwedishCalendar) -> set[str]:
            return self._names(calendar, self.attribute)

        def _async_check(self, **kwargs) -> bool:
            """Evaluate without network access or changing entities."""
            names = self._day_names(self._today_calendar())
            return bool(names) if self._day == ANY_DAY else self._day in names

    class _HolidayCondition(_CalendarDayCondition):
        """Match the holiday names reported by the data source."""

        key = 'is_holiday'
        attribute = 'holiday'

    class _HolidayEveCondition(_CalendarDayCondition):
        """Match eves, including recognized eves reported as holidays."""

        key = 'is_holiday_eve'
        attribute = 'eve'

        def _day_names(self, calendar: SwedishCalendar) -> set[str]:
            return self._names(calendar, 'eve') | (
                self._names(calendar, 'holiday') & _HOLIDAY_EVE_NAMES
            )

    class _FlagDayCondition(_CalendarDayCondition):
        """Match the day's individual reasons for flagging."""

        key = 'is_flag_day'
        attribute = 'reason_for_flagging'

    CONDITIONS = {
        'is_holiday': _HolidayCondition,
        'is_holiday_eve': _HolidayEveCondition,
        'is_flag_day': _FlagDayCondition,
    }


async def async_get_conditions(hass: HomeAssistant) -> dict[str, type[ha_condition.Condition]]:
    """Return the supported calendar day conditions."""
    return CONDITIONS
