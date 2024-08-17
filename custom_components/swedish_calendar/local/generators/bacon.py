from datetime import date

from generators.weekday_after_date import WeekdayAfterDateGenerator


class BaconGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 8, 30), 6)

    def name(self) -> str:
        return 'bacon'
