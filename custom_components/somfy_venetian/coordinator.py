from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from pyoverkiz.client import OverkizClient
from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.models import Device

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class SomfyVenetianCoordinator(DataUpdateCoordinator[dict[str, Device]]):

    def __init__(self, hass: HomeAssistant, username: str, password: str, server_key: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self._username = username
        self._password = password
        self._server_key = server_key
        self._client: OverkizClient | None = None

    async def _get_client(self) -> OverkizClient:
        if self._client is None:
            connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver(), ssl=False)
            session = aiohttp.ClientSession(connector=connector)
            self._client = OverkizClient(
                username=self._username,
                password=self._password,
                server=SUPPORTED_SERVERS[self._server_key],
                session=session,
            )
            await self._client.login()
        return self._client

    async def _async_update_data(self) -> dict[str, Device]:
        try:
            client = await self._get_client()
            devices = await client.get_devices()
            return {
                d.device_url: d
                for d in devices
                if d.ui_class == "ExteriorVenetianBlind"
            }
        except Exception as err:
            self._client = None  # force reconnect next time
            raise UpdateFailed(f"Erreur communication TaHoma: {err}") from err

    async def execute_command(self, device_url: str, command: str, *params) -> None:
        from pyoverkiz.models import Command
        client = await self._get_client()
        await client.execute_command(device_url, Command(command, list(params)))
