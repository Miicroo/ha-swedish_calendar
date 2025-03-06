from datetime import date, timedelta

from . import ThemeDateGenerator, count_descriptors


class XthWeekdayOfMonthGenerator(ThemeDateGenerator):

    @staticmethod
    def __how_many_xday_in_month__(date_in_month: date) -> int:
        return int(date_in_month.day / 7) + min(1, date_in_month.day % 7)

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 2:
            return False
        week_in_month = self.__how_many_xday_in_month__(dates[0])

        return all(
            [self.__how_many_xday_in_month__(d) == week_in_month and d.weekday() == dates[0].weekday() and d.month ==
             dates[0].month for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        xth = self.__how_many_xday_in_month__(dates[0])
        config['xth'] = xth
        config['weekday'] = dates[0].isoweekday()
        config['month'] = dates[0].month
        config['description'] = f'{count_descriptors[xth - 1]} {dates[0].strftime("%A")} i {dates[0].strftime("%B")}'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        start = date(year, config['month'], 1)
        diff_to_first = (config['weekday'] - start.isoweekday()) % 7
        diff_to_wanted_date = (config['xth'] - 1) * 7 + diff_to_first

        return start + timedelta(days=diff_to_wanted_date)

    def name(self) -> str:
        return 'xth_weekday_of_month'
