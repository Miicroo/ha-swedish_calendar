from datetime import date

from .weekday_after_date import WeekdayAfterDateGenerator


class GrandparentsGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 9, 7), 7)

    def name(self) -> str:
        return 'grandparents'
