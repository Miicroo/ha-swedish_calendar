from datetime import date

from .weekday_after_date import WeekdayAfterDateGenerator


class NettleGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 5, 2), 7)

    def name(self) -> str:
        return 'nettle'
