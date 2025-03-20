import json
import logging
import os

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
CUSTOM_DATA_DIRECTORY = "swedish_calendar/themes"


class ThemeConfigLoader:

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._configs = None

    def get_configs(self, reload=False) -> list:
        if self._configs is None or reload:
            self._configs = self._load_configs()

        return self._configs

    def _load_configs(self) -> list:
        configs = self._load_static_configs()
        configs.extend(self._load_custom_configs())

        return configs

    @staticmethod
    def _load_static_configs() -> list:
        return ThemeConfigLoader._load_json(os.path.join(os.path.dirname(__file__), 'theme_days_config.json'))

    def _load_custom_configs(self) -> list:
        configs = []
        data_dir = os.path.join(self.hass.config.config_dir, CUSTOM_DATA_DIRECTORY)

        if os.path.exists(data_dir):
            _LOGGER.debug(f'Loading custom themes from {data_dir}')

            for root, _, files in os.walk(data_dir, topdown=False):
                for file_name in files:
                    if file_name.endswith('.json'):
                        custom_themes_path = os.path.join(root, file_name)
                        custom_themes = self._load_json(custom_themes_path)

                        _LOGGER.info(f'Loaded {len(custom_themes)} custom themes from {custom_themes_path}')

                        configs.extend(custom_themes)
        return configs

    @staticmethod
    def _load_json(path: str) -> list:
        configs = []
        try:
            with open(path, encoding='iso-8859-1') as f:
                configs = json.load(f)
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid json in special themes config, %s", err)

        return configs
