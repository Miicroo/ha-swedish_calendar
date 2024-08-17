from datetime import date

from generators.weekday_after_date import WeekdayAfterDateGenerator


class StartOfLobsterFishingGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 9, 21), 1)

    def name(self) -> str:
        return 'start_of_lobster_fishing'
