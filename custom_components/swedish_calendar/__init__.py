import logging
import os
import voluptuous as vol

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform

from .provider import CalendarDataCoordinator
from .const import DOMAIN, CONF_SPECIAL_THEMES_DIR, SPECIAL_THEMES_PATH, CONF_EXCLUDE, SENSOR_TYPES

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_SPECIAL_THEMES_DIR, default=''): cv.string,
                vol.Optional(CONF_EXCLUDE, default=[]):
                    vol.All(cv.ensure_list, vol.Length(min=0), [vol.In(SENSOR_TYPES)]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    conf = config[DOMAIN]
    special_themes_path = None
    if conf[CONF_SPECIAL_THEMES_DIR]:
        special_themes_path = os.path.join(conf[CONF_SPECIAL_THEMES_DIR], SPECIAL_THEMES_PATH)
        if not os.path.exists(special_themes_path):
            _LOGGER.warning("Special themes is configured but file cannot be found at %s, please check your config",
                            special_themes_path)

    coordinator = CalendarDataCoordinator(hass, special_themes_path)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    hass.data[DOMAIN] = {
        "conf": conf,
        "coordinator": coordinator,
    }
    hass.async_create_task(async_load_platform(hass, "sensor", DOMAIN, {}, conf))
    return True
