from datetime import date, timedelta

from . import ThemeDateGenerator


class WeekdayOfLastFullWeekInMonthGenerator(ThemeDateGenerator):

    @staticmethod
    def __next_week_is_not_in_same_month__(date_in_month: date) -> bool:
        return (date_in_month + timedelta(
            days=14 - date_in_month.isoweekday())).month > date_in_month.month  # Next week is moved into next month

    @staticmethod
    def __this_week_is_in_same_month__(date_in_month: date) -> bool:
        return (date_in_month + timedelta(
            days=7 - date_in_month.isoweekday())).month == date_in_month.month  # Next week is moved into next month

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 2:
            return False
        return all([self.__this_week_is_in_same_month__(d) and self.__next_week_is_not_in_same_month__(d)
                    and d.weekday() == dates[0].weekday() and d.month == dates[0].month for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        config['weekday'] = dates[0].isoweekday()
        config['month'] = dates[0].month
        config['description'] = f'{dates[0].strftime("%A")} i sista hela veckan i {dates[0].strftime("%B")}'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        last_day_in_month = date(year, config['month']+1, 1) - timedelta(days=1)
        if last_day_in_month.isoweekday() == 7:  # Is full week
            days_diff = 7 - config['weekday']
        else:
            days_diff = (last_day_in_month.isoweekday() - config['weekday']) % 7 + 7
        return last_day_in_month - timedelta(days=days_diff)

    def name(self) -> str:
        return 'weekday_of_last_full_week_in_month'
