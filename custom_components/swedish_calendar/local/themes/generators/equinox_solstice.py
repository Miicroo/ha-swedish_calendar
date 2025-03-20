from datetime import date

import ephem

from . import ThemeDateGenerator


class EquinoxSolsticeGenerator(ThemeDateGenerator):
    def __init__(self):
        self.event_types = ['Vårdagjämning', 'Sommarsolstånd', 'Höstdagjämning', 'Vintersolstånd']

    @staticmethod
    def __get_dates(year: int) -> [date]:
        start_of_year = date(year, 1, 1)
        return [
            ephem.next_vernal_equinox(start_of_year).datetime().date(),
            ephem.next_summer_solstice(start_of_year).datetime().date(),
            ephem.next_autumnal_equinox(start_of_year).datetime().date(),
            ephem.next_winter_solstice(start_of_year).datetime().date()
        ]

    def __matches(self, date_in_month: date) -> bool:
        return date_in_month in self.__get_dates(date_in_month.year)

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 1:
            return False
        return all([self.__matches(d) for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        index = self.__get_dates(dates[0].year).index(dates[0])
        config['index'] = index
        config['description'] = self.event_types[index]

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        dates = self.__get_dates(year)
        return dates[config['index']]

    def name(self) -> str:
        return 'equinox_solstice'
