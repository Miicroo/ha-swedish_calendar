from datetime import date, timedelta
import math

from generators import ThemeDateGenerator, count_descriptors


def gauss_easter(year: int) -> date:
    a = year % 19
    b = year % 4
    c = year % 7

    p = math.floor(year / 100)
    q = math.floor((13 + 8 * p) / 25)
    m = (15 - q + p - p // 4) % 30
    n = (4 + p - p // 4) % 7
    d = (19 * a + m) % 30
    e = (2 * b + 4 * c + 6 * d + n) % 7
    days = (22 + d + e)

    # A corner case, when D is 29
    if (d == 29) and (e == 6):
        return date(year, 4, 19)
    # Another corner case, when D is 28
    elif (d == 28) and (e == 6):
        return date(year, 4, 18)
    else:
        # If days > 31, move to April
        if days > 31:
            return date(year, 4, days - 31)
        else:
            return date(year, 3, days)


class EasterGenerator(ThemeDateGenerator):

    @staticmethod
    def __get_easter_dates(year):
        easter_sun = gauss_easter(year)
        return [easter_sun - timedelta(i) for i in range(3, -2, -1)]

    @staticmethod
    def __is_easter__(date_in_month):
        return date_in_month in EasterGenerator.__get_easter_dates(date_in_month.year)

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 1:
            return False
        return all([self.__is_easter__(d) for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        index = EasterGenerator.__get_easter_dates(dates[0].year).index(dates[0])
        config['index'] = index
        config['description'] = f'{count_descriptors[index]} dagen i påsk'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        dates = self.__get_easter_dates(year)
        return dates[config['index']]

    def name(self) -> str:
        return 'easter'
