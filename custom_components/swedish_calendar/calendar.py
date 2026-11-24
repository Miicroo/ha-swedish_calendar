from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    BRIDGE_DAY,
    CONF_CALENDAR,
    CONF_INCLUDE,
    DOMAIN,
    DOMAIN_FRIENDLY_NAME,
    SENSOR_TYPES,
)
from .coordinator import CalendarDataCoordinator
from .types import SensorConfig, SwedishCalendar
from .utils import async_bridge_day_name

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
):
    """Set up the calendar if any event types are selected."""
    entry_conf = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_conf["coordinator"]
    conf = entry_conf["conf"][CONF_CALENDAR]

    sensor_configs = [SENSOR_TYPES[sensor_type]
                      for sensor_type in SENSOR_TYPES
                      if sensor_type in conf[CONF_INCLUDE]]

    bridge_day_name = await async_bridge_day_name(hass) if BRIDGE_DAY in conf[CONF_INCLUDE] else None
    if sensor_configs or bridge_day_name:
        async_add_entities([SwedishCalendarEntity(sensor_configs, coordinator, bridge_day_name)], update_before_add=True)


class SwedishCalendarEntity(CalendarEntity, CoordinatorEntity):
    """The Swedish calendar's selected all-day events."""

    def __init__(self, sensor_configs: list[SensorConfig], coordinator: CalendarDataCoordinator, bridge_day_name: str | None) -> None:
        super().__init__(coordinator)
        self._sensor_configs = sensor_configs
        self._bridge_day_name = bridge_day_name
        self._attr_name = DOMAIN_FRIENDLY_NAME
        self._events: list[SwedishCalendarEvent] = []

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f'calendar.{DOMAIN}'

    @property
    def should_poll(self):
        return False

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        for event in self._events:
            if not event.has_passed():
                return event.to_hass_calendar_event()

        return None

    async def async_get_events(
            self,
            hass: HomeAssistant,
            start_date: datetime,
            end_date: datetime,
    ) -> list[CalendarEvent]:
        # An all-day event overlaps the query from local midnight until the next local midnight.
        start = dt_util.as_local(start_date)
        end = dt_util.as_local(end_date)
        if dt_util.as_utc(end) <= dt_util.as_utc(start):
            return []
        return [event.to_hass_calendar_event()
                for event in self._events
                if start.date() <= event.date and dt_util.start_of_local_day(event.date) < end
                ]

    async def async_added_to_hass(self):
        await super().async_added_to_hass()  # Set up coordinator listener
        self._handle_coordinator_update()  # Set initial state

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        swedish_calendars: dict[date, SwedishCalendar] = self.coordinator.data
        events = []
        for event_date in swedish_calendars.keys():
            swedish_calendar = swedish_calendars[event_date]

            for sensor_config in self._sensor_configs:
                sensor_value = sensor_config.get_value_from_calendar(swedish_calendar)
                description = SwedishCalendarEntity._describe(sensor_value, sensor_config)
                if description:
                    event = SwedishCalendarEvent(isodate=event_date, description=description)
                    events.append(event)

            if self._bridge_day_name and self.coordinator.is_bridge_day(event_date):
                events.append(SwedishCalendarEvent(event_date, self._bridge_day_name))

        self._events = sorted(events, key=lambda event: event.date)
        super()._handle_coordinator_update()

    @staticmethod
    def _describe(value: Any, item: SensorConfig) -> Any:
        if value is None:
            return None
        elif isinstance(value, bool):
            return SwedishCalendarEntity._describe_bool(value, item.friendly_name)
        elif isinstance(value, int):
            return SwedishCalendarEntity._describe_int(value, item.friendly_name)
        elif isinstance(value, list):
            return ','.join(value)
        elif isinstance(value, dict):
            return ','.join([SwedishCalendarEntity._describe_any(value[key], key) for key in value])
        else:
            return value

    @staticmethod
    def _describe_bool(value: bool, friendly_name: str) -> str | None:
        return friendly_name if value else None

    @staticmethod
    def _describe_int(value: int, friendly_name: str) -> str:
        return f'{friendly_name}: {value}'

    @staticmethod
    def _describe_any(value: Any, friendly_name: str) -> str:
        return f'{friendly_name}: {value}'


class SwedishCalendarEvent:
    def __init__(self, isodate: date, description: str):
        self.date = isodate
        self.description = description

    def to_hass_calendar_event(self) -> CalendarEvent:
        end = self.date + timedelta(days=1)
        return CalendarEvent(start=self.date, end=end, summary=str(self.description), description=str(self.description))

    def has_passed(self) -> bool:
        return self.date < dt_util.now().date()
