from __future__ import annotations

from typing import Optional, List, Dict, Any


class SwedishCalendar:
    def __init__(self, api_data: ApiData, themes: ThemeData):
        self.api_data = api_data
        self.themes = themes

    def get_value_by_attribute(self, attr: str):
        if attr != 'themes':
            return getattr(self.api_data, attr)
        else:
            return self.themes.themes if self.themes is not None else None


class ApiData:
    def __init__(self, json_data: Dict[str, Any]):
        self.date: str = json_data["datum"]
        self.weekday: str = json_data["veckodag"]
        self.work_free_day: bool = self._to_bool(json_data["arbetsfri dag"])
        self.red_day: bool = self._to_bool(json_data["röd dag"])
        self.week: int = int(json_data["vecka"])
        self.day_of_week_index: int = int(json_data["dag i vecka"])
        self.name_day: List[str] = json_data["namnsdag"]
        self.reason_for_flagging: Optional[str] = self._to_optional(json_data, "flaggdag")
        self.eve: Optional[str] = self._to_optional(json_data, 'helgdagsafton')
        self.holiday: Optional[str] = self._to_optional(json_data, 'helgdag')
        self.day_before_work_free_holiday: bool = self._to_optional_bool(json_data, "dag före arbetsfri helgdag")

    @staticmethod
    def _to_bool(value: str) -> bool:
        return value is not None and value == 'Ja'

    @staticmethod
    def _to_optional_bool(json_value: Dict[str, Any], key: str) -> bool:
        return ApiData._to_bool(json_value[key]) if key in json_value else False

    @staticmethod
    def _to_optional(json_value: Dict[str, Any], key: str) -> Optional[Any]:
        return json_value[key] if key in json_value else None


class ThemeData:
    def __init__(self, date: str, themes: List[str]):
        self.date: str = date
        self.themes: List[str] = themes
