import asyncio
from datetime import date, datetime, timedelta
import json
import logging
import os
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN_FRIENDLY_NAME
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


class ApiDataProvider:
    def __init__(self, session: aiohttp.ClientSession, cache_config: CacheConfig):
        self._base_url: str = 'https://sholiday.faboul.se/dagar/v2.1/'
        self._session = session
        self._cache = ApiDataCache(cache_config)

    async def fetch_data(self, start: date, end: date) -> list[ApiData]:
        urls: list[str] = self._get_urls(start, end)
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

    def _get_urls(self, start: date, end: date) -> list[str]:
        return [f'{self._base_url}{date_pattern}' for date_pattern in
                ApiDataProvider._get_url_patterns_for_date_range(start, end)]

    @staticmethod
    def _get_url_patterns_for_date_range(start: date, end: date) -> list[str]:
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

    async def _get_json_from_url(self, url) -> dict[str, Any]:
        if self._cache.has_data_for(url):
            data = self._cache.get(url)
        else:
            data = await self._get_data_online(url)
            self._cache.update(url, data)

        return data

    async def _get_data_online(self, url):
        with async_timeout.timeout(10):
            resp = await self._session.get(url)

        if resp.status != 200:
            raise aiohttp.ClientError(f'Failed to fetch data for: {url}, response code: {resp.status}')
        else:
            response_data = await resp.text()
            data: dict[str, Any] = json.loads(response_data)
            return data

    @staticmethod
    def _to_api_data(json_response: dict[str, Any], start: date, end: date) -> list[ApiData]:
        all_data = [ApiData(data_per_date) for data_per_date in json_response["dagar"]]
        wanted_data = list(filter(lambda api_data: DateUtils.in_range(api_data.date, start, end), all_data))
        return wanted_data


class ApiDataCache:
    def __init__(self, cache_config: CacheConfig):
        self.config = cache_config

    def has_data_for(self, url: str) -> bool:
        return self.config.enabled and os.path.exists(self._url_to_path(url))

    def _url_to_path(self, url: str) -> str:
        filename = f'{hash(url)}.json'
        return os.path.join(self.config.cache_dir, filename)

    def get(self, url) -> dict[str, Any] | None:
        path = self._url_to_path(url)
        data = None
        with open(path) as cached_file:
            try:
                data = json.load(cached_file)
            except json.JSONDecodeError as err:
                _LOGGER.error("Invalid json in cached file: %s, removing. Error: %s", path, err)
                os.remove(path)

        return data

    def update(self, url, data: dict[str, Any]) -> None:
        if self.config.enabled:
            path = self._url_to_path(url)
            self._assert_path_directories_exist()
            with open(path, 'w') as cache_file:
                cache_file.write(json.dumps(data))

    def _assert_path_directories_exist(self):
        if not os.path.exists(self.config.cache_dir):
            os.makedirs(self.config.cache_dir)


class ThemeDataProvider:
    def __init__(self, theme_path):
        self._theme_path = theme_path

    async def fetch_data(self, start: date, end: date) -> list[ThemeData]:
        theme_dates = []
        try:
            with open(self._theme_path) as data_file:
                data = json.load(data_file)
            theme_dates = ThemeDataProvider._map_to_theme_dates(data, start, end)
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid json in special themes json, path: %s, %s", self._theme_path, err)

        return theme_dates

    @staticmethod
    def _map_to_theme_dates(json_data: dict[str, Any], start: date, end: date) -> list[ThemeData]:
        special_themes = json_data['themeDays']
        themes = []

        for day in DateUtils.range(start, end):
            date_str = day.strftime('%Y%m%d')
            iso_date_str = day.strftime('%Y-%m-%d')

            if date_str in special_themes:
                theme_list = list(map(lambda x: x['event'], special_themes[date_str]))
                themes.append(ThemeData(iso_date_str, theme_list))
        return themes


class ThemeDataUpdater:
    def __init__(self, config: SpecialThemesConfig, session: aiohttp.ClientSession):
        self._config = config
        self._session = session
        self._url = 'https://raw.githubusercontent.com/Miicroo/ha-swedish_calendar/master/custom_components' \
                    '/swedish_calendar/specialThemes.json'

    def can_update(self):
        return self._config.auto_update and self._config.path is not None

    async def update(self):
        new_data = await self._download()
        if new_data:
            with open(self._config.path, 'w') as themes_file:
                themes_file.write(new_data)
                _LOGGER.info('Themes updated with latest json')

    async def _download(self) -> str | None:
        _LOGGER.debug("Downloading latest themes")
        response_data: str | None = None
        try:
            with async_timeout.timeout(10):
                resp = await self._session.get(self._url)

            if resp.status != 200:
                raise aiohttp.ClientError(f'Failed to fetch data for: {self._url}, response code: {resp.status}')
            else:
                response_data = await resp.text()
                json.loads(response_data)  # Test that data can be loaded as json
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.warning('Error when calling: %s, %s', self._url, err)
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid json, error: %s", err)

        return response_data
