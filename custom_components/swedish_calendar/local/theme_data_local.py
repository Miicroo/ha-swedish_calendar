from datetime import date
from functools import partial
import json
import logging
import os
import threading

from custom_components.swedish_calendar.local.generators import ThemeDateGenerator
from custom_components.swedish_calendar.local.generators.advent import AdventGenerator
from custom_components.swedish_calendar.local.generators.all_bosses import (
    AllBossesGenerator,
)
from custom_components.swedish_calendar.local.generators.all_saints import (
    AllSaintsGenerator,
)
from custom_components.swedish_calendar.local.generators.ascension import (
    AscensionGenerator,
)
from custom_components.swedish_calendar.local.generators.bacon import BaconGenerator
from custom_components.swedish_calendar.local.generators.caravan import CaravanGenerator
from custom_components.swedish_calendar.local.generators.easter import EasterGenerator
from custom_components.swedish_calendar.local.generators.equinox_solstice import (
    EquinoxSolsticeGenerator,
)
from custom_components.swedish_calendar.local.generators.fast_days import (
    FastDaysGenerator,
)
from custom_components.swedish_calendar.local.generators.funeral_greeting import (
    FuneralGreetingGenerator,
)
from custom_components.swedish_calendar.local.generators.grandparents import (
    GrandparentsGenerator,
)
from custom_components.swedish_calendar.local.generators.grill import GrillGenerator
from custom_components.swedish_calendar.local.generators.holy_mikael import (
    HolyMikaelGenerator,
)
from custom_components.swedish_calendar.local.generators.last_weekday_of_month import (
    LastWeekdayOfMonthGenerator,
)
from custom_components.swedish_calendar.local.generators.midsummer import (
    MidsummerGenerator,
)
from custom_components.swedish_calendar.local.generators.national_o import (
    NationalOGenerator,
)
from custom_components.swedish_calendar.local.generators.nettle import NettleGenerator
from custom_components.swedish_calendar.local.generators.news_deliverer import (
    NewsDelivererGenerator,
)
from custom_components.swedish_calendar.local.generators.pentecost import (
    PentecostGenerator,
)
from custom_components.swedish_calendar.local.generators.safer_internet import (
    SaferInternetGenerator,
)
from custom_components.swedish_calendar.local.generators.same_date import (
    SameDateGenerator,
)
from custom_components.swedish_calendar.local.generators.start_of_lobster_fishing import (
    StartOfLobsterFishingGenerator,
)
from custom_components.swedish_calendar.local.generators.stockfish import (
    StockfishGenerator,
)
from custom_components.swedish_calendar.local.generators.swedish_parliamentary_election import (
    SwedishParliamentaryElectionGenerator,
)
from custom_components.swedish_calendar.local.generators.thanksgiving import (
    ThanksGivingGenerator,
)
from custom_components.swedish_calendar.local.generators.weekday_of_last_full_week_in_month import (
    WeekdayOfLastFullWeekInMonthGenerator,
)
from custom_components.swedish_calendar.local.generators.weekday_of_xth_week import (
    WeekdayOfXthWeekGenerator,
)
from custom_components.swedish_calendar.local.generators.xth_day_of_year import (
    XthDayOfYearGenerator,
)
from custom_components.swedish_calendar.local.generators.xth_weekday_of_month import (
    XthWeekdayOfMonthGenerator,
)
from custom_components.swedish_calendar.types import ThemeData

_LOGGER = logging.getLogger(__name__)


class LocalThemeDataUpdater:

    def can_update(self) -> bool:
        return False

    def update(self):
        pass


class LocalThemeDataProvider:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, hass):
        if not hasattr(self, "hass"):
            self._initialized = True
            self.hass = hass
            self.generators: [ThemeDateGenerator] = [EasterGenerator(),
                                                     FastDaysGenerator(),
                                                     AdventGenerator(),
                                                     AscensionGenerator(),
                                                     PentecostGenerator(),
                                                     EquinoxSolsticeGenerator(),
                                                     MidsummerGenerator(),
                                                     AllSaintsGenerator(),
                                                     LastWeekdayOfMonthGenerator(),
                                                     WeekdayOfLastFullWeekInMonthGenerator(),
                                                     XthWeekdayOfMonthGenerator(),
                                                     WeekdayOfXthWeekGenerator(),
                                                     SameDateGenerator(),
                                                     NettleGenerator(),
                                                     HolyMikaelGenerator(),
                                                     ThanksGivingGenerator(),
                                                     AllBossesGenerator(),
                                                     StockfishGenerator(),
                                                     FuneralGreetingGenerator(),
                                                     NationalOGenerator(),
                                                     StartOfLobsterFishingGenerator(),
                                                     SwedishParliamentaryElectionGenerator(),
                                                     NewsDelivererGenerator(),
                                                     GrillGenerator(),
                                                     BaconGenerator(),
                                                     CaravanGenerator(),
                                                     GrandparentsGenerator(),
                                                     SaferInternetGenerator(),
                                                     XthDayOfYearGenerator()
                                                     ]
            self.generator_config = {generator.name(): generator for generator in self.generators}

    async def fetch_data(self, start: date, end: date) -> list[ThemeData]:
        return await self.hass.async_add_executor_job(partial(self._fetch_data, start=start, end=end))

    def _fetch_data(self, start: date, end: date) -> list[ThemeData]:
        years = list(range(min(start.year, end.year), max(start.year, end.year) + 1))
        all_themes = self.__get_theme_days(years)
        themes = []

        for (theme_date, special_themes) in all_themes.items():
            iso_date_str = theme_date.strftime('%Y-%m-%d')
            themes.append(ThemeData(date=iso_date_str, themes=special_themes))

        return themes

    def __get_theme_days(self, years: list[int]) -> dict[date, list[str]]:
        if not hasattr(self, 'theme_configs'):
            self.theme_configs = self.__load_configs()

        theme_days = {}
        for config in self.theme_configs:
            generator: ThemeDateGenerator = self.generator_config.get(config['generator'])
            if generator is None:
                _LOGGER.warning(f'{config} does not have a matching generator, skipping...')
                continue
            for year in years:
                date_of_theme = generator.generate(config, year)
                if date_of_theme is None:
                    continue
                themes = theme_days.get(date_of_theme) or []
                themes.append(config['theme'])
                theme_days[date_of_theme] = themes

        return theme_days

    @staticmethod
    def __load_configs() -> list:
        try:
            with open(os.path.join(os.path.dirname(__file__), 'theme_days_config.json'),
                      encoding='iso-8859-1') as f:
                configs = json.load(f)
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid json in special themes config, %s", err)

        return configs
