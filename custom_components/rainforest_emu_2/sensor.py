"""Support for Rainforest EMU-2."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_NAME,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_HW_VERSION,
    ATTR_SW_VERSION,
    UnitOfEnergy.KILO_WATT_HOUR,
    UnitOfPower.KILO_WATT,
    CURRENCY_DOLLAR,
)

from .const import DOMAIN, DEVICE_NAME

# Only allow a single update at a time as they all go through the same serial interface
PARALLEL_UPDATES = 1

async def async_setup_entry(hass, config_entry, async_add_entities):
    device = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        Emu2ActivePowerSensor(device),
        Emu2CurrentPriceSensor(device),
        Emu2CurrentPeriodUsageSensor(device),
        Emu2SummationDeliveredSensor(device),
        Emu2SummationReceivedSensor(device),
    ]
    async_add_entities(entities)


class SensorEntityBase(SensorEntity):
    should_poll = True

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
            ATTR_SW_VERSION: self._device.device_sw_version,
        }

    @property
    def available(self) -> bool:
        return self._device.connected

    async def async_added_to_hass(self):
        self._device.register_callback(self._observe, self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._device.remove_callback(self._observe, self.async_write_ha_state)


class Emu2ActivePowerSensor(SensorEntityBase):
    should_poll = False

    def __init__(self, device):
        super().__init__(device, "InstantaneousDemand")

        self._attr_unique_id = f"{self._device.device_id}_power"
        self._attr_name = f"{self._device.device_name} Power"

        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.KILO_WATT

    @property
    def state(self):
        return self._device.power


class Emu2CurrentPriceSensor(SensorEntityBase):
    def __init__(self, device):
        super().__init__(device, "PriceCluster")

        self._attr_unique_id = f"{self._device.device_id}_current_price"
        self._attr_name = f"{self._device.device_name} Current Price"

        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = (
            f"{CURRENCY_DOLLAR}/{UnitOfEnergy.KILO_WATT_HOUR}"
        )

    async def async_update(self):
        await self._device._emu2.get_current_price()

    @property
    def state(self):
        return self._device.current_price


class Emu2CurrentPeriodUsageSensor(SensorEntityBase):
    def __init__(self, device):
        super().__init__(device, "CurrentPeriodUsage")

        self._attr_unique_id = f"{self._device.device_id}_current_period_usage"
        self._attr_name = f"{self._device.device_name} Current Period Usage"

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    async def async_update(self):
        await self._device._emu2.get_current_period_usage()

    @property
    def state(self):
        return self._device.current_usage

    @property
    def last_reset(self):
        return self._device.current_usage_start_date


class Emu2SummationDeliveredSensor(SensorEntityBase):
    should_poll = False

    def __init__(self, device):
        super().__init__(device, "CurrentSummationDelivered")

        self._attr_unique_id = f"{self._device.device_id}_summation_delivered"
        self._attr_name = f"{self._device.device_name} Summation Delivered"

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    @property
    def state(self):
        return self._device.summation_delivered


class Emu2SummationReceivedSensor(SensorEntityBase):
    should_poll = False

    def __init__(self, device):
        # The received information is part of the Summation Delivered XML packet
        super().__init__(device, "CurrentSummationDelivered")

        self._attr_unique_id = f"{self._device.device_id}_summation_received"
        self._attr_name = f"{self._device.device_name} Summation Received"

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    @property
    def state(self):
        return self._device.summation_received
