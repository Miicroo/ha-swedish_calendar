from datetime import date, timedelta

from generators import ThemeDateGenerator


class AllBossesGenerator(ThemeDateGenerator):
    @staticmethod
    def __get_all_bosses_day(year: int) -> date:
        all_bosses_day = date(year, 10, 16)

        if all_bosses_day.isoweekday() == 6:  # Sat -> Fri
            all_bosses_day -= timedelta(days=1)
        elif all_bosses_day.isoweekday() == 7:  # Sun -> Mon
            all_bosses_day += timedelta(days=1)

        return all_bosses_day

    def matches(self, theme: str, dates: [date]) -> bool:
        return len(dates) > 1 and all([d == self.__get_all_bosses_day(d.year) for d in dates])

    def generate(self, config: dict[str, any], year: int) -> date:
        return self.__get_all_bosses_day(year)

    def name(self) -> str:
        return 'all_bosses'
