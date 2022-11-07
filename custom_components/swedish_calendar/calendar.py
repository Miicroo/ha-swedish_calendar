from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Any, Dict

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES, CONF_CALENDAR, CONF_INCLUDE, DOMAIN_FRIENDLY_NAME
from .provider import CalendarDataCoordinator
from .types import SwedishCalendar, SensorConfig
from .utils import DateUtils

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None) -> None:
    """Set up the calendar sensor."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    conf = hass.data[DOMAIN]["conf"][CONF_CALENDAR]

    sensor_configs = [SENSOR_TYPES[sensor_type]
                      for sensor_type in SENSOR_TYPES
                      if sensor_type in conf[CONF_INCLUDE]]

    if len(sensor_configs) > 0:
        async_add_entities([SwedishCalendarEntity(sensor_configs, coordinator)])


class SwedishCalendarEntity(CalendarEntity, CoordinatorEntity):
    """Representation of a Demo Calendar element."""

    def __init__(self, sensor_configs: List[SensorConfig], coordinator: CalendarDataCoordinator) -> None:
        super().__init__(coordinator)
        # Sort sensor_configs so that calendar events are always shown in the same order
        self._sensor_configs = sorted(sensor_configs, key=lambda c: c.swedish_calendar_attribute)
        self._attr_name = DOMAIN_FRIENDLY_NAME
        self._events: List[SwedishCalendarEvent] = []

    @property
    def should_poll(self):
        return False

    @property
    def event(self) -> CalendarEvent:
        """Return the next upcoming event."""
        sorted_events: List[SwedishCalendarEvent] = sorted(self._events, key=lambda e: e.date)
        for event in sorted_events:
            if not event.has_passed():
                return event.to_hass_calendar_event()

        return None

    async def async_get_events(
            self,
            hass: HomeAssistant,
            start_date: datetime,
            end_date: datetime,
    ) -> list[CalendarEvent]:
        return [event.to_hass_calendar_event()
                for event in self._events
                if DateUtils.in_range(str(event.date), start_date.date(), end_date.date())
                ]

    async def async_added_to_hass(self):
        await super().async_added_to_hass()  # Set up coordinator listener
        self._handle_coordinator_update()  # Set initial state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        swedish_calendars: Dict[date, SwedishCalendar] = self.coordinator.data
        events = []
        for event_date in swedish_calendars.keys():
            swedish_calendar = swedish_calendars[event_date]

            for sensor_config in self._sensor_configs:
                sensor_value = sensor_config.get_value_from_calendar(swedish_calendar)
                description = SwedishCalendarEntity._describe(sensor_value, sensor_config)
                if description:
                    event = SwedishCalendarEvent(isodate=event_date, description=description)
                    events.append(event)

        self._events = events

    @staticmethod
    def _describe(value: Any, item: SensorConfig) -> Any:
        if value is None:
            return None
        elif isinstance(value, bool):
            return SwedishCalendarEntity._describe_bool(value, item.friendly_name)
        elif isinstance(value, int):
            return SwedishCalendarEntity._describe_int(value, item.friendly_name)
        else:
            return value

    @staticmethod
    def _describe_bool(value: bool, friendly_name: str) -> Optional[str]:
        return friendly_name if value else None

    @staticmethod
    def _describe_int(value: int, friendly_name: str) -> str:
        return f'{friendly_name}: {value}'


class SwedishCalendarEvent:
    def __init__(self, isodate: date, description: str):
        self.date = isodate
        self.description = description

    def to_hass_calendar_event(self) -> CalendarEvent:
        end = self.date + timedelta(days=1)
        return CalendarEvent(start=self.date, end=end, summary=self.description, description=self.description)

    def has_passed(self) -> bool:
        return self.date < date.today()
