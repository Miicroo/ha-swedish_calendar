import asyncio
from datetime import date
from functools import partial
import json
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant

from .types import SpecialThemesConfig, ThemeData
from .utils import DateUtils

_LOGGER = logging.getLogger(__name__)


class ThemeDataProvider:
    def __init__(self, hass, theme_path):
        self._hass = hass
        self._theme_path = theme_path

    async def fetch_data(self, start: date, end: date) -> list[ThemeData]:
        return await self._hass.async_add_executor_job(partial(self._fetch_data, start=start, end=end))

    def _fetch_data(self, start: date, end: date) -> list[ThemeData]:
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
    def __init__(self, hass: HomeAssistant, config: SpecialThemesConfig, session: aiohttp.ClientSession):
        self._hass = hass
        self._config = config
        self._session = session
        self._url = 'https://raw.githubusercontent.com/Miicroo/ha-swedish_calendar/master/custom_components' \
                    '/swedish_calendar/specialThemes.json'

    def can_update(self):
        return self._config.auto_update and self._config.path is not None

    async def update(self):
        new_data = await self._download()
        if new_data:
            await self._hass.async_add_executor_job(partial(self._write_update, new_data=new_data))

    def _write_update(self, new_data):
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
