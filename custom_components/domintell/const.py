"""Constants of the Domintell component."""

from homeassistant.const import Platform

DOMAIN = "domintell"
ATTR_DOMINTELL_EVENT = "domintell_event"
ATTR_DEVICE = "device"

DOMINTELL_OUI = "CC43E3"
PLATFORMS = [
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.COVER,
    Platform.FAN,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.SCENE,
    Platform.CLIMATE,
    Platform.NUMBER,
]

CONF_IGNORE_AVAILABILITY = "ignore_availability"
CONF_MODULE_TYPE = "module_type"
CONF_MODULE_SN = "module_serial_number"

BUTTON_EVENTS_TYPES = [
    "released",
    "start_short_push",
    "end_short_push",
    "start_long_push",
    "end_long_push",
    "pressed",
]

SIMPLE_PRESS_EVENTS_TYPES = [
    "start_short_push",
    "end_short_push",
]

BUTTON_DEVICE_TRIGGERS_TYPES = [
    "press",
    "short_press",
    "long_press",
]

GESTURE_EVENTS_TYPES = [
    # "gesture_right",
    # "gesture_left",
    "gesture_up",
    "gesture_down",
    # "gesture_push",
]

MOTION_EVENTS_TYPES = [
    "start_detection",
    "end_detection",
]


IR_CODE_EVENTS_TYPES = ["no_key"] + [f"key_{i:02d}" for i in range(1, 33)]


CONF_SUBTYPE = "subtype"

BRIDGES_LIST = ("DGQG02", "DGQG03", "DGQG04", "DGQG05", "DNET01", "DNET02")
DEFAULT_BRIDGE = "DGQG04"
