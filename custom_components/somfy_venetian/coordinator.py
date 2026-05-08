from __future__ import annotations

import asyncio
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

EVENT_POLL_INTERVAL = 2


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
        self._session: aiohttp.ClientSession | None = None
        self._event_task: asyncio.Task | None = None
        self._connecting = False  # verrou contre la double-connexion

    async def _get_client(self) -> OverkizClient:
        if self._client is not None:
            return self._client
        if self._connecting:
            # attend que la connexion en cours se termine
            while self._connecting:
                await asyncio.sleep(0.1)
            return self._client  # type: ignore[return-value]
        self._connecting = True
        try:
            # ferme l'ancienne session proprement avant d'en créer une nouvelle
            if self._session and not self._session.closed:
                await self._session.close()
            connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver(), ssl=False)
            self._session = aiohttp.ClientSession(connector=connector)
            self._client = OverkizClient(
                username=self._username,
                password=self._password,
                server=SUPPORTED_SERVERS[self._server_key],
                session=self._session,
            )
            await self._client.login()
            await self._client.register_event_listener()
            _LOGGER.debug("Connecté, event listener enregistré")
        finally:
            self._connecting = False
        return self._client

    async def _reset_client(self) -> None:
        self._client = None

    async def _async_update_data(self) -> dict[str, Device]:
        """Chargement complet — au démarrage et comme fallback toutes les 30s."""
        try:
            client = await self._get_client()
            devices = await client.get_devices(refresh=True)
            result = {
                d.device_url: d
                for d in devices
                if d.ui_class == "ExteriorVenetianBlind"
            }
            if self._event_task is None or self._event_task.done():
                self._event_task = self.hass.async_create_task(self._event_loop())
            return result
        except Exception as err:
            await self._reset_client()
            raise UpdateFailed(f"Erreur communication TaHoma: {err}") from err

    async def _event_loop(self) -> None:
        """Boucle événementielle : fetch_events() toutes les 2s."""
        _LOGGER.debug("Boucle événementielle démarrée")
        while True:
            await asyncio.sleep(EVENT_POLL_INTERVAL)
            try:
                client = await self._get_client()
                events = await client.fetch_events()
                updated = False
                for event in events:
                    if not event.device_url or event.device_url not in self.data:
                        continue
                    if not event.device_states:
                        continue
                    device = self.data[event.device_url]
                    state_map = {s.name: s for s in device.states}
                    for new_state in event.device_states:
                        state_map[new_state.name] = new_state
                        _LOGGER.debug("%s: %s = %s", device.label, new_state.name, new_state.value)
                    device.states = list(state_map.values())
                    updated = True
                if updated:
                    self.async_set_updated_data(self.data)
            except asyncio.CancelledError:
                _LOGGER.debug("Boucle événementielle annulée")
                return
            except Exception as err:
                _LOGGER.warning("Erreur event loop: %s — reconnexion dans 5s", err)
                await self._reset_client()
                await asyncio.sleep(5)

    async def async_shutdown(self) -> None:
        """Annule la boucle événementielle et ferme la session proprement."""
        if self._event_task and not self._event_task.done():
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass
        if self._session and not self._session.closed:
            await self._session.close()
        await super().async_shutdown()

    async def execute_command(self, device_url: str, command: str, *params) -> None:
        from pyoverkiz.models import Command
        try:
            client = await self._get_client()
            await client.execute_command(device_url, Command(command, list(params)))
            _LOGGER.debug("Commande %s(%s) → %s", command, params, device_url)
        except Exception as err:
            _LOGGER.error("Échec commande %s sur %s: %s", command, device_url, err)
            await self._reset_client()
            raise
