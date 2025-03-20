from datetime import date, timedelta
from functools import partial
import logging

from custom_components.swedish_calendar.local import StaticHolidayConfig
from custom_components.swedish_calendar.local.flag_days import get_flag_days
from custom_components.swedish_calendar.local.holidays import get_holidays
from custom_components.swedish_calendar.local.name_days import NameDayProvider
from custom_components.swedish_calendar.local.themes.theme_data_local import (
    LocalThemeDataProvider,
)
from custom_components.swedish_calendar.types import ApiData, ThemeData
from custom_components.swedish_calendar.utils import DateUtils
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

#  TODO: There must be a better way than this
_WEEKDAYS = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]


class LocalApiDataProvider:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.theme_data_provider = LocalThemeDataProvider(hass)
        self.name_day_provider = NameDayProvider()

    async def fetch_data(self, start: date, end: date) -> list[ApiData]:
        themes = await self.theme_data_provider.fetch_data(start, end)
        return await self.hass.async_add_executor_job(partial(self._fetch_data, start=start, end=end, themes=themes))

    def _fetch_data(self, start: date, end: date, themes: list[ThemeData]) -> list[ApiData]:
        all_api_data = []

        holidays = get_holidays(start, end, themes)
        flag_days = get_flag_days(start, end, themes)

        for day in DateUtils.range(start, end):
            iso_date: str = day.strftime('%Y-%m-%d')
            iso_tomorrow = (day + timedelta(days=1)).strftime('%Y-%m-%d')
            holidays_today = holidays[iso_date] if iso_date in holidays.keys() else []
            holidays_tomorrow = holidays[iso_tomorrow] if iso_tomorrow in holidays.keys() else []
            reasons_for_flagging = flag_days.get(iso_date)

            work_free_today = self._is_work_free_day(day, holidays_today)

            #  TODO: Klämdag -> igår och imorgon är arbetsfri
            all_api_data.append(
                ApiData(
                    date=iso_date,
                    weekday=self._get_weekday(day),
                    week=day.isocalendar().week,
                    day_of_week_index=day.isoweekday(),
                    red_day=self._is_red_day(day, holidays_today),
                    work_free_day=work_free_today,
                    eve=self._eve(holidays_today),
                    holiday=self._holiday(holidays_today),
                    day_before_work_free_holiday=self._is_work_free_holiday(holidays_tomorrow) and not work_free_today,
                    reason_for_flagging=', '.join(reasons_for_flagging) if reasons_for_flagging is not None else "",
                    name_day=self.name_day_provider.get_names(day.strftime('%m-%d'))
                )
            )

        return all_api_data

    @staticmethod
    def _get_weekday(day: date) -> str:
        return _WEEKDAYS[day.weekday()]

    @staticmethod
    def _is_red_day(day: date, holidays: list[(str, StaticHolidayConfig)]) -> bool:
        red_holiday = any([config.red_day for (_, config) in holidays])
        is_sunday = day.isoweekday() == 7
        return is_sunday or red_holiday

    @staticmethod
    def _is_work_free_day(day: date, holidays: list[(str, StaticHolidayConfig)]) -> bool:
        work_free_holiday = LocalApiDataProvider._is_work_free_holiday(holidays)
        is_weekend = day.isoweekday() >= 6
        return is_weekend or work_free_holiday

    @staticmethod
    def _is_work_free_holiday(holidays: list[(str, StaticHolidayConfig)]):
        return any([config.work_free for (_, config) in holidays if not config.eve])

    @staticmethod
    def _eve(holidays_today: list[(str, StaticHolidayConfig)]) -> str | None:
        holidays = [theme for (theme, config) in holidays_today if not config.eve]
        eves = [theme for (theme, config) in holidays_today if config.eve]

        # If any holiday is set, it is not an eve
        return ', '.join(eves) if len(holidays) == 0 and len(eves) > 0 else None

    @staticmethod
    def _holiday(holidays_today: list[(str, StaticHolidayConfig)]) -> str | None:
        holidays = [theme for (theme, config) in holidays_today if not config.eve]
        eves = [theme for (theme, config) in holidays_today if config.eve]

        # If both holidays and eves exist, everything is treated as a holiday
        all_holidays = (holidays + eves) if len(holidays) > 0 else []
        return ', '.join(all_holidays) if len(all_holidays) > 0 else None
