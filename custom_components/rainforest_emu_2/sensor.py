"""Support for Rainforest EMU-2."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

ATTR_MANUFACTURER="Rainforest"
ATTR_MODEL="EMU-2"

async def async_setup_entry(hass, config_entry, async_add_entities):
    device = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    entities.append(DemandSensor(device))
    async_add_entities(entities)

class DemandSensor(SensorEntity):
    should_poll = False

    def __init__(self, device):
        self._device = device

        self._attr_unique_id = f"{self._device.device_id}_power"
        self._attr_name = f"{self._device.device_name} Power"

        self._state = 10

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device.device_id)},
            name=self._device.device_name,
            manufacturer=ATTR_MANUFACTURER,
            model=ATTR_MODEL,
        )    

    @property
    def available(self) -> bool:
        return self._device.connected

    async def async_added_to_hass(self):
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._device.remove_callback(self.async_write_ha_state)    

    @property
    def state(self):
        return self._device.power
