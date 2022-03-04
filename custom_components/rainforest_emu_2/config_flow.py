""" Config flow for Rainforest EMU-2. """
from __future__ import annotations

import asyncio
import logging
import serial.tools.list_ports
import voluptuous as vol
import xml.etree.ElementTree as ET

from homeassistant import config_entries
from homeassistant.components import usb
from homeassistant.const import (
    ATTR_SW_VERSION,
    ATTR_HW_VERSION,
    ATTR_MANUFACTURER,
    ATTR_MODEL
)

from .const import (
    DOMAIN,
    ATTR_DEVICE_PATH,
    ATTR_DEVICE_MAC_ID
)
from .emu2 import Emu2
from .emu2_entities import (
    DeviceInfo
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

            device_properties = await self.get_device_id(device_path)
            if device_properties is not None:
                await self.async_set_unique_id(device_properties[ATTR_DEVICE_MAC_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title = device_path,
                    data = device_properties
                )

            errors[CONF_DEVICE_PATH] = "device not detected"

        schema = vol.Schema({vol.Required(CONF_DEVICE_PATH): vol.In(list_of_ports)})
        return self.async_show_form(step_id="user", data_schema = schema, errors = errors)


    async def async_step_manual(self, user_input = None):
        """Manually specify the path."""
        dev_path = user_input[CONF_DEVICE_PATH]

        if dev_path is not None:
            dev_path = user_input[CONF_DEVICE_PATH]

            device_id = await self.get_device_id(dev_path)

#            if device_id is not None


            # return self.async_create_entry(
            #     title=port,
            #     data={CONF_PORT: port}
            # )        

        schema = vol.Schema({vol.Required(CONF_DEVICE_PATH): str})
        return self.async_show_form(step_id = "manual", data_schema=schema)   

    async def get_device_id(self, device_path: str) -> dict[str, str]:
        """Probe the the device for the device mac id."""
        emu2 = Emu2(device_path)
        
        response = None
        if await emu2.connect() == True:
            # Start the monitoring loop
            serial_loop_task = self.hass.loop.create_task(
                emu2.serial_read()
            )

            _LOGGER.debug("Connected, sending query")
            emu2.get_device_info()

            _LOGGER.debug("Connected, waiting for response")
            await asyncio.sleep(3)
            
            response = emu2.get_data(DeviceInfo)

        # End the monitoring loop
        emu2.stop_serial()

        if response is None:
            return None

        return {
            ATTR_DEVICE_PATH: device_path,
            ATTR_DEVICE_MAC_ID: response.device_mac,
            ATTR_SW_VERSION: response.fw_version,
            ATTR_HW_VERSION: response.hw_version,
            ATTR_MANUFACTURER: response.manufacturer,
            ATTR_MODEL: response.model_id
        }
