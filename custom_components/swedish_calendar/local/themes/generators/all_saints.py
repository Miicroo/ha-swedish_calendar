from datetime import date, timedelta

from . import ThemeDateGenerator, count_descriptors
from .weekday_after_date import WeekdayAfterDateGenerator


class AllSaintsGenerator(WeekdayAfterDateGenerator):

    def __init__(self):
        super().__init__(date(1970, 10, 31), 6)

    @staticmethod
    def all_saints_date(year: int) -> date:
        return AllSaintsGenerator()._get_date(year)

    def _get_dates(self, year: int) -> [date]:
        all_saints = self._get_date(year)
        return [all_saints, all_saints + timedelta(days=1)]

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        index = self._get_dates(dates[0].year).index(dates[0])
        config['index'] = index
        config['description'] = f'{count_descriptors[index]} dagen i alla helgons dag-helgen'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        dates = self._get_dates(year)
        return dates[config['index']]

    def name(self) -> str:
        return 'all_saints'
