import asyncio
from collections import deque
from datetime import date, datetime, timedelta, timezone
from functools import partial
import hashlib
import json
import logging
import os
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant

from .types import ApiData, CacheConfig
from .utils import DateUtils

_LOGGER = logging.getLogger(__name__)


class ApiDataProvider:
    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession, cache_config: CacheConfig):
        self._base_url: str = 'https://sholiday.faboul.se/dagar/v2.1/'
        self._session = session
        self._cache = ApiDataCache(hass, cache_config)

    async def fetch_data(self, start: date, end: date) -> list[ApiData]:
        urls = deque(self._get_urls(start, end))
        urls_retries = {url: 0 for url in urls}

        max_tries = 3
        all_api_data = []
        while len(urls) > 0:
            url = urls.popleft()
            tries = urls_retries[url]+1

            if tries > max_tries:
                _LOGGER.info(f"Ignoring url {url}, exceeded max tries")
                continue

            try:
                json_data = await self._get_json_from_url(url, tries*10)
                current_api_data = self._to_api_data(json_data, start, end)
                all_api_data.extend(current_api_data)
            except aiohttp.ClientError as err:
                _LOGGER.warning('Error when calling: %s, %s', url, str(err))
            except asyncio.TimeoutError as err:
                _LOGGER.warning('Timeout when calling: %s', url)
                # Retry url
                urls_retries[url] = tries
                urls.append(url)
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

    async def _get_json_from_url(self, url, timeout) -> dict[str, Any]:
        if self._cache.has_data_for(url):
            _LOGGER.debug("Using cached version of url: %s", url)
            data = await self._cache.get(url)
        else:
            data = await self._get_data_online(url, timeout)
            await self._cache.update(url, data)

        return data

    async def _get_data_online(self, url, timeout):
        _LOGGER.debug(f'Calling {url} with timeout {timeout} seconds')
        with async_timeout.timeout(timeout):
            resp = await self._session.get(url)

        if resp.status != 200:
            raise aiohttp.ClientError(f'Failed to fetch data for: {url}, response code: {resp.status}')
        else:
            response_data = await resp.text()
            data: dict[str, Any] = json.loads(response_data)
            return data

    @staticmethod
    def _to_api_data(json_response: dict[str, Any], start: date, end: date) -> list[ApiData]:
        all_data = [ApiData.from_json(data_per_date) for data_per_date in json_response["dagar"]]
        wanted_data = list(filter(lambda api_data: DateUtils.in_range(api_data.date, start, end), all_data))
        return wanted_data


class ApiDataCache:
    def __init__(self, hass: HomeAssistant, cache_config: CacheConfig):
        self._hass = hass
        self.config = cache_config

    def has_data_for(self, url: str) -> bool:
        return self.config.enabled and \
               os.path.exists(self._url_to_path(url)) and \
               self._cache_age(url) <= self.config.retention

    def _url_to_path(self, url: str) -> str:
        hashed_name = hashlib.md5(url.encode())
        filename = f'{hashed_name.hexdigest()}.json'
        return os.path.join(self.config.cache_dir, filename)

    def _cache_age(self, url) -> timedelta:
        path = self._url_to_path(url)
        modified_time = os.path.getmtime(path)
        cache_in_utc = datetime.fromtimestamp(modified_time, tz=timezone.utc)
        now_in_utc = datetime.now().astimezone(tz=timezone.utc)
        return now_in_utc - cache_in_utc

    async def get(self, url) -> dict[str, Any] | None:
        return await self._hass.async_add_executor_job(partial(self._get, url=url))

    def _get(self, url) -> dict[str, Any] | None:
        path = self._url_to_path(url)
        data = None
        with open(path) as cached_file:
            try:
                data = json.load(cached_file)
            except json.JSONDecodeError as err:
                _LOGGER.error("Invalid json in cached file: %s, removing. Error: %s", path, err)
                os.remove(path)

        return data

    async def update(self, url, data: dict[str, Any]) -> None:
        return await self._hass.async_add_executor_job(partial(self._update, url=url, data=data))

    def _update(self, url, data: dict[str, Any]) -> None:
        if self.config.enabled:
            path = self._url_to_path(url)
            _LOGGER.debug("Caching %s, saving to %s", url, path)
            self._assert_path_directories_exist()
            with open(path, 'w') as cache_file:
                cache_file.write(json.dumps(data))
                _LOGGER.debug("%s updated", path)

    def _assert_path_directories_exist(self):
        if not os.path.exists(self.config.cache_dir):
            _LOGGER.debug("%s does not exist, creating", self.config.cache_dir)
            os.makedirs(self.config.cache_dir, exist_ok=True)
