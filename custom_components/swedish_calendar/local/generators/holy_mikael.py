from datetime import date

from generators.weekday_after_date import WeekdayAfterDateGenerator


class HolyMikaelGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 9, 29), 7)

    def name(self) -> str:
        return 'holy_mikael'
