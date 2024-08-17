from datetime import date

from generators.weekday_after_date import WeekdayAfterDateGenerator


class SaferInternetGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 2, 5), 2)

    def name(self) -> str:
        return 'safer_internet'
