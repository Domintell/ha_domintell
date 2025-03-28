from dataclasses import dataclass
from typing import Any
import inspect
import types
from enum import Enum, StrEnum
from .const import IO_TYPES_INT, IO_TYPES_STRING
from .lightprotocol import LpCommand, construct_endpoint_id


class PushState(Enum):
    UNKNOWN = -1
    RELEASED = 0
    START_SHORT_PUSH = 1
    END_SHORT_PUSH = 2
    START_LONG_PUSH = 3
    END_LONG_PUSH = 4
    PRESSED = 5


class MotionState(Enum):
    UNKNOWN = 0
    START_DETECTION = 1
    END_DETECTION = 2


class CoverState(Enum):
    UNKNOWN = 0
    STOPPED_UNKNOWN = 1
    MOVING_UP = 2
    MOVING_DOWN = 3
    STOPPED_UP = 4
    STOPPED_DOWN = 5


class GestureState(Enum):
    UNKNOWN = 0
    GESTURE_RIGHT = 2
    GESTURE_LEFT = 3
    GESTURE_UP = 4
    GESTURE_DOWN = 5
    GESTURE_PUSH = 6


class TemperatureMode(Enum):
    ABSENCE = 1
    AUTO = 2
    COMFORT = 5
    FROST = 6


temp_mode_bit_mapping = {
    TemperatureMode.AUTO: 0,
    TemperatureMode.COMFORT: 1,
    TemperatureMode.ABSENCE: 2,
    TemperatureMode.FROST: 3,
}


class RegulationMode(Enum):
    OFF = 0
    HEATING = 1
    COOLING = 2
    MIXED = 3
    AUTO = 5
    DRY = 6
    FAN = 7


regul_mode_bit_mapping = {
    RegulationMode.OFF: 0,
    RegulationMode.HEATING: 1,
    RegulationMode.COOLING: 2,
    RegulationMode.MIXED: 3,
    RegulationMode.AUTO: 4,
    RegulationMode.DRY: 5,
    RegulationMode.FAN: 6,
}


class FanMode(Enum):
    MANUAL = 0  # From 0 or 1 to number_of_speeds
    AUTO = 254
    UNKNOWN = 255


class VanesMode(Enum):
    MANUAL = 0  # From 0 to number_of_positions
    AUTO = 252
    FROZEN = 253
    SWING = 254
    UNKNOWN = 255


class AnalogConfig:
    def __init__(self, min: float = 0.0, max: float = 100.0, unit: str = "V"):
        self.min = min
        self.max = max
        self.unit = unit

    def __str__(self):
        return f"AnalogConfig(min={self.min}, max={self.max}, unit={self.unit})"


class FanConfig:
    def __init__(
        self,
        number_of_speeds: int = 3,
        has_off_speed: bool = True,
        has_auto_speed: bool = False,
    ):
        self.number_of_speeds = number_of_speeds
        self.has_off_speed = has_off_speed
        self.has_auto_speed = has_auto_speed

    def __str__(self):
        return f"FanConfig(number_of_speeds={self.number_of_speeds}, has_off_speed={self.has_off_speed}, has_auto_speed={self.has_auto_speed})"


class VanesConfig:
    def __init__(
        self,
        number_of_position: int = 0,
        has_auto_speed: bool = False,
        has_frozen_mode: bool = False,
        has_swing_mode: bool = False,
    ):
        self.number_of_position = number_of_position
        self.has_auto_speed = has_auto_speed
        self.has_frozen_mode = has_frozen_mode
        self.has_swing_mode = has_swing_mode

    def __str__(self):
        return f"VanesConfig(number_of_position={self.number_of_position}, has_auto_speed={self.has_auto_speed}, has_frozen_mode={self.has_frozen_mode}, has_swing_mode={self.has_swing_mode})"


class ThermostatConfig:
    def __init__(
        self,
        regul_mask: int = 0x70,
        temp_mask: int = 0x00,
        heat_limit_high: float = 30.0,
        heat_limit_low: float = 10.0,
        cool_limit_high: float = 40.0,
        cool_limit_low: float = 20.0,
        setpoint_step: float = 0.5,
    ):
        self.regul_mask: int = regul_mask
        self.temp_mask: int = temp_mask
        self.heat_limit_high: float = heat_limit_high
        self.heat_limit_low: float = heat_limit_low
        self.cool_limit_high: float = cool_limit_high
        self.cool_limit_low: float = cool_limit_low
        self.setpoint_step: float = setpoint_step
        self._temperature_mode_list: list = []
        self._regulation_mode_list: list = []

        for mode in TemperatureMode:
            bit_position = temp_mode_bit_mapping[mode]
            if (self.temp_mask & (1 << bit_position)) == 0:
                self._temperature_mode_list.append(mode)

        for mode in RegulationMode:
            bit_position = regul_mode_bit_mapping[mode]
            if (self.regul_mask & (1 << bit_position)) == 0:
                self._regulation_mode_list.append(mode)

    @property
    def temperature_modes(self) -> list:
        """Return the list of unhidden teperature modes"""
        return self._temperature_mode_list

    @property
    def regulation_modes(self) -> list:
        """Return the list of unhidden regulation modes"""
        return self._regulation_mode_list

    def __str__(self):
        return f"ThermostatConfig(HMR={self.regul_mask}, HMT={self.temp_mask}, LHH={self.heat_limit_high}, LHL={self.heat_limit_low}, LCH={self.cool_limit_high}, LCL={self.cool_limit_low}, ISP={self.setpoint_step})"


class ThermostatState:
    def __init__(
        self,
        current_temperature: float = 0.0,
        heating_setpoint: float = 0.0,
        temperature_mode: TemperatureMode = TemperatureMode.FROST,
        heating_profile_setpoint: float = 0.0,
        cooling_setpoint: float = 0.0,
        regulation_mode: RegulationMode = RegulationMode.OFF,
        cooling_profile_setpoint: float = 0.0,
    ):
        self.current_temperature: float = current_temperature
        self.active_heating_setpoint: float = heating_setpoint
        self.temperature_mode: TemperatureMode = temperature_mode
        self.heating_profile_setpoint: float = heating_profile_setpoint
        self.active_cooling_setpoint: float = cooling_setpoint
        self.regulation_mode: RegulationMode = regulation_mode
        self.cooling_profile_setpoint: float = cooling_profile_setpoint

    @classmethod
    def from_list(cls, data: list):
        """Initialize an instance from a list..

        Args:
            data: A list containing the values of the attributes in the same order as the constructor parameters.

        Returns:
            An instance of the class ThermostatState.
        """

        if len(data) != 7:
            raise ValueError("The data list must contain 7 elements")

        return cls(*data)

    def __eq__(self, other):
        if isinstance(other, ThermostatState):
            return (
                self.current_temperature == other.current_temperature
                and self.temperature_mode == other.temperature_mode
                and self.regulation_mode == other.regulation_mode
                and self.active_heating_setpoint == other.active_heating_setpoint
                and self.active_cooling_setpoint == other.active_cooling_setpoint
                and self.heating_profile_setpoint == other.heating_profile_setpoint
                and self.cooling_profile_setpoint == other.cooling_profile_setpoint
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"ThermostatState(temperarture={self.current_temperature}, active_heating_setpoint={self.active_heating_setpoint}, temperature_mode={self.temperature_mode}, heating_profile_setpoint={self.heating_profile_setpoint}, active_cooling_setpoint={self.active_cooling_setpoint}, regulation_mode={self.regulation_mode}, cooling_profile_setpoint={self.cooling_profile_setpoint})"


class DfanComboState:
    def __init__(self, speed: int = 0, heating: str = "OFF", mode: str = "AUTO"):
        self.speed = speed
        self.heating = heating  # "HEATING", "COOLING" or "OFF"
        self.mode = mode  # "AUTO", "MANUAL"

    @property
    def number_of_speeds(self) -> int:
        return 3

    def __eq__(self, other):
        if isinstance(other, DfanComboState):
            return (
                self.speed == other.speed
                and self.heating == other.heating
                and self.mode == other.mode
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"DfanComboState(speed={self.speed}, heating={self.heating}, mode={self.mode})"


class LightColorMode(StrEnum):
    """Possible light color modes."""

    UNKNOWN = "unknown"
    ONOFF = "onoff"
    BRIGHTNESS = "brightness"
    COLOR_TEMP = "color_temp"
    RGB = "rgb"
    RGBW = "rgbw"
    WHITE = "white"


class LightType(StrEnum):
    """Possible light types."""

    TL = "TL"  # Device Type 0 for fluorescent lamps (IEC 62386-201)
    ER = "ER"  # Device Type 1 for self-contained emergency lighting (IEC62386-202)
    DISC = "DISC"  # Device Type 2 for discharge lamps (IEC 62386-203)
    LOWV = "LOWV"  # Device Type 3 for low voltage halogen lamps (IEC 62386-204)
    INCA = "INCA"  # Device Type 4 for supply Voltage controller for incandescent lamps (IEC 62386-205)
    DC = "DC"  # Device Type 5 for conversion from digital into D.C. voltage (IEC62386-206)
    LED = "LED"  # Device Type 6 for LED modules (IEC 62386-207)
    SW = "SW"  # Device Type 7 for switching function (IEC 62386-208)
    RGB = "RGB"  # Device Type 8 for colour control (IEC 62386-209)


class DmxType(Enum):
    """Possible DMX types."""

    UNKNOWN = (
        0  # misconfigured DMX slave/output. Please check configuration in GoldenGate !
    )
    RGB = 1
    RGBI = 2
    RGBW = 3
    SINGLE = 4  # single channel (of any color)
    MULTIPLE = 5  # multiple channels (of any color)
    RGBWI = 6


class ColorRGB:
    def __init__(self, *args, **kwargs):
        self.r: int = 0
        self.g: int = 0
        self.b: int = 0

        if args:
            if len(args) == 1 and isinstance(args[0], list):
                if len(args[0]) != 3:
                    raise ValueError("The list must contain exactly 3 values")
                self.r, self.g, self.b = args[0]
            else:
                self.r, self.g, self.b = args
        elif kwargs:
            self.r: int = kwargs.get("r", 0)
            self.g: int = kwargs.get("g", 0)
            self.b: int = kwargs.get("b", 0)
        else:
            raise TypeError(
                "The constructor expects either a list or a dictionary of 3 values"
            )

    def get_max_value(self):
        """Returns the maximum value among r, g and b."""
        return max(self.r, self.g, self.b)

    def is_on(self):
        return True if (self.r > 0) or (self.g > 0) or (self.b > 0) else False

    def as_list(self):
        return [self.r, self.g, self.b]

    def as_tuple(self):
        return tuple(self.as_list())

    def as_set(self):
        return set(self.as_list())

    def as_dict(self):
        return {"r": self.r, "g": self.g, "b": self.b}

    def __eq__(self, other):
        if isinstance(other, ColorRGB):
            return self.r == other.r and self.g == other.g and self.b == other.b
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"ColorRGB(R={self.r}, G={self.g}, B={self.b})"


class ColorRGBI:
    def __init__(self, *args, **kwargs):
        self.r: int = 0
        self.g: int = 0
        self.b: int = 0
        self.i: int = 0

        if args:
            if len(args) == 1 and isinstance(args[0], list):
                if len(args[0]) != 4:
                    raise ValueError("The list must contain exactly 4 values")
                self.r, self.g, self.b, self.i = args[0]
            else:
                self.r, self.g, self.b, self.i = args
        elif kwargs:
            self.r: int = kwargs.get("r", 0)
            self.g: int = kwargs.get("g", 0)
            self.b: int = kwargs.get("b", 0)
            self.i: int = kwargs.get("i", 0)
        else:
            raise TypeError(
                "The constructor expects either a list or a dictionary of 4 values"
            )

    def get_max_value(self):
        """Returns the maximum value among r, g and b."""
        return max(self.r, self.g, self.b)

    def is_on(self):
        return (
            True
            if (self.r > 0) or (self.g > 0) or (self.b > 0) or (self.i > 0)
            else False
        )

    def as_list(self):
        return [self.r, self.g, self.b, self.i]

    def as_tuple(self):
        return tuple(self.as_list())

    def as_set(self):
        return set(self.as_list())

    def as_dict(self):
        return {"r": self.r, "g": self.g, "b": self.b, "i": self.i}

    def __eq__(self, other):
        if isinstance(other, ColorRGBI):
            return (
                self.r == other.r
                and self.g == other.g
                and self.b == other.b
                and self.i == other.i
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"ColorRGB(R={self.r}, G={self.g}, B={self.b}, I={self.i})"


class ColorRGBW:
    def __init__(self, *args, **kwargs):
        self.r: int = 0
        self.g: int = 0
        self.b: int = 0
        self.w: int = 0

        if args:
            if len(args) == 1 and isinstance(args[0], list):
                if len(args[0]) != 4:
                    raise ValueError("The list must contain exactly 4 values")
                self.r, self.g, self.b, self.w = args[0]
            else:
                self.r, self.g, self.b, self.w = args
        elif kwargs:
            self.r: int = kwargs.get("r", 0)
            self.g: int = kwargs.get("g", 0)
            self.b: int = kwargs.get("b", 0)
            self.w: int = kwargs.get("w", 0)
        else:
            raise TypeError(
                "The constructor expects either a list or a dictionary of 4 values"
            )

    def get_max_value(self):
        """Returns the maximum value among r, g, and b."""
        return max(self.r, self.g, self.b)

    def is_on(self):
        return (
            True
            if (self.r > 0) or (self.g > 0) or (self.b > 0) or (self.w > 0)
            else False
        )

    def as_list(self):
        return [self.r, self.g, self.b, self.w]

    def as_tuple(self):
        return tuple(self.as_list())

    def as_set(self):
        return set(self.as_list())

    def as_dict(self):
        return {"r": self.r, "g": self.g, "b": self.b, "w": self.w}

    def __eq__(self, other):
        if isinstance(other, ColorRGBW):
            return (
                self.r == other.r
                and self.g == other.g
                and self.b == other.b
                and self.w == other.w
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"ColorRGBW(R={self.r}, G={self.g}, B={self.b}, W={self.w})"


class ColorRGBWI:
    def __init__(self, *args, **kwargs):
        self.r: int = 0
        self.g: int = 0
        self.b: int = 0
        self.w: int = 0
        self.i: int = 0

        if args:
            if len(args) == 1 and isinstance(args[0], list):
                if len(args[0]) != 4:
                    raise ValueError("The list must contain exactly 5 values")
                self.r, self.g, self.b, self.w, self.i = args[0]
            else:
                self.r, self.g, self.b, self.w = args
        elif kwargs:
            self.r: int = kwargs.get("r", 0)
            self.g: int = kwargs.get("g", 0)
            self.b: int = kwargs.get("b", 0)
            self.w: int = kwargs.get("w", 0)
            self.w: int = kwargs.get("i", 0)
        else:
            raise TypeError(
                "The constructor expects either a list or a dictionary of 5 values"
            )

    def get_max_value(self):
        """Returns the maximum value among r, g and b."""
        return max(self.r, self.g, self.b)

    def is_on(self):
        return (
            True
            if (self.r > 0)
            or (self.g > 0)
            or (self.b > 0)
            or (self.w > 0)
            or (self.i > 0)
            else False
        )

    def as_list(self):
        return [self.r, self.g, self.b, self.w, self.i]

    def as_tuple(self):
        return tuple(self.as_list())

    def as_set(self):
        return set(self.as_list())

    def as_dict(self):
        return {"r": self.r, "g": self.g, "b": self.b, "w": self.w, "i": self.i}

    def __eq__(self, other):
        if isinstance(other, ColorRGBWI):
            return (
                self.r == other.r
                and self.g == other.g
                and self.b == other.b
                and self.w == other.w
                and self.i == other.i
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"ColorRGBW(R={self.r}, G={self.g}, B={self.b}, W={self.w}, I={self.i})"


class WindDirection(StrEnum):
    """Possible wind directions."""

    UNKNOWN = "unknown"
    N = "N"
    NNE = "NNE"
    NE = "NE"
    ENE = "ENE"
    E = "E"
    ESE = "ESE"
    SE = "SE"
    SSE = "SSE"
    S = "S"
    SSW = "SSW"
    SW = "SW"
    WSW = "WSW"
    W = "W"
    WNW = "WNW"
    NW = "NW"
    NNW = "NNW"


class WindState:
    def __init__(
        self, speed: float = 0.0, direction: WindDirection = WindDirection.UNKNOWN
    ):
        self.speed = speed
        self.direction = direction

    def __eq__(self, other):
        if isinstance(other, WindState):
            return self.speed == other.speed and self.direction == other.direction
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return (
            f"WindState(speed={self.speed:.1f} km/h, direction={self.direction.name})"
        )


class PowerSupplyState:
    def __init__(self, load: int = 0, voltage: float = 0.0, temperature: float = 0.0):
        self.load = load
        self.voltage = voltage
        self.temperature = temperature

    def __eq__(self, other):
        if isinstance(other, PowerSupplyState):
            return (
                self.load == other.load
                and self.voltage == other.voltage
                and self.temperature == other.temperature
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"PowerSupplyState(load={self.load} %, voltage={self.voltage:.2f} V, temperature={self.temperature:.2f} °C)"


class ElectricityState:
    def __init__(
        self,
        flag: int = 0,
        frequency: float = 0.0,
        power_factor_l1: float = 0.0,
        power_factor_l2: float = 0.0,
        power_factor_l3: float = 0.0,
        voltage_l1: int = 0,
        voltage_l2: int = 0,
        voltage_l3: int = 0,
        intensity_l1: int = 0,
        intensity_l2: int = 0,
        intensity_l3: int = 0,
        instant_power_l1: int = 0,
        instant_power_l2: int = 0,
        instant_power_l3: int = 0,
        consumed_power: int = 0,
        produced_power: int = 0,
        total_power: int = 0,
        total_energy_l1: int = 0,
        total_energy_l2: int = 0,
        total_energy_l3: int = 0,
        forward_energy: int = 0,
        reverse_energy: int = 0,
        total_energy: int = 0,
        total_energy_for_t1: int = 0,
        total_energy_for_t2: int = 0,
        total_energy_for_t3: int = 0,
        total_energy_for_t4: int = 0,
        tariff_indicator: int = 1,
    ):
        self.flag = flag
        self.frequency = frequency
        self.power_factor_l1 = power_factor_l1
        self.power_factor_l2 = power_factor_l2
        self.power_factor_l3 = power_factor_l3
        self.voltage_l1 = voltage_l1
        self.voltage_l2 = voltage_l2
        self.voltage_l3 = voltage_l3
        self.intensity_l1 = intensity_l1
        self.intensity_l2 = intensity_l2
        self.intensity_l3 = intensity_l3
        self.instant_power_l1 = instant_power_l1
        self.instant_power_l2 = instant_power_l2
        self.instant_power_l3 = instant_power_l3
        self.consumed_power = consumed_power
        self.produced_power = produced_power
        self.total_power = total_power
        self.total_energy_l1 = total_energy_l1
        self.total_energy_l2 = total_energy_l2
        self.total_energy_l3 = total_energy_l3
        self.forward_energy = forward_energy
        self.reverse_energy = reverse_energy
        self.total_energy = total_energy
        self.total_energy_for_t1 = total_energy_for_t1
        self.total_energy_for_t2 = total_energy_for_t2
        self.total_energy_for_t3 = total_energy_for_t3
        self.total_energy_for_t4 = total_energy_for_t4
        self.tariff_indicator = tariff_indicator

    def __eq__(self, other):
        if isinstance(other, ElectricityState):
            return (
                self.flag == other.flag
                and self.frequency == other.frequency
                and self.power_factor_l1 == other.power_factor_l1
                and self.power_factor_l2 == other.power_factor_l2
                and self.power_factor_l3 == other.power_factor_l3
                and self.voltage_l1 == other.voltage_l1
                and self.voltage_l2 == other.voltage_l2
                and self.voltage_l3 == other.voltage_l3
                and self.intensity_l1 == other.intensity_l1
                and self.intensity_l2 == other.intensity_l2
                and self.intensity_l3 == other.intensity_l3
                and self.instant_power_l1 == other.instant_power_l1
                and self.instant_power_l2 == other.instant_power_l2
                and self.instant_power_l3 == other.instant_power_l3
                and self.consumed_power == other.consumed_power
                and self.produced_power == other.produced_power
                and self.total_power == other.total_power
                and self.total_energy_l1 == other.total_energy_l1
                and self.total_energy_l2 == other.total_energy_l2
                and self.total_energy_l3 == other.total_energy_l3
                and self.forward_energy == other.forward_energy
                and self.reverse_energy == other.reverse_energy
                and self.total_energy == other.total_energy
                and self.total_energy_for_t1 == other.total_energy_for_t1
                and self.total_energy_for_t2 == other.total_energy_for_t2
                and self.total_energy_for_t3 == other.total_energy_for_t3
                and self.total_energy_for_t4 == other.total_energy_for_t4
                and self.tariff_indicator == other.tariff_indicator
            )
        return False

    @classmethod
    def from_dict(cls, data: dict):
        """Initialize an instance from a dict..

        Args:
            data: A dictionnry containing the values of the attributes.
            The value for missing attributes will be default

        Returns:
            An instance of the class ElectricityState.
        """
        return cls(**data)

    @classmethod
    def from_list(cls, data: list):
        """Initialize an instance from a list..

        Args:
            data: A list containing the values of the attributes in the same order as the constructor parameters.

        Returns:
            An instance of the class ElectricityState.
        """

        if len(data) != 28:
            raise ValueError("The data list must contain 28 elements")

        return cls(*data)

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return (
            f"ElectricityState("
            f"flag={self.flag}, "
            f"frequency={self.frequency:.1f}, "
            f"power_factor_l1={self.power_factor_l1:.2f}, "
            f"power_factor_l2={self.power_factor_l2:.2f}, "
            f"power_factor_l3={self.power_factor_l3:.2f}, "
            f"voltage_l1={self.voltage_l1}, "
            f"voltage_l2={self.voltage_l2}, "
            f"voltage_l3={self.voltage_l3}, "
            f"intensity_l1={self.intensity_l1}, "
            f"intensity_l2={self.intensity_l2}, "
            f"intensity_l3={self.intensity_l3}, "
            f"instant_power_l1={self.instant_power_l1}, "
            f"instant_power_l2={self.instant_power_l2}, "
            f"instant_power_l3={self.instant_power_l3}, "
            f"consumed_power={self.consumed_power}, "
            f"produced_power={self.produced_power}, "
            f"total_power={self.total_power}, "
            f"total_energy_l1={self.total_energy_l1}, "
            f"total_energy_l2={self.total_energy_l2}, "
            f"total_energy_l3={self.total_energy_l3}, "
            f"forward_energy={self.forward_energy}, "
            f"reverse_energy={self.reverse_energy}, "
            f"total_energy={self.total_energy}, "
            f"total_energy_for_t1={self.total_energy_for_t1}, "
            f"total_energy_for_t2={self.total_energy_for_t2}, "
            f"total_energy_for_t3={self.total_energy_for_t3}, "
            f"total_energy_for_t4={self.total_energy_for_t4}, "
            f"tariff_indicator={self.tariff_indicator}"
            f")"
        )


class CloudInfoErrorCode(Enum):
    NO_ERROR = 0
    AUTHENTICATION_ERROR = 1
    DATA_ERROR = 2
    NETWORK_ERROR = 3
    WEBSOCKET_ERROR = 4
    PROTOCOL_ERROR = 5
    VERSION_ERROR = 6
    TOKEN_ERROR = 7
    URL_ERROR = 8
    FILE_ERROR = 9
    NOTIFICTION_TYPE_ERROR = 10
    UNKNOWN_SERVICE_ERROR = 11


class CloudInfoState:
    def __init__(
        self,
        allowed: int = 0,
        registered: bool = False,
        connected: bool = False,
        error_code: int = 0,
        error_description: str = "",
    ):
        self.allowed = allowed
        self.registered = bool(registered)
        self.connected = bool(connected)
        self.error_code = CloudInfoErrorCode(error_code)
        self.error_description = error_description

    def __eq__(self, other):
        if isinstance(other, CloudInfoState):
            return (
                self.allowed == other.allowed
                and self.registered == other.registered
                and self.connected == other.connected
                and self.error_code == other.error_code
                and self.error_description == other.error_description
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"CloudInfoState(allowed={self.allowed}, registered={self.registered}, connected={self.connected}, error_code={self.error_code}, error_description={self.error_description})"


class MemoryInfoState:
    def __init__(
        self,
        total_ram: int = 0,
        free_ram: int = 0,
        uptime: int = 0,
        os_ram_size: int = 0,
        os_data_ram_size: int = 0,
    ):
        self.total_ram = total_ram
        self.free_ram = free_ram
        self.uptime = uptime
        self.os_ram_size = os_ram_size
        self.os_data_ram_size = os_data_ram_size

    def __eq__(self, other):
        if isinstance(other, MemoryInfoState):
            return (
                self.total_ram == other.total_ram
                and self.free_ram == other.free_ram
                and self.uptime == other.uptime
                and self.os_ram_size == other.os_ram_size
                and self.os_data_ram_size == other.os_data_ram_size
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"MemoryInfoState(Total RAM={self.total_ram} bytes, Free RAM={self.free_ram} bytes, Uptime={self.uptime} minutes, OS RAM size={self.os_ram_size} bytes, OS Data RAM size={self.os_data_ram_size} bytes)"


class CpuInfoState:
    def __init__(
        self,
        nbr_of_cpu: int = 0,
        avg_load_1min: int = 0,
        avg_load_5min: int = 0,
        avg_load_15min: int = 0,
    ):
        self.nbr_of_cpu = nbr_of_cpu
        self.avg_load_1min = avg_load_1min
        self.avg_load_5min = avg_load_5min
        self.avg_load_15min = avg_load_15min

    def __eq__(self, other):
        if isinstance(other, CpuInfoState):
            return (
                self.nbr_of_cpu == other.nbr_of_cpu
                and self.avg_load_1min == other.avg_load_1min
                and self.avg_load_5min == other.avg_load_5min
                and self.avg_load_15min == other.avg_load_15min
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"CpuInfoState(nbr_of_cpu={self.nbr_of_cpu}, avg_load_1min={self.avg_load_1min}, avg_load_5min={self.avg_load_5min}, avg_load_15min={self.avg_load_15min})"


class DiBusGwState(Enum):
    UNKNOWN = 0
    MISSING = 1
    PRESENT = 2
    UPDATING = 3
    LOADER = 4
    ERROR = 5


class DiBusGwInfoState:
    def __init__(
        self,
        version: int = 0,
        online: bool = False,
        state: DiBusGwState = DiBusGwState.UNKNOWN,
        description: str = "unknown",
    ):
        self.version = version
        self.online = online
        self.state = state
        self.description = description

    def __eq__(self, other):
        if isinstance(other, DiBusGwInfoState):
            return (
                self.version == other.version
                and self.online == other.online
                and self.state == other.state
                and self.description == other.description
            )
        return False

    def __repr__(self):
        return f"{str(self)}"

    def __str__(self):
        return f"DiBusGwInfoState(version={self.version}, online={self.online}, state={self.state}, description={self.description})"


@dataclass
class BaseIO:
    """Domintell base io representation."""

    id: str = ""
    target_type: str | None = None
    module_type: str | None = None
    io_type: int | None = None
    io_offset: int | None = None
    io_name: str = ""
    floor_name: str = ""
    room_name: str = ""

    serial_number: str | None = None
    installation_name: str | None = None
    sw_version: str | None = None
    extra_info: list[str] | None = None

    # async def _send_command(self, cmd: str) -> None:
    #     command_message = LpCommand(self.id, cmd)
    #     await self._gateway._client.send_command(command_message)

    def __str__(self):
        return 'IO (Id: "{}", Target Type: "{}", Module Type: "{}", Io Type: {} ({}), Io Offset: {}, Io Name: "{}", Floor: "{}", Room: "{}")'.format(
            self.id,
            self.target_type,
            self.module_type,
            self.io_type,
            IO_TYPES_STRING.get(self.io_type, "TypeIoNotHandled"),
            self.io_offset,
            self.io_name,
            self.floor_name,
            self.room_name,
        )


class SceneIO(BaseIO):
    """Domintell SceneIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeIoNotHandled", 0)

        # Set io_name to default if empty (ie: "Scene #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Scene #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: None = None

    @property
    def state(self) -> None:
        return self._state

    async def activate(self) -> None:
        await self._send_command("On")

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class TorIO(BaseIO):
    """Domintell TorIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeTorIo", 1)

        # Set io_name to default if empty (ie: "TorIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "TorIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: bool = False
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
        }

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, state: bool) -> None:
        self._state = state

    def is_on(self) -> bool:
        return self.state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class TorBasicTempoIO(BaseIO):
    """Domintell TorBasicTempoIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeTorBasicTempoIO", 52)

        # Set io_name to default if empty (ie: "TorBasicTempoIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "TorBasicTempoIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: bool = False  # most probably always False

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, state: bool) -> None:
        self._state = state

    def is_on(self) -> bool:
        return self.state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class InputTriggerIO(BaseIO):
    """Domintell InputTriggerIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeInputTriggerIO", 53)

        # Set io_name to default if empty (ie: "InputTriggerIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "InputTriggerIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: PushState = PushState.UNKNOWN

    @property
    def state(self) -> PushState:
        return self._state

    @state.setter
    def state(self, state: PushState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def execute_link(self, push_state: PushState) -> None:
        print(f"Execute link for {push_state} of InputTriggerIO id: {self.id}")
        cmd = "Start of short push"
        match push_state:
            case PushState.START_SHORT_PUSH:
                cmd = "Start of short push"
            case PushState.END_SHORT_PUSH:
                cmd = "End of short push"
            case _:
                print("Unkown push state:", push_state)
                return

        await self._send_command(cmd)

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class InputIO(BaseIO):
    """domintell InputIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeInputIo", 2)

        # Set io_name to default if empty (ie: "InputIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "InputIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: PushState = PushState.UNKNOWN

    @property
    def state(self) -> PushState:
        return self._state

    @state.setter
    def state(self, state: PushState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def execute_link(self, push_state: PushState) -> None:
        print(f"Execute link for {push_state} of InputIO id: {self.id}")
        cmd = "Start of short push"
        match push_state:
            case PushState.START_SHORT_PUSH:
                cmd = "Start of short push"
            case PushState.END_SHORT_PUSH:
                cmd = "End of short push"
            case PushState.START_LONG_PUSH:
                cmd = "Start of long push"
            case PushState.END_LONG_PUSH:
                cmd = "End of long push"
            case _:
                print("Unkown push state:", push_state)
                return

        await self._send_command(cmd)

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class TrvIO(BaseIO):
    """domintell TrvIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeTrvIo", 6)

        # Set io_name to default if empty (ie: "TrvIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "TrvIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: CoverState = CoverState.UNKNOWN

    @property
    def state(self) -> CoverState:
        return self._state

    @state.setter
    def state(self, state: CoverState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def move_up(self) -> None:
        await self._send_command("Move Up")

    async def move_down(self) -> None:
        await self._send_command("Move Down")

    async def stop(self) -> None:
        await self._send_command("Off")

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class TrvBtIO(BaseIO):
    """domintell TrvBtIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeTrvBtIo", 7)

        # Set io_name to default if empty (ie: "TrvBtIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "TrvBtIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: CoverState = CoverState.UNKNOWN

    @property
    def state(self) -> CoverState:
        return self._state

    @state.setter
    def state(self, state: CoverState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def move_up(self) -> None:
        await self._send_command("Move Up")

    async def move_down(self) -> None:
        await self._send_command("Move Down")

    async def stop(self) -> None:
        await self._send_command("Off")

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class LedIO(BaseIO):
    """Domintell LedIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeLedIo", 10)

        # Set io_name to default if empty (ie: "LedIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "LedIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: bool = False
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
        }

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, state: bool) -> None:
        self._state = state

    def is_on(self) -> bool:
        return self.state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class Led8cIO(BaseIO):
    """Domintell Led8cIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeLed8cIo", 15)

        # Set io_name to default if empty (ie: "Led8cIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Led8cIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: bool = False
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
        }

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, state: bool) -> None:
        self._state = state

    def is_on(self) -> bool:
        return self.state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class LedRgbIo(BaseIO):
    """Domintell LedRgbIo reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeLedRgbIo", 60)

        # Set io_name to default if empty (ie: "LedRgbIo #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "LedRgbIo #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: bool = False
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
        }

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, state: bool) -> None:
        self._state = state

    def is_on(self) -> bool:
        return self.state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class PblcdIO(BaseIO):
    """Domintell PblcdIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypePblcdIo", 20)

        # Set io_name to default if empty (ie: "PblcdIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "PblcdIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: bool = False
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
        }

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, state: bool) -> None:
        self._state = state

    def is_on(self) -> bool:
        return self.state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def _send_command(self, cmd: str) -> None:
        command_message = LpCommand(self.id, cmd)
        await self._gateway._client.send_command(command_message)


class Out10VIO(BaseIO):
    """domintell Out10VIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeOut10VIo", 23)

        # Set io_name to default if empty (ie: "Out10VIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Out10VIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._brightness_scale: tuple = (1, 100)
        self._state: int = 0
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
            LightColorMode.BRIGHTNESS,
        }

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        # Make sure we have state from 0 to 100%
        self._state = 0 if self.state < 0 else 100 if self.state > 100 else state

    @property
    def brightness_scale(self) -> tuple:
        return self._brightness_scale

    @property
    def brightness(self) -> int:
        return self._state

    def is_on(self) -> bool:
        return True if self.state > 0 else False

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def set_value(self, value: int) -> None:
        await self._send_command("Set Value", value)

    async def increase_value(self) -> None:
        await self._send_command("Increase")

    async def decrease_value(self) -> None:
        await self._send_command("Decrease")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class AccessControlIO(BaseIO):
    """domintell AccessControlIO reprensentation."""

    # Note: This IO type is not handled

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeAccessControlIo", 40)

        # Set io_name to default if empty (ie: "Access #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Access #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 0

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        self._state = state


class VideoIO(BaseIO):
    """domintell VideoIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeVideoIo", 31)

        # Set io_name to default if empty (ie: "VideoIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Video #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 0

        # Possible status:
        # ▪ 0x01 = Video output is online and is ready to display video
        #          stream
        # ▪ 0x02 = Incomming call running (bell)
        # ▪ 0x04 = Call has been caught. Bi-directional connection
        #          established with doorstation.
        # ▪ 0x08 = For half-duplex audio comminucation only : sound
        #          from microphone of the screen is sent to doorstation.
        # ▪ 0x10 = A video stream is currently playing on video output
        # ▪ 0x20 = The currpenly played video stream has been started
        #          by user directly from screen (not started due to a call)

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class CamIO(BaseIO):
    """Domintell CamIO reprensentation."""

    # Note: This IO type is not handled

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeCamIo", 14)

        # Set io_name to default if empty (ie: "CamIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "CamIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 0

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class DimmerIO(BaseIO):
    """domintell DimmerIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeDimmerIo", 3)

        # Set io_name to default if empty (ie: "Dimmer #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Dimmer #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 0
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
            LightColorMode.BRIGHTNESS,
        }

        if self.module_type == "DIM":
            self._brightness_scale = (10, 100)
        else:
            self._brightness_scale = (1, 100)

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        # Make sure we have state from 0 to 100%
        self._state = 0 if self.state < 0 else 100 if self.state > 100 else state

    @property
    def brightness_scale(self) -> tuple:
        return self._brightness_scale

    @property
    def brightness(self) -> int:
        return self._state

    def is_on(self) -> bool:
        return True if self.state > 0 else False

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def set_value(self, value: int) -> None:
        await self._send_command("Set Value", value)

    async def increase_value(self) -> None:
        await self._send_command("Increase")

    async def decrease_value(self) -> None:
        await self._send_command("Decrease")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class LbIO(BaseIO):
    """domintell LbIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeLbIo", 42)

        # Set io_name to default if empty (ie: "OutputLb #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "OutputLb #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._brightness_scale: tuple = (1, 100)
        self._state: int = 0
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
            LightColorMode.BRIGHTNESS,
        }

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        # Make sure we have state from 0 to 100%
        self._state = 0 if self.state < 0 else 100 if self.state > 100 else state

    @property
    def brightness_scale(self) -> tuple:
        return self._brightness_scale

    @property
    def brightness(self) -> int:
        return self._state

    def is_on(self) -> bool:
        return True if self.state > 0 else False

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def set_value(self, value: int) -> None:
        await self._send_command("Set Value", value)

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class DmxIO(BaseIO):
    """domintell DmxIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeDmxIo", 25)

        # Set io_name to default if empty (ie: "DMX Slave #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "DMX Slave #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._brightness_scale: tuple = (0, 255)
        self._nbr_of_channels = 0
        self._dmx_type = DmxType.UNKNOWN
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
            LightColorMode.BRIGHTNESS,
        }

        # Process configuration
        if self.module_type == "DMX":
            # Legacy module
            # ["R 0x00-0xFF", "G 0x00-0xFF", "B 0x00-0xFF", "I 0x00-0x64"]
            # ["R 0x00-0xFF", "G 0x00-0xFF", "B 0x00-0xFF"]
            # ["G 0x00-0xFF", "R 0x00-0xFF", "B 0x00-0xFF"] # channels not in order!
            # ["I 0x00-0xFF", "I 0x00-0xFF"]
            # ...
            # Note: The maximum number of channels is 8
            self._nbr_of_channels = len(self.extra_info)

            # TODO si on a juste RGB (ou dans le désordre) -> RGB
            # mais il faut connaitre le canal de chaque couleur pour le pilotage
            # on peut avoir jusqu'a 8 canaux
            channels_types_list = [
                channel[0] for channel in self.extra_info
            ]  # ie: ["R","G","B","I"]

        else:
            # New gen module
            # [nbr_of_channels, dmx_type] -> ["3", "1"] -> RGB
            # Note: Order of channels are fixed
            #       Number of channels is used for command (see mask value)
            try:
                if len(self.extra_info) >= 2:
                    self._nbr_of_channels = int(self.extra_info[0])
                    dmx_type = int(self.extra_info[1])
                    self._dmx_type = DmxType(dmx_type)
                else:
                    raise ValueError("missing extra information for DMX")
            except Exception:
                self._nbr_of_channels = 0
                self._configuration = DmxType.UNKNOWN

        # Set state type and color mode
        if self._dmx_type == DmxType.RGBWI:
            self._state: ColorRGBWI = ColorRGBWI(0, 0, 0, 0, 0)
            self._color_mode.add(LightColorMode.RGBW)
        elif self._dmx_type == DmxType.RGBW:
            self._state: ColorRGBW = ColorRGBW(0, 0, 0, 0)
            self._color_mode.add(LightColorMode.RGBW)
        elif self._dmx_type == DmxType.RGBI:
            self._state: ColorRGBI = ColorRGBI(0, 0, 0, 0)
            self._color_mode.add(LightColorMode.RGB)
        elif self._dmx_type == DmxType.RGB:
            self._state: ColorRGB = ColorRGB(0, 0, 0)
            self._color_mode.add(LightColorMode.RGB)
        elif self._dmx_type == DmxType.SINGLE:
            self._state: int = 0
        else:
            self._state: int = 0

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

        # TODO les DMX on des dmx_channel pour représenter la couleur
        # mask
        # channel_offset = 0
        # channel_val = 0

        # channel: dict[int, int] = {0: 255, 1: 0, 2: 52}
        # dmx_data = {"mask": 0x06, "channel": channel}

        # exemple de status frame legacy DMX0000001F-2X00EB000000000000
        # exemple de status frame new gen DX2/20/25/2/71|0x06|0|56|55 # 0x06 est le mask
        # TODO il faut une représentation spéciale avec la liste des channel_offset et _val

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state) -> None:
        self._state = state

    @property
    def brightness_scale(self) -> tuple:
        return self._brightness_scale

    @property
    def brightness(self) -> int:
        if type(self._state) == int:
            return self._state
        else:
            return self._state.get_max_value()

    def is_on(self) -> bool:
        state = self.state
        if type(state) == int:
            return True if state > 0 else False
        else:
            return state.is_on()

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def set_value(self, value: int) -> None:
        await self.set_intensity(value)

    async def set_intensity(self, value: int) -> None:
        if self._dmx_type == DmxType.RGBW or self._dmx_type == DmxType.RGBWI:
            intensity = ["0x10", 0, 0, 0, 0, value]
        elif self._dmx_type == DmxType.RGB or self._dmx_type == DmxType.RGBI:
            intensity = ["0x08", 0, 0, 0, value]
        elif self._dmx_type == DmxType.SINGLE:
            intensity = ["0x01", value]
        else:
            return

        command_message = LpCommand(self.id, "Set Color", intensity)
        await self._gateway._client.send_command(command_message)

    async def set_color(self, value: dict) -> None:
        if self._dmx_type == DmxType.RGBW or self._dmx_type == DmxType.RGBWI:
            color = ["0x0F", value["r"], value["g"], value["b"], value["w"]]
        elif self._dmx_type == DmxType.RGB or self._dmx_type == DmxType.RGBI:
            color = ["0x07", value["r"], value["g"], value["b"]]
        else:
            return

        command_message = LpCommand(self.id, "Set Color", color)
        await self._gateway._client.send_command(command_message)

    async def set_color_cycle(self, enable: bool | None) -> None:
        # Available on RGB only
        value = None if enable is None else (1 if enable else 0)
        await self._send_command("Color Cycle", value)

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class DaliIO(BaseIO):
    """domintell DaliIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeDali", 29)

        # Set io_name to default if empty (ie: "Dali #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Dali #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._brightness_scale: tuple = (1, 100)
        self._state: int = 0
        self._light_type: str = self.extra_info[0]
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
            LightColorMode.BRIGHTNESS,
        }

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def light_type(self) -> str:
        return self._light_type

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        # Make sure we have state from 0 to 100%
        self._state = 0 if self.state < 0 else 100 if self.state > 100 else state

    @property
    def brightness_scale(self) -> tuple:
        return self._brightness_scale

    @property
    def brightness(self) -> int:
        return self._state

    def is_on(self) -> bool:
        return True if self.state > 0 else False

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def set_value(self, value: int) -> None:
        await self._send_command("Set Value", value)

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class RgbwIO(BaseIO):
    """domintell RgbwIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeRgbwIo", 46)

        # Set io_name to default if empty (ie: "RgbwIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "RgbwIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._brightness_scale: tuple = (0, 255)
        self._state: ColorRGBW = ColorRGBW(0, 0, 0, 0)
        self._color_mode: set[LightColorMode] = {
            LightColorMode.ONOFF,
            LightColorMode.BRIGHTNESS,
            LightColorMode.RGBW,
        }

    @property
    def color_mode(self) -> LightColorMode:
        return self._color_mode

    @property
    def state(self) -> ColorRGBW:
        return self._state

    @state.setter
    def state(self, state: ColorRGBW) -> None:
        self._state = state

    @property
    def brightness_scale(self) -> tuple:
        return self._brightness_scale

    @property
    def brightness(self) -> int:
        return self._state.get_max_value()

    def is_on(self) -> bool:
        state = self.state
        if (state.r > 0) or (state.g > 0) or (state.b > 0) or (state.w > 0):
            return True
        else:
            return False

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        await self._send_command("On")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def toggle(self) -> None:
        await self._send_command("Toggle")

    async def set_value(self, value: int) -> None:
        await self.set_intensity(value)

    async def set_intensity(self, value: int) -> None:
        # intensity = [16, 0, 0, 0, 0, value]
        color = self.state
        intensity = [31, color.r, color.g, color.b, color.w, value]

        command_message = LpCommand(self.id, "Set Color", intensity)
        await self._gateway._client.send_command(command_message)

    async def set_color(self, value: dict) -> None:
        # color = [15, value["r"], value["g"], value["b"], value["w"]]
        color = [31, value["r"], value["g"], value["b"], value["w"], self.brightness]
        command_message = LpCommand(self.id, "Set Color", color)
        await self._gateway._client.send_command(command_message)

    async def set_color_cycle(self, enable: bool | None) -> None:
        value = None if enable is None else (1 if enable else 0)
        await self._send_command("Color Cycle", value)

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class In10VIO(BaseIO):
    """domintell In10VIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeIn10VIo", 21)

        # Set io_name to default if empty (ie: "In10VIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "In10VIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 0  # from 0 to 100% (0 to 10V)

        # Process configuration
        try:
            if self.extra_info[0] == "ANALOG":
                # ["ANALOG-MIN=-10.5-MAX=120-UNIT=°C"] -> ["ANALOG","-10.5","120","°C"]
                min = float(self.extra_info[1])
                max = float(self.extra_info[2])
                unit = float(self.extra_info[3])
                self._configuration: AnalogConfig = AnalogConfig(min, max, unit)

                # Parce unit in SI
                self.update_attributes()
        except Exception:
            # default = ["ANALOG","0.0","100.0","V"]
            self._configuration: AnalogConfig = AnalogConfig()

    @property
    def config(self) -> AnalogConfig:
        return self._configuration

    @config.setter
    def config(self, config: AnalogConfig) -> None:
        self._state = 0
        self._configuration = config

    @property
    def unit(self) -> str:
        return self._configuration.unit

    @property
    def value(self) -> int:
        return self._state

    @property
    def percent(self) -> int:
        return self._state

    @property
    def voltage(self) -> float:
        return float(self._state) / 10.0  # in Volt

    @property
    def _state_to_unit(self) -> float | None:
        return (self.config.max - self.config.min) * self._state / 100

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        # Make sure we have state from 0 to 100%
        self._state = 0 if self.state < 0 else 100 if self.state > 100 else state
        self.update_attributes()

    def update_attributes(self):
        # Parce unit in SI
        match self.config.unit.lower():
            case "°c":
                setattr(self, "temperature", self._state_to_unit)
            case "l":
                setattr(self, "liter", self._state_to_unit)
            case "m":
                setattr(self, "meter", self._state_to_unit)
            case "m³":
                setattr(self, "cubic_meter", self._state_to_unit)
            case "m3":
                setattr(self, "cubic_meter", self._state_to_unit)
            case _:
                pass

    def is_on(self) -> bool:
        return True if self.state > 0 else False

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class GestureIO(BaseIO):
    """domintell GestureIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeGestureIo", 49)

        # Set io_name to default if empty (ie: "GestureIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "GestureIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: GestureState = GestureState.UNKNOWN

    @property
    def state(self) -> GestureState:
        return self._state

    @state.setter
    def state(self, state: GestureState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def execute_link(self, gesture: GestureState) -> None:
        print(f"Execute link for {gesture} of GestureIO id: {self.id}")
        cmd = "Gesture up"
        match gesture:
            case GestureState.GESTURE_RIGHT:
                cmd = "Gesture right"
            case GestureState.GESTURE_LEFT:
                cmd = "Gesture left"
            case GestureState.GESTURE_UP:
                cmd = "Gesture up"
            case GestureState.GESTURE_DOWN:
                cmd = "Gesture down"
            case GestureState.GESTURE_PUSH:
                cmd = "Gesture push"
            case _:
                print("Unkown gesture state:", gesture)
                return

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class IrIO(BaseIO):
    """domintell IrIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeIrIO", 9)

        # Set io_name to default if empty (ie: "IrIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "IrIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._key: int = 0  # 0 to 32
        self._state: PushState = PushState.UNKNOWN

    @property
    def key(self) -> int:
        return self._key

    @property
    def state(self) -> PushState:
        return self._state

    @key.setter
    def key(self, state: int) -> None:
        # Make sure we have maximum 32
        self._state = 0 if self.state > 32 else state

    @state.setter
    def state(self, state: PushState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class DfanComboIO(BaseIO):
    """domintell DfanComboIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeDfanComboIo", 12)

        # Set io_name to default if empty (ie: "DfanComboIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "DfanComboIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: DfanComboState = DfanComboState()

    @property
    def number_of_speeds(self) -> int:
        return self._state.number_of_speeds

    @property
    def has_off_speed(self) -> bool:
        return True

    @property
    def has_auto_speed(self) -> bool:
        return True

    @property
    def speed(self) -> int:
        return self._state.speed

    @property
    def mode(self) -> str:
        return self._state.mode

    @property
    def state(self) -> DfanComboState:
        return self._state

    def is_on(self) -> bool:
        return True if self.state.speed > 0 else False

    @state.setter
    def state(self, state: DfanComboState) -> None:
        self._state = state

    def supports_speed(self) -> bool:
        """Return True if this IO supports any of the speed related commands."""
        return True

    def supports_off(self) -> bool:
        """Return True if this IO supports turn off commands."""
        return self.has_off_speed

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def set_value(self, value: int) -> None:
        if value == 0:
            await self.turn_off()
        else:
            message = self.id[:9] + "-" + str(value) + "%I"
            await self._gateway._client.send_message(message)

    async def set_mode(self, mode: str) -> None:
        base_message = self.id[:9] + "-6"

        if mode == "AUTO":
            message = base_message + "%O"
        else:
            message = base_message + "%I"

        await self._gateway._client.send_message(message)

    async def set_heating(self, mode: str) -> None:
        base_message = self.id[:9]

        if mode == "HEATING":
            # Set Heating (if speed different of 0) Advise : change T° sensor setpoint!
            message = base_message + "-4%I"
        else:
            # Set Cooling (if speed different of 0) Advise : change T° sensor setpoint!
            message = base_message + "-5%I"

        if self._state.speed != 0:
            await self._gateway._client.send_message(message)
        else:
            print("To set Heating/Cooling need to change change T° sensor setpoint!")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class FanIO(BaseIO):
    """domintell FanIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeFanIo", 13)

        # Set io_name to default if empty (ie: "FanIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "FanIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 255

        # Process configuration
        try:
            number_of_speeds, has_off_speed, has_auto_speed = map(int, self.extra_info)
            self._configuration: FanConfig = FanConfig(
                number_of_speeds, bool(has_off_speed), bool(has_auto_speed)
            )
        except Exception:
            self._configuration: FanConfig = FanConfig()

    @property
    def config(self) -> FanConfig:
        return self._configuration

    @config.setter
    def config(self, config: FanConfig) -> None:
        self._state = 255
        self._configuration = config

    @property
    def number_of_speeds(self) -> int:
        return self.config.number_of_speeds

    @property
    def has_off_speed(self) -> bool:
        return self.config.has_off_speed

    @property
    def has_auto_speed(self) -> bool:
        return self.config.has_auto_speed

    @property
    def speed(self) -> int:
        return 0 if self._state > self.number_of_speeds else self._state

    @property
    def mode(self) -> str:
        return "AUTO" if self._state == 254 else "MANUAL"

    # @property
    # def mode(self) -> FanMode:
    #     return FanMode.AUTO if self._state == 254 else FanMode.MANUAL

    @property
    def state(self) -> int:
        """State of the FanIO.

        Returns:
            0 to <number_of_speeds> if has_off_speed=True or

            1 to <number_of_speeds> if has_off_speed=False
        """
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        # Make sure we have maximum 255
        self._state = 255 if self.state > 255 else state

    def is_on(self) -> bool:
        if self._state == 0 or self._state == 255:
            return False
        else:
            return True

    def supports_speed(self) -> bool:
        """Return True if this IO supports any of the speed related commands."""
        return True

    def supports_off(self) -> bool:
        """Return True if this IO supports turn off commands."""
        return self.has_off_speed

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_off(self) -> None:
        await self._send_command("Off")

    async def set_value(self, value: int) -> None:
        # Case of DMV01
        if self.module_type == "DMV":
            if value == 0:
                await self.turn_off()
            else:
                message = self.id[:9] + "-" + str(value) + "%I"
                await self._gateway._client.send_message(message)
        else:
            await self._send_command("Set Value", value)

    async def increase_value(self) -> None:
        if self.module_type != "DMV":
            await self._send_command("Increase")

    async def decrease_value(self) -> None:
        if self.module_type != "DMV":
            await self._send_command("Decrease")

    async def set_mode(self, mode: str) -> None:
        if self.has_auto_speed:
            if mode == "AUTO":
                await self.set_value(254)
            else:
                # No command to set to manual mode so set speed to 1
                await self.set_value(1)

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class VanesIO(BaseIO):
    """domintell VanesIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeVanesIo", 54)

        # Set io_name to default if empty (ie: "VanesIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "VanesIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 255

        # Process configuration
        try:
            number_of_positions, has_auto_speed, has_frozen_mode, has_swing_mode = map(
                int, self.extra_info
            )
            self._configuration: VanesConfig = VanesConfig(
                number_of_positions,
                bool(has_auto_speed),
                bool(has_frozen_mode),
                bool(has_swing_mode),
            )
        except Exception:
            self._configuration: VanesConfig = VanesConfig()

    @property
    def config(self) -> VanesConfig:
        return self._configuration

    @config.setter
    def config(self, config: VanesConfig) -> None:
        self._state = 255  # UNKNOWN
        self._configuration = config

    @property
    def number_of_position(self) -> int:
        return self.config.number_of_position

    @property
    def has_auto_speed(self) -> bool:
        return self.config.has_auto_speed

    @property
    def has_frozen_mode(self) -> bool:
        return self.config.has_frozen_mode

    @property
    def has_swing_mode(self) -> bool:
        return self.config.has_swing_mode

    @property
    def position(self) -> int:
        return self._state

    @property
    def mode(self) -> VanesMode:
        if self._state < 252:
            return VanesMode.MANUAL
        else:
            return VanesMode(self._state)

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        # Make sure we have maximum 255
        self._state = 255 if self.state > 255 else state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def set_value(self, value: int) -> None:
        await self._send_command("Set Value", value)

    async def increase_value(self) -> None:
        await self._send_command("Increase")

    async def decrease_value(self) -> None:
        await self._send_command("Decrease")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class MovIO(BaseIO):
    """domintell MovIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeMovIo", 34)

        # Set io_name to default if empty (ie: "MovIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "MovIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: MotionState = MotionState.UNKNOWN

    @property
    def motion(self) -> bool:
        return True if self._state == MotionState.START_DETECTION else False

    @property
    def state(self) -> MotionState:
        return self._state

    @state.setter
    def state(self, state: MotionState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def execute_link(self, detection_state: MotionState) -> None:
        print(f"Execute link for {detection_state} of MovIO id: {self.id}")
        cmd = "Start of short push"
        match detection_state:
            case MotionState.START_DETECTION:
                cmd = "Start of detection"
            case MotionState.END_DETECTION:
                cmd = "End of detection"
            case _:
                print("Unkown detection state:", detection_state)
                return

        await self._send_command(cmd)

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class SensorIO(BaseIO):
    """domintell SensorIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeSensorIo", 8)

        # Set io_name to default if empty (ie: "Temperature #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Temperature #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: ThermostatState = ThermostatState()

        # Process configuration
        # Format:  extra_info: [<regul_mask>,<temperature_mask>,<heat_limit_high>,<heat_limit_low>,<cool_limit_high>,<cool_limit_low>,<setpoint_step>, ...]
        try:
            config_dict = {
                "regul_mask": int(self.extra_info[0], 16),
                "temp_mask": int(self.extra_info[1], 16),
                "heat_limit_high": float(self.extra_info[2]),
                "heat_limit_low": float(self.extra_info[3]),
                "cool_limit_high": float(self.extra_info[4]),
                "cool_limit_low": float(self.extra_info[5]),
                "setpoint_step": float(self.extra_info[6]),
            }

            self._configuration = ThermostatConfig(**config_dict)
            self._have_link = (
                False
                if (len(self.extra_info) >= 8 and self.extra_info[7] == "NOLINK")
                else True
            )
        except Exception:
            print("Thermostat configuration data is incorrect")
            self._configuration = ThermostatConfig()

    @property
    def temperature(self) -> float:
        return self._state.current_temperature  # in °C

    @property
    def state(self) -> ThermostatState:
        return self._state

    @state.setter
    def state(self, state: ThermostatState) -> None:
        self._state = state

    @property
    def temperature_mode(self) -> TemperatureMode:
        return self._state.temperature_mode

    @property
    def regulation_mode(self) -> RegulationMode:
        return self._state.regulation_mode

    @property
    def config(self) -> ThermostatConfig:
        return self._configuration

    @config.setter
    def config(self, config: ThermostatConfig) -> None:
        self._configuration = config

    @property
    def is_thermostat(self) -> bool:
        return False if self.config.regul_mask == 255 else True

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def set_heating_set_point(self, set_point: float) -> None:
        await self._send_command("Set Heating Setpoint", set_point)

    async def set_cooling_set_point(self, set_point: float) -> None:
        await self._send_command("Set Cooling Setpoint", set_point)

    async def set_mode_temperature(self, mode: TemperatureMode) -> None:
        data: int = mode.value
        await self._send_command("Set Mode Temperature", data)

    async def set_mode_regulation(self, mode: RegulationMode) -> None:
        data: int = mode.value
        await self._send_command("Set Mode Regulation", data)

    async def _send_command(self, cmd: str, value: int | float = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class LuxIO(BaseIO):
    """domintell LuxIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeLuxIo", 36)

        # Set io_name to default if empty (ie: "Light Level #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Light Level #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 0  # in lux

    @property
    def illuminance(self) -> int:
        return self._state

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class HumidityIO(BaseIO):
    """domintell HumidityIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeHumidityIo", 37)

        # Set io_name to default if empty (ie: "Humidity #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Humidity #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: float = 0.0  # in % RH

    @property
    def humidity(self) -> float:
        return self._state

    @property
    def state(self) -> float:
        return self._state

    @state.setter
    def state(self, state: float) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class PressureIO(BaseIO):
    """domintell PressureIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypePressureIo", 38)

        # Set io_name to default if empty (ie: "Pressure #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Pressure #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: float = 0.0  # in hPa

    @property
    def pressure(self) -> float:
        return self._state

    @property
    def state(self) -> float:
        return self._state

    @state.setter
    def state(self, state: float) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class Co2IO(BaseIO):
    """domintell Co2IO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeCo2Io", 39)

        # Set io_name to default if empty (ie: "Co2IO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Co2IO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: float = 0.0  # in ppm

    @property
    def co2(self) -> float:
        return self._state

    @property
    def state(self) -> float:
        return self._state

    @state.setter
    def state(self, state: float) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class WindIO(BaseIO):
    """domintell WindIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeWindIo", 41)

        # Set io_name to default if empty (ie: "WindIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "WindIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: WindState = WindState(0.0, WindDirection.UNKNOWN)

    @property
    def wind_speed(self) -> float:
        return self._state.speed

    @property
    def wind_direction(self) -> str:
        return self._state.direction.value()

    @property
    def state(self) -> WindState:
        return self._state

    @state.setter
    def state(self, state: WindState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class PowerSupplyIO(BaseIO):
    """domintell PowerSupplyIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypePowerSupplyIo", 51)

        # Set io_name to default if empty (ie: "PowerSupplyIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "PowerSupplyIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: PowerSupplyState = PowerSupplyState()

    @property
    def power_supply_load(self) -> int:
        return self._state.load

    @property
    def output_voltage(self) -> float:
        return self._state.voltage

    @property
    def internal_temperature(self) -> float:
        return self._state.temperature

    @property
    def state(self) -> PowerSupplyState:
        return self._state

    @state.setter
    def state(self, state: PowerSupplyState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class ElecIO(BaseIO):
    """domintell ElecIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeElecIo", 51)

        # Set io_name to default if empty (ie: "ElecIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "ElecIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: ElectricityState = ElectricityState()  # Default values @ 0

        # Process configuration
        try:
            self._nbr_of_phases = int(self.extra_info[0])
        except Exception:
            self._nbr_of_phases = 3  # Default to triphases

    @property
    def nbr_of_phases(self) -> int:
        return self._nbr_of_phases

    @nbr_of_phases.setter
    def nbr_of_phases(self, nbr_of_phases: int) -> None:
        self._nbr_of_phases = nbr_of_phases

    @property
    def state(self) -> ElectricityState:
        return self._state

    @state.setter
    def state(self, state: ElectricityState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class SoundIO(BaseIO):
    """domintell SoundIO reprensentation."""

    # Note: This IO type is not handled

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeSoundIo", 23)

        # Set io_name to default if empty (ie: "SoundIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "SoundIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 0

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    # TODO add possible commands
    # like %F to set frequency

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class GenericSoundIo(BaseIO):
    """domintell GenericSoundIo reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeGenericSoundIo", 43)

        # Set io_name to default if empty (ie: "Generic SoundIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Generic SoundIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: list = []  # ie: "2|4|0|255|"

    @property
    def state(self) -> list:
        return self._state

    @state.setter
    def state(self, state: list) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class DeviceStatus(BaseIO):
    """Domintell DeviceStatus reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeDeviceStatus", 55)

        # Set io_name to default if empty (ie: "Device Status #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Device Status #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: list = []

    @property
    def state(self) -> list:
        return self._state

    @state.setter
    def state(self, state: list) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class PercentIO(BaseIO):
    """Domintell PercentIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypePercentIo", 56)

        # Set io_name to default if empty (ie: "PercentIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "PercentIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: int = 0

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        # Make sure we have state from 0 to 100%
        self._state = 0 if self.state < 0 else 100 if self.state > 100 else state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class AnalogInIO(BaseIO):
    """Domintell AnalogInIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeAnalogInIo", 57)

        # Set io_name to default if empty (ie: "AnalogInIO #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "AnalogInIO #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: float = 0.0

    @property
    def value(self) -> int:
        return self._state

    @property
    def state(self) -> float:
        return self._state

    @state.setter
    def state(self, state: float) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class VarIO(BaseIO):
    """Domintell VarIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeVar", 16)

        # Set io_name to default if empty (ie: "Variable #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Variable #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._is_read_only = True
        self._is_master_only = False
        self._is_bool_status = False
        self._state_range: tuple[int, int] = (0, 100)
        self._state: int = 0  # Absolute Max is 100

        # Process configuration
        # ie: ['VALU,00->40', 'MASTERONLY']
        # ie: ['VALU,00->50,LOOP']
        # ie: ['VALU,00->20']
        # ie: ['BOOL']
        self._is_bool_status = True if "BOOL" in self.extra_info else False
        self._is_read_only = True if "READONLY" in self.extra_info else False
        self._is_master_only = True if "MASTERONLY" in self.extra_info else False

        if len(self.extra_info) >= 1:
            if self._is_bool_status == False:
                parts = self.extra_info[0].split(",")
                if len(parts) >= 2:
                    range_part = parts[1].split("->")
                    if len(range_part) == 2:
                        try:
                            start = int(range_part[0])
                            end = int(range_part[1].split(",")[0])
                            self._state_range = (start, end)
                        except ValueError:
                            self._state_range = (0, 100)
            else:
                self._state_range = (0, 1)

    @property
    def is_master_only(self) -> bool:
        return self._is_master_only

    @property
    def is_read_only(self) -> bool:
        return self._is_read_only

    @property
    def is_bool_status(self) -> bool:
        return self._is_bool_status

    @property
    def state_range(self) -> tuple[int, int]:
        return self._state_range

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        self._state = state

    def is_on(self) -> bool:
        return False if self.state == 0 else True

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        if self._is_read_only:
            return
        await self._send_command("On")

    async def turn_off(self) -> None:
        if self._is_read_only:
            return
        await self._send_command("Off")

    async def toggle(self) -> None:
        if self._is_read_only:
            return
        await self._send_command("Toggle")

    async def set_value(self, value: int) -> None:
        start, end = self._state_range
        if self._is_read_only:
            return
        if value > end:
            value = end
        if value < start:
            value = start

        if self._is_bool_status:
            if value == 0:
                await self.turn_off()
            else:
                await self.turn_on()
        else:
            await self._send_command("Set Value", value)

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class VarSysIO(BaseIO):
    """Domintell VarSysIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeVarSys", 17)

        # Set io_name to default if empty (ie: "System variable #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "System variable #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._is_read_only: bool = True
        self._is_master_only = False
        self._is_bool_status: bool = True
        self._state_range: tuple[int, int] = (0, 100)
        self._state: int = 0

        # Notes:
        # "SYS000000" -> 0 = Simulation is not playing (only record) and 1 = Simulation is playing
        # "SYS000009" -> Based on astronomical clock, 0 = Night and 1 = Daytime (Read Only)

        # Process configuration
        # ie: ['BOOL'] for "SYS000000"
        # ie: ['BOOL', 'READONLY'] for "SYS000009"
        self._is_bool_status = True if "BOOL" in self.extra_info else False
        self._is_read_only = True if "READONLY" in self.extra_info else False
        self._is_master_only = True if "MASTERONLY" in self.extra_info else False

        if len(self.extra_info) >= 1:
            if self._is_bool_status:
                parts = self.extra_info[0].split(",")
                if len(parts) >= 2:
                    range_part = parts[1].split("->")
                    if len(range_part) == 2:
                        try:
                            start = int(range_part[0])
                            end = int(range_part[1].split(",")[0])
                            self._state_range = (start, end)
                        except ValueError:
                            self._state_range = (0, 100)
            else:
                self._state_range = (0, 1)

        # Create attribute only for system variable "SYS000009"
        if self.io_offset == 9:
            self.update_attributes()

    @property
    def is_master_only(self) -> bool:
        return self._is_master_only

    @property
    def is_read_only(self) -> bool:
        return self._is_read_only

    @property
    def is_bool_status(self) -> bool:
        return self._is_bool_status

    @property
    def state_range(self) -> tuple[int, int]:
        return self._state_range

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state: int) -> None:
        self._state = state
        self.update_attributes()

    def update_attributes(self):
        if self.io_offset == 9:
            setattr(self, "night_and_day", "night" if self._state == 0 else "day")

    def is_on(self) -> bool:
        return False if self.state == 0 else True

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def turn_on(self) -> None:
        if self._is_read_only:
            return
        await self._send_command("On")

    async def turn_off(self) -> None:
        if self._is_read_only:
            return
        await self._send_command("Off")

    async def toggle(self) -> None:
        if self._is_read_only:
            return
        await self._send_command("Toggle")

    async def set_value(self, value: int) -> None:
        start, end = self._state_range
        if self._is_read_only:
            return

        if value > end:
            value = end
        if value < start:
            value = start

        if self._is_bool_status:
            if value == 0:
                await self.turn_off()
            else:
                await self.turn_on()
        else:
            await self._send_command("Set Value", value)

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class CloudInfo(BaseIO):
    """Domintell CloudInfo reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeCloudInfo", 62)

        # Set io_name to default if empty (ie: "Cloud Info #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Cloud Info #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: CloudInfoState = CloudInfoState()

    @property
    def allowed(self) -> int:
        return self._state.allowed

    @property
    def registered(self) -> bool:
        return self._state.registered

    @property
    def connected(self) -> bool:
        return self._state.connected

    @property
    def error_code(self) -> int:
        return CloudInfoErrorCode(self._state.error_code).name

    @property
    def error_description(self) -> str:
        return self._state.error_description

    @property
    def state(self) -> CloudInfoState:
        return self._state

    @state.setter
    def state(self, state: CloudInfoState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class EthernetInfo(BaseIO):
    """Domintell EthernetInfo reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeEthernetInfo", 63)

        # Set io_name to default if empty (ie: "Memory Info #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Memory Info #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: list = []

    @property
    def state(self) -> list:
        return self._state

    @state.setter
    def state(self, state: list) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class MemoryInfo(BaseIO):
    """Domintell MemoryInfo reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeMemoryInfo", 64)

        # Set io_name to default if empty (ie: "Memory Info #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Memory Info #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: MemoryInfoState = MemoryInfoState()

    @property
    def state(self) -> MemoryInfoState:
        return self._state

    @state.setter
    def state(self, state: MemoryInfoState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class StorageInfo(BaseIO):
    """Domintell StorageInfo reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeStorageInfo", 64)

        # Set io_name to default if empty (ie: "Storage Info #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Storage Info #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: list = []

    @property
    def state(self) -> list:
        return self._state

    @state.setter
    def state(self, state: list) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class CpuInfo(BaseIO):
    """Domintell CpuInfo reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeCpuInfo", 66)

        # Set io_name to default if empty (ie: "CPU Info #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "CPU Info #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: CpuInfoState = CpuInfoState()

    @property
    def state(self) -> CpuInfoState:
        return self._state

    @state.setter
    def state(self, state: CpuInfoState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class DiBusGwInfo(BaseIO):
    """Domintell DiBusGwInfo reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        kwargs["io_type"] = IO_TYPES_INT.get("TypeDiBusGwInfo", 66)

        # Set io_name to default if empty (ie: "DiBusGw Info #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "DiBusGw Info #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: DiBusGwInfoState = DiBusGwInfoState()

    @property
    def state(self) -> DiBusGwInfoState:
        return self._state

    @state.setter
    def state(self, state: DiBusGwInfoState) -> None:
        self._state = state

    async def update_state(self) -> None:
        await self._send_command("Get Status")

    async def _send_command(self, cmd: str, value: int = 0) -> None:
        command_message = LpCommand(self.id, cmd, [value])
        await self._gateway._client.send_command(command_message)


class GroupIO(BaseIO):
    """Domintell GroupIO reprensentation."""

    def __init__(self, gateway, **kwargs) -> None:
        # Set io_name to default if empty (ie: "Group #01")
        if kwargs["io_name"] == "":
            kwargs["io_name"] = "Group #" + str(kwargs["io_offset"]).zfill(2)

        super().__init__(**kwargs)
        self._gateway = gateway
        self._state: Any | None = None

        # Configuration
        io_type_str = IO_TYPES_STRING.get(self.io_type, "TypeIoNotHandled")

        # Retrieving target class methods
        parent_class = IOFactory()._io_classes[io_type_str]
        members = inspect.getmembers(parent_class)

        # Dynamic creation of methods and properties
        for member_name, member in members:
            if not member_name.startswith("__"):
                if inspect.isfunction(member):
                    # Bind methods
                    bound_method = types.MethodType(member, self)
                    setattr(self, member_name, bound_method)
                elif isinstance(member, property):
                    # Bind properties
                    setattr(self, member_name, member)

        # Configuration
        try:
            if len(self.extra_info) >= 2:
                ref_io: str = self.extra_info[1].split("REF=")[
                    1
                ]  # ie: "REF=QG2/253/6/1"
                self._ref_io: str = construct_endpoint_id(ref_io)
        except Exception:
            self._ref_io = None
            pass

    @property
    def ref_io(self) -> str | None:
        return self._ref_io


class IOFactory:
    """IO instance factory."""

    def __init__(self):
        self._io_classes: dict = {
            "TypeIoNotHandled": SceneIO,
            "TypeTorIo": TorIO,
            "TypeTorBasicTempoIo": TorBasicTempoIO,
            "TypeInputTriggerIo": InputTriggerIO,
            "TypeInputIo": InputIO,
            "TypeTrvIo": TrvIO,
            "TypeTrvBtIo": TrvBtIO,
            "TypeLedIo": LedIO,
            "TypeLed8cIo": Led8cIO,
            "TypeLedRgbIo": LedRgbIo,
            "TypePbLcdIo": PblcdIO,
            "TypeOut10VIo": Out10VIO,
            "TypeAccessControlIo": AccessControlIO,
            "TypeVideoIo": VideoIO,
            "TypeDimmerIo": DimmerIO,
            "TypeLbIo": LbIO,
            "TypeDmxIo": DmxIO,
            "TypeDali": DaliIO,
            "TypeRgbwIo": RgbwIO,
            "TypeIn10VIo": In10VIO,
            "TypeGestureIo": GestureIO,
            "TypeIrIo": IrIO,
            "TypeFanIo": FanIO,
            "TypeDfanComboIo": DfanComboIO,
            "TypeVanesIo": VanesIO,
            "TypeMovIo": MovIO,
            "TypeSensorIo": SensorIO,
            "TypeLuxIo": LuxIO,
            "TypeHumidityIo": HumidityIO,
            "TypePressureIo": PressureIO,
            "TypeCo2Io": Co2IO,
            "TypeWindIo": WindIO,
            "TypePowerSupplyIo": PowerSupplyIO,
            "TypeElecIo": ElecIO,
            "TypeSoundIo": SoundIO,
            "TypeGenericSoundIo": GenericSoundIo,
            "TypeDeviceStatus": DeviceStatus,
            "TypePercentInIo": PercentIO,
            "TypeAnalogInIo": AnalogInIO,
            "TypeVar": VarIO,
            "TypeVarSys": VarSysIO,
            # "TypeCloudNotif": CloudNotifInfo,
            "TypeCloudInfo": CloudInfo,
            "TypeEthernetInfo": EthernetInfo,
            "TypeMemoryInfo": MemoryInfo,
            "TypeStorageInfo": StorageInfo,
            "TypeCpuInfo": CpuInfo,
            "TypeDiBusGwInfo": DiBusGwInfo,
        }

    def create_io(self, io_type_str: str, *args, **kwargs):
        """Create an io instance."""

        if kwargs["module_type"] == "MEM":
            return GroupIO(*args, **kwargs)
        elif io_type_str in self._io_classes:
            return self._io_classes[io_type_str](*args, **kwargs)
        else:
            raise ValueError(f"Unknown IO type: {io_type_str}")
