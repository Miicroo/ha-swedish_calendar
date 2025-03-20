from datetime import date

from . import ThemeDateGenerator


class SameDateGenerator(ThemeDateGenerator):
    def matches(self, theme: str, dates: [date]) -> bool:
        return len(dates) > 0 and all([d.month == dates[0].month and d.day == dates[0].day for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        config['month'] = dates[0].month
        config['day'] = dates[0].day
        config['description'] = f'{dates[0].strftime("%d %B")} varje år'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        return date(year, config['month'], config['day'])

    def name(self) -> str:
        return 'same_date'
