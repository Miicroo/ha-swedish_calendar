from collections import defaultdict
from collections.abc import Callable
from datetime import date

from custom_components.swedish_calendar.types import ThemeData

_FLAG_DAYS_THAT_ARE_ALSO_THEMES = [
    'Nyårsdagen',
    'Första maj',
    'Veterandagen',
    'Sveriges nationaldag',
    'FN-dagen',
    'Gustav Adolfsdagen',
    'Nobeldagen',
    'Juldagen',
    'Påskdagen',
    'Pingstdagen',
    'Midsommardagen',
    'Valdagen',
]

_ROYAL_FLAG_DAYS: dict[str, Callable[[int], date]] = {
    'Kung Carl XVI Gustafs namnsdag': lambda y: date(y, 1, 28),
    'Kung Carl XVI Gustafs födelsedag': lambda y: date(y, 4, 30),
    'Kronprinsessan Victorias namnsdag': lambda y: date(y, 3, 12),
    'Kronprinsessan Victorias födelsedag': lambda y: date(y, 7, 14),
    'Drottning Silvias namnsdag': lambda y: date(y, 8, 8),
    'Drottning Silvias födelsedag': lambda y: date(y, 12, 23),
}


def get_flag_days(start: date, end: date, theme_days: list[ThemeData]) -> dict[str, list[str]]:
    flag_days: dict[str, list[str]] = defaultdict(list)

    for theme_data in theme_days:
        for flag_day in _FLAG_DAYS_THAT_ARE_ALSO_THEMES:
            if flag_day in theme_data.themes:
                flag_days[theme_data.date].append(flag_day)

    start_year = min(start.year, end.year)
    end_year = max(start.year, end.year) + 1

    for (flag_day, date_function) in _ROYAL_FLAG_DAYS.items():
        for year in range(start_year, end_year):
            flag_date = date_function(year).strftime('%Y-%m-%d')
            flag_days[flag_date].append(flag_day)

    return flag_days
