from datetime import date, timedelta

from . import ThemeDateGenerator, count_descriptors
from .easter import gauss_easter


class FastDaysGenerator(ThemeDateGenerator):

    @staticmethod
    def __get_fast_dates(year: int) -> [date]:
        easter_sun = gauss_easter(year)
        return [easter_sun - timedelta(i) for i in range(49, 45, -1)]

    @staticmethod
    def __is_fast_day(date_in_month: date) -> bool:
        return date_in_month in FastDaysGenerator.__get_fast_dates(date_in_month.year)

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 1:
            return False
        return all([self.__is_fast_day(d) for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        index = FastDaysGenerator.__get_fast_dates(dates[0].year).index(dates[0])
        config['index'] = index
        config['description'] = f'{count_descriptors[index]} dagen i fastlagsdagarna'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        dates = self.__get_fast_dates(year)
        return dates[config['index']]

    def name(self) -> str:
        return 'fast_days'
