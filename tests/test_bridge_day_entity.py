"""Exercise the bridge day binary sensor through native Home Assistant automations."""

from freezegun import freeze_time
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar.const import BRIDGE_DAY, DOMAIN, SENSOR_TYPES
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

ENTITY_ID = "binary_sensor.swedish_calendar_bridge_day"


async def setup_bridge_day(hass, *, excluded=False):
    """Set up in local mode without creating the existing sensors or calendar."""
    exclude = list(SENSOR_TYPES)
    if excluded:
        exclude.append(BRIDGE_DAY)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "exclude": exclude,
            "local_mode": True,
            "calendar_config": {
                "include": [],
                "days_before_today": 0,
                "days_after_today": 0,
            },
            "cache": {"enabled": False, "dir": "", "retention": 7},
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_native_trigger_and_script_condition(hass):
    """Run the editor's state trigger and condition across a real bridge day."""
    with freeze_time("2024-12-22 12:00:00") as clock:
        entry = await setup_bridge_day(hass)
        assert hass.states.get(ENTITY_ID).state == "off"
        assert hass.states.get(ENTITY_ID).attributes["friendly_name"] == "Bridge day"
        assert er.async_get(hass).async_get(ENTITY_ID).unique_id == BRIDGE_DAY

        events = []
        hass.bus.async_listen("bridge_day_matched", events.append)
        assert await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "check_bridge_day": {
                        "sequence": [
                            {
                                "condition": "state",
                                "entity_id": ENTITY_ID,
                                "state": "on",
                            },
                            {"event": "bridge_day_matched"},
                        ]
                    }
                }
            },
        )
        assert await async_setup_component(
            hass,
            "automation",
            {
                "automation": [
                    {
                        "alias": "Bridge day starts",
                        "trigger": {
                            "platform": "state",
                            "entity_id": ENTITY_ID,
                            "from": "off",
                            "to": "on",
                        },
                        "action": {"service": "script.check_bridge_day"},
                    }
                ]
            },
        )
        await hass.async_block_till_done()
        await hass.services.async_call("script", "check_bridge_day", blocking=True)
        assert not events

        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        clock.move_to("2024-12-23 12:00:00")
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(ENTITY_ID).state == "on"
        assert len(events) == 1

        clock.move_to("2024-12-24 12:00:00")
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(ENTITY_ID).state == "off"
        assert len(events) == 1


async def test_bridge_day_can_be_excluded(hass):
    """Respect an explicitly excluded binary sensor."""
    await setup_bridge_day(hass, excluded=True)
    assert hass.states.get(ENTITY_ID) is None
    assert er.async_get(hass).async_get(ENTITY_ID) is None
