"""Support for Rainforest EMU-2."""
from __future__ import annotations

from homeassistant.core import callback
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
    ATTR_HW_VERSION,
    ATTR_SW_VERSION,
    ENERGY_KILO_WATT_HOUR,
    POWER_KILO_WATT
)

from .const import DOMAIN, DEVICE_NAME

async def async_setup_entry(hass, config_entry, async_add_entities):
    device = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        Emu2ActivePowerSensor(device),
        Emu2EnergyCurrentUsageSensor(device)
    ]
    async_add_entities(entities)

class SensorEntityBase(SensorEntity):
    should_poll = False

    def __init__(self, device, observe):
        self._device = device
        self._observe = observe

    @property
    def device_info(self):
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device.device_id)},
            ATTR_NAME: DEVICE_NAME,
            ATTR_MANUFACTURER: self._device.device_manufacturer,
            ATTR_MODEL: self._device.device_model,
            ATTR_HW_VERSION: self._device.device_hw_version,
            ATTR_SW_VERSION: self._device.device_sw_version
        }

    @property
    def available(self) -> bool:
        return self._device.connected

    async def async_added_to_hass(self):
        self._device.register_callback(self._observe, self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._device.remove_callback(self._observe, self.async_write_ha_state)

class Emu2ActivePowerSensor(SensorEntityBase):
    def __init__(self, device):
        super().__init__(device, 'InstantaneousDemand')

        self._attr_unique_id = f"{self._device.device_id}_power"
        self._attr_name = f"{self._device.device_name} Power"

        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = POWER_KILO_WATT

    @property
    def state(self):
        return self._device.power

class Emu2EnergyCurrentUsageSensor(SensorEntityBase):
    should_poll = True
    
    def __init__(self, device):
        super().__init__(device, 'CurrentPeriodUsage')        

        self._attr_unique_id = f"{self._device.device_id}_energy_usage"
        self._attr_name = f"{self._device.device_name} Energy Usage"

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def update(self):
        self._device._emu.get_current_period_usage()

    @property
    def state(self):
        return self._device.current_usage

    @property
    def last_reset(self):
        return self._device.current_usage_start_date
