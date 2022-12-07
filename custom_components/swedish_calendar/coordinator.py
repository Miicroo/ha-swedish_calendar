from datetime import date, datetime, timedelta
import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api_data import ApiDataProvider
from .const import DOMAIN_FRIENDLY_NAME
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
                 cache_config: CacheConfig):
        """Initialize the data object."""
        self.hass = hass
        self._themes_path: str = special_themes_config.path
        self._cache: dict[date, SwedishCalendar] = {}
        self._fetch_days_before_today = calendar_config.days_before_today
        self._fetch_days_after_today = calendar_config.days_after_today
        self._first_update = True  # Keep track of first update so that we keep boot times down

        session = async_get_clientsession(hass)
        self._api_data_provider = ApiDataProvider(session=session, cache_config=cache_config)
        self._theme_data_updater = ThemeDataUpdater(config=special_themes_config, session=session)
        self._theme_provider = ThemeDataProvider(theme_path=special_themes_config.path)

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

    async def update_data(self) -> dict[date, SwedishCalendar]:
        _LOGGER.debug("Fetching new data")

        if self._theme_data_updater.can_update() and not self._first_update:
            await self._theme_data_updater.update()

        if self._get_start() not in self._cache or self._get_end() not in self._cache:
            try:
                self._cache = await self._get_calendars()
            except Exception as err:
                _LOGGER.warning("Failed to fetch swedish calendar: %s", err)

        # Recalculate update interval in case of restart
        self.update_interval = timedelta(seconds=DateUtils.seconds_until_midnight())
        self._first_update = False  # First update (on boot) considered successful

        return self._cache or {}

    def _get_start(self):
        return date.today() - timedelta(days=self._fetch_days_before_today)

    def _get_end(self):
        return date.today() + timedelta(days=self._fetch_days_after_today)

    async def _get_calendars(self) -> dict[date, SwedishCalendar]:
        start_date = self._get_start()
        end_date = self._get_end()

        themes = []
        if self._themes_path:
            themes = await self._theme_provider.fetch_data(start_date, end_date)
        swedish_dates = await self._api_data_provider.fetch_data(start_date, end_date)

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
