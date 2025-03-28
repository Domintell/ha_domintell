"""Creates Domintell sensor entities."""

from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    LIGHT_LUX,
    PERCENTAGE,
    DEGREE,
    CONCENTRATION_PARTS_PER_MILLION,
    EntityCategory,
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfEnergy,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType


from .domintell_api import DomintellGateway
from .domintell_api.controllers import VariablesController
from .domintell_api.controllers.sensors import (
    TemperatureController,
    IlluminanceController,
    HumidityController,
    PressureController,
    CO2Controller,
    WindController,
    PowerSupplyController,
    ElectricityController,
)
from .domintell_api.controllers.events import EventType, ResourceTypes
from .bridge import DomintellBridge
from .const import DOMAIN

type ControllerType = (
    TemperatureController
    | IlluminanceController
    | HumidityController
    | PressureController
    | CO2Controller
    | WindController
    | PowerSupplyController
    | ElectricityController
    | VariablesController
)


def to_percentage(value: float | None) -> float | None:
    """Convert 0..1 value to percentage when value is not None."""
    return value * 100 if value is not None else None


@dataclass(frozen=True, kw_only=True)
class DomintellSensorEntityDescription(SensorEntityDescription):
    """Class describing Domintell sensor entities."""

    enabled_fn: Callable[[Any], bool] = lambda data: True
    exists_fn: Callable[[Any], bool]
    value_fn: Callable[[Any], StateType]


SENSORS: dict[DomintellSensorEntityDescription] = {
    "temperature": DomintellSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.temperature,
        exists_fn=lambda resource: True if hasattr(resource, "temperature") else False,
    ),
    "illuminance": DomintellSensorEntityDescription(
        key="illuminance",
        translation_key="illuminance",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.illuminance,
        exists_fn=lambda resource: True if hasattr(resource, "illuminance") else False,
    ),
    "humidity": DomintellSensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda resource: resource.humidity,
        exists_fn=lambda resource: True if hasattr(resource, "humidity") else False,
    ),
    "pressure": DomintellSensorEntityDescription(
        key="pressure",
        translation_key="pressure",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda resource: resource.pressure,
        exists_fn=lambda resource: True if hasattr(resource, "pressure") else False,
    ),
    "carbon_dioxide": DomintellSensorEntityDescription(
        key="co2",
        translation_key="carbon_dioxide",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.co2,
        exists_fn=lambda resource: True if hasattr(resource, "co2") else False,
    ),
    "voltage": DomintellSensorEntityDescription(
        key="voltage",
        translation_key="voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.voltage,
        exists_fn=lambda resource: True if hasattr(resource, "voltage") else False,
    ),
    "analog": DomintellSensorEntityDescription(
        key="analog",
        translation_key="value",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.value,
        exists_fn=lambda resource: True if hasattr(resource, "value") else False,
    ),
    "percent": DomintellSensorEntityDescription(
        key="percent",
        translation_key="percentage",
        icon="mdi:percent",  # TODO
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.percent,
        exists_fn=lambda resource: True if hasattr(resource, "percent") else False,
    ),
    "liter": DomintellSensorEntityDescription(
        key="volume_liter",
        translation_key="volume",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.liter,
        exists_fn=lambda resource: True if hasattr(resource, "liter") else False,
    ),
    "cubic_meter": DomintellSensorEntityDescription(
        key="volume_cubic_meter",
        translation_key="volume",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.cubic_meter,
        exists_fn=lambda resource: True if hasattr(resource, "cubic_meter") else False,
    ),
}


WIND_SENSORS: tuple[DomintellSensorEntityDescription, ...] = (
    DomintellSensorEntityDescription(
        key="wind_speed",
        translation_key="wind_speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda resource: resource.state.speed,
        exists_fn=lambda resource: True if hasattr(resource.state, "speed") else False,
    ),
    DomintellSensorEntityDescription(
        key="wind_direction",
        translation_key="wind_direction",
        icon="mdi:windsock",  # TODO
        # native_unit_of_measurement=DEGREE,
        # https://www.meteo.be/fr/infos/faq/mesures-et-unites-de-mesure/quelles-sont-les-directions-de-vent
        device_class=SensorDeviceClass.ENUM,
        # state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.state.direction,
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "direction") else False
        ),
        options=[
            "unknown",
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ],
    ),
)


POWERSUPPLY_SENSORS: tuple[DomintellSensorEntityDescription, ...] = (
    DomintellSensorEntityDescription(
        key="power_supply_load",
        translation_key="power_supply_load",
        icon="mdi:speedometer",  # TODO
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.state.load,
        exists_fn=lambda resource: True if hasattr(resource.state, "load") else False,
    ),
    DomintellSensorEntityDescription(
        key="power_supply_voltage",
        translation_key="power_supply_voltage",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda resource: resource.state.voltage,
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "voltage") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="power_supply_temperature",
        translation_key="power_supply_temperature",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda resource: resource.state.temperature,
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "temperature") else False
        ),
    ),
)

ELECTRICITY_SENSORS: tuple[DomintellSensorEntityDescription, ...] = (
    DomintellSensorEntityDescription(
        key="frequency",
        translation_key="frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.frequency,
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "frequency") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="power_factor_l1",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: to_percentage(resource.state.power_factor_l1),
        exists_fn=lambda resource: hasattr(resource.state, "power_factor_l1")
        and getattr(resource, "nbr_of_phases", 0) == 1,
    ),
    DomintellSensorEntityDescription(
        key="power_factor_l1",
        translation_key="power_factor_phase",
        translation_placeholders={"phase": "1"},
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: to_percentage(resource.state.power_factor_l1),
        exists_fn=lambda resource: hasattr(resource.state, "power_factor_l1")
        and getattr(resource, "nbr_of_phases", 0) > 1,
    ),
    DomintellSensorEntityDescription(
        key="power_factor_l2",
        translation_key="power_factor_phase",
        translation_placeholders={"phase": "2"},
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: to_percentage(resource.state.power_factor_l2),
        exists_fn=lambda resource: hasattr(resource.state, "power_factor_l2")
        and getattr(resource, "nbr_of_phases", 0) > 1,
    ),
    DomintellSensorEntityDescription(
        key="power_factor_l3",
        translation_key="power_factor_phase",
        translation_placeholders={"phase": "3"},
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: to_percentage(resource.state.power_factor_l3),
        exists_fn=lambda resource: hasattr(resource.state, "power_factor_l3")
        and getattr(resource, "nbr_of_phases", 0) > 2,
    ),
    DomintellSensorEntityDescription(
        key="voltage_l1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.voltage_l1,
        exists_fn=lambda resource: hasattr(resource.state, "voltage_l1")
        and getattr(resource, "nbr_of_phases", 0) == 1,
    ),
    DomintellSensorEntityDescription(
        key="voltage_l1",
        translation_key="voltage_phase",
        translation_placeholders={"phase": "1"},
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.voltage_l1,
        exists_fn=lambda resource: hasattr(resource.state, "voltage_l1")
        and getattr(resource, "nbr_of_phases", 0) > 1,
    ),
    DomintellSensorEntityDescription(
        key="voltage_l2",
        translation_key="voltage_phase",
        translation_placeholders={"phase": "2"},
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.voltage_l2,
        exists_fn=lambda resource: hasattr(resource.state, "voltage_l2")
        and getattr(resource, "nbr_of_phases", 0) > 1,
    ),
    DomintellSensorEntityDescription(
        key="voltage_l3",
        translation_key="voltage_phase",
        translation_placeholders={"phase": "3"},
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.voltage_l3,
        exists_fn=lambda resource: hasattr(resource.state, "voltage_l3")
        and getattr(resource, "nbr_of_phases", 0) > 2,
    ),
    DomintellSensorEntityDescription(
        key="intensity_l1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.intensity_l1
        / 1000,  # data source is in mA
        exists_fn=lambda resource: hasattr(resource.state, "intensity_l1")
        and getattr(resource, "nbr_of_phases", 0) == 1,
    ),
    DomintellSensorEntityDescription(
        key="intensity_l1",
        translation_key="intensity_phase",
        translation_placeholders={"phase": "1"},
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.intensity_l1
        / 1000,  # data source is in mA
        exists_fn=lambda resource: hasattr(resource.state, "intensity_l1")
        and getattr(resource, "nbr_of_phases", 0) > 1,
    ),
    DomintellSensorEntityDescription(
        key="intensity_l2",
        translation_key="intensity_phase",
        translation_placeholders={"phase": "2"},
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.intensity_l2
        / 1000,  # data source is in mA
        exists_fn=lambda resource: hasattr(resource.state, "intensity_l2")
        and getattr(resource, "nbr_of_phases", 0) > 1,
    ),
    DomintellSensorEntityDescription(
        key="intensity_l3",
        translation_key="intensity_phase",
        translation_placeholders={"phase": "3"},
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.intensity_l3
        / 1000,  # data source is in mA
        exists_fn=lambda resource: hasattr(resource.state, "intensity_l3")
        and getattr(resource, "nbr_of_phases", 0) > 2,
    ),
    DomintellSensorEntityDescription(
        key="instant_power_l1",
        translation_key="instant_power_phase",
        translation_placeholders={"phase": "1"},
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda resource: resource.state.instant_power_l1,
        exists_fn=lambda resource: hasattr(resource.state, "instant_power_l1")
        and getattr(resource, "nbr_of_phases", 0) > 0,
    ),
    DomintellSensorEntityDescription(
        key="instant_power_l2",
        translation_key="instant_power_phase",
        translation_placeholders={"phase": "2"},
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda resource: resource.state.instant_power_l2,
        exists_fn=lambda resource: hasattr(resource.state, "instant_power_l2")
        and getattr(resource, "nbr_of_phases", 0) > 1,
    ),
    DomintellSensorEntityDescription(
        key="instant_power_l3",
        translation_key="instant_power_phase",
        translation_placeholders={"phase": "3"},
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda resource: resource.state.instant_power_l3,
        exists_fn=lambda resource: hasattr(resource.state, "instant_power_l3")
        and getattr(resource, "nbr_of_phases", 0) > 2,
    ),
    DomintellSensorEntityDescription(
        key="consumed_power",
        translation_key="consumed_power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.state.consumed_power
        / 1000,  # data source is in W
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "consumed_power") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="produced_power",
        translation_key="produced_power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda resource: resource.state.produced_power
        / 1000,  # data source is in W
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "produced_power") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="total_power",
        translation_key="total_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        # Difference between consumed power and produced power (value is given in W).
        value_fn=lambda resource: resource.state.total_power,  # data source is in W
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "total_power") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="total_energy_l1",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.total_energy_l1
        / 1000,  # data source is in Wh
        exists_fn=lambda resource: hasattr(resource.state, "total_energy_l1")
        and getattr(resource, "nbr_of_phases", 0) == 1,
    ),
    DomintellSensorEntityDescription(
        key="total_energy_l1",
        translation_key="total_energy_phase",
        translation_placeholders={"phase": "1"},
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.total_energy_l1
        / 1000,  # data source is in Wh
        exists_fn=lambda resource: hasattr(resource.state, "total_energy_l1")
        and getattr(resource, "nbr_of_phases", 0) > 1,
    ),
    DomintellSensorEntityDescription(
        key="total_energy_l2",
        translation_key="total_energy_phase",
        translation_placeholders={"phase": "2"},
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.total_energy_l2
        / 1000,  # data source is in Wh
        exists_fn=lambda resource: hasattr(resource.state, "total_energy_l2")
        and getattr(resource, "nbr_of_phases", 0) > 1,
    ),
    DomintellSensorEntityDescription(
        key="total_energy_l3",
        translation_key="total_energy_phase",
        translation_placeholders={"phase": "3"},
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.total_energy_l3
        / 1000,  # data source is in Wh
        exists_fn=lambda resource: hasattr(resource.state, "total_energy_l3")
        and getattr(resource, "nbr_of_phases", 0) > 2,
    ),
    DomintellSensorEntityDescription(
        key="forward_energy",
        translation_key="forward_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        # Total energy consumed from grid for all tariff’s (value is given in Wh).
        value_fn=lambda resource: resource.state.forward_energy
        / 1000,  # data source is in Wh
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "forward_energy") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="reverse_energy",
        translation_key="reverse_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        # Total energy returned to the grid for all tariff’s (value is given in Wh)
        value_fn=lambda resource: resource.state.reverse_energy
        / 1000,  # data source is in Wh
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "reverse_energy") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="total_energy",
        translation_key="total_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        # Difference between forward and reverse energy (value is given in Wh)
        value_fn=lambda resource: resource.state.total_energy
        / 1000,  # data source is in Wh
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "total_energy") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="total_energy_for_t1",
        translation_key="total_energy_for_tariff",
        translation_placeholders={"tariff": "1"},
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        # If value is negative this means that there is more produced energy than consumed energy for this tariff.
        value_fn=lambda resource: resource.state.total_energy_for_t1
        / 1000,  # data source is in Wh
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "total_energy_for_t1") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="total_energy_for_t2",
        translation_key="total_energy_for_tariff",
        translation_placeholders={"tariff": "2"},
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.total_energy_for_t2
        / 1000,  # data source is in Wh
        # If value is negative this means that there is more produced energy than consumed energy for this tariff.
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "total_energy_for_t2") else False
        ),
    ),
    DomintellSensorEntityDescription(
        key="total_energy_for_t3",
        translation_key="total_energy_for_tariff",
        translation_placeholders={"tariff": "3"},
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.total_energy_for_t3
        / 1000,  # data source is in Wh
        # If value is negative this means that there is more produced energy than consumed energy for this tariff.
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "total_energy_for_t3") else False
        ),
        # enabled_fn=lambda data: data.total_energy_for_t3 != 0,
    ),
    DomintellSensorEntityDescription(
        key="total_energy_for_t4",
        translation_key="total_energy_for_tariff",
        translation_placeholders={"tariff": "4"},
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        value_fn=lambda resource: resource.state.total_energy_for_t4
        / 1000,  # data source is in Wh
        # If value is negative this means that there is more produced energy than consumed energy for this tariff.
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "total_energy_for_t4") else False
        ),
        # enabled_fn=lambda data: data.total_energy_for_t4 != 0,
    ),
    DomintellSensorEntityDescription(
        key="tariff_indicator",
        translation_key="tariff_indicator",
        device_class=SensorDeviceClass.ENUM,
        options=[1, 2, 3, 4],
        value_fn=lambda resource: resource.state.tariff_indicator,
        exists_fn=lambda resource: (
            True if hasattr(resource.state, "tariff_indicator") else False
        ),
    ),
)

VARIABLE_SENSORS: tuple[DomintellSensorEntityDescription, ...] = (
    DomintellSensorEntityDescription(
        key="night_and_day",
        translation_key="night_and_day",
        icon="mdi:theme-light-dark",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=["night", "day"],
        value_fn=lambda resource: resource.night_and_day,
        exists_fn=lambda resource: (
            True if hasattr(resource, "night_and_day") else False
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor from Config Entry."""
    bridge: DomintellBridge = hass.data[DOMAIN][config_entry.entry_id]
    api: DomintellGateway = bridge.api
    controller = api.sensors
    variables_controller: VariablesController = api.variables

    @callback
    def register_items(controller: ControllerType):
        """Register items from controller."""

        @callback
        def async_add_entity(event_type: EventType, resource) -> None:
            """Add entity from Domintell resource."""
            # pylint: disable=unused-argument

            if included := SENSORS.get(resource.target_type):
                # Initialize default sensors
                sensor_entities: list = [
                    DomintellSensor(bridge, controller, resource, description)
                    for description in SENSORS.values()
                    if description.exists_fn(resource)
                ]

                async_add_entities(sensor_entities)
            else:
                # Initialize sensors that have multiple measurement data or system variable
                if resource.target_type == ResourceTypes.WIND.value:
                    wind_entities: list = [
                        DomintellSensor(bridge, controller, resource, description)
                        for description in WIND_SENSORS
                        if description.exists_fn(resource)
                    ]

                    async_add_entities(wind_entities)

                elif resource.target_type == ResourceTypes.POWER_SUPPLY.value:
                    powersupply_entities: list = [
                        DomintellSensor(bridge, controller, resource, description)
                        for description in POWERSUPPLY_SENSORS
                        if description.exists_fn(resource)
                    ]

                    async_add_entities(powersupply_entities)

                elif resource.target_type == ResourceTypes.ELECTRICITY.value:
                    elec_entities: list = [
                        DomintellSensor(bridge, controller, resource, description)
                        for description in ELECTRICITY_SENSORS
                        if description.exists_fn(resource)
                    ]

                    async_add_entities(elec_entities)

                elif resource.target_type == ResourceTypes.VARIABLE.value:
                    variable_entities: list = [
                        DomintellSensor(bridge, controller, resource, description)
                        for description in VARIABLE_SENSORS
                        if description.exists_fn(resource)
                    ]

                    async_add_entities(variable_entities)

                else:
                    # Do nothing
                    pass

        # Add all current items from controller
        for item in controller:
            async_add_entity(EventType.RESOURCE_ADDED, item)

        # Register listener for new items only
        config_entry.async_on_unload(
            controller.subscribe(
                async_add_entity, event_filter=EventType.RESOURCE_ADDED
            )
        )

    # setup for each sensor from domintell resource
    register_items(controller.temperature)
    register_items(controller.analog)
    register_items(controller.illuminance)
    register_items(controller.humidity)
    register_items(controller.pressure)
    register_items(controller.carbon_dioxide)
    register_items(controller.wind)
    register_items(controller.power_supply)
    register_items(controller.electricity)
    register_items(variables_controller)

    # Check for entities that no longer exist and remove them
    entity_reg = er.async_get(hass)
    reg_entities = er.async_entries_for_config_entry(entity_reg, config_entry.entry_id)

    for entity in reg_entities:
        if entity.domain != SENSOR_DOMAIN:
            continue

        part = entity.unique_id.split("_")
        if len(part) >= 3:
            endpoint_id = part[2]

            if (
                endpoint_id not in controller.temperature.keys()
                and endpoint_id not in controller.analog.keys()
                and endpoint_id not in controller.illuminance.keys()
                and endpoint_id not in controller.humidity.keys()
                and endpoint_id not in controller.pressure.keys()
                and endpoint_id not in controller.carbon_dioxide.keys()
                and endpoint_id not in controller.wind.keys()
                and endpoint_id not in controller.power_supply.keys()
                and endpoint_id not in controller.electricity.keys()
                and endpoint_id not in variables_controller.keys()
            ):
                entity_reg.async_remove(entity.entity_id)


class DomintellSensor(SensorEntity):
    """Representation of a Domintell sensor."""

    entity_description: DomintellSensorEntityDescription

    def __init__(
        self,
        bridge: DomintellBridge,
        controller: ControllerType,
        resource,
        description: DomintellSensorEntityDescription,
    ):
        """Initialize Domintell Sensor."""
        self._bridge = bridge
        self._api = bridge.api
        self._controller = controller
        self._resource = resource
        self._logger = bridge.logger

        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_assumed_state = False
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
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self.entity_description.value_fn(self._resource)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        return {"io_name": self._resource.io_name}

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
