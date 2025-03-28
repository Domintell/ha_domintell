"""Creates Domintell fan entities."""

from __future__ import annotations
import math
from typing import Any


from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.components.fan import (
    DOMAIN as FAN_DOMAIN,
    FanEntity,
    FanEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ranged_value_to_percentage,
    percentage_to_ranged_value,
)
from homeassistant.util.scaling import int_states_in_range


from .domintell_api import DomintellGateway
from .domintell_api.controllers import FansController
from .domintell_api.controllers.events import EventType
from .bridge import DomintellBridge
from .const import DOMAIN

PRESET_MODE_AUTO = "AUTO"
PRESET_MODE_MANUAL = "MANUAL"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch from Config Entry."""
    bridge: DomintellBridge = hass.data[DOMAIN][config_entry.entry_id]
    api: DomintellGateway = bridge.api
    controller = api.fans

    @callback
    def async_add_entity(event_type: EventType, resource) -> None:
        """Add entity from Domintell resource."""
        # pylint: disable=unused-argument

        async_add_entities([DomintellFan(bridge, controller, resource)])

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
        if entity.domain != FAN_DOMAIN:
            continue

        part = entity.unique_id.split("_")
        if len(part) >= 3:
            endpoint_id = part[2]

            if endpoint_id not in controller.keys():
                entity_reg.async_remove(entity.entity_id)


class DomintellFan(FanEntity):
    """Representation of a Domintell Fan."""

    def __init__(self, bridge: DomintellBridge, controller: FansController, resource):
        """Initialize a Domintell Fan."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._name = self._resource.io_name
        self._number_of_speeds = self._resource.number_of_speeds
        self._has_auto_speed = self._resource.has_auto_speed
        self._has_off_speed = self._resource.has_off_speed
        self._supports_speed = self._resource.supports_speed()
        self._mode = self._resource.mode
        self._speed = self._resource.speed
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

        # Case of Fans group
        self._status_ref_io: str | None = None
        if self._resource.module_type == "MEM":
            ref_io: str = self._resource.ref_io

            if ref_io is not None:
                self._status_ref_io = self._api.modules.get_io(ref_io)
                self._number_of_speeds = self._status_ref_io.number_of_speeds
                self._has_auto_speed = self._status_ref_io.has_auto_speed
                self._has_off_speed = self._status_ref_io.has_off_speed
                self._supports_speed = self._status_ref_io.supports_speed()
                self._mode = self._status_ref_io.mode
                self._speed = self._status_ref_io.speed

        # Configuration of fan
        self._speed_range = (1, self._number_of_speeds)

        features = FanEntityFeature.TURN_ON
        if self._supports_speed:
            features |= FanEntityFeature.SET_SPEED
        if self._has_off_speed:
            features |= FanEntityFeature.TURN_OFF
        if self._has_auto_speed:
            features |= FanEntityFeature.PRESET_MODE
            self._attr_preset_modes = [PRESET_MODE_MANUAL, PRESET_MODE_AUTO]

        self._attr_supported_features = features

    @property
    def name(self) -> str:
        """Return the display name of this Fan."""
        return self._name

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return int_states_in_range(self._speed_range)

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage for the fan."""
        percentage = 0

        if self.is_on:
            percentage = ranged_value_to_percentage(self._speed_range, self._speed)

        return percentage

    @property
    def preset_mode(self) -> int:
        """Return the current preset mode of the fan."""
        return self._mode

    @property
    def is_on(self) -> bool | None:
        """Return true if fan is on."""
        if self._status_ref_io is not None:
            return self._status_ref_io.is_on()
        return self._resource.is_on()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the Fan off."""
        # pylint: disable=unused-argument

        await self._resource.turn_off()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        # pylint: disable=unused-argument

        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)
        else:
            await self.async_set_percentage(100)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""

        if percentage == 0:
            await self.async_turn_off()
            return

        bond_speed = math.ceil(
            percentage_to_ranged_value(self._speed_range, percentage)
        )
        self._logger.debug(
            "async_set_percentage converted percentage %s to bond speed %s",
            percentage,
            bond_speed,
        )

        await self._resource.set_value(bond_speed)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        if self._has_auto_speed:
            await self._resource.set_mode(preset_mode)

    @callback
    def _handle_event(self, event_type: EventType, resource) -> None:
        """Handle status event for this resource."""

        if event_type == EventType.RESOURCE_DELETED:
            entity_reg = er.async_get(self.hass)
            entity_reg.async_remove(self.entity_id)
            return

        if event_type == EventType.RESOURCE_UPDATED:
            self._mode = (
                self._status_ref_io.mode
                if self._status_ref_io is not None
                else self._resource.mode
            )
            self._speed = (
                self._status_ref_io.speed
                if self._status_ref_io is not None
                else self._resource.speed
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
