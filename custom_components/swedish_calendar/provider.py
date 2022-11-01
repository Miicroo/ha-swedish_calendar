import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List

import aiohttp
import async_timeout
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .types import ApiData, ThemeData, SwedishCalendar
from .utils import DateUtils

_LOGGER = logging.getLogger(__name__)


class CalendarDataCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, themes_path):
        """Initialize the data object."""
        self.hass = hass
        self._themes_path: str = themes_path
        self._cache: Dict[date, SwedishCalendar] = {}
        self._theme_provider = ThemeDataProvider(themes_path)
        self._api_data_provider = ApiDataProvider(async_get_clientsession(hass))

        super().__init__(
            hass,
            _LOGGER,
            name="Swedish calendar update",
            update_interval=timedelta(seconds=3600),
            update_method=self.fetching_data,
        )

    async def fetching_data(self, *_) -> SwedishCalendar:
        if date.today() not in self._cache:
            try:
                self._cache[date.today()] = await self._get_calendar()
            except Exception as err:
                _LOGGER.warning("Failed to fetch swedish calendar: %s", err)

        return self._cache[date.today()]

    async def _get_calendar(self) -> SwedishCalendar:
        themes = []
        if self._themes_path:
            themes = await self._theme_provider.fetch_data_for_today()
        swedish_dates = await self._api_data_provider.fetch_data_for_today()

        theme: ThemeData = themes[0] if len(themes) > 0 else None
        swedish_date: ApiData = swedish_dates[0] if len(swedish_dates) > 0 else None

        return SwedishCalendar(swedish_date, theme)


class ApiDataProvider:
    def __init__(self, session: aiohttp.ClientSession):
        self._base_url: str = 'https://sholiday.faboul.se/dagar/v2.1/'
        self._session = session

    async def fetch_data_for_today(self) -> List[ApiData]:
        return await self.fetch_data(date.today(), date.today())

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

    async def fetch_data_for_today(self) -> List[ThemeData]:
        return await self.fetch_data(datetime.today(), datetime.today())

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
