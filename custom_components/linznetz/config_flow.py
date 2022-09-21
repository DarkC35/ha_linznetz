"""Adds config flow for linznetz."""
from homeassistant import config_entries

import voluptuous as vol

from .const import (
    CONF_METER_POINT_NUMBER,
    CONF_NAME,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_METER_POINT_NUMBER): str,
        vol.Optional(CONF_NAME): str,
    }
)


class LinzNetzFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for linznetz."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        valid = len(user_input[CONF_METER_POINT_NUMBER]) == 33
        if not valid:
            errors["base"] = "invalid_length"
        else:
            await self.async_set_unique_id(user_input[CONF_METER_POINT_NUMBER])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_METER_POINT_NUMBER], data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
