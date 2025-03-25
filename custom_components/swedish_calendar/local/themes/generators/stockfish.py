from datetime import date, timedelta

from . import ThemeDateGenerator
from .all_saints import AllSaintsGenerator


class StockfishGenerator(ThemeDateGenerator):

    @staticmethod
    def _stockfish_day(year: int) -> date:
        return AllSaintsGenerator.all_saints_date(year) - timedelta(days=1)

    def matches(self, theme: str, dates: [date]) -> bool:
        return len(dates) > 1 and all([d == self._stockfish_day(d.year) for d in dates])

    def generate(self, config: dict[str, any], year: int) -> date:
        return self._stockfish_day(year)

    def name(self) -> str:
        return 'stockfish'
