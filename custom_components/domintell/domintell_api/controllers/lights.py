import copy

from .base import BaseController
from .events import ResourceTypes, EventType
from ..iotypes import ColorRGB, ColorRGBI, ColorRGBW, ColorRGBWI

ID_FILTER_ALL = "*"


class LightsController(BaseController):
    """Controller holding and managing Domintell lights."""

    item_type = ResourceTypes.LIGHT

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
                # If this happens it is an item not supported in this implementation
                self._logger.warning(
                    f"Lights controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = copy.deepcopy(my_io.state)
            data = event_data["data"]
            io_type = event_data["io_type"]

            if isinstance(my_io.state, bool):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    my_io.state = bool(data[0])
                elif (
                    (io_type == 60) and (len(data) >= 1) and (isinstance(data[0], list))
                ):
                    # Case of TypeLedIo (io_type = 60) status
                    # Ignore RGB informations
                    my_io.state = bool(data[0][0])
                else:
                    self._logger.warning(
                        f"Status for Light IO has an incorrect format: data={data}"
                    )
            elif isinstance(my_io.state, int):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    my_io.state = event_data["data"][0]
                else:
                    self._logger.warning(
                        f"Status for Light IO has an incorrect format: data={data}"
                    )
            elif isinstance(my_io.state, ColorRGB):
                if (len(data[0]) >= 3) and (isinstance(data[0], int)):
                    my_io.state = ColorRGB(data[0])
                else:
                    self._logger.warning(
                        f"Status for Light IO has an incorrect format: data={data}"
                    )
            elif isinstance(my_io.state, ColorRGBI):
                if (len(data[0]) >= 4) and (isinstance(data[0], list)):
                    my_io.state = ColorRGBI(data[0])
                else:
                    self._logger.warning(
                        f"Status for Light IO has an incorrect format: data={data}"
                    )
            elif isinstance(my_io.state, ColorRGBW):
                if (len(data[0]) >= 4) and (isinstance(data[0], list)):
                    my_io.state = ColorRGBW(data[0])
                else:
                    self._logger.warning(
                        f"Status for Light IO has an incorrect format: data={data}"
                    )
            elif isinstance(my_io.state, ColorRGBWI):
                if (len(data[0]) >= 5) and (isinstance(data[0], list)):
                    my_io.state = ColorRGBWI(data[0])
                else:
                    self._logger.warning(
                        f"Status for Light IO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of Light IO is not the expected one, state type: {type(my_io.state)}"
                )

            self._logger.debug(f"---> Light New state: {my_io.state}")

            if my_io.state == previous_state:
                return

        await super()._handle_event(event_type, event_data)
