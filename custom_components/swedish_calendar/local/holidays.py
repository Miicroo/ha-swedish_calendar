import copy
from datetime import date

from . import StaticHolidayConfig
from ..types import ThemeData

_HOLIDAY = StaticHolidayConfig(work_free=False, red_day=False)
_WORK_FREE_HOLIDAY = StaticHolidayConfig(work_free=True, red_day=False)
_WORK_FREE_RED_HOLIDAY = StaticHolidayConfig(work_free=True, red_day=True)
_EVE = StaticHolidayConfig(work_free=False, red_day=False, eve=True)
_WORK_FREE_EVE = StaticHolidayConfig(work_free=True, red_day=False, eve=True)

_STATIC_HOLIDAY_CONFIGS = {
    'Midsommarafton': _WORK_FREE_HOLIDAY,
    'Midsommardagen': _WORK_FREE_RED_HOLIDAY,
    'Skärtorsdagen': _EVE,
    'Långfredagen': _WORK_FREE_RED_HOLIDAY,
    'Påskafton': _WORK_FREE_HOLIDAY,
    'Påskdagen': _WORK_FREE_RED_HOLIDAY,
    'Annandag påsk': _WORK_FREE_RED_HOLIDAY,
    'Kristi himmelsfärdsdag': _WORK_FREE_RED_HOLIDAY,
    'Valborgsmässoafton': _EVE,
    'Pingstafton': _WORK_FREE_EVE,
    'Pingstdagen': _WORK_FREE_RED_HOLIDAY,
    'Allhelgonaafton': _EVE,
    'Alla helgons dag': _WORK_FREE_RED_HOLIDAY,
    'Trettondagsafton': _EVE,
    'Trettondagen': _WORK_FREE_RED_HOLIDAY,
    'Första maj': _WORK_FREE_RED_HOLIDAY,
    'Julafton': _WORK_FREE_HOLIDAY,
    'Juldagen': _WORK_FREE_RED_HOLIDAY,
    'Annandag jul': _WORK_FREE_RED_HOLIDAY,
    'Nyårsafton': _WORK_FREE_HOLIDAY,
    'Nyårsdagen': _WORK_FREE_RED_HOLIDAY,
}


# TODO: Improvement here would be to not send in themes: list[ThemeData], and let this class handle source data
#  itself
def get_holidays(start: date, end: date, themes: list[ThemeData]) -> dict[str, list[(str, StaticHolidayConfig)]]:
    year = min(start.year, end.year)  # TODO: What if there are multiple years?

    holiday_configs = copy.deepcopy(_STATIC_HOLIDAY_CONFIGS)

    if year < 1983:
        holiday_configs['Svenska flaggans dag'] = _HOLIDAY,
    else:
        holiday_configs['Sveriges nationaldag'] = _WORK_FREE_RED_HOLIDAY if year >= 2005 else _HOLIDAY

    holiday_configs['Annandag pingst'] = _HOLIDAY if year >= 2005 else _WORK_FREE_RED_HOLIDAY

    # TODO Test 2008 "helgdag": "Kristi himmelsfärdsdag, Första Maj",

    holidays: dict[str, list[(str, StaticHolidayConfig)]] = {}
    for theme_data in themes:
        for holiday in holiday_configs.keys():
            if holiday in theme_data.themes:
                holiday_themes = holidays.get(theme_data.date) or []
                holiday_themes.append((holiday, holiday_configs[holiday]))
                holidays[theme_data.date] = holiday_themes

    # TODO: Missing Allhelgonaafton
    return holidays
