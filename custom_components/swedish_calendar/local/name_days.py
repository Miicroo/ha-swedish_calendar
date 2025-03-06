import json
import logging
import os

_LOGGER = logging.getLogger(__name__)


class NameDayProvider:

    def __init__(self):
        pass

    def get_names(self, month_and_day: str) -> list[str]:
        return self._get_name_days().get(month_and_day) or []

    def _get_name_days(self) -> dict[str, list[str]]:
        if not hasattr(self, 'name_days'):
            name_days = self.__load_name_days()
            self.name_days: dict[str, list[str]] = {}

            for month in name_days.keys():
                for (day, names) in name_days[month].items():
                    self.name_days[f'{month}-{day}'] = names.split(', ')

        return self.name_days

    @staticmethod
    def __load_name_days() -> dict[str, dict[str, str]]:
        try:
            with open(os.path.join(os.path.dirname(__file__), 'name_days.json')) as f:
                name_days = json.load(f)
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid json in name days file, %s", err)

        return name_days
