from .base import BaseController
from .events import ResourceTypes, EventType

ID_FILTER_ALL = "*"


class SwitchesController(BaseController):
    """Controller holding and managing Domintell switches."""

    item_type = ResourceTypes.SWITCH

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
                    f"Switches controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for SWITCH IO Id: {item_id}")

            if isinstance(my_io.state, bool):
                # Note: status.data[0] must be an integer
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    my_io.state = bool(data[0])
                    self._logger.debug(f"---> Switch New state: {my_io.state}")
                else:
                    self._logger.warning(
                        f"Status for TorIO has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of Switch IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                return

        await super()._handle_event(event_type, event_data)


class MomentarySwitchesController(BaseController):
    """Controller holding and managing Domintell momentary switches."""

    item_type = ResourceTypes.MOMENTARY_SWITCH

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
                    f"Momentary switches controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state
            data = event_data["data"]
            self._logger.debug(f"Update IO state for Momentary Switch IO Id: {item_id}")

            if isinstance(my_io.state, bool):
                # Note: status.data[0] must be an integer
                if (len(data) >= 1) and (isinstance(data[0], int)):
                    my_io.state = bool(data[0])
                    self._logger.debug(
                        f"---> Momentary Switch New state: {my_io.state}"
                    )
                else:
                    self._logger.warning(
                        f"Status for TorBasicTempoIo has an incorrect format: data={data}"
                    )
            else:
                self._logger.warning(
                    f"The IO state type of Momentary Switch IO is not the expected one, state type: {type(my_io.state)}"
                )

            if my_io.state == previous_state:
                return

        await super()._handle_event(event_type, event_data)
