import copy

from .base import BaseController
from .events import ResourceTypes, EventType
from ..iotypes import DfanComboState

ID_FILTER_ALL = "*"


class FansController(BaseController):
    """Controller holding and managing Domintell fans."""

    item_type = ResourceTypes.FAN

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
                    f"Fans controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = copy.deepcopy(my_io.state)
            data = event_data["data"]

            if isinstance(my_io.state, DfanComboState):
                # From legacy LpStatus -> data = [speed:int, heating:str, mode:str]
                if len(data) == 3:
                    speed = data[0]  # int
                    heating = str(data[1])  # string
                    mode = str(data[2])  # string
                    my_io.state = DfanComboState(speed, heating, mode)
                else:
                    self._logger.warning(
                        f"Status for DfanComboIO has an incorrect format: data={data}"
                    )

            elif isinstance(my_io.state, int):
                # From legacy LpStatus -> data = [speed:int, aux1:int, aux2:int]
                # From newGen LpStatus -> data = [speed:int]
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    speed = data[0]
                    my_io.state = speed
                else:
                    self._logger.warning(
                        f"Status for FanIO has an incorrect format: data={data}"
                    )

            self._logger.debug(f"---> Fan New state: {my_io.state}")

            if my_io.state == previous_state:
                return

        await super()._handle_event(event_type, event_data)
