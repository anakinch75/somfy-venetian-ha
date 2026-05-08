"""Tests du mécanisme de pending state et des commandes combinées."""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from custom_components.somfy_venetian.cover import SomfyVenetianBlind
from custom_components.somfy_venetian.const import STATE_MOVING, STATE_CLOSURE, STATE_ORIENTATION


def make_state(name, value):
    s = MagicMock()
    s.name = name
    s.value = value
    return s


def make_device(label="Test", closure=0, orientation=0, moving=False):
    device = MagicMock()
    device.label = label
    device.states = [
        make_state(STATE_CLOSURE, closure),
        make_state(STATE_ORIENTATION, orientation),
        make_state(STATE_MOVING, moving),
    ]
    return device


def make_coordinator(closure=0, orientation=0, moving=False):
    coordinator = MagicMock()
    coordinator.data = {"io://test/1": make_device(closure=closure, orientation=orientation, moving=moving)}
    coordinator.execute_command = AsyncMock()
    return coordinator


def make_blind(closure=0, orientation=0, moving=False):
    coordinator = make_coordinator(closure=closure, orientation=orientation, moving=moving)
    with patch.object(SomfyVenetianBlind, "__init__", lambda self, *a, **kw: None):
        blind = SomfyVenetianBlind.__new__(SomfyVenetianBlind)
    blind.coordinator = coordinator
    blind._device_url = "io://test/1"
    blind._attr_unique_id = "io://test/1"
    blind._attr_name = "Test"
    blind._pending_position = None
    blind._pending_tilt = None
    blind.async_write_ha_state = MagicMock()
    return blind


# ── Pending state ─────────────────────────────────────────────────────────────

class TestPendingState:
    def test_no_pending_reads_coordinator(self):
        blind = make_blind(closure=40)
        assert blind.current_cover_position == 60  # 100-40

    def test_pending_overrides_coordinator(self):
        blind = make_blind(closure=40)
        blind._pending_position = 80
        assert blind.current_cover_position == 80

    def test_pending_cleared_when_not_moving(self):
        blind = make_blind(closure=40, moving=False)
        blind._pending_position = 80
        blind._pending_tilt = 30
        blind._handle_coordinator_update()
        assert blind._pending_position is None
        assert blind._pending_tilt is None

    def test_pending_preserved_when_moving(self):
        blind = make_blind(closure=40, moving=True)
        blind._pending_position = 80
        blind._pending_tilt = 30
        blind._handle_coordinator_update()
        assert blind._pending_position == 80
        assert blind._pending_tilt == 30


# ── Commandes combinées ───────────────────────────────────────────────────────

class TestCombinedCommands:
    @pytest.mark.asyncio
    async def test_set_position_uses_current_tilt(self):
        """Changer la position doit conserver le tilt actuel."""
        blind = make_blind(closure=0, orientation=30)  # tilt HA = 70
        await blind.async_set_cover_position(position=50)
        blind.coordinator.execute_command.assert_called_once_with(
            "io://test/1",
            "setClosureAndOrientation",
            50,   # Somfy closure = 100-50
            30,   # Somfy orientation = conservé tel quel
        )

    @pytest.mark.asyncio
    async def test_set_tilt_uses_current_position(self):
        """Changer le tilt doit conserver la position actuelle."""
        blind = make_blind(closure=25, orientation=0)  # position HA = 75
        await blind.async_set_cover_tilt_position(tilt_position=40)
        blind.coordinator.execute_command.assert_called_once_with(
            "io://test/1",
            "setClosureAndOrientation",
            25,   # Somfy closure = conservé tel quel
            60,   # Somfy orientation = 100-40
        )

    @pytest.mark.asyncio
    async def test_position_then_tilt_uses_pending_position(self):
        """Si position commandée avant que le coordinateur rafraîchisse,
        le tilt doit utiliser la position en attente et non l'ancienne valeur."""
        blind = make_blind(closure=0, orientation=50)  # position initiale = 100
        # 1. Commande position → pending = 30
        await blind.async_set_cover_position(position=30)
        # 2. Commande tilt sans que le coordinateur ait mis à jour
        await blind.async_set_cover_tilt_position(tilt_position=20)
        last_call = blind.coordinator.execute_command.call_args
        closure_sent = last_call[0][2]
        assert closure_sent == 70  # 100-30, et non 0 (l'ancienne valeur)

    @pytest.mark.asyncio
    async def test_tilt_then_position_uses_pending_tilt(self):
        """Si tilt commandé avant que le coordinateur rafraîchisse,
        la position doit utiliser le tilt en attente."""
        blind = make_blind(closure=50, orientation=0)  # tilt initial = 100
        await blind.async_set_cover_tilt_position(tilt_position=10)
        await blind.async_set_cover_position(position=60)
        last_call = blind.coordinator.execute_command.call_args
        orientation_sent = last_call[0][3]
        assert orientation_sent == 90  # 100-10, et non 0 (l'ancienne valeur)


# ── Stop ─────────────────────────────────────────────────────────────────────

class TestStop:
    @pytest.mark.asyncio
    async def test_stop_clears_pending(self):
        blind = make_blind()
        blind._pending_position = 50
        blind._pending_tilt = 30
        await blind.async_stop_cover()
        assert blind._pending_position is None
        assert blind._pending_tilt is None


# ── is_closed ────────────────────────────────────────────────────────────────

class TestIsClosed:
    def test_closed_when_position_0(self):
        blind = make_blind(closure=100)
        assert blind.is_closed is True

    def test_open_when_position_100(self):
        blind = make_blind(closure=0)
        assert blind.is_closed is False

    def test_pending_overrides_for_is_closed(self):
        blind = make_blind(closure=100)  # store fermé réellement
        blind._pending_position = 50    # mais commande d'ouverture en cours
        assert blind.is_closed is False
