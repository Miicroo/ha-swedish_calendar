import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import aiohttp
import async_timeout
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN_FRIENDLY_NAME
from .types import ApiData, ThemeData, SwedishCalendar, SpecialThemesConfig, CalendarConfig
from .utils import DateUtils

_LOGGER = logging.getLogger(__name__)


class CalendarDataCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, special_themes_config: SpecialThemesConfig, calendar_config: CalendarConfig):
        """Initialize the data object."""
        self.hass = hass
        self._themes_path: str = special_themes_config.path
        self._cache: Dict[date, SwedishCalendar] = {}
        self._theme_provider = ThemeDataProvider(special_themes_config.path)
        self._api_data_provider = ApiDataProvider(async_get_clientsession(hass))
        self._fetch_days_before_today = calendar_config.days_before_today
        self._fetch_days_after_today = calendar_config.days_after_today

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN_FRIENDLY_NAME,
            update_interval=timedelta(seconds=DateUtils.seconds_until_midnight()),
            update_method=self.update_data,
        )

    @callback
    def _schedule_refresh(self) -> None:
        _LOGGER.debug("Scheduling refresh in %s at %s", self.update_interval, (datetime.now()+self.update_interval))
        super()._schedule_refresh()

    async def update_data(self) -> Dict[date, SwedishCalendar]:
        _LOGGER.debug("Fetching new data")
        if date.today() not in self._cache:
            try:
                self._cache = await self._get_calendars()
            except Exception as err:
                _LOGGER.warning("Failed to fetch swedish calendar: %s", err)

        # Recalculate update interval in case of restart
        self.update_interval = timedelta(seconds=DateUtils.seconds_until_midnight())

        return self._cache or {}

    async def _get_calendars(self) -> Dict[date, SwedishCalendar]:
        start_date = date.today() - timedelta(days=self._fetch_days_before_today)
        end_date = date.today() + timedelta(days=self._fetch_days_after_today)

        themes = []
        if self._themes_path:
            themes = await self._theme_provider.fetch_data(start_date, end_date)
        swedish_dates = await self._api_data_provider.fetch_data(start_date, end_date)

        return CalendarDataCoordinator._merge(swedish_dates, themes)

    @staticmethod
    def _merge(swedish_dates: List[ApiData], themes: List[ThemeData]) -> Dict[date, SwedishCalendar]:
        all_calendars: Dict[date, SwedishCalendar] = {}
        # Add all themes into the dict
        for theme_data in themes:
            all_calendars[date.fromisoformat(theme_data.date)] = SwedishCalendar(None, theme_data)

        # Add all api data, merging with themes for dates where themes are present
        for api_data in swedish_dates:
            key = date.fromisoformat(api_data.date)
            if key in all_calendars:
                all_calendars[key]._api_data = api_data
            else:
                all_calendars[key] = SwedishCalendar(api_data, None)

        return all_calendars


class ApiDataProvider:
    def __init__(self, session: aiohttp.ClientSession):
        self._base_url: str = 'https://sholiday.faboul.se/dagar/v2.1/'
        self._session = session

    async def fetch_data(self, start: date, end: date) -> List[ApiData]:
        urls: List[str] = self._get_urls(start, end)
        all_api_data = []
        for url in urls:
            try:
                json_data = await self._get_json_from_url(url)
                current_api_data = self._to_api_data(json_data, start, end)
                all_api_data.extend(current_api_data)
            except (asyncio.TimeoutError, aiohttp.ClientError) as err:
                _LOGGER.warning('Error when calling: %s, %s', url, err)
            except json.JSONDecodeError as err:
                _LOGGER.error("Invalid json, error: %s", err)

        return all_api_data

    def _get_urls(self, start: date, end: date) -> List[str]:
        return [f'{self._base_url}{date_pattern}' for date_pattern in
                ApiDataProvider._get_url_patterns_for_date_range(start, end)]

    @staticmethod
    def _get_url_patterns_for_date_range(start: date, end: date) -> List[str]:
        if start.year != end.year:
            # Different years -> get all days for each year
            return [str(year) for year in range(start.year, end.year + 1)]
        elif start.month != end.month:
            # Different months -> get all days for each month
            return [f'{start.year}/{month}' for month in range(start.month, end.month + 1)]
        elif start.day != end.day:
            # Different days -> get all days for that month
            return [f'{start.year}/{start.month}']
        else:
            # Same day -> get the day
            return [f'{start.year}/{start.month}/{start.day}']

    async def _get_json_from_url(self, url) -> Dict[str, Any]:
        with async_timeout.timeout(10):
            resp = await self._session.get(url)

        if resp.status != 200:
            raise aiohttp.ClientError(f'Failed to fetch data for: {url}, response code: {resp.status}')
        else:
            response_data = await resp.text()
            data: Dict[str, Any] = json.loads(response_data)
            return data

    @staticmethod
    def _to_api_data(json_response: Dict[str, Any], start: date, end: date) -> List[ApiData]:
        all_data = [ApiData(data_per_date) for data_per_date in json_response["dagar"]]
        wanted_data = list(filter(lambda api_data: DateUtils.in_range(api_data.date, start, end), all_data))
        return wanted_data


class ThemeDataProvider:
    def __init__(self, theme_path):
        self._theme_path = theme_path

    async def fetch_data(self, start: date, end: date) -> List[ThemeData]:
        theme_dates = []
        try:
            with open(self._theme_path, 'r') as data_file:
                data = json.load(data_file)
            theme_dates = ThemeDataProvider._map_to_theme_dates(data, start, end)
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid json in special themes json, path: %s, %s", self._theme_path, err)

        return theme_dates

    @staticmethod
    def _map_to_theme_dates(json_data: Dict[str, Any], start: date, end: date) -> List[ThemeData]:
        special_themes = json_data['themeDays']
        themes = []

        for day in DateUtils.range(start, end):
            date_str = day.strftime('%Y%m%d')
            iso_date_str = day.strftime('%Y-%m-%d')

            if date_str in special_themes:
                theme_list = list(map(lambda x: x['event'], special_themes[date_str]))
                themes.append(ThemeData(iso_date_str, theme_list))
        return themes
