"""
Support for Swedish calendar including holidays and name days.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.swedish_calendar/
"""
import asyncio
import logging

from random import randrange

import aiohttp
import async_timeout
import os
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = 'Data provided by api.dryg.net'
CONF_ATTRIBUTION_SPECIAL_THEMES = 'Data provided by https://temadagar.se. For full calendar, see https://temadagar.se/kop-temadagar-kalender/'
CONF_EXCLUDE = 'exclude'
CONF_SPECIAL_THEMES_DIR = 'special_themes_dir'

SPECIAL_THEMES_PATH = 'specialThemes.json'

SENSOR_TYPES = {
    'date': ['Date', 'mdi:calendar-today', 'datum', 'unknown'],
    'weekday': ['Week day', 'mdi:calendar-today', 'veckodag', 'unknown'],
    'workfree_day': ['Workfree day', 'mdi:beach', 'arbetsfri dag', 'Nej'],
    'red_day': ['Red Day', 'mdi:pine-tree', 'röd dag', 'Nej'],
    'week': ['Week', 'mdi:calendar-week', 'vecka', 'unknown'],
    'day_of_week': ['Day of week', 'mdi:calendar-range', 'dag i vecka', 'unknown'],
    'eve': ['Eve', 'mdi:ornament-variant', 'helgdagsafton', 'unknown'],
    'holiday': ['Holiday', 'mdi:ornament', 'helgdag', 'unknown'],
    'day_before_workfree_holiday': ['Day before workfree holiday', 'mdi:clock-fast', 'dag före arbetsfri helgdag', 'Nej'],
    'name_day': ['Names celebrated', 'mdi:human-handsup', 'namnsdag', 'unknown'],
    'flag_day': ['Reason for flagging', 'mdi:flag', 'flaggdag', 'unknown'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SPECIAL_THEMES_DIR, default=''): cv.string,
    vol.Optional(CONF_EXCLUDE, default=[]):
        vol.All(cv.ensure_list, vol.Length(min=0), [vol.In(SENSOR_TYPES)]),
})

VERSION = '0.0.4'

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the calendar sensor."""

    devices = []
    if config[CONF_SPECIAL_THEMES_DIR]:
        specialThemesPath = os.path.join(config[CONF_SPECIAL_THEMES_DIR], SPECIAL_THEMES_PATH)
        if os.path.exists(specialThemesPath):
            themeSensor = SpecialThemesSensor(hass, specialThemesPath)
            async_add_entities([themeSensor])
            await themeSensor.fetching_data()

    included_sensor_types = [sensor_type for sensor_type in SENSOR_TYPES if sensor_type not in config[CONF_EXCLUDE]]

    for sensor_type in included_sensor_types:
        name = SENSOR_TYPES[sensor_type][0]
        icon = SENSOR_TYPES[sensor_type][1]
        state_key = SENSOR_TYPES[sensor_type][2]
        default_value = SENSOR_TYPES[sensor_type][3]
        devices.append(SwedishCalendarSensor(sensor_type, name, icon, state_key, default_value))

    async_add_entities(devices)

    calendar = SwedishCalendarData(hass, devices)
    await calendar.fetching_data()


class SwedishCalendarSensor(Entity):
    """Representation of a calendar sensor."""

    def __init__(self, sensor_type, name, icon, state_key, default_value):
        """Initialize the sensor."""
        self.type = sensor_type
        self._name = name
        self._icon = icon
        self.state_key = state_key
        self._default_value = default_value
        self._state = None
        self.entity_id = 'sensor.swedish_calendar_{}'.format(sensor_type)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state if self._state else self._default_value

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def icon(self):
        return self._icon

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return None

    @property
    def hidden(self):
        """Return hidden if it should not be visible in GUI"""
        return self._state is None or self._state == ""

class SwedishCalendarData:
    """Get the latest data and updates the states."""

    def __init__(self, hass, devices):
        """Initialize the data object."""
        self._base_url = 'https://api.dryg.net/dagar/v2.1/'
        self.devices = devices
        self.data = {}
        self.hass = hass

    async def fetching_data(self, *_):
        """Get the latest data from the api."""
        import json

        def retry(err: str):
            """Retry in an hour."""
            minutes = 60
            _LOGGER.error("Retrying in %i minutes: %s", minutes, err)
            async_call_later(self.hass, minutes*60, self.fetching_data)

        def get_url(base_url):
            return base_url + dt_util.now().strftime('%Y/%m/%d')

        def get_seconds_until_midnight():
            one_day_in_seconds = 24 * 60 * 60

            now = dt_util.now()
            total_seconds_passed_today = (now.hour*60*60) + (now.minute*60) + now.second

            return one_day_in_seconds - total_seconds_passed_today
        try:
            websession = async_get_clientsession(self.hass)
            with async_timeout.timeout(10, loop=self.hass.loop):
                resp = await websession.get(get_url(self._base_url))
            if resp.status != 200:
                retry('{} returned {}'.format(resp.url, resp.status))
                return
            response_data = await resp.text()

        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            retry(err)
            return

        try:
            self.data = json.loads(response_data)['dagar'][0]
        except json.JSONDecodeError as err:
            retry(err)
            return

        await self.updating_devices()
        async_call_later(self.hass, get_seconds_until_midnight(), self.fetching_data)

    async def updating_devices(self, *_):
        """Find the current data from self.data."""
        if not self.data:
            return

        tasks = []
        for device in self.devices:
            json_key = device.state_key
            new_state = None

            if json_key in self.data:
                new_state = self.data[json_key]

            # pylint: disable=protected-access
            if new_state != device._state:
                if type(new_state) is list:
                    new_state = ",".join(new_state)
                device._state = new_state
                tasks.append(device.async_update_ha_state())

        if tasks:
            await asyncio.wait(tasks, loop=self.hass.loop)

class SpecialThemesSensor(Entity):

    def __init__(self, hass, theme_path):
        self.hass = hass
        self._state = None
        self.entity_id = 'sensor.swedish_calendar_theme_day'
        self._theme_path = theme_path

    @property
    def name(self):
        return 'Special Themes'

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def should_poll(self):
        return False

    @property
    def icon(self):
        return None

    @property
    def device_state_attributes(self):
        return {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION_SPECIAL_THEMES
        }

    @property
    def unit_of_measurement(self):
        return None

    @property
    def hidden(self):
        """Return hidden if it should not be visible in GUI"""
        return self._state is None or self._state == ""

    async def fetching_data(self, *_):
        import json

        def retry(err: str):
            minutes = 60
            _LOGGER.error("Retrying in %i minutes: %s", minutes, err)
            async_call_later(self.hass, minutes*60, self.fetching_data)

        def get_seconds_until_midnight():
            one_day_in_seconds = 24 * 60 * 60

            now = dt_util.now()
            total_seconds_passed_today = (now.hour*60*60) + (now.minute*60) + now.second

            return one_day_in_seconds - total_seconds_passed_today

        try:
            with open(self._theme_path, 'r') as dataFile:
                data = json.load(dataFile)
        except json.JSONDecodeError as err:
            retry(err)
            return

        specialThemes = data['themeDays']
        date = dt_util.start_of_local_day()
        dateStr = date.strftime('%Y%m%d')

        if dateStr in specialThemes:
            events = map(lambda x: x['event'], specialThemes[dateStr])
            self._state = ",".join(events)

            tasks = [self.async_update_ha_state()]
            await asyncio.wait(tasks, loop=self.hass.loop)

        async_call_later(self.hass, get_seconds_until_midnight(), self.fetching_data)
