"""Creates Domintell number entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.number import (
    DOMAIN as NUMBER_DOMAIN,
    NumberEntity,
)
from homeassistant.const import EntityCategory


from .domintell_api import DomintellGateway
from .domintell_api.controllers import VariablesController
from .domintell_api.controllers.events import EventType
from .bridge import DomintellBridge
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number from Config Entry."""
    bridge: DomintellBridge = hass.data[DOMAIN][config_entry.entry_id]
    api: DomintellGateway = bridge.api
    controller = api.variables

    @callback
    def async_add_entity(event_type: EventType, resource) -> None:
        """Add entity from Domintell resource."""
        # pylint: disable=unused-argument

        if resource.is_bool_status == False and resource.is_master_only == False:
            async_add_entities([DomintellVariable(bridge, controller, resource)])

    # Add all current items in controller
    for item in controller:
        async_add_entity(EventType.RESOURCE_ADDED, item)

    # Register listener for new items only
    config_entry.async_on_unload(
        controller.subscribe(async_add_entity, event_filter=EventType.RESOURCE_ADDED)
    )

    # Check for entities that no longer exist and remove them
    entity_reg = er.async_get(hass)
    reg_entities = er.async_entries_for_config_entry(entity_reg, config_entry.entry_id)

    for entity in reg_entities:
        if entity.domain != NUMBER_DOMAIN:
            continue

        part = entity.unique_id.split("_")
        if len(part) >= 3:
            endpoint_id = part[2]

            if endpoint_id not in controller.keys():
                entity_reg.async_remove(entity.entity_id)


class DomintellVariable(NumberEntity):
    """Representation of a Domintell Variable."""

    def __init__(
        self, bridge: DomintellBridge, controller: VariablesController, resource
    ):
        """Initialize a Domintell variable."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._name = self._resource.io_name
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}"

        # Variables are attached to the bridge
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

        if self._resource.is_read_only:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        else:
            self._attr_entity_category = EntityCategory.CONFIG

        self._attr_entity_mode = "auto"
        self._attr_native_step = 1
        range_start, range_end = self._resource.state_range
        self._attr_native_min_value = range_start
        self._attr_native_max_value = range_end

    @property
    def name(self) -> str:
        """Return the display name of this variable."""
        return self._name

    @property
    def native_value(self) -> int | None:
        """Return the number value."""
        return self._resource.state

    async def async_set_native_value(self, value: float) -> None:
        """Change to new number value."""

        data: int = round(value)
        await self._resource.set_value(data)

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
