"""
Support for Swedish calendar including holidays and name days.

For more details about this platform, please refer to the documentation at
https://github.com/Miicroo/ha-swedish_calendar
"""
import logging
from typing import Any

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN, SENSOR_TYPES, CONF_EXCLUDE
from .provider import CalendarDataCoordinator
from .types import SwedishCalendar

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the calendar sensor."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    conf = hass.data[DOMAIN]["conf"]

    included_sensor_types = [sensor_type for sensor_type in SENSOR_TYPES if sensor_type not in conf[CONF_EXCLUDE]]

    devices = []
    for sensor_type in included_sensor_types:
        name = SENSOR_TYPES[sensor_type][0]
        icon = SENSOR_TYPES[sensor_type][1]
        state_key = SENSOR_TYPES[sensor_type][2]
        default_value = SENSOR_TYPES[sensor_type][3]
        attribution = SENSOR_TYPES[sensor_type][4]
        devices.append(
            SwedishCalendarSensor(sensor_type, name, icon, state_key, default_value, attribution, coordinator))

    async_add_entities(devices)


class SwedishCalendarSensor(CoordinatorEntity):

    def __init__(self, sensor_type: str, name: str, icon: str, state_key: str, default_value: Any, attribution: str,
                 coordinator: CalendarDataCoordinator):
        super().__init__(coordinator)
        self.type = sensor_type
        self._name = name
        self._icon = icon
        self.state_key = state_key
        self._default_value = default_value
        self._attribution = attribution
        self.entity_id = 'sensor.swedish_calendar_{}'.format(sensor_type)
        self._handle_coordinator_update()  # Set initial state

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return 'sensor.{}'.format(slugify(self._name))

    @property
    def state(self):
        return self._state if self._state else self._default_value

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def icon(self):
        return self._icon

    @property
    def extra_state_attributes(self):
        return {
            ATTR_ATTRIBUTION: self._attribution,
        }

    @property
    def unit_of_measurement(self):
        return None

    @property
    def hidden(self):
        """Return hidden if it should not be visible in GUI"""
        return self._state is None or self._state == ""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        swedish_calendar: SwedishCalendar = self.coordinator.data
        if swedish_calendar is not None:
            state = swedish_calendar.get_value_by_attribute(self.state_key)
            if isinstance(state, list):
                state = ",".join(state)
            self._state = state
