"""Creates Domintell switch entities."""

from __future__ import annotations


from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SwitchDeviceClass,
    SwitchEntity,
)
from homeassistant.const import EntityCategory

from .domintell_api import DomintellGateway
from .domintell_api.controllers import SwitchesController, VariablesController
from .domintell_api.controllers.events import EventType, ResourceTypes
from .bridge import DomintellBridge
from .const import DOMAIN

type ControllerType = (SwitchesController | VariablesController)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch from Config Entry."""
    bridge: DomintellBridge = hass.data[DOMAIN][config_entry.entry_id]
    api: DomintellGateway = bridge.api
    switches_controller: SwitchesController = api.switches
    variables_controller: VariablesController = api.variables

    @callback
    def register_items(controller: ControllerType):
        """Register items from controller."""

        @callback
        def async_add_entity(event_type: EventType, resource) -> None:
            """Add entity from Domintell resource."""
            # pylint: disable=unused-argument

            add_entity_flag = True
            if controller.item_type == ResourceTypes.VARIABLE:
                if (
                    resource.id == "SYS000000-17-9"  # Endpoint Night/Day
                    or not resource.is_bool_status
                    or resource.is_master_only
                ):
                    add_entity_flag = False

                if resource.id == "SYS000000-17-0":  # Endpoint presence simulation
                    add_entity_flag = True

            if add_entity_flag:
                async_add_entities([DomintellSwitch(bridge, controller, resource)])

        for item in controller:
            async_add_entity(EventType.RESOURCE_ADDED, item)

        # Register listener for new items only
        config_entry.async_on_unload(
            controller.subscribe(
                async_add_entity, event_filter=EventType.RESOURCE_ADDED
            )
        )

    # Setup for each switch from domintell resource
    register_items(switches_controller)
    register_items(variables_controller)

    # Check for entities that no longer exist and remove them
    entity_reg = er.async_get(hass)
    reg_entities = er.async_entries_for_config_entry(entity_reg, config_entry.entry_id)

    for entity in reg_entities:
        if entity.domain != SWITCH_DOMAIN:
            continue

        part = entity.unique_id.split("_")
        if len(part) >= 3:
            endpoint_id = part[2]

            if (
                endpoint_id not in switches_controller.keys()
                and endpoint_id not in variables_controller.keys()
            ):
                entity_reg.async_remove(entity.entity_id)


class DomintellSwitch(SwitchEntity):
    """Representation of a Domintell Switch."""

    def __init__(
        self, bridge: DomintellBridge, controller: SwitchesController, resource
    ):
        """Initialize a Domintell switch."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._name = self._resource.io_name
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False
        self._attr_device_class = SwitchDeviceClass.SWITCH

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

        if self._resource.target_type == ResourceTypes.VARIABLE.value:
            if hasattr(self._resource, "is_read_only"):
                if self._resource.is_read_only:
                    self._attr_entity_category = EntityCategory.DIAGNOSTIC
                else:
                    self._attr_entity_category = EntityCategory.CONFIG

            if self._resource.module_type == "SYS" and self._resource.io_offset == 0:
                self._attr_key = "presence_simulation"
                self._attr_translation_key = "presence_simulation"

        # Case of Switches group
        self._status_ref_io: str | None = None
        if self._resource.module_type == "MEM":
            ref_io: str = self._resource.ref_io

            if ref_io is not None:
                self._status_ref_io = self._api.modules.get_io(ref_io)

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return self._name

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        if self._status_ref_io is not None:
            return self._status_ref_io.is_on()
        return self._resource.is_on()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        # pylint: disable=unused-argument

        await self._resource.turn_on()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        # pylint: disable=unused-argument

        await self._resource.turn_off()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        # pylint: disable=unused-argument

        await self._resource.toggle()

    @callback
    def _handle_event(self, event_type: EventType, resource) -> None:
        """Handle status event for this resource."""
        # pylint: disable=unused-argument

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

        if self._status_ref_io is not None:
            self.async_on_remove(
                self._controller.subscribe(
                    self._handle_event,
                    self._status_ref_io.id,
                    (EventType.RESOURCE_UPDATED, EventType.RESOURCE_DELETED),
                )
            )
