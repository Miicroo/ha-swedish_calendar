from datetime import date, timedelta

from . import ThemeDateGenerator


class WeekdayAfterDateGenerator(ThemeDateGenerator):

    def __init__(self, earliest_date: date, weekday: int):
        self.earliest_date = earliest_date
        self.weekday = weekday

    def _get_date(self, year: int) -> date:
        next_date_shift = (self.weekday - self.earliest_date.replace(year=year).isoweekday()) % 7
        return self.earliest_date.replace(year=year) + timedelta(days=next_date_shift)

    def _get_dates(self, year: int) -> [date]:
        return [self._get_date(year)]  # default implementation

    def matches(self, theme: str, dates: [date]) -> bool:
        return len(dates) > 1 and all([d in self._get_dates(d.year) for d in dates])

    def generate(self, config: dict[str, any], year: int) -> date:
        return self._get_date(year)
