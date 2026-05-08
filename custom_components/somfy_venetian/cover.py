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
    """Somfy 0=horizontal 100=vertical → HA 100=horizontal 0=vertical"""
    return 100 - int(orientation)


def _ha_tilt_to_somfy(tilt: int) -> int:
    """HA 100=horizontal 0=vertical → Somfy 0=horizontal 100=vertical"""
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
        # état optimiste local (None = utilise la valeur du coordinateur)
        self._optimistic_position: int | None = None
        self._optimistic_tilt: int | None = None

    def _handle_coordinator_update(self) -> None:
        # on efface l'état optimiste dès que le coordinateur retourne une vraie valeur
        self._optimistic_position = None
        self._optimistic_tilt = None
        super()._handle_coordinator_update()

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
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    @property
    def is_opening(self) -> bool:
        moving = self._get_state(STATE_MOVING)
        return str(moving).lower() == "true"

    @property
    def current_cover_position(self) -> int | None:
        if self._optimistic_position is not None:
            return self._optimistic_position
        closure = self._get_state(STATE_CLOSURE)
        if closure is None:
            return None
        return _somfy_closure_to_ha(closure)

    @property
    def current_cover_tilt_position(self) -> int | None:
        if self._optimistic_tilt is not None:
            return self._optimistic_tilt
        orientation = self._get_state(STATE_ORIENTATION)
        if orientation is None:
            return None
        return _somfy_tilt_to_ha(orientation)

    async def async_open_cover(self, **kwargs) -> None:
        await self.coordinator.execute_command(self._device_url, CMD_OPEN)
        self._optimistic_position = 100
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs) -> None:
        await self.coordinator.execute_command(self._device_url, CMD_CLOSE)
        self._optimistic_position = 0
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs) -> None:
        await self.coordinator.execute_command(self._device_url, CMD_STOP)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs) -> None:
        ha_position = kwargs["position"]
        somfy_closure = _ha_position_to_somfy(ha_position)
        somfy_orientation = _ha_tilt_to_somfy(self.current_cover_tilt_position or 50)
        await self.coordinator.execute_command(
            self._device_url,
            CMD_SET_CLOSURE_AND_ORIENTATION,
            somfy_closure,
            somfy_orientation,
        )
        self._optimistic_position = ha_position
        self.async_write_ha_state()

    async def async_open_cover_tilt(self, **kwargs) -> None:
        await self.async_set_cover_tilt_position(tilt_position=100)

    async def async_close_cover_tilt(self, **kwargs) -> None:
        await self.async_set_cover_tilt_position(tilt_position=0)

    async def async_set_cover_tilt_position(self, **kwargs) -> None:
        ha_tilt = kwargs["tilt_position"]
        somfy_orientation = _ha_tilt_to_somfy(ha_tilt)
        somfy_closure = _ha_position_to_somfy(self.current_cover_position or 0)
        await self.coordinator.execute_command(
            self._device_url,
            CMD_SET_CLOSURE_AND_ORIENTATION,
            somfy_closure,
            somfy_orientation,
        )
        self._optimistic_tilt = ha_tilt
        self.async_write_ha_state()

    async def async_my(self) -> None:
        """Position mémorisée (bouton My de la télécommande)."""
        await self.coordinator.execute_command(self._device_url, CMD_MY)
        await self.coordinator.async_request_refresh()
