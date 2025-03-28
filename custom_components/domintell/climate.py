"""Creates Domintell switch entities."""

from __future__ import annotations
from enum import Enum
from typing import Final


from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    ATTR_TEMPERATURE,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TARGET_TEMP_HIGH,
    SWING_OFF,
    SWING_ON,
)

from .domintell_api import DomintellGateway
from .domintell_api.controllers.sensors import TemperatureController
from .domintell_api.controllers.events import EventType
from .domintell_api.iotypes import TemperatureMode, RegulationMode
from .bridge import DomintellBridge
from .const import DOMAIN


class PresetMode(Enum):
    ABSENCE = "absence"
    AUTO = "auto"
    COMFORT = "comfort"
    FROST = "frost"


TEMPERATURE_MODE_TO_HASS: Final[dict[TemperatureMode, PresetMode]] = {
    TemperatureMode.ABSENCE: PresetMode.ABSENCE,
    TemperatureMode.AUTO: PresetMode.AUTO,
    TemperatureMode.COMFORT: PresetMode.COMFORT,
    TemperatureMode.FROST: PresetMode.FROST,
}

REGULATION_MODE_TO_HASS: Final[dict[RegulationMode, HVACMode]] = {
    RegulationMode.OFF: HVACMode.OFF,
    RegulationMode.HEATING: HVACMode.HEAT,
    RegulationMode.COOLING: HVACMode.COOL,
    RegulationMode.MIXED: HVACMode.HEAT_COOL,
    RegulationMode.AUTO: HVACMode.AUTO,
    RegulationMode.DRY: HVACMode.DRY,
    RegulationMode.FAN: HVACMode.FAN_ONLY,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch from Config Entry."""
    bridge: DomintellBridge = hass.data[DOMAIN][config_entry.entry_id]
    api: DomintellGateway = bridge.api
    controller = api.sensors.temperature

    @callback
    def async_add_entity(event_type: EventType, resource) -> None:
        """Add entity from Domintell resource."""
        # pylint: disable=unused-argument

        if resource.is_thermostat:
            async_add_entities([DomintellThermostat(bridge, controller, resource)])

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
        if entity.domain != CLIMATE_DOMAIN:
            continue

        part = entity.unique_id.split("_")
        if len(part) >= 3:
            endpoint_id = part[2]

            if endpoint_id not in controller.keys():
                entity_reg.async_remove(entity.entity_id)


class DomintellThermostat(ClimateEntity):
    """Representation of a Domintell Thermostat."""

    def __init__(
        self, bridge: DomintellBridge, controller: TemperatureController, resource
    ):
        """Initialize a Domintell thermostat."""
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

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
        )

        configuration = self._resource.config
        self._attr_hvac_modes = []
        self._attr_preset_modes = []

        for mode in configuration.regulation_modes:
            self._attr_hvac_modes.append(REGULATION_MODE_TO_HASS.get(mode))

        for mode in configuration.temperature_modes:
            self._attr_preset_modes.append(TEMPERATURE_MODE_TO_HASS.get(mode).value)

        self._attr_supported_features = ClimateEntityFeature.TURN_OFF

        if self._attr_preset_modes:
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

        if (
            (
                (HVACMode.HEAT in self._attr_hvac_modes)
                and (HVACMode.COOL in self._attr_hvac_modes)
            )
            or HVACMode.HEAT_COOL in self._attr_hvac_modes
            or HVACMode.DRY in self._attr_hvac_modes
            or HVACMode.FAN_ONLY in self._attr_hvac_modes
        ):
            self._attr_supported_features |= (
                ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            )
        else:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def name(self) -> str:
        """Return the display name of this thermostat."""
        return self._name

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current hvac mode."""
        mode = self._resource.regulation_mode
        return REGULATION_MODE_TO_HASS.get(mode, HVACMode.AUTO)

    @property
    def hvac_action(self) -> HVACAction:
        """The current HVAC action."""
        mode = self._resource.regulation_mode

        match mode:
            case RegulationMode.OFF:
                return HVACAction.OFF
            case RegulationMode.HEATING:
                if (
                    self.current_temperature
                    < self._resource.state.active_heating_setpoint
                ):
                    return HVACAction.HEATING
                else:
                    return HVACAction.IDLE
            case RegulationMode.COOLING:
                if (
                    self.current_temperature
                    > self._resource.state.active_cooling_setpoint
                ):
                    return HVACAction.COOLING
                else:
                    return HVACAction.IDLE
            case RegulationMode.DRY:
                return HVACAction.DRYING
            case RegulationMode.FAN:
                return HVACAction.FAN
            case RegulationMode.MIXED | RegulationMode.AUTO:
                if (
                    self.current_temperature is not None
                    and self.target_temperature_low is not None
                ):
                    if self.current_temperature > self.target_temperature_high:
                        return HVACAction.COOLING
                    elif self.current_temperature < self.target_temperature_low:
                        return HVACAction.HEATING
                    else:
                        return HVACAction.IDLE
            case _:
                return HVACAction.IDLE

    @property
    def preset_mode(self) -> str:
        """Return the current preset mode."""
        mode = self._resource.temperature_mode
        preset = TEMPERATURE_MODE_TO_HASS.get(mode, PresetMode.AUTO).value
        return preset

    @property
    def temperature_unit(self) -> str:
        """Return the temperature_unit."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float:
        """Return the state of the sensor."""
        return self._resource.temperature

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step size a target temperature
        can be increased or decreased.
        """
        return self._resource.config.setpoint_step

    @property
    def target_temperature(self) -> float:
        """Return the temperature currently set to be reached."""
        mode = self._resource.regulation_mode

        match mode:
            case RegulationMode.HEATING:
                return self._resource.state.active_heating_setpoint
            case RegulationMode.COOLING:
                return self._resource.state.active_cooling_setpoint
            case _:
                return self._resource.state.active_heating_setpoint

    @property
    def target_temperature_high(self) -> float:
        """Return the upper bound target temperature."""
        return self._resource.state.active_cooling_setpoint

    @property
    def target_temperature_low(self) -> float:
        """Return the lower bound target temperature."""
        return self._resource.state.active_heating_setpoint

    @property
    def max_temp(self) -> float:
        """Return max temperature for the device."""
        return max(
            self._resource.config.heat_limit_high, self._resource.config.cool_limit_high
        )

    @property
    def min_temp(self) -> float:
        """Return min temperature for the device."""
        return min(
            self._resource.config.heat_limit_low, self._resource.config.cool_limit_low
        )

    async def async_turn_off(self):
        """Turn the entity off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""

        if ATTR_TEMPERATURE in kwargs:
            active_setpoint = kwargs[ATTR_TEMPERATURE]
            if self.hvac_mode == HVACMode.HEAT:
                await self._resource.set_heating_set_point(active_setpoint)
            elif self.hvac_mode == HVACMode.COOL:
                await self._resource.set_cooling_set_point(active_setpoint)
            else:
                pass

        if ATTR_TARGET_TEMP_LOW in kwargs:
            await self._resource.set_heating_set_point(kwargs[ATTR_TARGET_TEMP_LOW])

        if ATTR_TARGET_TEMP_HIGH in kwargs:
            await self._resource.set_cooling_set_point(kwargs[ATTR_TARGET_TEMP_HIGH])

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set hvac mode."""

        regulation_mode = RegulationMode.OFF
        match hvac_mode:
            case HVACMode.OFF:
                regulation_mode = RegulationMode.OFF
            case HVACMode.HEAT:
                regulation_mode = RegulationMode.HEATING
            case HVACMode.COOL:
                regulation_mode = RegulationMode.COOLING
            case HVACMode.HEAT_COOL:
                regulation_mode = RegulationMode.MIXED
            case HVACMode.AUTO:
                regulation_mode = RegulationMode.AUTO
            case HVACMode.DRY:
                regulation_mode = RegulationMode.DRY
            case HVACMode.FAN_ONLY:
                regulation_mode = RegulationMode.FAN
            case _:
                return

        await self._resource.set_mode_regulation(regulation_mode)

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""

        temperature_mode = TemperatureMode.AUTO
        mode: PresetMode = PresetMode(preset_mode)

        match mode:
            case PresetMode.ABSENCE:
                temperature_mode = TemperatureMode.ABSENCE
            case PresetMode.AUTO:
                temperature_mode = TemperatureMode.AUTO
            case PresetMode.COMFORT:
                temperature_mode = TemperatureMode.COMFORT
            case PresetMode.FROST:
                temperature_mode = TemperatureMode.FROST
            case _:
                return

        await self._resource.set_mode_temperature(temperature_mode)

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
