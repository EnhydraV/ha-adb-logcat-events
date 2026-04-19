DOMAIN = "shield_volume"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"

DEFAULT_PORT = 5555

EVENT_VOLUME_BUTTON = "shield_volume_button"

ACTION_VOLUME_UP = "volume_up"
ACTION_VOLUME_DOWN = "volume_down"

# Logcat patterns (keyAction: 1 = key up, avoids double-fire on key down)
LOGCAT_PATTERNS = {
    "WindowManager: handleComboKeys keyCode: 24, keyAction: 1": ACTION_VOLUME_UP,
    "WindowManager: handleComboKeys keyCode: 25, keyAction: 1": ACTION_VOLUME_DOWN,
}

# Reconnection backoff
BACKOFF_INITIAL = 5       # seconds
BACKOFF_MULTIPLIER = 2
BACKOFF_MAX = 300         # 5 minutes max
