"""Provides device automations for Domintell events."""

from __future__ import annotations

import voluptuous as vol
from typing import Any

from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.components.device_automation import (
    DEVICE_TRIGGER_BASE_SCHEMA,
    InvalidDeviceAutomationConfig,
)
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    BUTTON_DEVICE_TRIGGERS_TYPES,
    GESTURE_EVENTS_TYPES,
    MOTION_EVENTS_TYPES,
    SIMPLE_PRESS_EVENTS_TYPES,
    IR_CODE_EVENTS_TYPES,
    CONF_SUBTYPE,
    ATTR_DOMINTELL_EVENT,
)

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): str,
        vol.Required(CONF_SUBTYPE): vol.Any(int, str),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for Domintell devices."""
    if DOMAIN not in hass.data:
        return []

    dev_reg = dr.async_get(hass)
    device_entry = dev_reg.async_get(device_id)
    if device_entry is None:
        return []

    triggers: list[dict[str, Any]] = []

    for conf_entry_id in device_entry.config_entries:
        if conf_entry_id not in hass.data[DOMAIN]:
            continue

        bridge = hass.data[DOMAIN][conf_entry_id]
        api = bridge.api

        identifier = get_domintell_device_id(device_entry)

        if not identifier or "_" not in identifier:
            continue

        module_id = identifier.split("_")[1]
        device = api.modules.get_module(module_id)
        if not device:
            continue

        for resource in device:
            base_trigger = {
                CONF_PLATFORM: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
            }

            if resource.io_type == 2:  # TypeInputIo
                for event_type in BUTTON_DEVICE_TRIGGERS_TYPES:
                    triggers.append(
                        {
                            **base_trigger,
                            CONF_TYPE: event_type,
                            CONF_SUBTYPE: f"button {resource.io_offset}",
                        }
                    )

            elif resource.io_type == 49:  # TypeGestureIo
                for event_type in GESTURE_EVENTS_TYPES:
                    triggers.append(
                        {
                            **base_trigger,
                            CONF_TYPE: event_type,
                            CONF_SUBTYPE: f"gesture {resource.io_offset}",
                        }
                    )

            elif resource.io_type == 34:  # TypeMovIo
                for event_type in MOTION_EVENTS_TYPES:
                    triggers.append(
                        {
                            **base_trigger,
                            CONF_TYPE: event_type,
                            CONF_SUBTYPE: f"detector {resource.io_offset}",
                        }
                    )

            elif resource.io_type == 53:  # TypeInputTriggerIo
                for event_type in SIMPLE_PRESS_EVENTS_TYPES:
                    triggers.append(
                        {
                            **base_trigger,
                            CONF_TYPE: event_type,
                            CONF_SUBTYPE: f"button {resource.io_offset}",
                        }
                    )

            elif resource.io_type == 9:  # TypeIrIo
                for event_type in IR_CODE_EVENTS_TYPES:
                    for i in range(1, 33):
                        triggers.append(
                            {
                                **base_trigger,
                                CONF_TYPE: event_type,
                                CONF_SUBTYPE: f"code {i}",
                            }
                        )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action,
    automation_info: dict[str, Any],
) -> Any:
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
        hass, event_config, action, automation_info, platform_type="device"
    )


@callback
def get_domintell_device_id(device_entry: dr.DeviceEntry) -> str | None:
    """Get Domintell device id from device entry."""
    for identifier in device_entry.identifiers:
        if identifier[0] == DOMAIN:
            return identifier[1]
    return None
