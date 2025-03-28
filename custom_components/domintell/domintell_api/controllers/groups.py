from .base import BaseController
from .events import ResourceTypes, EventType

ID_FILTER_ALL = "*"


class GroupsController(BaseController):
    """Controller holding and managing Domintell groups."""

    item_type = ResourceTypes.GROUP

    async def initialize(self) -> None:
        """Initialize controller."""

        for module in self._gateway.modules.values():
            for io in module.values():
                if io.module_type == "MEM":
                    await self._handle_event(
                        EventType.RESOURCE_ADDED, {"id": io.id, "instance": io}
                    )

        await super().initialize()

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
                    f"Groups controller received update for unknown io {item_id}",
                )
                return

            # Update the existing data with the changed keys/data
            previous_state = my_io.state

            # Note: Groups have no status
            self._logger.debug(f"Update IO state for GROUP IO Id: {item_id}")
            self._logger.debug(f"---> Group New state: {my_io.state}")

            if my_io.state == previous_state:
                return

        await super()._handle_event(event_type, event_data)
