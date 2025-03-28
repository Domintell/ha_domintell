"""Domintell event entities from Button resources."""

from __future__ import annotations


from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.components.event import (
    EventDeviceClass,
    EventEntity,
    EventEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .domintell_api import DomintellGateway
from .domintell_api.controllers.sensors import (
    ButtonController,
    MotionController,
)
from .domintell_api.controllers.events import EventType
from .domintell_api.iotypes import PushState, GestureState, MotionState
from .bridge import DomintellBridge

from .const import (
    DOMAIN,
    CONF_SUBTYPE,
    BUTTON_EVENTS_TYPES,
    GESTURE_EVENTS_TYPES,
    MOTION_EVENTS_TYPES,
    SIMPLE_PRESS_EVENTS_TYPES,
    IR_CODE_EVENTS_TYPES,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button from Config Entry."""
    bridge: DomintellBridge = hass.data[DOMAIN][config_entry.entry_id]
    api: DomintellGateway = bridge.api
    controller = api.sensors.button

    @callback
    def async_add_entity(event_type: EventType, resource) -> None:
        """Add entity from Domintell resource."""
        # pylint: disable=unused-argument

        if resource.io_type == 2:  # TypeInputIo
            async_add_entities([DomintellButton(bridge, controller, resource)])
        if resource.io_type == 53:  # TypeInputTriggerIo
            async_add_entities([DomintellButton(bridge, controller, resource)])
        elif resource.io_type == 49:  # TypeGestureIo
            async_add_entities([DomintellGesture(bridge, controller, resource)])
        elif resource.io_type == 9:  # TypeIrIo
            async_add_entities([DomintellIrDetector(bridge, controller, resource)])
        else:
            return

    # Add all current items in controller
    for item in controller:
        async_add_entity(EventType.RESOURCE_ADDED, item)

    # register listener for new items only
    config_entry.async_on_unload(
        controller.subscribe(async_add_entity, event_filter=EventType.RESOURCE_ADDED)
    )


class DomintellButton(EventEntity):
    """Representation of a Domintell Button."""

    def __init__(self, bridge: DomintellBridge, controller: ButtonController, resource):
        """Initialize a Domintell button."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._name = self._resource.io_name
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False
        self._attr_device_class = EventDeviceClass.BUTTON

        # By default button events must be not visible
        self._attr_entity_registry_visible_default = False
        # self._attr_entity_registry_enabled_default = False # TODO désactive donc non utilisable

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}"

        match self._resource.io_type:
            case 2:  # TypeInputIo
                self._attr_device_class = EventDeviceClass.BUTTON
                self._attr_event_types = BUTTON_EVENTS_TYPES
            case 53:  # TypeInputTriggerIo
                if self._resource.module_type == "DST":  # Doorstation
                    self._attr_device_class = EventDeviceClass.DOORBELL
                else:
                    self._attr_device_class = EventDeviceClass.BUTTON
                self._attr_event_types = SIMPLE_PRESS_EVENTS_TYPES
            case _:
                self._attr_device_class = EventDeviceClass.BUTTON
                self._attr_event_types = BUTTON_EVENTS_TYPES

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def name(self) -> str:
        """Return the display name of this button."""
        return self._name

    @callback
    def _handle_event(self, event_type: EventType, resource) -> None:
        """Handle status event for this resource (or it's parent)."""

        if event_type == EventType.RESOURCE_DELETED:
            entity_reg = er.async_get(self.hass)
            entity_reg.async_remove(self.entity_id)
            return

        if event_type == EventType.RESOURCE_UPDATED:
            self._logger.debug("Received status update for %s", self.entity_id)
            match resource.state:
                case PushState.RELEASED:
                    value = "released"
                case PushState.START_SHORT_PUSH:
                    value = "start_short_push"
                case PushState.END_SHORT_PUSH:
                    value = "end_short_push"
                case PushState.START_LONG_PUSH:
                    value = "start_long_push"
                case PushState.END_LONG_PUSH:
                    value = "end_long_push"
                case PushState.PRESSED:
                    value = "pressed"
                case _:
                    value = "unknown"
                    return

            self._trigger_event(value)
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""

        # Add value_changed callbacks.
        self.async_on_remove(
            self._controller.subscribe(
                self._handle_event,
                self._resource.id,
                (EventType.RESOURCE_UPDATED, EventType.RESOURCE_DELETED),
            )
        )


class DomintellGesture(EventEntity):
    """Representation of a Domintell Gesture."""

    def __init__(self, bridge: DomintellBridge, controller: ButtonController, resource):
        """Initialize a Domintell gesture."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._name = self._resource.io_name
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False
        self._attr_device_class = EventDeviceClass.BUTTON
        self._attr_event_types = GESTURE_EVENTS_TYPES

        # By default gesture events must be not visible
        self._attr_entity_registry_visible_default = False

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def name(self) -> str:
        """Return the display name of this button."""
        return self._name

    @callback
    def _handle_event(self, event_type: EventType, resource) -> None:
        """Handle status event for this resource (or it's parent)."""

        if event_type == EventType.RESOURCE_DELETED:
            entity_reg = er.async_get(self.hass)
            entity_reg.async_remove(self.entity_id)
            return

        if event_type == EventType.RESOURCE_UPDATED:
            match resource.state:
                # case GestureState.GESTURE_NONE:
                #     value = "no_gesture"
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
                case GestureState.UNKNOWN:
                    value = "unknown"
                case _:
                    value = "unknown"
                    return

            self._trigger_event(value)
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""

        # Add value_changed callbacks.
        self.async_on_remove(
            self._controller.subscribe(
                self._handle_event,
                self._resource.id,
                (EventType.RESOURCE_UPDATED, EventType.RESOURCE_DELETED),
            )
        )


class DomintellMotion(EventEntity):
    """Representation of a Domintell Motion detector."""

    def __init__(self, bridge: DomintellBridge, controller: MotionController, resource):
        """Initialize a Domintell motion detector."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._name = self._resource.io_name
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False
        self._attr_device_class = EventDeviceClass.MOTION
        self._attr_event_types = MOTION_EVENTS_TYPES

        # By default motion events must be not visible
        self._attr_entity_registry_visible_default = False

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def name(self) -> str:
        """Return the display name of this button."""
        return self._name

    @callback
    def _handle_event(self, event_type: EventType, resource) -> None:
        """Handle status event for this resource (or it's parent)."""

        if event_type == EventType.RESOURCE_DELETED:
            entity_reg = er.async_get(self.hass)
            entity_reg.async_remove(self.entity_id)
            return

        if event_type == EventType.RESOURCE_UPDATED:
            match resource.state:
                case MotionState.START_DETECTION:
                    value = "Start_detection"
                case MotionState.END_DETECTION:
                    value = "End_detection"
                case MotionState.UNKNOWN:
                    value = "unknown"
                    return

            self._trigger_event(value)
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""

        # Add value_changed callbacks.
        self.async_on_remove(
            self._controller.subscribe(
                self._handle_event,
                self._resource.id,
                (EventType.RESOURCE_UPDATED, EventType.RESOURCE_DELETED),
            )
        )


class DomintellIrDetector(EventEntity):
    """Representation of a Domintell IR detector."""

    def __init__(self, bridge: DomintellBridge, controller: ButtonController, resource):
        """Initialize a Domintell IR detector."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._name = self._resource.io_name
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False
        self._attr_device_class = EventDeviceClass.BUTTON
        self._attr_event_types = IR_CODE_EVENTS_TYPES

        # By default IR detector events must be not visible
        self._attr_entity_registry_visible_default = False

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def name(self) -> str:
        """Return the display name of this button."""
        return self._name

    @callback
    def _handle_event(self, event_type: EventType, resource) -> None:
        """Handle status event for this resource (or it's parent)."""

        if event_type == EventType.RESOURCE_DELETED:
            entity_reg = er.async_get(self.hass)
            entity_reg.async_remove(self.entity_id)
            return

        if event_type == EventType.RESOURCE_UPDATED:
            # Note: Type of press (short, long) not handled
            value = IR_CODE_EVENTS_TYPES[resource.key]
            self._trigger_event(value)
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""

        # Add value_changed callbacks.
        self.async_on_remove(
            self._controller.subscribe(
                self._handle_event,
                self._resource.id,
                (EventType.RESOURCE_UPDATED, EventType.RESOURCE_DELETED),
            )
        )
