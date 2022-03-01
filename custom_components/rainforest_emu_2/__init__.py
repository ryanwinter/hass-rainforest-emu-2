"""The Rainforest EMU-2 integration."""
from __future__ import annotations

import asyncio
import logging

from serial import SerialException
import serial_asyncio

import xml.etree.ElementTree as ET

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, CONF_PORT, Platform

from .const import DOMAIN, DEVICE_ID, DEVICE_NAME

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [Platform.SENSOR]

SERIAL_BAUD = 115200
SERIAL_BYTESIZE = serial_asyncio.serial.EIGHTBITS
SERIAL_PARITY = serial_asyncio.serial.PARITY_NONE
SERIAL_STOPBITS = serial_asyncio.serial.STOPBITS_ONE
SERIAL_XONXOFF = False
SERIAL_RTSCTR = False
SERIAL_DSRDTR = False

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rainforest EMU-2 from a config entry."""
    port = entry.data[CONF_PORT]

    device = RainforestEmu2Device(hass, port)

    async def async_shutdown(event):
        """Handle shutdown tasks."""
        device.stop()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = device

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    device = hass.data[DOMAIN][entry.entry_id]
    device.stop()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok    

class RainforestEmu2Device:
    def __init__(
        self,
        hass : HomeAssistant,
        port
    ):
        self._hass = hass
        self._port = port

        self._id = ''
        self._device_mac_id = ''
        self._meter_mac_id = ''
        self._power = 0.0

        self._callbacks = set()

        self._serial_loop_task = self._hass.loop.create_task(
            self.serial_read(self._port)
        )

    async def serial_read(self, device, **kwargs):
        self._connected = False
        xml_str = ''
        while True:
            try:
                reader, _ = await serial_asyncio.open_serial_connection(
                    url=device,
                    baudrate=SERIAL_BAUD,
                    bytesize=SERIAL_BYTESIZE,
                    parity=SERIAL_PARITY,
                    stopbits=SERIAL_STOPBITS,
                    xonxoff=SERIAL_XONXOFF,
                    rtscts=SERIAL_RTSCTR,
                    dsrdtr=SERIAL_DSRDTR,
                    **kwargs,
                )

            except SerialException as exc:
                if self._connected:
                    self._connected = False
                    _LOGGER.exception(
                        "Unable to connect to the serial device %s: %s. Will retry",
                        device,
                        exc,
                    )
                await self.handle_error()
            else:
                self._connected = True
                _LOGGER.info("Serial device %s connected", device)

                while True:
                    try:
                        line = await reader.readline()
                    except SerialException as exc:
                        _LOGGER.exception(
                            "Error while reading serial device %s: %s", device, exc
                        )
                        await self.handle_error()
                        break
                    else:
                        line = line.decode("utf-8").strip()
                        _LOGGER.debug("Received: %s", line)

                        # clear the string when detecting the open
                        if line == '<InstantaneousDemand>':
                            xml_str = ''
                        
                        xml_str += line
                        
                        # process the string when detecting the close
                        if line == '</InstantaneousDemand>':
                            await self.process_update(xml_str)

    def stop(self) -> None:
        """Close resources."""
        if self._serial_loop_task:
            self._serial_loop_task.cancel()

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when serial data received."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    async def process_update(self, xml_str) -> None:
        """Process data and notify"""
        root = ET.fromstring(xml_str)

        # Extract ids
        self._device_mac_id = root.find('DeviceMacId').text
        self._meter_mac_id = root.find('MeterMacId').text

        # Extract power values        
        demand = int(root.find('Demand').text, 16)
        demand = -(demand & 0x80000000) | (demand & 0x7fffffff)
        multiplier = int(root.find('Multiplier').text, 16)
        divisor = int(root.find('Divisor').text, 16)

        # Calculator power
        if (divisor != 0):
            self._power = demand * multiplier / divisor

        for callback in self._callbacks:
            callback()

    async def handle_error(self) -> None:
        """Handle error for serial connection."""
        self._state = None
        self._attributes = None
        self.async_write_ha_state()
        await asyncio.sleep(5)

    @property
    def device_id(self) -> str:
        return DEVICE_ID

    @property
    def device_name(self) -> str:
        return DEVICE_NAME

    @property
    def device_mac_id(self) -> str:
        return self._device_mac_id

    @property
    def meter_mac_id(self) -> str:
        return self._meter_mac_id

    @property
    def power(self) -> float:
        return self._power

    @property
    def connected(self) -> bool:
        return self._connected
