""" Config flow for Rainforest EMU-2. """
from __future__ import annotations

import asyncio
import logging
import serial.tools.list_ports
import voluptuous as vol
import xml.etree.ElementTree as ET

from serial import Serial, SerialException

from homeassistant import config_entries
from homeassistant.components import usb
from homeassistant.const import (
    ATTR_SW_VERSION,
    ATTR_HW_VERSION,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    CONF_HOST,
    CONF_PORT
)

from .const import (
    DOMAIN,
    ATTR_DEVICE_PATH,
    ATTR_DEVICE_MAC_ID
)
from .emu2 import Emu2
from .emu2_entities import (
    DeviceInfo,
    InstantaneousDemand
)

_LOGGER = logging.getLogger(__name__)

CONF_DEVICE_PATH = "device_path"
CONF_MANUAL_PATH = "Enter Manually"

class RainforestConfigFlow(config_entries.ConfigFlow, domain = DOMAIN):
    """Handle a config flow for Rainforest EMU-2 integration."""

    VERSION = 1

    async def async_step_user(self, user_input = None):
        """Handle the initial step."""
        ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)
        list_of_ports = [
            f"{p}"
            + (f" - {p.manufacturer}" if p.manufacturer else "")
            for p in ports
        ]

        if not list_of_ports:
            return await self.async_step_manual()

        list_of_ports.append(CONF_MANUAL_PATH)

        errors = {}
        if user_input is not None:
            user_selection = user_input[CONF_DEVICE_PATH]
            if user_selection == CONF_MANUAL_PATH:
                return await self.async_step_manual()

            port = ports[list_of_ports.index(user_selection)]
            device_path = await self.hass.async_add_executor_job(
                usb.get_serial_by_id, port.device
            )

            device_properties = await self.async_get_device_properties(device_path, None, None)
            if device_properties is not None:
                return await self.async_setup_device(device_path, device_properties)

            _LOGGER.info("EMU-2 device not detected on %s", device_path)
            errors[CONF_DEVICE_PATH] = "not_detected"

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_PATH): vol.In(list_of_ports)
            }
        )
        return self.async_show_form(step_id="user", data_schema = schema, errors = errors)

    async def async_step_manual(self, user_input = None):
        """Manually specify the path."""
        errors = {}

        if user_input is not None:
            device_path = None
            host = None
            port = None
            try:
                device_path = user_input[CONF_DEVICE_PATH]
            except Exception as ex:
                host = user_input[CONF_HOST]
                port = user_input[CONF_PORT]
            
            device_properties = await self.async_get_device_properties(device_path, host, port)
            if device_properties is not None:
                return await self.async_setup_device(device_path, device_properties)
            errors[CONF_DEVICE_PATH] = "not_detected"

        schema = vol.Schema(
            {
                vol.Optional(CONF_DEVICE_PATH): str,
                vol.Optional(CONF_HOST): str,
                vol.Optional(CONF_PORT): str             
            }
        )
        return self.async_show_form(step_id = "manual", data_schema = schema, errors = errors)

    async def async_setup_device(self, device_path: str, device_properties: dict):
        await self.async_set_unique_id(device_properties[ATTR_DEVICE_MAC_ID])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title = device_path,
            data = device_properties
        )        

    async def async_get_device_properties(self, device_path, host, port) -> dict[str, str]:
        """Probe the the device for the its properties."""

        emu2 = Emu2(device_path, host, port)

        if await emu2.test_available() == False:
            return None

        serial_loop_task = self.hass.loop.create_task(emu2.serial_read())
        if await emu2.wait_connected(8) == False:
            _LOGGER.debug("Failed to receive data from device")

        await emu2.get_device_info()

        await asyncio.sleep(2)
        serial_loop_task.cancel()

        try:
            await serial_loop_task
        except asyncio.CancelledError as ex:
            _LOGGER.debug("Cancelled, caught %s", ex)

        await emu2.close()

        response = emu2.get_data(DeviceInfo)
        if response is not None:
            return {
                ATTR_DEVICE_PATH: device_path,
                ATTR_DEVICE_MAC_ID: response.device_mac,
                ATTR_SW_VERSION: response.fw_version,
                ATTR_HW_VERSION: response.hw_version,
                ATTR_MANUFACTURER: response.manufacturer,
                ATTR_MODEL: response.model_id,
                CONF_HOST: host,
                CONF_PORT: port
            }
        _LOGGER.debug("get_devices_properties DeviceInfo response is None")

        # For some reason we didnt get a DeviceInfo response, failback to an InstananeousDemand response
        response = emu2.get_data(InstantaneousDemand)
        if response is not None:
            return {
                ATTR_DEVICE_PATH: device_path,
                ATTR_DEVICE_MAC_ID: response.device_mac,
                CONF_HOST: host,
                CONF_PORT: port
            }

        _LOGGER.debug("get_devices_properties InstantaneousDemand response is None")
        return None
