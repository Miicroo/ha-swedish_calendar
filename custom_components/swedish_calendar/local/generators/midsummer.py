from datetime import date, timedelta

from generators.weekday_after_date import WeekdayAfterDateGenerator


class MidsummerGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 6, 19), 5)
        self.event_types = ['Midsommarafton', 'Midsommardagen']

    @staticmethod
    def midsummer(year: int) -> date:
        return MidsummerGenerator()._get_date(year)

    def _get_dates(self, year: int) -> [date]:
        midsummer = self._get_date(year)
        return [midsummer, midsummer + timedelta(days=1)]

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        index = self._get_dates(dates[0].year).index(dates[0])
        config['index'] = index
        config['description'] = self.event_types[index]

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        dates = self._get_dates(year)
        return dates[config['index']]

    def name(self) -> str:
        return 'midsummer'
