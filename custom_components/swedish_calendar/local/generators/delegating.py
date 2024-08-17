from datetime import date

from generators import ThemeDateGenerator
from generators.all_saints import AllSaintsGenerator
from generators.holy_mikael import HolyMikaelGenerator
from generators.last_weekday_of_month import LastWeekdayOfMonthGenerator
from generators.news_deliverer import NewsDelivererGenerator
from generators.safer_internet import SaferInternetGenerator
from generators.same_date import SameDateGenerator
from generators.stockfish import StockfishGenerator
from generators.weekday_of_xth_week import WeekdayOfXthWeekGenerator
from generators.xth_day_of_year import XthDayOfYearGenerator
from generators.xth_weekday_of_month import XthWeekdayOfMonthGenerator


class DelegatingGenerator(ThemeDateGenerator):

    def __init__(self):
        self.overrides = {
            'Världsvänskapsdagen': {
                'dates': [date(2021, 7, 31), date(2022, 7, 31), date(2023, 7, 31), date(2024, 7, 31)],
                'generator': SameDateGenerator()
            },
            'Alla helgons dag': {
                'dates': [date(2021, 11, 6), date(2022, 11, 5), date(2023, 11, 4), date(2024, 11, 2)],
                'generator': AllSaintsGenerator()
            },
            'Alla själars dag': {
                'dates': [date(2021, 11, 7), date(2022, 11, 6), date(2023, 11, 5), date(2024, 11, 3)],
                'generator': AllSaintsGenerator()
            },
            'Programmerarens dag': {
                'dates': [date(2021, 9, 13), date(2022, 9, 13), date(2024, 9, 12)],
                'generator': XthDayOfYearGenerator()
            },
            'Internationella gin och tonic-dagen': {
                'dates': [date(2022, 10, 19), date(2023, 10, 19), date(2024, 10, 19)],
                'generator': SameDateGenerator()
            },
            'Ångans dag': {
                'dates': [date(2021, 6, 5), date(2023, 6, 3), date(2024, 6, 1)],
                'generator': XthWeekdayOfMonthGenerator()
            },
            'Internationella champagnedagen': {
                'dates': [date(2021, 10, 22), date(2022, 10, 28), date(2023, 10, 27), date(2024, 10, 25)],
                'generator': XthWeekdayOfMonthGenerator()
            },
            'Den helige Mikaels dag': {
                'dates': [[date(2021, 10, 3), date(2022, 10, 2), date(2024, 9, 29)]],
                'generator': HolyMikaelGenerator()
            },
            'Lutfiskens dag': {
                'dates': [date(2021, 11, 5), date(2022, 11, 4), date(2023, 11, 3), date(2024, 11, 1)],
                'generator': StockfishGenerator()
            },
            'Lösgodisets dag': {
                'dates': [date(2023, 9, 30), date(2024, 9, 28)],
                'generator': LastWeekdayOfMonthGenerator()
            },
            'Int. dagen för begränsning av naturkatastrofer': {
                'dates': [date(2023, 10, 11), date(2024, 10, 9)],
                'generator': XthWeekdayOfMonthGenerator()
            },
            'Uniform på jobbet-dagen': {
                'dates': [date(2023, 4, 19), date(2024, 4, 17)],
                'generator': WeekdayOfXthWeekGenerator()
            },
            'Kälkåkningens dag': {
                'dates': [date(2023, 2, 26), date(2024, 2, 25)],
                'generator': LastWeekdayOfMonthGenerator()
            },
            'Ängens dag': {
                'dates': [date(2023, 8, 5), date(2024, 8, 3)],
                'generator': XthWeekdayOfMonthGenerator()
            },
            'Östersjödagen': {
                'dates': [date(2023, 8, 31), date(2024, 8, 29)],
                'generator': LastWeekdayOfMonthGenerator()
            },
            'Tidningsbudens dag': {
                'dates': [date(2023, 10, 7), date(2024, 10, 12)],
                'generator': NewsDelivererGenerator()
            },
            'Unik butik-dagen': {
                'dates': [date(2021, 10, 30), date(2023, 10, 28)],
                'generator': LastWeekdayOfMonthGenerator()
            },
            'Dövas dag': {
                'dates': [date(2021, 9, 19), date(2022, 9, 18)],
                'generator': XthWeekdayOfMonthGenerator()
            },
            'Internationella flyttfågeldagen': {
                'dates': [date(2021, 5, 8), date(2022, 5, 7), date(2023, 5, 13), date(2024, 5, 11)],
                'generator': XthWeekdayOfMonthGenerator()
            },
            'Safer internet day': {
                'dates': [date(2021, 2, 9), date(2022, 2, 8), date(2023, 2, 7), date(2024, 2, 6)],
                'generator': SaferInternetGenerator()
            },
        }

    def matches(self, theme: str, dates: [date]) -> bool:
        return theme in self.overrides.keys()

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        return self.overrides[theme]['generator'].generate_config(theme, self.overrides[theme]['dates'])

    def generate(self, config: dict[str, any], year: int) -> date:
        return self.overrides[config['theme']]['generator'].generate(config, year)
