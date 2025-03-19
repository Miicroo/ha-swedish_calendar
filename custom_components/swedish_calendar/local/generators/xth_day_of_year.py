from datetime import date, timedelta

from . import ThemeDateGenerator


class XthDayOfYearGenerator(ThemeDateGenerator):

    @staticmethod
    def __days_since_jan_1(date_to_diff: date) -> int:
        return (date_to_diff - date(date_to_diff.year - 1, 12, 31)).days

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 2:
            return False

        day_of_year = self.__days_since_jan_1(dates[0])
        print([self.__days_since_jan_1(d) for d in dates])

        return all([self.__days_since_jan_1(d) == day_of_year for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        day = self.__days_since_jan_1(dates[0])
        config['day'] = day
        config['description'] = f'Dag {day} varje år'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        return date(year - 1, 12, 31) + timedelta(days=config['day'])

    def name(self) -> str:
        return 'xth_day_of_year'
