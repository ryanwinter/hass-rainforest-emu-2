"""The Rainforest EMU-2 integration."""
import asyncio
import logging

from serial import SerialException
import serial_asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, CONF_PORT, Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = {}# [Platform.SENSOR]

ATTR_DEVICE_MAC_ID = "Device MAC ID"
ATTR_METER_MAC_ID = "Meter MAC ID"

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

    device = RainforstEmu2Device(hass, port)

    async def async_shutdown(event):
        """Handle shutdown tasks."""
        device.stop()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = device

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    device = hass.data[DOMAIN][entry.entry_id]
    device.stop()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok    

class RainforstEmu2Device:
    def __init__(
        self,
        hass : HomeAssistant,
        port
    ):
        self._hass = hass
        self._port = port
        
        self._data = {}                
        self._data[ATTR_DEVICE_MAC_ID] = None
        self._data[ATTR_METER_MAC_ID] = None

        self._serial_loop_task = self._hass.loop.create_task(
            self.serial_read(self._port)
        )

    async def serial_read(self, device, **kwargs):
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
                if not logged_error:
                    _LOGGER.exception(
                        "Unable to connect to the serial device %s: %s. Will retry",
                        device,
                        exc,
                    )
                    logged_error = True
                await self._handle_error()
            else:
                _LOGGER.info("Serial device %s connected", device)
                while True:
                    try:
                        line = await reader.readline()
                    except SerialException as exc:
                        _LOGGER.exception(
                            "Error while reading serial device %s: %s", device, exc
                        )
                        await self._handle_error()
                        break
                    else:
                        line = line.decode("utf-8").strip()

                        # try:
                        #     data = json.loads(line)
                        # except ValueError:
                        #     pass
                        # else:
                        #     if isinstance(data, dict):
                        #         self._attributes = data

                        # if self._template is not None:
                        #     line = self._template.async_render_with_possible_json_value(
                        #         line
                        #     )

                        _LOGGER.debug("Received: %s", line)
#                        self._state = line
#                        self._hass.async_write_ha_state()

    async def _handle_error(self):
        """Handle error for serial connection."""
        self._state = None
        self._attributes = None
        self.async_write_ha_state()
        await asyncio.sleep(5)

    def stop(self):
        """Close resources."""
        if self._serial_loop_task:
            self._serial_loop_task.cancel()
