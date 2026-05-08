from __future__ import annotations

import aiohttp
import voluptuous as vol
from pyoverkiz.client import OverkizClient
from pyoverkiz.const import SUPPORTED_SERVERS

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import CONF_SERVER, DEFAULT_SERVER, DOMAIN

SERVERS = {
    "somfy_europe": "Somfy (Europe)",
    "somfy_america": "Somfy (Amérique)",
    "somfy_oceania": "Somfy (Océanie)",
}

STEP_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Optional(CONF_SERVER, default=DEFAULT_SERVER): vol.In(SERVERS),
})


class SomfyVenetianConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver(), ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    client = OverkizClient(
                        username=user_input[CONF_USERNAME],
                        password=user_input[CONF_PASSWORD],
                        server=SUPPORTED_SERVERS[user_input[CONF_SERVER]],
                        session=session,
                    )
                    await client.login()

                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Somfy TaHoma Switch",
                    data=user_input,
                )
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
        )
