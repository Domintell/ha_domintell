"""Creates Domintell binary sensor entities."""

from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType


from .domintell_api import DomintellGateway
from .domintell_api.controllers import SensorsController
from .domintell_api.controllers.sensors import (
    MotionController,
    ContactController,
    TamperController,
)
from .domintell_api.controllers.events import EventType
from .domintell_api.iotypes import MotionState
from .bridge import DomintellBridge
from .const import DOMAIN

type ControllerType = (MotionController | ContactController | TamperController)


@dataclass(frozen=True, kw_only=True)
class DomintellBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing Domintell sensor entities."""

    enabled_fn: Callable[[Any], bool] = lambda data: True
    exists_fn: Callable[[Any], bool]
    value_fn: Callable[[Any], StateType]


BINARY_SENSORS: dict[DomintellBinarySensorEntityDescription] = {
    "motion": DomintellBinarySensorEntityDescription(
        key="motion",
        translation_key="motion",
        device_class=BinarySensorDeviceClass.MOTION,
        value_fn=lambda data: data.motion,
        exists_fn=lambda resource: True if hasattr(resource, "motion") else False,
    ),
    "contact": DomintellBinarySensorEntityDescription(
        key="contact",
        translation_key="contact",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=lambda data: data.opened,
        exists_fn=lambda resource: True if hasattr(resource, "contact") else False,
    ),
    "tamper": DomintellBinarySensorEntityDescription(
        key="tamper",
        translation_key="tamper",
        device_class=BinarySensorDeviceClass.TAMPER,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.opened,
        exists_fn=lambda resource: True if hasattr(resource, "tamper") else False,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor from Config Entry."""
    bridge: DomintellBridge = hass.data[DOMAIN][config_entry.entry_id]
    api: DomintellGateway = bridge.api
    controller = api.sensors

    @callback
    def register_items(controller: ControllerType):
        """Register items from controller."""

        @callback
        def async_add_entity(event_type: EventType, resource) -> None:
            """Add entity from Domintell resource."""
            # pylint: disable=unused-argument

            if included := BINARY_SENSORS.get(resource.target_type):
                # Initialize binary sensors
                sensor_entities: list = [
                    DomintellBinarySensor(bridge, controller, resource, description)
                    for description in BINARY_SENSORS.values()
                    if description.exists_fn(resource)
                ]

                async_add_entities(sensor_entities)
            else:
                # Do nothing
                pass

        # Add all current items from controller
        for item in controller:
            async_add_entity(EventType.RESOURCE_ADDED, item)

        # register listener for new items only
        config_entry.async_on_unload(
            controller.subscribe(
                async_add_entity, event_filter=EventType.RESOURCE_ADDED
            )
        )

    # Setup for each binary sensor from domintell resource
    register_items(controller.motion)

    # Check for entities that no longer exist and remove them
    entity_reg = er.async_get(hass)
    reg_entities = er.async_entries_for_config_entry(entity_reg, config_entry.entry_id)

    for entity in reg_entities:
        if entity.domain != BINARY_SENSOR_DOMAIN:
            continue

        part = entity.unique_id.split("_")
        if len(part) >= 3:
            endpoint_id = part[2]

            if endpoint_id not in controller.motion.keys():
                entity_reg.async_remove(entity.entity_id)


class DomintellBinarySensor(BinarySensorEntity):
    """Representation of a Domintell binary sensor."""

    entity_description: DomintellBinarySensorEntityDescription

    def __init__(
        self,
        bridge: DomintellBridge,
        controller: MotionController,
        resource,
        description: DomintellBinarySensorEntityDescription,
    ):
        """Initialize Domintell Binary sensor."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._attr_should_poll = False
        self._attr_assumed_state = False
        self._attr_has_entity_name = True
        self.entity_description = description
        if not description.enabled_fn(self._resource.state):
            self._attr_entity_registry_enabled_default = False

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}_{description.key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

    @property
    def is_on(self) -> bool | None:
        """Return the value reported by the binary sensor."""
        return self.entity_description.value_fn(self._resource)

    @callback
    def _handle_event(self, event_type: EventType, resource) -> None:
        """Handle status event for this resource."""

        if event_type == EventType.RESOURCE_DELETED:
            entity_reg = er.async_get(self.hass)
            entity_reg.async_remove(self.entity_id)
            return

        if event_type == EventType.RESOURCE_UPDATED:
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
