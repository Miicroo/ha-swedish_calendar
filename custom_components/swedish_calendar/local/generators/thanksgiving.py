from datetime import date, timedelta

from . import ThemeDateGenerator, count_descriptors


class ThanksGivingGenerator(ThemeDateGenerator):

    @staticmethod
    def __thanksgiving(year: int) -> date:
        nov_first = date(year, 11, 1)
        shift_to_first_thursday = (4 - nov_first.isoweekday()) % 7
        fourth_thursday = nov_first + timedelta(days=shift_to_first_thursday + 21)
        return fourth_thursday

    @staticmethod
    def __get_dates(year: int) -> [date]:
        thanksgiving = ThanksGivingGenerator.__thanksgiving(year)

        # Thanksgiving, Black Friday, Cyber Monday, Giving Tuesday
        return [thanksgiving,
                thanksgiving + timedelta(days=1),
                thanksgiving + timedelta(days=4),
                thanksgiving + timedelta(days=5)
                ]

    @staticmethod
    def __get_thanksgiving_index(d: date) -> int:
        dates = ThanksGivingGenerator.__get_dates(d.year)
        return dates.index(d) if d in dates else -1

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 2:
            return False

        thanksgiving_index = self.__get_thanksgiving_index(dates[0])
        return thanksgiving_index != -1 and all([self.__get_thanksgiving_index(d) == thanksgiving_index for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        index = self.__get_thanksgiving_index(dates[0])
        config['index'] = index
        config['description'] = f'{count_descriptors[index]} dagen i Thanks Giving'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        dates = self.__get_dates(year)
        return dates[config['index']]

    def name(self) -> str:
        return 'thanksgiving'
