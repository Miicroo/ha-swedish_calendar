"""Binary sensor for Swedish bridge days."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BRIDGE_DAY, BRIDGE_DAY_NAME, CONF_EXCLUDE, DOMAIN
from .coordinator import CalendarDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add the bridge day sensor unless excluded in the integration settings."""
    if BRIDGE_DAY not in entry.data[CONF_EXCLUDE]:
        async_add_entities([BridgeDayBinarySensor(hass.data[DOMAIN][entry.entry_id]["coordinator"])])


class BridgeDayBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Whether today's working day falls between two work-free days."""

    _attr_unique_id = BRIDGE_DAY
    _attr_has_entity_name = True
    _attr_translation_key = BRIDGE_DAY
    _attr_icon = "mdi:bridge"

    # Home Assistant versions without translated entity names use the English label.
    if not hasattr(BinarySensorEntity, "translation_key"):
        _attr_name = BRIDGE_DAY_NAME

    def __init__(self, coordinator: CalendarDataCoordinator) -> None:
        super().__init__(coordinator)
        self.entity_id = f"binary_sensor.{DOMAIN}_{BRIDGE_DAY}"

    @property
    def is_on(self) -> bool | None:
        """Return the bridge day status from the latest coordinator update."""
        return self.coordinator.bridge_day
