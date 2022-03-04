"""The Rainforest EMU-2 integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    Platform,
    EVENT_HOMEASSISTANT_STOP,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_HW_VERSION,
    ATTR_SW_VERSION
)

from .emu2 import Emu2
from .emu2_entities import (
    CurrentSummationDelivered,
    InstantaneousDemand
)
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
    emu2 = RainforestEmu2Device(hass, entry.data)

    async def async_shutdown(event):
        # Handle shutdown
        emu2.stop()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = emu2

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    emu2 = hass.data[DOMAIN][entry.entry_id]
    emu2.stop()

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

        self._power = 0.0
        self._summation_delivered = 0.0

        self._emu = Emu2(properties[ATTR_DEVICE_PATH])
        self._emu.register_callback(self.process_update)

        self._serial_loop_task = self._hass.loop.create_task(
            self._emu.serial_read()
        )

    def stop(self):
        """Close resources."""
        if self._emu:
            self._emu.stop_serial()

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when serial data received."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    def process_update(self, type, response) -> None:
        if type == 'InstantaneousDemand':
            self._power = self._emu.get_data(InstantaneousDemand).reading
        elif type == 'CurrentSummationDelivered':
            self._summation_delivered = self._emu.get_data(CurrentSummationDelivered).summation_delivered

        for callback in self._callbacks:
            callback()            

    @property
    def device_id(self) -> str:
        return f"{DEVICE_ID}_{self._properties[ATTR_DEVICE_MAC_ID]}"

    @property
    def device_name(self) -> str:
        return DEVICE_NAME

    @property
    def device_manufacturer(self) -> str:
        return self._properties[ATTR_MANUFACTURER]

    @property
    def device_model(self) -> str:
        return self._properties[ATTR_MODEL]

    @property
    def device_sw_version(self) -> str:
        return self._properties[ATTR_SW_VERSION]

    @property
    def device_hw_version(self) -> str:
        return self._properties[ATTR_HW_VERSION]

    @property
    def power(self) -> float:
        return self._power

    @property
    def connected(self) -> bool:
        return self._emu.connected
