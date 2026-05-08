# Somfy Venetian Blinds for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/anakinch75/somfy-venetian-ha)](https://github.com/anakinch75/somfy-venetian-ha/releases)
[![Tests](https://github.com/anakinch75/somfy-venetian-ha/actions/workflows/tests.yml/badge.svg)](https://github.com/anakinch75/somfy-venetian-ha/actions/workflows/tests.yml)

Home Assistant integration for Somfy venetian blinds via TaHoma Switch, with full slat tilt control — a feature missing from the official Overkiz integration.

---

## Why this integration?

The official **Overkiz** integration in Home Assistant does not support the `DynamicExteriorVenetianBlind` widget and does not expose the `core:SlateOrientationState` attribute. This integration fills that gap for Somfy io-homecontrol venetian blinds.

## Features

- Position control (raise/lower)
- Slat tilt control (`tilt_position`)
- Combined position + tilt command (`setClosureAndOrientation`)
- Stop
- Memorized position (My button)
- Real-time state updates via event polling (every 2 seconds)

## Supported devices

- Widget `DynamicExteriorVenetianBlind` / UI Class `ExteriorVenetianBlind`
- Via TaHoma Switch (io-homecontrol)
- Tested in Switzerland with a Somfy Europe account

## Requirements

- Home Assistant 2023.1+
- HACS installed
- Somfy account (mysciosomfy.com)
- TaHoma Switch connected and paired

## Installation via HACS

1. In HACS → **Integrations** → ⋮ menu → **Custom repositories**
2. URL: `https://github.com/anakinch75/somfy-venetian-ha`
3. Category: **Integration**
4. Click **Add**
5. Search for "Somfy Venetian" and install
6. Restart Home Assistant

## Configuration

1. **Settings** → **Devices & services** → **Add integration**
2. Search for **Somfy Venetian Blinds**
3. Enter your Somfy account email and password
4. Select your region (Europe by default)

## Entities

One `cover` entity per detected blind, named after the label in the TaHoma app.

| Attribute | Description | Values |
|-----------|-------------|--------|
| `current_cover_position` | Blind position | 0 = closed, 100 = open |
| `current_cover_tilt_position` | Slat tilt angle | 0 = vertical (closed), 100 = horizontal (open) |
| `is_closed` | Is the blind closed? | boolean |

## Tilt mapping

The Somfy API uses `core:SlateOrientationState` with values 0–100:

| Somfy | HA `tilt_position` | Physical position |
|-------|--------------------|-------------------|
| 0 | 100 | Slats horizontal (max light) |
| 50 | 50 | Slats at 45° |
| 100 | 0 | Slats vertical (blackout) |

## Available services

| Service | Description |
|---------|-------------|
| `cover.open_cover` | Fully raise the blind |
| `cover.close_cover` | Fully lower the blind |
| `cover.stop_cover` | Stop movement |
| `cover.set_cover_position` | Set precise position (0–100) |
| `cover.set_cover_tilt_position` | Set precise tilt angle (0–100) |

## Automation examples

```yaml
# Open slats at 45° every morning
automation:
  - alias: "Morning blinds"
    trigger:
      platform: time
      at: "07:30:00"
    action:
      - service: cover.set_cover_tilt_position
        target:
          entity_id: cover.salon
        data:
          tilt_position: 50

# Close all blinds at sunset
  - alias: "Evening blinds"
    trigger:
      platform: sun
      event: sunset
    action:
      - service: cover.close_cover
        target:
          area_id: living_room
```

---

## Changelog

### v1.0.10
- Added Somfy brand icon (shown in HACS and HA integration page)

### v1.0.9
- Cleaner integration page: title "Somfy TaHoma Switch" instead of email address
- All blinds grouped under a single "TaHoma Switch" device in HA

### v1.0.8
- Added 29 unit tests (mappings, pending state, combined commands)
- GitHub Actions: tests run automatically on every push
- Test status badge in README

### v1.0.7
- Fixed aiohttp session leak on reconnection
- Event loop properly cancelled on integration unload
- Lock against concurrent double-connection
- `open`/`close` now show target position during movement
- `stop` immediately clears pending state
- `is_opening`/`is_closing` correctly implemented

### v1.0.6
- Fixed end-of-movement slider jump: shows target value during movement, switches to real value when stopped

### v1.0.5
- Fixed combined position+tilt commands: pending values prevent conflicts between rapid successive commands

### v1.0.4
- Major refactor: replaced polling with real-time event loop (`fetch_events()` every 2s)
- States update in real time during blind movement

### v1.0.3
- Fixed slider bouncing back during movement

### v1.0.2
- Fixed state not updating: `get_devices(refresh=True)`
- Added optimistic state updates

### v1.0.1
- Fixed tilt mapping: Somfy API expects 0–100 (not -90 to 0)

### v1.0.0
- Initial release: position + slat tilt control
