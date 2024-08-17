from datetime import date

import ephem
from generators import ThemeDateGenerator
from generators.midsummer import MidsummerGenerator


class NationalOGenerator(ThemeDateGenerator):

    @staticmethod
    def _get_date(year: int) -> date:
        midsummer = MidsummerGenerator.midsummer(year)
        return ephem.next_full_moon(ephem.Date(midsummer)).datetime().date()

    def matches(self, theme: str, dates: [date]) -> bool:
        return len(dates) > 1 and all([d == self._get_date(d.year) for d in dates])

    def generate(self, config: dict[str, any], year: int) -> date:
        return self._get_date(year)

    def name(self) -> str:
        return 'national_o'
