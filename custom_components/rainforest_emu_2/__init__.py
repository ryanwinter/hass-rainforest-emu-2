"""The Rainforest EMU-2 integration."""
from __future__ import annotations

import asyncio
import datetime
import logging
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt
from homeassistant.const import (
    Platform,
    EVENT_HOMEASSISTANT_STOP,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_HW_VERSION,
    ATTR_SW_VERSION,
    CONF_HOST,
    CONF_PORT
)

from .emu2 import Emu2
from .const import (
    DOMAIN, 
    DEVICE_ID,
    DEVICE_NAME,
    ATTR_DEVICE_PATH,
    ATTR_DEVICE_MAC_ID
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rainforest EMU-2 from a config entry."""
    emu2device = RainforestEmu2Device(hass, entry.data)

    async def async_shutdown(event):
        # Handle shutdown
        await emu2device.stop()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = emu2device
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    emu2device = hass.data[DOMAIN][entry.entry_id]
    await emu2device.stop()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok    

class RainforestEmu2Device:
    def __init__(
        self,
        hass : HomeAssistant,
        properties
    ):
        self._hass = hass
        self._properties = properties
        self._callbacks = set()

        self._power = None
       
        self._summation_delivered = None
        self._summation_received = None
        self._current_price = None
        self._current_usage = None
        self._current_usage_start_date = dt.utc_from_timestamp(0)

        self._emu2 = Emu2(properties[ATTR_DEVICE_PATH], properties[CONF_HOST], properties[CONF_PORT])
        self._emu2.register_process_callback(self._process_update)

        self._serial_loop_task = self._hass.loop.create_task(self._emu2.serial_read())

    async def stop(self):
        self._serial_loop_task.cancel()

        try:
            await self._serial_loop_task
        except asyncio.CancelledError as ex:
            pass

        await self._emu2.close()

    def register_callback(self, type: str, callback: Callable[[], None]) -> None:
        """Register callback, called when serial data received."""
        self._callbacks.add((type, callback))

    def remove_callback(self, type: str, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard((type, callback))

    def _process_update(self, type, response) -> None:
    
        if type == 'InstantaneousDemand':
            self._power = response.reading

        elif type == 'CurrentPeriodUsage':
            self._current_usage = response.reading
            self._current_usage_start_date = dt.utc_from_timestamp(response.start_date + 946713600)

        elif type == 'PriceCluster':
            self._current_price = response.price_dollars
            
        elif type == 'CurrentSummationDelivered':
            self._summation_delivered = response.delivered
            self._summation_received = response.received
        
        for callback in self._callbacks:
            if (callback[0] == type):
                callback[1]()

    @property
    def connected(self) -> bool:
        return self._emu2.connected

    @property
    def device_id(self) -> str:
        return f"{DEVICE_ID}_{self._properties[ATTR_DEVICE_MAC_ID]}"

    @property
    def device_name(self) -> str:
        return DEVICE_NAME

    @property
    def device_manufacturer(self) -> str:
        return self._properties.get(ATTR_MANUFACTURER)

    @property
    def device_model(self) -> str:
        return self._properties.get(ATTR_MODEL)

    @property
    def device_sw_version(self) -> str:
        return self._properties.get(ATTR_SW_VERSION)

    @property
    def device_hw_version(self) -> str:
        return self._properties.get(ATTR_HW_VERSION)

    @property
    def power(self) -> float:
        return self._power

    @property
    def summation_delivered(self) -> float:
        return self._summation_delivered
    
    @property
    def summation_received(self) -> float:
        return self._summation_received

    @property
    def current_price(self) -> float:
        return self._current_price

    @property
    def current_usage(self) -> float:
        return self._current_usage

    @property
    def current_usage_start_date(self) -> datetime:
        return self._current_usage_start_date
