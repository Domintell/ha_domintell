from .base import BaseController
from .events import ResourceTypes, EventType

ID_FILTER_ALL = "*"


class ScenesController(BaseController):
    """Controller holding and managing Domintell scenes."""

    item_type = ResourceTypes.SCENE

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
                    f"Scenes controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state

            # Note: Scenes have no status
            self._logger.debug(f"Update IO state for SCENE IO Id: {item_id}")
            self._logger.debug(f"---> Scene New state: {my_io.state}")

            if my_io.state == previous_state:
                return

        await super()._handle_event(event_type, event_data)
