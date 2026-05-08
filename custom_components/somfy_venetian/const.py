DOMAIN = "somfy_venetian"
PLATFORMS = ["cover"]

CONF_SERVER = "server"
DEFAULT_SERVER = "somfy_europe"

# Somfy state names
STATE_CLOSURE = "core:ClosureState"
STATE_ORIENTATION = "core:SlateOrientationState"
STATE_MOVING = "core:MovingState"
STATE_OPEN_CLOSED = "core:OpenClosedState"

# Somfy commands
CMD_SET_CLOSURE = "setClosure"
CMD_SET_ORIENTATION = "setOrientation"
CMD_SET_CLOSURE_AND_ORIENTATION = "setClosureAndOrientation"
CMD_OPEN = "open"
CMD_CLOSE = "close"
CMD_STOP = "stop"
CMD_MY = "my"

# Tilt bounds (Somfy uses -90 to 0)
SOMFY_TILT_MIN = -90
SOMFY_TILT_MAX = 0

SCAN_INTERVAL_SECONDS = 30
