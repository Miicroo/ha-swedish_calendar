from datetime import date, timedelta

from . import ThemeDateGenerator, count_descriptors


class AdventGenerator(ThemeDateGenerator):

    @staticmethod
    def __get_advent_dates(year: int) -> [date]:
        christmas_eve = date(year, 12, 24)
        fourth_advent = christmas_eve - timedelta(days=christmas_eve.isoweekday() % 7)
        return [fourth_advent - timedelta(i) for i in range(21, -7, -7)]

    @staticmethod
    def __is_advent(date_in_month: date) -> bool:
        return date_in_month in AdventGenerator.__get_advent_dates(date_in_month.year)

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 1:
            return False
        return all([self.__is_advent(d) for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        index = AdventGenerator.__get_advent_dates(dates[0].year).index(dates[0])
        config['index'] = index
        config['description'] = f'{count_descriptors[index]} advent'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        dates = self.__get_advent_dates(year)
        return dates[config['index']]

    def name(self) -> str:
        return 'advent'
