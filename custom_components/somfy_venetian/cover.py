from __future__ import annotations

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CMD_CLOSE,
    CMD_MY,
    CMD_OPEN,
    CMD_SET_CLOSURE_AND_ORIENTATION,
    CMD_STOP,
    DOMAIN,
    STATE_CLOSURE,
    STATE_MOVING,
    STATE_ORIENTATION,
)
from .coordinator import SomfyVenetianCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SomfyVenetianCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_config_entry_first_refresh()
    async_add_entities(
        SomfyVenetianBlind(coordinator, device_url)
        for device_url in coordinator.data
    )


def _somfy_closure_to_ha(closure: int) -> int:
    """Somfy 0=ouvert 100=fermé → HA 100=ouvert 0=fermé"""
    return 100 - int(closure)


def _ha_position_to_somfy(position: int) -> int:
    return 100 - int(position)


def _somfy_tilt_to_ha(orientation: int) -> int:
    """Somfy 0=ouvert→100=fermé → HA 100=ouvert→0=fermé"""
    return 100 - int(orientation)


def _ha_tilt_to_somfy(tilt: int) -> int:
    """HA 100=ouvert→0=fermé → Somfy 0=ouvert→100=fermé"""
    return 100 - int(tilt)


class SomfyVenetianBlind(CoordinatorEntity[SomfyVenetianCoordinator], CoverEntity):

    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.SET_TILT_POSITION
    )

    def __init__(self, coordinator: SomfyVenetianCoordinator, device_url: str) -> None:
        super().__init__(coordinator)
        self._device_url = device_url
        self._attr_unique_id = device_url
        self._attr_name = coordinator.data[device_url].label

    def _get_state(self, name: str):
        device = self.coordinator.data.get(self._device_url)
        if device is None:
            return None
        for s in device.states:
            if s.name == name:
                return s.value
        return None

    @property
    def is_closed(self) -> bool | None:
        closure = self._get_state(STATE_CLOSURE)
        if closure is None:
            return None
        return int(closure) >= 100

    @property
    def is_opening(self) -> bool:
        moving = self._get_state(STATE_MOVING)
        return str(moving).lower() == "true"

    @property
    def current_cover_position(self) -> int | None:
        closure = self._get_state(STATE_CLOSURE)
        if closure is None:
            return None
        return _somfy_closure_to_ha(closure)

    @property
    def current_cover_tilt_position(self) -> int | None:
        orientation = self._get_state(STATE_ORIENTATION)
        if orientation is None:
            return None
        return _somfy_tilt_to_ha(orientation)

    async def async_open_cover(self, **kwargs) -> None:
        await self.coordinator.execute_command(self._device_url, CMD_OPEN)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs) -> None:
        await self.coordinator.execute_command(self._device_url, CMD_CLOSE)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs) -> None:
        await self.coordinator.execute_command(self._device_url, CMD_STOP)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs) -> None:
        ha_position = kwargs["position"]
        orientation = self._get_state(STATE_ORIENTATION) or 0
        somfy_closure = _ha_position_to_somfy(ha_position)
        await self.coordinator.execute_command(
            self._device_url,
            CMD_SET_CLOSURE_AND_ORIENTATION,
            somfy_closure,
            int(orientation),
        )
        await self.coordinator.async_request_refresh()

    async def async_open_cover_tilt(self, **kwargs) -> None:
        await self.async_set_cover_tilt_position(tilt_position=100)

    async def async_close_cover_tilt(self, **kwargs) -> None:
        await self.async_set_cover_tilt_position(tilt_position=0)

    async def async_set_cover_tilt_position(self, **kwargs) -> None:
        ha_tilt = kwargs["tilt_position"]
        closure = self._get_state(STATE_CLOSURE) or 0
        somfy_orientation = _ha_tilt_to_somfy(ha_tilt)
        await self.coordinator.execute_command(
            self._device_url,
            CMD_SET_CLOSURE_AND_ORIENTATION,
            int(closure),
            somfy_orientation,
        )
        await self.coordinator.async_request_refresh()

    async def async_my(self) -> None:
        """Position mémorisée (bouton My de la télécommande)."""
        await self.coordinator.execute_command(self._device_url, CMD_MY)
        await self.coordinator.async_request_refresh()
