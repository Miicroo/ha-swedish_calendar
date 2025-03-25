from datetime import date, timedelta

import ephem

from . import ThemeDateGenerator
from .midsummer import MidsummerGenerator


class CaravanGenerator(ThemeDateGenerator):

    @staticmethod
    def _get_date(year: int) -> date:
        midsummer = MidsummerGenerator.midsummer(year)
        return midsummer - timedelta(days=6)

    def matches(self, theme: str, dates: [date]) -> bool:
        return len(dates) > 1 and all([d == self._get_date(d.year) for d in dates])

    def generate(self, config: dict[str, any], year: int) -> date:
        return self._get_date(year)

    def name(self) -> str:
        return 'caravan'
