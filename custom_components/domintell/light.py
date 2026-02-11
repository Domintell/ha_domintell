"""Creates Domintell light entities."""

from __future__ import annotations
import math


from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.components.light import (
    DOMAIN as LIGHT_DOMAIN,
    ATTR_RGBW_COLOR,
    ATTR_RGB_COLOR,
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.color import (
    value_to_brightness,
    brightness_to_value,
)

from .domintell_api import DomintellGateway
from .domintell_api.controllers import LightsController
from .domintell_api.controllers.events import EventType
from .domintell_api.const import LED_INDICATOR_IO_TYPE_LIST
from .bridge import DomintellBridge
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up light from Config Entry."""
    bridge: DomintellBridge = hass.data[DOMAIN][config_entry.entry_id]
    api: DomintellGateway = bridge.api
    controller = api.lights

    @callback
    def async_add_entity(event_type: EventType, resource) -> None:
        """Add entity from Domintell resource."""
        # pylint: disable=unused-argument

        async_add_entities([DomintellLight(bridge, controller, resource)])

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
        if entity.domain != LIGHT_DOMAIN:
            continue

        part = entity.unique_id.split("_")
        if len(part) >= 3:
            endpoint_id = part[2]

            if endpoint_id not in controller.keys():
                entity_reg.async_remove(entity.entity_id)


class DomintellLight(LightEntity):
    """Representation of a Domintell Light."""

    def __init__(self, bridge: DomintellBridge, controller: LightsController, resource):
        """Initialize a Domintell light."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._brightness: int = 0
        self._color_rgbw: tuple = (0, 0, 0, 0)
        self._color_rgb: tuple = (0, 0, 0)

        self._name = self._resource.io_name
        self._state = self._resource.state
        self._color_mode = self._resource.color_mode
        if hasattr(self._resource, "brightness_scale"):
            self._brightness_scale = self._resource.brightness_scale
            self._brightness = self._resource.brightness

        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False

        # By default indicator light must be desabled and not visible
        if self._resource.io_type in LED_INDICATOR_IO_TYPE_LIST:
            self._attr_entity_registry_enabled_default = False
            self._attr_entity_registry_visible_default = False

        module = self._api.modules.get_module_of_io(self._resource.id)
        device_id = f"{self._bridge.config_entry.unique_id}_{module.id}"
        self._attr_unique_id = f"{device_id}_{resource.id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

        # Case of Lights group
        self._status_ref_io: str | None = None
        if self._resource.module_type == "MEM":
            self._color_mode = set()
            ref_io: str = self._resource.ref_io

            if ref_io is not None:
                self._status_ref_io = self._api.modules.get_io(ref_io)
                if self._status_ref_io is not None:
                    self._color_mode = self._status_ref_io.color_mode
                    self._state = self._status_ref_io.state
                    if hasattr(self._resource, "brightness_scale"):
                        self._brightness_scale = self._status_ref_io.brightness_scale
                        self._brightness = self._status_ref_io.brightness

        self._attr_supported_color_modes: set[ColorMode] = set()

        if ColorMode.RGBW in self._color_mode:
            self._attr_supported_color_modes.add(ColorMode.RGBW)

        elif ColorMode.RGB in self._color_mode:
            self._attr_supported_color_modes.add(ColorMode.RGB)

        elif ColorMode.BRIGHTNESS in self._color_mode:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)

        if not self._attr_supported_color_modes:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)

        if hasattr(resource, "light_type"):
            self._attr_extra_state_attributes = {"light_type": resource.light_type}

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        if self._status_ref_io is not None:
            return self._status_ref_io.is_on()
        return self._resource.is_on()

    @property
    def rgb_color(self) -> tuple | None:
        """Return the RGB color value of this light."""
        if self.color_mode == ColorMode.RGB:
            return self._state.as_tuple()[:3]
        else:
            return None

    @property
    def rgbw_color(self) -> tuple | None:
        """Return the RGBW color value of this light."""
        if self.color_mode == ColorMode.RGBW:
            return self._state.as_tuple()[:4]
        else:
            return None

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..100."""
        return value_to_brightness(self._brightness_scale, self._brightness)

    @property
    def color_mode(self) -> ColorMode | None:
        """Return the color mode of the light."""

        if ColorMode.RGBW in self._color_mode:
            color_mode = ColorMode.RGBW
        elif ColorMode.RGB in self._color_mode:
            color_mode = ColorMode.RGB
        elif ColorMode.BRIGHTNESS in self._color_mode:
            color_mode = ColorMode.BRIGHTNESS
        else:
            color_mode = ColorMode.ONOFF

        return color_mode

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the light on."""

        if ATTR_RGBW_COLOR in kwargs:
            self._color_rgbw = kwargs[ATTR_RGBW_COLOR]
            await self._resource.set_color(
                {
                    "r": self._color_rgbw[0],
                    "g": self._color_rgbw[1],
                    "b": self._color_rgbw[2],
                    "w": self._color_rgbw[3],
                }
            )

        elif ATTR_RGB_COLOR in kwargs:
            self._color_rgb = kwargs[ATTR_RGB_COLOR]
            await self._resource.set_color(
                {
                    "r": self._color_rgb[0],
                    "g": self._color_rgb[1],
                    "b": self._color_rgb[2],
                }
            )

        elif ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            value_in_range = math.ceil(
                brightness_to_value(self._brightness_scale, brightness)
            )
            await self._resource.set_value(value_in_range)

        else:
            await self._resource.turn_on()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the light off."""
        # pylint: disable=unused-argument

        await self._resource.turn_off()

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

            if self._status_ref_io is not None or hasattr(self._resource, "brightness"):
                self._brightness = (
                    self._status_ref_io.brightness
                    if self._status_ref_io is not None
                    else self._resource.brightness
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
