import copy

from .base import BaseController
from .events import ResourceTypes, EventType
from ..iotypes import (
    PushState,
    GestureState,
    ThermostatState,
    TemperatureMode,
    RegulationMode,
    MotionState,
    WindState,
    WindDirection,
    PowerSupplyState,
    ElectricityState,
)
from ..const import SENSORS_TARGET_TYPE_LIST

ID_FILTER_ALL = "*"


class ButtonController(BaseController):
    """Controller holding and managing Domintell resources of type `button`."""

    item_type = ResourceTypes.BUTTON

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Button controller received update for unknown io {item_id}"
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]

            self._logger.debug(f"Update IO state for BUTTON/GESTURE IO Id: {item_id}")

            if isinstance(my_io.state, PushState):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    new_state = PushState(data[0])

                    # For TypeInputTriggerIo unknown state is same as button RELEASED
                    if my_io.io_type == 53:  # TypeInputTriggerIo
                        if new_state == PushState.RELEASED:
                            new_state = PushState.UNKNOWN

                    if new_state != PushState.UNKNOWN:
                        my_io.state = new_state
                    self._logger.debug(f"---> Button New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for Button IO has an incorrect format: data={data}"
                    )

                if previous_state == PushState.UNKNOWN:
                    # Do not propagate the event if previous state was unknown
                    # Case of the 1st start
                    return

                if my_io.state == previous_state:
                    # Propagate the event only if it has had an update
                    return

            elif isinstance(my_io.state, GestureState):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    new_state = GestureState(event_data["data"][0])
                    if new_state != GestureState.UNKNOWN:
                        my_io.state = new_state
                    self._logger.debug(f"---> Gesture New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for Gesture IO has an incorrect format: data={data}"
                    )

                if previous_state == GestureState.UNKNOWN:
                    # Do not propagate the event if previous state was unknown
                    # Case of the 1st start
                    return

            elif (isinstance(my_io.state, int)) and (my_io.io_type == 9):
                # Case of Ir Detector
                if (
                    (len(data) >= 1)
                    and (isinstance(data[0], int))
                    and (isinstance(data[1], int))
                ):
                    # data = [key, push_state]
                    my_io.key = event_data["data"][0]
                    my_io.state = PushState(event_data["data"][1])
                    self._logger.debug(
                        f"---> Ir detector New state: {my_io.state}, key: {my_io.key}"
                    )
                else:
                    self._logger.warning(
                        f"Status for Ir detector IO has an incorrect format: data={data}"
                    )

                if previous_state == PushState.UNKNOWN:
                    # Do not propagate the event if previous state was unknown
                    # Case of the 1st start
                    return

                if my_io.state == previous_state:
                    # Propagate the event only if it has had an update
                    return
            else:
                self._logger.warning(
                    f"The IO state type of Button/Gesture IO is not the expected one, state type: {type(my_io.state)}"
                )

        await super()._handle_event(event_type, event_data)


class MotionController(BaseController):
    """Controller holding and managing Domintell resources of type `motion`."""

    item_type = ResourceTypes.MOTION

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Motion controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Motion IO Id: {item_id}")

            if isinstance(my_io.state, MotionState):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    my_io.state = MotionState(data[0])
                else:
                    self._logger.warning(
                        f"Status for Motion IO has an incorrect format: data={data}"
                    )
                self._logger.debug(f"---> Motion New state: {my_io.state}")
            else:
                self._logger.warning(
                    f"The IO state type of Motion IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class ContactController(BaseController):
    """Controller holding and managing Domintell resources of type `contact`."""

    item_type = ResourceTypes.CONTACT

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Contact controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for CONTACT IO Id: {item_id}")

            if isinstance(my_io.state, bool):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    if data[0] == 1:
                        my_io.state = True
                    else:
                        my_io.state = False
                else:
                    self._logger.warning(
                        f"Status for Motion IO has an incorrect format: data={data}"
                    )

                self._logger.debug(f"---> Contact New state: {my_io.state}")
            else:
                self._logger.warning(
                    f"The IO state type of Contact IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class TamperController(BaseController):
    """Controller holding and managing Domintell resources of type `tamper`."""

    item_type = ResourceTypes.TAMPER

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Tamper controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Tamper IO Id: {item_id}")

            if isinstance(my_io.state, bool):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    if data[0] == 1:
                        my_io.state = True
                    else:
                        my_io.state = False
                else:
                    self._logger.warning(
                        f"Status for Tamper IO has an incorrect format: data={data}"
                    )

                self._logger.debug(f"---> Tamper New state: {my_io.state}")

            else:
                self._logger.warning(
                    f"The IO state type of Tamper IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class TemperatureController(BaseController):
    """Controller holding and managing Domintell resources of type `temperature`."""

    item_type = ResourceTypes.TEMPERATURE

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""

        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Temperature controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = copy.deepcopy(my_io.state)
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Temperature IO Id: {item_id}")

            if isinstance(my_io.state, float):
                if (len(data) >= 1) and (isinstance(data[0], float)):
                    my_io.state = data[0]
                else:
                    self._logger.warning(
                        f"Status for Temperature IO has an incorrect format: data={data}"
                    )
            elif isinstance(my_io.state, ThermostatState):
                if len(data) == 5 and data[0] == "T":
                    # Legacy status with data type = 'T'
                    my_io.state.current_temperature = data[1]
                    my_io.state.active_heating_setpoint = data[2]
                    my_io.state.heating_profile_setpoint = data[4]

                    try:
                        my_io.state.temperature_mode = TemperatureMode[data[3]]
                    except Exception:
                        self._logger.warning(
                            f"Status for Thermostat IO has an incorrect format: temperature_mode={data[3]}"
                        )

                elif len(data) == 5 and data[0] == "U":
                    # Legacy status with data type = 'U'
                    my_io.state.current_temperature = data[1]
                    my_io.state.active_cooling_setpoint = data[2]
                    my_io.state.cooling_profile_setpoint = data[4]

                    try:
                        my_io.state.regulation_mode = RegulationMode[data[3]]
                    except Exception:
                        self._logger.warning(
                            f"Status for Thermostat IO has an incorrect format: regulation_mode={data[3]}"
                        )

                elif len(data) == 7:
                    # NewGen status
                    try:
                        data[2] = TemperatureMode[data[2]]
                        data[5] = RegulationMode[data[5]]
                        my_io.state = ThermostatState(*data)
                    except Exception:
                        self._logger.warning(
                            f"Status for Thermostat IO has an incorrect format: data={data}"
                        )
                else:
                    self._logger.warning(
                        f"Status for Thermostat IO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of Temperature IO is not the expected one, state type: {type(my_io.state)}"
                )

            self._logger.debug(f"---> Temp. Sensor New state: {my_io.state}")

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class AnalogController(BaseController):
    """Controller holding and managing Domintell resources of type `analog`."""

    item_type = ResourceTypes.ANALOG

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""

        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Analog controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Analog IO Id: {item_id}")

            if isinstance(my_io.state, int):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    my_io.state = data[0]
                    self._logger.debug(f"---> Analog New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for Analog IO has an incorrect format: data={data}"
                    )
            elif isinstance(my_io.state, float):
                if (len(data) >= 1) and (isinstance(data[0], float)):
                    my_io.state = data[0]
                    self._logger.debug(f"---> Analog New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for Analog IO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of Analog IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class IlluminanceController(BaseController):
    """Controller holding and managing Domintell resources of type `illuminance`."""

    item_type = ResourceTypes.ILLUMINANCE

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    "Illuminance controller received update for unknown io %s", item_id
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Illuminance IO Id: {item_id}")

            if isinstance(my_io.state, int):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    my_io.state = data[0]
                    self._logger.debug(f"---> Illuminance New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for Illuminance IO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of Illuminance IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class HumidityController(BaseController):
    """Controller holding and managing Domintell resources of type `humidity`."""

    item_type = ResourceTypes.HUMIDITY

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Humidity controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Humidity IO Id: {item_id}")

            if isinstance(my_io.state, float):
                if (len(data) >= 1) and (isinstance(data[0], float)):
                    my_io.state = data[0]
                    self._logger.debug(f"---> Humidity New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for HumidityIO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of HumidityIO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class PressureController(BaseController):
    """Controller holding and managing Domintell resources of type `pressure`."""

    item_type = ResourceTypes.PRESSURE

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Pressure controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Pressure IO Id: {item_id}")

            if isinstance(my_io.state, float):
                if (len(data) >= 1) and (isinstance(data[0], float)):
                    my_io.state = data[0]
                    self._logger.debug(f"---> Pressure New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for PressureIO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of PressureIO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class CO2Controller(BaseController):
    """Controller holding and managing Domintell resources of type `co2`."""

    item_type = ResourceTypes.CO2

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"CO2 controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for CO2 IO Id: {item_id}")

            if isinstance(my_io.state, float):
                if (len(data) >= 1) and (isinstance(data[0], float)):
                    my_io.state = data[0]
                    self._logger.debug(f"---> CO2 New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for CO2 IO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of CO2 IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class WindController(BaseController):
    """Controller holding and managing Domintell resources of type `wind`."""

    item_type = ResourceTypes.WIND

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Wind controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = copy.deepcopy(my_io.state)
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Wind IO Id: {item_id}")

            if isinstance(my_io.state, WindState):
                if (
                    (len(data) >= 2)
                    and (isinstance(data[0], float))
                    and (isinstance(data[1], str))
                ):
                    wind_speed = data[0]
                    if data[1] == "":
                        data[1] = "unknown"

                    wind_direction = WindDirection(data[1])
                    my_io.state = WindState(wind_speed, wind_direction)
                    self._logger.debug(f"---> Wind New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for WindIO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of WindIO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class PowerSupplyController(BaseController):
    """Controller holding and managing Domintell resources of type `power_supply`."""

    item_type = ResourceTypes.POWER_SUPPLY

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"PowerSupply controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = copy.deepcopy(my_io.state)
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Power supply IO Id: {item_id}")

            if isinstance(my_io.state, PowerSupplyState):
                if (
                    (len(data) >= 3)
                    and (isinstance(data[0], int))
                    and (isinstance(data[1], float))
                    and (isinstance(data[2], float))
                ):
                    load = int(event_data["data"][0])
                    voltage = float(event_data["data"][1])
                    temperature = float(event_data["data"][2])
                    my_io.state = PowerSupplyState(load, voltage, temperature)
                    self._logger.debug(f"---> Power supply New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for PowerSupplyIO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of PowerSupplyIO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class ElectricityController(BaseController):
    """Controller holding and managing Domintell resources of type `electricity`."""

    item_type = ResourceTypes.ELECTRICITY

    async def _handle_event(
        self, event_type: EventType, event_data: dict | None
    ) -> None:
        """Handle incoming event for this resource."""
        if event_data is None:
            return

        item_id = event_data["id"]

        if event_type == EventType.RESOURCE_UPDATED:
            # Existing item updated
            my_io = self.get_io(item_id)
            if my_io is None:
                # Should not be possible but just in case
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Electricity controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = copy.deepcopy(my_io.state)
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Electricity IO Id: {item_id}")

            if isinstance(my_io.state, ElectricityState):
                if len(data) == 28:
                    my_io.state = ElectricityState.from_list(data)
                    self._logger.debug(f"---> Electricity New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for ElectricityIO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of ElectricityIO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                # Propagate the event only if it has had an update
                return

        await super()._handle_event(event_type, event_data)


class SensorsController(BaseController):
    """Controller holding and managing Domintell sensors."""

    item_type = ResourceTypes.SENSOR

    def __init__(self, gateway) -> None:
        """Initialize instance."""

        # Sub-Controllers
        self.button = ButtonController(gateway)
        self.motion = MotionController(gateway)
        self.contact = ContactController(gateway)
        self.temperature = TemperatureController(gateway)
        self.analog = AnalogController(gateway)
        self.illuminance = IlluminanceController(gateway)
        self.humidity = HumidityController(gateway)
        self.pressure = PressureController(gateway)
        self.carbon_dioxide = CO2Controller(gateway)
        self.wind = WindController(gateway)
        self.power_supply = PowerSupplyController(gateway)
        self.electricity = ElectricityController(gateway)

        super().__init__(gateway)

    async def initialize(self) -> None:
        """Initialize sensors IO."""

        for module in self._gateway.modules.values():
            for io in module.values():
                if io.target_type in SENSORS_TARGET_TYPE_LIST:
                    await self._handle_event(
                        EventType.RESOURCE_ADDED, {"id": io.id, "instance": io}
                    )

        # Initialize sub-controllers
        await self.button.initialize()
        await self.motion.initialize()
        await self.contact.initialize()
        await self.temperature.initialize()
        await self.analog.initialize()
        await self.illuminance.initialize()
        await self.humidity.initialize()
        await self.pressure.initialize()
        await self.carbon_dioxide.initialize()
        await self.wind.initialize()
        await self.power_supply.initialize()
        await self.electricity.initialize()

        self._logger.debug("fetched %s sensors", len(self.items))
        self._logger.debug("fetched %s buttons", len(self.button.items))

        self._initialized = True

    async def update(self, ios_removed, ios_added):
        """Update sensors IO."""

        for io in ios_removed:
            if io["target_type"] in SENSORS_TARGET_TYPE_LIST:
                await self._handle_event(EventType.RESOURCE_DELETED, {"id": io["id"]})

        for io in ios_added:
            if io["target_type"] in SENSORS_TARGET_TYPE_LIST:
                instance = self._gateway.modules.get_io(io["id"])
                if instance is not None:
                    await self._handle_event(
                        EventType.RESOURCE_ADDED, {"id": io["id"], "instance": instance}
                    )

        # Update sub-controllers io
        await self.button.update(ios_removed, ios_added)
        await self.motion.update(ios_removed, ios_added)
        await self.contact.update(ios_removed, ios_added)
        await self.temperature.update(ios_removed, ios_added)
        await self.analog.update(ios_removed, ios_added)
        await self.illuminance.update(ios_removed, ios_added)
        await self.humidity.update(ios_removed, ios_added)
        await self.pressure.update(ios_removed, ios_added)
        await self.carbon_dioxide.update(ios_removed, ios_added)
        await self.wind.update(ios_removed, ios_added)
        await self.power_supply.update(ios_removed, ios_added)
        await self.electricity.update(ios_removed, ios_added)
