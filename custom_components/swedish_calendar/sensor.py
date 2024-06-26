"""
Support for Swedish calendar including holidays and name days.

For more details about this platform, please refer to the documentation at
https://github.com/Miicroo/ha-swedish_calendar
"""
from datetime import date
import logging

from homeassistant import config_entries
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_EXCLUDE, DOMAIN, SENSOR_TYPES
from .coordinator import CalendarDataCoordinator
from .types import SensorConfig, SwedishCalendar

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    entry_conf = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_conf["coordinator"]
    conf = entry_conf["conf"]

    included_sensor_types: list[str] = [sensor_type
                                        for sensor_type in SENSOR_TYPES
                                        if sensor_type not in conf[CONF_EXCLUDE]]

    devices = [SwedishCalendarSensor(sensor_type, SENSOR_TYPES[sensor_type], coordinator)
               for sensor_type in included_sensor_types]
    async_add_entities(devices, update_before_add=True)


class SwedishCalendarSensor(CoordinatorEntity):

    def __init__(self, sensor_type: str, sensor_config: SensorConfig, coordinator: CalendarDataCoordinator):
        super().__init__(coordinator)
        self.entity_id = f'sensor.swedish_calendar_{sensor_type}'
        self._sensor_config = sensor_config
        self._state = None

    @property
    def name(self):
        return self._sensor_config.friendly_name

    @property
    def unique_id(self):
        return f'sensor.{slugify(self._sensor_config.friendly_name)}'

    @property
    def state(self):
        return self._state if self._state else self._sensor_config.default_value

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def icon(self):
        return self._sensor_config.icon

    @property
    def extra_state_attributes(self):
        return {
            ATTR_ATTRIBUTION: self._sensor_config.attribution,
        }

    @property
    def unit_of_measurement(self):
        return None

    @property
    def hidden(self):
        """Return hidden if it should not be visible in GUI"""
        return self._state is None or self._state == ""

    async def async_added_to_hass(self):
        await super().async_added_to_hass()  # Set up coordinator listener
        self._handle_coordinator_update()  # Set initial state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        swedish_calendars: dict[date, SwedishCalendar] = self.coordinator.data
        today = date.today()
        if today in swedish_calendars:
            swedish_calendar = swedish_calendars[today]
            state = self._sensor_config.get_value_from_calendar(swedish_calendar)
            if isinstance(state, list):
                state = ",".join(state)
            elif isinstance(state, bool):
                state = 'Ja' if state else 'Nej'
            self._state = state
            super()._handle_coordinator_update()
