from datetime import date

from .weekday_after_date import WeekdayAfterDateGenerator


class SwedishParliamentaryElectionGenerator(WeekdayAfterDateGenerator):
    def __init__(self):
        super().__init__(date(1970, 9, 9), 7)

    @staticmethod
    def _is_election_year(year: int) -> bool:
        if year < 1970:
            raise Exception("Not implemented")
        mod_year = 3 if year < 1994 else 4
        return year % mod_year == 2

    def matches(self, theme: str, dates: [date]) -> bool:
        return len(dates) > 0 and all([self._is_election_year(d.year) and d == self._get_date(d.year) for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        config['description'] = 'Andra söndagen efter 1e september, vart fjärde år efter 1994'  # Good enough precision

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        return super().generate(config, year) if self._is_election_year(year) else None

    def name(self) -> str:
        return 'swedish_parliamentary_election'
