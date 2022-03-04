"""Support for Rainforest EMU-2."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.util import dt
from homeassistant.components.sensor import (
    SensorEntity, 
    SensorStateClass, 
    SensorDeviceClass
)
from homeassistant.const import (
    ATTR_IDENTIFIERS, 
    ATTR_NAME, 
    ATTR_MANUFACTURER, 
    ATTR_MODEL,     
    ENERGY_KILO_WATT_HOUR
)
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, DEVICE_ID, DEVICE_NAME

DEVICE_INFO_MANUFACTURER = "Rainforest"
DEVICE_INFO_MODEL = "EMU-2"

async def async_setup_entry(hass, config_entry, async_add_entities):
    device = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    entities.append(Emu2PowerSensor(device))
    async_add_entities(entities)

class Emu2PowerSensor(SensorEntity):
    should_poll=False
    
    def __init__(self, device):
        self._device = device

        self._attr_unique_id = f"{self._device.device_id}_power"
        self._attr_name = f"{self._device.device_name} Power"

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_last_reset = dt.utc_from_timestamp(0)

    @property
    def device_info(self) -> DeviceInfo:
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device.device_id)},
            ATTR_NAME: DEVICE_NAME,
            ATTR_MANUFACTURER: DEVICE_INFO_MANUFACTURER,
            ATTR_MODEL: DEVICE_INFO_MODEL,
        }

    @property
    def available(self) -> bool:
#        return self._device.connected
        return True

    @property
    def state(self):
        return self._device.power

    async def async_added_to_hass(self):
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._device.remove_callback(self.async_write_ha_state)    


