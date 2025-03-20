from datetime import date

from .weekday_after_date import WeekdayAfterDateGenerator


class NewsDelivererGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 10, 7), 6)

    def name(self) -> str:
        return 'news_deliverer'
