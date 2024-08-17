from datetime import date, timedelta

from generators import ThemeDateGenerator


class LastWeekdayOfMonthGenerator(ThemeDateGenerator):

    @staticmethod
    def __is_last_xday_in_month__(date_in_month: date) -> bool:
        return (date_in_month + timedelta(days=7)).month > date_in_month.month  # Next week is moved into next month

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 2:
            return False

        return all([self.__is_last_xday_in_month__(d) and d.weekday() == dates[
            0].weekday() and d.month ==
                    dates[0].month for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        config['weekday'] = dates[0].isoweekday()
        config['month'] = dates[0].month
        config['description'] = f'Sista {dates[0].strftime("%A")} i {dates[0].strftime("%B")}'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        start = date(year, config['month'], 1)
        next_month = date(year, config['month']+1, 1)
        diff_to_first = (config['weekday'] - start.isoweekday()) % 7
        first = start + timedelta(days=diff_to_first)
        days_to_last_in_month = (next_month-first).days - 1

        return first + timedelta(days=int(days_to_last_in_month / 7) * 7)

    def name(self) -> str:
        return 'last_weekday_of_month'
