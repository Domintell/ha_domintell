"""Provides device automations for Domintell events."""

from __future__ import annotations

from typing import Final, Any
import voluptuous as vol


from homeassistant.components.device_automation import (
    DEVICE_TRIGGER_BASE_SCHEMA,
    InvalidDeviceAutomationConfig,
)
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
    CONF_TYPE,
)

from .const import (
    DOMAIN,
    BUTTON_EVENTS_TYPES,
    BUTTON_DEVICE_TRIGGERS_TYPES,
    GESTURE_EVENTS_TYPES,
    MOTION_EVENTS_TYPES,
    SIMPLE_PRESS_EVENTS_TYPES,
    IR_CODE_EVENTS_TYPES,
    CONF_SUBTYPE,
    ATTR_DOMINTELL_EVENT,
)
from .bridge import DomintellBridge


TRIGGER_SCHEMA: Final = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): str,
        vol.Required(CONF_SUBTYPE): vol.Union(int, str),
        # vol.Optional(CONF_UNIQUE_ID): str,
    }
)


def append_input_triggers(
    triggers: list[dict[str, str]],
    input_triggers: list[tuple[str, str]],
    device_id: str,
) -> None:
    """Add trigger to triggers list."""
    for trigger, subtype in input_triggers:
        triggers.append(
            {
                CONF_PLATFORM: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: trigger,
                CONF_SUBTYPE: subtype,
            }
        )


async def async_validate_trigger_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate config."""
    # pylint: disable=unused-argument

    config = TRIGGER_SCHEMA(config)

    # if device is available verify parameters against device capabilities
    trigger = (config[CONF_TYPE], config[CONF_SUBTYPE])

    if config[CONF_TYPE] in BUTTON_DEVICE_TRIGGERS_TYPES:
        return config
    elif config[CONF_TYPE] in GESTURE_EVENTS_TYPES:
        return config
    elif config[CONF_TYPE] in MOTION_EVENTS_TYPES:
        return config
    elif config[CONF_TYPE] in SIMPLE_PRESS_EVENTS_TYPES:
        return config
    elif config[CONF_TYPE] in IR_CODE_EVENTS_TYPES:
        return config
    else:
        raise InvalidDeviceAutomationConfig(
            f"Invalid ({CONF_TYPE},{CONF_SUBTYPE}): {trigger}"
        )


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device triggers for Domintell devices."""
    if DOMAIN not in hass.data:
        return []
    # lookup device in HASS DeviceRegistry
    dev_reg: dr.DeviceRegistry = dr.async_get(hass)
    if (device_entry := dev_reg.async_get(device_id)) is None:
        raise ValueError(f"Device ID {device_id} is not valid")

    for conf_entry_id in device_entry.config_entries:
        if conf_entry_id not in hass.data[DOMAIN]:
            continue
        bridge: DomintellBridge = hass.data[DOMAIN][conf_entry_id]
        api = bridge.api

        # Get device id and Domintell module id from device identifier
        identifier = get_domintell_device_id(device_entry)  # ie: "dgqg02-253_520000FD"
        device_id_parts = identifier.split("_")  # ie: ["dgqg02-253","520000FD"]
        module_id = device_id_parts[1]  # "520000FD"
        device = api.modules.get_module(module_id)  # instance of the module

        # Extract triggers from all button resources of this Domintell device
        triggers: list[dict[str, Any]] = []

        for resource in device:
            # button triggers
            if resource.io_type == 2:  # TypeInputIo
                triggers.extend(
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_PLATFORM: "device",
                        CONF_TYPE: event_type,
                        CONF_SUBTYPE: f"button {resource.io_offset}",
                    }
                    for event_type in BUTTON_DEVICE_TRIGGERS_TYPES
                )
            # gesture triggers
            elif resource.io_type == 49:  # TypeGestureIo
                triggers.extend(
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_PLATFORM: "device",
                        CONF_TYPE: event_type,
                        CONF_SUBTYPE: f"gesture {resource.io_offset}",
                    }
                    for event_type in GESTURE_EVENTS_TYPES
                )
            # motion triggers
            elif resource.io_type == 34:  # TypeMovIo
                triggers.extend(
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_PLATFORM: "device",
                        CONF_TYPE: event_type,
                        CONF_SUBTYPE: f"detector {resource.io_offset}",
                    }
                    for event_type in MOTION_EVENTS_TYPES
                )
            # simmple button triggers
            elif resource.io_type == 53:  # TypeInputTriggerIo
                triggers.extend(
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_PLATFORM: "device",
                        CONF_TYPE: event_type,
                        CONF_SUBTYPE: f"button {resource.io_offset}",
                    }
                    for event_type in SIMPLE_PRESS_EVENTS_TYPES
                )
            # Ir detector triggers
            elif resource.io_type == 9:  # TypeIrIo
                code_list = [f"code {i}" for i in range(1, 33)]
                triggers.extend(
                    {
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_PLATFORM: "device",
                        CONF_TYPE: event_type,
                        CONF_SUBTYPE: sub_type,
                    }
                    for event_type in IR_CODE_EVENTS_TYPES
                    for sub_type in code_list
                )

        return triggers
    return []


async def async_attach_trigger(hass, config, action, trigger_info):
    """Attach a trigger."""
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: ATTR_DOMINTELL_EVENT,
            event_trigger.CONF_EVENT_DATA: {
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_TYPE: config[CONF_TYPE],
                CONF_SUBTYPE: config[CONF_SUBTYPE],
            },
        }
    )

    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )


@callback
def get_domintell_device_id(device_entry: DeviceEntry) -> str | None:
    """Get Domintell device id from device entry."""
    return next(
        (
            identifier[1]
            for identifier in device_entry.identifiers
            if identifier[0] == DOMAIN
        ),
        None,
    )
