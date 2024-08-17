"""Tests for ApiData."""
from datetime import datetime, timedelta, timezone
import time
from unittest import mock
from unittest.mock import call

from custom_components.swedish_calendar.api_data import ApiDataCache
from custom_components.swedish_calendar.types import CacheConfig


def test_api_data_cache_has_data_for_returns_false_if_cache_is_disabled(mocker, hass):
    """Disabled cache -> has_data_for returns False."""
    config = _cache_is_disabled()  # This triggers has_data_for -> False
    api_cache = ApiDataCache(hass=hass, cache_config=config)

    _cache_is_not_old(mocker)
    _url_is_cached(mocker)

    assert api_cache.has_data_for("https://whatever") is False


def test_api_data_cache_has_data_for_returns_false_if_cache_file_does_not_exist(
    mocker, hass
):
    """Cache (file) does not exist -> has_data_for returns False."""
    config = _cache_is_enabled()
    api_cache = ApiDataCache(hass=hass, cache_config=config)

    _cache_is_not_old(mocker)
    _url_is_not_cached(mocker)  # This triggers has_data_for -> False

    assert api_cache.has_data_for("https://whatever") is False


def test_api_data_cache_has_data_for_returns_false_if_cache_file_is_old(mocker, hass):
    """Cache is too old -> has_data_for returns False."""
    config = _cache_is_enabled()
    api_cache = ApiDataCache(hass=hass, cache_config=config)

    _cache_is_old(mocker)  # This triggers has_data_for -> False
    _url_is_cached(mocker)

    assert api_cache.has_data_for("https://whatever") is False


def test_api_data_cache_has_data_for_returns_true_if_all_conditions_are_true(
    mocker, hass
):
    """Cache enabled + cached file exists + cache not too old -> has_data_for returns True."""
    config = _cache_is_enabled()
    api_cache = ApiDataCache(hass=hass, cache_config=config)

    _cache_is_not_old(mocker)
    _url_is_cached(mocker)

    assert api_cache.has_data_for("https://whatever") is True


async def test_api_data_cache_get_removes_file_on_json_decode_error(mocker, hass):
    """Get cached url removes cache entry if json is malformed."""
    remove_mock = mocker.patch("os.remove")
    config = _cache_is_enabled()
    api_cache = ApiDataCache(hass, config)
    expected_file_path = "ecc5e2d8d57c91749b379bc26d1f677a.json"

    mock_open = mock.mock_open(read_data="<html>")
    with mock.patch("builtins.open", mock_open):
        result = api_cache.get("https://whatever")

        assert result is None
        remove_mock.assert_has_calls(calls=[call(expected_file_path)], any_order=True)


def _cache_is_not_old(mocker):
    now_in_seconds = time.mktime(datetime.now().astimezone(timezone.utc).timetuple())
    _set_cache_age(mocker, now_in_seconds)


def _cache_is_old(mocker):
    one_year_ago = datetime.now() - timedelta(days=365)
    one_year_ago_in_seconds = time.mktime(
        one_year_ago.astimezone(timezone.utc).timetuple()
    )
    _set_cache_age(mocker, one_year_ago_in_seconds)


def _set_cache_age(mocker, time_in_seconds):
    mocker.patch("os.path.getmtime", return_value=time_in_seconds)


def _url_is_not_cached(mocker):
    _set_if_url_cache_exists(mocker, False)


def _url_is_cached(mocker):
    _set_if_url_cache_exists(mocker, True)


def _set_if_url_cache_exists(mocker, exists: bool):
    mocker.patch("os.path.exists", return_value=exists)


def _cache_is_enabled() -> CacheConfig:
    return CacheConfig(enabled=True, cache_dir="", retention=timedelta(days=7))


def _cache_is_disabled() -> CacheConfig:
    return CacheConfig(enabled=False, cache_dir="", retention=timedelta(days=7))
