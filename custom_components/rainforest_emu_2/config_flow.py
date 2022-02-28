""" Config flow for Rainforest EMU-2. """
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({vol.Required(CONF_PORT): str})

class RainforestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rainforest EMU-2 integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        if user_input is not None:
            port = user_input[CONF_PORT]

            errors = {}

            return self.async_create_entry(
                title=port,
                data={CONF_PORT: port}
            )

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors={})
    