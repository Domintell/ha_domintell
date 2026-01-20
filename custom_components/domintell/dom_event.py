"""Handle forward of events transmitted by Domintell devices to HASS."""

from __future__ import annotations

from homeassistant.const import CONF_DEVICE_ID, CONF_TYPE
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr


from .domintell_api.controllers.events import EventType
from .domintell_api import DomintellGateway
from .domintell_api.iotypes import PushState, GestureState, MotionState
from .const import (
    DOMAIN,
    ATTR_DOMINTELL_EVENT,
    ATTR_DEVICE,
    CONF_SUBTYPE,
    IR_CODE_EVENTS_TYPES,
)


async def async_setup_domintell_events(bridge):
    """Manage listeners for stateless Domintell sensors that emit events."""
    hass = bridge.hass
    api: DomintellGateway = bridge.api
    btn_controller = api.sensors.button
    conf_entry = bridge.config_entry
    device_reg = dr.async_get(hass)
    conf_uid = conf_entry.unique_id

    @callback
    def handle_button_event(event_type: EventType, resource) -> None:
        """Handle event from Domintell button resource controller."""

        if event_type != EventType.RESOURCE_UPDATED:
            return

        # Guard for missing button object on the resource
        if resource.io_type not in (2, 53):  # "TypeInputIo", "TypeInputTriggerIo"
            return

        if not isinstance(resource.state, PushState):
            return

        module = api.modules.get_module_of_io(resource.id)  # ie: "0A0012BF""
        device_uid = f"{conf_uid}_{module.id}"  # ie: "dnet02-22_0A0012BF"
        device = device_reg.async_get_device(identifiers={(DOMAIN, device_uid)})

        if resource.state == PushState.RELEASED:
            value = "press"
        elif resource.state == PushState.END_SHORT_PUSH:
            value = "short_press"
        elif resource.state == PushState.START_LONG_PUSH:
            value = "long_press"
        else:
            value = "unknown"

        if value != "unknown":
            # Fire event
            data = {
                CONF_DEVICE_ID: device.id,
                ATTR_DEVICE: module.serial_number_text,
                CONF_TYPE: value,
                CONF_SUBTYPE: f"button {resource.io_offset}",
            }

            hass.bus.async_fire(ATTR_DOMINTELL_EVENT, data)

    # add listener for updates from `button` resource
    conf_entry.async_on_unload(
        btn_controller.subscribe(
            handle_button_event, event_filter=EventType.RESOURCE_UPDATED
        )
    )

    @callback
    def handle_gesture_event(event_type: EventType, resource) -> None:
        """Handle event from Domintell gesture resource controller."""

        if event_type != EventType.RESOURCE_UPDATED:
            return

        # Guard for missing gesture object on the resource
        if resource.io_type != 49:  # TypeGestureIo
            return

        if not isinstance(resource.state, GestureState):
            return

        module = api.modules.get_module_of_io(resource.id)
        device_uid = f"{conf_uid}_{module.id}"
        device = device_reg.async_get_device(identifiers={(DOMAIN, device_uid)})

        match resource.state:
            # case GestureState.GESTURE_RIGHT:
            #     value = "gesture_right"
            # case GestureState.GESTURE_LEFT:
            #     value = "gesture_left"
            case GestureState.GESTURE_UP:
                value = "gesture_up"
            case GestureState.GESTURE_DOWN:
                value = "gesture_down"
            # case GestureState.GESTURE_PUSH:
            #     value = "gesture_push"
            case _:
                value = "unknown"
                return

        if value != "unknown":
            # Fire event
            data = {
                CONF_DEVICE_ID: device.id,
                ATTR_DEVICE: module.serial_number_text,
                CONF_TYPE: value,
                CONF_SUBTYPE: f"gesture {resource.io_offset}",
            }

            hass.bus.async_fire(ATTR_DOMINTELL_EVENT, data)

    # add listener for updates from `gesture` resource
    conf_entry.async_on_unload(
        btn_controller.subscribe(
            handle_gesture_event, event_filter=EventType.RESOURCE_UPDATED
        )
    )

    @callback
    def handle_move_event(event_type: EventType, resource) -> None:
        """Handle event from Domintell move resource controller."""

        if event_type != EventType.RESOURCE_UPDATED:
            return

        # Guard for missing gesture object on the resource
        if resource.io_type != 34:  # TypeMovIo
            return

        if not isinstance(resource.state, MotionState):
            return

        module = api.modules.get_module_of_io(resource.id)
        device_uid = f"{conf_uid}_{module.id}"
        device = device_reg.async_get_device(identifiers={(DOMAIN, device_uid)})

        match resource.state:
            case MotionState.START_DETECTION:
                value = "Start_detection"
            case MotionState.END_DETECTION:
                value = "End_detection"
            case MotionState.UNKNOWN:
                value = "unknown"
                return

        if value != "unknown":
            # Fire event
            data = {
                CONF_DEVICE_ID: device.id,
                ATTR_DEVICE: module.serial_number_text,
                CONF_TYPE: value,
                CONF_SUBTYPE: f"detector {resource.io_offset}",
            }

            hass.bus.async_fire(ATTR_DOMINTELL_EVENT, data)

    # add listener for updates from `gesture` resource
    conf_entry.async_on_unload(
        btn_controller.subscribe(
            handle_move_event, event_filter=EventType.RESOURCE_UPDATED
        )
    )

    @callback
    def handle_ir_detector_event(event_type: EventType, resource) -> None:
        """Handle event from Domintell ir detector resource controller."""

        if event_type != EventType.RESOURCE_UPDATED:
            return

        # Guard for missing gesture object on the resource
        if resource.io_type != 9:  # TypeIrIo
            return

        if not isinstance(resource.state, PushState):
            return

        if not isinstance(resource.key, int):
            return

        module = api.modules.get_module_of_io(resource.id)
        device_uid = f"{conf_uid}_{module.id}"
        device = device_reg.async_get_device(identifiers={(DOMAIN, device_uid)})

        value = IR_CODE_EVENTS_TYPES[resource.key]

        if resource.state != PushState.UNKNOWN:
            # Fire event
            data = {
                CONF_DEVICE_ID: device.id,
                ATTR_DEVICE: module.serial_number_text,
                CONF_TYPE: value,
                CONF_SUBTYPE: f"code {resource.key}",
            }

            hass.bus.async_fire(ATTR_DOMINTELL_EVENT, data)

    # add listener for updates from `gesture` resource
    conf_entry.async_on_unload(
        btn_controller.subscribe(
            handle_ir_detector_event, event_filter=EventType.RESOURCE_UPDATED
        )
    )
