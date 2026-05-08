"""Tests des fonctions de conversion Somfy ↔ Home Assistant."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from custom_components.somfy_venetian.cover import (
    _ha_position_to_somfy,
    _ha_tilt_to_somfy,
    _somfy_closure_to_ha,
    _somfy_tilt_to_ha,
)


# ── Position (closure) ────────────────────────────────────────────────────────

class TestPositionMapping:
    def test_somfy_open_is_ha_100(self):
        assert _somfy_closure_to_ha(0) == 100

    def test_somfy_closed_is_ha_0(self):
        assert _somfy_closure_to_ha(100) == 0

    def test_somfy_half_is_ha_half(self):
        assert _somfy_closure_to_ha(50) == 50

    def test_ha_open_is_somfy_0(self):
        assert _ha_position_to_somfy(100) == 0

    def test_ha_closed_is_somfy_100(self):
        assert _ha_position_to_somfy(0) == 100

    def test_ha_half_is_somfy_half(self):
        assert _ha_position_to_somfy(50) == 50

    def test_round_trip_position(self):
        """Convertir vers HA puis vers Somfy doit redonner la valeur initiale."""
        for somfy_val in range(0, 101, 10):
            assert _ha_position_to_somfy(_somfy_closure_to_ha(somfy_val)) == somfy_val

    def test_round_trip_ha_position(self):
        for ha_val in range(0, 101, 10):
            assert _somfy_closure_to_ha(_ha_position_to_somfy(ha_val)) == ha_val


# ── Inclinaison (tilt) ────────────────────────────────────────────────────────

class TestTiltMapping:
    def test_somfy_horizontal_is_ha_100(self):
        """Lamelles horizontales (max lumière) = tilt HA 100%."""
        assert _somfy_tilt_to_ha(0) == 100

    def test_somfy_vertical_is_ha_0(self):
        """Lamelles verticales (occultant) = tilt HA 0%."""
        assert _somfy_tilt_to_ha(100) == 0

    def test_somfy_45deg_is_ha_50(self):
        assert _somfy_tilt_to_ha(50) == 50

    def test_ha_100_is_somfy_0(self):
        assert _ha_tilt_to_somfy(100) == 0

    def test_ha_0_is_somfy_100(self):
        assert _ha_tilt_to_somfy(0) == 100

    def test_ha_50_is_somfy_50(self):
        assert _ha_tilt_to_somfy(50) == 50

    def test_round_trip_tilt(self):
        for somfy_val in range(0, 101, 10):
            assert _ha_tilt_to_somfy(_somfy_tilt_to_ha(somfy_val)) == somfy_val

    def test_round_trip_ha_tilt(self):
        for ha_val in range(0, 101, 10):
            assert _somfy_tilt_to_ha(_ha_tilt_to_somfy(ha_val)) == ha_val

    def test_real_observed_values(self):
        """Valeurs réelles observées sur les stores en production."""
        # SlateOrientationState=1 → store presque horizontal → HA ~99%
        assert _somfy_tilt_to_ha(1) == 99
        # SlateOrientationState=98 → store presque vertical → HA ~2%
        assert _somfy_tilt_to_ha(98) == 2
        # SlateOrientationState=42 → HA 58%
        assert _somfy_tilt_to_ha(42) == 58
