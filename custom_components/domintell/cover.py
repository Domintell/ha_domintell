"""Creates Domintell cover entities."""

from __future__ import annotations
from typing import Any


from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.components.cover import (
    DOMAIN as COVER_DOMAIN,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .domintell_api import DomintellGateway
from .domintell_api.controllers import CoversController
from .domintell_api.controllers.events import EventType
from .domintell_api.iotypes import CoverState
from .bridge import DomintellBridge
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up cover from Config Entry."""
    bridge: DomintellBridge = hass.data[DOMAIN][config_entry.entry_id]
    api: DomintellGateway = bridge.api
    controller = api.covers

    @callback
    def async_add_entity(event_type: EventType, resource) -> None:
        """Add entity from Domintell resource."""
        # pylint: disable=unused-argument

        async_add_entities([DomintellCover(bridge, controller, resource)])

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
        if entity.domain != COVER_DOMAIN:
            continue

        part = entity.unique_id.split("_")
        if len(part) >= 3:
            endpoint_id = part[2]

            if endpoint_id not in controller.keys():
                entity_reg.async_remove(entity.entity_id)


class DomintellCover(CoverEntity):
    """Representation of a Domintell Cover."""

    def __init__(self, bridge: DomintellBridge, controller: CoversController, resource):
        """Initialize a Domintell cover."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._name = self._resource.io_name
        self._state = self._resource.state
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False
        self._attr_device_class = CoverDeviceClass.SHUTTER
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

        # Case of Covers group
        self._status_ref_io: str | None = None
        if self._resource.module_type == "MEM":
            ref_io: str = self._resource.ref_io

            if ref_io is not None:
                self._status_ref_io = self._api.modules.get_io(ref_io)
                self._state = self._status_ref_io.state

    @property
    def name(self) -> str:
        """Return the display name of this cover."""
        return self._name

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        return self._state == CoverState.STOPPED_DOWN

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        return self._state == CoverState.MOVING_DOWN

    @property
    def is_opening(self) -> bool:
        """Return if the cover is closing."""
        return self._state == CoverState.MOVING_UP

    @property
    def current_cover_position(self) -> int:
        """Return the cover position."""
        # Workaround, because we don't have the position information
        if self._state == CoverState.STOPPED_DOWN:
            return 10
        elif self._state == CoverState.STOPPED_UP:
            return 90
        else:
            return 50

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Fire the stop action."""
        # pylint: disable=unused-argument

        await self._resource.stop()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Move the cover up."""
        # pylint: disable=unused-argument

        await self._resource.move_up()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Move the cover down."""
        # pylint: disable=unused-argument

        await self._resource.move_down()

    @callback
    def _handle_event(self, event_type: EventType, resource) -> None:
        """Handle status event for this resource."""
        # pylint: disable=unused-argument

        if event_type == EventType.RESOURCE_DELETED:
            entity_reg = er.async_get(self.hass)
            entity_reg.async_remove(self.entity_id)
            return

        if event_type == EventType.RESOURCE_UPDATED:
            self._state = (
                self._status_ref_io.state
                if self._status_ref_io is not None
                else self._resource.state
            )
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
