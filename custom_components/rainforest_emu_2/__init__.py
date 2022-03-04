"""The Rainforest EMU-2 integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    Platform,
    EVENT_HOMEASSISTANT_STOP, 
    CONF_PORT,
    CONF_DEVICE_ID
)

from .emu2 import Emu2
from .emu2_entities import (
    InstantaneousDemand
)
from .const import (
    DOMAIN, 
    DEVICE_ID, 
    DEVICE_NAME,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rainforest EMU-2 from a config entry."""
    device_path = entry.data[CONF_PORT]
    device_id = entry.data[CONF_DEVICE_ID]

    emu2 = RainforestEmu2Device(hass, device_path, device_id)

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
        device_path,
        device_id,
    ):
        self._hass = hass
        self._device_path = device_path
        self._device_id = device_id

        self._power = 0.0
        self._callbacks = set()

        self._emu = Emu2(device_path)
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

        for callback in self._callbacks:
            callback()            

    @property
    def device_id(self) -> str:
        return f"{DEVICE_ID}_{self._device_id}"

    @property
    def device_name(self) -> str:
        return DEVICE_NAME

    @property
    def power(self) -> float:
        return self._power

    @property
    def connected(self) -> bool:
        self._emu.connected
