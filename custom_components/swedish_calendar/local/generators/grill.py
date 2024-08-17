from datetime import date

from generators.weekday_after_date import WeekdayAfterDateGenerator


class GrillGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 5, 2), 5)

    def name(self) -> str:
        return 'grill'
