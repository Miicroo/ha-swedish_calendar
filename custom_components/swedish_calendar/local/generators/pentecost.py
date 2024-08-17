from datetime import date, timedelta

from generators import ThemeDateGenerator, count_descriptors
from generators.easter import gauss_easter


class PentecostGenerator(ThemeDateGenerator):

    @staticmethod
    def __get_pentecost_dates(year: int) -> [date]:
        easter_sun = gauss_easter(year)
        return [easter_sun + timedelta(i) for i in range(48, 50)]

    @staticmethod
    def __is_pentecost_day(date_in_month: date) -> bool:
        return date_in_month in PentecostGenerator.__get_pentecost_dates(date_in_month.year)

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 1:
            return False
        return all([self.__is_pentecost_day(d) for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        index = PentecostGenerator.__get_pentecost_dates(dates[0].year).index(dates[0])
        config['index'] = index
        config['description'] = f'{count_descriptors[index]} dagen i pingst'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        dates = self.__get_pentecost_dates(year)
        return dates[config['index']]

    def name(self) -> str:
        return 'pentecost'
