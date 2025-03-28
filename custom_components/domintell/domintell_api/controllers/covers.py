from .base import BaseController
from .events import ResourceTypes, EventType
from ..iotypes import CoverState

ID_FILTER_ALL = "*"


class CoversController(BaseController):
    """Controller holding and managing Domintell lights."""

    item_type = ResourceTypes.COVER

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
                    f"Covers controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for COVER IO Id: {item_id}")

            if isinstance(my_io.state, CoverState):
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    new_state = CoverState(data[0])

                    if new_state == CoverState.STOPPED_UNKNOWN:
                        match previous_state:
                            case CoverState.MOVING_UP:
                                current_state = CoverState.STOPPED_UP
                            case CoverState.MOVING_DOWN:
                                current_state = CoverState.STOPPED_DOWN
                            case _:
                                current_state = previous_state
                    else:
                        current_state = new_state

                    my_io.state = current_state
                    self._logger.debug(f"---> Cover New state: {my_io.state}")

                else:
                    self._logger.warning(
                        f"Status for Cover IO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of Cover IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                return

        await super()._handle_event(event_type, event_data)
