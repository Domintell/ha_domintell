from .base import BaseController
from .events import ResourceTypes, EventType

ID_FILTER_ALL = "*"


class VariablesController(BaseController):
    """Controller holding and managing Domintell variables."""

    item_type = ResourceTypes.VARIABLE

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
                self._logger.debug(
                    f"Variables controller received update for unknown io {item_id}"
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Variable IO Id: {item_id}")

            if isinstance(my_io.state, int):
                # Note: status.data[0] must be an integer
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    my_io.state = data[0]
                    self._logger.debug(f"---> Variable New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for Variable IO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of Variable IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                return

        await super()._handle_event(event_type, event_data)
