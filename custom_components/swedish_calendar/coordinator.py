from datetime import date, datetime, timedelta
import logging

from custom_components.swedish_calendar.local.themes.theme_data_local import (
    LocalThemeDataProvider,
    LocalThemeDataUpdater,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api_data import ApiDataProvider
from .const import BRIDGE_DAY, CONF_EXCLUDE, DOMAIN_FRIENDLY_NAME, THEME_DAY
from .local.api_data_local import LocalApiDataProvider
from .theme_data import ThemeDataProvider, ThemeDataUpdater
from .types import (
    ApiData,
    CacheConfig,
    CalendarConfig,
    SpecialThemesConfig,
    SwedishCalendar,
    ThemeData,
)
from .utils import DateUtils

_LOGGER = logging.getLogger(__name__)


class CalendarDataCoordinator(DataUpdateCoordinator):

    def __init__(self,
                 hass: HomeAssistant,
                 special_themes_config: SpecialThemesConfig,
                 calendar_config: CalendarConfig,
                 cache_config: CacheConfig,
                 is_local_mode: bool,
                 conf: dict):
        """Initialize the data object."""
        self.hass = hass
        self._themes_enabled: str = THEME_DAY not in (conf[CONF_EXCLUDE] or [])
        self._bridge_day_enabled = BRIDGE_DAY not in (conf[CONF_EXCLUDE] or [])
        self._work_free_days: dict[date, bool | None] = {}
        self._cache: dict[date, SwedishCalendar] = {}
        self._fetch_days_before_today = calendar_config.days_before_today
        self._fetch_days_after_today = calendar_config.days_after_today
        self._first_update = True  # Keep track of first update so that we keep boot times down

        if is_local_mode:
            self._api_data_provider = LocalApiDataProvider(hass=hass)
            self._theme_data_updater = LocalThemeDataUpdater()
            self._theme_provider = LocalThemeDataProvider(hass=hass)
        else:
            session = async_get_clientsession(hass)
            self._api_data_provider = ApiDataProvider(hass=hass, session=session, cache_config=cache_config)
            self._theme_data_updater = ThemeDataUpdater(hass=hass, config=special_themes_config, session=session)
            self._theme_provider = ThemeDataProvider(hass=hass, theme_path=special_themes_config.path)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN_FRIENDLY_NAME,
            update_interval=timedelta(seconds=DateUtils.seconds_until_midnight()),
            update_method=self.update_data,
        )

    @callback
    def _schedule_refresh(self) -> None:
        _LOGGER.debug("Scheduling refresh in %s at %s", self.update_interval, (datetime.now() + self.update_interval))
        super()._schedule_refresh()

    @property
    def bridge_day(self) -> bool | None:
        """A working day immediately between two work-free calendar days."""
        today = dt_util.now().date()
        work_free = self._work_free_days.get(today)
        if work_free is None:
            return None
        if work_free:
            return False
        yesterday = self._work_free_days.get(today - timedelta(days=1))
        tomorrow = self._work_free_days.get(today + timedelta(days=1))
        if yesterday is None or tomorrow is None:
            return None
        return yesterday and tomorrow

    async def update_data(self) -> dict[date, SwedishCalendar]:
        _LOGGER.debug("Fetching new data")

        if self._theme_data_updater.can_update() and not self._first_update:
            await self._theme_data_updater.update()

        today = dt_util.now().date()
        start = today - timedelta(days=self._fetch_days_before_today)
        end = today + timedelta(days=self._fetch_days_after_today)
        if (not self._is_cached(start) or not self._is_cached(end)
                or (self._bridge_day_enabled and self.bridge_day is None)):
            try:
                self._cache = await self._get_calendars(start, end, today)
            except Exception as err:
                self._work_free_days.clear()
                _LOGGER.warning("Failed to fetch swedish calendar: %s", err)

        # Recalculate update interval in case of restart
        self.update_interval = timedelta(seconds=DateUtils.seconds_until_midnight())
        self._first_update = False  # First update (on boot) considered successful

        return self._cache or {}

    def _is_cached(self, day: date) -> bool:
        # Theme data covers whole years, so a date can be in the cache without its api data
        calendar = self._cache.get(day)
        return calendar is not None and calendar.get_value_by_attribute('date') is not None

    async def _get_calendars(self, start: date, end: date, today: date) -> dict[date, SwedishCalendar]:
        themes = []
        if self._themes_enabled:
            themes = await self._theme_provider.fetch_data(start, end)
        api_start, api_end = start, end
        if self._bridge_day_enabled:
            api_start = min(start, today - timedelta(days=1))
            api_end = max(end, today + timedelta(days=1))

        swedish_dates = await self._api_data_provider.fetch_data(api_start, api_end)
        if self._bridge_day_enabled:
            self._work_free_days = {date.fromisoformat(row.date): row.work_free_day for row in swedish_dates}
            # The extra dates supply the sensor, not additional calendar events.
            swedish_dates = [row for row in swedish_dates if DateUtils.in_range(row.date, start, end)]

        return CalendarDataCoordinator._merge(swedish_dates, themes)

    @staticmethod
    def _merge(swedish_dates: list[ApiData], themes: list[ThemeData]) -> dict[date, SwedishCalendar]:
        all_calendars: dict[date, SwedishCalendar] = {}
        # Add all themes into the dict
        for theme_data in themes:
            all_calendars[date.fromisoformat(theme_data.date)] = SwedishCalendar.from_themes(theme_data)

        # Add all api data, merging with themes for dates where themes are present
        for api_data in swedish_dates:
            key = date.fromisoformat(api_data.date)
            if key in all_calendars:
                all_calendars[key].with_api_data(api_data)
            else:
                all_calendars[key] = SwedishCalendar.from_api_data(api_data)

        return all_calendars
