from __future__ import annotations

import datetime
from datetime import timedelta
import json
from typing import Any


class SensorConfig:
    def __init__(self,
                 friendly_name: str,
                 swedish_calendar_attribute: str,
                 default_value: Any,
                 icon: str | None = None,
                 attribution: str | None = None):
        self.friendly_name = friendly_name
        self.icon = icon
        self.swedish_calendar_attribute = swedish_calendar_attribute
        self.default_value = default_value
        self.attribution = attribution

    def get_value_from_calendar(self, calendar: SwedishCalendar) -> Any:
        return calendar.get_value_by_attribute(self.swedish_calendar_attribute)


class SwedishCalendar:
    def __init__(self):
        self._api_data: ApiData | None = None
        self._themes: ThemeData | None = None

    @staticmethod
    def from_api_data(api_data: ApiData) -> SwedishCalendar:
        return SwedishCalendar().with_api_data(api_data)

    @staticmethod
    def from_themes(themes: ThemeData) -> SwedishCalendar:
        return SwedishCalendar().with_themes(themes)

    def with_api_data(self, api_data: ApiData) -> SwedishCalendar:
        self._api_data = api_data
        return self

    def with_themes(self, themes: ThemeData) -> SwedishCalendar:
        self._themes = themes
        return self

    def get_value_by_attribute(self, attr: str) -> Any:
        if attr != 'themes':
            return getattr(self._api_data, attr) if self._api_data is not None else None
        else:
            return self._themes.themes if self._themes is not None else None


class ApiData:
    def __init__(self,
                 date: str,
                 weekday: str,
                 work_free_day: bool,
                 red_day: bool,
                 week: int,
                 day_of_week_index: int,
                 name_day: list[str],
                 reason_for_flagging: str | None,
                 eve: str | None,
                 holiday: str | None,
                 day_before_work_free_holiday: bool):
        self.date: str = date
        self.weekday: str = weekday
        self.work_free_day: bool = work_free_day
        self.red_day: bool = red_day
        self.week: int = week
        self.day_of_week_index: int = day_of_week_index
        self.name_day: list[str] = name_day
        self.reason_for_flagging: str | None = reason_for_flagging
        self.eve: str | None = eve
        self.holiday: str | None = holiday
        self.day_before_work_free_holiday: bool = day_before_work_free_holiday

    @staticmethod
    def from_json(json_data: dict[str, Any]) -> ApiData:
        return ApiData(
            date=json_data["datum"],
            weekday=json_data["veckodag"],
            work_free_day=ApiData._to_bool(json_data["arbetsfri dag"]),
            red_day=ApiData._to_bool(json_data["röd dag"]),
            week=int(json_data["vecka"]),
            day_of_week_index=int(json_data["dag i vecka"]),
            name_day=json_data["namnsdag"],
            reason_for_flagging=ApiData._to_optional(json_data, "flaggdag"),
            eve=ApiData._to_optional(json_data, 'helgdagsafton'),
            holiday=ApiData._to_optional(json_data, 'helgdag'),
            day_before_work_free_holiday=ApiData._to_optional_bool(json_data, "dag före arbetsfri helgdag")
        )

    @staticmethod
    def _to_bool(value: str) -> bool:
        return value is not None and value == 'Ja'

    @staticmethod
    def _to_optional_bool(json_value: dict[str, Any], key: str) -> bool:
        return ApiData._to_bool(json_value[key]) if key in json_value else False

    @staticmethod
    def _to_optional(json_value: dict[str, Any], key: str) -> Any | None:
        return json_value[key] if key in json_value else None

    def __repr__(self):
        return str(self)

    def __str__(self):
        return json.dumps(self.__dict__)


class ThemeData:
    def __init__(self, date: str, themes: list[str]):
        self.date: str = date
        self.themes: list[str] = themes


class SpecialThemesConfig:
    def __init__(self, path: str, auto_update: False):
        self.path = path
        self.auto_update = auto_update


class CalendarConfig:
    def __init__(self, includes: list[str], days_before_today: int, days_after_today: int):
        self.includes = includes
        self.days_before_today = days_before_today
        self.days_after_today = days_after_today


class CacheConfig:
    def __init__(self, enabled: bool, cache_dir: str, retention: timedelta):
        self.enabled = enabled
        self.cache_dir = cache_dir
        self.retention = retention
